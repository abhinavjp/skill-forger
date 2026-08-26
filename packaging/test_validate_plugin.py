#!/usr/bin/env python3
"""Regression tests for the repository's canonical plugin payload."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_SKILLS = REPO_ROOT / "plugin" / "skills"
EXPECTED_SKILL_IDS = {"merge-sentinel", "skill-engineer"}
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
    def test_plugin_skills_are_the_complete_canonical_payload(self) -> None:
        """Catches a missing, extra, or incompletely packaged canonical skill."""
        discovered = {
            path.name
            for path in PLUGIN_SKILLS.iterdir()
            if path.is_dir() and (path / "SKILL.md").is_file()
        }
        self.assertEqual(EXPECTED_SKILL_IDS, discovered)

    def test_no_repository_skill_mirror_exists(self) -> None:
        """Catches reintroduction of authored host mirrors outside plugin/skills/."""
        mirrors = [
            REPO_ROOT / "skill-engineer",
            REPO_ROOT / ".agents" / "skills" / "skill-engineer",
            REPO_ROOT / ".agents" / "skills" / "merge-sentinel",
        ]
        self.assertEqual([], [str(path.relative_to(REPO_ROOT)) for path in mirrors if path.exists()])

    def test_canonical_payload_excludes_generated_eval_results(self) -> None:
        """Catches committed or generated eval output in an authored Skill tree."""
        result_dirs = sorted(
            str(path.relative_to(REPO_ROOT))
            for path in PLUGIN_SKILLS.glob("*/evals/results")
            if path.is_dir()
        )
        self.assertEqual([], result_dirs)

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


if __name__ == "__main__":
    unittest.main()
