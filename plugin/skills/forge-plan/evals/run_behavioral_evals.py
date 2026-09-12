#!/usr/bin/env python3
"""Run optional fixture-driven forge-plan trials against trusted host runners.

The runner emits normalized execution evidence only. Case-declared graders,
not the runner, derive correctness. Process inputs use validated argv files so
Windows paths and shell metacharacters remain literal. Missing host evidence
is reported as UNMEASURED instead of passing.
"""
from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
DEFAULT_FIXTURE = HERE / "fixtures" / "approved-planning-context.json"
SCRIPTS = SKILL_ROOT.parent / "skill-engineer" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import validate_evals  # noqa: E402


EVIDENCE_KEYS = {"response", "artifacts", "trace", "mutations", "errors", "metrics"}
JUDGE_KEYS = {"assertions", "metrics"}
METRICS_VERSION = 1
METRIC_FIELDS = (
    "mode", "correctness", "material_omissions", "blocking_questions",
    "rediscovery", "traceability_coverage", "acceptance_coverage",
    "dependency_errors", "scope_errors", "input_tokens", "context_tokens",
    "output_tokens", "references", "tool_calls", "duration_ms", "retries",
    "errors", "review_findings", "deviations",
)
UNMEASURED = "UNMEASURED"


class CorpusError(ValueError):
    """The canonical corpus cannot safely be executed."""


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _argv_file(value: str | None) -> list[str] | None:
    if not value:
        return None
    path = Path(value)
    try:
        data = _load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid argv file {path}: {exc}") from exc
    if not isinstance(data, list) or not data or not all(isinstance(item, str) and item for item in data):
        raise ValueError(f"argv file {path} must contain a non-empty JSON array of non-empty strings")
    if any("\x00" in item for item in data):
        raise ValueError(f"argv file {path} contains a NUL argument")
    return data


def _load_fixture(path: Path) -> dict:
    data = _load_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("authority"), list) or not isinstance(data.get("repository"), dict) or not isinstance(data.get("plan"), dict):
        raise CorpusError("fixture must contain authority, repository, and plan objects")
    baseline_name = data.get("accepted_baseline_fixture")
    if not isinstance(baseline_name, str) or Path(baseline_name).is_absolute() or ".." in Path(baseline_name).parts:
        raise CorpusError("fixture accepted_baseline_fixture must be a safe relative path")
    baseline_path = path.parent / baseline_name
    baseline = _load_json(baseline_path)
    if not isinstance(baseline, dict) or not isinstance(baseline.get("scenarios"), list) or not baseline.get("scenarios"):
        raise CorpusError("accepted baseline fixture must contain scenarios")
    data["accepted_baseline"] = baseline
    return data


def _load_cases(evals: Path, requested: list[str] | None) -> tuple[list[dict], list[str]]:
    corpus = evals / "execution.json"
    validation = validate_evals.validate_paths([str(corpus)])
    if validation["errors"]:
        raise CorpusError(f"invalid execution corpus: {validation['errors']}")
    try:
        data = _load_json(corpus)
    except (OSError, json.JSONDecodeError) as exc:
        raise CorpusError(f"unreadable execution corpus: {exc}") from exc
    cases = data if isinstance(data, list) else [data]
    if not cases:
        raise CorpusError("execution corpus must contain at least one case")
    ids = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(ids) != len(set(ids)):
        raise CorpusError("execution corpus contains duplicate case IDs")
    if requested:
        missing = sorted(set(requested) - set(ids))
        if missing:
            raise CorpusError(f"unknown case IDs: {missing}")
        cases = [case for case in cases if case.get("id") in requested]
    static_only = []
    behavioral = []
    for case in cases:
        graders = case.get("graders", [])
        if graders and all(grader.get("type") == "deterministic" for grader in graders):
            static_only.append(case["id"])
        else:
            behavioral.append(case)
    return behavioral, static_only


def _expected(case: dict) -> list[str]:
    return case["expected"]["outcome"]["assertions"]


def _normalize_metrics(value: object) -> tuple[dict | None, list[str]]:
    if value is None:
        value = {}
    if not isinstance(value, dict):
        return None, ["metrics must be an object"]
    errors = []
    if value.get("version", METRICS_VERSION) != METRICS_VERSION:
        errors.append(f"metrics.version must be {METRICS_VERSION}")
    unknown = sorted(set(value) - ({"version"} | set(METRIC_FIELDS)))
    if unknown:
        errors.append(f"unknown metric fields: {unknown}")
    normalized = {"version": METRICS_VERSION}
    for field in METRIC_FIELDS:
        normalized[field] = value.get(field, UNMEASURED)
    return (normalized if not errors else None), errors


