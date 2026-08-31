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
from unittest import mock


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
PLAN_CANDIDATE_FIELDS = (
    "id", "name", "boundary", "trigger", "sources",
    "proposed mechanism", "invocation policy", "invocation evidence",
    "portable invocation", "host enhancements", "dependencies", "eval outline",
    "acceptance criteria",
)
INVOCATION_POLICIES = {"automatic", "both", "explicit-only-required"}


def _top_level_headings(lines):
    return [
        (index, line[3:].strip())
        for index, line in enumerate(lines)
        if line.startswith("## ")
    ]


def _section_span(lines, headings, title):
    start = next((index for index, heading in headings if heading == title), None)
    if start is None:
        return None
    end = next(
        (index for index, _heading in headings if index > start),
        len(lines),
    )
    return start, end


def _label_matches(lines, labels):
    pattern = re.compile(
        r"^\s*(" + "|".join(re.escape(label) for label in labels) + r"):\s*(.*)$"
    )
    return [
        (index, match.group(1), match.group(2).strip())
        for index, line in enumerate(lines)
        if (match := pattern.match(line))
    ]


def _inventory_row(line):
    if not line.strip().startswith("|"):
        return None
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if len(cells) != 2:
        return (), ()
    if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
        return None
    return cells


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
    headings = _top_level_headings(lines)
    heading_names = [heading for _index, heading in headings]
    counts = {heading: heading_names.count(heading)
              for heading in REQUIRED_PLAN_HEADINGS}
    missing = [heading for heading, count in counts.items() if count == 0]
    duplicate = [heading for heading, count in counts.items() if count > 1]
    if missing:
        reasons.append(f"missing plan headings: {missing}")
    if duplicate:
        reasons.append(f"duplicate plan headings: {duplicate}")
    unexpected = [heading for heading in heading_names
                  if heading not in REQUIRED_PLAN_HEADINGS]
    if unexpected:
        reasons.append(f"unexpected plan headings: {unexpected}")
    if [heading for heading in heading_names if heading in REQUIRED_PLAN_HEADINGS] != list(REQUIRED_PLAN_HEADINGS):
        reasons.append("plan headings are not in documented order")

    target_span = _section_span(lines, headings, "Target and authority")
    if target_span is not None:
        target_lines = lines[target_span[0] + 1:target_span[1]]
        authority = _label_matches(target_lines, ("authority",))
        if len(authority) != 1 or authority[0][2] not in {"default", "explicit", "redirected"}:
            reasons.append("missing or invalid authority field in Target and authority")
        overwrite = _label_matches(target_lines, ("overwrite",))
        if len(overwrite) != 1 or overwrite[0][2] not in {"yes", "no"}:
            reasons.append("missing or invalid overwrite field in Target and authority")

    candidate_ids = []
    candidates_span = _section_span(lines, headings, "Candidates")
    if candidates_span is not None:
        candidate_start, candidate_end = candidates_span
        candidate_headers = []
        candidate_heading_re = re.compile(r"### Candidate:\s*(.*?)\s*")
        for index in range(candidate_start + 1, candidate_end):
            if not lines[index].startswith("### "):
                continue
            header_match = re.fullmatch(candidate_heading_re, lines[index])
            if header_match is None:
                reasons.append(f"malformed candidate heading at line {index + 1}")
            else:
                candidate_headers.append(index)
        first_header = candidate_headers[0] if candidate_headers else candidate_end
        if _label_matches(lines[candidate_start + 1:first_header], PLAN_CANDIDATE_FIELDS):
            reasons.append("candidate fields outside a recognized candidate block")
        for position, start in enumerate(candidate_headers):
            end = candidate_headers[position + 1] if position + 1 < len(candidate_headers) else candidate_end
            header_match = re.fullmatch(candidate_heading_re, lines[start])
            candidate_id = header_match.group(1).strip() if header_match else ""
            if not candidate_id:
                reasons.append(f"candidate block at line {start + 1} has an empty header id")
            elif candidate_id in candidate_ids:
                reasons.append(f"duplicate candidate id: {candidate_id}")
            else:
                candidate_ids.append(candidate_id)

            block = lines[start + 1:end]
            matches = _label_matches(block, PLAN_CANDIDATE_FIELDS)
            labels = [label for _index, label, _value in matches]
            for field in PLAN_CANDIDATE_FIELDS:
                field_matches = [match for match in matches if match[1] == field]
                if len(field_matches) != 1:
                    reasons.append(
                        f"candidate {candidate_id or '<empty>'} field {field!r} must occur exactly once"
                    )
                elif not field_matches[0][2]:
                    reasons.append(
                        f"candidate {candidate_id or '<empty>'} field {field!r} is empty"
                    )
            if labels != list(PLAN_CANDIDATE_FIELDS):
                reasons.append(f"candidate block at line {start + 1} has invalid field order")
            id_matches = [match for match in matches if match[1] == "id"]
            if len(id_matches) == 1 and candidate_id and id_matches[0][2] != candidate_id:
                reasons.append(f"candidate header/id mismatch: {candidate_id!r} vs {id_matches[0][2]!r}")
            policy_matches = [match for match in matches if match[1] == "invocation policy"]
            if len(policy_matches) == 1 and policy_matches[0][2] not in INVOCATION_POLICIES:
                reasons.append(
                    f"candidate {candidate_id or '<empty>'} has invalid invocation policy"
                )

    inventory_span = _section_span(lines, headings, "Discovery inventory")
    if inventory_span is not None:
        inventory_lines = lines[inventory_span[0] + 1:inventory_span[1]]
        table_headers = [
            index for index, line in enumerate(inventory_lines)
            if re.fullmatch(r"\|\s*path\s*\|\s*terminal state\s*\|", line.strip())
        ]
        if len(table_headers) != 1:
            reasons.append("Discovery inventory must contain exactly one path/terminal state table")
        else:
            paths = set()
            for line in inventory_lines[table_headers[0] + 1:]:
                row = _inventory_row(line)
                if row is None:
                    continue
                if row == ((), ()):
                    reasons.append(f"invalid discovery inventory row: {line}")
                    continue
                path_value, state = row
                if not path_value:
                    reasons.append(f"discovery inventory path is empty: {line}")
                elif path_value in paths:
                    reasons.append(f"duplicate discovery inventory path: {path_value}")
                else:
                    paths.add(path_value)
                covered_match = re.fullmatch(r"covered-by-candidate:\s*(.+?)\s*", state)
                valid_state = state in {"deferred", "unreadable"}
                valid_state = valid_state or bool(
                    re.fullmatch(r"stays-as-.+", state)
                )
                if covered_match:
                    valid_state = True
                    if covered_match.group(1) not in candidate_ids:
                        reasons.append(
                            f"inventory references unknown candidate: {covered_match.group(1)}"
                        )
                if not valid_state:
                    reasons.append(f"invalid inventory terminal state: {line}")
    return not reasons, reasons


