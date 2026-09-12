# Forge Portable SDLC — Implementation Plan

## 1. Goal

Implement five portable, explicitly user-invoked Forge SDLC Skills:

- `forge-clarify`
- `forge-discover`
- `forge-spec`
- `forge-plan`
- `forge-implement`

The Forge suite must provide one portable source of truth for shared SDLC behaviour while allowing Brain-specific Skills to remain thin adapters.

The completed implementation must be:

- portable across compatible harnesses
- safe to resume
- evidence-driven
- token-conscious
- deterministic where practical
- usable without Brain Payroll, Jira, OKF, named models, subagents, hooks, MCP servers, shells, or interpreters as correctness dependencies
- detailed enough that a competent workhorse can execute an approved plan without new research, architecture selection, or user questions

**Specification:** `docs/specs/forge-portable-sdlc.md`

---

## 2. Non-Goals

Do not:

- change the existing BA Skill
- change or replace MR Review
- make Jira or OKF mandatory for Forge
- add host-specific copies of Forge Skills
- require delegation/subagents for correctness
- automatically publish Forge artifacts to issue trackers
- automatically repair unrelated knowledge/repository defects
- automatically edit `.gitignore`
- silently expand approved scope
- include pre-existing unrelated working-tree changes
- automatically push, squash, open a PR, or merge
- move implementation design back into `forge-spec`
- make plans pre-write full implementations where a concise contract or sketch is sufficient

---

## 3. Relevant Existing State

### Existing plugin

The repository currently has three required Skills:

- `merge-sentinel`
- `skill-engineer`
- `skill-prospector`

Packaging currently assumes this baseline and must be changed so additional valid Skills are supported without allowing the existing required Skills to disappear.

### Existing reusable validation

Reuse, extend, or integrate with:

- `packaging/validate_plugin.py`
- `packaging/test_validate_plugin.py`
- `packaging/build_plugin.py`
- `plugin/skills/skill-engineer/scripts/inspect_skill.py`
- `plugin/skills/skill-engineer/scripts/validate_evals.py`
- existing version-1 eval schema
- existing repository package/build validation

Do not introduce a second evaluation framework unless the existing seams cannot cover a required deterministic behaviour.

### Brain packages

The actual Brain clarification/discovery/specification/planning/implementation packages are not present in this repository.

This repository therefore implements and verifies the **portable Forge core + Brain adapter contract**.

The repository-specific Brain refactor remains a separate follow-up plan in the repository that owns those packages.

---

## 4. Planning Research and Frozen Decisions

The following decisions are frozen for implementation.

### PD-001 — Five user-facing stages

Use five separate user-facing Skills because the stages have different intent, input/output artifacts, completion conditions, and context surfaces.

### PD-002 — Shared core is not a sixth Skill

Shared contracts, deterministic utilities, fixtures, and cross-stage evals live under:

`plugin/shared/forge/`

They must remain outside `plugin/skills/` so they cannot be discovered as user-facing Skills.

### PD-003 — Canonical authored payload

`plugin/` is the authored plugin payload.

Do not create tracked harness-specific Skill mirrors.

### PD-004 — Portable core / adapter split

Forge defines portable semantics.

Adapters may supply:

- issue acquisition
- project knowledge
- artifact location conventions
- validators
- authorized delivery operations

Adapters must not redefine Forge stage semantics.

### PD-005 — Approval semantics

Approval is tied to meaningful artifact content.

Formatting noise that does not change meaning must not invalidate approval, while meaning-bearing indentation/whitespace must remain significant.

### PD-006 — Workflow status semantics

All applicable checks report one of:

- `PASS`
- `FAIL`
- `UNMEASURED`

Unavailable or incomplete verification is never treated as a pass.

### PD-007 — Retry semantics

Transient retries are bounded.

Deterministic failures may be retried only after a relevant state/input change that could affect the result.

### PD-008 — Plan contradiction semantics

A contradiction blocks the affected packet and transitive dependants.

Independent packets whose approved inputs remain valid may continue.

### PD-009 — Scope semantics

Unplanned scope must be surfaced for authorization.

It is never implemented silently.

### PD-010 — Verification structure

Implementation flow is:

`packet implementation → narrow deterministic verification → checkpoint → next packet`

After integration:

`full deterministic verification → one final semantic review`

No semantic/code review occurs after every packet.

### PD-011 — Optional delegation

Delegation may be used only when it reduces net work or context.

Correctness must not depend on it.

### PD-012 — Knowledge routing

Forge supports a generic optional knowledge-provider contract.

Brain may supply OKF through its adapter.

Only applicable leaf knowledge should be loaded where possible.

### PD-013 — Approval gates cannot be bypassed

Full-workflow intent authorizes orchestration, not future artifact approval.

For workflows requiring both functional and technical approval, enforce:

`Discovery/Clarification → Specification → Spec approval → Planning → Plan approval → Implementation`

No source-code or implementation-artifact mutation is permitted before the
implementation gate is open.

### PD-014 — Approval must precede dependent work

Approval is prospective. A gate approval obtained after dependent code changes
does not retroactively authorize those changes.

### PD-015 — Adapter-defined approver policy

The portable core enforces gate state. A Brain/project adapter may additionally
define the designated approver or approval policy. The core/adapter must reject
self-approval, stale approval, approval from an unauthorized actor, and approval
inferred from an earlier "implement" request.

---

## 5. Architecture / Mechanism

### 5.1 Directory structure

```text
plugin/
├── shared/
│   └── forge/
│       ├── references/
│       │   ├── workflow-contract.md
│       │   ├── issue-source-contract.md
│       │   ├── knowledge-provider-contract.md
│       │   └── brain-adapter-contract.md
│       ├── scripts/
│       │   └── workflow_state.py
│       ├── tests/
│       │   ├── __init__.py
│       │   ├── test_workflow_state.py
│       │   └── test_run_static_evals.py
│       └── evals/
│           ├── execution.json
│           ├── run_static_evals.py
│           └── fixtures/
└── skills/
    ├── forge-clarify/
    ├── forge-discover/
    ├── forge-spec/
    ├── forge-plan/
    └── forge-implement/
```

Each Forge Skill contains:

```text
SKILL.md
references/           # only when stage-specific detail needs progressive disclosure
evals/
├── trigger.json
└── execution.json
```

### 5.2 Artifact contract

Shared workflow semantics cover:

