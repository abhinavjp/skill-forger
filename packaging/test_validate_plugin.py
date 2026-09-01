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
from unittest import mock

from plugin.shared.forge.evals import run_static_evals


REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_SKILLS = REPO_ROOT / "plugin" / "skills"
CANONICAL_EVAL_VALIDATORS = {
    "merge-sentinel": PLUGIN_SKILLS / "merge-sentinel" / "evals" / "validate_corpus.py",
    "skill-engineer": PLUGIN_SKILLS / "skill-engineer" / "scripts" / "validate_evals.py",
    "skill-prospector": PLUGIN_SKILLS / "skill-engineer" / "scripts" / "validate_evals.py",
}
FORGE_SKILL_IDS = {
    "forge-clarify",
    "forge-discover",
    "forge-spec",
    "forge-plan",
    "forge-implement",
}
EXPECTED_SKILL_IDS = {"merge-sentinel", "skill-engineer", "skill-prospector"} | FORGE_SKILL_IDS
FORGE_EVAL_VALIDATOR = PLUGIN_SKILLS / "skill-engineer" / "scripts" / "validate_evals.py"
PERSONAL_PATH_RE = re.compile(
    r"(?i)(?:[a-z]:[\\/]+users[\\/]+[^\\/]+|/(?:home|users)/[^/]+)"
)

VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "validate_plugin", REPO_ROOT / "packaging" / "validate_plugin.py"
)
assert VALIDATOR_SPEC is not None and VALIDATOR_SPEC.loader is not None
validator = importlib.util.module_from_spec(VALIDATOR_SPEC)
VALIDATOR_SPEC.loader.exec_module(validator)


def frontmatter_name(skill_md: Path) -> str | None:
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("name:"):
            return line.removeprefix("name:").strip().strip("'\"")
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
        self.assertGreaterEqual(report["summary"]["passed"], 5)
        self.assertEqual(0, report["summary"]["failed"])
        self.assertGreater(report["summary"]["skipped"], 0)
        self.assertEqual([], report["results"]["unmeasured"])
        skipped_ids = {result["id"] for result in report["results"]["skipped"]}
        forge_ex_ids = {"FORGE-EX-{:03d}".format(n) for n in range(1, 14)}
        self.assertTrue(forge_ex_ids <= skipped_ids)

    def test_cross_stage_gates_keep_implementation_read_only_until_both_approvals(self) -> None:
        """A shared static transition check proves both prospective approval gates."""
        def state(spec_approval, plan_approval):
            return {
                "artifacts": {
                    "specification": {"hash": "spec", "revision": "1", **({"approval": spec_approval} if spec_approval else {})},
                    "plan": {"hash": "plan", "revision": "1", **({"approval": plan_approval} if plan_approval else {})},
                }
            }

        spec = {"artifact_hash": "spec", "revision": "1", "actor": "functional-owner", "intent": "artifact", "approved_at": 1}
        plan = {"artifact_hash": "plan", "revision": "1", "actor": "technical-owner", "intent": "artifact", "approved_at": 2}
        cases = [
            {"id": "spec-pending", "static": {"kind": "workflow-transition", "state": state(None, None), "target": "implementation", "expected_allowed": False, "expected_code": "GATE_REQUIRED", "require_read_only": True, "result": {"status": "passed"}}},
            {"id": "plan-pending", "static": {"kind": "workflow-transition", "state": state(spec, None), "target": "implementation", "expected_allowed": False, "expected_code": "GATE_REQUIRED", "require_read_only": True, "result": {"status": "passed"}}},
            {"id": "both-approved", "static": {"kind": "workflow-transition", "state": state(spec, plan), "target": "implementation", "expected_allowed": True, "result": {"status": "passed"}}},
        ]
        report = run_static_evals.evaluate_cases(
            cases, PLUGIN_SKILLS.parent / "shared" / "forge" / "evals"
        )
        self.assertEqual(3, report["summary"]["passed"])

    def test_brain_adapter_fixture_enforces_designated_approver_policy(self) -> None:
        """Brain supplies approvers; Forge still owns the resulting gate decision."""
        state = {
            "current_actor": "forge-agent",
            "requires_spec_approval": True,
            "artifacts": {
                "specification": {"hash": "spec-r1", "revision": "spec-r1", "approval": {"artifact_hash": "spec-r1", "revision": "spec-r1", "actor": "functional-owner", "intent": "artifact", "approved_at": 1}},
                "plan": {"hash": "plan-r1", "revision": "plan-r1", "approval": {"artifact_hash": "plan-r1", "revision": "plan-r1", "actor": "unapproved-actor", "intent": "artifact", "approved_at": 2}},
            },
        }
        case = {
            "id": "brain-policy",
            "static": {
                "kind": "adapter-parity",
                "fixture": "fixtures/brain-adapter",
                "approval_state": state,
                "target": "implementation",
                "expected_allowed": False,
                "result": {"status": "passed"},
            },
        }
        report = run_static_evals.evaluate_cases(
            [case], PLUGIN_SKILLS.parent / "shared" / "forge" / "evals"
        )
        self.assertEqual(1, report["summary"]["passed"])

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
            findings: list[str] = []
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
        names: list[str] = []
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
            self.assertEqual([], report["platform_extensions"], skill_id)

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
                self.assertEqual(ids, sorted(ids), "ids must stay in ascending order")


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
