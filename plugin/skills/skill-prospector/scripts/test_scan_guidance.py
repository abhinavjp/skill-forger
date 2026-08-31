#!/usr/bin/env python3
"""Unit tests for the read-only guidance scanner."""
from __future__ import annotations

import contextlib
import errno
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scan_guidance


class ScanGuidanceTests(unittest.TestCase):
    def run_scan(self, root: Path, *extra: str):
        output = io.StringIO()
        errors = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = scan_guidance.main(["scan", str(root), "--json", *extra])
        rendered = output.getvalue()
        return code, json.loads(rendered) if rendered else {}, errors.getvalue()

    def run_slice(self, root: Path, relative: str, *extra: str):
        if "--scan-id" not in extra:
            scan_code, result, scan_errors = self.run_scan(root)
            if scan_code != 0:
                return scan_code, "", scan_errors
            extra = (*extra, "--scan-id", result["scan_id"])
        output = io.StringIO()
        errors = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = scan_guidance.main(["slice", str(root), relative, *extra])
        return code, output.getvalue(), errors.getvalue()

    def make_file_symlink(self, link: Path, target: Path):
        try:
            link.symlink_to(target)
        except (NotImplementedError, OSError) as exc:
            unsupported = getattr(exc, "winerror", None) in {1314, 1920}
            unsupported = unsupported or getattr(exc, "errno", None) in {
                errno.EPERM, errno.ENOSYS, errno.EOPNOTSUPP,
            }
            if unsupported:
                self.skipTest(f"file symlinks unavailable: {exc}")
            raise

    def test_catalogue_and_heuristic_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENTS.md").write_text("Use the repository rules.\n", encoding="utf-8")
            (root / "notes.md").write_text(
                "\n".join([
                    "Read the brief.", "Run the check.", "Use the fixture.",
                    "Always record the result.", "Never skip evidence.",
                    "Verify the output.",
                ]) + "\n", encoding="utf-8")
            code, result, _ = self.run_scan(root)
            self.assertEqual(0, code)
            by_path = {unit["path"]: unit for unit in result["matched_units"]}
            self.assertIn("AGENTS.md", by_path)
            self.assertIn("notes.md", by_path)
            self.assertIn("catalogue:agent-instructions", by_path["AGENTS.md"]["match_reason"])
            self.assertIn("heuristic:imperative-density", by_path["notes.md"]["match_reason"])

    def test_exclusion_and_oversize(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".gitignore").write_text("ignored.md\n", encoding="utf-8")
            (root / "ignored.md").write_text("Read this.\n", encoding="utf-8")
            (root / "dist").mkdir()
            (root / "dist" / "CONTRIBUTING.md").write_text("Read this.\n", encoding="utf-8")
            (root / "CONTRIBUTING.md").write_text("x" * 32, encoding="utf-8")
            code, result, _ = self.run_scan(root, "--max-bytes", "16")
            self.assertEqual(0, code)
            self.assertTrue(result["truncated"])
            self.assertEqual("oversize", result["matched_units"][0]["status"])
            skipped = {item["path"] for item in result["skipped"]}
            self.assertIn("dist", skipped)
            self.assertIn("ignored.md", skipped)

    def test_unreadable_candidate_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENTS.md").write_text("Read this.\n", encoding="utf-8")
            with mock.patch.object(
                scan_guidance, "_read_file_metadata", side_effect=OSError("denied")
            ):
                code, result, _ = self.run_scan(root)
            self.assertEqual(2, code)
            self.assertEqual("AGENTS.md", result["errors"][0]["path"])
            self.assertEqual("candidate read failed", result["errors"][0]["error"])

    def test_outline_directives_fences_and_cross_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runbook = root / "docs" / "runbooks"
            runbook.mkdir(parents=True)
            (runbook / "deploy.md").write_text(
                "\n".join([
                    "# Deploy", "", "Read the checklist.", "Run the tests.",
                    "", "## Rollback", "", "Always keep the backup.",
                    "", "```sh", "run deployment", "```", "",
                    "See [ADR](../adr/0001.md).",
                ]) + "\n", encoding="utf-8")
            code, result, _ = self.run_scan(root)
            self.assertEqual(0, code)
            unit = result["matched_units"][0]
            self.assertEqual(2, len(unit["outline"]))
            self.assertEqual("Deploy", unit["outline"][0]["title"])
            self.assertEqual("Rollback", unit["outline"][1]["title"])
            self.assertGreaterEqual(unit["directive_count"], 3)
            self.assertEqual(1, unit["code_fence_count"])
            self.assertEqual(["../adr/0001.md"], unit["cross_references"])

    def test_slice_exact_case_insensitive_ambiguous_and_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "SKILL.md"
            path.write_text(
                "# Intro\nintro body\n## Rollback\nrollback body\n## Deploy\ndeploy body\n",
                encoding="utf-8",
            )
            code, output, errors = self.run_slice(
                root, "SKILL.md", "--section", "Rollback"
            )
            self.assertEqual(0, code)
            self.assertIn("rollback body", output)
            self.assertIn(":3-4", output)

            code, output, errors = self.run_slice(
                root, "SKILL.md", "--section", "deploy"
            )
            self.assertEqual(0, code, errors)
            self.assertIn("deploy body", output)

            path.write_text("# Repeat\none\n# repeat\ntwo\n", encoding="utf-8")
            code, output, errors = self.run_slice(
                root, "SKILL.md", "--section", "REPEAT"
            )
            self.assertEqual(3, code)
            self.assertIn("ambiguous", errors)

            code, output, errors = self.run_slice(
                root, "SKILL.md", "--section", "Missing"
            )
            self.assertEqual(4, code)
            self.assertIn("not found", errors)

    def test_slice_respects_byte_bound_and_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "SKILL.md"
            path.write_text("# Intro\n" + ("long line\n" * 20), encoding="utf-8")
            code, rendered, errors = self.run_slice(
                root, "SKILL.md", "--section", "Intro", "--max-bytes", "64"
            )
            self.assertEqual(0, code, errors)
            self.assertLessEqual(len(rendered.encode("utf-8")), 64)
            self.assertIn("[truncated]", rendered)

    def test_truncated_slice_preserves_multibyte_complete_lines_and_span(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "SKILL.md").write_text("αβγδε\nsecond line\n", encoding="utf-8")

            code, output, errors = self.run_slice(
                root, "SKILL.md", "--document", "--max-bytes", "35"
            )

            self.assertEqual(0, code, errors)
            self.assertEqual(
                "SKILL.md:1-1\nαβγδε\n[truncated]", output
            )
            self.assertEqual(35, len(output.encode("utf-8")))

    def test_first_line_larger_than_budget_emits_truthful_empty_span(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "SKILL.md").write_text("🙂" * 20 + "\nsmall\n", encoding="utf-8")

            code, output, errors = self.run_slice(
                root, "SKILL.md", "--document", "--max-bytes", "24"
            )

            self.assertEqual(0, code, errors)
            self.assertEqual("SKILL.md:1-0\n[truncated]", output)
            self.assertEqual(24, len(output.encode("utf-8")))

    def test_truncation_recomputes_end_line_digit_width(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "SKILL.md").write_text("line\n" * 12, encoding="utf-8")

            code, output, errors = self.run_slice(
                root, "SKILL.md", "--document", "--max-bytes", "69"
            )

            self.assertEqual(0, code, errors)
            self.assertTrue(output.startswith("SKILL.md:1-9\n"))
            self.assertEqual("line\n" * 9, output[len("SKILL.md:1-9\n"):-len("[truncated]")])
            self.assertTrue(output.endswith("[truncated]"))
            self.assertLessEqual(len(output.encode("utf-8")), 69)

    def test_exact_byte_boundary_keeps_full_span_without_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "SKILL.md").write_text("hello\n", encoding="utf-8")

            code, output, errors = self.run_slice(
                root, "SKILL.md", "--document", "--max-bytes", "19"
            )

            self.assertEqual(0, code, errors)
            self.assertEqual("SKILL.md:1-1\nhello\n", output)
            self.assertNotIn("[truncated]", output)

    def test_empty_document_keeps_empty_full_span(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "SKILL.md").write_text("", encoding="utf-8")

            code, output, errors = self.run_slice(
                root, "SKILL.md", "--document", "--max-bytes", "14"
            )

            self.assertEqual(0, code, errors)
            self.assertEqual("SKILL.md:1-0\n", output)
            self.assertNotIn("[truncated]", output)

    def test_tiny_limit_fails_closed_without_provenance_loss(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "SKILL.md").write_text("line\n" * 3, encoding="utf-8")

            code, output, errors = self.run_slice(
                root, "SKILL.md", "--document", "--max-bytes", "23"
            )

            self.assertEqual(2, code)
            self.assertEqual("", output)
            self.assertEqual(
                "error: slice limit is too small for provenance and truncation marker\n",
                errors,
            )

    def test_truncated_provenance_does_not_claim_one_thousand_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "SKILL.md").write_text("line\n" * 1000, encoding="utf-8")

            code, output, errors = self.run_slice(
                root, "SKILL.md", "--document", "--max-bytes", "64"
            )

            self.assertEqual(0, code, errors)
            self.assertTrue(output.startswith("SKILL.md:1-8\n"))
            self.assertNotIn("SKILL.md:1-1000", output)
            self.assertEqual("line\n" * 8, output[len("SKILL.md:1-8\n"):-len("[truncated]")])

    def test_json_schema_and_read_only_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENTS.md").write_text("Use this.\n", encoding="utf-8")
            before = {
                path.relative_to(root).as_posix(): path.stat().st_mtime_ns
                for path in root.rglob("*") if path.is_file()
            }
            code, result, _ = self.run_scan(root)
            after = {
                path.relative_to(root).as_posix(): path.stat().st_mtime_ns
                for path in root.rglob("*") if path.is_file()
            }
            self.assertEqual(0, code)
            self.assertEqual(before, after)
            self.assertEqual(
                 {"version", "root", "scanned_files", "matched_units", "skipped",
                  "scan_id", "ignored_guidance_count", "truncated", "errors"},
                 set(result),
            )
            self.assertEqual(0, len(result["errors"]))

    def test_missing_root_returns_two(self):
        code, _, errors = self.run_scan(Path("missing-target"))
        self.assertEqual(2, code)
        self.assertIn("not a directory", errors)

    def test_ignored_catalogue_guidance_is_scanned_but_prose_is_not(self):
        fixture = (
            Path(__file__).resolve().parent.parent
            / "evals" / "fixtures" / "target-ignored-guidance"
        )

        code, result, _ = self.run_scan(fixture)

        self.assertEqual(0, code)
        by_path = {unit["path"]: unit for unit in result["matched_units"]}
        self.assertIn(".claude/commands/local-review.md", by_path)
        command = by_path[".claude/commands/local-review.md"]
        self.assertEqual("catalogue", command["source_scope"])
        self.assertTrue(command["ignored_by_git"])
        self.assertNotIn("notes.md", by_path)
        self.assertEqual(1, result["ignored_guidance_count"])

    def test_ignored_nested_known_basename_is_scanned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ignored = root / "local-config"
            ignored.mkdir()
            (ignored / "AGENTS.md").write_text("Use the rules.\n", encoding="utf-8")
            (root / ".gitignore").write_text("local-config/\n", encoding="utf-8")

            code, result, _ = self.run_scan(root)

            self.assertEqual(0, code)
            unit = result["matched_units"][0]
            self.assertEqual("local-config/AGENTS.md", unit["path"])
            self.assertEqual("catalogue", unit["source_scope"])
            self.assertTrue(unit["ignored_by_git"])

    def test_ignored_arbitrary_file_is_skipped_and_hard_exclusion_is_pruned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ignored = root / "archive"
            ignored.mkdir()
            (ignored / "notes.md").write_text(
                "\n".join(["Read this."] * 8) + "\n", encoding="utf-8"
            )
            dependencies = root / "node_modules"
            dependencies.mkdir()
            (dependencies / "AGENTS.md").write_text("Use this.\n", encoding="utf-8")
            (root / ".gitignore").write_text("archive/\n", encoding="utf-8")

            code, result, _ = self.run_scan(root)

            self.assertEqual(0, code)
            self.assertEqual([], result["matched_units"])
            skipped = {item["path"]: item["reason"] for item in result["skipped"]}
            self.assertEqual("excluded:.gitignore", skipped["archive/notes.md"])
            self.assertEqual("excluded:default-directory", skipped["node_modules"])
            self.assertNotIn("archive", skipped)

    def test_document_slice_supports_headingless_files_and_byte_bound(self):
        fixture = (
            Path(__file__).resolve().parent.parent
            / "evals" / "fixtures" / "target-unheaded-guidance"
        )

        code, output, errors = self.run_slice(
            fixture, "AGENTS.md", "--document", "--max-bytes", "96"
        )

        self.assertEqual(0, code, errors)
        self.assertLessEqual(len(output.encode("utf-8")), 96)
        self.assertIn("AGENTS.md:1-2", output)
        self.assertIn("Run the deployment check.", output)

    def test_document_slice_handles_empty_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "SKILL.md").write_text("", encoding="utf-8")

            code, output, errors = self.run_slice(root, "SKILL.md", "--document")

            self.assertEqual(0, code, errors)
            self.assertEqual("SKILL.md:1-0\n", output)

    def test_document_and_section_selectors_are_mutually_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENTS.md").write_text("# Intro\nbody\n", encoding="utf-8")
            output, errors = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                with self.assertRaises(SystemExit) as raised:
                    scan_guidance.main([
                        "slice", str(root), "AGENTS.md", "--document",
                        "--section", "Intro",
                    ])
            self.assertEqual(2, raised.exception.code)

    def test_slice_requires_scan_id_before_reading_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "secret.json").write_text('{"secret": true}\n', encoding="utf-8")
            output, errors = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                with self.assertRaises(SystemExit) as raised:
                    scan_guidance.main([
                        "slice", str(root), "secret.json", "--document"
                    ])

            self.assertEqual(2, raised.exception.code)
            self.assertEqual("", output.getvalue())
            self.assertIn("the following arguments are required: --scan-id", errors.getvalue())
            self.assertNotIn("secret", errors.getvalue())

    def test_gitignore_read_errors_emit_json_exit_two(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENTS.md").write_text("Read this.\n", encoding="utf-8")
            with mock.patch.object(
                scan_guidance, "_read_gitignore", side_effect=OSError("D:/private/.gitignore")
            ):
                code, result, errors = self.run_scan(root)

            self.assertEqual(2, code)
            self.assertEqual("", errors)
            self.assertEqual([], result["matched_units"])
            self.assertEqual(
                [{"path": ".gitignore", "error": "gitignore read failed"}],
                result["errors"],
            )
            self.assertNotIn("D:/private", json.dumps(result))

    def test_scan_id_rejects_changed_file_before_document_slice(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "AGENTS.md"
            original = "Run the deployment check.\n"
            path.write_text(original, encoding="utf-8")
            code, result, errors = self.run_scan(root)
            self.assertEqual(0, code, errors)
            scan_id = result["scan_id"]

            code, output, errors = self.run_slice(
                root, "AGENTS.md", "--document", "--scan-id", scan_id
            )
            self.assertEqual(0, code, errors)
            self.assertIn(original, output)

            path.write_text("Changed after scan.\n", encoding="utf-8")
            code, output, errors = self.run_slice(
                root, "AGENTS.md", "--document", "--scan-id", scan_id
            )
            self.assertEqual(2, code)
            self.assertEqual("", output)
            self.assertNotIn("Changed after scan", errors)

    def test_scan_id_rejects_post_recompute_freshness_race(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "AGENTS.md"
            path.write_text("Run the original check.\n", encoding="utf-8")
            code, result, errors = self.run_scan(root)
            self.assertEqual(0, code, errors)
            scan_id = result["scan_id"]

            original_read = scan_guidance.SafeRoot.read_bytes_with_stat
            calls = 0

            def read_with_race(safe_root, relative_path):
                nonlocal calls
                if relative_path == "AGENTS.md":
                    calls += 1
                if relative_path == "AGENTS.md" and calls == 2:
                    path.write_text("Changed after recompute.\n", encoding="utf-8")
                return original_read(safe_root, relative_path)

            with mock.patch.object(
                scan_guidance.SafeRoot,
                "read_bytes_with_stat",
                autospec=True,
                side_effect=read_with_race,
            ):
                code, output, errors = self.run_slice(
                    root, "AGENTS.md", "--document", "--scan-id", scan_id
                )

            self.assertEqual(2, code)
            self.assertEqual("", output)
            self.assertIn("digest does not match inventory", errors)
            self.assertEqual(2, calls)

    def test_scan_id_authorizes_only_matched_inventory_units(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENTS.md").write_text("# Rules\nRun the check.\n", encoding="utf-8")
            (root / "secret.json").write_text('{"secret": true}\n', encoding="utf-8")
            (root / "notes.md").write_text("Read once.\n", encoding="utf-8")
            (root / "package-lock.json").write_text(
                '{"name": "ignored-lock"}\n', encoding="utf-8"
            )
            (root / "ignored.md").write_text("\n".join(["Run this."] * 8), encoding="utf-8")
            (root / ".gitignore").write_text("ignored.md\n", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "AGENTS.md").write_text(
                "Run the ignored dependency rule.\n", encoding="utf-8"
            )

            code, result, errors = self.run_scan(root)
            self.assertEqual(0, code, errors)
            self.assertTrue(result["scan_id"].startswith("v2:"))
            matched = {unit["path"] for unit in result["matched_units"]}
            self.assertEqual({"AGENTS.md"}, matched)

            code, output, errors = self.run_slice(
                root, "AGENTS.md", "--document", "--scan-id", result["scan_id"]
            )
            self.assertEqual(0, code, errors)
            self.assertIn("Run the check.", output)

            for relative in (
                "secret.json",
                "notes.md",
                "package-lock.json",
                "ignored.md",
                "node_modules/AGENTS.md",
            ):
                code, output, errors = self.run_slice(
                    root, relative, "--document", "--scan-id", result["scan_id"]
                )
                self.assertEqual(2, code, relative)
                self.assertEqual("", output, relative)
                self.assertNotIn("secret", errors)

    def test_ignored_two_level_known_basename_is_scanned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "local-config" / "deep"
            nested.mkdir(parents=True)
            (nested / "AGENTS.md").write_text("Use the deep rules.\n", encoding="utf-8")
            (root / ".gitignore").write_text("local-config/\n", encoding="utf-8")

            code, result, errors = self.run_scan(root)

            self.assertEqual(0, code, errors)
            by_path = {unit["path"]: unit for unit in result["matched_units"]}
            self.assertIn("local-config/deep/AGENTS.md", by_path)
            self.assertTrue(by_path["local-config/deep/AGENTS.md"]["ignored_by_git"])

    def test_nested_ignored_catalogue_roots_are_scanned_but_prose_is_unopened(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "sandbox"
            (workspace / ".cursor" / "rules").mkdir(parents=True)
            (workspace / ".github").mkdir(parents=True)
            (workspace / "docs" / "runbooks").mkdir(parents=True)
            (workspace / "scratch").mkdir(parents=True)
            (workspace / ".cursor" / "rules" / "review.mdc").write_text(
                "Always review locally.\n", encoding="utf-8"
            )
            (workspace / ".github" / "copilot-instructions.md").write_text(
                "Use the Copilot rules.\n", encoding="utf-8"
            )
            (workspace / "docs" / "runbooks" / "deploy.md").write_text(
                "Run the deploy checklist.\n", encoding="utf-8"
            )
            (workspace / "scratch" / "notes.md").write_text(
                "\n".join(["Run this ignored prose."] * 8) + "\n", encoding="utf-8"
            )
            (root / ".gitignore").write_text("sandbox/\n", encoding="utf-8")

            original = scan_guidance.SafeRoot.read_bytes_with_stat

            def guarded_read(safe_root, relative):
                self.assertNotEqual("sandbox/scratch/notes.md", relative)
                return original(safe_root, relative)

            with mock.patch.object(
                scan_guidance.SafeRoot, "read_bytes_with_stat", guarded_read
            ):
                code, result, errors = self.run_scan(root)

            self.assertEqual(0, code, errors)
            by_path = {unit["path"]: unit for unit in result["matched_units"]}
            self.assertIn("sandbox/.cursor/rules/review.mdc", by_path)
            self.assertIn("sandbox/.github/copilot-instructions.md", by_path)
            self.assertIn("sandbox/docs/runbooks/deploy.md", by_path)
            self.assertNotIn("sandbox/scratch/notes.md", by_path)
            self.assertTrue(all(unit["ignored_by_git"] for unit in by_path.values()))

    def test_scan_errors_emit_json_exit_two_and_stable_messages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENTS.md").write_text("Read this.\n", encoding="utf-8")
            original = scan_guidance.SafeRoot.read_bytes_with_stat

            def failing_read(safe_root, relative):
                if relative == "AGENTS.md":
                    raise scan_guidance.SafePathError("D:/secret/path/AGENTS.md")
                return original(safe_root, relative)

            with mock.patch.object(
                scan_guidance.SafeRoot, "read_bytes_with_stat", failing_read
            ):
                code, result, errors = self.run_scan(root)

            self.assertEqual(2, code)
            self.assertEqual("", errors)
            self.assertEqual([], result["matched_units"])
            self.assertEqual(
                [{"path": "AGENTS.md", "error": "candidate rejected by containment"}],
                result["errors"],
            )
            self.assertNotIn(str(root), json.dumps(result["errors"]))

    def test_walk_errors_emit_json_exit_two_and_stable_messages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def broken_walk(_root, topdown=True, onerror=None):
                error = OSError("D:/private/walk detail")
                error.filename = os.fspath(root / "blocked")
                onerror(error)
                return iter(())

            with mock.patch.object(scan_guidance.os, "walk", broken_walk):
                code, result, errors = self.run_scan(root)

            self.assertEqual(2, code)
            self.assertEqual("", errors)
            self.assertEqual([{"path": "blocked", "error": "walk failed"}], result["errors"])

    def test_slice_rejects_v1_scan_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENTS.md").write_text("Run the check.\n", encoding="utf-8")

            code, output, errors = self.run_slice(
                root, "AGENTS.md", "--document", "--scan-id", "old-v1-token"
            )

            self.assertEqual(2, code)
            self.assertEqual("", output)
            self.assertIn("scan id", errors)

    def test_custom_inventory_max_bytes_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENTS.md").write_text("# Rules\n" + ("Run this.\n" * 8), encoding="utf-8")

            code, result, errors = self.run_scan(root, "--max-bytes", "16")
            self.assertEqual(0, code, errors)
            self.assertTrue(result["scan_id"].startswith("v2:16:"))
            self.assertEqual("oversize", result["matched_units"][0]["status"])

            code, output, errors = self.run_slice(
                root, "AGENTS.md", "--document", "--scan-id", result["scan_id"],
                "--max-bytes", "64"
            )
            self.assertEqual(0, code, errors)
            self.assertLessEqual(len(output.encode("utf-8")), 64)

    def test_scan_rejects_file_symlink_outside_root(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            external = Path(outside) / "secret.md"
            external.write_text("OUTSIDE SECRET\n", encoding="utf-8")
            self.make_file_symlink(root / "AGENTS.md", external)

            code, result, errors = self.run_scan(root)

            self.assertEqual(2, code)
            self.assertNotIn("OUTSIDE SECRET", json.dumps(result))
            self.assertNotIn("OUTSIDE SECRET", errors)
            self.assertEqual([], result["matched_units"])
            self.assertTrue(result["errors"])

    def test_slice_rejects_parent_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            root.mkdir()
            external = root.parent / "outside.md"
            external.write_text("# Intro\nOUTSIDE SECRET\n", encoding="utf-8")
            try:
                code, output, errors = self.run_slice(
                    root, "../outside.md", "--section", "Intro"
                )
                self.assertEqual(2, code)
                self.assertNotIn("OUTSIDE SECRET", output)
                self.assertNotIn("OUTSIDE SECRET", errors)
            finally:
                external.unlink()

    def test_slice_rejects_absolute_path(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            external = Path(outside) / "secret.md"
            external.write_text("# Intro\nOUTSIDE SECRET\n", encoding="utf-8")

            code, output, errors = self.run_slice(
                root, os.fspath(external), "--section", "Intro"
            )

            self.assertEqual(2, code)
            self.assertNotIn("OUTSIDE SECRET", output)
            self.assertNotIn("OUTSIDE SECRET", errors)

    def test_slice_rejects_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            external = Path(outside) / "secret.md"
            external.write_text("# Intro\nOUTSIDE SECRET\n", encoding="utf-8")
            code, result, errors = self.run_scan(root)
            self.assertEqual(0, code, errors)
            self.make_file_symlink(root / "link.md", external)

            code, output, errors = self.run_slice(
                root, "link.md", "--section", "Intro", "--scan-id", result["scan_id"]
            )

            self.assertEqual(2, code)
            self.assertNotIn("OUTSIDE SECRET", output)
            self.assertNotIn("OUTSIDE SECRET", errors)

    def test_out_must_stay_inside_root(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            (root / "AGENTS.md").write_text("Use this.\n", encoding="utf-8")
            target = Path(outside) / "inventory.json"

            code, result, errors = self.run_scan(root, "--out", os.fspath(target))

            self.assertEqual(2, code)
            self.assertNotIn("OUTSIDE", json.dumps(result))
            self.assertNotIn("OUTSIDE", errors)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