- `context.md`
- `decisions.md`
- `spec.md`
- optional `design.md`
- `plan.md`
- `tasks.md`
- `evidence.md`
- machine-readable workflow state

Each stage owns its output artifact and shared workflow-state changes.

Approved upstream artifacts are consumed as authoritative inputs and are not silently rewritten by downstream stages.

A downstream stage may enter only when every required upstream artifact is both
present and validly approved for the exact revision being consumed. Full-workflow
intent does not satisfy an artifact gate.

### 5.3 Deterministic core

`workflow_state.py` owns deterministic operations only.

Required public behaviour:

- content normalization for approval
- content hashing
- retry eligibility
- dependency blocking
- resume-point calculation
- check-result recording

It must:

- use Python 3.8+ standard library only
- consume JSON-compatible values
- have no host API dependency
- have no Brain-specific type dependency

### 5.4 Eval model

Use two complementary seams.

**Deterministic seam**

Covers exact state/format behaviour such as:

- approval normalization
- hashes
- workflow transitions
- retry accounting
- dependency blocking
- resume
- adapter parity fixtures
- eval/package structure

**Skill behavioural seam**

Uses the existing version-1 eval schema to test observable stage behaviour.

Do not assert hidden reasoning or exact prose wording.

---

## 6. Workhorse Execution Contract

The implementer must follow these rules.

1. Execute tasks in dependency order.
2. Before any source-code mutation, verify that the exact Specification revision
   and exact Plan revision required by the workflow are validly approved.
3. Treat this plan and the approved Specification as authoritative.
4. Never treat a full-workflow prompt, "implement" wording, or earlier generic
   continuation intent as approval of an artifact produced later.
5. If a required gate is closed, stop before mutation and request the required
   approval.
6. Do not redesign architecture during implementation.
7. Do not perform new research unless concrete repository evidence proves this plan stale or contradictory.
8. Read only the current task's listed context plus cited local references needed for that task.
9. Do not perform unrelated cleanup or refactoring.
10. Do not modify files outside the task's write scope.
11. Preserve pre-existing unrelated working-tree changes.
12. Run the task's narrow deterministic verification before moving on.
13. Do not perform semantic/code review after each task.
14. Checkpoint/commit only when authorized by the chosen Git mode.
15. Do not revisit completed tasks without concrete failure or contradiction evidence.
16. Surface plan/reality contradictions instead of inventing replacement design.
17. Record unavailable required checks as `UNMEASURED`.
18. Finish implementation and integrated deterministic verification before the final semantic review.

### Git / checkpoint rule

Before Task 1, use the caller's authorized commit mode.

If no commit mode has been authorized, leave changes uncommitted and use workflow checkpoints only.

Never include pre-existing or out-of-scope changes in a Forge-created commit.

---

# 7. Detailed Implementation Tasks

---

## Task 1 — Allow Additional Portable Skills in Packaging

### Objective

Allow the plugin to contain the five Forge Skills while preserving the existing three required Skills and existing validation guarantees.

### Requirements

- FR-005
- INV-011
- CON-001
- CON-007
- CON-008

### Dependencies

None.

### Write Scope

Modify only:

- `packaging/test_validate_plugin.py`
- `packaging/validate_plugin.py`
- `packaging/build_plugin.py` only if current build behaviour requires adjustment

### Read / Reference Context

Inspect:

- current Skill discovery logic
- current exact-Skill-count/equality assumptions
- current folder/frontmatter validation
- current plugin copy/build behaviour

### Canonical Existing Behaviour to Preserve

The three existing required Skills remain mandatory:

- `merge-sentinel`
- `skill-engineer`
- `skill-prospector`

Additional valid immediate children under `plugin/skills/` are allowed.

### Implementation

1. Add a failing test proving the baseline Skills cannot disappear.
2. Add a failing test proving one additional valid Skill package can be discovered.
3. Change discovery so it can be exercised against an injected `skills_dir`.
4. Replace exact-set equality with a required-baseline subset check for the canonical plugin directory.
5. Preserve existing rejection of:
   - missing `SKILL.md`
   - duplicate Skill names
   - folder/frontmatter mismatches
6. Confirm `plugin/shared/forge/` is not discoverable because it is outside `plugin/skills/`.
7. Keep `build_plugin.py` copying the complete `plugin/` payload unless current code proves a change is required.

### Must Not Change

- Do not weaken validation for malformed Skills.
- Do not make existing required Skills optional.
- Do not move shared Forge resources under `plugin/skills/`.
- Do not introduce Forge-specific hardcoded Skill counting.
- Do not change unrelated packaging behaviour.

### Narrow Verification

Run:

```bash
python -m unittest packaging.test_validate_plugin.CanonicalPluginLayoutTests -v
```

Expected:

- existing baseline Skill assertions pass
- additional valid Skill discovery passes
- malformed Skill validation continues to fail in existing negative tests

### Acceptance

Task is complete when:

- the existing three Skills remain required
- additional valid Skills are accepted
- discovery is testable against an isolated temporary directory
- shared Forge resources cannot be discovered as Skills
- focused packaging tests pass

### Checkpoint

Suggested message if commits are authorized:

`refactor(packaging): allow additional portable skills`

---

## Task 2 — Implement Deterministic Workflow State

### Objective

Create the host-neutral deterministic state utility used by all Forge stages.

### Requirements

- FR-029 to FR-032
- FR-048 to FR-057
- FR-069 to FR-075
- INV-004 to INV-007
- NFR-003
- NFR-004

### Dependencies

Task 1 only if repository validation requires the new shared tree to exist during tests. Otherwise logically independent.

### Write Scope

Create:

- `plugin/shared/forge/scripts/workflow_state.py`
- `plugin/shared/forge/tests/__init__.py`
- `plugin/shared/forge/tests/test_workflow_state.py`

### Interface Contract

Expose deterministic functions equivalent to:

```text
normalize_markdown(text) -> normalized text
content_hash(text) -> stable hash
can_retry(failure, attempts, changed_inputs) -> bool
block_dependants(tasks, blocked_id) -> set of blocked IDs
resume_point(state, observed_hashes) -> stage/task ID or None
record_check(state, check_id, status, reason=None) -> updated state
can_enter_stage(state, target_stage, approval_policy=None) -> decision
```

Function names may vary only if all local callers/tests use one consistent interface.

### Implementation Decisions

Use:

- `hashlib.sha256`
- `json`
- standard-library collections/utilities only

Approval normalization must:

