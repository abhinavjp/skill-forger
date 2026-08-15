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

Structured facts only: this validates schema shape, enum values, grader/check
structure and fixture reachability. It makes no judgement about eval quality or
coverage.

Trust boundary: eval files are data, not code. A deterministic grader names a
`check.kind` from a fixed vocabulary that trusted runner code implements; it
cannot carry a command line. A case that supplies `check.command` is rejected
here, so an untrusted corpus cannot reach `subprocess` through the runner.
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
GRADER_TYPES = {"deterministic", "host-routing", "process", "llm-judge",
                "human"}
BUDGET_KEYS = {"tokens", "duration_ms", "tool_calls", "commands"}

# Deterministic check vocabulary. Each kind maps to a trusted implementation in
# evals/run_static_evals.py; adding a kind is a code change, not a data change.
CHECK_KINDS = {
    # (required fields, optional fields)
    "inspect": ({"target"},
                {"expect_exit", "stdout_contains", "stdout_not_contains"}),
    "validate-evals": ({"target"},
                       {"expect_exit", "stdout_contains",
                        "stdout_not_contains"}),
    "file-exists": ({"path"}, set()),
    "validator": ({"validator"}, set()),
}
PATH_FIELDS = {"target", "path"}
STRING_LIST_FIELDS = {"stdout_contains", "stdout_not_contains"}

COMPETITION_POLICIES = {"skill-engineer-wins", "competitor-wins", "either",
                        "coactivation"}


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


def _contained(rel):
    """True if `rel` is a relative path that stays inside its root."""
    if not isinstance(rel, str) or not rel:
        return False
    if os.path.isabs(rel) or rel.startswith("\\") or rel[1:3] in (":/", ":\\"):
        return False
    normalized = os.path.normpath(rel).replace(os.sep, "/")
    return not (normalized == ".." or normalized.startswith("../"))


def _check_assertion_block(block, label, name, errors):
    if block is None:
        return
    if not isinstance(block, dict):
        _err(errors, label, f"expected.{name} must be a mapping")
        return
    assertions = block.get("assertions")
    if assertions is None:
        _err(errors, label, f"expected.{name} requires an assertions list")
    elif (not isinstance(assertions, list)
            or not all(isinstance(a, str) for a in assertions)):
        _err(errors, label,
             f"expected.{name}.assertions must be a list of strings")


def validate_check(check, label, errors):
    """Validate one deterministic grader's check block."""
    if "command" in (check if isinstance(check, dict) else {}):
        _err(errors, label,
             "check.command is not supported: deterministic checks name a "
             "check.kind implemented by trusted runner code, they do not carry "
             "commands")
        return
    if not isinstance(check, dict):
        _err(errors, label,
             "deterministic grader requires check to be a mapping with a kind")
        return
    kind = check.get("kind")
    if kind not in CHECK_KINDS:
        _err(errors, label,
             f"check.kind must be one of {sorted(CHECK_KINDS)}")
        return
    required, optional = CHECK_KINDS[kind]
    for field in required:
        if not check.get(field):
            _err(errors, label, f"check kind {kind!r} requires {field!r}")
    for field in check:
        if field != "kind" and field not in required and field not in optional:
            _err(errors, label,
                 f"unknown field {field!r} for check kind {kind!r}")
    for field in PATH_FIELDS & set(check):
        if not _contained(check[field]):
            _err(errors, label,
                 f"check.{field} must be a relative path inside the package: "
                 f"{check[field]!r}")
    for field in STRING_LIST_FIELDS & set(check):
        value = check[field]
        if (not isinstance(value, list)
                or not all(isinstance(v, str) for v in value)):
            _err(errors, label, f"check.{field} must be a list of strings")
    if "expect_exit" in check and not isinstance(check["expect_exit"], int):
        _err(errors, label, "check.expect_exit must be an integer")
    if kind == "validator" and not isinstance(check.get("validator"), str):
        _err(errors, label, "check.validator must be a validator name")


