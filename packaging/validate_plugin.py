#!/usr/bin/env python3
"""Deterministic validation for an assembled skill-engineer Agent Plugin.

Checks (Agent Plugins spec v1.0.0):
  1. plugin.json validates against the v1.0.0 manifest schema.
  2. Directory layout matches v1.0.0 discovery rules (skills/<id>/SKILL.md).
  3. No resolved path inside the package escapes the plugin root.
  4. Packaged skill-engineer content is byte-identical to the source of
     truth at skill-engineer/ (no drift between canonical and packaged copy).
  5. skill-engineer/scripts/inspect_skill.py reports no broken references,
     no hardcoded paths, no platform-specific frontmatter keys inside the
     packaged copy.

Usage:
    python packaging/validate_plugin.py <plugin-dir>
"""
from __future__ import annotations

import filecmp
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_SOURCE = REPO_ROOT / "skill-engineer"
SCHEMA_PATH = Path(__file__).resolve().parent / "plugin.schema.1.0.0.json"

REQUIRED_TOP_LEVEL = ["SKILL.md", "references", "scripts"]


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    global _ok
    _ok = False


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


_ok = True


def check_schema(plugin_json: Path) -> None:
    data = json.loads(plugin_json.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    try:
        import jsonschema

        jsonschema.validate(data, schema)
        ok("plugin.json validates against Agent Plugins v1.0.0 schema (jsonschema)")
    except ImportError:
        # Manual fallback covering the schema's required/closed constraints.
        errors = []
        if data.get("$schema") != schema["properties"]["$schema"]["const"]:
            errors.append("$schema mismatch")
        name = data.get("name")
        import re

        if not name or not re.match(schema["properties"]["name"]["pattern"], name):
            errors.append("name missing or fails pattern")
        if not (1 <= len(name or "") <= 64):
            errors.append("name length out of bounds")
        extra = set(data) - set(schema["properties"])
        if extra:
            errors.append(f"additional properties not allowed: {sorted(extra)}")
        missing = set(schema["required"]) - set(data)
        if missing:
            errors.append(f"missing required: {sorted(missing)}")
        if errors:
            fail("plugin.json schema (manual fallback): " + "; ".join(errors))
        else:
            ok("plugin.json validates against Agent Plugins v1.0.0 schema (manual fallback)")
    except Exception as exc:  # jsonschema.ValidationError etc.
        fail(f"plugin.json schema: {exc}")


def check_layout(plugin_dir: Path) -> Path | None:
    plugin_json = plugin_dir / "plugin.json"
    if not plugin_json.is_file():
        fail("plugin.json missing at plugin root")
        return None
    ok("plugin.json present at plugin root")

    skills_dir = plugin_dir / "skills"
    if not skills_dir.is_dir():
        fail("skills/ directory missing")
        return None

    skill_dirs = [
        d for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()
    ]
    if len(skill_dirs) != 1 or skill_dirs[0].name != "skill-engineer":
        fail(f"expected exactly skills/skill-engineer/SKILL.md, found: {skill_dirs}")
        return None
    ok("skills/skill-engineer/SKILL.md discoverable per v1.0.0 layout rules")
    return skill_dirs[0]


def check_containment(plugin_dir: Path) -> None:
    plugin_dir = plugin_dir.resolve()
    escapes = []
    for p in plugin_dir.rglob("*"):
        try:
            resolved = p.resolve()
        except OSError:
            escapes.append(str(p))
            continue
        if plugin_dir not in resolved.parents and resolved != plugin_dir:
            escapes.append(str(p))
    if escapes:
        fail(f"paths resolve outside plugin root: {escapes}")
    else:
        ok("all packaged paths resolve within the plugin root")


def check_content_match(skill_dir: Path) -> None:
    mismatches = []
    for name in REQUIRED_TOP_LEVEL:
        src = SKILL_SOURCE / name
        dst = skill_dir / name
        if src.is_dir():
            cmp = filecmp.dircmp(src, dst, ignore=["__pycache__"])
            _walk_dircmp(cmp, mismatches, name)
        else:
            if not dst.is_file() or src.read_bytes() != dst.read_bytes():
                mismatches.append(name)
    if mismatches:
        fail(f"packaged content differs from skill-engineer/ source: {mismatches}")
    else:
        ok("packaged skill-engineer content is byte-identical to source of truth")


def _walk_dircmp(cmp: filecmp.dircmp, mismatches: list[str], prefix: str) -> None:
    for name in cmp.left_only:
        mismatches.append(f"{prefix}/{name} (missing from package)")
    for name in cmp.right_only:
        mismatches.append(f"{prefix}/{name} (extra in package)")
    for name in cmp.diff_files:
        mismatches.append(f"{prefix}/{name} (content differs)")
    for name, sub in cmp.subdirs.items():
        _walk_dircmp(sub, mismatches, f"{prefix}/{name}")


def check_inspector(skill_dir: Path) -> None:
    inspector = SKILL_SOURCE / "scripts" / "inspect_skill.py"
    proc = subprocess.run(
        [sys.executable, str(inspector), str(skill_dir)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        fail(f"inspect_skill.py failed on packaged copy: {proc.stderr.strip()}")
        return
    data = json.loads(proc.stdout)
    m = data["metrics"]
    problems = []
    if m["metadata_error_count"]:
        problems.append("metadata errors")
    if m["broken_reference_count"]:
        problems.append("broken references")
    if m["hardcoded_path_count"]:
        problems.append("hardcoded paths")
    if data["platform_extensions"]:
        problems.append("platform-specific frontmatter keys")
    if data["exact_duplicates"]:
        problems.append("exact duplicate blocks")
    if problems:
        fail(f"inspect_skill.py findings in packaged copy: {problems}")
    else:
        ok("inspect_skill.py: 0 broken references, 0 hardcoded paths, 0 platform-specific keys")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    plugin_dir = Path(sys.argv[1])
    if not plugin_dir.is_dir():
        print(f"error: not a directory: {plugin_dir}", file=sys.stderr)
        return 2

    check_schema(plugin_dir / "plugin.json")
    skill_dir = check_layout(plugin_dir)
    check_containment(plugin_dir)
    if skill_dir is not None:
        check_content_match(skill_dir)
        check_inspector(skill_dir)

    print()
    print("RESULT:", "PASS" if _ok else "FAIL")
    return 0 if _ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
