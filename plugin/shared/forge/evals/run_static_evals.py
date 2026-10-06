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

Only the two named validators in ``VALIDATOR_KINDS`` are implemented.  This
is a small regression runner, not a general evaluation framework.  It never
spawns a process or executes corpus-provided content.
"""

from __future__ import annotations

import argparse
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

VALIDATOR_KINDS = {
    "file-exists",
    "artifact-shape",
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


CHECKS = {
    "file-exists": _check_file_exists,
    "artifact-shape": _check_artifact_shape,
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