def plan_sections_present(check):
    """Compatibility name for older local cases; checks the full artifact shape."""
    return plan_artifact_shape(check)


def headingless_document_evidence(_check):
    target = ROOT / "evals" / "fixtures" / "target-unheaded-guidance"
    inventory, inventory_reasons = _run_scan_path(target)
    if inventory_reasons:
        return False, inventory_reasons
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = scan_guidance.main([
            "slice", str(target), "AGENTS.md", "--document", "--max-bytes", "96",
            "--scan-id", inventory["scan_id"],
        ])
    rendered = out.getvalue()
    reasons = []
    if code != 0:
        reasons.append(f"document slice exited {code}: {err.getvalue().strip()}")
    if len(rendered.encode("utf-8")) > 96:
        reasons.append("document slice exceeds max bytes")
    source_lines = (target / "AGENTS.md").read_text(encoding="utf-8").splitlines(
        keepends=True
    )
    valid_spans = []
    marker = "[truncated]"
    for count in range(len(source_lines) + 1):
        actual_end = count if count else 0
        header = f"AGENTS.md:1-{actual_end}\n"
        body = "".join(source_lines[:count])
        separator = "" if not body or body.endswith(("\n", "\r")) else "\n"
        if rendered == header + body + separator + marker:
            valid_spans.append(actual_end)
        if rendered == header + body:
            valid_spans.append(actual_end)
    if not valid_spans:
        reasons.append("document slice lacks truthful line-span provenance")
    elif valid_spans[-1] != 2:
        reasons.append(f"document slice reports unexpected emitted end line: {valid_spans[-1]}")
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


