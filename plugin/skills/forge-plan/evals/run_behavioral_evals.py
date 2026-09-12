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
            results.append({"role": role, "id": case["id"], "status": "failed", "error": str(exc)})
            continue
        result = {"role": role, "id": case["id"], "exit": proc.returncode}
        if proc.returncode != 0:
            result.update({"status": "failed", "error": proc.stderr[-1000:]})
        else:
            try:
                result.update({"status": "executed", "output": json.loads(proc.stdout)})
            except json.JSONDecodeError as exc:
                result.update({"status": "failed", "error": f"runner output is not JSON: {exc}"})
        results.append(result)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evals", type=Path, default=HERE)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--candidate-command")
    parser.add_argument("--baseline-command")
    parser.add_argument("--no-skill-command")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        fixture = _load_json(args.fixture)
        cases = _cases(args.evals)
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
    failures = [result for result in results if result["status"] == "failed"]
    report = {
        "status": "EXECUTED",
        "case_count": len(cases),
        "fixture": str(args.fixture),
        "roles": list(commands),
        "results": results,
        "failure_count": len(failures),
    }
    print(json.dumps(report, indent=2) if args.json else f"EXECUTED: {len(results) - len(failures)} runs, {len(failures)} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
