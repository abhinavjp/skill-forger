#!/usr/bin/env python3
"""Deterministic validation for the skill-engineer plugin packaging.

Checks:
  1. plugin/plugin.json validates against the Agent Plugins v1.0.0 manifest schema.
  2. plugin/ layout matches v1.0.0 discovery rules (skills/<id>/SKILL.md).
  3. No resolved path inside plugin/ escapes the plugin root.
  4. plugin/skills/skill-engineer/ and .agents/skills/skill-engineer/ are
     byte-identical to the source of truth at skill-engineer/.
  5. scripts/inspect_skill.py reports no broken references, no hardcoded
     paths, no platform-specific frontmatter keys inside the packaged copy.
  6. plugin/.claude-plugin/plugin.json and .claude-plugin/marketplace.json
     carry Claude Code's required fields and a consistent plugin name.

Usage:
    python packaging/validate_plugin.py
"""
from __future__ import annotations

import filecmp
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_SOURCE = REPO_ROOT / "skill-engineer"
SCHEMA_PATH = Path(__file__).resolve().parent / "plugin.schema.1.0.0.json"
SKILL_ID = "skill-engineer"

PLUGIN_DIR = REPO_ROOT / "plugin"
CLAUDE_PLUGIN_JSON = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"
AGENTS_MIRROR = REPO_ROOT / ".agents" / "skills" / SKILL_ID

REQUIRED_TOP_LEVEL = ["SKILL.md", "references", "scripts"]

_ok = True


def fail(msg: str) -> None:
    global _ok
    _ok = False
    print(f"FAIL: {msg}")


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


def check_schema(plugin_json: Path) -> None:
    data = json.loads(plugin_json.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    try:
        import jsonschema

        jsonschema.validate(data, schema)
        ok("plugin/plugin.json validates against Agent Plugins v1.0.0 schema (jsonschema)")
    except ImportError:
        errors = []
        if data.get("$schema") != schema["properties"]["$schema"]["const"]:
            errors.append("$schema mismatch")
        name = data.get("name")
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
            fail("plugin/plugin.json schema (manual fallback): " + "; ".join(errors))
        else:
            ok("plugin/plugin.json validates against Agent Plugins v1.0.0 schema (manual fallback)")
    except Exception as exc:
        fail(f"plugin/plugin.json schema: {exc}")


def check_layout(plugin_dir: Path) -> Path | None:
    if not (plugin_dir / "plugin.json").is_file():
        fail("plugin/plugin.json missing at plugin root")
        return None
    ok("plugin/plugin.json present at plugin root")

    skills_dir = plugin_dir / "skills"
    if not skills_dir.is_dir():
        fail("plugin/skills/ directory missing")
        return None

    skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()]
    if len(skill_dirs) != 1 or skill_dirs[0].name != SKILL_ID:
        fail(f"expected exactly plugin/skills/{SKILL_ID}/SKILL.md, found: {skill_dirs}")
        return None
    ok(f"plugin/skills/{SKILL_ID}/SKILL.md discoverable per v1.0.0 layout rules")
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


def check_content_match(label: str, mirror_dir: Path) -> None:
    mismatches: list[str] = []
    for name in REQUIRED_TOP_LEVEL:
        src = SKILL_SOURCE / name
        dst = mirror_dir / name
        if src.is_dir():
            cmp = filecmp.dircmp(src, dst, ignore=["__pycache__"])
            _walk_dircmp(cmp, mismatches, name)
        else:
            if not dst.is_file() or src.read_bytes() != dst.read_bytes():
                mismatches.append(name)
    if mismatches:
        fail(f"{label} differs from skill-engineer/ source: {mismatches}")
    else:
        ok(f"{label} is byte-identical to source of truth")


def _walk_dircmp(cmp: filecmp.dircmp, mismatches: list[str], prefix: str) -> None:
    for name in cmp.left_only:
        mismatches.append(f"{prefix}/{name} (missing from package)")
    for name in cmp.right_only:
        mismatches.append(f"{prefix}/{name} (extra in package)")
    for name in cmp.diff_files:
        mismatches.append(f"{prefix}/{name} (content differs)")
    for name, sub in cmp.subdirs.items():
        _walk_dircmp(sub, mismatches, f"{prefix}/{name}")


def check_inspector(skill_dir: Path, label: str) -> None:
    inspector = SKILL_SOURCE / "scripts" / "inspect_skill.py"
    proc = subprocess.run(
        [sys.executable, str(inspector), str(skill_dir)], capture_output=True, text=True
    )
    if proc.returncode != 0:
        fail(f"inspect_skill.py failed on {label}: {proc.stderr.strip()}")
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
        fail(f"inspect_skill.py findings in {label}: {problems}")
    else:
        ok(f"inspect_skill.py: 0 broken references, 0 hardcoded paths, 0 platform-specific keys ({label})")


def check_claude_manifest() -> None:
    if not CLAUDE_PLUGIN_JSON.is_file():
        fail("plugin/.claude-plugin/plugin.json missing")
        return
    data = json.loads(CLAUDE_PLUGIN_JSON.read_text(encoding="utf-8"))
    if not data.get("name"):
        fail("plugin/.claude-plugin/plugin.json missing required 'name'")
        return
    ok("plugin/.claude-plugin/plugin.json has required 'name' field")

    if not MARKETPLACE_JSON.is_file():
        fail(".claude-plugin/marketplace.json missing")
        return
    market = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    missing = [f for f in ("name", "owner", "plugins") if f not in market]
    if missing:
        fail(f".claude-plugin/marketplace.json missing required fields: {missing}")
        return
    entries = [p for p in market["plugins"] if p.get("name") == data["name"]]
    if not entries:
        fail(f".claude-plugin/marketplace.json has no entry named '{data['name']}'")
        return
    source = entries[0].get("source")
    if source != "./plugin":
        fail(f".claude-plugin/marketplace.json entry source is {source!r}, expected './plugin'")
        return
    ok(".claude-plugin/marketplace.json has a matching, correctly-sourced plugin entry")


def main() -> int:
    check_schema(PLUGIN_DIR / "plugin.json")
    skill_dir = check_layout(PLUGIN_DIR)
    check_containment(PLUGIN_DIR)
    if skill_dir is not None:
        check_content_match("plugin/skills/skill-engineer/", skill_dir)
        check_inspector(skill_dir, "plugin/skills/skill-engineer/")
    check_content_match(".agents/skills/skill-engineer/", AGENTS_MIRROR)
    if AGENTS_MIRROR.is_dir():
        check_inspector(AGENTS_MIRROR, ".agents/skills/skill-engineer/")
    check_claude_manifest()

    print()
    print("RESULT:", "PASS" if _ok else "FAIL")
    return 0 if _ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