- normalize line endings to LF
- ignore trailing spaces/tabs outside fenced code
- collapse repeated blank-line runs outside fenced code
- preserve leading whitespace
- preserve non-trailing inline whitespace
- preserve fenced-code content except line-ending normalization

Check recording must:

- accept only `PASS`, `FAIL`, `UNMEASURED`
- set `passed=true` only for `PASS`
- require a reason for `UNMEASURED`

Retry logic must:

- bound transient retries according to the approved Forge contract
- refuse another deterministic retry unless a relevant input/state changed

Dependency blocking must:

- include the directly blocked task
- include transitive dependants
- preserve unrelated independent tasks

Resume logic must:

- verify observed artifact/repository hashes
- resume from the first incomplete or stale point
- not trust persisted state without verification

Stage-entry logic must:

- require the approved Specification revision before Planning when that gate applies
- require the approved Plan revision before Implementation
- validate approval against the exact current artifact hash/revision
- validate adapter-defined approver policy when configured
- reject approval inferred from full-workflow or "implement" intent
- reject stale or post-hoc approval as authorization for prior mutation
- return a non-mutating blocked/gate-required result when prerequisites are absent

### Must Not Change

- No host APIs.
- No Jira/OKF/Brain-specific imports.
- No third-party runtime dependency.
- Do not encode semantic review logic here.
- Do not execute repository commands from this module.

### Narrow Verification

Run:

```bash
python -m unittest plugin.shared.forge.tests.test_workflow_state -v
```

Required cases:

- equivalent Markdown formatting produces the same approval hash
- meaningful indentation or inline whitespace changes invalidate the hash
- fenced-code whitespace remains significant
- `UNMEASURED` never counts as pass
- deterministic retry requires a relevant change
- dependency blocking is transitive
- independent tasks remain unblocked
- stale observed state changes the resume point
- Planning entry is rejected for an unapproved Specification
- Implementation entry is rejected for a missing/unapproved Plan
- full-workflow intent does not satisfy either gate
- wrong/designated-approver mismatch leaves the gate closed
- material artifact change invalidates downstream gate state

Expected: all tests pass.

### Acceptance

Task is complete when all deterministic state behaviours above are covered by unit tests and the module remains host-neutral and standard-library-only.

### Checkpoint

Suggested message if authorized:

`feat(forge): add deterministic workflow state`

---

## Task 3 — Define Shared Portable Contracts and Cross-Stage Fixtures

### Objective

Create the shared portable contracts so stage Skills can reference one source of truth instead of duplicating workflow rules.

### Requirements

- FR-001 to FR-005
- FR-013 to FR-018
- FR-047
- FR-055 to FR-062
- INV-001 to INV-003
- SEC-001 to SEC-006
- CON-002 to CON-006

### Dependencies

- Task 2 for deterministic state terminology and approval/resume semantics.

### Write Scope

Create:

- `plugin/shared/forge/references/workflow-contract.md`
- `plugin/shared/forge/references/issue-source-contract.md`
- `plugin/shared/forge/references/knowledge-provider-contract.md`
- `plugin/shared/forge/references/brain-adapter-contract.md`
- `plugin/shared/forge/evals/execution.json`
- `plugin/shared/forge/evals/fixtures/brain-adapter/input.json`
- `plugin/shared/forge/evals/fixtures/brain-adapter/expected.json`

Additional fixture files may be created only under:

`plugin/shared/forge/evals/fixtures/`

when required by the existing eval schema.

### Contracts to Freeze

#### `workflow-contract.md`

Define:

- stage boundaries
- stage continuation rules
- ordered stage prerequisites
- read-only vs mutation-capable stage boundaries
- artifact ownership
- approval semantics
- designated-approver/policy semantics when supplied by an adapter
- stale approval handling
- source freshness
- `PASS` / `FAIL` / `UNMEASURED`
- resume
- retry
- contradiction propagation
- scope authorization
- pre-existing change isolation
- no silent delivery mutations
- no source-code mutation before the implementation gate
- no post-hoc approval
- no approval inference from full-workflow intent

Use a concise state model that makes artifact gates explicit:

```text
discover/clarify complete
  -> spec active
  -> spec awaiting-approval
  -> spec approved
  -> plan active
  -> plan awaiting-approval
  -> plan approved
  -> implementation active

any required gate missing/stale/unauthorized
  -> blocked-at-gate (read-only for source/implementation artifacts)

approved artifact materially changes
  -> approval stale
  -> downstream dependent gates invalid
```

Do not allow a direct transition from Discovery/Specification draft to
Implementation.

#### `issue-source-contract.md`

Define a host-neutral result containing the semantics of:

- current fields
- sources/provenance
- unavailable sources
- relationships
- requirement-changing history
- freshness

Raw source payloads must not be persisted by default unless materially used.

#### `knowledge-provider-contract.md`

Define:

- selected knowledge references
- hashes/freshness
- selection reason
- unavailable knowledge
- validation result

Keep transport/provider implementation optional.

#### `brain-adapter-contract.md`

Brain adapter supplies:

- issue source
- OKF provider
- artifact-location conventions
- project validators
- authorized delivery operations
- optional designated approver / approval-policy metadata

It must not override Forge workflow semantics or weaken Forge approval gates.

### Eval Cases

Add shared cases equivalent to:

- stage-only stop
- full-workflow continuation
- approval invalidation
- idempotent resume
- inaccessible issue evidence
- historical conflict handling
- unavailable-check evidence
- Brain adapter parity
- full-workflow prompt stops at Spec approval gate
- approved Spec allows Planning but not Implementation
- unapproved Plan blocks Implementation
- designated approver mismatch blocks the gate
- post-hoc approval does not validate prior mutation

Use the existing version-1 eval schema.

Do not place executable shell commands in eval case data.

### Brain Fixture

Fixture input must cover:

- populated custom fields
- paginated comments
- historical requirement conflict
- OKF leaf paths
- a pre-existing BA answer
- an unauthorized delivery request
- a full-workflow request equivalent to `Implement BR-21861 using Agentic SDLC`
- designated functional and technical approver policy

Expected behaviour must prove:

- BA answer reuse
- confirmation only for the genuine historical conflict
- leaf-only OKF loading
- Brain artifact convention preservation
- unauthorized delivery refusal
- no source-code mutation while Spec approval is pending
- Planning begins only after valid Spec approval
- no source-code mutation while Plan approval is pending
- Implementation begins only after valid Plan approval
- unauthorized/self/post-hoc approval does not open a gate

