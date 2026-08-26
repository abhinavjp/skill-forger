"""Contract tests for conditional Merge Sentinel reference assets."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"


class SkillAssetTests(unittest.TestCase):
    def read_reference(self, name: str) -> str:
        return (REFERENCES / name).read_text(encoding="utf-8")

    def test_reference_files_and_headings_exact(self) -> None:
        expected = {
            "implementation-compliance.md": [
                "# Implementation Compliance",
                "## Authority order",
                "## Requirement inventory",
                "## Forward trace",
                "## Reverse trace",
                "## Conflict Detected",
                "## Coverage result",
            ],
            "gitlab-transport.md": [
                "# GitLab Transport",
                "## Capability matrix",
                "## Acquisition",
                "## Operation routing",
                "## Freshness",
                "## Publication ledger",
                "## Verification",
            ],
            "risk-overlays.md": ["# Risk Overlays"],
            "finding-contract.md": ["# Finding Contract"],
            "review-patterns.md": [
                "# Review Patterns",
                "## Adversarial posture",
                "## Execution sizing",
                "## Domain overlay",
                "## Required passes",
                "## Comment quality",
            ],
            "summary-agent.md": [
                "# Summary Agent",
                "## Inputs",
                "## Publication round",
                "## Output contract",
                "## Signature",
            ],
            "rereview.md": [
                "# Re-review",
                "## Skip decision",
                "## Snapshot comparison",
                "## Per-finding packet",
                "## Semantic classification",
                "## Remote discussion action",
                "## Summary groups",
            ],
        }
        self.assertEqual({path.name for path in REFERENCES.glob("*.md")}, set(expected))
        for name, headings in expected.items():
            actual = [line for line in self.read_reference(name).splitlines() if line.startswith("#")]
            self.assertEqual(actual, headings, name)

    def test_authority_order_exact(self) -> None:
        content = self.read_reference("implementation-compliance.md")
        expected = [
            "explicit user instruction for this review",
            "formally approved specification or issue amendment",
            "issue description and acceptance criteria",
            "approved technical plan for implementation detail",
            "MR description as declared scope only",
            "tests and code as implementation evidence only",
        ]
        positions = [content.index(item) for item in expected]
        self.assertEqual(positions, sorted(positions))
        for status in ("implemented", "partial", "contradicted", "missing", "not-applicable", "unverified"):
            self.assertIn(f"`{status}`", content)

    def test_transport_operations_exact(self) -> None:
        content = self.read_reference("gitlab-transport.md")
        operations = [
            "read-metadata", "read-diff", "read-file", "read-discussions", "top-level-note",
            "reply", "inline-discussion", "resolve", "reopen", "approve",
        ]
        for operation in operations:
            self.assertIn(f"`{operation}`", content)
        self.assertEqual(content.count("`"), len(operations) * 2)
        self.assertIn("| Operation | MCP | API | browser |", content)

    def test_risk_domains_exact(self) -> None:
        content = self.read_reference("risk-overlays.md")
        domains = [
            "auth/authorization", "tenancy", "privacy/secrets", "concurrency/transactions",
            "migrations/dependencies", "shared APIs", "performance", "accessibility/UI", "deployment",
        ]
        rows = [line for line in content.splitlines() if line.startswith("|") and "---" not in line]
        self.assertEqual(len(rows), 10)
        for domain in domains:
            self.assertEqual(sum(f"| {domain} |" in line for line in rows), 1)

    def test_tenant_escape_is_blocker_unless_local_policy_overrides(self) -> None:
        content = self.read_reference("risk-overlays.md")
        self.assertIn("tenant-escape invariant", content)
        self.assertIn("`blocker`", content)

    def test_finding_enums_exact(self) -> None:
        content = self.read_reference("finding-contract.md")
        self.assertIn("[Severity] Short imperative title", content)
        for severity in ("blocker", "critical", "high", "medium", "low"):
            self.assertIn(f"`{severity}`", content)
        for confidence in ("proven", "strong", "plausible"):
            self.assertIn(f"`{confidence}`", content)

    def test_review_patterns_require_actionable_fix_comments(self) -> None:
        content = self.read_reference("review-patterns.md")
        for phrase in (
            "changed lines",
            "caller and callee contracts",
            "tenant or authorization boundary",
            "Do NOT Flag",
            "**Severity:**",
            "**Issue:**",
            "**Why it matters:**",
            "**Fix:**",
            "small, directly relevant replacement",
            "targeted verification",
            "local pattern",
            "safe replacement",
        ):
            self.assertIn(phrase, content)

    def test_skill_loads_review_patterns_for_every_review(self) -> None:
        content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`references/review-patterns.md`", content)
        self.assertIn("Always; use a supplied or discovered local review policy", content)

    def test_every_review_is_adversarial_by_default(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Every review is adversarial by default", skill)
        self.assertNotIn("adversarial mode", skill.lower())
        self.assertIn("try to falsify", skill)
        self.assertIn("Do not invent findings", skill)

    def test_every_changed_file_requires_a_terminal_coverage_state(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ("Every changed file", "reviewed", "excluded-with-reason", "blocked"):
            self.assertIn(phrase, skill)
        self.assertIn("prohibit a clean verdict", skill)

    def test_review_patterns_define_falsification_and_size_aware_delegation(self) -> None:
        content = self.read_reference("review-patterns.md")
        for phrase in (
            "Adversarial posture",
            "Competing hypothesis",
            "Small review",
            "Medium review",
            "Large or huge review",
            "The main reviewer owns cross-file reasoning",
            "return findings and evidence, not raw code",
        ):
            self.assertIn(phrase, content)

    def test_rereview_skip_requires_unchanged_head_and_discussions(self) -> None:
        content = self.read_reference("rereview.md")
        for phrase in (
            "latest reviewed head",
            "current head",
            "current discussions",
            "Skip code re-review only when",
            "discussion changed",
        ):
            self.assertIn(phrase, content)

    def test_summary_collects_one_round_and_refreshes_discussions(self) -> None:
        content = self.read_reference("summary-agent.md")
        self.assertIn("collect all independent findings before publication", content)
        self.assertIn("re-fetch all discussions", content)
        self.assertIn("one review round", content)

    def test_summary_agent_requires_decision_and_traceable_signature(self) -> None:
        content = self.read_reference("summary-agent.md")
        for phrase in ("coverage", "blocked", "evidence gaps", "reviewed head", "Merge Sentinel", "do not approve"):
            self.assertIn(phrase, content)

    def test_rereview_groups_exact(self) -> None:
        content = self.read_reference("rereview.md")
        groups = ("fixed", "persistent", "reopened", "obsolete", "new")
        for group in groups:
            self.assertIn(f"`{group}`", content)
        self.assertIn("`ambiguous`", content)
        self.assertIn("`missing`", content)


if __name__ == "__main__":
    unittest.main()
