#!/usr/bin/env python3
"""Run the deterministic slice of the eval corpus. No model, no host adapter.

Usage:
    python evals/run_static_evals.py [--evals <dir>] [--json]

Runs every case whose grader is `deterministic` with a `check.command`. Cases
graded by an LLM judge, a human, or a process assertion need a host runner and
are reported as SKIPPED — never as passed, which would be eval theatre.

Commands run with the Skill root as the working directory. Each case is also
schema-validated first, so a malformed case is a fixture failure, not a Skill
failure (see references/eval-spec.md, "Failure classification").

Exit codes:
    0  all runnable cases passed
    1  at least one case failed
    2  corpus could not be loaded
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import validate_evals  # noqa: E402


def runnable_check(case):
    for grader in case.get("graders") or []:
        if (isinstance(grader, dict) and grader.get("type") == "deterministic"
                and isinstance(grader.get("check"), dict)
                and grader["check"].get("command")):
            return grader["check"]
    return None


def run_check(check):
    """Execute one deterministic check. Returns (passed, reasons, duration_ms)."""
    started = time.time()
    proc = subprocess.run(
        [sys.executable if c == "python" else c for c in check["command"]],
        cwd=ROOT, capture_output=True, text=True,
    )
    duration_ms = int((time.time() - started) * 1000)
    reasons = []
    expected_exit = check.get("expect_exit", 0)
    if proc.returncode != expected_exit:
        reasons.append(
            f"exit {proc.returncode}, expected {expected_exit}"
            + (f": {proc.stderr.strip()[:200]}" if proc.stderr.strip() else "")
        )
    for needle in check.get("stdout_contains") or []:
        if needle not in proc.stdout:
            reasons.append(f"stdout missing: {needle!r}")
    for needle in check.get("stdout_not_contains") or []:
        if needle in proc.stdout:
            reasons.append(f"stdout unexpectedly contains: {needle!r}")
    return not reasons, reasons, duration_ms


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evals", default=HERE)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        validation = validate_evals.validate_paths([args.evals])
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if validation["errors"]:
        print("corpus failed schema validation (fixture failure):",
              file=sys.stderr)
        for error in validation["errors"]:
            print(f"  {error['case']}: {error['error']}", file=sys.stderr)
        return 2

    results = []
    for path in validation["files"]:
        data = validate_evals._load(path)
        for case in (data if isinstance(data, list) else [data]):
            check = runnable_check(case)
            if not check:
                results.append({"id": case["id"], "status": "skipped",
                                "reason": "requires host runner"})
                continue
            trials = case.get("trials", 1) if case.get("kind") == "trigger" else 1
            passes, reasons, duration = 0, [], 0
            for _ in range(trials):
                ok, why, ms = run_check(check)
                passes += 1 if ok else 0
                reasons.extend(why)
                duration += ms
            results.append({
                "id": case["id"],
                "status": "passed" if passes == trials else "failed",
                "trials": trials,
                "passes": passes,
                "pass_rate": passes / trials,
                "duration_ms": duration,
                "reasons": reasons[:10],
            })

    summary = {
        "runnable": sum(1 for r in results if r["status"] != "skipped"),
        "passed": sum(1 for r in results if r["status"] == "passed"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "skipped": sum(1 for r in results if r["status"] == "skipped"),
    }
    if args.json:
        print(json.dumps({"summary": summary, "results": results}, indent=2))
    else:
        for result in results:
            mark = {"passed": "PASS", "failed": "FAIL",
                    "skipped": "SKIP"}[result["status"]]
            extra = result.get("reason") or "; ".join(result.get("reasons", []))
            print(f"{mark} {result['id']}" + (f"  {extra}" if extra else ""))
        print(f"\n{summary['passed']}/{summary['runnable']} deterministic cases "
              f"passed, {summary['skipped']} require a host runner")
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
