#!/usr/bin/env python3
"""Run the deterministic slice of the eval corpus. No model, no host adapter.

Usage:
    python evals/run_static_evals.py [--evals <dir>] [--json]

Runs every case carrying a `deterministic` grader whose `check.kind` names an
operation implemented below. Cases graded by a host router, an LLM judge, a
human, or a process assertion need a host runner and are reported as SKIPPED —
never as passed, which would be eval theatre.

Trust boundary: eval files are data. They select a check kind from a fixed
vocabulary; they never supply a command line, an interpreter, or a path outside
the Skill package. Every operation below runs in-process against this Skill's
own trusted modules — the runner spawns no subprocess, so pointing `--evals` at
an untrusted corpus cannot execute that corpus's code. A case that tries to
carry `check.command` is rejected by schema validation before anything runs.

Exit codes:
    0  all runnable cases passed
    1  at least one case failed
    2  corpus could not be loaded
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import inspect_skill  # noqa: E402
import validate_evals  # noqa: E402


class UnsafeCheck(Exception):
    """A check asked for something outside the runner's capability bounds."""


def _resolve(rel):
    """Resolve a package-relative path, refusing anything outside the package."""
    if not validate_evals._contained(rel):
        raise UnsafeCheck(f"path escapes the package: {rel!r}")
    full = os.path.normpath(os.path.join(ROOT, rel))
    if os.path.commonpath([os.path.abspath(full), ROOT]) != ROOT:
        raise UnsafeCheck(f"path escapes the package: {rel!r}")
    return full


def _capture(entry, argv):
    """Run a trusted module entry point, returning (exit_code, stdout)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = entry(argv)
    return code, out.getvalue(), err.getvalue()


# --- trusted named validators -------------------------------------------------
# Referenced by `check: {kind: validator, validator: <name>}`. Adding one is a
# code change reviewed like any other, not a data change in the corpus.

def trigger_prompts_carry_their_input(_check):
    """No trigger prompt may elide the artefact its grader depends on (RG-007)."""
    path = os.path.join(ROOT, "evals", "trigger.json")
    cases = validate_evals._load(path)
    offenders = [
        case["id"] for case in cases
        if isinstance(case, dict)
        and any(marker in (case.get("prompt") or "")
                for marker in ("content follows]", "[...]", "<paste"))
    ]
    return (not offenders,
            [f"trigger prompt elides its own input: {', '.join(offenders)}"]
            if offenders else [])


def unsafe_sentinel_absent(_check):
    """Nothing in the hostile corpus ever executed (RG-008)."""
    sentinels = [
        "/tmp/skill-engineer-unsafe-sentinel",
        os.path.join(ROOT, "skill-engineer-unsafe-sentinel"),
    ]
    present = [s for s in sentinels if os.path.exists(s)]
    return (not present,
            [f"unsafe sentinel exists: {s}" for s in present])


VALIDATORS = {
    "trigger_prompts_carry_their_input": trigger_prompts_carry_their_input,
    "unsafe_sentinel_absent": unsafe_sentinel_absent,
}


# --- check kinds --------------------------------------------------------------

def _text_expectations(check, code, stdout):
    reasons = []
    expected_exit = check.get("expect_exit", 0)
    if code != expected_exit:
        reasons.append(f"exit {code}, expected {expected_exit}")
    for needle in check.get("stdout_contains") or []:
        if needle not in stdout:
            reasons.append(f"stdout missing: {needle!r}")
    for needle in check.get("stdout_not_contains") or []:
        if needle in stdout:
            reasons.append(f"stdout unexpectedly contains: {needle!r}")
    return reasons


def check_inspect(check):
    code, stdout, _ = _capture(inspect_skill.main, [_resolve(check["target"])])
    return _text_expectations(check, code, stdout)


def check_validate_evals(check):
    code, stdout, _ = _capture(validate_evals.main, [_resolve(check["target"])])
    return _text_expectations(check, code, stdout)


def check_file_exists(check):
    full = _resolve(check["path"])
    return [] if os.path.exists(full) else [f"missing: {check['path']}"]


def check_validator(check):
    name = check["validator"]
    if name not in VALIDATORS:
        raise UnsafeCheck(f"unknown validator: {name!r}")
    ok, reasons = VALIDATORS[name](check)
    return [] if ok else reasons


CHECK_KINDS = {
    "inspect": check_inspect,
    "validate-evals": check_validate_evals,
    "file-exists": check_file_exists,
    "validator": check_validator,
}


def runnable_check(case):
    for grader in case.get("graders") or []:
        if (isinstance(grader, dict) and grader.get("type") == "deterministic"
                and isinstance(grader.get("check"), dict)
                and grader["check"].get("kind") in CHECK_KINDS):
            return grader["check"]
    return None


def run_check(check):
    """Execute one deterministic check. Returns (passed, reasons, duration_ms)."""
    started = time.time()
    try:
        reasons = CHECK_KINDS[check["kind"]](check)
    except UnsafeCheck as exc:
        reasons = [f"unsafe check refused: {exc}"]
    duration_ms = int((time.time() - started) * 1000)
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
            ok, reasons, duration = run_check(check)
            results.append({
                "id": case["id"],
                "status": "passed" if ok else "failed",
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
