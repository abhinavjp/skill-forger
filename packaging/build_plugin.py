#!/usr/bin/env python3
"""Deterministically mirror skill-engineer/ into every host discovery path.

skill-engineer/ (SKILL.md, references/, scripts/) is the canonical source.
This script never edits it; it only regenerates tracked mirrors so each host
can discover the Skill directly from a git clone of this repo, with no build
step required on the consumer's side:

  plugin/skills/skill-engineer/    Agent Plugins v1.0.0 package (plugin/plugin.json
                                    at the package root) and the Claude Code plugin
                                    (plugin/.claude-plugin/plugin.json, referenced by
                                    .claude-plugin/marketplace.json)
  .agents/skills/skill-engineer/   Auto-discovered by Cursor and OpenAI Codex CLI,
                                    which both scan .agents/skills/ at the project root

Usage:
    python packaging/build_plugin.py [--out DIR ...]
        --out overrides/adds mirror targets instead of the two defaults above.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_SOURCE = REPO_ROOT / "skill-engineer"
SKILL_ID = "skill-engineer"

DEFAULT_MIRRORS = [
    REPO_ROOT / "plugin" / "skills" / SKILL_ID,
    REPO_ROOT / ".agents" / "skills" / SKILL_ID,
]

# Only what SKILL.md's own references resolve to at runtime (confirmed via
# scripts/inspect_skill.py: no broken references, evals/ is not referenced
# as a runtime dependency).
REQUIRED_TOP_LEVEL = ["SKILL.md", "references", "scripts"]


def build_mirror(target: Path) -> int:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    count = 0
    for name in REQUIRED_TOP_LEVEL:
        item = SKILL_SOURCE / name
        if not item.exists():
            print(f"error: required Skill path missing: {item}", file=sys.stderr)
            sys.exit(1)
        if item.is_dir():
            dest = target / name
            shutil.copytree(
                item, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
            )
            count += sum(1 for p in dest.rglob("*") if p.is_file())
        else:
            shutil.copy2(item, target / name)
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        action="append",
        help="Mirror target directory (repeatable). Defaults to the two "
        "canonical host discovery paths if omitted.",
    )
    args = parser.parse_args()

    targets = [Path(p).resolve() for p in args.out] if args.out else DEFAULT_MIRRORS

    for target in targets:
        count = build_mirror(target)
        print(f"{target.relative_to(REPO_ROOT) if REPO_ROOT in target.parents else target} <- skill-engineer/ ({count} files)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
