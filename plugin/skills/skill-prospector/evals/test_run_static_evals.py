#!/usr/bin/env python3
"""Mutation tests for the deterministic generated-plan validator."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import run_static_evals


class PlanArtifactShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_path = (
            run_static_evals.ROOT / "evals" / "fixtures" / "expected-plan.md"
        )
        cls.fixture = cls.fixture_path.read_text(encoding="utf-8")

    def validate(self, content):
        with tempfile.TemporaryDirectory(
            prefix="prospector-plan-"
        ) as directory:
            path = Path(directory) / "plan.md"
            path.write_text(content, encoding="utf-8")
            with mock.patch.object(run_static_evals, "_resolve", return_value=path):
                return run_static_evals.plan_artifact_shape({"path": "mutation.md"})

    def assert_invalid(self, content, expected_reason):
        valid, reasons = self.validate(content)
        self.assertFalse(valid)
        self.assertTrue(
            any(expected_reason in reason for reason in reasons),
            f"{expected_reason!r} missing from {reasons!r}",
        )

    def test_canonical_fixture_is_valid(self):
        self.assertEqual((True, []), self.validate(self.fixture))

    def test_field_moved_to_follow_up_cannot_satisfy_candidate(self):
        content = self.fixture.replace(
            "invocation evidence: The workflow is safe to discover and useful when named by the user.\n",
            "",
            1,
        ).replace(
            "Run host validation before release.",
            "Run host validation before release.\ninvocation evidence: moved out of the candidate.",
            1,
        )
        self.assert_invalid(content, "invocation evidence")

    def test_duplicate_candidate_field_is_rejected(self):
        content = self.fixture.replace(
            "name: example-workflow\n",
            "name: example-workflow\nname: duplicate\n",
            1,
        )
        self.assert_invalid(content, "must occur exactly once")

    def test_empty_candidate_field_is_rejected(self):
        content = self.fixture.replace(
            "acceptance criteria: the workflow completes and reports its result.",
            "acceptance criteria: ",
            1,
        )
        self.assert_invalid(content, "is empty")

    def test_reordered_candidate_fields_are_rejected(self):
        content = self.fixture.replace(
            "trigger: Use when the workflow is requested.\n"
            "sources: docs/runbooks/deploy.md:Deploy",
            "sources: docs/runbooks/deploy.md:Deploy\n"
            "trigger: Use when the workflow is requested.",
            1,
        )
        self.assert_invalid(content, "invalid field order")

    def test_invocation_policy_enum_is_rejected_when_unknown(self):
        content = self.fixture.replace(
            "invocation policy: both", "invocation policy: sometimes", 1
        )
        self.assert_invalid(content, "invalid invocation policy")

    def test_candidate_header_id_must_match_id_field(self):
        content = self.fixture.replace(
            "### Candidate: example-workflow", "### Candidate: different-id", 1
        )
        self.assert_invalid(content, "header/id mismatch")

    def test_duplicate_candidate_ids_are_rejected(self):
        content = self.fixture.replace(
            "\n## Rejected and deferred units",
            "\n### Candidate: example-workflow\n\n## Rejected and deferred units",
            1,
        )
        self.assert_invalid(content, "duplicate candidate id")

    def test_duplicate_inventory_paths_are_rejected(self):
        row = "| docs/runbooks/deploy.md | stays-as-runbook |"
        content = self.fixture.replace(row, row + "\n" + row, 1)
        self.assert_invalid(content, "duplicate discovery inventory path")

    def test_inventory_unknown_candidate_reference_is_rejected(self):
        content = self.fixture.replace(
            "| docs/runbooks/deploy.md | stays-as-runbook |",
            "| docs/runbooks/deploy.md | covered-by-candidate:missing |",
            1,
        )
        self.assert_invalid(content, "unknown candidate")

    def test_zero_candidate_plan_remains_valid_without_candidate_reference(self):
        start = self.fixture.index("### Candidate: example-workflow")
        end = self.fixture.index("\n## Rejected and deferred units", start)
        content = self.fixture[:start] + self.fixture[end:]
        self.assertEqual((True, []), self.validate(content))

    def test_authority_moved_to_follow_up_is_rejected(self):
        content = self.fixture.replace("authority: explicit\n", "", 1).replace(
            "Run host validation before release.",
            "Run host validation before release.\nauthority: explicit",
            1,
        )
        self.assert_invalid(content, "authority field")


if __name__ == "__main__":
    unittest.main()