def _run_scan_path_with_max(root: Path, max_bytes: int):
    code, stdout, stderr = _capture(
        scan_guidance.main, ["scan", str(root), "--json", "--max-bytes", str(max_bytes)]
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
            inventory, inventory_reasons = _run_scan_path(root)
            reasons.extend(inventory_reasons)
            if reasons:
                return False, reasons
            scan_id = inventory["scan_id"]

            for relative in ("../secret.md", str(secret)):
                code, output, _ = _capture(
                    scan_guidance.main,
                    ["slice", str(root), relative, "--document", "--scan-id", scan_id],
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
    root = target.parent.parent.parent
    inventory, inventory_reasons = _run_scan_path(root)
    if inventory_reasons:
        return False, inventory_reasons
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = scan_guidance.main([
            "slice", str(root), "docs/runbooks/deploy.md", "--section", "Deploy",
            "--max-bytes", "64", "--scan-id", inventory["scan_id"],
        ])
    rendered = out.getvalue()
    reasons = []
    if code != 0:
        reasons.append(f"slice exited {code}: {err.getvalue().strip()}")
    if len(rendered.encode("utf-8")) > 64:
        reasons.append("slice output exceeds max bytes")
    return not reasons, reasons


def inventory_bound_slice(_check):
    with tempfile.TemporaryDirectory(prefix="prospector-inventory-bound-") as directory:
        root = Path(directory)
        (root / "AGENTS.md").write_text("# Rules\nRun the check.\n", encoding="utf-8")
        (root / "secret.json").write_text('{"secret": true}\n', encoding="utf-8")
        (root / "notes.md").write_text("Read once.\n", encoding="utf-8")
        (root / "package-lock.json").write_text(
            '{"name": "ignored-lock"}\n', encoding="utf-8"
        )
        (root / "ignored.md").write_text("\n".join(["Run ignored prose."] * 8), encoding="utf-8")
        (root / ".gitignore").write_text("ignored.md\n", encoding="utf-8")
        (root / "node_modules").mkdir()
        (root / "node_modules" / "AGENTS.md").write_text("Run ignored dependency.\n", encoding="utf-8")

        result, reasons = _run_scan_path(root)
        if reasons:
            return False, reasons
        token = result.get("scan_id")
        if not isinstance(token, str) or not token.startswith("v2:"):
            reasons.append("scan_id is not a v2 inventory token")
            return False, reasons
        paths = {unit["path"] for unit in result.get("matched_units", [])}
        if paths != {"AGENTS.md"}:
            reasons.append(f"unexpected matched inventory paths: {sorted(paths)}")

        valid_code, valid_output, valid_error = _capture(
            scan_guidance.main,
            ["slice", str(root), "AGENTS.md", "--document", "--scan-id", token],
        )
        if valid_code != 0 or "Run the check." not in valid_output:
            reasons.append(f"matched inventory path was rejected: {valid_error.strip()}")

        for relative in (
            "secret.json",
            "notes.md",
            "package-lock.json",
            "ignored.md",
            "node_modules/AGENTS.md",
        ):
            code, output, stderr = _capture(
                scan_guidance.main,
                ["slice", str(root), relative, "--document", "--scan-id", token],
            )
            if code != 2 or output:
                reasons.append(f"non-inventory path was authorized: {relative}")
            if "secret" in output or "secret" in stderr:
                reasons.append("non-inventory file content leaked")

        old_code, old_output, _ = _capture(
            scan_guidance.main,
            ["slice", str(root), "AGENTS.md", "--document", "--scan-id", "old-v1-token"],
        )
        if old_code != 2 or old_output:
            reasons.append("v1 scan id was accepted")

        custom, custom_reasons = _run_scan_path_with_max(root, 16)
        reasons.extend(custom_reasons)
        custom_token = custom.get("scan_id") if custom else None
        if custom_token and not custom_token.startswith("v2:16:"):
            reasons.append("custom max bytes was not encoded in token")
        return not reasons, reasons


def nested_ignored_catalogue(_check):
    with tempfile.TemporaryDirectory(prefix="prospector-nested-ignored-") as directory:
        root = Path(directory)
        workspace = root / "sandbox"
        (workspace / ".cursor" / "rules").mkdir(parents=True)
        (workspace / ".github").mkdir(parents=True)
        (workspace / "docs" / "runbooks").mkdir(parents=True)
        (workspace / "scratch").mkdir(parents=True)
        (workspace / "deep" / "local").mkdir(parents=True)
        (workspace / ".cursor" / "rules" / "review.mdc").write_text(
            "Always review locally.\n", encoding="utf-8"
        )
        (workspace / ".github" / "copilot-instructions.md").write_text(
            "Use the Copilot rules.\n", encoding="utf-8"
        )
        (workspace / "docs" / "runbooks" / "deploy.md").write_text(
            "Run the deploy checklist.\n", encoding="utf-8"
        )
        (workspace / "deep" / "local" / "AGENTS.md").write_text(
            "Use the deep rules.\n", encoding="utf-8"
        )
        (workspace / "scratch" / "notes.md").write_text(
            "\n".join(["Run this ignored prose."] * 8) + "\n", encoding="utf-8"
        )
        (root / ".gitignore").write_text("sandbox/\n", encoding="utf-8")

        result, reasons = _run_scan_path(root)
        if reasons:
            return False, reasons
        by_path = {unit["path"]: unit for unit in result.get("matched_units", [])}
        expected = {
            "sandbox/.cursor/rules/review.mdc",
            "sandbox/.github/copilot-instructions.md",
            "sandbox/docs/runbooks/deploy.md",
            "sandbox/deep/local/AGENTS.md",
        }
        missing = expected - set(by_path)
        if missing:
            reasons.append(f"nested ignored catalogue paths missing: {sorted(missing)}")
        if "sandbox/scratch/notes.md" in by_path:
            reasons.append("ignored heuristic prose was inventoried")
        for path in expected & set(by_path):
            if by_path[path].get("ignored_by_git") is not True:
                reasons.append(f"nested ignored catalogue path lacks ignored provenance: {path}")
        return not reasons, reasons


def scan_error_exit_two(_check):
    with tempfile.TemporaryDirectory(prefix="prospector-scan-error-") as directory:
        root = Path(directory)
        (root / "AGENTS.md").write_text("Read this.\n", encoding="utf-8")
        original_read = scan_guidance.SafeRoot.read_bytes_with_stat

        def failing_read(safe_root, relative):
            if relative == "AGENTS.md":
                raise scan_guidance.SafePathError("D:/private/AGENTS.md")
            return original_read(safe_root, relative)

        with mock.patch.object(scan_guidance.SafeRoot, "read_bytes_with_stat", failing_read):
            code, stdout, stderr = _capture(scan_guidance.main, ["scan", str(root), "--json"])
        reasons = []
        if code != 2:
            reasons.append(f"read-error scan exited {code}, expected 2")
        if stderr:
            reasons.append("read-error scan wrote stderr before JSON")
        try:
            result = json.loads(stdout)
        except json.JSONDecodeError as exc:
            return False, [f"read-error scan emitted invalid JSON: {exc}"]
        if result.get("errors") != [{"path": "AGENTS.md", "error": "candidate rejected by containment"}]:
            reasons.append(f"read-error scan errors were unstable: {result.get('errors')}")

        def broken_walk(_root, topdown=True, onerror=None):
            error = OSError("D:/private/walk detail")
            error.filename = os.fspath(root / "blocked")
            onerror(error)
            return iter(())

        with mock.patch.object(scan_guidance.os, "walk", broken_walk):
            walk_code, walk_stdout, walk_stderr = _capture(
                scan_guidance.main, ["scan", str(root), "--json"]
            )
        if walk_code != 2:
            reasons.append(f"walk-error scan exited {walk_code}, expected 2")
        if walk_stderr:
            reasons.append("walk-error scan wrote stderr before JSON")
        try:
            walk_result = json.loads(walk_stdout)
        except json.JSONDecodeError as exc:
            return False, reasons + [f"walk-error scan emitted invalid JSON: {exc}"]
        if walk_result.get("errors") != [{"path": "blocked", "error": "walk failed"}]:
            reasons.append(f"walk-error scan errors were unstable: {walk_result.get('errors')}")

        with mock.patch.object(
            scan_guidance, "_read_gitignore", side_effect=OSError("D:/private/.gitignore")
        ):
            gitignore_code, gitignore_stdout, gitignore_stderr = _capture(
                scan_guidance.main, ["scan", str(root), "--json"]
            )
        if gitignore_code != 2:
            reasons.append(f"gitignore-error scan exited {gitignore_code}, expected 2")
        if gitignore_stderr:
            reasons.append("gitignore-error scan wrote stderr before JSON")
        try:
            gitignore_result = json.loads(gitignore_stdout)
        except json.JSONDecodeError as exc:
            return False, reasons + [f"gitignore-error scan emitted invalid JSON: {exc}"]
        if gitignore_result.get("errors") != [
            {"path": ".gitignore", "error": "gitignore read failed"}
        ]:
            reasons.append(
                "gitignore-error scan errors were unstable: "
                f"{gitignore_result.get('errors')}"
            )
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
    "inventory_bound_slice": inventory_bound_slice,
    "nested_ignored_catalogue": nested_ignored_catalogue,
    "scan_error_exit_two": scan_error_exit_two,
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
