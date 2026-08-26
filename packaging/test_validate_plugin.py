#!/usr/bin/env python3
"""Regression tests for the repository's canonical plugin payload."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_SKILLS = REPO_ROOT / "plugin" / "skills"
EXPECTED_SKILL_IDS = {"merge-sentinel", "skill-engineer"}


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
                if re.search(
                    r"(?i)(?:[a-z]:[\\/]+users[\\/]+[^\\/]+|/(?:home|users)/[^/]+)",
                    finding["match"],
                )
            ]
            self.assertEqual([], personal_paths, skill_id)
            self.assertEqual([], report["platform_extensions"], skill_id)

        self.assertEqual(sorted(EXPECTED_SKILL_IDS), sorted(names))
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
