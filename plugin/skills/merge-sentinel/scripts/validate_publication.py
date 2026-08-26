from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from reviewlib.models import (
    IncompatibleSchemaError,
    ValidationError,
    atomic_write_json,
    canonical_json_bytes,
    load_json,
    normalize_repo_path,
    require_schema,
)


OPERATIONS = {"top-level-note", "reply", "inline-discussion", "resolve", "reopen", "approve"}
STATES = {"intended", "attempted", "confirmed", "failed", "uncertain"}
MERGEABILITY = {"mergeable", "blocked", "indeterminate"}


def _fail(message: str) -> None:
    raise ValidationError(message)


def _non_empty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        _fail(f"{name} must be a non-empty string")
    return value


def _mapping(document: dict[str, object], name: str) -> dict[str, object]:
    value = document.get(name)
    if not isinstance(value, dict):
        _fail(f"{name} must be an object")
    return value


def _load_ledger(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"schema_version": 1, "revision": 0, "operations": {}}
    ledger = load_json(path)
    require_schema(ledger)
    if not isinstance(ledger.get("revision"), int) or ledger["revision"] < 0:
        _fail("ledger revision must be a non-negative integer")
    if not isinstance(ledger.get("operations"), dict):
        _fail("ledger operations must be an object")
    return ledger


def _validate_request(document: dict[str, object]) -> tuple[str, str, str]:
    require_schema(document)
    operation_id = _non_empty_string(document.get("operation_id"), "operation_id")
    operation = _non_empty_string(document.get("operation"), "operation")
    authority = _non_empty_string(document.get("authority"), "authority")
    if operation not in OPERATIONS:
        _fail("unsupported operation")
    if authority != operation:
        _fail("authority must exactly match operation")
    _non_empty_string(document.get("idempotency_key"), "idempotency_key")

    snapshot, remote = _mapping(document, "snapshot"), _mapping(document, "remote")
    for name in ("head_sha", "diff_version"):
        if not isinstance(snapshot.get(name), str) or not isinstance(remote.get(name), str):
            _fail(f"{name} must be a string")
    if snapshot["head_sha"] != remote["head_sha"]:
        _fail("stale head")
    if snapshot["diff_version"] != remote["diff_version"]:
        _fail("stale diff version")
    if remote.get("mergeability") not in MERGEABILITY:
        _fail("invalid mergeability")
    if operation == "approve" and remote["mergeability"] != "mergeable":
        _fail("approval requires mergeable remote")
    if operation == "inline-discussion":
        position = _mapping(document, "position")
        for name in ("base_sha", "start_sha", "head_sha"):
            _non_empty_string(position.get(name), f"position.{name}")
        normalize_repo_path(_non_empty_string(position.get("path"), "position.path"))
        if not isinstance(position.get("new_line"), int) or position["new_line"] <= 0:
            _fail("inline discussion requires a positive new_line")
        if position.get("commentable") is not True:
            _fail("inline discussion requires a commentable position")
    return operation_id, operation, _non_empty_string(document.get("idempotency_key"), "idempotency_key")


def _validate_entry(entry: object) -> dict[str, object]:
    if not isinstance(entry, dict):
        _fail("ledger operation must be an object")
    for field in ("operation_id", "idempotency_key", "state", "remote_object_id", "last_error"):
        if not isinstance(entry.get(field), str):
            _fail(f"ledger operation {field} must be a string")
    if entry["state"] not in STATES:
        _fail("invalid ledger operation state")
    return entry


def validate(document: dict[str, object], ledger: dict[str, object]) -> tuple[dict[str, object], bool]:
    operation_id, operation, key = _validate_request(document)
    operations = ledger["operations"]
    assert isinstance(operations, dict)
    prior = operations.get(key)
    if prior is not None:
        entry = _validate_entry(prior)
        if entry["operation_id"] != operation_id:
            _fail("idempotency key belongs to another operation")
        if entry["state"] == "confirmed":
            return ({"valid": True, "operation_id": operation_id, "next_action": "skip", "reasons": ["already-confirmed"], "ledger_state": "confirmed"}, False)
        if entry["state"] == "uncertain":
            _fail("uncertain operation requires remote verification")
        if entry["state"] == "attempted":
            _fail("attempted operation requires confirmation before retry")
        return ({"valid": True, "operation_id": operation_id, "next_action": "attempt", "reasons": [], "ledger_state": entry["state"]}, False)
    operations[key] = {"operation_id": operation_id, "idempotency_key": key, "state": "intended", "remote_object_id": "", "last_error": ""}
    ledger["revision"] = ledger["revision"] + 1
    return ({"valid": True, "operation_id": operation_id, "next_action": "attempt", "reasons": [], "ledger_state": "intended"}, True)


def _lock(path: Path) -> int:
    try:
        return os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise RuntimeError("locked") from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    command = parser.add_subparsers(dest="command", required=True)
    validate_parser = command.add_parser("validate")
    validate_parser.add_argument("--input", type=Path, required=True)
    validate_parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args(argv)
    lock_path = args.ledger.with_name(args.ledger.name + ".lock")
    locked = False
    try:
        fd = _lock(lock_path)
        os.close(fd)
        locked = True
        document = load_json(args.input)
        ledger = _load_ledger(args.ledger)
        result, changed = validate(document, ledger)
        if changed:
            atomic_write_json(args.ledger, ledger)
        sys.stdout.buffer.write(canonical_json_bytes(result) + b"\n")
        return 0
    except RuntimeError as error:
        if str(error) == "locked":
            sys.stderr.write("ledger is locked\n")
            return 4
        raise
    except IncompatibleSchemaError as error:
        sys.stderr.write(f"{error}\n")
        return 3
    except ValidationError as error:
        sys.stderr.write(f"{error}\n")
        return 2
    except Exception as error:
        sys.stderr.write(f"{error}\n")
        return 1
    finally:
        if locked:
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
