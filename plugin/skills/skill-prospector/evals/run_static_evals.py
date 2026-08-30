#!/usr/bin/env python3
"""Run the deterministic eval slice for skill-prospector.

The corpus remains data. It selects trusted operations but cannot provide a
command line or an interpreter. Host-routing and llm-judge cases are reported
as skipped, never as passing.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import scan_guidance  # noqa: E402


class UnsafeCheck(Exception):
    """A corpus entry requested an operation outside trusted runner bounds."""


def _contained(value: str) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if os.path.isabs(value) or value.startswith(("\\", "/")):
        return False
    if len(value) > 1 and value[1] == ":":
        return False
    normalized = os.path.normpath(value).replace(os.sep, "/")
    return normalized != ".." and not normalized.startswith("../")


def _resolve(relative: str) -> Path:
    if not _contained(relative):
        raise UnsafeCheck(f"path escapes the package: {relative!r}")
    candidate = (ROOT / relative).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        raise UnsafeCheck(f"path escapes the package: {relative!r}")
    return candidate


def _capture(entry, argv):
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = entry(argv)
    return code, stdout.getvalue(), stderr.getvalue()


def _load_data(path: Path):
    if path.suffix.lower() != ".json":
        raise RuntimeError("canonical evals must use JSON")
    return json.loads(path.read_text(encoding="utf-8"))


def _case_files(evals_path: Path):
    if evals_path.is_file():
        return [evals_path]
    if not evals_path.is_dir():
        raise RuntimeError(f"no such eval path: {evals_path}")
    return sorted(
        path for path in evals_path.iterdir()
        if path.suffix.lower() == ".json"
    )


def _cases(evals_path: Path):
    cases = []
    seen = set()
    for path in _case_files(evals_path):
        data = _load_data(path)
        values = data if isinstance(data, list) else [data]
        for value in values:
            if not isinstance(value, dict) or not value.get("id"):
                raise RuntimeError(f"invalid case in {path}")
            if value["id"] in seen:
                raise RuntimeError(f"duplicate case id: {value['id']}")
            seen.add(value["id"])
            cases.append(value)
    return cases


def _contains_command(value) -> bool:
    if isinstance(value, dict):
        return any(key == "command" or _contains_command(item)
                   for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_command(item) for item in value)
    return False


def _text_expectations(check, code, stdout):
    reasons = []
    expected = check.get("expect_exit", 0)
    if code != expected:
        reasons.append(f"exit {code}, expected {expected}")
    for needle in check.get("stdout_contains") or []:
        if needle not in stdout:
            reasons.append(f"stdout missing: {needle!r}")
    for needle in check.get("stdout_not_contains") or []:
        if needle in stdout:
            reasons.append(f"stdout unexpectedly contains: {needle!r}")
    return reasons


def check_scan(check):
    argv = ["scan", str(_resolve(check["root"])), "--json"]
    if check.get("max_bytes") is not None:
        argv.extend(["--max-bytes", str(check["max_bytes"])])
    code, stdout, _ = _capture(scan_guidance.main, argv)
    reasons = _text_expectations(check, code, stdout)
    return not reasons, reasons


def check_file_exists(check):
    reasons = [] if _resolve(check["path"]).exists() else [f"missing: {check['path']}"]
    return not reasons, reasons


def _snapshot_tree(root: Path):
    snapshot = {}
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_file():
            stat = path.stat()
            snapshot[relative] = ("file", stat.st_size, stat.st_mtime_ns)
        elif path.is_dir():
            snapshot[relative] = ("dir",)
    return snapshot


def _run_fixture_scan(name: str):
    target = ROOT / "evals" / "fixtures" / name
    if not target.is_dir():
        return None, [f"missing fixture: {name}"]
    code, stdout, stderr = _capture(
        scan_guidance.main, ["scan", str(target), "--json"]
    )
    if code != 0:
        return None, [f"scan exited {code}: {stderr.strip()}"]
    try:
        return json.loads(stdout), []
    except json.JSONDecodeError as exc:
        return None, [f"scan emitted invalid JSON: {exc}"]


def scan_fixture_shape(name: str):
    result, reasons = _run_fixture_scan(name)
    if reasons:
        return False, reasons
    expected_path = ROOT / "evals" / "fixtures" / name / "expectations.json"
    try:
        expectations = json.loads(expected_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, [f"expectations unreadable: {exc}"]
    if result["errors"]:
        reasons.append(f"scan errors: {result['errors']}")
    by_path = {unit["path"]: unit for unit in result["matched_units"]}
    actual = set(by_path)
    expected = set(expectations.get("expected_paths", []))
    missing = expected - actual
    if missing:
        reasons.append(f"expected paths missing from inventory: {sorted(missing)}")
    unexpected = actual - expected
    if unexpected:
        reasons.append(f"unexpected paths in inventory: {sorted(unexpected)}")
    for path in expectations.get("ignored_catalogue_paths", []):
        unit = by_path.get(path)
        if not unit:
            continue
        if unit.get("source_scope") != "catalogue":
            reasons.append(f"ignored path is not catalogue-scoped: {path}")
        if unit.get("ignored_by_git") is not True:
            reasons.append(f"catalogue path was not marked gitignored: {path}")
    skipped = {item.get("path"): item.get("reason") for item in result["skipped"]}
    for path in expectations.get("ignored_heuristic_paths", []):
        if path in actual:
            reasons.append(f"ignored heuristic path was inventoried: {path}")
        elif skipped.get(path) != "excluded:.gitignore":
            reasons.append(f"ignored heuristic path lacks gitignore skip: {path}")
    expected_ignored_count = expectations.get("ignored_guidance_count")
    if expected_ignored_count is not None and result.get("ignored_guidance_count") != expected_ignored_count:
        reasons.append(
            "ignored_guidance_count is "
            f"{result.get('ignored_guidance_count')}, expected {expected_ignored_count}"
        )
    if not isinstance(result.get("scanned_files"), int):
        reasons.append("scanned_files is not an integer")
    return not reasons, reasons


def scan_is_read_only(_check):
    target = ROOT / "evals" / "fixtures" / "target-claude-code-rich"
    before = _snapshot_tree(target)
    result, reasons = _run_fixture_scan("target-claude-code-rich")
    after = _snapshot_tree(target)
    if before != after:
        reasons.append("target tree changed during scan")
    if result and result.get("errors"):
        reasons.append(f"scan errors: {result['errors']}")
    return not reasons, reasons


REQUIRED_PLAN_HEADINGS = (
    "Run summary", "Target and authority", "Discovery inventory", "Candidates",
    "Rejected and deferred units", "Host adaptation", "Capabilities not exercised",
    "Follow-up",
)


def plan_artifact_shape(check):
    path = _resolve(check.get("path", "evals/fixtures/expected-plan.md"))
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return False, [f"fixture plan unreadable: {exc}"]
    reasons = []
    if lines[:2] != [
        "# Skill Prospector plan",
        "<!-- Generated by skill-prospector -->",
    ]:
        reasons.append("missing exact generated-plan marker")
    headings = {
        line[3:].strip() for line in lines if line.startswith("## ")
    }
    missing = [heading for heading in REQUIRED_PLAN_HEADINGS if heading not in headings]
    if missing:
        reasons.append(f"missing plan headings: {missing}")

    authority = [line for line in lines if line.startswith("authority:")]
    if len(authority) != 1 or not re.fullmatch(
        r"authority:\s+(default|explicit|redirected)", authority[0]
    ):
        reasons.append("missing or invalid authority field")
    overwrite = [line for line in lines if line.startswith("overwrite:")]
    if len(overwrite) != 1 or not re.fullmatch(
        r"overwrite:\s+(yes|no)", overwrite[0]
    ):
        reasons.append("missing or invalid overwrite field")

    candidate_fields = (
        "id", "name", "boundary", "trigger", "sources",
        "proposed mechanism", "invocation policy", "invocation evidence",
        "portable invocation", "host enhancements",
        "dependencies", "eval outline", "acceptance criteria",
    )
    starts = [index for index, line in enumerate(lines)
              if line.startswith("### Candidate:")]
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        block = [line for line in lines[start + 1:end] if line.strip()]
        fields = [line.split(":", 1)[0] for line in block if ":" in line]
        if fields[:len(candidate_fields)] != list(candidate_fields):
            reasons.append(f"candidate block at line {start + 1} has invalid fields")

    inventory_index = next(
        (index for index, line in enumerate(lines)
         if line == "## Discovery inventory"), None
    )
    if inventory_index is not None:
        inventory_end = next(
            (index for index in range(inventory_index + 1, len(lines))
             if lines[index].startswith("## ")),
            len(lines),
        )
        state_rows = [
            line for line in lines[inventory_index + 1:inventory_end]
            if line.startswith("|") and not line.startswith("|---")
            and "terminal state" not in line
        ]
        for line in state_rows:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) != 2 or not re.fullmatch(
                r"(?:covered-by-candidate:[^|]+|stays-as-[^|]+|deferred|unreadable)",
                cells[1],
            ):
                reasons.append(f"invalid inventory terminal state: {line}")
    return not reasons, reasons


def plan_sections_present(check):
    """Compatibility name for older local cases; checks the full artifact shape."""
    return plan_artifact_shape(check)


def headingless_document_evidence(_check):
    target = ROOT / "evals" / "fixtures" / "target-unheaded-guidance"
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = scan_guidance.main([
            "slice", str(target), "AGENTS.md", "--document", "--max-bytes", "96"
        ])
    rendered = out.getvalue()
    reasons = []
    if code != 0:
        reasons.append(f"document slice exited {code}: {err.getvalue().strip()}")
    if len(rendered.encode("utf-8")) > 96:
        reasons.append("document slice exceeds max bytes")
    if "AGENTS.md:1-4" not in rendered:
        reasons.append("document slice lacks line-span provenance")
    return not reasons, reasons


def hash_drift(_check):
    with tempfile.TemporaryDirectory(prefix="prospector-hash-drift-") as directory:
        root = Path(directory)
        path = root / "AGENTS.md"
        path.write_text("Run the original check.\n", encoding="utf-8")
        result, reasons = _run_scan_path(root)
        if reasons:
            return False, reasons
        scan_id = result.get("scan_id")
        first_code, first_output, first_error = _capture(
            scan_guidance.main,
            ["slice", str(root), "AGENTS.md", "--document", "--scan-id", scan_id],
        )
        if first_code != 0 or "Run the original check." not in first_output:
            reasons.append(f"fresh evidence rejected: {first_error.strip()}")
        path.write_text("Run the changed check.\n", encoding="utf-8")
        second_code, second_output, _ = _capture(
            scan_guidance.main,
            ["slice", str(root), "AGENTS.md", "--document", "--scan-id", scan_id],
        )
        if second_code != 2 or second_output:
            reasons.append("changed evidence was not rejected")
        return not reasons, reasons


def _run_scan_path(root: Path):
    code, stdout, stderr = _capture(
        scan_guidance.main, ["scan", str(root), "--json"]
    )
    if code != 0:
        return None, [f"scan exited {code}: {stderr.strip()}"]
    try:
        return json.loads(stdout), []
    except json.JSONDecodeError as exc:
        return None, [f"scan emitted invalid JSON: {exc}"]


def root_containment(_check):
    with tempfile.TemporaryDirectory(prefix="prospector-containment-") as directory:
        with tempfile.TemporaryDirectory(prefix="prospector-outside-") as outside_dir:
            root = Path(directory)
            outside = Path(outside_dir)
            secret = outside / "secret.md"
            secret.write_text("OUTSIDE SECRET\n", encoding="utf-8")
            reasons = []

            for relative in ("../secret.md", str(secret)):
                code, output, _ = _capture(
                    scan_guidance.main,
                    ["slice", str(root), relative, "--document"],
                )
                if code != 2 or "OUTSIDE SECRET" in output:
                    reasons.append(f"escape was not rejected: {relative}")

            inventory = outside / "inventory.json"
            code, _, _ = _capture(
                scan_guidance.main,
                ["scan", str(root), "--json", "--out", str(inventory)],
            )
            if code != 2 or inventory.exists():
                reasons.append("outside inventory output was accepted")
            return not reasons, reasons


def idempotent_scan(_check):
    first, reasons = _run_fixture_scan("target-claude-code-rich")
    second, second_reasons = _run_fixture_scan("target-claude-code-rich")
    reasons.extend(second_reasons)
    if first != second:
        reasons.append("consecutive scan inventories differ")
    if first:
        paths = [unit["path"] for unit in first["matched_units"]]
        if len(paths) != len(set(paths)):
            reasons.append("inventory contains duplicate paths")
    return not reasons, reasons


def slice_bounds(_check):
    target = ROOT / "evals" / "fixtures" / "target-claude-code-rich" / "docs" / "runbooks" / "deploy.md"
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = scan_guidance.main([
            "slice", str(target.parent.parent.parent),
            "docs/runbooks/deploy.md", "--section", "Deploy", "--max-bytes", "64"
        ])
    rendered = out.getvalue()
    reasons = []
    if code != 0:
        reasons.append(f"slice exited {code}: {err.getvalue().strip()}")
    if len(rendered.encode("utf-8")) > 64:
        reasons.append("slice output exceeds max bytes")
    return not reasons, reasons


def _scan_validator(check):
    name = check["validator"]
    prefix = "scan_"
    if name.startswith(prefix):
        return scan_fixture_shape(name[len(prefix):])
    raise UnsafeCheck(f"unknown validator: {name!r}")


VALIDATORS = {
    "scan_is_read_only": scan_is_read_only,
    "plan_sections_present": plan_sections_present,
    "plan_artifact_shape": plan_artifact_shape,
    "headingless_document_evidence": headingless_document_evidence,
    "hash_drift": hash_drift,
    "root_containment": root_containment,
    "idempotent_scan": idempotent_scan,
    "slice_bounds": slice_bounds,
}


def check_validator(check):
    name = check["validator"]
    if name.startswith("scan_target-"):
        return _scan_validator(check)
    if name not in VALIDATORS:
        raise UnsafeCheck(f"unknown validator: {name!r}")
    return VALIDATORS[name](check)


CHECK_KINDS = {
    "scan": check_scan,
    "file-exists": check_file_exists,
    "validator": check_validator,
}


def run_check(check):
    if not isinstance(check, dict) or "kind" not in check:
        raise UnsafeCheck("deterministic check requires a kind")
    if "command" in check:
        raise UnsafeCheck("check.command is not supported")
    kind = check["kind"]
    if kind not in CHECK_KINDS:
        raise UnsafeCheck(f"unknown check kind: {kind!r}")
    started = time.time()
    passed, reasons = CHECK_KINDS[kind](check)
    duration = int((time.time() - started) * 1000)
    return passed, reasons, duration


def _deterministic_check(case):
    for grader in case.get("graders") or []:
        if isinstance(grader, dict) and grader.get("type") == "deterministic":
            return grader.get("check")
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evals", default=str(HERE))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        cases = _cases(Path(args.evals).resolve())
        if any(_contains_command(case) for case in cases):
            raise UnsafeCheck("check.command is not supported")
    except (OSError, RuntimeError, json.JSONDecodeError, UnsafeCheck) as exc:
        print(f"corpus rejected: {exc}", file=sys.stderr)
        return 2

    results = []
    for case in cases:
        check = _deterministic_check(case)
        if check is None:
            results.append({"id": case["id"], "status": "skipped",
                            "reason": "requires host runner or model"})
            continue
        try:
            passed, reasons, duration = run_check(check)
            results.append({
                "id": case["id"],
                "status": "passed" if passed else "failed",
                "duration_ms": duration,
                "reasons": reasons[:10],
            })
        except (OSError, UnsafeCheck, KeyError, TypeError, ValueError) as exc:
            results.append({"id": case["id"], "status": "failed",
                            "reasons": [str(exc)]})

    summary = {
        "runnable": sum(result["status"] != "skipped" for result in results),
        "passed": sum(result["status"] == "passed" for result in results),
        "failed": sum(result["status"] == "failed" for result in results),
        "skipped": sum(result["status"] == "skipped" for result in results),
    }
    if args.json:
        print(json.dumps({"summary": summary, "results": results}, indent=2))
    else:
        for result in results:
            mark = {"passed": "PASS", "failed": "FAIL", "skipped": "SKIP"}[result["status"]]
            reason = result.get("reason") or "; ".join(result.get("reasons", []))
            print(f"{mark} {result['id']}" + (f"  {reason}" if reason else ""))
        print(f"\n{summary['passed']}/{summary['runnable']} deterministic cases passed; {summary['skipped']} skipped")
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
