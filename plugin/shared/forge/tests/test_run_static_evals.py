"""Tests for the trusted, deterministic Forge static-eval runner."""

from __future__ import annotations

import json
import contextlib
import io
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
            self.write_json(
                root,
                "fixtures/adapter/input.json",
                {
                    "request": {"delivery_operation": "publish"},
                    "artifact_location_conventions": {"specification": "spec.md", "plan": "plan.md"},
                    "okf_provider": {
                        "tree": [{"path": "okf/leaf.md", "kind": "file", "leaf": True}],
                        "requested_references": ["okf/leaf.md"],
                        "unavailable_knowledge": [{"path": "okf/missing.md", "reason": "denied"}],
                    },
                    "authorized_delivery_operations": ["prepare"],
                    "approval_policy": {
                        "planning": {"approvers": ["functional-owner"]},
                        "implementation": {"approvers": ["technical-owner"]},
                    },
                },
            )
            self.write_json(
                root,
                "fixtures/adapter/expected.json",
                {
                    "adapter_handling": {"preserve_artifact_locations": {"specification": "spec.md", "plan": "plan.md"}, "refused_delivery_operation": "publish"},
                    "knowledge_handling": {"selected_leaf_paths": ["okf/leaf.md"], "unavailable_knowledge": [{"path": "okf/missing.md", "status": "UNMEASURED", "reason": "denied"}]},
                },
            )
            state = {
                "artifacts": {
                    "specification": {
                        "hash": "spec", "revision": "1",
                        "approval": {"artifact_hash": "spec", "revision": "1", "actor": "owner", "intent": "artifact", "approved_at": 1},
                    },
                    "plan": {
                        "hash": "plan", "revision": "1",
                        "approval": {"artifact_hash": "plan", "revision": "1", "actor": "owner", "intent": "artifact", "approved_at": 2},
                    },
                }
            }
            report = run_static_evals.evaluate_cases(
                [
                    self.case("05-adapter", "adapter-parity", fixture="fixtures/adapter"),
                    self.case("04-normalization", "normalization", source="a  \r\n\r\n\r\nb", normalized="a\n\nb"),
                    self.case("03-transition", "workflow-transition", state=state, target="implementation", expected_allowed=True),
                    self.case("02-shape", "artifact-shape", fixture="fixtures/artifact.json", required={"name": "string", "items": "array"}),
                    self.case("01-exists", "file-exists", fixture="fixtures/exists.txt"),
                ],
                root,
            )
            self.assertEqual(5, report["summary"]["passed"])
            self.assertEqual(["01-exists", "02-shape", "03-transition", "04-normalization", "05-adapter"], [item["id"] for item in report["results"]["passed"]])

    def test_rejects_unsafe_or_malformed_static_data(self):
        bad_cases = (
            self.case("command", "file-exists", fixture="fixtures/a", command="touch owned"),
            self.case("unknown", "shell", result={"status": "passed"}),
            self.case("traversal", "file-exists", fixture="../secret"),
            self.case("missing", "file-exists", fixture="fixtures/missing"),
            {"id": "malformed", "static": {"kind": "normalization", "result": []}},
            {"id": "unclassified", "static": {"kind": "normalization", "source": "a", "normalized": "a", "result": {"status": "failed"}}},
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for case in bad_cases:
                with self.subTest(case=case["id"]):
                    with self.assertRaises(run_static_evals.CorpusError):
                        run_static_evals.evaluate_cases([case], root)

    def test_rejects_adapter_child_symlink_outside_the_eval_root(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            adapter = root / "fixtures" / "adapter"
            adapter.mkdir(parents=True)
            external_input = Path(outside) / "input.json"
            external_input.write_text('{"outside": true}', encoding="utf-8")
            try:
                (adapter / "input.json").symlink_to(external_input)
            except (NotImplementedError, OSError) as exc:
                self.skipTest("symlinks unavailable: {}".format(exc))
            self.write_json(root, "fixtures/adapter/expected.json", {})
            self.assert_invalid_corpus(
                root,
                self.static_corpus_case("adapter-symlink", "adapter-parity", fixture="fixtures/adapter"),
                "fixture path escapes the eval root",
            )

    def test_rejects_nested_commands_in_parsed_json_fixtures(self):
        cases = (
            ("adapter-input", "adapter-parity", "fixtures/adapter/input.json", {"nested": {"command": "owned"}}),
            ("adapter-expected", "adapter-parity", "fixtures/adapter/expected.json", {"nested": {"command": "owned"}}),
            ("artifact", "artifact-shape", "fixtures/artifact.json", {"nested": {"command": "owned"}}),
        )
        for case_id, kind, fixture_path, malicious_data in cases:
            with self.subTest(case=case_id), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                if kind == "adapter-parity":
                    self.write_json(root, "fixtures/adapter/input.json", {})
                    self.write_json(root, "fixtures/adapter/expected.json", {})
                    fixture = "fixtures/adapter"
                    check = {"fixture": fixture}
                else:
                    fixture = fixture_path
                    check = {"fixture": fixture, "required": {"name": "string"}}
                self.write_json(root, fixture_path, malicious_data)
                self.assert_invalid_corpus(
                    root,
                    self.static_corpus_case(case_id, kind, **check),
                    "command fields are forbidden in fixture JSON",
                )

    def test_rejects_commands_in_declared_fixture_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_json(root, "fixtures/declared/input.json", {"nested": {"command": "owned"}})
            case = self.static_corpus_case("declared-command", "normalization", source="a", normalized="a")
            del case["static"]
            case["fixtures"] = ["fixtures/declared"]
            self.assert_invalid_corpus(
                root,
                case,
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

    def test_gate_protection_and_designated_approver_policy(self):
        def state(spec_approved, plan_approved, plan_actor="technical-owner"):
            return {
                "current_actor": "forge-agent",
                "requires_spec_approval": True,
                "artifacts": {
                    "specification": {"hash": "spec", "revision": "1", **({"approval": {"artifact_hash": "spec", "revision": "1", "actor": "functional-owner", "intent": "artifact", "approved_at": 1}} if spec_approved else {})},
                    "plan": {"hash": "plan", "revision": "1", **({"approval": {"artifact_hash": "plan", "revision": "1", "actor": plan_actor, "intent": "artifact", "approved_at": 2}} if plan_approved else {})},
                },
            }

        policy = {"planning": ["functional-owner"], "implementation": ["technical-owner"]}
        cases = [
            self.case("spec-gate", "workflow-transition", state=state(False, False), target="implementation", expected_allowed=False, expected_code="GATE_REQUIRED", require_read_only=True),
            self.case("plan-gate", "workflow-transition", state=state(True, False), target="implementation", expected_allowed=False, expected_code="GATE_REQUIRED", require_read_only=True),
            self.case("approver", "workflow-transition", state=state(True, True, "other"), target="implementation", approval_policy=policy, expected_allowed=False, expected_code="GATE_REQUIRED"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            report = run_static_evals.evaluate_cases(cases, Path(directory))
        self.assertEqual(3, report["summary"]["passed"])

    def test_failure_result_has_stable_classification_and_summary(self):
        case = self.case("failure", "normalization", source="a", normalized="b")
        with tempfile.TemporaryDirectory() as directory:
            first = run_static_evals.evaluate_cases([case], Path(directory))
            second = run_static_evals.evaluate_cases([case], Path(directory))
        self.assertEqual(first, second)
        failed = first["results"]["failed"][0]
        self.assertEqual("assertion", failed["classification"])
        self.assertEqual(1, first["summary"]["failed"])

    def test_brain_adapter_parity_rejects_an_unauthorized_designated_approver(self):
        root = Path(__file__).resolve().parents[1] / "evals"
        state = {
            "current_actor": "forge-agent",
            "requires_spec_approval": True,
            "artifacts": {
                "specification": {"hash": "spec-r1", "revision": "spec-r1", "approval": {"artifact_hash": "spec-r1", "revision": "spec-r1", "actor": "functional-owner", "intent": "artifact", "approved_at": 1}},
                "plan": {"hash": "plan-r1", "revision": "plan-r1", "approval": {"artifact_hash": "plan-r1", "revision": "plan-r1", "actor": "not-technical-owner", "intent": "artifact", "approved_at": 2}},
            },
        }
        case = self.case(
            "brain-policy",
            "adapter-parity",
            fixture="fixtures/brain-adapter",
            approval_state=state,
            target="implementation",
            expected_allowed=False,
        )
        report = run_static_evals.evaluate_cases([case], root)
        self.assertEqual(1, report["summary"]["passed"])

    def test_cli_runs_by_path_from_outside_the_repository(self):
        script = Path(run_static_evals.__file__).resolve()
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            self.write_json(root, "execution.json", [self.static_corpus_case("01-normalization", "normalization", source="a", normalized="a")])
            completed = subprocess.run(
                [sys.executable, str(script), "--evals", str(root), "--json"],
                cwd=outside,
                capture_output=True,
                text=True,
            )
        self.assertEqual(0, completed.returncode, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(1, report["summary"]["passed"])

    def test_missing_v1_validator_raises_corpus_error(self):
        original = run_static_evals.VALIDATOR_PATH
        run_static_evals.VALIDATOR_PATH = original.parent / "does-not-exist.py"
        try:
            with self.assertRaises(run_static_evals.CorpusError):
                run_static_evals._load_v1_validator()
        finally:
            run_static_evals.VALIDATOR_PATH = original

    def test_cli_json_is_valid_for_the_current_shared_corpus(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = run_static_evals.main(["--json"])
        report = json.loads(stdout.getvalue())
        self.assertEqual(0, exit_code)
        self.assertEqual(report["summary"]["total"], report["summary"]["skipped"])


if __name__ == "__main__":
    unittest.main()
