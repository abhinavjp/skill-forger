#!/usr/bin/env python3
"""Unit tests for the read-only guidance scanner."""
from __future__ import annotations

import contextlib
import io
import json
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
            self.assertEqual(0, code)
            self.assertEqual("AGENTS.md", result["errors"][0]["path"])
            self.assertIn("denied", result["errors"][0]["error"])

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
            path = Path(directory) / "guide.md"
            path.write_text(
                "# Intro\nintro body\n## Rollback\nrollback body\n## Deploy\ndeploy body\n",
                encoding="utf-8",
            )
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = scan_guidance.main(["slice", str(path), "--section", "Rollback"])
            self.assertEqual(0, code)
            self.assertIn("rollback body", out.getvalue())
            self.assertIn(":3-4", out.getvalue())

            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = scan_guidance.main(["slice", str(path), "--section", "deploy"])
            self.assertEqual(0, code)
            self.assertIn("deploy body", out.getvalue())

            path.write_text("# Repeat\none\n# repeat\ntwo\n", encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = scan_guidance.main(["slice", str(path), "--section", "REPEAT"])
            self.assertEqual(3, code)
            self.assertIn("ambiguous", err.getvalue())

            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = scan_guidance.main(["slice", str(path), "--section", "Missing"])
            self.assertEqual(4, code)
            self.assertIn("not found", err.getvalue())

    def test_slice_respects_byte_bound_and_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "guide.md"
            path.write_text("# Intro\n" + ("long line\n" * 20), encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = scan_guidance.main([
                    "slice", str(path), "--section", "Intro", "--max-bytes", "64"
                ])
            rendered = out.getvalue()
            self.assertEqual(0, code)
            self.assertLessEqual(len(rendered.encode("utf-8")), 64)
            self.assertIn("[truncated]", rendered)

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
                 "truncated", "errors"},
                set(result),
            )
            self.assertEqual(0, len(result["errors"]))

    def test_missing_root_returns_two(self):
        code, _, errors = self.run_scan(Path("missing-target"))
        self.assertEqual(2, code)
        self.assertIn("not a directory", errors)


if __name__ == "__main__":
    unittest.main()
