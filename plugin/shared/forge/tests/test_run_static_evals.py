"""Tests for the trusted, deterministic Forge static-eval runner."""

from __future__ import annotations

import json
import contextlib
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from plugin.shared.forge.evals import run_static_evals


class StaticEvalRunnerTests(unittest.TestCase):
    def write_json(self, root: Path, relative: str, value) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def case(self, case_id: str, kind: str, **check):
        return {
            "id": case_id,
            "static": {
                "kind": kind,
                "result": {"status": "passed"},
                **check,
            },
        }

    def static_corpus_case(self, case_id: str, kind: str, **check):
        """Create a v1-compatible case for exercising the CLI trust boundary."""
        return {
            "version": 1,
            "id": case_id,
            "kind": "execution",
            "category": "positive",
            "prompt": "Run the deterministic fixture check.",
            "expected": {"outcome": {"assertions": ["fixture is safe"]}},
            "graders": [{"type": "llm-judge", "rubric": "Static fixture coverage."}],
            "static": {
                "kind": kind,
                "result": {"status": "passed"},
                **check,
            },
        }

    def assert_invalid_corpus(self, root: Path, case, error_fragment: str) -> None:
        self.write_json(root, "execution.json", [case])
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = run_static_evals.main(["--evals", str(root), "--json"])
        self.assertEqual(2, exit_code)
        report = json.loads(stdout.getvalue())
        self.assertIn(error_fragment, report["error"])

    def test_each_trusted_validator_kind_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fixtures").mkdir()
            (root / "fixtures" / "exists.txt").write_text("present", encoding="utf-8")
            self.write_json(root, "fixtures/artifact.json", {"name": "forge", "items": []})
            report = run_static_evals.evaluate_cases(
                [
                    self.case("02-shape", "artifact-shape", fixture="fixtures/artifact.json", required={"name": "string", "items": "array"}),
                    self.case("01-exists", "file-exists", fixture="fixtures/exists.txt"),
                ],
                root,
            )
            self.assertEqual(2, report["summary"]["passed"])
            self.assertEqual(["01-exists", "02-shape"], [item["id"] for item in report["results"]["passed"]])

    def test_rejects_unsafe_or_malformed_static_data(self):
        bad_cases = (
            self.case("command", "file-exists", fixture="fixtures/a", command="touch owned"),
            self.case("unknown", "shell", result={"status": "passed"}),
            self.case("traversal", "file-exists", fixture="../secret"),
            self.case("missing", "file-exists", fixture="fixtures/missing"),
            {"id": "malformed", "static": {"kind": "artifact-shape", "result": []}},
            {"id": "unclassified", "static": {"kind": "artifact-shape", "fixture": "fixtures/artifact.json", "required": {"name": "string"}, "result": {"status": "failed"}}},
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_json(root, "fixtures/artifact.json", {"name": "forge"})
            for case in bad_cases:
                with self.subTest(case=case["id"]):
                    with self.assertRaises(run_static_evals.CorpusError):
                        run_static_evals.evaluate_cases([case], root)

    def test_rejects_commands_in_declared_fixture_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_json(root, "fixtures/declared/input.json", {"nested": {"command": "owned"}})
            case = self.static_corpus_case("declared-command", "file-exists", fixture="fixtures/declared/input.json")
            del case["static"]
            case["fixtures"] = ["fixtures/declared"]
            self.assert_invalid_corpus(
                root,
                case,
                "command fields are forbidden in fixture JSON",
            )

    def test_rejects_nested_commands_in_parsed_json_fixtures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_json(root, "fixtures/artifact.json", {"nested": {"command": "owned"}})
            self.assert_invalid_corpus(
                root,
                self.static_corpus_case("artifact", "artifact-shape", fixture="fixtures/artifact.json", required={"name": "string"}),
                "command fields are forbidden in fixture JSON",
            )

    def test_unavailable_capabilities_are_never_passed(self):
        case = {
            "id": "needs-model",
            "graders": [{"type": "llm-judge", "rubric": "Needs a model."}],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skipped = run_static_evals.evaluate_cases([case], root, capabilities=set())
            unmeasured = run_static_evals.evaluate_cases([case], root, capabilities={"llm-judge"})
        self.assertEqual("skipped", skipped["results"]["skipped"][0]["status"])
        self.assertEqual("unmeasured", unmeasured["results"]["unmeasured"][0]["status"])
        self.assertEqual(0, skipped["summary"]["passed"])
        self.assertEqual(0, unmeasured["summary"]["passed"])

    def test_failure_result_has_stable_classification_and_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_json(root, "fixtures/artifact.json", {"name": 1})
            case = self.case("failure", "artifact-shape", fixture="fixtures/artifact.json", required={"name": "string"})
            first = run_static_evals.evaluate_cases([case], root)
            second = run_static_evals.evaluate_cases([case], root)
        self.assertEqual(first, second)
        failed = first["results"]["failed"][0]
        self.assertEqual("assertion", failed["classification"])
        self.assertEqual(1, first["summary"]["failed"])

    def test_cli_runs_by_path_from_outside_the_repository(self):
        script = Path(run_static_evals.__file__).resolve()
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            (root / "fixtures").mkdir()
            (root / "fixtures" / "exists.txt").write_text("present", encoding="utf-8")
            self.write_json(root, "execution.json", [self.static_corpus_case("01-exists", "file-exists", fixture="fixtures/exists.txt")])
            completed = subprocess.run(
                [sys.executable, str(script), "--evals", str(root), "--json"],
                cwd=outside,
                capture_output=True,
                text=True,
            )
        self.assertEqual(0, completed.returncode, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(1, report["summary"]["passed"])

    def test_cli_runs_from_an_installed_plugin_layout(self):
        plugin_root = Path(run_static_evals.__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as installed, tempfile.TemporaryDirectory() as outside:
            installed_root = Path(installed)
            shutil.copytree(plugin_root, installed_root, dirs_exist_ok=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(installed_root / "shared" / "forge" / "evals" / "run_static_evals.py"),
                    "--evals",
                    str(installed_root / "shared" / "forge" / "evals"),
                    "--json",
                ],
                cwd=outside,
                capture_output=True,
                text=True,
            )
        self.assertEqual(0, completed.returncode, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(0, report["summary"]["failed"])
        self.assertGreater(report["summary"]["passed"], 0)

    def test_missing_v1_validator_raises_corpus_error(self):
        original = run_static_evals.VALIDATOR_PATH
        original_paths = run_static_evals.VALIDATOR_PATHS
        original_module = run_static_evals._V1_VALIDATOR_MODULE
        run_static_evals.VALIDATOR_PATH = original.parent / "does-not-exist.py"
        run_static_evals.VALIDATOR_PATHS = (run_static_evals.VALIDATOR_PATH,)
        run_static_evals._V1_VALIDATOR_MODULE = None
        try:
            with self.assertRaises(run_static_evals.CorpusError):
                run_static_evals._load_v1_validator()
        finally:
            run_static_evals.VALIDATOR_PATH = original
            run_static_evals.VALIDATOR_PATHS = original_paths
            run_static_evals._V1_VALIDATOR_MODULE = original_module

    def test_cli_json_is_valid_for_the_current_shared_corpus(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = run_static_evals.main(["--json"])
        report = json.loads(stdout.getvalue())
        self.assertEqual(0, exit_code)
        self.assertEqual(0, report["summary"]["failed"])
        self.assertEqual(0, report["summary"]["unmeasured"])
        self.assertEqual(
            report["summary"]["total"],
            report["summary"]["passed"] + report["summary"]["skipped"],
        )


if __name__ == "__main__":
    unittest.main()
