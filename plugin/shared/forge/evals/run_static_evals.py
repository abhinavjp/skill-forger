#!/usr/bin/env python3
"""Run Forge's trusted deterministic evaluation slice.

The existing version-1 evaluator remains the corpus authority.  This module
first validates each selected eval root with it, then reports every ordinary
v1 host/model case as non-passing.  An optional, v1-compatible ``static``
wrapper may appear on a case for a data-only deterministic assertion:

    "static": {
      "kind": "file-exists",
      "fixture": "fixtures/example.json",
      "result": {"status": "passed"}
    }

The enclosing case still carries the normal required v1 fields and graders;
the wrapper supplements rather than replaces the v1 contract.

``result`` is the expected outcome of the named trusted validator.  A failed
expected result must declare one of the stable classifications below.  Fixtures
are relative to the case file and cannot leave the selected eval root.  The
wrapper deliberately has no command, program, import, or callable field.

Only the five named validators in ``VALIDATOR_KINDS`` are implemented.  This
is a small regression runner, not a general evaluation framework.  It never
spawns a process or executes corpus-provided content.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath


HERE = Path(__file__).resolve().parent
FORGE_ROOT = HERE.parent
# The plugin root is FORGE_ROOT.parents[1] in both the repository tree
# (``<repo>/plugin``) and an installed plugin tree (``<install-root>``), so this
# single candidate covers both layouts.  ``VALIDATOR_PATHS`` stays a tuple so a
# future genuinely-distinct candidate can be added without changing callers.
VALIDATOR_PATH = FORGE_ROOT.parents[1] / "skills" / "skill-engineer" / "scripts" / "validate_evals.py"
VALIDATOR_PATHS = (VALIDATOR_PATH,)
WORKFLOW_STATE_PATH = FORGE_ROOT / "scripts" / "workflow_state.py"

VALIDATOR_KINDS = {
    "file-exists",
    "artifact-shape",
    "workflow-transition",
    "normalization",
    "adapter-parity",
}
RESULT_STATUSES = {"passed", "failed", "skipped", "unmeasured"}
FAILURE_CLASSIFICATIONS = {"assertion", "capability", "corpus", "fixture", "security"}
NONSTATIC_GRADER_CAPABILITIES = {
    "host-routing": "host-routing",
    "llm-judge": "llm-judge",
    "process": "process",
    "human": "human",
}


class CorpusError(ValueError):
    """The selected corpus is malformed or crosses the data trust boundary."""


_V1_VALIDATOR_MODULE = None


def _load_v1_validator():
    global _V1_VALIDATOR_MODULE
    if _V1_VALIDATOR_MODULE is not None:
        return _V1_VALIDATOR_MODULE
    validator_path = next(
        (path for path in dict.fromkeys((VALIDATOR_PATH, *VALIDATOR_PATHS)) if path.is_file()),
        None,
    )
    if validator_path is None:
        raise CorpusError("existing v1 validator cannot be loaded")
    spec = importlib.util.spec_from_file_location("forge_v1_validate_evals", validator_path)
    if spec is None or spec.loader is None:
        raise CorpusError("existing v1 validator cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _V1_VALIDATOR_MODULE = module
    return _V1_VALIDATOR_MODULE


_WORKFLOW_STATE_MODULE = None


def _load_workflow_state():
    global _WORKFLOW_STATE_MODULE
    if _WORKFLOW_STATE_MODULE is not None:
        return _WORKFLOW_STATE_MODULE
    if not WORKFLOW_STATE_PATH.is_file():
        raise CorpusError("shared workflow state module cannot be loaded")
    spec = importlib.util.spec_from_file_location("forge_workflow_state", WORKFLOW_STATE_PATH)
    if spec is None or spec.loader is None:
        raise CorpusError("shared workflow state module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _WORKFLOW_STATE_MODULE = module
    return module


def _contains_command(value):
    if isinstance(value, dict):
        return "command" in value or any(_contains_command(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_command(item) for item in value)
    return False


def _safe_path(root, base, value):
    if not isinstance(value, str) or not value:
        raise CorpusError("fixture reference must be a non-empty relative path")
    if PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute():
        raise CorpusError("fixture path must be relative to the eval root: {!r}".format(value))
    root = root.resolve()
    candidate = (base / value).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise CorpusError("fixture path escapes the eval root: {!r}".format(value))
    return candidate


def _read_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CorpusError("unreadable JSON fixture {}: {}".format(path.name, exc))
    return value


def _load_fixture_json(root, fixture_directory, filename):
    """Load one contained, regular JSON fixture child with no command data."""
    path = _safe_path(root, fixture_directory, filename)
    raw_path = fixture_directory / filename
    if raw_path.is_symlink() or not path.is_file():
        raise CorpusError("fixture JSON child must be a regular file: {}".format(filename))
    data = _read_json(path)
    if _contains_command(data):
        raise CorpusError("command fields are forbidden in fixture JSON: {}".format(filename))
    return data


def _validate_fixture_directory(root, directory):
    """Reject unsafe children and command-bearing JSON in a fixture directory."""
    for raw_child in sorted(directory.iterdir(), key=lambda entry: entry.name):
        child = _safe_path(root, directory, raw_child.name)
        if raw_child.is_symlink():
            raise CorpusError("fixture child must not be a symlink: {}".format(raw_child.name))
        if child.is_dir():
            _validate_fixture_directory(root, child)
        elif child.is_file():
            if child.suffix.lower() == ".json":
                _load_fixture_json(root, child.parent, child.name)
        else:
            raise CorpusError("fixture child is not a regular file or directory: {}".format(child.name))


def _validate_declared_fixture(root, base, fixture):
    path = _safe_path(root, base, fixture)
    raw_path = base / fixture
    if raw_path.is_symlink():
        raise CorpusError("fixture reference must not be a symlink: {}".format(fixture))
    if path.is_dir():
        _validate_fixture_directory(root, path)
    elif path.is_file():
        if path.suffix.lower() == ".json":
            _load_fixture_json(root, base, fixture)
    else:
        raise CorpusError("missing fixture: {}".format(fixture))
    return path


def _validate_expected_result(result):
    if not isinstance(result, dict) or set(result) - {"status", "classification"}:
        raise CorpusError("static result must contain only status and classification")
    status = result.get("status")
    if status not in {"passed", "failed"}:
        raise CorpusError("static result.status must be passed or failed")
    classification = result.get("classification")
    if status == "failed" and classification not in FAILURE_CLASSIFICATIONS:
        raise CorpusError("failed static result requires an allowed classification")
    if status == "passed" and classification is not None:
        raise CorpusError("passed static result must not carry a classification")


def _check_file_exists(check, _root, base):
    path = _safe_path(_root, base, check.get("fixture"))
    if not path.exists():
        raise CorpusError("missing fixture: {}".format(check["fixture"]))
    return True, ""


def _check_artifact_shape(check, root, base):
    required = check.get("required")
    if not isinstance(required, dict) or not required:
        raise CorpusError("artifact-shape requires a non-empty required mapping")
    data = _load_fixture_json(root, base, check.get("fixture"))
    if not isinstance(data, dict):
        return False, "fixture root is not an object"
    type_map = {
        "object": dict,
        "array": list,
        "string": str,
        "boolean": bool,
        "number": (int, float),
    }
    for key in sorted(required):
        expected_type = required[key]
        if expected_type not in type_map:
            raise CorpusError("artifact-shape has unknown type {!r}".format(expected_type))
        value = data.get(key)
        if key not in data or (isinstance(value, bool) and expected_type == "number") or not isinstance(value, type_map[expected_type]):
            return False, "missing or invalid {}".format(key)
    return True, ""


def _check_workflow_transition(check, _root, _base):
    state = check.get("state")
    target = check.get("target")
    expected_allowed = check.get("expected_allowed")
    if not isinstance(state, dict) or not isinstance(target, str) or not isinstance(expected_allowed, bool):
        raise CorpusError("workflow-transition requires state, target, and expected_allowed")
    before = copy.deepcopy(state)
    decision = _load_workflow_state().can_enter_stage(
        state, target, check.get("approval_policy")
    )
    if state != before:
        return False, "workflow transition mutated its input state"
    if not isinstance(decision, dict) or not isinstance(decision.get("allowed"), bool):
        raise CorpusError("workflow-transition returned a malformed decision")
    if decision["allowed"] != expected_allowed:
        return False, "allowed was {}, expected {}".format(decision["allowed"], expected_allowed)
    expected_code = check.get("expected_code")
    if expected_code is not None and decision.get("code") != expected_code:
        return False, "code was {!r}, expected {!r}".format(decision.get("code"), expected_code)
    if check.get("require_read_only") is True and decision.get("read_only") is not True:
        return False, "blocked transition was not read-only"
    return True, ""


def _check_normalization(check, _root, _base):
    source = check.get("source")
    normalized = check.get("normalized")
    if not isinstance(source, str) or not isinstance(normalized, str):
        raise CorpusError("normalization requires string source and normalized values")
    actual = _load_workflow_state().normalize_markdown(source)
    return actual == normalized, "normalization did not match expected value"


def _policy_lists(policy):
    if not isinstance(policy, dict):
        return None
    result = {}
    for stage in ("planning", "implementation"):
        configured = policy.get(stage)
        allowed = configured.get("approvers") if isinstance(configured, dict) else configured
        if not isinstance(allowed, list) or not allowed or not all(isinstance(actor, str) for actor in allowed):
            return None
        result[stage] = allowed
    return result


def _check_adapter_parity(check, root, base):
    fixture = _safe_path(root, base, check.get("fixture"))
    if not fixture.is_dir():
        raise CorpusError("adapter-parity fixture must be a directory")
    _validate_fixture_directory(root, fixture)
    input_data = _load_fixture_json(root, fixture, "input.json")
    expected = _load_fixture_json(root, fixture, "expected.json")
    if not isinstance(input_data, dict) or not isinstance(expected, dict):
        raise CorpusError("adapter-parity fixture files must be JSON objects")
    locations = input_data.get("artifact_location_conventions")
    expected_locations = expected.get("adapter_handling", {}).get("preserve_artifact_locations")
    if locations != expected_locations:
        return False, "artifact location conventions were not preserved"
    delivery = input_data.get("request", {}).get("delivery_operation")
    refused = expected.get("adapter_handling", {}).get("refused_delivery_operation")
    if delivery != refused or delivery in input_data.get("authorized_delivery_operations", []):
        return False, "unauthorized delivery operation was not refused"
    tree = input_data.get("okf_provider", {}).get("tree", [])
    leaves = {entry.get("path") for entry in tree if isinstance(entry, dict) and entry.get("leaf") is True}
    requested = input_data.get("okf_provider", {}).get("requested_references", [])
    selected = expected.get("knowledge_handling", {}).get("selected_leaf_paths")
    if not isinstance(requested, list) or selected != requested or not set(requested) <= leaves:
        return False, "selected knowledge is not the requested leaf set"
    unavailable = input_data.get("okf_provider", {}).get("unavailable_knowledge", [])
    expected_unavailable = expected.get("knowledge_handling", {}).get("unavailable_knowledge", [])
    for item in unavailable:
        if not isinstance(item, dict) or not any(
            isinstance(other, dict)
            and other.get("path") == item.get("path")
            and other.get("reason") == item.get("reason")
            and other.get("status") == "UNMEASURED"
            for other in expected_unavailable
        ):
            return False, "unavailable knowledge was not reported as UNMEASURED"
    policy = _policy_lists(input_data.get("approval_policy"))
    if policy is None:
        return False, "adapter lacks designated approver policy"
    approval_state = check.get("approval_state")
    if approval_state is not None:
        target = check.get("target")
        expected_allowed = check.get("expected_allowed")
        if not isinstance(target, str) or not isinstance(expected_allowed, bool):
            raise CorpusError("adapter approval_state requires target and expected_allowed")
        decision = _load_workflow_state().can_enter_stage(approval_state, target, policy)
        if decision.get("allowed") != expected_allowed:
            return False, "adapter approver policy did not enforce the expected gate"
    return True, ""


CHECKS = {
    "file-exists": _check_file_exists,
    "artifact-shape": _check_artifact_shape,
    "workflow-transition": _check_workflow_transition,
    "normalization": _check_normalization,
    "adapter-parity": _check_adapter_parity,
}


def _verify_fixture_references(case, root, base):
    fixtures = case.get("fixtures", [])
    if fixtures is None:
        return
    if not isinstance(fixtures, list):
        raise CorpusError("fixtures must be a list")
    for fixture in fixtures:
        _validate_declared_fixture(root, base, fixture)


def _bucketed(results):
    buckets = {status: [] for status in sorted(RESULT_STATUSES)}
    for result in results:
        status = result.get("status")
        if status not in buckets:
            raise CorpusError("runner produced malformed result status")
        if status == "failed" and result.get("classification") not in FAILURE_CLASSIFICATIONS:
            raise CorpusError("runner produced an unclassified failure")
        buckets[status].append(result)
    for values in buckets.values():
        values.sort(key=lambda item: (item["id"], item.get("source", "")))
    summary = {status: len(buckets[status]) for status in ("passed", "failed", "skipped", "unmeasured")}
    summary["total"] = sum(summary.values())
    return {"summary": summary, "results": buckets}


def evaluate_cases(cases, root, capabilities=None, source=None):
    """Evaluate JSON-compatible case mappings without loading or executing code."""
    if not isinstance(cases, list):
        raise CorpusError("cases must be a list")
    root = Path(root).resolve()
    capabilities = set(capabilities or ())
    source = Path(source).resolve() if source else root / "<memory>"
    base = source.parent if source.name != "<memory>" else root
    source_label = "<memory>"
    if source.name != "<memory>":
        try:
            source_label = source.relative_to(root).as_posix()
        except ValueError:
            raise CorpusError("case source escapes the eval root")
    results = []
    for case in sorted(cases, key=lambda item: item.get("id", "") if isinstance(item, dict) else ""):
        if not isinstance(case, dict) or not isinstance(case.get("id"), str) or not case["id"]:
            raise CorpusError("case requires a non-empty string id")
        if _contains_command(case):
            raise CorpusError("command fields are forbidden in eval data")
        _verify_fixture_references(case, root, base)
        static = case.get("static")
        if static is not None:
            if not isinstance(static, dict):
                raise CorpusError("static wrapper must be an object")
            kind = static.get("kind")
            if kind not in VALIDATOR_KINDS:
                raise CorpusError("unknown trusted validator kind: {!r}".format(kind))
            _validate_expected_result(static.get("result"))
            passed, reason = CHECKS[kind](static, root, base)
            expected_status = static["result"]["status"]
            actual_status = "passed" if passed else "failed"
            if actual_status == expected_status:
                results.append({"id": case["id"], "status": "passed", "source": source_label})
            else:
                results.append({
                    "id": case["id"], "status": "failed", "source": source_label,
                    "classification": "assertion", "reason": reason or "static result did not match expectation",
                })
            continue
        graders = case.get("graders", [])
        required = sorted({
            NONSTATIC_GRADER_CAPABILITIES[grader.get("type")]
            for grader in graders if isinstance(grader, dict)
            and grader.get("type") in NONSTATIC_GRADER_CAPABILITIES
        })
        if not required:
            results.append({"id": case["id"], "status": "skipped", "source": source_label, "reason": "no trusted static validator"})
        elif not set(required) <= capabilities:
            missing = sorted(set(required) - capabilities)
            results.append({"id": case["id"], "status": "skipped", "source": source_label, "reason": "unavailable capabilities: {}".format(", ".join(missing))})
        else:
            results.append({"id": case["id"], "status": "unmeasured", "source": source_label, "reason": "declared capability requires a host/model runner"})
    return _bucketed(results)


def run_eval_roots(eval_roots, capabilities=None):
    """Validate selected v1 roots, then statically classify their cases."""
    if not eval_roots:
        raise CorpusError("at least one eval root is required")
    validator = _load_v1_validator()
    all_results = []
    for raw_root in sorted({str(Path(path).resolve()) for path in eval_roots}):
        root = Path(raw_root)
        try:
            report = validator.validate_paths([str(root)])
        except RuntimeError as exc:
            raise CorpusError(str(exc))
        if report.get("errors"):
            raise CorpusError("v1 corpus validation failed: {}".format(report["errors"]))
        for source_name in sorted(report.get("files", [])):
            source = Path(source_name).resolve()
            data = _read_json(source)
            cases = data if isinstance(data, list) else [data]
            evaluated = evaluate_cases(cases, root, capabilities, source)
            for bucket in evaluated["results"].values():
                all_results.extend(bucket)
    return _bucketed(all_results)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evals", action="append", help="shared or stage eval root; repeatable")
    parser.add_argument("--capability", action="append", default=[], help="declared non-static capability; repeatable")
    parser.add_argument("--json", action="store_true", help="emit only deterministic JSON")
    args = parser.parse_args(argv)
    roots = args.evals or [str(HERE)]
    try:
        report = run_eval_roots(roots, args.capability)
    except CorpusError as exc:
        report = {"summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "unmeasured": 0}, "results": {"passed": [], "failed": [], "skipped": [], "unmeasured": []}, "error": str(exc)}
        if args.json:
            print(json.dumps(report, sort_keys=True))
        else:
            print("INVALID CORPUS: {}".format(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        for status in ("passed", "failed", "skipped", "unmeasured"):
            for result in report["results"][status]:
                suffix = result.get("reason", "")
                print("{} {}{}".format(status.upper(), result["id"], "  " + suffix if suffix else ""))
    return 1 if report["summary"]["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
