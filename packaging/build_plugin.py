#!/usr/bin/env python3
"""Deterministically assemble the skill-engineer Agent Plugin (spec v1.0.0).

Copies the canonical Skill source (SKILL.md, references/, scripts/) from
skill-engineer/ into a plugin package under skills/skill-engineer/, alongside
the tracked packaging/plugin.json manifest. Does not touch skill-engineer/.

Usage:
    python packaging/build_plugin.py [--out DIST_DIR]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_SOURCE = REPO_ROOT / "skill-engineer"
MANIFEST_SOURCE = Path(__file__).resolve().parent / "plugin.json"
SKILL_ID = "skill-engineer"

# Only what SKILL.md's own references resolve to at runtime (confirmed via
# scripts/inspect_skill.py: no broken references, evals/ is not referenced
# as a runtime dependency).
REQUIRED_TOP_LEVEL = ["SKILL.md", "references", "scripts"]


def copy_skill(src: Path, dst: Path) -> list[Path]:
    copied: list[Path] = []
    dst.mkdir(parents=True, exist_ok=True)
    for name in REQUIRED_TOP_LEVEL:
        item = src / name
        if not item.exists():
            print(f"error: required Skill path missing: {item}", file=sys.stderr)
            sys.exit(1)
        if item.is_dir():
            target = dst / name
            shutil.copytree(
                item,
                target,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            copied.extend(p for p in target.rglob("*") if p.is_file())
        else:
            target = dst / name
            shutil.copy2(item, target)
            copied.append(target)
    return copied


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default=str(REPO_ROOT / "dist" / "skill-engineer-plugin"),
        help="Plugin output directory (default: dist/skill-engineer-plugin)",
    )
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    shutil.copy2(MANIFEST_SOURCE, out_dir / "plugin.json")

    skills_dir = out_dir / "skills" / SKILL_ID
    copied = copy_skill(SKILL_SOURCE, skills_dir)

    print(f"plugin.json     -> {out_dir / 'plugin.json'}")
    print(f"skills/{SKILL_ID}/ <- {SKILL_SOURCE} ({len(copied)} files)")
    print(f"\nBuilt: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
