#!/usr/bin/env python3
"""Report lexical overlap between the shipped Skills' routing metadata.

Two Skills compete for the same requests when their ``name`` + ``description``
say nearly the same thing, so this reports the most overlapping pairs to triage
first when adding a Skill or rewording one.

WHAT THIS IS NOT
    This is a lexical proxy, not a routing measurement.  It cannot see the
    clause a router actually discriminates on -- "but no Plan yet" versus
    "already has an approved Plan" are near-identical to this script and
    decisive to a router.  Only a host-routing trial measures routing.

WHY IT IS NOT A PASS/FAIL GATE
    Adjacent workflow stages legitimately share domain nouns, so a threshold
    would flag correct descriptions.  Worse, it is trivially gamed by dropping
    canonical vocabulary: rewording forge-implement away from "execution
    packets" scores better and is a worse description, because that term is
    what the workflow contract and the Skill bodies use.  Optimise the score
    and you get terminology drift.  Read the ranking, then use judgement.

Usage:
    python packaging/measure_catalog_overlap.py [--json] [--top N]
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_SKILLS = REPO_ROOT / "plugin" / "skills"

# Function words carry no routing signal; keeping them inflates every pair
# equally and compresses the ranking this script exists to produce.
STOPWORDS = frozenset(
    """use when a an the to and or of for it its is are be by with on in from that this
    into then than only not do does did should must can may them they their there here
    what which who whom how why any all each every other another new before after""".split()
)


def read_metadata(skill_md: Path) -> tuple[str, str] | None:
    """Return (name, description) from a SKILL.md frontmatter block."""
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    front = parts[1]
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    description = re.search(r"^description:\s*(.+?)(?=^\w+:|\Z)", front, re.M | re.S)
    if not name or not description:
        return None
    return name.group(1).strip(), " ".join(description.group(1).split())


def content_words(text: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z][a-z-]+", text.lower())
        if word not in STOPWORDS and len(word) > 2
    }


def measure(skills_dir: Path = PLUGIN_SKILLS) -> dict:
    vocabularies: dict[str, set[str]] = {}
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        metadata = read_metadata(skill_md)
        if metadata is None:
            continue
        name, description = metadata
        vocabularies[name] = content_words(f"{name} {description}")

    pairs = []
    for left, right in itertools.combinations(sorted(vocabularies), 2):
        first, second = vocabularies[left], vocabularies[right]
        union = first | second
        overlap = len(first & second) / len(union) if union else 0.0
        pairs.append(
            {
                "pair": [left, right],
                "jaccard": round(overlap, 4),
                "shared": sorted(first & second),
            }
        )
    pairs.sort(key=lambda item: (-item["jaccard"], item["pair"]))
    scores = [item["jaccard"] for item in pairs] or [0.0]
    return {
        "skills": sorted(vocabularies),
        "pair_count": len(pairs),
        "max_jaccard": max(scores),
        "mean_jaccard": round(sum(scores) / len(scores), 4),
        "pairs": pairs,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the full report as JSON")
    parser.add_argument("--top", type=int, default=8, help="how many pairs to print")
    args = parser.parse_args(argv)

    report = measure()
    if not report["skills"]:
        print("no Skill packages found", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, sort_keys=True, indent=2))
        return 0

    print(f"{len(report['skills'])} Skills, {report['pair_count']} pairs")
    print(f"max={report['max_jaccard']:.3f}  mean={report['mean_jaccard']:.3f}\n")
    for item in report["pairs"][: max(args.top, 0)]:
        left, right = item["pair"]
        print(f"{item['jaccard']:.3f}  {left:16s} {right:16s} shared={item['shared']}")
    print("\nLexical proxy only -- routing is measured by a host-routing trial.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
