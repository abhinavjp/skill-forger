#!/usr/bin/env python3
"""Validate the canonical, heterogeneous Merge Sentinel eval corpus.

Usage:
    validate_corpus.py <eval-root> --json

The validator reads JSON data only. It does not execute evals, load YAML, use
the network, or invoke subprocesses.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


CANONICAL_FILES = (
    "cases.json",
    "quality-inputs.json",
    "quality-contracts.json",
    "quality-cases.json",
    "trigger_queries.json",
)
SPLITS = {"development", "held-out"}
QUALITY_INPUT_FIELDS = ("base", "head", "policy")
COVERAGE_AXES = (
    "code_quality",
    "security",
    "implementation_compliance",
    "evidence_coverage",
)
CASE_RECORD_KEYS = {"id", "input", "expected", "split"}
QUALITY_INPUT_RECORD_KEYS = {"id", "input"}
QUALITY_CONTRACT_RECORD_KEYS = {"id", "expected_findings"}
QUALITY_CASE_RECORD_KEYS = {"id", "input", "expected_findings"}
TRIGGER_RECORD_KEYS = {"id", "prompt", "expected", "split"}


class DuplicateJSONKey(ValueError):
    """A JSON object contains the same key more than once."""

    def __init__(self, key: str):
        super().__init__(key)
        self.key = key


def _reject_duplicate_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateJSONKey(key)
        value[key] = item
    return value


def _load_json(path: Path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream, object_pairs_hook=_reject_duplicate_keys)


def _error(errors: list[dict[str, str]], label: str, message: str) -> None:
    errors.append({"case": label, "error": f"{label}: {message}"})


def _type_name(expected) -> str:
    if isinstance(expected, tuple):
        return " or ".join(item.__name__ for item in expected)
    return expected.__name__


def _is_instance(value, expected) -> bool:
    if expected is int:
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, expected)


def _require(
    value: dict,
    key: str,
    expected,
    label: str,
    errors: list[dict[str, str]],
) -> bool:
    field_label = f"{label}.{key}"
    if key not in value:
        _error(errors, label, f"missing required field: {key}")
        return False
    if not _is_instance(value[key], expected):
        _error(errors, field_label, f"must be {_type_name(expected)}")
        return False
    return True


def _non_empty_string(
    value,
    label: str,
    errors: list[dict[str, str]],
) -> bool:
    if not isinstance(value, str) or not value.strip():
        _error(errors, label, "must be a non-empty string")
        return False
    return True


def _string_list(
    value,
    label: str,
    errors: list[dict[str, str]],
    *,
    non_empty: bool = False,
) -> bool:
    if not isinstance(value, list):
        _error(errors, label, "must be a list")
        return False
    valid = True
    for index, item in enumerate(value):
        item_label = f"{label}[{index}]"
        if not isinstance(item, str) or (non_empty and not item.strip()):
            _error(errors, item_label, "must be a non-empty string")
            valid = False
    return valid


def _string_map(
    value,
    label: str,
    errors: list[dict[str, str]],
) -> bool:
    if not isinstance(value, dict):
        _error(errors, label, "must be an object")
        return False
    valid = True
    for key, item in value.items():
        if not isinstance(key, str):
            _error(errors, label, "keys must be strings")
            valid = False
        if not isinstance(item, str):
            _error(errors, f"{label}.{key}", "must be a string")
            valid = False
    return valid


def _validate_requirements(value, label: str, errors) -> None:
    if not isinstance(value, list):
        _error(errors, label, "must be a list")
        return
    for index, requirement in enumerate(value):
        item_label = f"{label}[{index}]"
        if not isinstance(requirement, dict):
            _error(errors, item_label, "must be an object")
            continue
        _require(requirement, "id", str, item_label, errors)
        _require(requirement, "status", str, item_label, errors)


def _validate_input_fixture(value, label: str, errors) -> None:
    if not isinstance(value, dict):
        _error(errors, label, "fixture must be an object")
        return

    required = {
        "request": str,
        "requirements": list,
        "base_files": dict,
        "head_files": dict,
        "diff_metadata": dict,
        "prior_findings": list,
        "discussions": list,
        "capabilities": dict,
        "authority": (str, list),
    }
    for key, expected in required.items():
        _require(value, key, expected, label, errors)

    if isinstance(value.get("base_files"), dict):
        _string_map(value["base_files"], f"{label}.base_files", errors)
    if isinstance(value.get("head_files"), dict):
        _string_map(value["head_files"], f"{label}.head_files", errors)
    if isinstance(value.get("requirements"), list):
        _validate_requirements(value["requirements"], f"{label}.requirements", errors)
    if isinstance(value.get("prior_findings"), list):
        _string_list(value["prior_findings"], f"{label}.prior_findings", errors)

    diff = value.get("diff_metadata")
    if isinstance(diff, dict):
        _require(diff, "base_sha", str, f"{label}.diff_metadata", errors)
        _require(diff, "head_sha", str, f"{label}.diff_metadata", errors)
        for key in ("truncated", "head_drift"):
            if key in diff:
                _require(diff, key, bool, f"{label}.diff_metadata", errors)

    capabilities = value.get("capabilities")
    if isinstance(capabilities, dict):
        for key in ("mcp", "api"):
            if _require(capabilities, key, list, f"{label}.capabilities", errors):
                _string_list(capabilities[key], f"{label}.capabilities.{key}", errors)

    authority = value.get("authority")
    if isinstance(authority, list):
        _string_list(authority, f"{label}.authority", errors, non_empty=True)

    discussions = value.get("discussions")
    if isinstance(discussions, list):
        for index, discussion in enumerate(discussions):
            discussion_label = f"{label}.discussions[{index}]"
            if isinstance(discussion, str):
                continue
            if not isinstance(discussion, dict):
                _error(errors, discussion_label, "must be a string or object")
                continue
            for key in (
                "id", "anchor_file", "status", "previous_status",
                "developer_reply", "last_updated",
            ):
                _require(discussion, key, str, discussion_label, errors)

    for key in ("context_files", "renamed_files"):
        if key in value:
            _string_map(value[key], f"{label}.{key}", errors)
    if "components" in value:
        components = value["components"]
        if not isinstance(components, dict):
            _error(errors, f"{label}.components", "must be an object")
        else:
            for key, paths in components.items():
                _string_list(paths, f"{label}.components.{key}", errors, non_empty=True)
    if "review_head" in value:
        _string_map(value["review_head"], f"{label}.review_head", errors)


def _validate_finding(value, label: str, errors) -> None:
    if not isinstance(value, dict):
        _error(errors, label, "must be an object")
        return
    for key in ("id", "severity", "fingerprint"):
        _require(value, key, str, label, errors)
    if _require(value, "equivalent_fingerprints", list, label, errors):
        _string_list(value["equivalent_fingerprints"], f"{label}.equivalent_fingerprints", errors)


def _validate_expected_fixture(value, label: str, errors) -> None:
    if not isinstance(value, dict):
        _error(errors, label, "fixture must be an object")
        return
    required = {
        "finding_ids": list,
        "findings": list,
        "discarded_ids": list,
        "requirements": list,
        "coverage": dict,
        "anchor_status": str,
        "allowed_writes": list,
        "required_warnings": list,
    }
    for key, expected in required.items():
        _require(value, key, expected, label, errors)

    for key in ("finding_ids", "discarded_ids", "allowed_writes", "required_warnings"):
        if isinstance(value.get(key), list):
            _string_list(value[key], f"{label}.{key}", errors, non_empty=True)
    if isinstance(value.get("findings"), list):
        for index, finding in enumerate(value["findings"]):
            _validate_finding(finding, f"{label}.findings[{index}]", errors)
    if isinstance(value.get("requirements"), list):
        _validate_requirements(value["requirements"], f"{label}.requirements", errors)

    coverage = value.get("coverage")
    if isinstance(coverage, dict):
        for axis in COVERAGE_AXES:
            _require(coverage, axis, str, f"{label}.coverage", errors)

    optional_types = {
        "head_changed": bool,
        "discussions_available": bool,
        "discussion_needs_verification": bool,
        "publication_rounds": int,
        "review_decision": str,
        "adversarial_posture": dict,
        "delegatable_scopes": list,
        "main_reviewer_owns": list,
        "changed_files": list,
    }
    for key, expected in optional_types.items():
        if key not in value or not _require(value, key, expected, label, errors):
            continue
        if key in {"changed_files", "main_reviewer_owns"}:
            _string_list(value[key], f"{label}.{key}", errors, non_empty=True)
        elif key == "delegatable_scopes":
            for index, scope in enumerate(value[key]):
                _string_list(scope, f"{label}.delegatable_scopes[{index}]", errors, non_empty=True)


def _load_named_json(root: Path, name: str, errors):
    path = root / name
    if not path.is_file():
        _error(errors, name, "canonical file is missing")
        return None
    try:
        return _load_json(path)
    except DuplicateJSONKey as exc:
        _error(errors, name, f"duplicate JSON key: {exc.key}")
    except (OSError, UnicodeError, json.JSONDecodeError):
        _error(errors, name, "canonical file is unreadable or invalid JSON")
    return None


def _load_fixture(root: Path, relative: str, label: str, errors):
    path = root / Path(relative)
    if not path.is_file():
        _error(errors, label, "referenced fixture file is missing")
        return None
    try:
        return _load_json(path)
    except DuplicateJSONKey as exc:
        _error(errors, label, f"duplicate JSON key: {exc.key}")
    except (OSError, UnicodeError, json.JSONDecodeError):
        _error(errors, label, "referenced fixture is unreadable or invalid JSON")
    return None


def _record(report: dict, filename: str, index: int, value) -> str:
    if isinstance(value, dict) and isinstance(value.get("id"), str) and value["id"].strip():
        identifier = value["id"]
    else:
        identifier = str(index)
    report["case_count"] += 1
    report["cases"].append({"id": identifier, "file": filename})
    return f"{filename}[{identifier}]"


def _validate_exact_record_keys(value: dict, expected: set[str], label: str, errors) -> None:
    for key in sorted(expected - set(value)):
        _error(errors, label, f"missing required field: {key}")
    for key in sorted(set(value) - expected):
        _error(errors, label, f"unexpected field: {key}")


def _validate_cases_root(root: Path, report: dict, errors) -> None:
    filename = "cases.json"
    data = _load_named_json(root, filename, errors)
    if data is None:
        return
    if not isinstance(data, list) or not data:
        _error(errors, filename, "cases must be a non-empty list")
        return

    seen_ids = set()
    for index, record in enumerate(data):
        label = _record(report, filename, index, record)
        if not isinstance(record, dict):
            _error(errors, label, "record must be an object")
            continue
        _validate_exact_record_keys(record, CASE_RECORD_KEYS, label, errors)
        case_id = record.get("id")
        valid_id = _non_empty_string(case_id, f"{label}.id", errors)
        if valid_id and case_id in seen_ids:
            _error(errors, label, "duplicate case id")
        if valid_id:
            seen_ids.add(case_id)

        split = record.get("split")
        if not isinstance(split, str) or split not in SPLITS:
            _error(errors, f"{label}.split", "must be development or held-out")
        if not valid_id:
            continue

        expected_input = f"fixtures/{case_id}/input.json"
        expected_output = f"fixtures/{case_id}/expected.json"
        input_ref = record.get("input")
        expected_ref = record.get("expected")
        input_valid = input_ref == expected_input
        expected_valid = expected_ref == expected_output
        if not input_valid:
            _error(errors, f"{label}.input", f"must be exactly {expected_input}")
        if not expected_valid:
            _error(errors, f"{label}.expected", f"must be exactly {expected_output}")
        if input_valid:
            input_value = _load_fixture(root, input_ref, f"{label}.input", errors)
            if input_value is not None:
                _validate_input_fixture(input_value, f"{case_id}/input.json", errors)
        if expected_valid:
            expected_value = _load_fixture(root, expected_ref, f"{label}.expected", errors)
            if expected_value is not None:
                _validate_expected_fixture(expected_value, f"{case_id}/expected.json", errors)


def _quality_root(data, filename: str, errors):
    if not isinstance(data, dict):
        _error(errors, filename, "top level must be an object with only cases")
        return None
    if set(data) != {"cases"}:
        _error(errors, filename, "top level must contain exactly cases")
        return None
    cases = data["cases"]
    if not isinstance(cases, list) or not cases:
        _error(errors, filename, "cases must be a non-empty list")
        return None
    return cases


def _validate_quality_input_payload(value: dict, label: str, errors) -> bool:
    if not isinstance(value, dict):
        _error(errors, label, "input must be an object")
        return False
    valid = True
    for key in QUALITY_INPUT_FIELDS:
        if key not in value:
            _error(errors, label, f"missing required field: {key}")
            valid = False
        elif not _non_empty_string(value[key], f"{label}.{key}", errors):
            valid = False
    if "requirement" in value and not isinstance(value["requirement"], str):
        _error(errors, f"{label}.requirement", "must be a string")
        valid = False
    return valid


def _validate_quality_inputs(root: Path, report: dict, errors):
    filename = "quality-inputs.json"
    data = _load_named_json(root, filename, errors)
    if data is None:
        return [], {}
    records = _quality_root(data, filename, errors)
    if records is None:
        return [], {}
    ids = []
    by_id = {}
    for index, record in enumerate(records):
        label = _record(report, filename, index, record)
        if not isinstance(record, dict):
            _error(errors, label, "record must be an object")
            continue
        for key in sorted(QUALITY_INPUT_RECORD_KEYS - set(record)):
            _error(errors, label, f"missing required field: {key}")
        case_id = record.get("id")
        valid_id = _non_empty_string(case_id, f"{label}.id", errors)
        if valid_id and case_id in by_id:
            _error(errors, label, "duplicate case id")
        if valid_id:
            ids.append(case_id)
        payload = record.get("input")
        if _validate_quality_input_payload(payload, f"{label}.input", errors) and valid_id:
            by_id[case_id] = payload
    return ids, by_id


def _validate_quality_contracts(root: Path, report: dict, errors):
    filename = "quality-contracts.json"
    data = _load_named_json(root, filename, errors)
    if data is None:
        return [], {}
    records = _quality_root(data, filename, errors)
    if records is None:
        return [], {}
    ids = []
    by_id = {}
    for index, record in enumerate(records):
        label = _record(report, filename, index, record)
        if not isinstance(record, dict):
            _error(errors, label, "record must be an object")
            continue
        for key in sorted(QUALITY_CONTRACT_RECORD_KEYS - set(record)):
            _error(errors, label, f"missing required field: {key}")
        case_id = record.get("id")
        valid_id = _non_empty_string(case_id, f"{label}.id", errors)
        if valid_id and case_id in by_id:
            _error(errors, label, "duplicate case id")
        if valid_id:
            ids.append(case_id)
        findings = record.get("expected_findings")
        if not _string_list(findings, f"{label}.expected_findings", errors, non_empty=True):
            continue
        if len(findings) != len(set(findings)):
            _error(errors, f"{label}.expected_findings", "finding ids must be unique")
        if valid_id:
            by_id[case_id] = findings
    return ids, by_id


def _validate_quality_cases(root: Path, report: dict, errors):
    filename = "quality-cases.json"
    data = _load_named_json(root, filename, errors)
    if data is None:
        return [], []
    records = _quality_root(data, filename, errors)
    if records is None:
        return [], []
    ids = []
    validated = []
    seen = set()
    for index, record in enumerate(records):
        label = _record(report, filename, index, record)
        if not isinstance(record, dict):
            _error(errors, label, "record must be an object")
            continue
        for key in sorted(QUALITY_CASE_RECORD_KEYS - set(record)):
            _error(errors, label, f"missing required field: {key}")
        case_id = record.get("id")
        valid_id = _non_empty_string(case_id, f"{label}.id", errors)
        if valid_id and case_id in seen:
            _error(errors, label, "duplicate case id")
        if valid_id:
            seen.add(case_id)
            ids.append(case_id)
        payload_valid = _validate_quality_input_payload(
            record.get("input"), f"{label}.input", errors
        )
        findings = record.get("expected_findings")
        findings_valid = _string_list(
            findings, f"{label}.expected_findings", errors, non_empty=True
        )
        if valid_id and payload_valid and findings_valid:
            validated.append(record)
    return ids, validated


def _validate_quality_cross_file(
    input_ids,
    inputs,
    contract_ids,
    contracts,
    case_ids,
    cases,
    errors,
) -> None:
    id_lists = (
        ("quality-inputs.json", input_ids),
        ("quality-contracts.json", contract_ids),
        ("quality-cases.json", case_ids),
    )
    for filename, ids in id_lists:
        if ids != input_ids:
            _error(errors, filename, "ordered IDs must match quality-inputs.json")

    if not (input_ids == contract_ids == case_ids):
        return
    merged = [
        {
            "id": case_id,
            "input": inputs[case_id],
            "expected_findings": contracts[case_id],
        }
        for case_id in input_ids
        if case_id in inputs and case_id in contracts
    ]
    if len(merged) != len(cases):
        _error(errors, "quality-cases.json", "records do not match quality corpus")
        return
    for actual, expected in zip(cases, merged):
        if actual != expected:
            case_id = actual.get("id", expected.get("id", "unknown"))
            _error(errors, f"quality-cases.json[{case_id}]", "does not equal merged input and contract")


def _validate_trigger_root(root: Path, report: dict, errors) -> None:
    filename = "trigger_queries.json"
    data = _load_named_json(root, filename, errors)
    if data is None:
        return
    if not isinstance(data, list) or not data:
        _error(errors, filename, "cases must be a non-empty list")
        return
    seen_ids = set()
    for index, record in enumerate(data):
        label = _record(report, filename, index, record)
        if not isinstance(record, dict):
            _error(errors, label, "record must be an object")
            continue
        _validate_exact_record_keys(record, TRIGGER_RECORD_KEYS, label, errors)
        case_id = record.get("id")
        if _non_empty_string(case_id, f"{label}.id", errors):
            if case_id in seen_ids:
                _error(errors, label, "duplicate case id")
            seen_ids.add(case_id)
        prompt = record.get("prompt")
        _non_empty_string(prompt, f"{label}.prompt", errors)
        if not isinstance(record.get("expected"), bool):
            _error(errors, f"{label}.expected", "must be a boolean")
        if record.get("split") not in SPLITS:
            _error(errors, f"{label}.split", "must be development or held-out")


def validate_paths(eval_root: Path) -> dict:
    """Return the shared package-validator report for one canonical corpus."""
    errors: list[dict[str, str]] = []
    report = {
        "files": [str(eval_root / name) for name in CANONICAL_FILES],
        "case_count": 0,
        "cases": [],
        "errors": errors,
    }
    _validate_cases_root(eval_root, report, errors)
    input_ids, inputs = _validate_quality_inputs(eval_root, report, errors)
    contract_ids, contracts = _validate_quality_contracts(eval_root, report, errors)
    case_ids, cases = _validate_quality_cases(eval_root, report, errors)
    _validate_quality_cross_file(
        input_ids, inputs, contract_ids, contracts, case_ids, cases, errors
    )
    _validate_trigger_root(eval_root, report, errors)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("eval_root", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        valid_root = args.eval_root.is_dir()
    except OSError:
        valid_root = False
    if not valid_root:
        print("error: evaluation root is not a directory", file=sys.stderr)
        return 2

    report = validate_paths(args.eval_root)
    print(json.dumps(report, indent=2))
    return 0 if report["case_count"] > 0 and not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
