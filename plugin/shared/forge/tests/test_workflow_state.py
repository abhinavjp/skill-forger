"""Behaviour tests for host-neutral deterministic Forge workflow state."""

import copy
import unittest

try:
    from plugin.shared.forge.scripts import workflow_state
except ImportError:
    workflow_state = None


class WorkflowStateTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            workflow_state, "workflow_state module must provide the workflow contract"
        )

    def valid_state(self):
        return {
            "current_actor": "forge-agent",
            "requires_spec_approval": True,
            "artifacts": {
                "specification": {
                    "hash": "spec-current",
                    "revision": "spec-r1",
                    "approval": {
                        "artifact_hash": "spec-current",
                        "revision": "spec-r1",
                        "actor": "product-owner",
                        "intent": "artifact",
                        "approved_at": 10,
                    },
                },
                "plan": {
                    "hash": "plan-current",
                    "revision": "plan-r1",
                    "approval": {
                        "artifact_hash": "plan-current",
                        "revision": "plan-r1",
                        "actor": "technical-owner",
                        "intent": "artifact",
                        "approved_at": 20,
                    },
                },
            },
        }

    def test_normalizes_non_semantic_markdown_formatting(self):
        source = "Title  \r\n\r\n\r\n  - child\t\r\nwords  within\t"

        self.assertEqual(
            workflow_state.normalize_markdown(source),
            "Title\n\n  - child\nwords  within",
        )

    def test_equivalent_markdown_has_the_same_hash(self):
        compact = "# Design\n\nBody text"
        noisy = "# Design  \r\n\r\n\r\nBody text\t"

        self.assertEqual(
            workflow_state.content_hash(compact),
            workflow_state.content_hash(noisy),
        )

    def test_meaningful_indentation_and_inline_whitespace_change_hash(self):
        self.assertNotEqual(
            workflow_state.content_hash("- parent\n  - child"),
            workflow_state.content_hash("- parent\n- child"),
        )
        self.assertNotEqual(
            workflow_state.content_hash("alpha beta"),
            workflow_state.content_hash("alpha  beta"),
        )

    def test_fenced_code_whitespace_remains_significant(self):
        original = "```python\nvalue = 1  \n\n\n```"
        changed = "```python\nvalue = 1\n\n```"

        self.assertNotEqual(
            workflow_state.content_hash(original),
            workflow_state.content_hash(changed),
        )

    def test_non_closing_fence_prefixed_code_preserves_later_whitespace(self):
        for code_line in ("```not a closing fence", "~~~not a closing fence"):
            with self.subTest(code_line=code_line):
                original = "```python\n{}\nvalue = 1  \n```".format(code_line)
                changed = "```python\n{}\nvalue = 1\n```".format(code_line)

                self.assertNotEqual(
                    workflow_state.content_hash(original),
                    workflow_state.content_hash(changed),
                )

    def test_transient_retry_is_bounded_by_failure_policy(self):
        failure = {"classification": "transient", "max_attempts": 2}

        self.assertTrue(workflow_state.can_retry(failure, 1, False))
        self.assertFalse(workflow_state.can_retry(failure, 2, True))

    def test_deterministic_retry_requires_relevant_change(self):
        failure = {"classification": "deterministic"}

        self.assertFalse(workflow_state.can_retry(failure, 0, False))
        self.assertTrue(workflow_state.can_retry(failure, 0, {"configuration": "changed"}))

    def test_blocking_includes_transitive_dependants_only(self):
        tasks = [
            {"id": "base", "depends_on": []},
            {"id": "child", "depends_on": ["base"]},
            {"id": "leaf", "depends_on": ["child"]},
            {"id": "independent", "depends_on": []},
        ]

        self.assertEqual(
            workflow_state.block_dependants(tasks, "base"),
            {"base", "child", "leaf"},
        )

    def test_resume_uses_first_incomplete_or_stale_item(self):
        state = {
            "items": [
                {"id": "specification", "completed": True, "hash": "spec-hash"},
                {"id": "plan", "completed": True, "hash": "plan-hash"},
                {"id": "implementation", "completed": False, "hash": "impl-hash"},
            ]
        }

        self.assertEqual(
            workflow_state.resume_point(state, {"specification": "spec-hash", "plan": "new"}),
            "plan",
        )

    def test_resume_returns_none_only_after_every_completed_item_is_verified(self):
        state = {
            "items": [
                {"id": "specification", "completed": True, "hash": "spec-hash"},
                {"id": "plan", "completed": True, "hash": "plan-hash"},
            ]
        }

        self.assertIsNone(
            workflow_state.resume_point(
                state, {"specification": "spec-hash", "plan": "plan-hash"}
            )
        )

    def test_recording_unmeasured_check_requires_reason_and_never_passes(self):
        updated = workflow_state.record_check(
            {"checks": {}}, "integration", "UNMEASURED", "runner unavailable"
        )

        self.assertEqual(updated["checks"]["integration"]["status"], "UNMEASURED")
        self.assertFalse(updated["checks"]["integration"]["passed"])
        with self.assertRaises(ValueError):
            workflow_state.record_check({"checks": {}}, "integration", "UNMEASURED")

    def test_record_check_accepts_only_forge_statuses(self):
        self.assertTrue(
            workflow_state.record_check({"checks": {}}, "unit", "PASS")["checks"]["unit"][
                "passed"
            ]
        )
        with self.assertRaises(ValueError):
            workflow_state.record_check({"checks": {}}, "unit", "SKIPPED")

    def test_planning_rejects_unapproved_specification(self):
        state = self.valid_state()
        state["artifacts"]["specification"].pop("approval")

        decision = workflow_state.can_enter_stage(state, "planning")

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["code"], "GATE_REQUIRED")
        self.assertTrue(decision["read_only"])

    def test_implementation_rejects_missing_or_unapproved_plan(self):
        for change in ("missing", "unapproved"):
            with self.subTest(change=change):
                state = self.valid_state()
                if change == "missing":
                    state["artifacts"].pop("plan")
                else:
                    state["artifacts"]["plan"].pop("approval")

                decision = workflow_state.can_enter_stage(state, "implementation")

                self.assertFalse(decision["allowed"])
                self.assertEqual(decision["code"], "GATE_REQUIRED")

    def test_full_workflow_intent_is_not_artifact_approval(self):
        cases = (
            ("full_workflow", False),
            ("full-workflow", False),
            ("run_workflow", False),
            ("implement_all", False),
            (123, False),
        )
        for target, artifact in (("planning", "specification"), ("implementation", "plan")):
            for intent, allowed in cases:
                with self.subTest(target=target, intent=intent):
                    state = self.valid_state()
                    state["artifacts"][artifact]["approval"]["intent"] = intent

                    decision = workflow_state.can_enter_stage(state, target)

                    self.assertEqual(decision["allowed"], allowed)
                    if not allowed:
                        self.assertEqual(decision["code"], "GATE_REQUIRED")

    def test_approval_without_intent_still_opens_gate(self):
        for target, artifact in (("planning", "specification"), ("implementation", "plan")):
            with self.subTest(target=target):
                state = self.valid_state()
                state["artifacts"][artifact]["approval"].pop("intent")

                decision = workflow_state.can_enter_stage(state, target)

                self.assertTrue(decision["allowed"])

    def test_stale_unauthorized_and_self_approvals_keep_gate_closed(self):
        cases = (
            ("stale", {"artifact_hash": "old"}, None),
            ("wrong actor", {"actor": "other"}, {"planning": ["product-owner"]}),
            ("self", {"actor": "forge-agent"}, {"planning": ["forge-agent"]}),
        )
        for name, approval_change, policy in cases:
            with self.subTest(name=name):
                state = self.valid_state()
                state["artifacts"]["specification"]["approval"].update(approval_change)

                decision = workflow_state.can_enter_stage(state, "planning", policy)

                self.assertFalse(decision["allowed"])
                self.assertEqual(decision["code"], "GATE_REQUIRED")

    def test_post_hoc_approval_does_not_authorize_prior_mutation(self):
        state = self.valid_state()
        state["mutations"] = [{"stage": "implementation", "at": 21}]
        state["artifacts"]["plan"]["approval"]["approved_at"] = 22

        decision = workflow_state.can_enter_stage(state, "implementation")

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["code"], "GATE_VIOLATION")

    def test_unlabelled_unknown_stage_or_malformed_mutations_fail_closed(self):
        cases = (
            ("unlabelled", [{"at": 21}]),
            ("unknown stage", [{"stage": "bogus", "at": 21}]),
            ("malformed mutations value", "oops"),
        )
        for name, mutations in cases:
            with self.subTest(name=name):
                state = self.valid_state()
                state["mutations"] = mutations
                state["artifacts"]["plan"]["approval"]["approved_at"] = 22

                decision = workflow_state.can_enter_stage(state, "implementation")

                self.assertFalse(decision["allowed"])
                self.assertEqual(decision["code"], "GATE_VIOLATION")
                self.assertTrue(decision["read_only"])

    def test_mutation_labelled_with_a_different_recognised_stage_does_not_block(self):
        state = self.valid_state()
        state["mutations"] = [{"stage": "specification", "at": 21}]
        state["artifacts"]["plan"]["approval"]["approved_at"] = 22

        decision = workflow_state.can_enter_stage(state, "implementation")

        self.assertTrue(decision["allowed"])

    def test_non_dict_mutation_entry_fails_closed(self):
        state = self.valid_state()
        state["mutations"] = ["oops"]
        state["artifacts"]["plan"]["approval"]["approved_at"] = 22

        decision = workflow_state.can_enter_stage(state, "implementation")

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["code"], "GATE_VIOLATION")

    def test_unproven_approval_ordering_closes_implementation_gate(self):
        cases = (
            ("equal timestamps", 20, 20),
            ("missing approval timestamp", None, 21),
            ("mixed timestamp types", "20", 21),
        )
        for name, approved_at, mutation_at in cases:
            with self.subTest(name=name):
                state = self.valid_state()
                state["mutations"] = [{"stage": "implementation", "at": mutation_at}]
                if approved_at is None:
                    state["artifacts"]["plan"]["approval"].pop("approved_at")
                else:
                    state["artifacts"]["plan"]["approval"]["approved_at"] = approved_at

                decision = workflow_state.can_enter_stage(state, "implementation")

                self.assertFalse(decision["allowed"])
                self.assertEqual(decision["code"], "GATE_VIOLATION")

    def test_optional_specification_approval_does_not_block_implementation(self):
        state = self.valid_state()
        state["requires_spec_approval"] = False
        state["mutations"] = [{"stage": "implementation", "at": 21}]
        state["artifacts"]["specification"]["approval"]["approved_at"] = 22

        decision = workflow_state.can_enter_stage(state, "implementation")

        self.assertTrue(decision["allowed"])

    def test_material_plan_change_invalidates_implementation_gate(self):
        state = self.valid_state()
        state["artifacts"]["plan"]["hash"] = "plan-changed"

        decision = workflow_state.can_enter_stage(state, "implementation")

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["code"], "GATE_REQUIRED")

    def test_stage_entry_decision_does_not_mutate_state(self):
        state = self.valid_state()
        before = copy.deepcopy(state)

        decision = workflow_state.can_enter_stage(state, "implementation")

        self.assertTrue(decision["allowed"])
        self.assertEqual(state, before)


if __name__ == "__main__":
    unittest.main()
