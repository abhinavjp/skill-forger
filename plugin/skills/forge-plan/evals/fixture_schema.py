#!/usr/bin/env python3
"""Versioned trust-boundary schemas for forge-plan evaluation fixtures.

The public fixture is deliberately small and allowlisted.  Expected answers,
rubrics, and accepted-baseline material belong to the trusted judge/control
plane and are never valid public runner-fixture fields.
"""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Dict, List


PUBLIC_FIXTURE_SCHEMA_VERSION = 1
PUBLIC_FIXTURE_KEYS = {
    "schema_version",
    "authority",
    "repository",
    "plan",
}
AUTHORITY_KEYS = {"path", "fresh"}
REPOSITORY_KEYS = {"state", "changed_paths"}
PLAN_KEYS = {"ticket_ready"}

# These are rejected case-insensitively and with common separator changes at
# every nesting level, before the allowlist is checked.  The explicit names
# make the oracle boundary auditable even if the public schema grows later.
FORBIDDEN_ORACLE_KEYS = {
    "accepted_baseline",
    "accepted_baseline_fixture",
    "answer",
    "answer_key",
    "answers",
    "control",
    "expected",
    "gold",
    "gold_answer",
    "grader",
    "graders",
    "ground_truth",
    "judge",
    "known_answer",
    "known_answer_material",
    "known_answers",
    "oracle",
    "private",
    "reference_answer",
    "rubric",
}


class FixtureSchemaError(ValueError):
    """The public or private evaluation fixture is malformed."""


def _normalized_key(value: str) -> str:
    return value.casefold().replace("-", "_").replace(" ", "_")


def _scan_forbidden(value: Any, location: str, errors: List[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str) and _normalized_key(key) in FORBIDDEN_ORACLE_KEYS:
                errors.append("{} contains forbidden oracle key {!r}".format(location, key))
            _scan_forbidden(child, "{}.{}".format(location, key), errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_forbidden(child, "{}[{}]".format(location, index), errors)


def _require_exact_keys(value: Any, allowed: set, location: str, errors: List[str]) -> bool:
    if not isinstance(value, dict):
        errors.append("{} must be an object".format(location))
        return False
    unknown = sorted(set(value) - allowed)
    if unknown:
        errors.append("{} has unknown fields: {}".format(location, unknown))
    return not unknown


def _safe_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or "\x00" in value:
        return False
    posix = PurePosixPath(value.replace("\\", "/"))
    windows = PureWindowsPath(value)
    if posix.is_absolute() or windows.is_absolute() or bool(windows.drive):
        return False
    return ".." not in posix.parts and all(part not in {"", "."} for part in posix.parts)


def validate_public_fixture(value: Any) -> List[str]:
    """Return all schema violations for data sent to a runner."""
    errors: List[str] = []
    _scan_forbidden(value, "$", errors)
    if not isinstance(value, dict):
        return errors + ["$ must be an object"]

    _require_exact_keys(value, PUBLIC_FIXTURE_KEYS, "$", errors)
    if (
        type(value.get("schema_version")) is not int
        or value.get("schema_version") != PUBLIC_FIXTURE_SCHEMA_VERSION
    ):
        errors.append("$.schema_version must be {}".format(PUBLIC_FIXTURE_SCHEMA_VERSION))

    authority = value.get("authority")
    if not isinstance(authority, list) or not authority:
        errors.append("$.authority must be a non-empty list")
    else:
        for index, entry in enumerate(authority):
            location = "$.authority[{}]".format(index)
            if not _require_exact_keys(entry, AUTHORITY_KEYS, location, errors):
                continue
            if not _safe_relative_path(entry.get("path")):
                errors.append("{}.path must be a safe relative path".format(location))
            if not isinstance(entry.get("fresh"), bool):
                errors.append("{}.fresh must be boolean".format(location))

    repository = value.get("repository")
    if _require_exact_keys(repository, REPOSITORY_KEYS, "$.repository", errors):
        if not isinstance(repository.get("state"), str) or not repository["state"].strip():
            errors.append("$.repository.state must be a non-empty string")
        changed_paths = repository.get("changed_paths")
        if not isinstance(changed_paths, list) or not all(
            _safe_relative_path(path) for path in changed_paths
        ):
            errors.append("$.repository.changed_paths must be a list of safe relative paths")

    plan = value.get("plan")
    if _require_exact_keys(plan, PLAN_KEYS, "$.plan", errors):
        if not isinstance(plan.get("ticket_ready"), bool):
            errors.append("$.plan.ticket_ready must be boolean")
    return errors


def load_public_fixture(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FixtureSchemaError("unreadable public fixture {}: {}".format(path, exc)) from exc
    errors = validate_public_fixture(data)
    if errors:
        raise FixtureSchemaError("invalid public fixture: {}".format("; ".join(errors)))
    return data


PRIVATE_BASELINE_KEYS = {"source", "scenarios"}
PRIVATE_SCENARIO_KEYS = {"id", "case_id", "source_case", "expected"}


def validate_private_baseline(value: Any) -> List[str]:
    """Validate trusted baseline material kept out of runner input."""
    errors: List[str] = []
    if not isinstance(value, dict):
        return ["private baseline must be an object"]
    _require_exact_keys(value, PRIVATE_BASELINE_KEYS, "private baseline", errors)
    if not isinstance(value.get("source"), str) or not value["source"].strip():
        errors.append("private baseline.source must be a non-empty string")
    scenarios = value.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("private baseline.scenarios must be a non-empty list")
        return errors
    ids = set()
    case_ids = set()
    for index, scenario in enumerate(scenarios):
        location = "private baseline.scenarios[{}]".format(index)
        if not _require_exact_keys(scenario, PRIVATE_SCENARIO_KEYS, location, errors):
            continue
        scenario_id = scenario.get("id")
        case_id = scenario.get("case_id")
        if not isinstance(scenario_id, str) or not scenario_id.strip() or scenario_id in ids:
            errors.append("{}.id must be unique and non-empty".format(location))
        if not isinstance(case_id, str) or not case_id.strip() or case_id in case_ids:
            errors.append("{}.case_id must be unique and non-empty".format(location))
        if isinstance(scenario_id, str):
            ids.add(scenario_id)
        if isinstance(case_id, str):
            case_ids.add(case_id)
        if not isinstance(scenario.get("expected"), str) or not scenario["expected"].strip():
            errors.append("{}.expected must be a non-empty string".format(location))
    return errors


def load_private_baseline(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FixtureSchemaError("unreadable private baseline {}: {}".format(path, exc)) from exc
    errors = validate_private_baseline(data)
    if errors:
        raise FixtureSchemaError("invalid private baseline: {}".format("; ".join(errors)))
    return data