### Must Not Change

- Do not duplicate stage-specific workflow prose in multiple contracts.
- Do not make transport bindings mandatory.
- Do not make OKF/Jira mandatory.
- Do not encode host invocation syntax.
- Do not copy raw all-field payloads into active context by default.

### Narrow Verification

Run:

```bash
python plugin/skills/skill-engineer/scripts/validate_evals.py plugin/shared/forge/evals --json
```

Expected:

- exit 0
- no schema errors
- no broken fixture references

### Acceptance

Task is complete when all later Forge Skills can reference the shared contracts without needing to duplicate portable workflow semantics.

### Checkpoint

Suggested message if authorized:

`docs(forge): define shared workflow contracts`

---

## Task 4 — Implement `forge-clarify`

### Objective

Create the user-invoked clarification stage that owns genuine unresolved human decisions and suppresses questions already answered by evidence.

### Requirements

- FR-001 to FR-013
- INV-003
- INV-004
- NFR-002
- NFR-006
- NFR-007
- AC-001
- AC-003
- AC-004

### Dependencies

- Task 3

### Write Scope

Create:

- `plugin/skills/forge-clarify/SKILL.md`
- `plugin/skills/forge-clarify/references/decision-frontier.md`
- `plugin/skills/forge-clarify/evals/trigger.json`
- `plugin/skills/forge-clarify/evals/execution.json`

### Skill Behaviour

`forge-clarify` must:

1. activate only on explicit stage intent or authorized full-workflow continuation
2. inspect available current evidence before asking
3. suppress materially equivalent answered questions
4. research evidence-answerable questions instead of asking the user
5. reopen settled decisions only for contradiction, staleness, or scope change
6. group independent ready questions into one round
7. write approved decisions to `decisions.md`
8. bind approval through shared workflow semantics
9. stop after the stage unless continuation is already authorized

### Trigger Coverage

Include:

- positive explicit invocation
- paraphrase
- boundary cases
- negative generic question
- competing Skill request
- implementation request
- full-workflow entry case

### Execution Coverage

Prove:

- answered-question suppression
- grouped independent frontier
- evidence-answerable research
- stale/conflicting decision reopening
- natural-language approval
- no silent reopening of settled decisions

### Must Not Change

- Do not perform broad Discovery.
- Do not ask questions already answerable from current evidence.
- Do not choose technical architecture.
- Do not continue automatically without authorized workflow intent.
- Do not reproduce shared workflow rules inline.

### Narrow Verification

Run:

```bash
python plugin/skills/skill-engineer/scripts/validate_evals.py plugin/skills/forge-clarify/evals --json
python plugin/skills/skill-engineer/scripts/inspect_skill.py plugin/skills/forge-clarify
```

Expected:

- eval validation passes
- inspector passes
- no broken references
- no platform-specific frontmatter
- no hardcoded personal paths

### Acceptance

A user can explicitly invoke clarification, receive only genuine unresolved human decisions, approve them, and stop at the boundary without duplicate questions.

### Checkpoint

Suggested message if authorized:

`feat(forge): add clarification stage`

---

## Task 5 — Implement `forge-discover`

### Objective

Create the evidence and functional-impact stage that establishes verified current behaviour and affected surfaces without owning human decisions.

### Requirements

- FR-001 to FR-005
- FR-007 to FR-022
- INV-003
- INV-004
- NFR-002
- NFR-006
- NFR-007
- AC-001 to AC-005

### Dependencies

- Task 3
- Task 4 only for full-workflow behaviour that routes unresolved decision frontiers to Clarify

### Write Scope

Create:

- `plugin/skills/forge-discover/SKILL.md`
- `plugin/skills/forge-discover/references/impact-coverage.md`
- `plugin/skills/forge-discover/evals/trigger.json`
- `plugin/skills/forge-discover/evals/execution.json`

### Skill Behaviour

Discovery must:

1. consume approved decisions and available issue/source evidence
2. establish current behaviour and repository/product context
3. cover relevant actors, states, parallel paths, exclusions, unassigned cohorts, permissions, integrations, and regressions
4. consider materially populated accessible issue fields
5. follow materially relevant comments, attachments, linked items, subtasks, parents, dependencies, and requirement-changing history
6. explicitly record inaccessible evidence and impact
7. treat historical conflict as supporting evidence requiring clarification when material
8. check missing screenshots/visual references only for relevant UI work
9. treat missing visual references as warnings unless they genuinely block correctness
10. produce `context.md`
11. route real unresolved human decisions to Clarify instead of asking directly

### Must Not Change

- Do not become an interview stage.
- Do not silently treat inaccessible data as empty.
- Do not persist raw all-field payloads by default.
- Do not load irrelevant visual/reference material.
- Do not choose implementation architecture.

### Narrow Verification

Run:

```bash
python plugin/skills/skill-engineer/scripts/validate_evals.py plugin/skills/forge-discover/evals --json
python plugin/skills/skill-engineer/scripts/inspect_skill.py plugin/skills/forge-discover
```

Expected: both pass.

### Acceptance

Discovery produces a verified, bounded `context.md` that contains enough evidence for Specification without repeating already settled user questions.

### Checkpoint

Suggested message if authorized:

`feat(forge): add discovery stage`

---

## Task 6 — Implement `forge-spec`

### Objective

Create the Specification stage that converts approved Discovery inputs into a testable behavioural contract without implementation design leakage.

### Requirements

- FR-023 to FR-032
- INV-004
- INV-008
- AC-006
- AC-007

### Dependencies

- Task 3
- Task 5

### Write Scope

Create:

- `plugin/skills/forge-spec/SKILL.md`
- `plugin/skills/forge-spec/references/behavioral-contract.md`
- `plugin/skills/forge-spec/evals/trigger.json`
- `plugin/skills/forge-spec/evals/execution.json`

### Inputs

Consume:

- approved `context.md`
- approved `decisions.md`

### Output

Produce:

- `spec.md`
- stable requirement identities
- `awaiting-approval` state after a new/revised Specification is presented
- approved state only after valid approval is received through the shared workflow contract

Creating the Specification does not itself approve it.

### Required Specification Coverage

Where relevant, the Skill must cover:

