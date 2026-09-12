#!/usr/bin/env python3
"""Run optional fixture-driven forge-plan trials against trusted host runners.

Runner commands emit normalized execution evidence only. Case-declared trusted
graders, not the runner, derive correctness. Without candidate, accepted-
baseline, and no-Skill commands this reports UNMEASURED instead of passing.
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_FIXTURE = HERE / "fixtures" / "approved-planning-context.json"
EVIDENCE_KEYS = {"response", "artifacts", "trace", "mutations", "errors", "metrics"}
JUDGE_KEYS = {"assertions", "metrics"}


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _command(value: str | None) -> list[str] | None:
    if not value:
        return None
    try:
        command = shlex.split(value, posix=True)
    except ValueError as exc:
        raise ValueError(f"invalid command: {exc}") from exc
    if not command:
        raise ValueError("command cannot be empty")
    return command


def _cases(evals: Path) -> list[dict]:
    data = _load_json(evals / "execution.json")
    return data if isinstance(data, list) else [data]


def _expected(case: dict) -> list[str]:
    return case.get("expected", {}).get("outcome", {}).get("assertions", [])


def _normalize_evidence(output: object) -> tuple[dict | None, list[str]]:
    """Accept execution evidence, never runner-provided correctness."""
    errors: list[str] = []
    if not isinstance(output, dict):
        return None, ["runner output must be an object"]
    unknown = sorted(set(output) - EVIDENCE_KEYS)
    if unknown:
        errors.append(f"unknown runner output fields: {unknown}")
    if not (set(output) & (EVIDENCE_KEYS - {"metrics"})):
        errors.append("runner output requires normalized execution evidence")
    if "metrics" in output and not isinstance(output["metrics"], dict):
        errors.append("runner output metrics must be an object")
    for key in ("artifacts", "trace", "mutations", "errors"):
        if key in output and not isinstance(output[key], (list, dict, str)):
            errors.append(f"runner output {key} must be a JSON collection or string")
    return (output if not errors else None), errors


def _grade_judge_output(output: object, expected: list[str]) -> dict:
    """Validate a trusted grader response and derive correctness centrally."""
    errors: list[str] = []
    missing = list(expected)
    failed: list[str] = []
    unknown: list[str] = []
    assertions = output.get("assertions") if isinstance(output, dict) else None
    metrics = output.get("metrics", {}) if isinstance(output, dict) else {}
    if not isinstance(output, dict):
        errors.append("grader output must be an object")
    else:
        unknown_keys = sorted(set(output) - JUDGE_KEYS)
        if unknown_keys:
            errors.append(f"unknown grader output fields: {unknown_keys}")
    if not isinstance(assertions, list):
        errors.append("grader output requires an assertions list")
        assertions = []
    if not isinstance(metrics, dict):
        errors.append("grader output metrics must be an object")
        metrics = {}

    seen: set[str] = set()
    normalized = []
    for item in assertions:
        if not isinstance(item, dict) or set(item) != {"text", "passed", "evidence"}:
            errors.append("each grader assertion requires exactly text, passed, evidence")
            continue
        text = item["text"]
        passed = item["passed"]
        evidence = item["evidence"]
        if not isinstance(text, str) or not text.strip() or not isinstance(passed, bool) or not isinstance(evidence, str) or not evidence.strip():
            errors.append("grader assertion text/evidence must be non-empty strings and passed must be boolean")
            continue
        if text in seen:
            errors.append(f"duplicate grader assertion: {text}")
            continue
        seen.add(text)
        if text not in expected:
            unknown.append(text)
        elif text in missing:
            missing.remove(text)
        if text in expected and not passed:
            failed.append(text)
        normalized.append({"text": text, "passed": passed, "evidence": evidence})
    if unknown:
        errors.append(f"unknown assertions: {unknown}")
    if missing:
        errors.append(f"missing assertions: {missing}")
    complete = not errors
    return {
        "status": "GRADED" if complete else "INCOMPLETE",
        "assertions": normalized,
        "missing_assertions": missing,
        "failed_assertions": failed,
        "material_omissions": len(missing),
        "correctness": complete and not failed,
        "metrics": metrics,
        "errors": errors,
    }


def _run_judge(command: list[str], role: str, case: dict, evidence: dict, fixture: dict, grader: dict) -> dict:
    request = {"role": role, "case": case, "fixture": fixture, "evidence": evidence, "grader": grader}
    try:
        proc = subprocess.run(
            command,
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=120,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "FAILED", "error": f"judge execution failed: {exc}"}
    if proc.returncode != 0:
        return {"status": "FAILED", "error": f"judge exited {proc.returncode}: {proc.stderr[-1000:]}"}
    try:
        output = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {"status": "INCOMPLETE", "error": f"judge output is not JSON: {exc}"}
    return _grade_judge_output(output, _expected(case))


def _run_deterministic(case: dict, grader: dict) -> dict:
    """Run only validators trusted by the repository, never corpus commands."""
    try:
        from run_static_evals import VALIDATORS

        check = grader.get("check", {})
        validator = VALIDATORS.get(check.get("validator"))
        if validator is None:
            return {"status": "UNMEASURED", "error": "unsupported deterministic validator"}
        ok, reasons = validator(check)
    except (ImportError, OSError, ValueError, KeyError) as exc:
        return {"status": "FAILED", "error": f"deterministic grader failed: {exc}"}
    evidence = "; ".join(reasons) if reasons else f"trusted validator {check.get('validator')} passed"
    return _grade_judge_output(
        {"assertions": [{"text": text, "passed": ok, "evidence": evidence} for text in _expected(case)]},
        _expected(case),
    )


def _grade_case(role: str, case: dict, evidence: dict, fixture: dict, judge_command: list[str] | None) -> dict:
    graders = case.get("graders", [])
    if not graders:
        return {"status": "UNMEASURED", "error": "case has no trusted grader"}
    graded = []
    for grader in graders:
        kind = grader.get("type") if isinstance(grader, dict) else None
        if kind == "deterministic":
            graded.append(_run_deterministic(case, grader))
        elif kind == "llm-judge":
            graded.append(
                {"status": "UNMEASURED", "error": "missing trusted judge command"}
                if judge_command is None
                else _run_judge(judge_command, role, case, evidence, fixture, grader)
            )
        else:
            graded.append({"status": "UNMEASURED", "error": f"unsupported grader type: {kind}"})
    unavailable = next((result for result in graded if result["status"] != "GRADED"), None)
    if unavailable is not None:
        return unavailable
    merged: dict[str, dict] = {}
    for result in graded:
        for assertion in result["assertions"]:
            prior = merged.get(assertion["text"])
            if prior is not None and prior["passed"] != assertion["passed"]:
                return {"status": "FAILED", "error": "trusted graders disagree"}
            merged[assertion["text"]] = assertion
    expected = _expected(case)
    assertions = [merged[text] for text in expected if text in merged]
    failed = [item["text"] for item in assertions if not item["passed"]]
    return {
        "status": "GRADED",
        "assertions": assertions,
        "missing_assertions": [text for text in expected if text not in merged],
        "failed_assertions": failed,
        "material_omissions": len([text for text in expected if text not in merged]),
        "correctness": len(assertions) == len(expected) and not failed,
        "metrics": evidence.get("metrics", {}),
        "grader_results": graded,
    }


def _run_role(role: str, command: list[str], cases: list[dict], fixture: dict, judge_command: list[str] | None) -> list[dict]:
    results = []
    for case in cases:
        envelope = {
            "role": role,
            "case": {"id": case["id"], "prompt": case["prompt"], "expected": case.get("expected", {}), "tags": case.get("tags", [])},
            "fixture": fixture,
        }
        try:
            proc = subprocess.run(
                command,
                input=json.dumps(envelope),
                capture_output=True,
                text=True,
                timeout=120,
                shell=False,
            )
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


def _comparison(role_results: dict[str, dict]) -> dict:
    correctness = {role: role_results[role]["correctness"] for role in role_results}
    omissions = {role: role_results[role]["material_omissions"] for role in role_results}
    assertion_results = {}
    for role, result in role_results.items():
        for assertion in result["assertions"]:
            assertion_results.setdefault(assertion["text"], {})[role] = {"passed": assertion["passed"], "evidence": assertion["evidence"]}

    def delta(other: str) -> dict:
        correctness_delta = int(correctness["candidate"]) - int(correctness[other])
        omission_delta = omissions["candidate"] - omissions[other]
        return {
            "correctness_delta": correctness_delta,
            "material_omission_delta": omission_delta,
            "improvement": correctness_delta > 0 or omission_delta < 0,
            "regression": correctness_delta < 0 or omission_delta > 0,
        }

    comparison = {
        "status": "COMPARED",
        "correctness": correctness,
        "material_omissions": omissions,
        "assertion_results": assertion_results,
        "candidate_vs_baseline": delta("baseline"),
        "candidate_vs_no_skill": delta("no-skill"),
    }
    efficiency = {role: result["metrics"] for role, result in role_results.items() if result.get("metrics")}
    if efficiency:
        comparison["efficiency_metrics"] = efficiency
    return comparison


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evals", type=Path, default=HERE)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--candidate-command")
    parser.add_argument("--baseline-command")
    parser.add_argument("--no-skill-command")
    parser.add_argument("--judge-command", help="explicit trusted grader command for llm-judge cases")
    parser.add_argument("--case-id", action="append", dest="case_ids")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        fixture = _load_json(args.fixture)
        cases = _cases(args.evals)
        if args.case_ids:
            requested = set(args.case_ids)
            available = {case.get("id") for case in cases}
            missing_cases = sorted(requested - available)
            if missing_cases:
                raise ValueError(f"unknown case IDs: {missing_cases}")
            cases = [case for case in cases if case.get("id") in requested]
        commands = {"candidate": _command(args.candidate_command), "baseline": _command(args.baseline_command), "no-skill": _command(args.no_skill_command)}
        judge_command = _command(args.judge_command)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    missing = [role for role, command in commands.items() if command is None]
    if missing:
        report = {"status": "UNMEASURED", "reason": "missing trusted runner commands", "missing_roles": missing, "case_count": len(cases), "fixture": str(args.fixture), "results": []}
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
            comparison = _comparison(role_results)  # type: ignore[arg-type]
            comparison["id"] = case["id"]
            comparisons.append(comparison)

    failures = [result for result in results if result["status"] in {"FAILED", "INCOMPLETE"}]
    incomplete_comparisons = [comparison for comparison in comparisons if comparison["status"] != "COMPARED"]
    candidate_results = [result for result in results if result["role"] == "candidate"]
    candidate_incorrect = [result for result in candidate_results if result.get("status") == "GRADED" and not result["correctness"]]
    candidate_unmeasured = [result for result in candidate_results if result.get("status") != "GRADED"]
    regressions = [comparison for comparison in comparisons if comparison.get("candidate_vs_baseline", {}).get("regression") or comparison.get("candidate_vs_no_skill", {}).get("regression")]
    hard_failure = bool(failures or candidate_incorrect or regressions)
    if hard_failure:
        status = "FAILED"
    elif incomplete_comparisons or candidate_unmeasured:
        status = "UNMEASURED"
    else:
        status = "EXECUTED"
    report = {"status": status, "case_count": len(cases), "fixture": str(args.fixture), "roles": list(commands), "results": results, "comparisons": comparisons, "failure_count": len(failures), "incorrect_count": len(candidate_incorrect), "regression_count": len(regressions)}
    print(json.dumps(report, indent=2) if args.json else f"{report['status']}: {len(results) - len(failures)} graded, {len(failures)} incomplete/failed, {len(regressions)} regressions")
    return 1 if hard_failure or (args.strict and status != "EXECUTED") else 0


if __name__ == "__main__":
    sys.exit(main())
