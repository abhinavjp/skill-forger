# Portable eval model

Evals are part of Skill engineering, not part of the Agent Skills format. The
canonical corpus stays platform-neutral so it survives a change of host — and so
a broken host runner cannot be mistaken for a broken Skill.

## Layers

| Layer | What it measures | Model needed |
|-------|------------------|--------------|
| A — Static validation | Frontmatter, paths, broken references, missing fixtures, eval-schema shape, platform metadata | No |
| B — Trigger evals | Implicit routing, measured independently of execution | Yes |
| C — Execution evals | Whether the Skill performs its intended work | Yes |
| D — Differential evals | Candidate vs previous version vs no-Skill | Yes |

Layer A is fully covered by `scripts/inspect_skill.py` and
`scripts/validate_evals.py`. Do not mix explicit invocation into implicit
trigger precision/recall — they are different modes.

## Case schema

One case per mapping; a file may hold a single case or a list.

```yaml
version: 1

id: EX-001
kind: trigger | execution
category: positive | negative | boundary | adversarial | regression |
          paraphrase | near-neighbour | competing-skill | large-input |
          failure-injection

prompt: |
  ...

fixtures: []          # paths relative to the case file
setup: []             # commands/state the harness applies first
trials: 1

expected:
  trigger: true       # required for kind: trigger
  outcome:
    assertions: []
  state:
    assertions: []
  process:
    required: []      # only where the process itself is required
    forbidden: []

graders:
  - type: deterministic | process | llm-judge | human
    check: ...
    rubric: ...       # required for llm-judge

budgets:
  tokens: null
  duration_ms: null
  tool_calls: null
  commands: null

platforms:
  required: []
  optional: []

tags: []
```

Extensible by design: unknown top-level keys are permitted, unknown *budget*
keys are not (they are silently ignored by runners otherwise).

Validate with:

```
python scripts/validate_evals.py <path> [--json]
```

## Required coverage

Every Skill with evals should carry, where the category is meaningful:
`positive`, `negative`, `boundary`, `adversarial`, `regression`. Add
`paraphrase`, `near-neighbour`, `competing-skill`, `large-input` and
`failure-injection` where the Skill's characteristics warrant them — not for
completeness.

## Fixtures

Keep both kinds:

- **Known-good** — valid Skill, correct reference structure, safely mutating
  workflow, correctly scoped description.
- **Intentionally defective** — one or more *known* defects: broken reference,
  overbroad description, false-trigger neighbour, oversized irrelevant
  reference, unsafe script, duplicated stale instruction, platform-specific
  field in an allegedly portable Skill, workflow that can complete prematurely,
  mutation that duplicates on re-run.

Every defective fixture must declare the defect it contains — that is what makes
the reviewer itself regression-testable.

## Grading order

1. **Deterministic outcome/state** — preferred. File exists, parser succeeds,
   tests pass, state mutated correctly, duplicate mutation absent.
2. **Deterministic process** — only where the process is itself required for
   correctness or safety (validator ran before deploy; destructive command never
   executed). Never require one exact trajectory when several are valid.
3. **LLM judge** — only where semantic judgement is unavoidable. Requires a
   narrow criterion, an explicit rubric, an evidence-backed verdict, structured
   output, and the judge model identifier where available.
4. **Human review** — judge calibration, high-value subjective criteria,
   disputed cases.

Prefer outcome/state grading over grading the final text.

## Trials

Use multiple trials when trigger behaviour varies, reasoning is stochastic,
candidates are close, an LLM judge is involved, or a failure looks intermittent.

Record at minimum `trial count`, `pass count`, `pass rate`; where useful, median
tokens, median duration, variance and p95 latency. Do not claim statistical
significance without the data to support it.

## Efficiency metrics

Correctness first. Then, where the host exposes them: input/context tokens,
output tokens, duration, tool calls, commands, retries, errors, references
loaded, subagents spawned, side-effect operations.

## Failure classification

Classify every failed trial before it counts against the Skill:

```
Skill failure | routing failure | model variance | tool failure |
fixture failure | harness failure | environment failure | grader failure
```

Host Skill-eval tooling has documented false-negative trigger failures. An
unclassified failure is not evidence.

## Change → suite map

| Change | Run |
|--------|-----|
| name / description | Full trigger suite, competing-Skill cases, trigger regressions |
| core workflow | Execution smoke, affected cases, historical regressions |
| reference | Cases that require that reference |
| script | Script tests plus dependent execution cases |
| platform adapter | That host's validation and runtime suite |
| safety / permission logic | Adversarial, failure, side-effect and permission cases |

Always run the minimal smoke suite. Retain reproducible known failures as
regression cases permanently.

## Runner architecture

If a runner is implemented, keep the seams:

```
portable eval case → host adapter → agent execution →
normalized trace/result → graders → comparison/report
```

Case definitions, grading criteria and the regression corpus must not embed any
host's trace format. `evals/run_static_evals.py` in this Skill implements the
deterministic slice of that pipeline (Layer A and deterministic Layer C) with no
model and no host adapter; Layers B and D require a host runner.
