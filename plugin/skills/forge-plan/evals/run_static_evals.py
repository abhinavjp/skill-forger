#!/usr/bin/env python3
"""Run trusted deterministic checks for the forge-plan eval corpus."""
from __future__ import annotations

import argparse
import ast
import json
import re
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
    errors = []
    required_files = ["SKILL.md", "references/compact-mode.md", "references/detailed-mode.md", "references/execution-packet.md"]
    for relative in required_files:
        path = SKILL_ROOT / relative
        if not path.is_file():
            errors.append(f"missing reference file: {relative}")
    skill = SKILL_ROOT / "SKILL.md"
    if skill.is_file():
        lines = skill.read_text(encoding="utf-8").splitlines()
        if not lines or lines[0].strip() != "---" or not any(line.startswith("name: forge-plan") for line in lines):
            errors.append("SKILL.md frontmatter does not declare forge-plan")
        headings = {line.lstrip("#").strip() for line in lines if line.startswith("#")}
        required_headings = {"Approved-plan handoff branch", "Shared workflow", "Read-only ticket handoff", "Completion"}
        errors.extend(f"SKILL.md missing heading: {heading}" for heading in sorted(required_headings - headings))
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", skill.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "#")):
                continue
            if not (skill.parent / target).resolve().is_file():
                errors.append(f"SKILL.md broken relative reference: {target}")
    return not errors, errors


def forge_plan_behavioral_boundary(_check: dict) -> tuple[bool, list[str]]:
    errors = []
    harness_path = HERE / "run_behavioral_evals.py"
    fixture_path = HERE / "fixtures" / "approved-planning-context.json"
    try:
        tree = ast.parse(harness_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        return False, [f"harness parse failed: {exc}"]
    functions = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    errors.extend(f"harness missing function: {name}" for name in sorted({"_argv_file", "_finalize_assertions", "_run_role", "_run_judge", "main"} - functions))
    allowed_imports = {"__future__", "argparse", "ast", "json", "pathlib", "subprocess", "sys", "validate_evals"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported = [node.module.split(".")[0]] if node.module else []
        else:
            continue
        errors.extend(f"unsupported harness import: {name}" for name in imported if name not in allowed_imports)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run"]
    if not calls or any(not any(keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is False for keyword in call.keywords) for call in calls):
        errors.append("all subprocess.run calls must set shell=False")
    arguments = {node.args[0].value for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument" and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)}
    errors.extend(f"harness missing argv option: {option}" for option in ("--candidate-argv-file", "--baseline-argv-file", "--no-skill-argv-file", "--judge-argv-file") if option not in arguments)
    try:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"fixture is not valid JSON: {exc}")
    else:
        if not isinstance(fixture, dict) or not isinstance(fixture.get("authority"), list) or not isinstance(fixture.get("repository"), dict) or not isinstance(fixture.get("plan"), dict):
            errors.append("fixture schema requires authority, repository, and plan")
        for authority in fixture.get("authority", []) if isinstance(fixture, dict) else []:
            if not isinstance(authority, dict) or not all(authority.get(key) for key in ("path", "approval", "approval_hash")) or authority.get("fresh") is not True:
                errors.append("fixture authority entries require approved hash and fresh=true")
        baseline_name = fixture.get("accepted_baseline_fixture") if isinstance(fixture, dict) else None
        baseline_path = fixture_path.parent / baseline_name if isinstance(baseline_name, str) else None
        if baseline_path is None or not baseline_path.is_file():
            errors.append("accepted baseline fixture is missing")
        else:
            try:
                baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"accepted baseline fixture is invalid: {exc}")
            else:
                scenarios = baseline.get("scenarios") if isinstance(baseline, dict) else None
                if not isinstance(scenarios, list) or not scenarios or not all(isinstance(item, dict) and item.get("id") and item.get("case_id") for item in scenarios):
                    errors.append("accepted baseline fixture scenarios are malformed")
    return not errors, errors


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