- goal / intent
- scope / non-goals
- actors
- scenarios
- functional requirements
- invariants
- data/state semantics
- edge/failure behaviour
- NFRs
- security/safety
- external contracts
- existing vs expected behaviour
- binding constraints
- acceptance scenarios
- success criteria
- traceability

### Readiness Rule

The Specification is not ready when:

- a material product/behavioural decision remains unresolved
- a requirement is not testable
- important changed/unchanged behaviour is ambiguous
- non-binding technical implementation design has leaked into the contract

Material unresolved human decisions route back to Discovery/Clarify.

When the Specification is ready, `forge-spec` must stop at the approval gate
unless a valid approval for that exact revision already exists. Full-workflow
intent does not bypass this gate.

### Must Not Change

- Do not reopen settled Discovery decisions without contradictory evidence.
- Do not choose implementation architecture.
- Do not decide file paths/classes/functions unless already a binding upstream constraint.
- Do not interview the user directly.

### Narrow Verification

Run:

```bash
python plugin/skills/skill-engineer/scripts/validate_evals.py plugin/skills/forge-spec/evals --json
python plugin/skills/skill-engineer/scripts/inspect_skill.py plugin/skills/forge-spec
```

Execution evals must prove:

- behavioural completeness
- stable requirement IDs
- changed/unchanged behaviour
- invariants
- edge cases
- constraints
- acceptance scenarios
- traceability
- unresolved-decision rejection
- technical-design leakage rejection

Expected: both commands pass.

### Acceptance

`forge-spec` can turn approved Discovery artifacts into an implementation-independent, plan-ready behavioural contract.

### Checkpoint

Suggested message if authorized:

`feat(forge): add specification stage`

---

## Task 7 — Implement `forge-plan`

### Objective

Create the Planning stage that converts an approved Specification into dependency-ordered, closed execution packets with all material technical decisions resolved before implementation.

### Requirements

- FR-033 to FR-037
- FR-069 to FR-075
- INV-008
- INV-009
- INV-012
- AC-008
- AC-019

### Dependencies

- Task 3
- Task 6

### Write Scope

Create:

- `plugin/skills/forge-plan/SKILL.md`
- `plugin/skills/forge-plan/references/execution-packet.md`
- `plugin/skills/forge-plan/evals/trigger.json`
- `plugin/skills/forge-plan/evals/execution.json`

### Inputs

Consume:

- validly approved `spec.md` revision; if approval is missing/stale/unauthorized,
  do not start Planning
- relevant Discovery `context.md`
- relevant Discovery `decisions.md`
- repository evidence
- applicable repository/project rules
- optional approved `design.md`

### Outputs

Produce:

- `plan.md`
- dependency-indexed `tasks.md`
- `awaiting-approval` state for the completed Plan revision
- approved Plan state only after valid technical/Plan approval

Planning may complete automatically in a full-workflow request, but Implementation
must remain blocked until the Plan approval gate is satisfied.

### Planning Behaviour

The Skill must:

1. preserve stable upstream IDs
2. reuse Discovery before broad rediscovery
3. perform planning-owned technical research when needed
4. resolve implementation architecture, reuse choices, meaningful alternatives, interfaces, compatibility/migration, and security mechanisms
5. discover exact create/modify/delete/move targets, symbols, rules, canonical examples, callers/contracts, tests/build/package/config
6. map every requirement/invariant to implementation or explicit no-change/protection
7. order packets by real dependency
8. make each packet self-contained for a workhorse
9. avoid meaningless micro-steps
10. freeze conclusions rather than passing research tasks to implementation
11. perform a readiness pass before approval
12. present the completed Plan for technical/Plan approval
13. stop before implementation unless valid approval for that exact Plan revision exists

### Closed Execution Packet Format

Each generated task must use this readable structure:

```text
Task N — <outcome>

Objective
Requirements
Dependencies
Write Scope
Read / Reference Context
Implementation
Must Not Change
Narrow Verification
Acceptance
Checkpoint
```

Use additional sections only when they remove real ambiguity.

### Packet Readiness

Reject a packet if the workhorse would still need to:

- research technical facts
- select architecture
- choose among meaningful implementation alternatives
- find the change surface
- ask the user a product question
- reinterpret an upstream requirement

### Planning Readiness Review

Before presenting the plan for approval, check at least:

- Specification coverage
- invariant protection
- exact change surface
- dependency order
- hidden technical choices
- packet scope
- narrow verification
- observable acceptance
- token/context duplication
- unresolved research
- contradictions between packets

Repair planning defects before approval.

### Must Not Change

- Do not interview the user for technical questions that Planning can research.
- Do not silently invent product behaviour.
- Do not copy large raw research into packets.
- Do not hardcode delegation as mandatory.
- Do not mandate semantic review per task.
- Do not require full implementation code inside the plan unless needed to freeze a meaningful decision.

### Narrow Verification

Run:

```bash
python plugin/skills/skill-engineer/scripts/validate_evals.py plugin/skills/forge-plan/evals --json
python plugin/skills/skill-engineer/scripts/inspect_skill.py plugin/skills/forge-plan
```

Planning evals must include:

**Small fixture**

Prove a concise packet is enough when the change is simple.

**Multi-system fixture**

Prove:

- exact files/symbols
- interfaces
- dependencies
- ordered steps
- meaningful technical decisions
- must-not-change boundaries
- exact checks/results
- acceptance evidence
- optional-design threshold
- ADR threshold
- no workhorse research
- no unresolved architecture choice
- unapproved Specification prevents Planning
- full-workflow intent does not count as Spec approval
- completed Plan remains non-mutating while technical approval is pending

Expected: both commands pass.

### Acceptance

A competent workhorse can execute every ready packet using the packet and cited local context without new research, architecture selection, or user questions.

### Checkpoint

Suggested message if authorized:

`feat(forge): add planning stage`

---

## Task 8 — Implement `forge-implement`

### Objective

Create the implementation stage that executes approved packets safely, runs applicable narrow checks, controls scope/Git behaviour, verifies integration, and produces compact final evidence.

### Requirements

- FR-038 to FR-057
- FR-069 to FR-075
- INV-005 to INV-007
- INV-010
- INV-012
- AC-009 to AC-017
- AC-020 to AC-022

### Dependencies

- Task 2
- Task 3
- Task 7

### Write Scope

Create:

- `plugin/skills/forge-implement/SKILL.md`
- `plugin/skills/forge-implement/references/commit-modes.md`
- `plugin/skills/forge-implement/references/quality-routing.md`
- `plugin/skills/forge-implement/references/failure-recovery.md`
- `plugin/skills/forge-implement/evals/trigger.json`
- `plugin/skills/forge-implement/evals/execution.json`