def validate_graders(case, label, errors):
    graders = case.get("graders", [])
    if not isinstance(graders, list) or not graders:
        _err(errors, label, "graders must be a non-empty list")
        return
    for grader in graders:
        if not isinstance(grader, dict) or "type" not in grader:
            _err(errors, label, "each grader needs a type")
            continue
        gtype = grader["type"]
        if gtype not in GRADER_TYPES:
            _err(errors, label,
                 f"grader type must be one of {sorted(GRADER_TYPES)}")
        elif gtype == "llm-judge" and not grader.get("rubric"):
            _err(errors, label, "llm-judge grader requires a rubric")
        elif gtype == "deterministic":
            validate_check(grader.get("check"), label, errors)
        elif gtype == "host-routing":
            check = grader.get("check")
            if not isinstance(check, dict):
                _err(errors, label,
                     "host-routing grader requires a check mapping")
                continue
            if not isinstance(check.get("selected_skill"), str):
                _err(errors, label,
                     "host-routing check requires selected_skill")
            if not isinstance(check.get("selected"), bool):
                _err(errors, label,
                     "host-routing check requires selected: true|false")

    if case.get("kind") == "trigger":
        has_routing = any(isinstance(g, dict) and g.get("type") == "host-routing"
                          for g in graders)
        if not has_routing:
            _err(errors, label,
                 "trigger case requires a host-routing grader naming the "
                 "Skill whose selection is asserted")


def validate_competition(case, label, errors):
    competition = case.get("competition")
    if case.get("category") == "competing-skill" and competition is None:
        _err(errors, label,
             "competing-skill case requires a competition block declaring "
             "required_candidates and expected_policy")
        return
    if competition is None:
        return
    if not isinstance(competition, dict):
        _err(errors, label, "competition must be a mapping")
        return
    candidates = competition.get("required_candidates")
    if (not isinstance(candidates, list) or not candidates
            or not all(isinstance(c, str) for c in candidates)):
        _err(errors, label,
             "competition.required_candidates must be a non-empty list of "
             "Skill names")
    policy = competition.get("expected_policy")
    if policy not in COMPETITION_POLICIES:
        _err(errors, label,
             f"competition.expected_policy must be one of "
             f"{sorted(COMPETITION_POLICIES)}")


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
        _check_assertion_block(expected.get("outcome"), label, "outcome",
                               errors)
        _check_assertion_block(expected.get("state"), label, "state", errors)
        process = expected.get("process")
        if process is not None:
            if not isinstance(process, dict):
                _err(errors, label, "expected.process must be a mapping")
            else:
                for key in ("required", "forbidden"):
                    value = process.get(key)
                    if value is None:
                        continue
                    if (not isinstance(value, list)
                            or not all(isinstance(v, str) for v in value)):
                        _err(errors, label,
                             f"expected.process.{key} must be a list of "
                             "strings")

    validate_graders(case, label, errors)
    validate_competition(case, label, errors)

    setup = case.get("setup")
    if setup is not None:
        if not isinstance(setup, list):
            _err(errors, label, "setup must be a list of harness steps")
        else:
            for step in setup:
                if not isinstance(step, str):
                    _err(errors, label,
                         "setup steps must be strings describing state the "
                         "harness applies")

    platforms = case.get("platforms")
    if platforms is not None:
        if not isinstance(platforms, dict):
            _err(errors, label, "platforms must be a mapping")
        else:
            for key in ("required", "optional"):
                value = platforms.get(key)
                if value is None:
                    continue
                if (not isinstance(value, list)
                        or not all(isinstance(v, str) for v in value)):
                    _err(errors, label,
                         f"platforms.{key} must be a list of host names")
            for key in platforms:
                if key not in ("required", "optional"):
                    _err(errors, label, f"unknown platforms key: {key}")

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
        if not _contained(fixture):
            _err(errors, label,
                 f"fixture path must stay inside the case directory: "
                 f"{fixture!r}")
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
