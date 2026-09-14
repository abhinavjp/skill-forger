#!/usr/bin/env python3
"""Run trusted deterministic checks for the forge-plan eval corpus."""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Dict, List, Optional, Set, Tuple

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
EXPECTED_SHAPE_MAPPINGS = SKILL_ROOT / "references" / "expected-shape-mappings.json"
REPO_ROOT = HERE.parents[3]
SCRIPTS = SKILL_ROOT.parent / "skill-engineer" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(HERE))
import validate_evals  # noqa: E402
from fixture_schema import (  # noqa: E402
    FixtureSchemaError,
    load_private_baseline,
    load_public_fixture,
    validate_private_baseline,
    validate_public_fixture,
)


def _text(relative: str) -> str:
    return (SKILL_ROOT / relative).read_text(encoding="utf-8")


def forge_plan_contract(_check: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    required_files = ["SKILL.md", "references/compact-mode.md", "references/detailed-mode.md", "references/execution-packet.md"]
    for relative in required_files:
        path = SKILL_ROOT / relative
        if not path.is_file():
            errors.append(f"missing reference file: {relative}")
    skill = SKILL_ROOT / "SKILL.md"
    if skill.is_file():
        skill_text = skill.read_text(encoding="utf-8")
        lines = skill_text.splitlines()
        if not lines or lines[0].strip() != "---" or not any(line.startswith("name: forge-plan") for line in lines):
            errors.append("SKILL.md frontmatter does not declare forge-plan")
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", skill_text):
            if target.startswith(("http://", "https://", "#")):
                continue
            if not (skill.parent / target).resolve().is_file():
                errors.append(f"SKILL.md broken relative reference: {target}")
        for target in ("../../shared/forge/references/workflow-contract.md",):
            if target not in skill_text:
                errors.append("SKILL.md missing shared contract pointer: {}".format(target))
        if "review or go" not in skill_text:
            errors.append("SKILL.md must stop and ask \"review or go?\" before implementation")
    return not errors, errors


def _heading_slugs(text: str) -> Set[str]:
    slugs: Set[str] = set()
    for line in text.splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        heading = re.sub(r"[`*_]", "", match.group(1).casefold())
        heading = re.sub(r"[^\w\s-]", "", heading)
        heading = re.sub(r"[\s-]+", "-", heading).strip("-")
        if heading:
            slugs.add(heading)
    return slugs


def _validate_clause(reference: Any, label: str, repo_root: Path, errors: List[str]) -> None:
    if not isinstance(reference, str) or "#" not in reference:
        errors.append("{} requires a repository-relative Markdown clause".format(label))
        return
    path_text, anchor = reference.split("#", 1)
    posix = PurePosixPath(path_text.replace("\\", "/"))
    windows = PureWindowsPath(path_text)
    if posix.is_absolute() or windows.is_absolute() or bool(windows.drive):
        errors.append("{} is not repository-relative: {}".format(label, reference))
        return
    path = (repo_root / path_text.replace("/", os.sep).replace("\\", os.sep)).resolve()
    try:
        path.relative_to(repo_root.resolve())
    except ValueError:
        errors.append("{} escapes the repository: {}".format(label, reference))
        return
    if not path.is_file():
        errors.append("{} does not resolve: {}".format(label, reference))
        return
    if anchor.casefold() not in _heading_slugs(path.read_text(encoding="utf-8")):
        errors.append("{} has no current heading: {}".format(label, reference))


def _mapping_record(
    record: Any,
    label: str,
    repo_root: Path,
    requirement_ids: Set[str],
    errors: List[str],
) -> None:
    if not isinstance(record, dict) or set(record) != {"authority", "clause"}:
        errors.append("{} must contain exactly authority and clause".format(label))
        return
    authority = record.get("authority")
    if not isinstance(authority, str) or not re.match(r"^REQ-\d+$", authority):
        errors.append("{} must name a current REQ authority".format(label))
    elif authority not in requirement_ids:
        errors.append("{} names an unknown current REQ authority: {}".format(label, authority))
    _validate_clause(record.get("clause"), label, repo_root, errors)


def _current_requirement_ids(repo_root: Path) -> Set[str]:
    specification = repo_root / "docs" / "specs" / "forge-plan-proportional-planning.md"
    try:
        text = specification.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return set()
    return set(re.findall(r"\bREQ-\d+\b", text))


def validate_artifact_shape_mappings(
    execution_path: Optional[Path] = None,
    repo_root: Path = REPO_ROOT,
) -> Tuple[bool, List[str]]:
    """Prove every current E-001/E-002 assertion and rubric has a live clause."""
    execution_path = execution_path or HERE / "execution.json"
    errors: List[str] = []
    try:
        data = json.loads(execution_path.read_text(encoding="utf-8"))
        expected_mappings = json.loads(EXPECTED_SHAPE_MAPPINGS.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, ["execution corpus or canonical mapping manifest is unreadable: {}".format(exc)]
    cases = data if isinstance(data, list) else [data]
    by_id = {case.get("id"): case for case in cases if isinstance(case, dict)}
    requirement_ids = _current_requirement_ids(Path(repo_root))
    if not requirement_ids:
        errors.append("Specification has no readable current REQ authorities")
    for case_id in ("FP-E-001", "FP-E-002"):
        case = by_id.get(case_id)
        if not isinstance(case, dict):
            errors.append("missing artifact-shape case {}".format(case_id))
            continue
        outcome = case.get("expected", {}).get("outcome")
        assertions = outcome.get("assertions") if isinstance(outcome, dict) else None
        graders = case.get("graders")
        rubrics = [
            grader.get("rubric")
            for grader in graders or []
            if isinstance(grader, dict) and isinstance(grader.get("rubric"), str)
        ]
        mapping = case.get("artifact_shape_mapping")
        expected_mapping = expected_mappings.get(case_id) if isinstance(expected_mappings, dict) else None
        if not isinstance(assertions, list) or not all(isinstance(item, str) for item in assertions):
            errors.append("{} has malformed outcome assertions".format(case_id))
            continue
        if not isinstance(mapping, dict) or set(mapping) != {"assertions", "rubrics"}:
            errors.append("{} must carry assertion and rubric mappings".format(case_id))
            continue
        if mapping != expected_mapping:
            errors.append("{} mappings do not exactly match the canonical mapping manifest".format(case_id))
        assertion_mapping = mapping.get("assertions")
        rubric_mapping = mapping.get("rubrics")
        if not isinstance(assertion_mapping, dict) or not isinstance(rubric_mapping, dict):
            errors.append("{} shape mappings must be objects".format(case_id))
            continue
        for assertion in assertions:
            record = assertion_mapping.get(assertion)
            if record is None:
                errors.append("{} assertion is unmapped: {}".format(case_id, assertion))
            else:
                _mapping_record(record, "{} assertion".format(case_id), Path(repo_root), requirement_ids, errors)
        if set(assertion_mapping) != set(assertions):
            errors.append("{} assertion mapping keys do not exactly match assertions".format(case_id))
        for rubric in rubrics:
            record = rubric_mapping.get(rubric)
            if record is None:
                errors.append("{} rubric is unmapped".format(case_id))
            else:
                _mapping_record(record, "{} rubric".format(case_id), Path(repo_root), requirement_ids, errors)
        if set(rubric_mapping) != set(rubrics):
            errors.append("{} rubric mapping keys do not exactly match rubrics".format(case_id))
    return not errors, errors


def inspect_behavioral_harness(
    harness_path: Optional[Path] = None,
    fixture_path: Optional[Path] = None,
    baseline_path: Optional[Path] = None,
    execution_path: Optional[Path] = None,
    repo_root: Path = REPO_ROOT,
) -> Tuple[bool, List[str]]:
    """Check only structural harness claims; never execute a runner or judge."""
    harness_path = harness_path or HERE / "run_behavioral_evals.py"
    fixture_path = fixture_path or HERE / "fixtures" / "ready-planning-context.json"
    baseline_path = baseline_path or HERE / "fixtures" / "brain-plan-scenarios.json"
    execution_path = execution_path or HERE / "execution.json"
    errors: List[str] = []
    try:
        source = harness_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError) as exc:
        return False, [f"harness parse failed: {exc}"]
    functions = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    errors.extend(
        "harness missing function: {}".format(name)
        for name in sorted({"_argv_file", "_load_fixture", "_normalize_evidence", "_finalize_assertions", "_run_role", "_run_judge", "main"} - functions)
    )
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    errors.extend(
        "harness must call {}".format(name)
        for name in ("load_public_fixture", "load_private_baseline")
        if name not in called_names
    )
    allowed_imports = {"__future__", "argparse", "ast", "fixture_schema", "json", "pathlib", "subprocess", "sys", "typing", "validate_evals"}
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
    if "load_public_fixture" not in source or "load_private_baseline" not in source:
        errors.append("harness must use the versioned public/private fixture loaders")
    if "accepted_baseline_fixture" in source:
        errors.append("harness must not accept a public baseline path")
    try:
        fixture = load_public_fixture(Path(fixture_path))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"fixture is not valid JSON: {exc}")
    except FixtureSchemaError as exc:
        errors.append(str(exc))
    if not Path(baseline_path).is_file():
        errors.append("private baseline fixture is missing")
    else:
        try:
            baseline = load_private_baseline(Path(baseline_path))
            errors.extend("private baseline: {}".format(error) for error in validate_private_baseline(baseline))
        except FixtureSchemaError as exc:
            errors.append(str(exc))

    try:
        data = json.loads(execution_path.read_text(encoding="utf-8"))
        cases = data if isinstance(data, list) else [data]
        case = next((item for item in cases if isinstance(item, dict) and item.get("id") == "FP-EX-020"), None)
        assertions = case.get("expected", {}).get("outcome", {}).get("assertions", []) if isinstance(case, dict) else []
        if not any("structural-only" in item.casefold() for item in assertions if isinstance(item, str)):
            errors.append("FP-EX-020 must declare structural-only evidence")
        if any(any(term in item.casefold() for term in ("missing host runner", "role comparison", "live trial")) for item in assertions if isinstance(item, str)):
            errors.append("FP-EX-020 contains a live behavioral claim")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append("execution corpus is not readable: {}".format(exc))
    return not errors, errors


def forge_plan_behavioral_boundary(_check: Dict[str, Any]) -> Tuple[bool, List[str]]:
    return inspect_behavioral_harness()


def forge_plan_shape_mapping(_check: Dict[str, Any]) -> Tuple[bool, List[str]]:
    return validate_artifact_shape_mappings()


VALIDATORS = {
    "forge_plan_contract": forge_plan_contract,
    "forge_plan_behavioral_boundary": forge_plan_behavioral_boundary,
    "forge_plan_shape_mapping": forge_plan_shape_mapping,
}


def main(argv: Any = None) -> int:
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
