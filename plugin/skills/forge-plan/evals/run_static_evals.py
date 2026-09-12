#!/usr/bin/env python3
"""Run trusted deterministic checks for the forge-plan eval corpus."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
SCRIPTS = SKILL_ROOT.parent / "skill-engineer" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import validate_evals  # noqa: E402


def _text(relative: str) -> str:
    return (SKILL_ROOT / relative).read_text(encoding="utf-8")


def forge_plan_contract(_check: dict) -> tuple[bool, list[str]]:
    main = _text("SKILL.md")
    compact = _text("references/compact-mode.md")
    packet = _text("references/execution-packet.md")
    required = {
        "SKILL.md": (main, ("Approved-plan handoff branch", "blocked/upstream-return", "Never treat an explicit blocker", "read-only `to-tickets` handoff")),
        "references/compact-mode.md": (compact, ("unresolved material decisions block", "Do not request or record approval")),
        "references/execution-packet.md": (packet, ("not approvable", "product, architecture, scope")),
    }
    missing = [f"{path}: {needle}" for path, (text, needles) in required.items() for needle in needles if needle not in text]
    return not missing, missing


def forge_plan_behavioral_boundary(_check: dict) -> tuple[bool, list[str]]:
    harness = _text("evals/run_behavioral_evals.py")
    fixture = HERE / "fixtures" / "approved-planning-context.json"
    required = ("candidate", "baseline", "no-skill", "UNMEASURED", "subprocess.run")
    missing = [needle for needle in required if needle not in harness]
    if not fixture.is_file():
        missing.append("fixtures/approved-planning-context.json")
    return not missing, missing


VALIDATORS = {
    "forge_plan_contract": forge_plan_contract,
    "forge_plan_behavioral_boundary": forge_plan_behavioral_boundary,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evals_positional", nargs="?", type=Path)
    parser.add_argument("--evals", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    evals = args.evals or args.evals_positional or HERE
    validation = validate_evals.validate_paths([str(evals)])
    results = []
    errors = list(validation["errors"])
    for path in validation["files"]:
        data = validate_evals._load(path)
        for case in data if isinstance(data, list) else [data]:
            check = next(
                (
                    grader.get("check")
                    for grader in case.get("graders", [])
                    if grader.get("type") == "deterministic"
                ),
                None,
            )
            if not check:
                results.append({"id": case["id"], "status": "UNMEASURED", "reason": "requires host runner"})
                continue
            validator = VALIDATORS.get(check.get("validator"))
            if validator is None:
                errors.append({"case": case["id"], "error": f"unknown trusted validator: {check.get('validator')}"})
                results.append({"id": case["id"], "status": "failed"})
                continue
            ok, reasons = validator(check)
            results.append({"id": case["id"], "status": "passed" if ok else "failed", "reasons": reasons})
            if not ok:
                errors.extend({"case": case["id"], "error": reason} for reason in reasons)
    summary = {
        "runnable": sum(result["status"] in {"passed", "failed"} for result in results),
        "passed": sum(result["status"] == "passed" for result in results),
        "failed": sum(result["status"] == "failed" for result in results),
        "unmeasured": sum(result["status"] == "UNMEASURED" for result in results),
    }
    report = {
        "case_count": validation["case_count"],
        "files": validation["files"],
        "errors": errors,
        "summary": summary,
        "results": results,
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{summary['passed']}/{summary['runnable']} deterministic cases passed; {summary['unmeasured']} UNMEASURED")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