### Inputs / Hard Preconditions

Before any source-code or implementation-artifact write, require:

- the exact current `spec.md` revision to have valid required approval
- the exact current `plan.md` revision to have valid required technical/Plan approval
- `tasks.md` to correspond to that approved Plan revision
- adapter-defined approver policy to be satisfied when configured
- neither approval to be stale

Then consume:

- approved `plan.md`
- `tasks.md`
- optional approved `design.md`
- workflow state
- repository evidence

If any hard precondition fails, `forge-implement` must stop before mutation and
report the closed gate. It must not "implement first, approve later."

### Outputs

Produce:

- scoped repository changes
- packet/check state
- authorized commits/checkpoints only
- integrated deterministic verification results
- one semantic-review result
- bounded remediation results
- compact `evidence.md`

### Implementation Behaviour

`SKILL.md` must:

1. verify Specification and Plan gate state before any implementation write
2. verify designated approver/policy when supplied by the adapter
3. reject full-workflow intent as substitute approval
4. reject stale, unauthorized, self, or post-hoc approval
5. select/confirm commit mode once when required
6. capture the pre-existing working-tree scope
7. execute dependency-ready packets
8. read only current-packet context unless concrete evidence requires expansion
9. run only quality guidance applicable to touched concerns
10. record every check as `PASS`, `FAIL`, or `UNMEASURED`
11. stop affected/dependent work on plan contradiction
12. allow safe independent work to continue
13. request authorization for unplanned required scope
14. keep unrelated failures separate
15. perform integrated deterministic verification after all packets
16. perform exactly one final semantic review
17. remediate only bounded findings from that final review
18. produce compact handoff evidence

### Reference Responsibilities

#### `commit-modes.md`

Define exact behaviour for:

- review-first
- per-task
- end-only
- failed-work exclusion
- dirty-tree isolation
- resume deduplication
- no automatic push/squash/PR/merge

#### `quality-routing.md`

Route quality checks by touched concern.

Cover, where applicable:

- design parity
- reusable component/style reuse
- inline styling
- duplication
- constants
- performance
- maintainability
- security
- permissions
- unintended diff scope

Do not load all quality guidance for every packet.

#### `failure-recovery.md`

Define:

- current-task verification failure
- unrelated pre-existing failure
- transient retry
- deterministic retry gating
- plan/reality contradiction
- dependency blocking
- independent continuation
- unplanned scope authorization
- unavailable verification
- resume

### Must Not Change

- Do not modify source code before both required artifact gates are valid.
- Do not treat "Implement ... using Agentic SDLC" as pre-approval.
- Do not request approval only after code changes are already made.
- Do not accept unauthorized/self/post-hoc approval as satisfying a configured gate.
- Do not modify pre-existing unrelated work.
- Do not silently add scope.
- Do not retry deterministic failure without relevant state change.
- Do not perform semantic review after every task.
- Do not make delegation mandatory.
- Do not count `UNMEASURED` as pass.
- Do not commit failed/blocked work.
- Do not push/open PR/merge without explicit authorization.

### Narrow Verification

Run:

```bash
python plugin/skills/skill-engineer/scripts/validate_evals.py plugin/skills/forge-implement/evals --json
python plugin/skills/skill-engineer/scripts/inspect_skill.py plugin/skills/forge-implement
```

Execution evals must cover:

- full-workflow prompt with unapproved Spec produces zero source-code writes
- approved Spec + missing Plan produces zero source-code writes
- approved Spec + unapproved Plan produces zero source-code writes
- designated approver mismatch leaves implementation blocked
- approval after a simulated prior mutation is reported as a gate violation, not retroactive success
- all three commit modes
- dirty-tree isolation
- idempotent resume
- failed-work exclusion
- quality routing
- contradiction + transitive blocking
- independent continuation
- bounded transient retry
- deterministic retry rejection
- unplanned scope approval/rejection
- unavailable checks
- final integrated verification
- exactly one semantic review
- bounded remediation

Expected: both commands pass.

### Acceptance

An approved Forge plan can be executed packet-by-packet without replanning, unrelated mutation, repeated semantic review, or dishonest verification reporting.

### Checkpoint

Suggested message if authorized:

`feat(forge): add implementation stage`

---

## Task 9 — Add Deterministic Cross-Stage Evaluation Runner

### Objective

Add a trusted deterministic runner for portable cross-stage cases without executing commands embedded in eval data.

### Requirements

- FR-063 to FR-068
- NFR-003
- NFR-006
- SC-003 to SC-009

### Dependencies

- Task 2
- Task 3
- Tasks 4 to 8 for complete stage corpus coverage

### Write Scope

Create:

- `plugin/shared/forge/evals/run_static_evals.py`
- `plugin/shared/forge/tests/test_run_static_evals.py`

Modify:

- `packaging/test_validate_plugin.py`

### Runner Contract

Input:

- shared Forge eval directory
- per-stage Forge eval directories
- declared available capabilities

Output JSON equivalent to:

```text
summary
results
  - passed
  - failed
  - skipped
  - unmeasured
  - failure classification
```

### Allowed Deterministic Validator Kinds

Support only named trusted validators needed by the approved corpus, including:

- `file-exists`
- `artifact-shape`
- `workflow-transition`
- `normalization`
- `adapter-parity`

Add another kind only if a planned case requires deterministic behaviour that cannot be represented by these existing kinds.

### Security Rules

Reject:

- executable `command` content
- unknown validator kinds
- fixture paths escaping the eval root
- missing fixture references
- malformed result shapes
- failed results without required failure classification

Model/host-required cases that cannot run must be:

- skipped with an explicit reason, or
- `UNMEASURED`

Never treat them as passed.

### Repository Validation Integration

Extend package tests so:

- every Forge eval directory passes the existing eval validator
- deterministic shared cases pass the new static runner
- each Forge Skill has required trigger categories
- missing capabilities cannot produce false passes
- cross-stage gate fixtures prove no implementation writes occur before Spec and Plan approvals
- Brain-adapter fixtures enforce designated approver policy

### Must Not Change

- Do not execute arbitrary commands from eval case data.
- Do not replace the existing version-1 eval validator.
- Do not create a competing general-purpose eval framework.
- Do not report missing host/model capability as success.