def _normalize_evidence(output: object) -> tuple[dict | None, list[str]]:
    """Accept execution evidence, never runner-provided correctness."""
    if not isinstance(output, dict):
        return None, ["runner output must be an object"]
    errors = []
    unknown = sorted(set(output) - EVIDENCE_KEYS)
    if unknown:
        errors.append(f"unknown runner output fields: {unknown}")
    if not (set(output) & (EVIDENCE_KEYS - {"metrics"})):
        errors.append("runner output requires normalized execution evidence")
    metrics, metric_errors = _normalize_metrics(output.get("metrics"))
    errors.extend(f"runner {error}" for error in metric_errors)
    for key in ("artifacts", "trace", "mutations", "errors"):
        if key in output and not isinstance(output[key], (list, dict, str)):
            errors.append(f"runner output {key} must be a JSON collection or string")
    if errors:
        return None, errors
    normalized = dict(output)
    normalized["metrics"] = metrics
    return normalized, []


def _finalize_assertions(expected: list[str], payloads: list[object]) -> dict:
    """Canonical finalizer for one or more trusted grader payloads."""
    errors: list[str] = []
    records: dict[str, dict] = {}
    metrics: list[dict] = []
    for payload in payloads:
        if not isinstance(payload, dict):
            errors.append("grader output must be an object")
            continue
        unknown_keys = sorted(set(payload) - JUDGE_KEYS)
        if unknown_keys:
            errors.append(f"unknown grader output fields: {unknown_keys}")
        raw_assertions = payload.get("assertions")
        if not isinstance(raw_assertions, list):
            errors.append("grader output requires an assertions list")
            raw_assertions = []
        metric_value, metric_errors = _normalize_metrics(payload.get("metrics"))
        errors.extend(f"grader {error}" for error in metric_errors)
        if metric_value is not None:
            metrics.append(metric_value)
        local_seen: set[str] = set()
        for item in raw_assertions:
            if not isinstance(item, dict) or set(item) != {"text", "passed", "evidence"}:
                errors.append("each grader assertion requires exactly text, passed, evidence")
                continue
            text = item["text"]
            passed = item["passed"]
            evidence = item["evidence"]
            if not isinstance(text, str) or not text.strip() or not isinstance(passed, bool) or not isinstance(evidence, str) or not evidence.strip():
                errors.append("grader assertion text/evidence must be non-empty strings and passed must be boolean")
                continue
            if text in local_seen:
                errors.append(f"duplicate grader assertion: {text}")
                continue
            local_seen.add(text)
            if text not in expected:
                errors.append(f"unknown assertion: {text}")
                continue
            prior = records.get(text)
            if prior is not None:
                if prior["passed"] != passed:
                    errors.append(f"conflicting grader assertion: {text}")
                elif evidence not in prior["evidence"].split(" | "):
                    prior["evidence"] += " | " + evidence
            else:
                records[text] = {"text": text, "passed": passed, "evidence": evidence}
    missing = [text for text in expected if text not in records]
    if missing:
        errors.append(f"missing assertions: {missing}")
    assertions = [records[text] for text in expected if text in records]
    failed = [item["text"] for item in assertions if not item["passed"]]
    complete = not errors
    return {
        "status": "GRADED" if complete else "INCOMPLETE",
        "assertions": assertions,
        "missing_grader_assertions": missing,
        "failed_assertions": failed,
        "material_omissions": len(failed) if complete else None,
        "correctness": complete and not failed,
        "grader_metrics": metrics,
        "errors": errors,
    }


def _run_judge(command: list[str], role: str, case: dict, evidence: dict, fixture: dict, grader: dict) -> dict:
    request = {
        "role": role,
        "case_id": case["id"],
        "prompt": case["prompt"],
        "tags": case.get("tags", []),
        "expected": case["expected"],
        "grader": grader,
        "fixture": fixture,
        "evidence": evidence,
    }
    try:
        proc = subprocess.run(command, input=json.dumps(request), capture_output=True, text=True, timeout=120, shell=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "FAILED", "error": f"judge execution failed: {exc}"}
    if proc.returncode != 0:
        return {"status": "FAILED", "error": f"judge exited {proc.returncode}: {proc.stderr[-1000:]}"}
    try:
        return {"status": "PAYLOAD", "payload": json.loads(proc.stdout)}
    except json.JSONDecodeError as exc:
        return {"status": "INCOMPLETE", "error": f"judge output is not JSON: {exc}"}


