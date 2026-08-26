"""Quality benchmark contracts are separate from controller-safety fixtures."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class QualitySuiteTests(unittest.TestCase):
    def test_quality_cases_cover_original_reviewer_patterns(self) -> None:
        inputs = json.loads((ROOT / "evals" / "quality-inputs.json").read_text(encoding="utf-8"))["cases"]
        expected = json.loads((ROOT / "evals" / "quality-contracts.json").read_text(encoding="utf-8"))["cases"]
        self.assertEqual(len(inputs), 10)
        self.assertEqual(len(expected), 10)
        contracts = {
            "clean-preserved-contract": [],
            "inverted-null-guard": ["inverted-null-guard"],
            "tenant-scope-removed": ["tenant-scope-removed"],
            "permission-key-mismatch": ["permission-key-mismatch"],
            "bulk-filter-asymmetry": ["bulk-filter-asymmetry"],
            "intentional-email-queue-done": [],
            "unguarded-service-response-output": ["unguarded-service-response-output"],
            "duplicate-html-class": ["duplicate-html-class"],
            "missing-required-audit-event": ["missing-required-audit-event"],
            "migration-dependency-missing": ["migration-dependency-missing"],
        }
        self.assertEqual({case["id"]: case["expected_findings"] for case in expected}, contracts)
        self.assertEqual({case["id"] for case in inputs}, set(contracts))
        self.assertTrue(all(case["input"] for case in inputs))


if __name__ == "__main__":
    unittest.main()
