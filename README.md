# skill-forger

*Forges Agent Skills. Catches the forgeries.*

An agent-agnostic Agent Skill that creates and reviews Agent Skills, built to
`SKILL_ENGINEERING_SPEC.md`. The Skill itself is `skill-engineer/` and obeys the
rules it enforces.

```
skill-engineer/
├── SKILL.md                        operational core (CREATE + REVIEW)
├── references/
│   ├── rules.md                    R1–R26, the shared rule set
│   ├── eval-spec.md                portable eval schema, layers, grading
│   └── platform-extensions.md      optional host adapters
├── scripts/
│   ├── inspect_skill.py            deterministic inspector (facts only)
│   └── validate_evals.py           portable eval-schema validator
└── evals/
    ├── trigger.yaml                Layer B (needs a host runner)
    ├── execution.yaml              Layer C (deterministic + judged cases)
    ├── regressions.yaml            reproducible past failures
    ├── run_static_evals.py         deterministic runner, no model
    └── fixtures/                   known-good and intentionally defective
```

Install by copying `skill-engineer/` into any Agent Skills-compatible skills
directory. No host-specific configuration is required.

## Running the checks

```bash
python skill-engineer/evals/run_static_evals.py
```

Runs every case with a deterministic grader and reports the rest as requiring a
host runner. Requires Python 3.8+; PyYAML for the YAML cases.

Inspect any Skill package:

```bash
python skill-engineer/scripts/inspect_skill.py <skill-dir>
```
