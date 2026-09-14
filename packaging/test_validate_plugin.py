#!/usr/bin/env python3
"""Regression tests for the repository's canonical plugin payload."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import List, Optional
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from plugin.shared.forge.evals import run_static_evals


REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_SKILLS = REPO_ROOT / "plugin" / "skills"
PERSONAL_PATH_RE = re.compile(
    r"(?i)(?:[a-z]:[\\/]+users[\\/]+[^\\/]+|/(?:home|users)/[^/]+)"
)

VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "validate_plugin", REPO_ROOT / "packaging" / "validate_plugin.py"
)
assert VALIDATOR_SPEC is not None and VALIDATOR_SPEC.loader is not None
validator = importlib.util.module_from_spec(VALIDATOR_SPEC)
VALIDATOR_SPEC.loader.exec_module(validator)
EXPECTED_SKILL_IDS = validator.EXPECTED_SKILL_IDS
FORGE_SKILL_IDS = {
    "forge-clarify",
    "forge-discover",
    "forge-spec",
    "forge-plan",
    "forge-implement",
}
FORGE_EVAL_VALIDATOR = PLUGIN_SKILLS / "skill-engineer" / "scripts" / "validate_evals.py"
CANONICAL_EVAL_VALIDATORS = {
    skill_id: REPO_ROOT / relative_path
    for skill_id, relative_path in validator.CANONICAL_EVAL_VALIDATORS.items()
}

BEHAVIORAL_SPEC = importlib.util.spec_from_file_location(
    "forge_plan_behavioral_evals", PLUGIN_SKILLS / "forge-plan" / "evals" / "run_behavioral_evals.py"
)
assert BEHAVIORAL_SPEC is not None and BEHAVIORAL_SPEC.loader is not None
behavioral_evals = importlib.util.module_from_spec(BEHAVIORAL_SPEC)
BEHAVIORAL_SPEC.loader.exec_module(behavioral_evals)

STATIC_EVAL_SPEC = importlib.util.spec_from_file_location(
    "forge_plan_static_evals", PLUGIN_SKILLS / "forge-plan" / "evals" / "run_static_evals.py"
)
assert STATIC_EVAL_SPEC is not None and STATIC_EVAL_SPEC.loader is not None
forge_plan_static_evals = importlib.util.module_from_spec(STATIC_EVAL_SPEC)
STATIC_EVAL_SPEC.loader.exec_module(forge_plan_static_evals)


def frontmatter_name(skill_md: Path) -> Optional[str]:
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("name:"):
            return line[len("name:"):].strip().strip("'\"")
    return None


class CanonicalPluginLayoutTests(unittest.TestCase):
    def test_marketplace_versions_match_plugin_manifests(self) -> None:
        """Keeps Claude marketplace refreshes tied to the released plugin version."""
        agent = json.loads((REPO_ROOT / "plugin" / "plugin.json").read_text(encoding="utf-8"))
        claude = json.loads(
            (REPO_ROOT / "plugin" / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        marketplace = json.loads(
            (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        entries = [
            entry for entry in marketplace["plugins"]
            if entry.get("name") == agent["name"]
        ]

        self.assertEqual(agent["version"], claude["version"])
        self.assertEqual(agent["version"], marketplace["version"])
        self.assertEqual(1, len(entries))
        self.assertEqual(agent["version"], entries[0]["version"])

    def test_packaging_policy_is_the_single_skill_roster_source(self) -> None:
        """Keeps validator and tests on one canonical roster/eval map."""
        policy_spec = importlib.util.spec_from_file_location(
            "plugin_policy", REPO_ROOT / "packaging" / "plugin_policy.py"
        )
        assert policy_spec is not None and policy_spec.loader is not None
        policy = importlib.util.module_from_spec(policy_spec)
        policy_spec.loader.exec_module(policy)

        self.assertEqual(policy.EXPECTED_SKILL_IDS, validator.EXPECTED_SKILL_IDS)
        self.assertEqual(
            policy.CANONICAL_EVAL_VALIDATORS,
            validator.CANONICAL_EVAL_VALIDATORS,
        )

    def test_forge_plan_uses_its_target_specific_static_gate(self) -> None:
        """Runs forge-plan contract checks instead of schema validation only."""
        runner = CANONICAL_EVAL_VALIDATORS["forge-plan"]
        proc = subprocess.run(
            [sys.executable, str(runner), "--json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertGreater(report["summary"]["runnable"], 0)
        self.assertEqual(0, report["summary"]["failed"])

    def test_forge_plan_behavioral_harness_discloses_missing_live_runners(self) -> None:
        """Never turns absent candidate/baseline/no-Skill execution into a pass."""
        harness = PLUGIN_SKILLS / "forge-plan" / "evals" / "run_behavioral_evals.py"
        proc = subprocess.run(
            [sys.executable, str(harness), "--json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertEqual("UNMEASURED", report["status"])
        self.assertNotEqual("passed", report["status"].lower())

    def test_forge_plan_delegates_workflow_and_source_semantics_to_shared_contracts(self) -> None:
        skill = (PLUGIN_SKILLS / "forge-plan" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("../../shared/forge/references/workflow-contract.md", skill)
        self.assertIn("review or go", skill)
        self.assertNotIn("can_enter_stage", skill)
        self.assertNotIn("awaiting-approval", skill)
        self.assertNotIn("content hash", skill)
        self.assertNotIn("Present the artifact paths and approval hash", skill)
        self.assertNotIn("to-tickets", skill.lower())

    def test_forge_plan_evidence_records_real_approval_provenance(self) -> None:
        evidence = (REPO_ROOT / "docs" / "superpowers" / "plans" / "2026-09-12-forge-plan-pr-2-review-fixes-evidence.md").read_text(encoding="utf-8")
        approval = json.loads((REPO_ROOT / "docs" / "superpowers" / "plans" / "2026-09-13-forge-plan-approval-record.json").read_text(encoding="utf-8"))
        self.assertNotIn("approved these exact authority bytes with", evidence)
        self.assertIn("was continuation and\n  delivery intent, not artifact approval", evidence)
        self.assertIn("docs/superpowers/plans/2026-09-13-forge-plan-approval-record.json", evidence)
        self.assertIn("Earlier implementation preceded valid artifact approval", evidence)
        self.assertEqual("GATE_VIOLATION", approval["prior_gate_violation"]["status"])
        self.assertEqual("artifact", approval["state"]["artifacts"]["specification"]["approval"]["intent"])
        self.assertEqual("Commit and push and continue", approval["negative_proof"]["continuation_intent"])
        self.assertIn("not an artifact approval", approval["negative_proof"]["result"])

    def test_repository_gate_requires_tracked_resolved_specification_authority(self) -> None:
        self.assertEqual([], validator.validate_implementation_plan_specs())
        with tempfile.TemporaryDirectory(prefix="spec-authority-") as directory:
            root = Path(directory)
            plan = root / "docs" / "superpowers" / "plans" / "current.md"
            plan.parent.mkdir(parents=True)
            plan.write_text("**Spec:** `docs/specs/current.md`\n", encoding="utf-8")
            spec = root / "docs" / "specs" / "current.md"
            spec.parent.mkdir(parents=True)
            spec.write_text("Revision: 1\n## Resolved decisions\n- fixed\n", encoding="utf-8")
            tracked = {
                "docs/superpowers/plans/current.md",
                "docs/specs/current.md",
            }
            self.assertEqual(
                [],
                validator.validate_implementation_plan_specs(
                    [plan], tracked_paths=tracked, repo_root=root
                ),
            )

            for name, content, tracked_paths in (
                (
                    "missing",
                    "**Spec:** `docs/specs/missing.md`\n",
                    {"docs/superpowers/plans/current.md"},
                ),
                (
                    "untracked",
                    "**Spec:** `docs/specs/current.md`\n",
                    {"docs/superpowers/plans/current.md"},
                ),
                (
                    "draft",
                    "**Spec:** `docs/specs/current.md`\n",
                    {"docs/superpowers/plans/current.md", "docs/specs/current.md"},
                ),
                (
                    "unresolved",
                    "**Spec:** `docs/specs/current.md`\n",
                    {"docs/superpowers/plans/current.md", "docs/specs/current.md"},
                ),
            ):
                with self.subTest(name=name):
                    plan.write_text(content, encoding="utf-8")
                    if name == "draft":
                        spec.write_text("Revision: 1\nDraft for grilling\n", encoding="utf-8")
                    elif name == "unresolved":
                        spec.write_text("Revision: 1\n## Open questions\n- decide\n", encoding="utf-8")
                    else:
                        spec.write_text("Revision: 1\n## Resolved decisions\n- fixed\n", encoding="utf-8")
                    errors = validator.validate_implementation_plan_specs(
                        [plan], tracked_paths=tracked_paths, repo_root=root
                    )
                    self.assertTrue(errors)

    def test_current_compact_and_detailed_shape_mappings_are_deterministic(self) -> None:
        manifest = PLUGIN_SKILLS / "forge-plan" / "references" / "expected-shape-mappings.json"
        self.assertTrue(manifest.is_file(), "shape mappings require one canonical manifest")
        ok, errors = forge_plan_static_evals.validate_artifact_shape_mappings()
        self.assertTrue(ok, errors)
        self.assertEqual([], errors)
        with tempfile.TemporaryDirectory(prefix="shape-mapping-") as directory:
            execution = Path(directory) / "execution.json"
            data = json.loads(
                (PLUGIN_SKILLS / "forge-plan" / "evals" / "execution.json").read_text(
                    encoding="utf-8"
                )
            )
            case = next(item for item in data if item.get("id") == "FP-E-001")
            assertion = case["expected"]["outcome"]["assertions"][0]
            case["artifact_shape_mapping"]["assertions"][assertion] = {
                "authority": "REQ-004",
                "clause": "plugin/skills/forge-plan/references/detailed-mode.md#detailed-artifact-tree",
            }
            rubric = case["graders"][0]["rubric"]
            case["artifact_shape_mapping"]["rubrics"][rubric] = {
                "authority": "REQ-005",
                "clause": "plugin/skills/forge-plan/references/execution-packet.md#packet-fields",
            }
            execution.write_text(json.dumps(data), encoding="utf-8")
            ok, errors = forge_plan_static_evals.validate_artifact_shape_mappings(execution)
        self.assertFalse(ok)
        self.assertTrue(any("canonical mapping" in error for error in errors))

    def test_behavioral_structural_mutations_fail_even_when_names_and_options_remain(self) -> None:
        harness = PLUGIN_SKILLS / "forge-plan" / "evals" / "run_behavioral_evals.py"
        fixture = PLUGIN_SKILLS / "forge-plan" / "evals" / "fixtures" / "approved-planning-context.json"
        baseline = PLUGIN_SKILLS / "forge-plan" / "evals" / "fixtures" / "brain-plan-scenarios.json"
        with tempfile.TemporaryDirectory(prefix="behavioral-structure-") as directory:
            root = Path(directory)
            mutated_harness = root / "run_behavioral_evals.py"
            mutated_harness.write_text(
                harness.read_text(encoding="utf-8").replace("shell=False", "shell=True", 1),
                encoding="utf-8",
            )
            mutated_loader = root / "run_behavioral_loader_mutation.py"
            mutated_loader.write_text(
                harness.read_text(encoding="utf-8").replace(
                    "public = load_public_fixture(path)", "public = _load_json(path)"
                ),
                encoding="utf-8",
            )
            mutated_fixture = root / "fixture.json"
            fixture_data = json.loads(fixture.read_text(encoding="utf-8"))
            fixture_data["schema_version"] = 99
            mutated_fixture.write_text(json.dumps(fixture_data), encoding="utf-8")
            copied_baseline = root / "baseline.json"
            shutil.copy2(baseline, copied_baseline)

            shell_ok, shell_errors = forge_plan_static_evals.inspect_behavioral_harness(
                mutated_harness, fixture, baseline
            )
            loader_ok, loader_errors = forge_plan_static_evals.inspect_behavioral_harness(
                mutated_loader, fixture, baseline
            )
            fixture_ok, fixture_errors = forge_plan_static_evals.inspect_behavioral_harness(
                harness, mutated_fixture, copied_baseline
            )

        self.assertFalse(shell_ok, shell_errors)
        self.assertFalse(loader_ok, loader_errors)
        self.assertFalse(fixture_ok, fixture_errors)

    def test_forge_plan_has_no_downstream_conversion_provenance(self) -> None:
        scoped = (
            Path("intent.md"),
            Path("docs/research/2026-09-12-forge-plan-modes-research.md"),
            Path("docs/superpowers/plans/2026-09-12-forge-plan-pr-2-review-fixes.md"),
            Path("plugin/skills/forge-plan/SKILL.md"),
            Path("plugin/skills/forge-plan/evals/execution.json"),
        )
        text = "\n".join((REPO_ROOT / path).read_text(encoding="utf-8") for path in scoped).lower()
        self.assertNotIn("to-tickets", text)
        self.assertNotIn("ticket handoff", text)
        self.assertIn("tracker publication", text)

    def run_behavioral_harness(self, temporary: Path, mode: str, *, strict: bool = False, with_judge: bool = True, case_id: str = "FP-EX-001"):
        """Run one real harness case against temporary runner and judge argv files."""
        runner = temporary / "runner.py"
        judge = temporary / "judge.py"
        runner_argv = temporary / "runner-argv.json"
        judge_argv = temporary / "judge-argv.json"
        mode_literal = repr(mode)
        runner.write_text(
            "import json, sys\n"
            f"mode = {mode_literal}\n"
            "request = json.load(sys.stdin)\n"
            "if mode == 'capture':\n"
            "    open(sys.argv[1], 'w', encoding='utf-8').write(json.dumps(request))\n"
            "if mode == 'empty':\n"
            "    print('{}')\n"
            "elif mode == 'malformed':\n"
            "    print('not json')\n"
            "elif mode == 'nonzero':\n"
            "    print(json.dumps({}))\n"
            "    sys.exit(7)\n"
            "elif mode == 'parrot':\n"
            "    print(json.dumps({'assertions': [{'text': 'copied', 'passed': True, 'evidence': 'self-attested'}]}))\n"
            "else:\n"
            "    print(json.dumps({'response': 'observed execution', 'trace': [{'event': 'response'}], 'metrics': {'version': 1, 'input_tokens': 10, 'output_tokens': 20}}))\n",
            encoding="utf-8",
        )
        judge.write_text(
            "import json, sys\n"
            f"mode = {mode_literal}\n"
            "request = json.load(sys.stdin)\n"
            "if mode == 'judge-malformed':\n"
            "    print('not json')\n"
            "    raise SystemExit\n"
            "assertions = request['expected']['outcome']['assertions']\n"
            "if mode == 'partial':\n"
            "    assertions = assertions[:1]\n"
            "role = request['role']\n"
            "def passed(index):\n"
            "    if mode == 'candidate-regression': return role != 'candidate'\n"
            "    if mode == 'candidate-improves': return role == 'candidate'\n"
            "    if mode == 'candidate-no-skill-regression': return role == 'no-skill'\n"
            "    if mode == 'mixed': return not ((role == 'candidate' and index == 0) or (role == 'baseline' and index == 1))\n"
            "    if mode == 'single-fail': return not (role == 'candidate' and index == 0)\n"
            "    return True\n"
            "print(json.dumps({'assertions': [{'text': text, 'passed': passed(index), 'evidence': 'trusted judge'} for index, text in enumerate(assertions)]}))\n",
            encoding="utf-8",
        )
        capture = temporary / "runner-input.json"
        runner_args = [sys.executable, str(runner)]
        if mode == "capture":
            runner_args.append(str(capture))
        runner_argv.write_text(json.dumps(runner_args), encoding="utf-8")
        judge_argv.write_text(json.dumps([sys.executable, str(judge)]), encoding="utf-8")
        harness = PLUGIN_SKILLS / "forge-plan" / "evals" / "run_behavioral_evals.py"
        args = [
            sys.executable,
            str(harness),
            "--case-id",
            case_id,
            "--candidate-argv-file",
            str(runner_argv),
            "--baseline-argv-file",
            str(runner_argv),
            "--no-skill-argv-file",
            str(runner_argv),
            "--json",
        ]
        if with_judge:
            args.extend(["--judge-argv-file", str(judge_argv)])
        if strict:
            args.append("--strict")
        return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True)

    def test_behavioral_harness_rejects_empty_runner_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc = self.run_behavioral_harness(Path(directory), "empty")
        self.assertNotEqual(0, proc.returncode)
        report = json.loads(proc.stdout)
        self.assertEqual("FAILED", report["status"])
        self.assertTrue(any(result["status"] == "INCOMPLETE" for result in report["results"]))

    def test_behavioral_harness_rejects_malformed_and_nonzero_runner_output(self) -> None:
        for mode in ("malformed", "nonzero"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                proc = self.run_behavioral_harness(Path(directory), mode)
            self.assertNotEqual(0, proc.returncode)
            report = json.loads(proc.stdout)
            self.assertEqual("FAILED", report["status"])

    def test_behavioral_harness_rejects_missing_assertion_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc = self.run_behavioral_harness(Path(directory), "partial")
        self.assertNotEqual(0, proc.returncode)
        report = json.loads(proc.stdout)
        self.assertTrue(any(result["missing_grader_assertions"] for result in report["results"]))

    def test_behavioral_harness_compares_complete_role_results(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc = self.run_behavioral_harness(Path(directory), "complete")
        self.assertEqual(0, proc.returncode, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertEqual("EXECUTED", report["status"])
        self.assertEqual(1, len(report["comparisons"]))
        self.assertEqual(
            {"candidate": True, "baseline": True, "no-skill": True},
            report["comparisons"][0]["correctness"],
        )
        candidate = next(result for result in report["results"] if result["role"] == "candidate")
        self.assertEqual("UNMEASURED", candidate["metrics"]["duration_ms"])

    def test_behavioral_harness_surfaces_candidate_regression(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc = self.run_behavioral_harness(Path(directory), "candidate-regression", case_id="FP-E-001")
        self.assertNotEqual(0, proc.returncode)
        report = json.loads(proc.stdout)
        comparison = report["comparisons"][0]
        self.assertTrue(comparison["candidate_vs_baseline"]["regression"])
        self.assertTrue(comparison["candidate_vs_no_skill"]["regression"])
        self.assertEqual(3, comparison["trial_count"])
        self.assertEqual(3, len(comparison["candidate_vs_baseline"]["trial_deltas"]))
        self.assertTrue(
            all(delta["regression"] for delta in comparison["candidate_vs_baseline"]["trial_deltas"])
        )

    def test_behavioral_harness_reports_candidate_improvement_over_bad_comparators(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc = self.run_behavioral_harness(Path(directory), "candidate-improves")
        self.assertEqual(0, proc.returncode, proc.stderr)
        report = json.loads(proc.stdout)
        comparison = report["comparisons"][0]
        self.assertEqual("EXECUTED", report["status"])
        self.assertTrue(comparison["candidate_vs_baseline"]["improvement"])
        self.assertTrue(comparison["candidate_vs_no_skill"]["improvement"])

    def test_behavioral_harness_fails_candidate_regression_against_no_skill(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc = self.run_behavioral_harness(Path(directory), "candidate-no-skill-regression")
        self.assertNotEqual(0, proc.returncode)
        report = json.loads(proc.stdout)
        comparison = report["comparisons"][0]
        self.assertTrue(comparison["candidate_vs_no_skill"]["regression"])

    def test_behavioral_harness_rejects_self_attesting_runner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc = self.run_behavioral_harness(Path(directory), "parrot")
        self.assertNotEqual(0, proc.returncode)
        report = json.loads(proc.stdout)
        self.assertTrue(any("unknown runner output fields" in error for result in report["results"] for error in result.get("errors", [])))

    def test_behavioral_harness_requires_a_trusted_judge(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc = self.run_behavioral_harness(Path(directory), "complete", with_judge=False)
        self.assertEqual(0, proc.returncode)
        report = json.loads(proc.stdout)
        self.assertEqual("UNMEASURED", report["status"])
        self.assertTrue(all(result["status"] == "UNMEASURED" for result in report["results"]))

    def test_behavioral_harness_excludes_repository_static_cases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc = self.run_behavioral_harness(Path(directory), "complete", with_judge=False, case_id="FP-EX-019")
        self.assertEqual(0, proc.returncode, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertEqual("UNMEASURED", report["status"])
        self.assertEqual(["FP-EX-019"], report["static_only_cases"])
        self.assertEqual([], report["results"])

    def test_behavioral_harness_does_not_expose_answer_key_to_runner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc = self.run_behavioral_harness(Path(directory), "capture")
            captured = json.loads((Path(directory) / "runner-input.json").read_text(encoding="utf-8"))
        self.assertEqual(0, proc.returncode, proc.stderr)
        forbidden_keys = {
            "accepted_baseline", "accepted_baseline_fixture", "expected", "grader",
            "graders", "rubric", "known_answer", "known_answer_material", "oracle",
        }

        def contains_forbidden(value):
            if isinstance(value, dict):
                return any(key in forbidden_keys or contains_forbidden(item) for key, item in value.items())
            if isinstance(value, list):
                return any(contains_forbidden(item) for item in value)
            return False

        self.assertFalse(contains_forbidden(captured))
        self.assertEqual({"case_id", "trial_index", "prompt", "tags", "role", "fixture"}, set(captured))
        self.assertEqual(1, captured["trial_index"])

    def test_behavioral_harness_rejects_nested_public_oracles_before_spawning(self) -> None:
        harness = PLUGIN_SKILLS / "forge-plan" / "evals" / "run_behavioral_evals.py"
        source_fixture = PLUGIN_SKILLS / "forge-plan" / "evals" / "fixtures" / "approved-planning-context.json"
        with tempfile.TemporaryDirectory(prefix="nested-fixture-") as directory:
            temporary = Path(directory)
            fixture = json.loads(source_fixture.read_text(encoding="utf-8"))
            fixture["authority"][0]["accepted_baseline"] = "oracle"
            fixture["authority"][0]["expected"] = "oracle"
            fixture["repository"]["grader"] = "oracle"
            fixture["repository"]["rubric"] = "oracle"
            fixture["plan"]["known_answer_material"] = "oracle"
            fixture_path = temporary / "fixture.json"
            fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
            counter = temporary / "runner-called.txt"
            runner = temporary / "runner.py"
            runner.write_text(
                "from pathlib import Path\n"
                "import sys\n"
                "Path(sys.argv[1]).write_text('called', encoding='utf-8')\n"
                "print('{}')\n",
                encoding="utf-8",
            )
            argv_file = temporary / "runner-argv.json"
            argv_file.write_text(json.dumps([sys.executable, str(runner), str(counter)]), encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable, str(harness), "--fixture", str(fixture_path),
                    "--case-id", "FP-E-001", "--candidate-argv-file", str(argv_file),
                    "--baseline-argv-file", str(argv_file), "--no-skill-argv-file", str(argv_file),
                    "--json",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
        self.assertEqual(2, proc.returncode, proc.stderr)
        self.assertIn("forbidden oracle key", proc.stderr)
        self.assertFalse(counter.exists())

    def test_behavioral_harness_executes_every_declared_trial(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            runner = temporary / "trial-runner.py"
            judge = temporary / "trial-judge.py"
            runner_count = temporary / "runner-count.txt"
            judge_count = temporary / "judge-count.txt"
            runner_count.write_text("0", encoding="utf-8")
            judge_count.write_text("0", encoding="utf-8")
            runner.write_text(
                "import json, pathlib, sys\n"
                "request = json.load(sys.stdin)\n"
                "path = pathlib.Path(sys.argv[1])\n"
                "path.write_text(str(int(path.read_text() or '0') + 1), encoding='utf-8')\n"
                "print(json.dumps({'response': request['trial_index'], 'metrics': {'version': 1}}))\n",
                encoding="utf-8",
            )
            judge.write_text(
                "import json, pathlib, sys\n"
                "request = json.load(sys.stdin)\n"
                "path = pathlib.Path(sys.argv[1])\n"
                "path.write_text(str(int(path.read_text() or '0') + 1), encoding='utf-8')\n"
                "assertions = request['expected']['outcome']['assertions']\n"
                "print(json.dumps({'assertions': [{'text': text, 'passed': True, 'evidence': str(request['trial_index'])} for text in assertions]}))\n",
                encoding="utf-8",
            )
            runner_argv = temporary / "runner-argv.json"
            judge_argv = temporary / "judge-argv.json"
            runner_argv.write_text(json.dumps([sys.executable, str(runner), str(runner_count)]), encoding="utf-8")
            judge_argv.write_text(json.dumps([sys.executable, str(judge), str(judge_count)]), encoding="utf-8")
            harness = PLUGIN_SKILLS / "forge-plan" / "evals" / "run_behavioral_evals.py"
            args = [
                sys.executable, str(harness), "--case-id", "FP-E-001",
                "--candidate-argv-file", str(runner_argv),
                "--baseline-argv-file", str(runner_argv),
                "--no-skill-argv-file", str(runner_argv),
                "--judge-argv-file", str(judge_argv), "--json",
            ]
            proc = subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True)
            report = json.loads(proc.stdout)
            runner_invocations = int(runner_count.read_text(encoding="utf-8"))
            judge_invocations = int(judge_count.read_text(encoding="utf-8"))
        self.assertEqual(0, proc.returncode, proc.stderr + proc.stdout)
        self.assertEqual("EXECUTED", report["status"])
        self.assertEqual(9, runner_invocations)
        self.assertEqual(9, judge_invocations)
        self.assertEqual(3, report["comparisons"][0]["trial_count"])
        self.assertEqual([1, 2, 3], [item["trial_index"] for item in report["results"] if item["role"] == "candidate"])

    def test_behavioral_harness_rejects_a_missing_declared_trial(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            runner = temporary / "missing-trial-runner.py"
            argv_file = temporary / "runner-argv.json"
            runner.write_text(
                "import json, sys\n"
                "request = json.load(sys.stdin)\n"
                "if request['trial_index'] == 2: sys.exit(9)\n"
                "print(json.dumps({'response': 'observed', 'metrics': {'version': 1}}))\n",
                encoding="utf-8",
            )
            argv_file.write_text(json.dumps([sys.executable, str(runner)]), encoding="utf-8")
            harness = PLUGIN_SKILLS / "forge-plan" / "evals" / "run_behavioral_evals.py"
            args = [
                sys.executable, str(harness), "--case-id", "FP-E-001",
                "--candidate-argv-file", str(argv_file), "--baseline-argv-file", str(argv_file),
                "--no-skill-argv-file", str(argv_file), "--json",
            ]
            proc = subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True)
            report = json.loads(proc.stdout)
        self.assertNotEqual(0, proc.returncode)
        self.assertEqual("FAILED", report["status"])
        self.assertTrue(report["comparisons"][0]["incomplete_roles"])

    def test_behavioral_metrics_validate_types_ranges_and_partial_values(self) -> None:
        schema = behavioral_evals.METRIC_SCHEMA
        self.assertEqual(1, schema["version"])
        self.assertEqual("UNMEASURED", schema["unmeasured"])
        count_fields = {
            "material_omissions", "blocking_questions", "rediscovery", "dependency_errors",
            "scope_errors", "input_tokens", "context_tokens", "output_tokens", "references",
            "tool_calls", "duration_ms", "retries",
        }
        self.assertEqual(
            {
                "mode", "correctness", *count_fields, "traceability_coverage",
                "acceptance_coverage", "errors", "review_findings", "deviations",
            },
            set(schema["fields"]),
        )
        self.assertEqual({"type": "enum", "values": ["compact", "detailed"]}, schema["fields"]["mode"])
        self.assertEqual({"type": "boolean"}, schema["fields"]["correctness"])
        for field in count_fields:
            self.assertEqual({"type": "integer", "minimum": 0}, schema["fields"][field])
        for field in ("traceability_coverage", "acceptance_coverage"):
            self.assertEqual({"type": "number", "minimum": 0, "maximum": 1}, schema["fields"][field])
        self.assertEqual({"type": "string", "min_length": 1}, schema["fields"]["errors"]["items"]["properties"]["message"])
        self.assertEqual({"type": "string", "min_length": 1}, schema["fields"]["review_findings"]["items"]["properties"]["severity"])
        self.assertEqual({"type": "string", "min_length": 1}, schema["fields"]["review_findings"]["items"]["properties"]["summary"])
        self.assertEqual({"type": "string", "min_length": 1}, schema["fields"]["deviations"]["items"]["properties"]["description"])
        valid, errors = behavioral_evals._normalize_metrics({"mode": "compact", "input_tokens": 0, "traceability_coverage": 1.0})
        self.assertEqual([], errors)
        self.assertEqual("UNMEASURED", valid["output_tokens"])
        for field, value in (("mode", "banana"), ("mode", []), ("input_tokens", -1), ("retries", True), ("acceptance_coverage", 1.1), ("acceptance_coverage", -0.1), ("correctness", "yes"), ("unexpected", 1)):
            normalized, errors = behavioral_evals._normalize_metrics({field: value})
            self.assertIsNone(normalized, field)
            self.assertTrue(errors, field)
        for field, value in (("errors", {"message": "wrong type"}), ("review_findings", "wrong type"), ("deviations", ["wrong item type"])):
            normalized, errors = behavioral_evals._normalize_metrics({field: value})
            self.assertIsNone(normalized, field)
            self.assertTrue(errors, field)
        valid_collections, errors = behavioral_evals._normalize_metrics({
            "errors": [{"message": "runner unavailable"}],
            "review_findings": [{"severity": "medium", "summary": "missing proof"}],
            "deviations": [{"description": "live runner unmeasured"}],
        })
        self.assertEqual([], errors)
        self.assertIsNotNone(valid_collections)
        for field, value in (("errors", [{}]), ("errors", [{"message": "ok", "extra": "no"}]), ("errors", [{"message": " "}])):
            normalized, errors = behavioral_evals._normalize_metrics({field: value})
            self.assertIsNone(normalized, field)
            self.assertTrue(errors, field)
        harness = PLUGIN_SKILLS / "forge-plan" / "evals" / "run_behavioral_evals.py"
        proc = subprocess.run([sys.executable, str(harness), "--json"], cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertEqual(schema, json.loads(proc.stdout)["metrics_schema"])

    def test_behavioral_harness_reports_mixed_assertion_regression(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc = self.run_behavioral_harness(Path(directory), "mixed")
        self.assertNotEqual(0, proc.returncode)
        report = json.loads(proc.stdout)
        comparison = report["comparisons"][0]
        self.assertTrue(comparison["candidate_vs_baseline"]["lost_assertions"])
        self.assertTrue(comparison["candidate_vs_baseline"]["gained_assertions"])
        self.assertTrue(comparison["candidate_vs_baseline"]["regression"])

    def test_behavioral_harness_counts_failed_assertions_as_material_omissions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc = self.run_behavioral_harness(Path(directory), "single-fail")
        self.assertNotEqual(0, proc.returncode)
        report = json.loads(proc.stdout)
        candidate = next(result for result in report["results"] if result["role"] == "candidate")
        self.assertEqual(1, candidate["material_omissions"])
        self.assertEqual(1, len(candidate["failed_assertions"]))

    def test_behavioral_harness_rejects_malformed_argv_file(self) -> None:
        harness = PLUGIN_SKILLS / "forge-plan" / "evals" / "run_behavioral_evals.py"
        with tempfile.TemporaryDirectory() as directory:
            argv_file = Path(directory) / "argv.json"
            for value, expected in (([sys.executable, ""], "argv file"), ([sys.executable, "\x00"], "NUL")):
                with self.subTest(value=value):
                    argv_file.write_text(json.dumps(value), encoding="utf-8")
                    proc = subprocess.run(
                        [sys.executable, str(harness), "--candidate-argv-file", str(argv_file), "--json"],
                        cwd=REPO_ROOT,
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(0, proc.returncode)
                    self.assertIn(expected, proc.stderr)

            proc = subprocess.run(
                [sys.executable, str(harness), "--candidate-argv-file", "", "--json"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
        self.assertEqual(2, proc.returncode)
        self.assertIn("argv file", proc.stderr)

    def test_behavioral_harness_preserves_windows_backslashes_and_shell_metacharacters(self) -> None:
        harness = PLUGIN_SKILLS / "forge-plan" / "evals" / "run_behavioral_evals.py"
        with tempfile.TemporaryDirectory(prefix="argv literal ") as directory:
            temporary = Path(directory)
            captured = temporary / "captured-argv.txt"
            runner = temporary / "runner.py"
            literal = r'C:\work dir\quoted "value" & ; $(literal)'
            runner.write_text(
                "import json, pathlib, sys\n"
                "json.load(sys.stdin)\n"
                "pathlib.Path(sys.argv[1]).write_text(sys.argv[2], encoding='utf-8')\n"
                "print(json.dumps({'response': 'observed'}))\n",
                encoding="utf-8",
            )
            argv_file = temporary / "runner-argv.json"
            argv_file.write_text(json.dumps([sys.executable, str(runner), str(captured), literal]), encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable, str(harness), "--case-id", "FP-EX-001",
                    "--candidate-argv-file", str(argv_file), "--baseline-argv-file", str(argv_file),
                    "--no-skill-argv-file", str(argv_file), "--json",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            observed = captured.read_text(encoding="utf-8")
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertEqual(literal, observed)

    def test_behavioral_harness_rejects_malformed_judge_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc = self.run_behavioral_harness(Path(directory), "judge-malformed")
        self.assertNotEqual(0, proc.returncode)
        report = json.loads(proc.stdout)
        self.assertEqual("FAILED", report["status"])

    def test_behavioral_harness_finalizer_accepts_identical_graders_and_rejects_conflicts(self) -> None:
        expected = ["A"]
        identical = behavioral_evals._finalize_assertions(
            expected,
            [
                {"assertions": [{"text": "A", "passed": True, "evidence": "one"}]},
                {"assertions": [{"text": "A", "passed": True, "evidence": "two"}]},
            ],
        )
        conflict = behavioral_evals._finalize_assertions(
            expected,
            [
                {"assertions": [{"text": "A", "passed": True, "evidence": "one"}]},
                {"assertions": [{"text": "A", "passed": False, "evidence": "two"}]},
            ],
        )
        self.assertEqual("GRADED", identical["status"])
        self.assertEqual("one | two", identical["assertions"][0]["evidence"])
        self.assertEqual("INCOMPLETE", conflict["status"])
        self.assertTrue(any("conflicting" in error for error in conflict["errors"]))

    def test_behavioral_harness_rejects_invalid_corpus_before_spawning(self) -> None:
        harness = PLUGIN_SKILLS / "forge-plan" / "evals" / "run_behavioral_evals.py"
        with tempfile.TemporaryDirectory() as directory:
            evals = Path(directory)
            case = {
                "version": 1,
                "id": "DUPLICATE",
                "kind": "execution",
                "category": "positive",
                "prompt": "probe",
                "expected": {"outcome": {"assertions": ["A"]}},
                "graders": [{"type": "llm-judge", "rubric": "probe"}],
            }
            (evals / "execution.json").write_text(json.dumps([case, case]), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(harness), "--evals", str(evals), "--json"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(0, proc.returncode)
        self.assertIn("duplicate case id", proc.stderr)

        with tempfile.TemporaryDirectory() as directory:
            evals = Path(directory)
            malformed = dict(case)
            malformed["id"] = []
            (evals / "execution.json").write_text(json.dumps(malformed), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(harness), "--evals", str(evals), "--json"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
        self.assertEqual(2, proc.returncode)
        self.assertIn("execution corpus", proc.stderr)

    def test_behavioral_harness_preserves_argv_paths_with_spaces(self) -> None:
        with tempfile.TemporaryDirectory(prefix="argv path ") as directory:
            proc = self.run_behavioral_harness(Path(directory), "capture")
        self.assertEqual(0, proc.returncode, proc.stderr)

    def test_behavioral_harness_strict_mode_fails_without_all_roles(self) -> None:
        harness = PLUGIN_SKILLS / "forge-plan" / "evals" / "run_behavioral_evals.py"
        proc = subprocess.run(
            [sys.executable, str(harness), "--strict", "--json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(0, proc.returncode)
        self.assertEqual("UNMEASURED", json.loads(proc.stdout)["status"])

    def test_plugin_skills_include_the_required_canonical_payload(self) -> None:
        """Catches removal of a required Skill while allowing additional Skills."""
        discovered = {
            path.name
            for path in PLUGIN_SKILLS.iterdir()
            if path.is_dir() and (path / "SKILL.md").is_file()
        }
        self.assertTrue(EXPECTED_SKILL_IDS <= discovered)

    def test_expected_skill_ids_match_the_validator_constant(self) -> None:
        """Catches the test module's copy of EXPECTED_SKILL_IDS drifting from validate_plugin.py."""
        self.assertEqual(validator.EXPECTED_SKILL_IDS, EXPECTED_SKILL_IDS)

    def test_discovery_rejects_missing_required_baseline_skill(self) -> None:
        """Required baseline Skills remain mandatory in an isolated discovery root."""
        with tempfile.TemporaryDirectory(prefix="missing-baseline-") as directory:
            skills_dir = Path(directory)
            for skill_id in sorted(EXPECTED_SKILL_IDS - {"merge-sentinel"}):
                skill_dir = skills_dir / skill_id
                skill_dir.mkdir()
                (skill_dir / "SKILL.md").write_text(
                    f"---\nname: {skill_id}\n---\n", encoding="utf-8"
                )

            validator._ok = True
            with contextlib.redirect_stdout(io.StringIO()):
                discovered = validator.discover_skills(skills_dir)
            self.addCleanup(setattr, validator, "_ok", True)

            self.assertEqual(EXPECTED_SKILL_IDS - {"merge-sentinel"},
                             {path.name for path in discovered})
            self.assertFalse(validator._ok)

    def test_discovery_finds_an_additional_valid_skill_package(self) -> None:
        """Additional immediate Skill packages are discoverable beside the baseline."""
        with tempfile.TemporaryDirectory(prefix="additional-skill-") as directory:
            skills_dir = Path(directory)
            for skill_id in sorted(EXPECTED_SKILL_IDS | {"portable-extra"}):
                skill_dir = skills_dir / skill_id
                skill_dir.mkdir()
                (skill_dir / "SKILL.md").write_text(
                    f"---\nname: {skill_id}\n---\n", encoding="utf-8"
                )

            validator._ok = True
            with contextlib.redirect_stdout(io.StringIO()):
                discovered = validator.discover_skills(skills_dir)
            self.addCleanup(setattr, validator, "_ok", True)

            self.assertEqual(
                EXPECTED_SKILL_IDS | {"portable-extra"},
                {path.name for path in discovered},
            )
            self.assertTrue(validator._ok)

    def test_discovery_does_not_include_shared_forge_resources(self) -> None:
        """Only immediate children under the injected Skills directory are discovered."""
        with tempfile.TemporaryDirectory(prefix="skills-boundary-") as directory:
            root = Path(directory)
            skills_dir = root / "plugin" / "skills"
            skills_dir.mkdir(parents=True)
            for skill_id in sorted(EXPECTED_SKILL_IDS):
                skill_dir = skills_dir / skill_id
                skill_dir.mkdir()
                (skill_dir / "SKILL.md").write_text(
                    f"---\nname: {skill_id}\n---\n", encoding="utf-8"
                )
            shared_skill = root / "plugin" / "shared" / "forge"
            shared_skill.mkdir(parents=True)
            (shared_skill / "SKILL.md").write_text(
                "---\nname: shared-forge\n---\n", encoding="utf-8"
            )

            validator._ok = True
            with contextlib.redirect_stdout(io.StringIO()):
                discovered = validator.discover_skills(skills_dir)
            self.addCleanup(setattr, validator, "_ok", True)

            self.assertNotIn(shared_skill, discovered)

    def test_no_repository_skill_mirror_exists(self) -> None:
        """Catches reintroduction of authored host mirrors outside plugin/skills/."""
        mirrors = [
            REPO_ROOT / "skill-engineer",
            REPO_ROOT / ".agents" / "skills" / "skill-engineer",
            REPO_ROOT / ".agents" / "skills" / "merge-sentinel",
        ]
        self.assertEqual([], [str(path.relative_to(REPO_ROOT)) for path in mirrors if path.exists()])

    def test_canonical_payload_excludes_committed_eval_results(self) -> None:
        """Catches committed eval output in an authored Skill tree."""
        proc = subprocess.run(
            ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertEqual(
            [], validator.tracked_generated_results(proc.stdout.splitlines())
        )

    def canonical_eval_command(self, skill_id: str, evals: Path):
        """Return the trusted bundled-Python validator for one Skill corpus."""
        return [
            sys.executable,
            str(CANONICAL_EVAL_VALIDATORS[skill_id]),
            str(evals),
            "--json",
        ]

    def validate_canonical_eval_corpora(self, runner=None):
        """Return per-Skill failures without short-circuiting the corpus loop."""
        runner = runner or subprocess.run
        failures = []
        for skill_id in sorted(CANONICAL_EVAL_VALIDATORS):
            evals = PLUGIN_SKILLS / skill_id / "evals"
            proc = runner(
                self.canonical_eval_command(skill_id, evals),
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                failures.append(f"{skill_id}: validator exit {proc.returncode}: {proc.stderr}")
                continue
            try:
                report = json.loads(proc.stdout)
            except json.JSONDecodeError as exc:
                failures.append(f"{skill_id}: invalid validator JSON: {exc}")
                continue
            if not isinstance(report, dict):
                failures.append(f"{skill_id}: validator output is not a JSON object")
                continue
            case_count = report.get("case_count")
            if isinstance(case_count, bool) or not isinstance(case_count, int) or case_count <= 0:
                failures.append(f"{skill_id}: canonical corpus has no cases")
            errors = report.get("errors")
            if not isinstance(errors, list) or errors:
                failures.append(f"{skill_id}: canonical corpus errors: {report.get('errors')}")
        return failures

    def test_every_packaged_skill_canonical_evals_validate_without_optional_dependencies(self) -> None:
        """Keeps every packaged canonical eval corpus readable by bundled Python."""
        self.assertEqual([], self.validate_canonical_eval_corpora())

    def test_every_forge_eval_directory_passes_the_existing_v1_validator(self) -> None:
        """Forge keeps using the existing v1 schema validator, not a replacement."""
        failures = []
        for skill_id in sorted(FORGE_SKILL_IDS):
            evals = PLUGIN_SKILLS / skill_id / "evals"
            proc = subprocess.run(
                [sys.executable, str(FORGE_EVAL_VALIDATOR), str(evals), "--json"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            if proc.returncode:
                failures.append(f"{skill_id}: {proc.stderr}")
                continue
            report = json.loads(proc.stdout)
            if report.get("errors") or report.get("case_count", 0) <= 0:
                failures.append(f"{skill_id}: {report}")
        self.assertEqual([], failures)

    def test_forge_trigger_corpora_cover_required_categories(self) -> None:
        """Every Forge stage guards positive, negative, and boundary routing."""
        required_categories = {"positive", "negative", "boundary"}
        for skill_id in sorted(FORGE_SKILL_IDS):
            trigger_path = PLUGIN_SKILLS / skill_id / "evals" / "trigger.json"
            cases = json.loads(trigger_path.read_text(encoding="utf-8"))
            categories = {case.get("category") for case in cases if isinstance(case, dict)}
            self.assertTrue(
                required_categories <= categories,
                f"{skill_id} lacks {sorted(required_categories - categories)}",
            )

    def test_shared_static_runner_classifies_current_v1_corpus_without_false_passes(self) -> None:
        """Model/host evals remain non-passing when no such capability is declared."""
        report = run_static_evals.run_eval_roots(
            [PLUGIN_SKILLS.parent / "shared" / "forge" / "evals"], capabilities=set()
        )
        self.assertGreaterEqual(report["summary"]["passed"], 1)
        self.assertEqual(0, report["summary"]["failed"])
        self.assertGreater(report["summary"]["skipped"], 0)
        self.assertEqual([], report["results"]["unmeasured"])
        skipped_ids = {result["id"] for result in report["results"]["skipped"]}
        forge_ex_ids = {"FORGE-EX-{:03d}".format(n) for n in range(1, 7)}
        self.assertTrue(forge_ex_ids <= skipped_ids)

    def test_each_canonical_corpus_failure_is_independently_gated(self) -> None:
        """Catches a package gate that stops after the first Skill or ignores empty/error reports."""
        expected_ids = sorted(CANONICAL_EVAL_VALIDATORS)
        valid_report = json.dumps({"case_count": 1, "errors": []})
        for failing_skill in expected_ids:
            for mutation in ("zero-cases", "one-error"):
                calls = []

                def fake_run(argv, **_kwargs):
                    evals_arg = next(
                        arg for arg in argv
                        if Path(arg).name == "evals"
                        and Path(arg).parent.name in CANONICAL_EVAL_VALIDATORS
                    )
                    skill_id = Path(evals_arg).parent.name
                    calls.append(skill_id)
                    if skill_id == failing_skill:
                        report = (
                            {"case_count": 0, "errors": []}
                            if mutation == "zero-cases"
                            else {"case_count": 1, "errors": [{"error": "mutated"}]}
                        )
                        return subprocess.CompletedProcess(
                            argv, 0, json.dumps(report), ""
                        )
                    return subprocess.CompletedProcess(argv, 0, valid_report, "")

                failures = self.validate_canonical_eval_corpora(fake_run)
                self.assertEqual(expected_ids, calls, mutation)
                self.assertTrue(
                    any(failing_skill in failure for failure in failures),
                    f"{failing_skill}/{mutation}: {failures}",
                )

    def test_merge_sentinel_validator_rejects_canonical_mutations(self) -> None:
        source = PLUGIN_SKILLS / "merge-sentinel" / "evals"

        def missing_record_field(root: Path) -> None:
            path = root / "cases.json"
            cases = json.loads(path.read_text(encoding="utf-8"))
            del cases[0]["split"]
            path.write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")

        def broken_fixture_reference(root: Path) -> None:
            path = root / "cases.json"
            cases = json.loads(path.read_text(encoding="utf-8"))
            cases[0]["input"] = "fixtures/clean-mr/missing.json"
            path.write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")

        def quality_contract_divergence(root: Path) -> None:
            path = root / "quality-contracts.json"
            contracts = json.loads(path.read_text(encoding="utf-8"))
            contracts["cases"][0]["expected_findings"] = ["drifted"]
            path.write_text(json.dumps(contracts, indent=2) + "\n", encoding="utf-8")

        mutations = (
            ("missing record field", missing_record_field, "cases.json[clean-mr]"),
            ("broken fixture reference", broken_fixture_reference, "cases.json[clean-mr].input"),
            ("quality contract divergence", quality_contract_divergence, "quality-cases.json[clean-preserved-contract]"),
        )
        for name, mutate, expected in mutations:
            with self.subTest(mutation=name):
                with tempfile.TemporaryDirectory(prefix="merge-sentinel-corpus-") as directory:
                    root = Path(directory) / "evals"
                    shutil.copytree(source, root)
                    mutate(root)
                    proc = subprocess.run(
                        self.canonical_eval_command("merge-sentinel", root),
                        cwd=REPO_ROOT,
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(0, proc.returncode, proc.stdout)
                    report = json.loads(proc.stdout)
                    self.assertTrue(
                        any(expected in error.get("case", "") for error in report["errors"]),
                        report["errors"],
                    )

    def test_canonical_eval_roots_are_json_and_fixture_json_is_excluded(self) -> None:
        """Canonical roots use JSON while fixture inputs remain outside validator traversal."""
        for skill_id in sorted(EXPECTED_SKILL_IDS):
            evals = PLUGIN_SKILLS / skill_id / "evals"
            root_files = [path for path in evals.iterdir() if path.is_file()]
            self.assertTrue(
                any(path.suffix.lower() == ".json" for path in root_files),
                skill_id,
            )
            self.assertEqual(
                [],
                [path.name for path in root_files if path.suffix.lower() in {".yaml", ".yml"}],
                skill_id,
            )
            fixture_files = list((evals / "fixtures").rglob("*.json"))
            if not fixture_files:
                continue
            proc = subprocess.run(
                self.canonical_eval_command(skill_id, evals),
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, proc.returncode, proc.stderr)
            report = json.loads(proc.stdout)
            reported = {Path(path).resolve() for path in report["files"]}
            self.assertTrue(
                reported.isdisjoint(path.resolve() for path in fixture_files),
                skill_id,
            )

    def test_generated_results_are_matched_only_at_the_skill_eval_root(self) -> None:
        """Catches a matcher that flags fixture payloads or ignores real result output."""
        self.assertEqual(
            ["plugin/skills/merge-sentinel/evals/results/run1/summary.json"],
            validator.tracked_generated_results(
                [
                    "plugin/skills/merge-sentinel/evals/results/run1/summary.json",
                    r"plugin\skills\skill-engineer\evals\fixtures\x\evals\results\run1\t.md",
                    "plugin/skills/skill-engineer/evals/cases.json",
                ]
            ),
        )

    def test_untracked_generated_results_do_not_fail_validation(self) -> None:
        """Task 8 reserves a local, git-ignored results run directory for final review."""
        results_dir = PLUGIN_SKILLS / "merge-sentinel" / "evals" / "results"
        with self.generated_result_fixture(results_dir):
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                exit_code = validator.main()
            self.assertEqual(0, exit_code, buffer.getvalue())

    def test_built_payload_excludes_generated_results(self) -> None:
        """Catches a distribution build that copies host-generated eval output."""
        results_dir = PLUGIN_SKILLS / "merge-sentinel" / "evals" / "results"
        with self.generated_result_fixture(results_dir):
            with self.built_payload() as payload:
                result_dirs = sorted(
                    str(path.relative_to(payload))
                    for path in payload.glob("skills/*/evals/results")
                    if path.is_dir()
                )
                self.assertEqual([], result_dirs)

    def test_built_payload_excludes_bytecode_caches(self) -> None:
        """Catches a build that ships .pyc files, which embed absolute source paths."""
        cache_dir = PLUGIN_SKILLS / "merge-sentinel" / "evals" / "__pycache__"
        created = not cache_dir.exists()
        cache_dir.mkdir(parents=True, exist_ok=True)
        probe = cache_dir / "build-probe.cpython-000.pyc"
        probe.write_bytes(b"\x00\x00\x00\x00" + str(REPO_ROOT).encode("utf-8"))
        try:
            with self.built_payload() as payload:
                leaked = sorted(
                    str(path.relative_to(payload))
                    for path in payload.rglob("*")
                    if path.name == "__pycache__" or path.suffix == ".pyc"
                )
                self.assertEqual([], leaked)
        finally:
            probe.unlink(missing_ok=True)
            if created:
                with contextlib.suppress(OSError):
                    cache_dir.rmdir()

    def test_generated_result_setup_preserves_preexisting_content(self) -> None:
        """Catches fixed-name setup that overwrites and deletes an existing result."""
        with tempfile.TemporaryDirectory(prefix="collision-safety-") as directory:
            root = Path(directory)
            skills = root / "skills"
            results_dir = skills / "merge-sentinel" / "evals" / "results"
            results_dir.mkdir(parents=True)
            preexisting = results_dir / "generated.jsonl"
            original = b'{"preserve":true}\n'
            preexisting.write_bytes(original)

            with self.generated_result_fixture(results_dir) as marker:
                self.assertNotEqual(preexisting, marker)
                self.assertTrue(marker.is_file())
                self.assertEqual(original, preexisting.read_bytes())

            self.assertTrue(preexisting.is_file())
            self.assertEqual(original, preexisting.read_bytes())
            self.assertFalse(marker.exists())

    def test_generated_results_path_is_git_ignored(self) -> None:
        """Catches generated eval results that can be accidentally committed."""
        candidate = "plugin/skills/merge-sentinel/evals/results/generated.jsonl"
        proc = subprocess.run(
            ["git", "check-ignore", candidate],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)

    def test_validator_scans_extensionless_packaged_text_for_credentials(self) -> None:
        """Catches suffix allowlists that omit readable packaged scripts or text."""
        scripts_dir = PLUGIN_SKILLS / "merge-sentinel" / "scripts"
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix="credential-probe-",
            suffix="",
            dir=scripts_dir,
            delete=False,
        ) as handle:
            handle.write("token=" + "ghp_" + "A" * 24 + "\n")
            probe = Path(handle.name)
        try:
            proc = subprocess.run(
                [sys.executable, str(REPO_ROOT / "packaging" / "validate_plugin.py")],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
        finally:
            probe.unlink(missing_ok=True)

        self.assertNotEqual(0, proc.returncode)
        self.assertIn(probe.name, proc.stdout)

    def test_built_payload_contains_no_personal_paths(self) -> None:
        """Catches personal paths in every text artifact, including JSONL transcripts."""
        with self.built_payload() as payload:
            findings: List[str] = []
            for path in payload.rglob("*"):
                if not path.is_file():
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                if PERSONAL_PATH_RE.search(text):
                    findings.append(str(path.relative_to(payload)))
            self.assertEqual([], findings)

    def test_repository_root_skill_is_an_illegal_tracked_source(self) -> None:
        """Catches a tracked root SKILL.md omitted by slash-only source discovery."""
        completed = subprocess.CompletedProcess(
            ["git", "ls-files"],
            0,
            stdout="SKILL.md\nplugin/skills/skill-engineer/SKILL.md\n",
            stderr="",
        )
        with mock.patch.object(validator.subprocess, "run", return_value=completed):
            validator._ok = True
            with contextlib.redirect_stdout(io.StringIO()):
                validator.check_no_tracked_mirrors()
        self.addCleanup(setattr, validator, "_ok", True)
        self.assertFalse(validator._ok)

    @contextlib.contextmanager
    def generated_result_fixture(self, results_dir: Path):
        """Create and remove one exclusive result marker without touching peers."""
        existed = results_dir.exists()
        results_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix="generated-result-",
            suffix=".jsonl",
            dir=results_dir,
            delete=False,
        ) as handle:
            handle.write('{"workspace":"C:/Users/local/repo"}\n')
            marker = Path(handle.name)
        try:
            yield marker
        finally:
            marker.unlink(missing_ok=True)
            if not existed:
                try:
                    results_dir.rmdir()
                except OSError:
                    pass

    @contextlib.contextmanager
    def built_payload(self):
        """Build the real plugin into an isolated ignored directory."""
        dist_dir = REPO_ROOT / "dist"
        dist_dir.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="test-plugin-", dir=dist_dir) as directory:
            payload = Path(directory) / "payload"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "packaging" / "build_plugin.py"),
                    "--out",
                    str(payload),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, proc.returncode, proc.stderr)
            yield payload

    def test_install_docs_do_not_commit_a_tracked_mirror(self) -> None:
        """Catches an install doc that instructs committing a banned Skill mirror."""
        validator._ok = True
        with contextlib.redirect_stdout(io.StringIO()):
            validator.check_install_docs_do_not_instruct_committing_mirrors()
        self.addCleanup(setattr, validator, "_ok", True)
        self.assertTrue(validator._ok)

    def test_install_docs_check_ignores_prose_mentions_of_mirror_paths(self) -> None:
        """Catches a naive banned-string scan that would flag legitimate warnings."""
        with tempfile.TemporaryDirectory() as directory:
            docs_dir = Path(directory) / "docs" / "install"
            docs_dir.mkdir(parents=True)
            (Path(directory) / "README.md").write_text(
                "Do not create `.agents/skills/merge-sentinel/` inside this repository.\n",
                encoding="utf-8",
            )
            (docs_dir / "codex.md").write_text(
                "```bash\nln -s \"$(pwd)/plugin/skills/merge-sentinel\" .agents/skills/merge-sentinel\n```\n",
                encoding="utf-8",
            )
            with mock.patch.object(validator, "REPO_ROOT", Path(directory)), mock.patch.object(
                validator, "INSTALL_DOCS_DIR", docs_dir
            ):
                validator._ok = True
                with contextlib.redirect_stdout(io.StringIO()):
                    validator.check_install_docs_do_not_instruct_committing_mirrors()
                self.addCleanup(setattr, validator, "_ok", True)
                self.assertTrue(validator._ok)

    def test_install_docs_check_catches_a_git_add_of_a_mirror_path(self) -> None:
        """Catches a real regression: a doc that tells users to commit a mirror."""
        with tempfile.TemporaryDirectory() as directory:
            docs_dir = Path(directory) / "docs" / "install"
            docs_dir.mkdir(parents=True)
            (Path(directory) / "README.md").write_text("See install docs.\n", encoding="utf-8")
            (docs_dir / "bad.md").write_text(
                "```bash\ngit add .agents/skills/merge-sentinel\ngit commit -m 'mirror'\n```\n",
                encoding="utf-8",
            )
            with mock.patch.object(validator, "REPO_ROOT", Path(directory)), mock.patch.object(
                validator, "INSTALL_DOCS_DIR", docs_dir
            ):
                validator._ok = True
                with contextlib.redirect_stdout(io.StringIO()):
                    validator.check_install_docs_do_not_instruct_committing_mirrors()
                self.addCleanup(setattr, validator, "_ok", True)
                self.assertFalse(validator._ok)

    def test_canonical_skill_names_are_unique_and_inspect_cleanly(self) -> None:
        """Catches name collisions and portable-core path/reference regressions."""
        inspector = PLUGIN_SKILLS / "skill-engineer" / "scripts" / "inspect_skill.py"
        names: List[str] = []
        for skill_id in sorted(EXPECTED_SKILL_IDS):
            skill_dir = PLUGIN_SKILLS / skill_id
            skill_md = skill_dir / "SKILL.md"
            self.assertTrue(skill_md.is_file(), f"missing {skill_md.relative_to(REPO_ROOT)}")
            names.append(frontmatter_name(skill_md) or "")
            proc = subprocess.run(
                [sys.executable, str(inspector), str(skill_dir)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, proc.returncode, proc.stderr)
            report = json.loads(proc.stdout)
            self.assertEqual([], report["broken_references"], skill_id)
            personal_paths = [
                finding
                for finding in report["hardcoded_paths"]
                if PERSONAL_PATH_RE.search(finding["match"])
            ]
            self.assertEqual([], personal_paths, skill_id)
            # disable-model-invocation is the one accepted host-only-field
            # exception (R22): user-invoked Skills pair it with an
            # agents/openai.yaml policy, checked by invocation_policy below.
            unexpected_extensions = [
                extension for extension in report["platform_extensions"]
                if extension.get("key") != "disable-model-invocation"
            ]
            self.assertEqual([], unexpected_extensions, skill_id)
            if any(extension.get("key") == "disable-model-invocation"
                   for extension in report["platform_extensions"]):
                self.assertIsNone(report["invocation_policy"]["mismatch"], skill_id)

        self.assertEqual(sorted(EXPECTED_SKILL_IDS), sorted(names))
        self.assertEqual(len(names), len(set(names)))

    def test_inspector_discloses_pyyaml_fallback(self) -> None:
        """The no-site probe must expose degraded frontmatter parsing."""
        inspector = PLUGIN_SKILLS / "skill-engineer" / "scripts" / "inspect_skill.py"
        fixture = PLUGIN_SKILLS / "skill-engineer" / "evals" / "fixtures" / "good-release-notes"
        proc = subprocess.run(
            [sys.executable, "-S", str(inspector), str(fixture)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertEqual(
            {"backend": "line-fallback", "degraded": True},
            report["metadata"]["parser"],
        )
        self.assertEqual(
            ["PyYAML unavailable: frontmatter parsed line-by-line"],
            report["metadata"]["errors"],
        )
        self.assertEqual(1, report["metrics"]["metadata_error_count"])

    def _run_inspector_on_openai_yaml(
        self, openai_yaml_content: Optional[str], block_yaml: bool = False
    ) -> dict:
        """Build a minimal disable-model-invocation Skill, run inspect_skill.py."""
        inspector = PLUGIN_SKILLS / "skill-engineer" / "scripts" / "inspect_skill.py"
        with tempfile.TemporaryDirectory() as directory:
            skill_dir = Path(directory)
            (skill_dir / "SKILL.md").write_text(
                "---\n"
                "name: fixture-skill\n"
                "description: A fixture Skill for invocation-policy tests.\n"
                "disable-model-invocation: true\n"
                "---\n\nBody.\n",
                encoding="utf-8",
            )
            if openai_yaml_content is not None:
                agents_dir = skill_dir / "agents"
                agents_dir.mkdir()
                (agents_dir / "openai.yaml").write_text(openai_yaml_content, encoding="utf-8")
            if block_yaml:
                # A `yaml` stub that raises ImportError hides any installed PyYAML.
                stub_dir = skill_dir / "_no_yaml"
                stub_dir.mkdir()
                (stub_dir / "yaml.py").write_text("raise ImportError('blocked')\n", encoding="utf-8")
                command = [sys.executable, "-c",
                           "import runpy, sys; sys.path.insert(0, sys.argv[1]); "
                           "sys.argv = sys.argv[2:]; "
                           "runpy.run_path(sys.argv[0], run_name='__main__')",
                           str(stub_dir), str(inspector), str(skill_dir)]
            else:
                command = [sys.executable, str(inspector), str(skill_dir)]
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, proc.returncode, proc.stderr)
            return json.loads(proc.stdout)

    def test_invocation_policy_check_is_structural_not_textual(self) -> None:
        """Only a real policy.allow_implicit_invocation: false counts.

        A raw substring search on openai.yaml text is fooled by a commented-out
        key or a key nested under the wrong parent; both must be treated the
        same as the key being absent, not as a match (PR #3 Codex P2 finding).
        """
        correct = self._run_inspector_on_openai_yaml(
            "policy:\n  allow_implicit_invocation: false\n"
        )
        self.assertTrue(correct["invocation_policy"]["openai_no_implicit_invocation"])
        self.assertIsNone(correct["invocation_policy"]["mismatch"])

        commented_out = self._run_inspector_on_openai_yaml(
            "# policy:\n#   allow_implicit_invocation: false\n"
        )
        self.assertFalse(commented_out["invocation_policy"]["openai_no_implicit_invocation"])
        self.assertIsNotNone(commented_out["invocation_policy"]["mismatch"])

        wrongly_nested = self._run_inspector_on_openai_yaml(
            "allow_implicit_invocation: false\n"
            "policy:\n"
            "  something_else: true\n"
        )
        self.assertFalse(wrongly_nested["invocation_policy"]["openai_no_implicit_invocation"])
        self.assertIsNotNone(wrongly_nested["invocation_policy"]["mismatch"])

    def test_invocation_policy_check_reports_malformed_yaml_as_a_finding(self) -> None:
        """Malformed openai.yaml must surface as a finding, not crash or silently pass."""
        report = self._run_inspector_on_openai_yaml(
            "policy:\n  allow_implicit_invocation: false\n bad_indent: [1, 2\n"
        )
        self.assertFalse(report["invocation_policy"]["openai_no_implicit_invocation"])
        self.assertIsNotNone(report["invocation_policy"]["openai_yaml_error"])
        self.assertIsNotNone(report["invocation_policy"]["mismatch"])

    def test_invocation_policy_check_without_pyyaml(self) -> None:
        """The no-PyYAML fallback validates the whole file and fails closed."""
        cases = {
            "policy:\n  allow_implicit_invocation: false\n": True,
            "# policy:\n#   allow_implicit_invocation: false\n": False,
            "allow_implicit_invocation: false\npolicy:\n  x: true\n": False,
            "policy:\n  allow_implicit_invocation: false\n bad_indent: [1, 2\n": False,
            "bad: [1, 2\npolicy:\n  allow_implicit_invocation: false\n": False,
            "policy:\n  allow_implicit_invocation: 'false'\n": False,
        }
        for content, expected in cases.items():
            with self.subTest(content=content):
                report = self._run_inspector_on_openai_yaml(content, block_yaml=True)
                policy = report["invocation_policy"]
                self.assertEqual(expected, policy["openai_no_implicit_invocation"])
                if not expected:
                    self.assertIsNotNone(policy["mismatch"])
        malformed = self._run_inspector_on_openai_yaml(
            "policy:\n  allow_implicit_invocation: false\n bad_indent: [1, 2\n",
            block_yaml=True,
        )
        self.assertIsNotNone(malformed["invocation_policy"]["openai_yaml_error"])

    def test_skill_count_claims_are_derived_from_discovery(self) -> None:
        """A stale whole-set count in any manifest or install doc must fail.

        ``discover_skills`` permits Skills beyond the required baseline, so a
        hardcoded count is the one claim nothing else can catch.
        """
        validator._ok = True
        self.addCleanup(setattr, validator, "_ok", True)
        with contextlib.redirect_stdout(io.StringIO()):
            validator.check_skill_count_claims(8, {"manifest": "Eight portable Agent Skills"})
        self.assertTrue(validator._ok)

        validator._ok = True
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            validator.check_skill_count_claims(9, {"manifest": "Eight portable Agent Skills"})
        self.assertFalse(validator._ok)
        self.assertIn("claims 8", stream.getvalue())

    def test_count_claim_scan_covers_the_readme_and_every_install_doc(self) -> None:
        """The README is the most likely home for a stale whole-set count."""
        scanned = {path.relative_to(REPO_ROOT).as_posix() for path in validator.count_claim_documents()}
        self.assertIn("README.md", scanned)
        expected_docs = {
            path.relative_to(REPO_ROOT).as_posix()
            for path in (REPO_ROOT / "docs" / "install").glob("*.md")
        }
        self.assertTrue(expected_docs)
        self.assertTrue(expected_docs <= scanned, sorted(expected_docs - scanned))

    def test_skill_count_check_ignores_subset_and_version_numbers(self) -> None:
        """Subset phrases and version strings are not whole-set count claims."""
        for text in (
            "The five `forge-*` Skills reference the shared core.",
            "Agent Plugins v1.0.0 plus `plugin/skills/`.",
            "Link each of the 3 forge-* Skills you need.",
        ):
            with self.subTest(text=text):
                self.assertEqual(set(), validator._claimed_counts(text))

    def test_forge_shared_references_resolve_lexically_in_a_linked_layout(self) -> None:
        """Each forge-* Skill keeps its shared-core references reachable when the
        Skill directories are installed individually beside a sibling ``shared``
        tree, as the Codex and Antigravity per-Skill routes document.

        The check is lexical (``..`` normalised without following links), which is
        the resolution mode that can break; a host resolving through the link
        target is strictly more permissive.
        """
        plugin_root = REPO_ROOT / "plugin"
        with tempfile.TemporaryDirectory(prefix="linked-layout-") as directory:
            install_root = Path(directory)
            skills_dir = install_root / "skills"
            skills_dir.mkdir()
            shutil.copytree(plugin_root / "shared", install_root / "shared")
            for skill_id in sorted(FORGE_SKILL_IDS):
                shutil.copytree(plugin_root / "skills" / skill_id, skills_dir / skill_id)

            unreachable = []
            for skill_id in sorted(FORGE_SKILL_IDS):
                skill_dir = skills_dir / skill_id
                for markdown in sorted(skill_dir.rglob("*.md")):
                    for target in re.findall(r"\]\(([^)]+)\)", markdown.read_text(encoding="utf-8")):
                        if not target.startswith("../"):
                            continue
                        resolved = Path(os.path.normpath(markdown.parent / target))
                        if not resolved.exists():
                            unreachable.append(f"{skill_id}: {markdown.name} -> {target}")
            self.assertEqual([], unreachable)


    def test_install_guides_must_name_every_discovered_skill(self) -> None:
        """A new Skill nobody documented leaves each route's Verify step blind."""
        shipped = [type("Stub", (), {"name": name})() for name in sorted(EXPECTED_SKILL_IDS)]
        validator._ok = True
        self.addCleanup(setattr, validator, "_ok", True)
        with contextlib.redirect_stdout(io.StringIO()):
            validator.check_install_docs_name_every_skill(shipped)
        self.assertTrue(validator._ok)

        undocumented = shipped + [type("Stub", (), {"name": "forge-deliver"})()]
        validator._ok = True
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            validator.check_install_docs_name_every_skill(undocumented)
        self.assertFalse(validator._ok)
        self.assertIn("forge-deliver", stream.getvalue())

    def test_competition_candidates_must_be_shipped_or_declared_host_skills(self) -> None:
        """An unshippable candidate can never compete, so the case is dead weight."""
        shipped = [type("Stub", (), {"name": name})() for name in sorted(EXPECTED_SKILL_IDS)]
        validator._ok = True
        self.addCleanup(setattr, validator, "_ok", True)
        with contextlib.redirect_stdout(io.StringIO()):
            validator.check_competition_candidates(shipped)
        self.assertTrue(validator._ok)
        self.assertIn("skill-creator", validator.EXTERNAL_COMPETITORS)

    def test_every_forge_trigger_case_id_is_unique_and_stable(self) -> None:
        """Case ids are the handle a recorded routing result is traced by."""
        for skill_id in sorted(FORGE_SKILL_IDS):
            corpus = PLUGIN_SKILLS / skill_id / "evals" / "trigger.json"
            cases = json.loads(corpus.read_text(encoding="utf-8"))
            ids = [case["id"] for case in cases]
            with self.subTest(skill=skill_id):
                self.assertEqual(len(ids), len(set(ids)))
                self.assertEqual(ids, list(dict.fromkeys(ids)), "ids must remain in stable corpus order")


    def test_catalog_overlap_report_is_well_formed_and_deterministic(self) -> None:
        """The overlap report is triage input, so it must be stable and complete."""
        spec = importlib.util.spec_from_file_location(
            "measure_catalog_overlap", REPO_ROOT / "packaging" / "measure_catalog_overlap.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        first = module.measure()
        self.assertEqual(sorted(EXPECTED_SKILL_IDS), first["skills"])
        expected_pairs = len(EXPECTED_SKILL_IDS) * (len(EXPECTED_SKILL_IDS) - 1) // 2
        self.assertEqual(expected_pairs, first["pair_count"])
        self.assertEqual(expected_pairs, len(first["pairs"]))

        scores = [pair["jaccard"] for pair in first["pairs"]]
        self.assertEqual(scores, sorted(scores, reverse=True), "pairs must rank worst-first")
        self.assertTrue(all(0.0 <= score <= 1.0 for score in scores))
        self.assertEqual(first, module.measure(), "report must be deterministic")

    def test_catalog_overlap_ignores_function_words(self) -> None:
        """Function words appear in every description and would flatten the ranking."""
        spec = importlib.util.spec_from_file_location(
            "measure_catalog_overlap", REPO_ROOT / "packaging" / "measure_catalog_overlap.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertEqual(set(), module.content_words("Use when the a to and of for it is"))
        self.assertEqual({"specification", "packets"}, module.content_words("the Specification and PACKETS"))


if __name__ == "__main__":
    unittest.main()