### Narrow Verification

Run:

```bash
python -m unittest plugin.shared.forge.tests.test_run_static_evals -v
python -m unittest plugin.shared.forge.tests -v
python plugin/shared/forge/evals/run_static_evals.py --json
python -m unittest packaging.test_validate_plugin -v
```

Expected:

- all deterministic unit tests pass
- static eval runner exits successfully for valid deterministic cases
- unavailable host/model cases are not counted as passes
- repository packaging tests pass

### Acceptance

Forge has a portable deterministic cross-stage regression seam that is safe to run and cannot execute commands supplied by eval data.

### Checkpoint

Suggested message if authorized:

`test(forge): add portable cross-stage regressions`

---

## Task 10 — Update Product Metadata and Installation Documentation

### Objective

Expose the expanded eight-Skill plugin consistently in manifests, README, and installation verification.

### Requirements

- NFR-001
- NFR-005
- CON-001 to CON-003
- CON-007
- SC-001
- SC-008
- SC-009

### Dependencies

- Tasks 4 to 9

### Write Scope

Modify:

- `README.md`
- `plugin/plugin.json`
- `plugin/.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `docs/install/verify-installation.md`

### Implementation

1. Add one concise README entry for each Forge stage.
2. Explain the shared portable core without presenting it as a user-facing Skill.
3. Update manifest descriptions consistently.
4. Update version metadata consistently according to the repository's existing versioning convention.
5. Update installation verification to enumerate all eight user-facing Skills:
   - 3 existing
   - 5 Forge
6. State explicitly:
   - portable deterministic/static coverage belongs to this repository
   - external Brain runtime parity remains unmeasured until run in the owning Brain repository
   - host/model trials remain separate and unmeasured until executed

### Must Not Change

- Do not claim Brain runtime parity has passed.
- Do not claim unavailable host/model trials have passed.
- Do not describe shared Forge resources as a sixth Forge Skill.
- Do not alter unrelated documentation.

### Narrow Verification

Run:

```bash
python -m unittest packaging.test_validate_plugin.CanonicalPluginLayoutTests -v
```

Expected: pass.

### Acceptance

README, manifests, marketplace metadata, and installation verification describe the same eight-Skill payload and do not overclaim external coverage.

### Checkpoint

Suggested message if authorized:

`docs(forge): publish portable SDLC suite`

---

# 8. Full Deterministic Verification

Run after all implementation tasks are complete.

## PASS REQUIRED

```bash
python packaging/validate_plugin.py
python -m unittest discover -s packaging -p "test_*.py" -v
python -m unittest plugin.shared.forge.tests -v
python plugin/shared/forge/evals/run_static_evals.py --json
python plugin/skills/skill-engineer/evals/run_static_evals.py
python plugin/skills/skill-prospector/evals/run_static_evals.py
python plugin/skills/merge-sentinel/evals/validate_corpus.py
git diff --check
```

Also inspect every Forge Skill:

```bash
python plugin/skills/skill-engineer/scripts/inspect_skill.py plugin/skills/forge-clarify
python plugin/skills/skill-engineer/scripts/inspect_skill.py plugin/skills/forge-discover
python plugin/skills/skill-engineer/scripts/inspect_skill.py plugin/skills/forge-spec
python plugin/skills/skill-engineer/scripts/inspect_skill.py plugin/skills/forge-plan
python plugin/skills/skill-engineer/scripts/inspect_skill.py plugin/skills/forge-implement
```

Validate every Forge eval directory with the existing eval validator.

## DIFF / SCOPE CHECK

Run:

```bash
git status --short
git diff --stat
git diff --check
```

If an agreed baseline revision exists, also compare against it.

Expected changed scope:

- approved Forge spec/plan artifacts if they are intentionally tracked
- `plugin/shared/forge/**`
- five `plugin/skills/forge-*/**`
- packaging validators/tests required by this plan
- approved manifests
- approved README/install documentation

Pre-existing unrelated/untracked files must remain untouched.

## ALLOWED SKIP

A check may be skipped only when:

- it is not applicable to the touched repository/environment, and
- that reason is recorded

## UNAVAILABLE / UNMEASURED

Record as `UNMEASURED`, never PASS:

- unavailable host-specific trials
- unavailable model trials
- Brain runtime/adapter parity in repositories not available here
- any required platform check that cannot run in the current environment

---

# 9. Final Review Handoff

Produce a compact handoff containing only:

- Specification reference
- Plan reference
- baseline revision, if known
- final revision, if committed
- task checkpoints/commits
- changed artifacts
- deterministic verification commands/results
- deviations/blockers
- pre-existing failures
- `UNMEASURED` checks
- any authorized scope change

Do not include chain-of-thought or replay the full implementation session.

---

# 10. One Final Semantic Review

Run only after full deterministic verification.

Review the integrated result against the approved Specification and this Plan.

Check:

1. every requirement is implemented or explicitly accounted for
2. no requirement silently disappeared
3. scope stayed bounded
4. Brain/portable responsibilities remain separated
5. no duplicate portable workflow logic was introduced
6. cross-stage behaviour is consistent
7. approval/resume/retry/scope semantics match the plan
8. no source-code mutation occurred before required Spec and Plan approvals
9. full-workflow wording was not used as implicit approval
10. designated approver policy was preserved
11. security and mutation boundaries are preserved
12. packaging/discovery remains correct
13. tests/evals are adequate
14. host/model/Brain limitations are not overclaimed
15. token-saving/context shortcuts did not reduce correctness

If findings exist:

- produce a bounded remediation list for those findings only
- remediate
- rerun affected narrow checks
- rerun full deterministic verification when the finding can affect integration
- do not restart the complete planning/implementation cycle unless the approved architecture is invalid

---

# 11. Acceptance Criteria

The implementation is complete only when all of the following are true.

### Portable suite

- [ ] All five Forge Skills exist and pass package inspection.
- [ ] All five are explicitly user-invoked.
- [ ] Full-workflow continuation and stage-only stopping are covered.
- [ ] Portable correctness does not depend on Brain/Jira/OKF or optional harness features.

### Shared core

- [ ] Shared Forge contracts are referenced rather than duplicated.
- [ ] Deterministic approval/state/retry/blocking/resume behaviour has unit coverage.
- [ ] `PASS` / `FAIL` / `UNMEASURED` semantics are enforced.

### Clarification / Discovery

- [ ] Already answered questions are suppressed.
- [ ] Evidence-answerable questions are researched instead of asked.
- [ ] Discovery covers required functional-impact dimensions.
- [ ] Inaccessible evidence is explicit.
- [ ] Historical conflicts do not silently override current intent.

### Specification / Planning

- [ ] `forge-spec` rejects unresolved behavioural decisions.
- [ ] `forge-spec` rejects non-binding implementation design leakage.
- [ ] `forge-plan` resolves technical HOW.
- [ ] Every material requirement is mapped to work/verification.
- [ ] Generated packets are readable closed execution packets.
- [ ] Workhorse implementation requires no new research, architecture selection, or user interview.

### Approval gates

- [ ] Full-workflow intent does not pre-approve future artifacts.
- [ ] Planning cannot start from an unapproved/stale Specification when the gate applies.
- [ ] Implementation cannot start without an approved current Plan.
- [ ] Source code remains unchanged while either required gate is closed.
- [ ] Configured designated approver policy is enforced.
- [ ] Post-hoc approval cannot retroactively authorize earlier source mutation.
- [ ] Material changes to approved Spec/Plan invalidate dependent gates.

### Implementation

- [ ] Dirty-tree isolation is covered.
- [ ] All commit modes are covered.
- [ ] Failed/blocked work cannot be committed.
- [ ] Scope expansion requires authorization.
- [ ] Applicable quality checks run narrowly.
- [ ] Integrated deterministic verification precedes exactly one semantic review.
- [ ] Resume does not duplicate verified side effects.

### Evaluation / packaging

- [ ] Existing three Skills remain mandatory.
- [ ] Additional valid Skills are accepted.
- [ ] Shared Forge resources are not discoverable as Skills.
- [ ] Cross-stage deterministic runner cannot execute case-supplied commands.
- [ ] Missing capabilities cannot appear as passes.
- [ ] Full repository deterministic verification passes.

---

# 12. Requirement-to-Task Traceability

| Requirement area | Tasks |
|---|---|
| Portable canonical Skill source / packaging | 1, 3, 10 |
| Approval / workflow state / retry / resume | 2, 3, 6, 7, 8, 9 |
| Prospective Spec/Plan gates / designated approver | 2, 3, 6, 7, 8, 9 |
| Shared adapter/provider contracts | 3 |
| Clarification | 4 |
| Discovery | 5 |
| Specification | 6 |
| Planning | 7 |
| Implementation safety / quality / Git | 8 |
| Portable/static evaluation | 9 |
| Product metadata / installation docs | 10 |
| Integrated verification / final review | Sections 8–10 |

Detailed requirement IDs remain attached to each task and should be preserved in implementation evidence.

Preferred trace:

`DEC-* → FR/INV/NFR/SEC/CON → Task → Verification`

---

# 13. Assumptions, Known Deviations, and Unmeasured Items

## Known repository limitation

The Brain SDLC packages to be refactored are not present in this repository.

Therefore:

- this plan implements the Brain adapter contract
- this plan can test portable adapter fixtures
- the actual Brain repository refactor is not part of this implementation

## External Brain follow-up

After this plan lands, create a separate repository-grounded plan in the Brain Skills repository that:

1. maps each Brain clarification/discovery/specification/planning/implementation entry point to the matching Forge core
2. implements `plugin/shared/forge/references/brain-adapter-contract.md`
3. preserves Jira acquisition
4. preserves OKF routing
5. preserves Brain artifact conventions
6. preserves Brain validators and authorized delivery behaviour
7. replays relevant historical Brain fixtures
8. leaves BA unchanged
9. leaves MR Review unchanged

Until that follow-up is executed:

- Brain runtime parity = `UNMEASURED`
- Brain-vs-Forge differential runtime results = `UNMEASURED`

## Host/model trials

Host/model trials are separate from portable correctness.

If unavailable during this implementation, record them as `UNMEASURED`.

---

# 14. Plan Readiness Gate

Do not start implementation until all items below are true.

### Upstream integrity

- [ ] Approved Specification has been consumed.
- [ ] Relevant Discovery Context/Decisions have been consumed or their absence is explicitly known.
- [ ] No settled behaviour has been silently reopened.
- [ ] No product behaviour has been invented.

### Coverage

- [ ] Every material Specification requirement is accounted for by a task or explicit protection/no-change decision.
- [ ] Invariants and constraints have verification/protection.
- [ ] No difficult requirement was dropped.

### Research / design

- [ ] Repository architecture needed by these tasks is known.
- [ ] Shared-core location is decided.
- [ ] Stage boundaries are decided.
- [ ] Deterministic utility responsibilities are decided.
- [ ] Adapter/provider contracts are decided.
- [ ] Eval strategy is decided.
- [ ] No implementation packet contains a research or architecture-selection task.

### Approval gate integrity

- [ ] Full-workflow intent is explicitly separated from artifact approval.
- [ ] Specification approval is required before Planning when configured by the workflow.
- [ ] Plan/technical approval is required before Implementation.
- [ ] Implementation has a hard read-only stop while either required gate is closed.
- [ ] Designated approver/policy enforcement is defined.
- [ ] Stale and post-hoc approvals cannot silently open gates.

### Execution

- [ ] Tasks are dependency ordered.
- [ ] Every task has bounded write scope.
- [ ] Every task has concrete implementation steps.
- [ ] Every task has `Must Not Change`.
- [ ] Every task has narrow deterministic verification.
- [ ] Every task has observable acceptance.
- [ ] Checkpoint behaviour is defined.

### Context efficiency

- [ ] Shared rules are referenced instead of duplicated.
- [ ] Stage-specific detail uses progressive disclosure.
- [ ] No task requires broad rediscovery already completed by earlier tasks.
- [ ] Delegation is optional.
- [ ] No repeated semantic review exists in the packet loop.

### Completion

- [ ] Full deterministic verification is defined.
- [ ] `UNMEASURED` cannot be mistaken for PASS.
- [ ] Final handoff is compact.
- [ ] Final semantic review occurs once after integrated verification.

### Workhorse readiness

- [ ] Implementer can execute without interviewing the user.
- [ ] Implementer can execute without external research.
- [ ] Implementer can execute without choosing architecture.
- [ ] Implementer can execute without reinterpreting requirements.
- [ ] Implementer can execute without repeatedly rediscovering the repository.

If a material user-owned requirement/decision is still missing, this plan is **not ready** and the affected branch must return to Discovery/Specification.
