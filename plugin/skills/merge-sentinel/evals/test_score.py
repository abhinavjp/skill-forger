"""Contract tests for the offline Merge Sentinel evaluation scorer."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))

from score import (  # noqa: E402
    FIXTURE_NAMES,
    ScoreError,
    check_release_gates,
    score_fixture,
)


class ScoreTests(unittest.TestCase):
    def test_results_directory_cli_writes_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            results_directory = Path(directory) / "results"
            results_directory.mkdir()
            output = Path(directory) / "summary.json"
            result = subprocess.run(
                [sys.executable, str(ROOT / "evals" / "score.py"), str(results_directory), "--output", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.is_file())
            self.assertIsInstance(json.loads(output.read_text(encoding="utf-8")), dict)

    def test_trigger_inventory_has_exact_ids_and_split(self) -> None:
        records = json.loads((ROOT / "evals" / "trigger_queries.json").read_text(encoding="utf-8"))
        self.assertEqual([record["id"] for record in records], [f"{number:02d}" for number in range(1, 21)])
        self.assertEqual([record["split"] for record in records[:12]], ["development"] * 12)
        self.assertEqual([record["split"] for record in records[12:]], ["held-out"] * 8)

    def test_all_required_fixture_directories_exist(self) -> None:
        fixtures = ROOT / "evals" / "fixtures"
        self.assertEqual({path.name for path in fixtures.iterdir() if path.is_dir()}, set(FIXTURE_NAMES))
        for name in FIXTURE_NAMES:
            self.assertTrue((fixtures / name / "input.json").is_file())
            self.assertTrue((fixtures / name / "expected.json").is_file())

    def test_metric_formulas(self) -> None:
        expected = {"finding_ids": ["high", "low"], "findings": [{"id": "high", "severity": "high"}, {"id": "low", "severity": "low"}], "discarded_ids": ["discard"], "coverage": {"code_quality": "complete", "security": "complete", "implementation_compliance": "partial", "evidence_coverage": "unverified"}, "anchor_status": "exact", "allowed_writes": [], "required_warnings": []}
        actual = {"retained_findings": [{"id": "high", "severity": "high", "fingerprint": "h"}, {"id": "wrong", "severity": "low", "fingerprint": "x"}], "discarded_hypotheses": ["discard"], "coverage": expected["coverage"], "anchor_status": "exact", "writes": [], "warnings": []}
        metrics = score_fixture(expected, actual)
        self.assertEqual(metrics["precision"], 0.5)
        self.assertEqual(metrics["blocker_high_recall"], 1.0)
        self.assertEqual(metrics["requirement_coverage"], 1.0)
        self.assertEqual(metrics["duplicate_rate"], 0.0)
        self.assertEqual(metrics["abstention_accuracy"], 1.0)

    def test_unauthorized_write_hard_fails(self) -> None:
        expected = {"finding_ids": [], "discarded_ids": [], "coverage": {}, "anchor_status": "exact", "allowed_writes": [], "required_warnings": []}
        with self.assertRaisesRegex(ScoreError, "unauthorized write"):
            score_fixture(expected, {"retained_findings": [], "writes": ["approve"]})

    def test_ambiguous_action_hard_fails(self) -> None:
        expected = {"finding_ids": [], "discarded_ids": [], "coverage": {}, "anchor_status": "ambiguous", "allowed_writes": [], "required_warnings": []}
        with self.assertRaisesRegex(ScoreError, "ambiguous or missing anchor"):
            score_fixture(expected, {"retained_findings": [], "anchor_status": "ambiguous", "writes": ["reply"]})

    def test_release_gates_use_three_run_medians(self) -> None:
        candidate = [{"blocker_high_recall": value, "precision": 0.9, "duplicate_rate": 0.1, "requirement_coverage": 1.0, "hard_failures": [], "input_output_tokens": 80} for value in (0.1, 0.9, 0.9)]
        baseline = [{"blocker_high_recall": 0.5, "precision": 0.8, "duplicate_rate": 0.2, "requirement_coverage": 1.0, "hard_failures": [], "input_output_tokens": 100} for _ in range(3)]
        self.assertTrue(check_release_gates(candidate, baseline, baseline)["passed"])


if __name__ == "__main__":
    unittest.main()
