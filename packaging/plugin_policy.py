"""Canonical packaging policy shared by validators and regression tests."""
from __future__ import annotations


CANONICAL_EVAL_VALIDATORS = {
    "forge-plan": "plugin/skills/forge-plan/evals/run_static_evals.py",
    "merge-sentinel": "plugin/skills/merge-sentinel/evals/validate_corpus.py",
    "skill-engineer": "plugin/skills/skill-engineer/scripts/validate_evals.py",
    "skill-prospector": "plugin/skills/skill-engineer/scripts/validate_evals.py",
    "forge-clarify": "plugin/skills/skill-engineer/scripts/validate_evals.py",
    "forge-discover": "plugin/skills/skill-engineer/scripts/validate_evals.py",
    "forge-spec": "plugin/skills/skill-engineer/scripts/validate_evals.py",
    "forge-implement": "plugin/skills/skill-engineer/scripts/validate_evals.py",
}
EXPECTED_SKILL_IDS = frozenset(CANONICAL_EVAL_VALIDATORS)