def _grade_case(role: str, case: dict, evidence: dict, fixture: dict, judge_command: list[str] | None) -> dict:
    graders = case.get("graders", [])
    payloads = []
    grader_results = []
    for grader in graders:
        if grader.get("type") != "llm-judge":
            return {"status": "UNMEASURED", "error": "static-only or unsupported grader excluded from behavioral harness"}
        if judge_command is None:
            return {"status": "UNMEASURED", "error": "missing trusted judge argv"}
        result = _run_judge(judge_command, role, case, evidence, fixture, grader)
        if result["status"] != "PAYLOAD":
            return result
        payloads.append(result["payload"])
        grader_results.append({"type": grader.get("type"), "status": "RECEIVED"})
    final = _finalize_assertions(_expected(case), payloads)
    final["grader_results"] = grader_results
    final["metrics"] = evidence["metrics"]
    return final


def _run_role(role: str, command: list[str], cases: list[dict], fixture: dict, judge_command: list[str] | None) -> list[dict]:
    results = []
    for case in cases:
        envelope = {
            "case_id": case["id"],
            "prompt": case["prompt"],
            "tags": case.get("tags", []),
            "role": role,
            "fixture": fixture,
        }
        try:
            proc = subprocess.run(command, input=json.dumps(envelope), capture_output=True, text=True, timeout=120, shell=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            results.append({"role": role, "id": case["id"], "status": "FAILED", "error": str(exc)})
            continue
        result = {"role": role, "id": case["id"], "exit": proc.returncode}
        if proc.returncode != 0:
            result.update({"status": "FAILED", "error": proc.stderr[-1000:]})
        else:
            try:
                output = json.loads(proc.stdout)
            except json.JSONDecodeError as exc:
                result.update({"status": "INCOMPLETE", "error": f"runner output is not JSON: {exc}"})
            else:
                evidence, errors = _normalize_evidence(output)
                if errors:
                    result.update({"status": "INCOMPLETE", "errors": errors})
                else:
                    assert evidence is not None
                    result.update(_grade_case(role, case, evidence, fixture, judge_command))
                    result["evidence"] = evidence
        results.append(result)
    return results


def _comparison(case: dict, role_results: dict[str, dict]) -> dict:
    expected = _expected(case)
    role_assertions = {
        role: {item["text"]: item for item in result["assertions"]}
        for role, result in role_results.items()
    }
    correctness = {role: result["correctness"] for role, result in role_results.items()}
    omissions = {role: role_results[role]["material_omissions"] for role in role_results}
    assertion_results = {
        text: {
            role: role_assertions[role].get(text, {"passed": False, "evidence": UNMEASURED})
            for role in role_results
        }
        for text in expected
    }

    def delta(other: str) -> dict:
        lost = [text for text in expected if role_assertions[other][text]["passed"] and not role_assertions["candidate"][text]["passed"]]
        gained = [text for text in expected if role_assertions["candidate"][text]["passed"] and not role_assertions[other][text]["passed"]]
        pass_count_delta = sum(role_assertions["candidate"][text]["passed"] for text in expected) - sum(role_assertions[other][text]["passed"] for text in expected)
        omission_delta = omissions["candidate"] - omissions[other]
        return {
            "lost_assertions": lost,
            "gained_assertions": gained,
            "pass_count_delta": pass_count_delta,
            "correctness_delta": int(correctness["candidate"]) - int(correctness[other]),
            "material_omission_delta": omission_delta,
            "improvement": bool(gained) and not lost,
            "regression": bool(lost),
        }

    comparison = {
        "status": "COMPARED",
        "correctness": correctness,
        "material_omissions": omissions,
        "assertion_results": assertion_results,
        "candidate_vs_baseline": delta("baseline"),
        "candidate_vs_no_skill": delta("no-skill"),
    }
    comparison["metrics"] = {role: result["metrics"] for role, result in role_results.items()}
    return comparison


def _static_structure_ok() -> tuple[bool, list[str]]:
    """Structural self-check used by the static corpus, not a prose gate."""
    try:
        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        return False, [f"harness cannot be parsed: {exc}"]
    functions = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    required = {"_argv_file", "_finalize_assertions", "_run_role", "_run_judge", "main"}
    missing = sorted(required - functions)
    subprocess_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run"]
    if any(not any(keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is False for keyword in call.keywords) for call in subprocess_calls):
        missing.append("subprocess.run shell=False")
    return not missing, missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evals", type=Path, default=HERE)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--candidate-argv-file")
    parser.add_argument("--baseline-argv-file")
    parser.add_argument("--no-skill-argv-file")
    parser.add_argument("--judge-argv-file")
    parser.add_argument("--case-id", action="append", dest="case_ids")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        fixture = _load_fixture(args.fixture)
        cases, static_only = _load_cases(args.evals, args.case_ids)
        commands = {
            "candidate": _argv_file(args.candidate_argv_file),
            "baseline": _argv_file(args.baseline_argv_file),
            "no-skill": _argv_file(args.no_skill_argv_file),
        }
        judge_command = _argv_file(args.judge_argv_file)
    except (OSError, json.JSONDecodeError, ValueError, CorpusError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not cases:
        report = {
            "status": "UNMEASURED",
            "reason": "selected cases are repository-static; run run_static_evals.py",
            "static_only_cases": static_only,
            "case_count": 0,
            "results": [],
        }
        print(json.dumps(report, indent=2) if args.json else "UNMEASURED: static-only cases")
        return 1 if args.strict else 0
    missing = [role for role, command in commands.items() if command is None]
    if missing:
        report = {"status": "UNMEASURED", "reason": "missing trusted runner argv", "missing_roles": missing, "static_only_cases": static_only, "case_count": len(cases), "fixture": str(args.fixture), "results": []}
        print(json.dumps(report, indent=2) if args.json else "UNMEASURED: " + ", ".join(missing))
        return 1 if args.strict else 0

    results = []
    for role, command in commands.items():
        assert command is not None
        results.extend(_run_role(role, command, cases, fixture, judge_command))
    by_case = {case["id"]: {role: None for role in commands} for case in cases}
    for result in results:
        by_case[result["id"]][result["role"]] = result
    comparisons = []
    for case in cases:
        role_results = by_case[case["id"]]
        incomplete_roles = [role for role, result in role_results.items() if result is None or result.get("status") != "GRADED"]
        if incomplete_roles:
            comparisons.append({"id": case["id"], "status": "INCOMPLETE", "incomplete_roles": incomplete_roles})
        else:
            comparison = _comparison(case, role_results)  # type: ignore[arg-type]
            comparison["id"] = case["id"]
            comparisons.append(comparison)
    failures = [result for result in results if result["status"] in {"FAILED", "INCOMPLETE"}]
    candidate_results = [result for result in results if result["role"] == "candidate"]
    candidate_incorrect = [result for result in candidate_results if result.get("status") == "GRADED" and not result["correctness"]]
    candidate_unmeasured = [result for result in candidate_results if result.get("status") != "GRADED"]
    regressions = [comparison for comparison in comparisons if comparison.get("candidate_vs_baseline", {}).get("regression") or comparison.get("candidate_vs_no_skill", {}).get("regression")]
    hard_failure = bool(failures or candidate_incorrect or regressions)
    status = "FAILED" if hard_failure else ("UNMEASURED" if candidate_unmeasured or any(item["status"] != "COMPARED" for item in comparisons) else "EXECUTED")
    report = {
        "status": status,
        "case_count": len(cases),
        "static_only_cases": static_only,
        "fixture": str(args.fixture),
        "roles": list(commands),
        "metrics_schema": {"version": METRICS_VERSION, "fields": list(METRIC_FIELDS)},
        "results": results,
        "comparisons": comparisons,
        "failure_count": len(failures),
        "incorrect_count": len(candidate_incorrect),
        "regression_count": len(regressions),
    }
    print(json.dumps(report, indent=2) if args.json else f"{report['status']}: {len(results) - len(failures)} graded, {len(failures)} incomplete/failed, {len(regressions)} regressions")
    return 1 if hard_failure or (args.strict and status != "EXECUTED") else 0


if __name__ == "__main__":
    sys.exit(main())
