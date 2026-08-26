"""Command-line boundary for Merge Sentinel deterministic review state."""
from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path

from reviewlib.anchors import resolve_anchor
from reviewlib.fingerprints import normalize_finding
from reviewlib.models import (
    IncompatibleSchemaError,
    ValidationError,
    atomic_write_json,
    canonical_json_bytes,
    load_json,
    require_schema,
)
from reviewlib.queue import QueueError, complete_lease, new_queue, request_lease
from reviewlib.rereview import build_packet


OUTCOMES = ("reviewed", "excluded", "blocked", "proven", "disproven", "unresolved")


def _emit(value: object) -> None:
    sys.stdout.buffer.write(canonical_json_bytes(value) + b"\n")


def _lock_path(state_path: Path) -> Path:
    return state_path.with_name(state_path.name + ".lock")


def _mutate(state_path: Path, operation) -> object:
    lock_path = _lock_path(state_path)
    descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(descriptor)
    try:
        state = load_json(state_path)
        updated = operation(state)
        atomic_write_json(state_path, updated)
        return updated
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _create_queue(output_path: Path, snapshot_id: str) -> object:
    lock_path = _lock_path(output_path)
    descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(descriptor)
    try:
        state = new_queue(snapshot_id)
        atomic_write_json(output_path, state)
        return state
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate-manifest", "resolve-anchor", "normalize-finding"):
        command = commands.add_parser(name)
        command.add_argument("--input", type=Path, required=True)
    queue = commands.add_parser("new-queue")
    queue.add_argument("--snapshot-id", required=True)
    queue.add_argument("--output", type=Path, required=True)
    lease = commands.add_parser("request-lease")
    lease.add_argument("--state", type=Path, required=True)
    lease.add_argument("--invariant-id", required=True)
    lease.add_argument("--evidence-key", required=True)
    complete = commands.add_parser("complete-lease")
    complete.add_argument("--state", type=Path, required=True)
    complete.add_argument("--lease-id", required=True)
    complete.add_argument("--outcome", choices=OUTCOMES, required=True)
    complete.add_argument("--evidence-hash")
    packet = commands.add_parser("build-rereview-packet")
    packet.add_argument("--prior", type=Path, required=True)
    packet.add_argument("--anchor", type=Path, required=True)
    packet.add_argument("--snapshot", type=Path, required=True)
    return parser


def _dispatch(args: argparse.Namespace) -> object:
    if args.command == "validate-manifest":
        manifest = load_json(args.input)
        require_schema(manifest)
        return manifest
    if args.command == "resolve-anchor":
        return resolve_anchor(load_json(args.input))
    if args.command == "new-queue":
        return _create_queue(args.output, args.snapshot_id)
    if args.command == "request-lease":
        return _mutate(args.state, lambda state: request_lease(state, args.invariant_id, args.evidence_key))
    if args.command == "complete-lease":
        return _mutate(args.state, lambda state: complete_lease(state, args.lease_id, args.outcome, args.evidence_hash))
    if args.command == "normalize-finding":
        return normalize_finding(load_json(args.input))
    if args.command == "build-rereview-packet":
        return build_packet(load_json(args.prior), load_json(args.anchor), load_json(args.snapshot))
    raise RuntimeError(f"unknown command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    try:
        result = _dispatch(_parser().parse_args(argv))
        _emit(result)
        return 0
    except FileExistsError:
        print("state is locked", file=sys.stderr)
        return 4
    except IncompatibleSchemaError as error:
        print(error, file=sys.stderr)
        return 3
    except (ValidationError, QueueError) as error:
        print(error, file=sys.stderr)
        return 2
    except Exception as error:
        print(error, file=sys.stderr)
        if error.__class__.__module__ == "subprocess":
            return 5
        if os.environ.get("MERGE_SENTINEL_DEBUG") == "1":
            traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
