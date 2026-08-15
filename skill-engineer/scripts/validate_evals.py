#!/usr/bin/env python3
"""Validate portable eval case files against the portable eval schema.

Usage:
    validate_evals.py <path> [<path> ...] [--json]

<path> may be an eval file (.yaml/.yml/.json) or a directory containing them.
Each file holds either a single case (mapping) or a list of cases. Directory
walks skip `fixtures/` — fixtures are case inputs, not cases; pass a fixture
file explicitly to validate it.

Exit codes:
    0  all cases valid
    1  at least one case invalid
    2  usage / unreadable input

Structured facts only: this validates schema shape, enum values and fixture
reachability. It makes no judgement about eval quality or coverage.
"""
from __future__ import annotations

import json
import os
import sys

KINDS = {"trigger", "execution"}
CATEGORIES = {
    "positive", "negative", "boundary", "adversarial", "regression",
    "paraphrase", "near-neighbour", "competing-skill", "large-input",
    "failure-injection",
}
GRADER_TYPES = {"deterministic", "process", "llm-judge", "human"}
BUDGET_KEYS = {"tokens", "duration_ms", "tool_calls", "commands"}


def _load(path):
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        return json.loads(text)
    try:
        import yaml  # optional dependency; JSON cases work without it
    except ImportError:
        raise RuntimeError(
            "PyYAML not installed; install it or use .json eval files"
        )
    return yaml.safe_load(text)


def _err(errors, case_id, msg):
    errors.append({"case": case_id, "error": msg})


def validate_case(case, path, index, errors):
    case_id = case.get("id") if isinstance(case, dict) else None
    label = f"{os.path.basename(path)}#{case_id or index}"
    if not isinstance(case, dict):
        _err(errors, label, "case is not a mapping")
        return
    if case.get("version") != 1:
        _err(errors, label, "version must be 1")
    for field in ("id", "kind", "category", "prompt"):
        if not case.get(field):
            _err(errors, label, f"missing required field: {field}")
    if case.get("kind") not in KINDS and "kind" in case:
        _err(errors, label, f"kind must be one of {sorted(KINDS)}")
    if case.get("category") not in CATEGORIES and "category" in case:
        _err(errors, label, f"category must be one of {sorted(CATEGORIES)}")

    trials = case.get("trials", 1)
    if not isinstance(trials, int) or trials < 1:
        _err(errors, label, "trials must be an integer >= 1")

    expected = case.get("expected")
    if not isinstance(expected, dict) or not expected:
        _err(errors, label, "expected must be a non-empty mapping")
    else:
        if case.get("kind") == "trigger" and "trigger" not in expected:
            _err(errors, label, "trigger case must set expected.trigger")
        if "trigger" in expected and not isinstance(expected["trigger"], bool):
            _err(errors, label, "expected.trigger must be a boolean")
        process = expected.get("process")
        if process is not None and not isinstance(process, dict):
            _err(errors, label, "expected.process must be a mapping")

    graders = case.get("graders", [])
    if not isinstance(graders, list) or not graders:
        _err(errors, label, "graders must be a non-empty list")
    else:
        for grader in graders:
            if not isinstance(grader, dict) or "type" not in grader:
                _err(errors, label, "each grader needs a type")
            elif grader["type"] not in GRADER_TYPES:
                _err(errors, label,
                     f"grader type must be one of {sorted(GRADER_TYPES)}")
            elif grader["type"] == "llm-judge" and not grader.get("rubric"):
                _err(errors, label, "llm-judge grader requires a rubric")

    budgets = case.get("budgets") or {}
    if not isinstance(budgets, dict):
        _err(errors, label, "budgets must be a mapping")
    else:
        for key in budgets:
            if key not in BUDGET_KEYS:
                _err(errors, label, f"unknown budget key: {key}")

    base = os.path.dirname(os.path.abspath(path))
    for fixture in case.get("fixtures") or []:
        if not isinstance(fixture, str):
            _err(errors, label, "fixtures entries must be paths")
            continue
        if not os.path.exists(os.path.join(base, fixture)):
            _err(errors, label, f"missing fixture: {fixture}")


def collect_files(paths):
    files = []
    for path in paths:
        if os.path.isdir(path):
            for root, dirs, names in os.walk(path):
                # fixtures/ holds inputs for cases (including intentionally
                # malformed ones), not the corpus itself. Pass a fixture file
                # explicitly to validate it.
                dirs[:] = [d for d in dirs if d != "fixtures"]
                for name in sorted(names):
                    if name.endswith((".yaml", ".yml", ".json")):
                        files.append(os.path.join(root, name))
        elif os.path.exists(path):
            files.append(path)
        else:
            raise RuntimeError(f"no such path: {path}")
    return files


def validate_paths(paths):
    """Return {files, case_count, cases, errors} for the given paths."""
    result = {"files": [], "case_count": 0, "cases": [], "errors": []}
    seen_ids = {}  # ids must be unique: results are reported and tracked by id
    for path in collect_files(paths):
        result["files"].append(path)
        try:
            data = _load(path)
        except Exception as exc:  # unreadable/unparseable file is an error
            _err(result["errors"], os.path.basename(path), f"unreadable: {exc}")
            continue
        cases = data if isinstance(data, list) else [data]
        for index, case in enumerate(cases):
            result["case_count"] += 1
            if isinstance(case, dict):
                case_id = case.get("id")
                if case_id and case_id in seen_ids:
                    _err(result["errors"], f"{os.path.basename(path)}#{case_id}",
                         f"duplicate case id (also in {seen_ids[case_id]})")
                elif case_id:
                    seen_ids[case_id] = os.path.basename(path)
                result["cases"].append({
                    "id": case.get("id"),
                    "kind": case.get("kind"),
                    "category": case.get("category"),
                    "file": path,
                })
            validate_case(case, path, index, result["errors"])
    return result


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    as_json = "--json" in argv
    if not args:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        result = validate_paths(args)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"files: {len(result['files'])}  cases: {result['case_count']}  "
              f"errors: {len(result['errors'])}")
        for error in result["errors"]:
            print(f"  {error['case']}: {error['error']}")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
