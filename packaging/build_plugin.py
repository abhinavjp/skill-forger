#!/usr/bin/env python3
"""Package the existing canonical plugin payload without rewriting it.

The authored payload lives only in ``plugin/skills/``. This command validates
the immediate Skill directories, refuses duplicate frontmatter names, and
copies the complete ``plugin/`` tree to an ignored directory beneath ``dist/``.
Immediate per-Skill ``evals/results/`` directories are excluded. It never
writes to host discovery trees or back into ``plugin/skills/``.

Usage:
    python packaging/build_plugin.py [--out dist/DIR]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "plugin"
DIST_DIR = REPO_ROOT / "dist"
DEFAULT_OUTPUT = DIST_DIR / "skill-engineer"


def frontmatter_name(skill_md: Path) -> str:
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{skill_md}: missing YAML frontmatter")
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("name:"):
            name = line.removeprefix("name:").strip().strip("'\"")
            if name:
                return name
    raise ValueError(f"{skill_md}: missing frontmatter name")


def discover_skills() -> list[tuple[Path, str]]:
    skills_dir = PLUGIN_DIR / "skills"
    skills: list[tuple[Path, str]] = []
    for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            raise ValueError(f"{skill_dir}: immediate Skill directory has no SKILL.md")
        skills.append((skill_dir, frontmatter_name(skill_md)))
    if not skills:
        raise ValueError("plugin/skills/ contains no discoverable Skills")
    names = [name for _, name in skills]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"duplicate Skill frontmatter names: {duplicates}")
    return skills


def output_path(value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    candidate = candidate.resolve()
    dist_dir = DIST_DIR.resolve()
    if not candidate.is_relative_to(dist_dir) or candidate == dist_dir:
        raise ValueError("--out must be a new directory beneath the ignored dist/ tree")
    return candidate


def ignore_generated_results(directory: str, names: list[str]) -> set[str]:
    """Exclude only immediate per-Skill eval output from distribution copies."""
    try:
        relative = Path(directory).resolve().relative_to(PLUGIN_DIR.resolve())
    except ValueError:
        return set()
    is_skill_evals = (
        len(relative.parts) == 3
        and relative.parts[0] == "skills"
        and relative.parts[2] == "evals"
    )
    if is_skill_evals:
        return {"results"} if "results" in names else set()
    return set()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate plugin/skills/*/SKILL.md and copy the unchanged canonical "
            "plugin/ payload beneath ignored dist/. Never writes host mirrors."
        )
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUTPUT.relative_to(REPO_ROOT)),
        metavar="dist/DIR",
        help="new output directory beneath dist/ (default: dist/skill-engineer)",
    )
    args = parser.parse_args()

    try:
        skills = discover_skills()
        target = output_path(args.out)
        if target.exists():
            raise ValueError(f"output already exists; refusing to overwrite: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(PLUGIN_DIR, target, ignore=ignore_generated_results)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    names = ", ".join(name for _, name in skills)
    print(f"packaged unchanged plugin payload ({names}) to {target.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
