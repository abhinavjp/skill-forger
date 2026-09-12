#!/usr/bin/env python3
"""Run optional fixture-driven forge-plan trials against trusted host runners.

The runner commands are supplied by the maintainer, never by the eval corpus.
Without candidate, accepted-baseline, and no-Skill commands, this reports
UNMEASURED instead of passing.
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


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _command(value: str | None) -> list[str] | None:
    if not value:
        return None
    try:
        # Commands are passed to subprocess without a shell. POSIX tokenization
        # gives the same quote-removal contract on Windows and POSIX hosts.
        command = shlex.split(value, posix=True)
    except ValueError as exc:
        raise ValueError(f"invalid runner command: {exc}") from exc
    if not command:
        raise ValueError("runner command cannot be empty")
    return command


def _cases(evals: Path) -> list[dict]:
    data = _load_json(evals / "execution.json")
    return data if isinstance(data, list) else [data]


def _grade_output(output: object, expected: list[str]) -> dict:
    """Validate and grade one runner response against one case."""
    errors: list[str] = []
    missing = list(expected)
    failed: list[str] = []
    unknown: list[str] = []
    assertions = output.get("assertions") if isinstance(output, dict) else None
    metrics = output.get("metrics", {}) if isinstance(output, dict) else {}
    if not isinstance(output, dict):
        errors.append("runner output must be an object")
    else:
        unknown_keys = sorted(set(output) - {"assertions", "metrics"})
        if unknown_keys:
            errors.append(f"unknown runner output fields: {unknown_keys}")
    if not isinstance(assertions, list):
        errors.append("runner output requires an assertions list")
        assertions = []
    if not isinstance(metrics, dict):
        errors.append("runner output metrics must be an object")
        metrics = {}

    seen: set[str] = set()
    normalized = []
    for item in assertions:
        if not isinstance(item, dict) or set(item) != {"text", "passed", "evidence"}:
            errors.append("each assertion requires exactly text, passed, evidence")
            continue
        text = item["text"]
        passed = item["passed"]
        evidence = item["evidence"]
        if not isinstance(text, str) or not isinstance(passed, bool) or not isinstance(evidence, str) or not evidence.strip():
            errors.append("assertion text/evidence must be non-empty strings and passed must be boolean")
            continue
        if text in seen:
            errors.append(f"duplicate assertion: {text}")
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


def _run_role(role: str, command: list[str], cases: list[dict], fixture: dict) -> list[dict]:
    results = []
    for case in cases:
        envelope = {
            "role": role,
            "case": {
                "id": case["id"],
                "prompt": case["prompt"],
                "expected": case.get("expected", {}),
                "tags": case.get("tags", []),
            },
            "fixture": fixture,
        }
        try:
            proc = subprocess.run(
                command,
                input=json.dumps(envelope),
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            results.append({"role": role, "id": case["id"], "status": "FAILED", "error": str(exc)})
            continue
        result = {"role": role, "id": case["id"], "exit": proc.returncode}
        if proc.returncode != 0:
            result.update({"status": "FAILED", "error": proc.stderr[-1000:]})
        else:
            try:
                graded = _grade_output(
                    json.loads(proc.stdout),
                    case.get("expected", {}).get("outcome", {}).get("assertions", []),
                )
                result.update(graded)
            except json.JSONDecodeError as exc:
                result.update({"status": "INCOMPLETE", "error": f"runner output is not JSON: {exc}"})
        results.append(result)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evals", type=Path, default=HERE)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--candidate-command")
    parser.add_argument("--baseline-command")
    parser.add_argument("--no-skill-command")
    parser.add_argument("--case-id", action="append", dest="case_ids")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        fixture = _load_json(args.fixture)
        cases = _cases(args.evals)
        if args.case_ids:
            cases = [case for case in cases if case.get("id") in args.case_ids]
            missing_cases = sorted(set(args.case_ids) - {case.get("id") for case in cases})
            if missing_cases:
                raise ValueError(f"unknown case IDs: {missing_cases}")
        commands = {
            "candidate": _command(args.candidate_command),
            "baseline": _command(args.baseline_command),
            "no-skill": _command(args.no_skill_command),
        }
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    missing = [role for role, command in commands.items() if command is None]
    if missing:
        report = {
            "status": "UNMEASURED",
            "reason": "missing trusted runner commands",
            "missing_roles": missing,
            "case_count": len(cases),
            "fixture": str(args.fixture),
            "results": [],
        }
        print(json.dumps(report, indent=2) if args.json else "UNMEASURED: " + ", ".join(missing))
        return 1 if args.strict else 0

    results = []
    for role, command in commands.items():
        assert command is not None
        results.extend(_run_role(role, command, cases, fixture))
    by_case = {case["id"]: {role: None for role in commands} for case in cases}
    for result in results:
        by_case[result["id"]][result["role"]] = result
    comparisons = []
    for case in cases:
        role_results = by_case[case["id"]]
        incomplete_roles = [
            role for role, result in role_results.items()
            if result is None or result.get("status") != "GRADED"
        ]
        if incomplete_roles:
            comparisons.append({
                "id": case["id"],
                "status": "INCOMPLETE",
                "incomplete_roles": incomplete_roles,
            })
            continue
        correctness = {role: role_results[role]["correctness"] for role in commands}
        omissions = {role: role_results[role]["material_omissions"] for role in commands}
        candidate_vs_baseline = {
            "regression": (
                not correctness["candidate"] and correctness["baseline"]
            ) or omissions["candidate"] > omissions["baseline"],
            "correctness_delta": int(correctness["candidate"]) - int(correctness["baseline"]),
            "material_omission_delta": omissions["candidate"] - omissions["baseline"],
        }
        comparison = {
            "id": case["id"],
            "status": "COMPARED",
            "correctness": correctness,
            "material_omissions": omissions,
            "candidate_vs_baseline": candidate_vs_baseline,
        }
        efficiency = {
            role: role_results[role]["metrics"]
            for role in commands
            if role_results[role].get("metrics")
        }
        if efficiency:
            comparison["efficiency_metrics"] = efficiency
        comparisons.append(comparison)
    failures = [result for result in results if result["status"] in {"FAILED", "INCOMPLETE"}]
    incorrect = [
        result for result in results
        if result["status"] == "GRADED" and not result["correctness"]
    ]
    regressions = [
        comparison for comparison in comparisons
        if comparison.get("candidate_vs_baseline", {}).get("regression")
    ]
    incomplete_comparisons = [comparison for comparison in comparisons if comparison["status"] != "COMPARED"]
    overall_failed = bool(failures or incorrect or regressions or incomplete_comparisons)
    report = {
        "status": "FAILED" if overall_failed else "EXECUTED",
        "case_count": len(cases),
        "fixture": str(args.fixture),
        "roles": list(commands),
        "results": results,
        "comparisons": comparisons,
        "failure_count": len(failures),
        "incorrect_count": len(incorrect),
        "regression_count": len(regressions),
    }
    print(json.dumps(report, indent=2) if args.json else f"{report['status']}: {len(results) - len(failures)} graded, {len(failures)} incomplete/failed, {len(regressions)} regressions")
    return 1 if overall_failed else 0


if __name__ == "__main__":
    sys.exit(main())
