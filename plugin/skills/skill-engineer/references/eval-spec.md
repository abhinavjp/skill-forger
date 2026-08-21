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

**Keep the layers apart in the cases themselves.** A trigger case grades
selection and nothing else; the moment its grader inspects what the Skill did
afterwards, a routing failure and an execution failure become the same red
result, and a host that satisfies the rubric through some other mechanism
passes a case the Skill never routed to. Where one prompt is worth measuring
both ways, ship two cases with the same prompt — one trigger, one execution —
and cross-reference them in their notes.

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
  - type: deterministic | host-routing | process | llm-judge | human
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

competition:          # required for category: competing-skill
  required_candidates: []
  expected_policy: skill-engineer-wins | competitor-wins | either | coactivation

tags: []
```

Extensible by design: unknown top-level keys are permitted, unknown *budget*
keys are not (they are silently ignored by runners otherwise).

### Graders and checks

A **`host-routing`** grader is the only way to assert selection, and every
trigger case needs one. It names the Skill whose selection is being asserted, so
"skill selected" can never quietly mean "some skill was selected":

```yaml
- type: host-routing
  check:
    selected_skill: skill-engineer
    selected: true
```

A **`deterministic`** grader names a `check.kind` from a fixed vocabulary that
trusted runner code implements. Cases are data; they do not carry command lines,
interpreters, or paths outside the package:

```yaml
- type: deterministic
  check:
    kind: inspect          # inspect | validate-evals | file-exists | validator
    target: evals/fixtures/good-release-notes
    expect_exit: 0
    stdout_contains: ['"broken_reference_count": 0']
```

`check.command` is rejected by the validator. An evaluator that runs commands
supplied by its own corpus hands whoever wrote that corpus the reviewer's
permissions — the sharpest version of the supply-chain problem the reviewer
exists to find (R21). A check that cannot be expressed in the vocabulary earns
a new `kind` implemented and reviewed as code, or a named `validator` function;
both are code changes, not data changes. `RG-008` is the containment test.

### Competition preconditions

A `competing-skill` case must declare which competitors have to be present for
the result to mean anything:

```yaml
competition:
  required_candidates: [skill-engineer, pdf]
  expected_policy: skill-engineer-wins
```

The host runner captures the catalog before each trial and marks the case
**UNMEASURED** — not passed, not failed — when a required candidate is missing
or not routable. Run important trigger boundaries in at least four
environments: candidate alone, candidate plus one deliberately overlapping
Skill, a representative production catalog, and a high-overlap catalog. Record
which candidate won each trial, not merely whether the candidate did.

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

Keep at least one known-good fixture per major applicability class the reviewer
must judge — a read-only Skill, a safely mutating one — or the corpus rewards a
reviewer that raises those rules unconditionally.

### Known-good fixtures are frozen, and disputes are adjudicated

A known-good fixture is a claim, not a fact — and so is a finding against one.
An evidence-backed finding can still be wrong: quoting real fixture text proves
attribution, not defect, and not severity.

Freeze known-good expectations for a validation cycle. When a reviewer raises a
finding a known-good fixture does not account for:

1. mark the case **DISPUTED / NEEDS ADJUDICATION** — it counts as neither a
   reviewer pass nor a fixture failure;
2. adjudicate independently: human review, a second judge working from its own
   rubric, official platform evidence, or a focused behavioural experiment;
3. change the fixture only after adjudication concludes the fixture was wrong;
4. record the adjudication evidence and outcome in the fixture's `defects.json`
   alongside the change, so the corpus keeps its history.

Rewriting the fixture whenever the reviewer complains closes a loop — the rules
define a suspicious pattern, the reviewer reports it, the quoted evidence is
taken as proof, the fixture is reclassified, and the corpus now ratifies the
reviewer's interpretation. A systematically overcritical reviewer keeps a
perfect record by moving the goalposts, and the fixture stops detecting the
false positives it exists to detect. Grading a real finding as a false positive
teaches the reviewer to miss it; grading a false positive as a real finding
teaches it to shout. Adjudication is what tells them apart.

Seed known-good fixtures with features that are easy to criticise and
deliberately correct — a repetition a protocol requires, a small unconditional
reference cheaper than the branch machinery that would avoid it, an illustrative
shell example that is not an execution contract — and list them as
`adjudicated_non_defects` with the reasoning. A finding against one of those is
a false positive, and the grader should say so.

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
fixture failure | harness failure | environment failure | grader failure |
unmeasured (precondition absent) | disputed (awaiting adjudication)
```

The last two are not failures and not passes. `unmeasured` covers a trial whose
precondition did not hold — a required competitor missing from the catalog, a
capability the host lacks. `disputed` covers a finding against a frozen
known-good fixture. Reporting either as a pass is how a suite comes to overstate
what it established.

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
