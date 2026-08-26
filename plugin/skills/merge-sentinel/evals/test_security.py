"""Release security and integrity checks for Merge Sentinel runtime assets."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
RUNTIME_GLOBS = ("SKILL.md", "agents/openai.yaml", "scripts/**/*.py", "references/*.md")
FORBIDDEN_IMPORTS = {"requests", "httpx", "urllib.request", "socket", "aiohttp"}
PERSONAL_PATH = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]", re.IGNORECASE)
CREDENTIAL_PATTERN = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|secret|password|private[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}"
)


def runtime_files() -> list[Path]:
    files = {SKILL_ROOT / "SKILL.md", SKILL_ROOT / "agents" / "openai.yaml"}
    files.update(SCRIPTS_DIR.rglob("*.py"))
    files.update((SKILL_ROOT / "references").glob("*.md"))
    return sorted(files, key=lambda path: path.relative_to(SKILL_ROOT).as_posix())


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module)
    return modules


class SecurityTests(unittest.TestCase):
    def test_only_stdlib_imports(self) -> None:
        stdlib = getattr(__import__("sys"), "stdlib_module_names")
        allowed_local = {"reviewlib"}
        for path in SCRIPTS_DIR.rglob("*.py"):
            for module in imported_modules(path):
                root = module.split(".", 1)[0]
                self.assertTrue(
                    root in stdlib or root in allowed_local,
                    f"non-stdlib import {module!r} in {path.relative_to(SKILL_ROOT)}",
                )

    def test_no_network_imports_in_scripts(self) -> None:
        for path in SCRIPTS_DIR.rglob("*.py"):
            modules = imported_modules(path)
            self.assertFalse(
                modules & FORBIDDEN_IMPORTS,
                f"network import in {path.relative_to(SKILL_ROOT)}: {modules & FORBIDDEN_IMPORTS}",
            )

    def test_subprocess_only_used_for_fixed_git_command(self) -> None:
        for path in SCRIPTS_DIR.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("shell=True", source)
            if "subprocess" not in imported_modules(path):
                continue
            self.assertEqual(path, SCRIPTS_DIR / "reviewlib" / "anchors.py")
            self.assertIn("subprocess.run(", source)
            self.assertIn('"git", "-C", repo, "diff", "--find-renames=50%", "--name-status", "-z", base_sha, head_sha', source)

    def test_no_absolute_personal_paths_in_runtime_content(self) -> None:
        for path in runtime_files():
            self.assertIsNone(
                PERSONAL_PATH.search(path.read_text(encoding="utf-8")),
                f"absolute personal path in {path.relative_to(SKILL_ROOT)}",
            )

    def test_no_credential_patterns(self) -> None:
        for path in runtime_files():
            self.assertIsNone(
                CREDENTIAL_PATTERN.search(path.read_text(encoding="utf-8")),
                f"possible credential in {path.relative_to(SKILL_ROOT)}",
            )

    def test_runtime_files_match_release_manifest(self) -> None:
        manifest_path = SKILL_ROOT / "release-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["skill_version"], "0.1.0")
        self.assertEqual(manifest["controller_version"], "0.1.0")
        self.assertEqual(manifest["schema_versions"], [1])
        expected = {
            path.relative_to(SKILL_ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in runtime_files()
        }
        self.assertEqual(manifest["files"], expected)


if __name__ == "__main__":
    unittest.main()
