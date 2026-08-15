# skill-forger

*Forges Agent Skills. Catches the forgeries.*

An agent-agnostic Agent Skill that creates and reviews Agent Skills, built to
`SKILL_ENGINEERING_SPEC.md`. The Skill itself is `skill-engineer/` and obeys the
rules it enforces.

```
skill-engineer/
├── SKILL.md                        operational core (CREATE + REVIEW)
├── references/
│   ├── rules-index.md              routes R1–R26 to the modules below
│   ├── rules-core.md               always loaded: mechanism, safety, drift
│   ├── rules-trigger.md            routing, precision/recall, competition
│   ├── rules-context.md            disclosure, references, branches, filtering
│   ├── rules-execution.md          workflow, scripts, tools, completion
│   ├── rules-mutation-safety.md    failure recovery, idempotency
│   ├── rules-portability.md        portability boundary
│   ├── rules-evals.md              regression preservation, measured utility
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
host runner. Requires Python 3.8+; PyYAML for the YAML cases. Where a host
cannot run Python or scripts, the Skill still reviews what it can read and
reports the deterministic checks as unvalidated rather than claiming them.

Eval cases are data. A deterministic grader selects a `check.kind` implemented
by trusted runner code; it cannot carry a command line, and the runner spawns no
subprocess — so pointing `--evals` at an untrusted corpus does not execute it
(`RG-008` is the containment test).

Inspect any Skill package:

```bash
python skill-engineer/scripts/inspect_skill.py <skill-dir>
```
