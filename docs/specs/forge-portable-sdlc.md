# Forge Portable SDLC Skills — Specification

## 1. Purpose

The existing Brain SDLC skills contain useful clarification, discovery,
specification, planning, and implementation behaviour, but much of that behaviour
is coupled to Brain Payroll, Jira, OKF, project-specific tooling, and host
assumptions.

Shared workflow logic is repeated across stages, causing repeated questions,
unnecessary context loading, inconsistent functional coverage, and quality
problems that are discovered late during review instead of prevented during
implementation.

The required change is to create a portable, user-invoked SDLC suite that works
across projects and compatible harnesses while allowing Brain-specific skills to
reuse the portable behaviour through thin adapters.

The resulting workflow must remain token-efficient, evidence-driven, safe to
resume, and detailed enough that a competent workhorse can implement an approved
plan without new research, architecture decisions, or user questions.

In this specification:

- **BA** means the existing Brain Business Analysis workflow.
- **OKF** means the Brain project knowledge framework.
- **MR Review** means the existing Brain merge-request review workflow.
- **Forge** means the portable SDLC skill suite defined here.

---

## 2. Goals

The change must:

1. Provide portable clarification, discovery, specification, planning, and
   implementation stages.
2. Keep each stage explicitly user-invoked unless the user's expressed intent
   authorizes continuation into later stages.
3. Preserve Brain-specific behaviour through thin adapters rather than duplicate
   portable workflow logic.
4. Prevent repeated clarification and unnecessary context loading.
5. Preserve requirement intent and traceability across workflow stages.
6. Produce implementation plans that a competent workhorse can execute without
   rediscovery or unresolved design decisions.
7. Prevent common quality defects during implementation rather than relying only
   on final review.
8. Remain usable without depending on a particular model, harness, subagent
   system, MCP server, hook, shell, interpreter, Jira instance, or OKF bundle.
9. Support safe reruns and recovery without duplicate questions, artifacts,
   commits, or side effects.
10. Keep side effects such as issue updates, commits, pushes, PR creation, and
    unrelated repository mutation under explicit user control.

---

## 3. Scope

### 3.1 In Scope

The suite consists of five portable stages:

- `forge-clarify`
- `forge-discover`
- `forge-spec`
- `forge-plan`
- `forge-implement`

The corresponding Brain skills will be refactored to use these portable stages
while retaining Brain-specific issue-source, knowledge, validation, artifact, and
delivery behaviour.

The workflow includes:

- clarification ownership and question suppression
- evidence acquisition and impact analysis
- behavioural specification
- implementation planning
- implementation execution
- narrow validation during implementation
- integrated deterministic verification
- final semantic review
- safe resume
- scope control
- optional project knowledge integration
- portable and Brain-specific evaluation coverage

### 3.2 Out of Scope

The following are explicitly out of scope:

- changing the existing BA skill
- changing the existing MR Review skill
- creating a replacement review skill
- automatically publishing Forge artifacts to Jira or another issue tracker
- requiring OKF in projects that do not use it
- requiring a specific harness, model, subagent system, MCP server, hook, shell,
  or interpreter for core workflow correctness
- automatically fixing unrelated knowledge-bundle, repository, or baseline defects
- automatically editing `.gitignore`
- automatically squashing, pushing, opening pull requests, or merging without
  required user authorization
- treating every missing screenshot or visual sample as a blocker
- copying entire project knowledge profiles into Forge context
- moving non-binding technical implementation decisions into the behavioural
  specification
- pre-writing complete implementations inside plans when a concise contract,
  pseudocode, signature, schema, or sketch is sufficient

---

## 4. Actors

### ACT-001 — Developer

A developer invokes Forge or a Brain adapter to clarify, discover, specify, plan,
implement, resume, or verify a work item.

### ACT-002 — Product Owner / Decision Owner

A human decision owner answers genuine product or behavioural questions that
cannot be resolved from evidence.

### ACT-003 — Workhorse Implementer

A competent implementation model or agent executes approved plan packets without
performing new research, architecture selection, or requirement clarification.

### ACT-004 — Reviewer

A stronger reviewer or review stage evaluates the integrated implementation after
deterministic verification.

### ACT-005 — Brain Adapter

A Brain-specific skill supplies Brain Payroll, Jira, OKF, validation, artifact,
and delivery specialisation while delegating portable workflow behaviour to Forge.

### ACT-006 — Knowledge Provider

An optional project-specific provider supplies applicable project knowledge
without coupling Forge to a particular knowledge format.

---

## 5. Functional Requirements

### Workflow and Invocation

**FR-001 — Explicit stage invocation**  
Each Forge stage MUST be user-invoked and MUST NOT begin an SDLC workflow
unexpectedly.

**FR-002 — Intent-based continuation**  
When the user explicitly requests a full workflow, or gives an unambiguous
instruction to continue, the workflow MAY continue automatically only through
stage transitions whose prerequisites and required approvals are already
satisfied. Full-workflow intent authorizes orchestration; it does NOT pre-approve
artifacts that have not yet been produced and presented.

**FR-003 — Stage boundary control**  
When the user's intent is limited to one stage, the workflow MUST stop at that
stage boundary.

**FR-004 — Brain adapter delegation**  
A user invocation of a Brain SDLC skill MUST authorize that Brain skill to use its
matching Forge core.

**FR-005 — Portable source of truth**  
Portable workflow behaviour MUST have one canonical source and MUST NOT be
independently reimplemented in Brain adapters.

---

### Clarification and Decision Ownership

**FR-006 — Clarification ownership**  
`forge-clarify` MUST own unresolved human product or behavioural decisions.

**FR-007 — Evidence ownership**  
`forge-discover` MUST own evidence gathering, current-behaviour analysis, affected
area identification, and impact analysis.

**FR-008 — Evidence-answerable questions**  
Questions that can be answered from available authoritative evidence MUST be
researched rather than sent to the user.

**FR-009 — Question suppression**  
Forge MUST automatically reuse materially equivalent answers already available
from current issue fields, comments, BA output, approved artifacts, or current
conversation context.

**FR-010 — Relevant clarification only**  
Forge MUST raise only unanswered, conflicting, stale, or newly exposed human
decisions.

**FR-011 — Group independent questions**  
Independent clarification questions that are ready at the same time SHOULD be
grouped into one round.

**FR-012 — Stable decisions**  
A settled decision MUST NOT be reopened unless contradictory evidence, staleness,
or scope change materially affects it.

**FR-013 — Historical conflict handling**  
Requirement-changing historical content MUST be treated as supporting evidence
and MUST NOT silently override current authoritative intent. A material conflict
MUST return the affected decision to clarification.

---

### Discovery

**FR-014 — Current information coverage**  
Discovery MUST consider current issue fields and clarification replies together.

**FR-015 — Material issue field coverage**  
Where issue metadata is available, Discovery MUST consider materially populated
accessible fields rather than relying only on a fixed default field set.

**FR-016 — Related source coverage**  
Where available and materially relevant, Discovery MUST consider paginated
comments, attachments, linked items, subtasks, parent relationships,
dependencies, and requirement-changing history.

**FR-017 — Inaccessible source handling**  
An inaccessible source MUST be recorded with its potential impact and MUST NOT be
silently treated as empty or successfully checked.

**FR-018 — Minimal persistence**  
Raw issue payloads or unrelated source content SHOULD NOT be persisted or loaded
into active context unless materially needed.

**FR-019 — Functional impact coverage**  
Discovery MUST identify materially affected:

- actors
- states
- parallel paths
- exclusions
- unassigned cohorts
- permissions
- integrations
- regressions

where applicable to the work item.

**FR-020 — Visual evidence relevance**  
Missing screenshots or visual references MUST be checked only when relevant to UI
or visual work.

**FR-021 — Missing visual evidence**  
Missing visual references SHOULD be reported as warnings or risks unless the
change genuinely cannot be specified or verified without them.

**FR-022 — Existing behaviour as evidence**  
Existing system behaviour SHOULD be used as reference evidence where it is
material to preserving consistency or defining the behavioural delta.

---

### Specification

**FR-023 — Preserve Discovery decisions**  
`forge-spec` MUST consume approved Discovery context and decisions without
reopening settled decisions.

**FR-024 — Behavioural contract**  
Specification MUST define the observable required behaviour, boundaries,
constraints, unchanged behaviour, and verification expectations.

**FR-025 — Specification completeness**  
Where relevant, Specification MUST cover:

- actors
- states
- inputs
- outputs
- permissions
- errors
- boundaries
- changed behaviour
- unchanged behaviour
- invariants
- edge cases
- constraints
- acceptance scenarios
- success criteria

**FR-026 — No unresolved product decisions**  
A Specification MUST NOT be marked ready while a material product or behavioural
decision remains unresolved.

**FR-027 — No implementation-design leakage**  
Specification MUST NOT introduce non-binding implementation design or arbitrary
technical mechanisms.

**FR-028 — Requirement identity**  
Meaningful requirements MUST have stable identities that downstream stages can
preserve.

---

### Approval

**FR-029 — Natural-language approval**  
An unambiguous natural-language instruction such as "proceed" MAY approve a
clearly presented pending artifact revision.

**FR-030 — Approval binds to content**  
Approval MUST bind to the meaningful content of the approved artifact so that a
material change invalidates stale approval.

**FR-031 — Formatting-noise tolerance**  
Non-semantic formatting differences such as line-ending differences, trailing
whitespace, or repeated blank lines MUST NOT invalidate approval.

**FR-032 — Semantic-whitespace preservation**  
Whitespace that can affect meaning, including meaningful indentation and content
inside fenced code blocks, MUST remain approval-significant.

**FR-069 — Approval is prospective, not retroactive**  
A required approval MUST be obtained for the presented artifact revision before
any downstream stage or mutation that depends on that approval begins. Completing
the downstream work first and requesting approval afterwards is invalid.

**FR-070 — Full-workflow intent is not artifact approval**  
A request such as "implement this using the SDLC" MAY authorize the workflow to
orchestrate all required stages, but MUST NOT be interpreted as approval of a
Specification, Plan, design, or implementation revision that did not exist when
the request was made.

**FR-071 — Specification approval gate**  
`forge-plan` MUST NOT begin planning from a draft/unapproved Specification when
the workflow requires Specification approval. The Specification revision consumed
by Planning MUST have a valid approval bound to that revision.

**FR-072 — Plan approval gate**  
`forge-implement` MUST NOT begin source-code or implementation-artifact mutation
until an implementation Plan exists and the required technical/Plan approval is
valid for that Plan revision.

**FR-073 — No implementation mutation before gates close**  
Before all implementation prerequisites are satisfied, Forge and Brain adapters
MUST remain read-only with respect to source code and other implementation
artifacts. They MAY create/update SDLC artifacts owned by the current pre-
implementation stage.

**FR-074 — Authorized approver enforcement**  
When the workflow or adapter defines a designated approver or approval policy,
only an approval satisfying that policy counts. The agent MUST NOT self-approve,
infer approval from earlier workflow intent, or substitute a different approver.

**FR-075 — Gate invalidation on approved-artifact change**  
If an approved Specification or Plan changes materially after approval, its
approval becomes stale and every downstream gate that depends on that revision
MUST be re-evaluated before downstream work resumes.

---

### Planning

**FR-033 — Closed execution packets**  
`forge-plan` MUST produce dependency-ordered execution packets that a competent
workhorse can implement without:

- new research
- architecture selection
- unresolved requirement decisions
- user questions

**FR-034 — Packet implementation detail**  
Each packet MUST contain enough implementation guidance to identify the intended:

- files
- symbols
- operations
- relevant local patterns
- interfaces
- dependencies
- ordered steps
- checks
- expected results
- acceptance evidence
- must-not-change boundaries

where applicable.

**FR-035 — No unnecessary preimplementation**  
Plans MUST include signatures, schemas, pseudocode, or code sketches only when
needed to freeze a meaningful decision or remove implementation ambiguity.

**FR-036 — Optional design separation**  
Cross-system integration, security-sensitive architecture, migration, material
compatibility contracts, hard-to-reverse trade-offs, or complexity that would
make the execution plan unreadable MAY be captured in a separate design artifact.

**FR-037 — ADR restraint**  
An ADR SHOULD be created only for a decision that is durable, surprising to a
future maintainer, and expensive or risky to reverse.

---

### Implementation

**FR-038 — Commit mode selection**  
At implementation start, the implementer MUST be able to choose among:

- review-first
- per-task
- end-only

commit behaviour.

**FR-039 — Dirty-tree isolation**  
Forge MUST NOT include, modify, or commit pre-existing or out-of-scope user
changes.

**FR-040 — Failed work exclusion**  
Failed or blocked work MUST NOT be committed by Forge.

**FR-041 — No automatic delivery side effects**  
Forge MUST NOT automatically squash, push, open a pull request, or merge without
explicit authorization.

**FR-042 — Narrow task validation**  
After each implementation packet, Forge MUST run only checks applicable to the
touched concerns before dependent work proceeds.

**FR-043 — Prevention checks**  
Where applicable to the changed code, implementation MUST proactively check for:

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

**FR-044 — Integrated verification**  
After implementation integration, Forge MUST perform one integrated deterministic
verification stage.

**FR-045 — Final semantic review**  
After deterministic verification, Forge MUST perform one final semantic review.

**FR-046 — Applicable quality only**  
Quality knowledge and checks MUST be selected according to touched concerns so
that unrelated checks do not consume unnecessary context or execution effort.

**FR-047 — Optional delegation**  
Forge MAY delegate large independent work where beneficial, but correctness MUST
NOT depend on delegation being available.

---

### Failure, Retry, Scope, and Recovery

**FR-048 — Bounded transient retry**  
Transient operations MAY be retried only within a bounded retry policy.

**FR-049 — Deterministic retry gating**  
A deterministic failure MUST NOT be retried until a cited input, code,
configuration, dependency, or environment state change could reasonably affect
the result.

**FR-050 — Dependency-aware blocking**  
When an approved packet or artifact contradicts current evidence, Forge MUST block
the affected packet and its dependent work.

**FR-051 — Independent progress**  
A blocked branch MUST NOT prevent unrelated independent packets from continuing
when their approved inputs remain valid.

**FR-052 — Scope authorization**  
Work outside approved scope MUST NOT be implemented silently.

**FR-053 — Proposed scope expansion**  
When unplanned work is discovered, Forge MUST present the proposed addition,
impact, and affected work for authorization.

**FR-054 — Approval invalidation after scope change**  
An approved scope change MUST invalidate downstream approvals or execution state
that are materially affected by that change.

**FR-055 — Honest unavailable checks**  
An unavailable, incomplete, or unexecuted required check MUST be recorded as
`UNMEASURED` with its reason and MUST NOT be represented as a pass.

**FR-056 — Safe resume**  
A rerun MUST verify recorded artifacts and relevant repository state before
resuming.

**FR-057 — Resume without duplication**  
A rerun MUST avoid duplicating verified questions, artifacts, completed work,
commits, or other side effects.

---

### Knowledge

**FR-058 — Generic knowledge provider**  
Forge MUST support optional project knowledge through a generic provider boundary
rather than depending on a specific knowledge system.

**FR-059 — Brain OKF integration**  
The Brain adapter MAY provide OKF as its project knowledge source.

**FR-060 — Applicable knowledge only**  
Forge SHOULD load only applicable leaf knowledge rather than full project
knowledge profiles.

**FR-061 — Knowledge continuity**  
Selected knowledge references and conclusions SHOULD be carried forward so later
stages need to reload only stale or newly applicable knowledge.

**FR-062 — Knowledge validation failure**  
A knowledge validation problem MUST be explained with its impact and MUST NOT
cause automatic repair or automatic blocking unless the current work item
requires the missing knowledge for correctness.

---

### Evaluation

**FR-063 — Portable behavioural evaluation**  
Forge MUST have portable static and behavioural evaluations covering its core
stage behaviour.

**FR-064 — Brain regression evaluation**  
Brain adapters MUST be evaluated against relevant historical Brain behaviour to
detect regressions.

**FR-065 — Baseline comparison**  
Evaluation SHOULD compare Forge-assisted behaviour with a no-skill baseline where
practical.

**FR-066 — Correctness before efficiency**  
Correctness MUST be evaluated before token usage, duration, tool calls,
references loaded, retries, or question counts.

**FR-067 — Host/model trial separation**  
Harness-specific and model-specific trials MUST be reported separately from
portable correctness validation.

**FR-068 — Missing evaluation capability**  
Unavailable test runners, harness capabilities, comparison systems, or models MUST
be reported as `UNMEASURED`, not as successful coverage.

---

## 6. Invariants

**INV-001 — Brain behaviour preservation**  
Refactoring Brain SDLC skills to use Forge MUST preserve required Brain-specific
behaviour.

**INV-002 — Portable correctness**  
Core Forge correctness MUST NOT depend on Brain Payroll, Jira, OKF, a specific
model, a named agent type, or a particular harness feature.

**INV-003 — User control of progression**  
Forge MUST NOT cross a stage boundary unless the user's expressed intent
authorizes it.

**INV-004 — Settled decision preservation**  
Approved upstream decisions MUST remain authoritative until contradictory
evidence, staleness, or authorized scope change makes them invalid.

**INV-005 — Scope isolation**  
Forge MUST NOT silently modify work outside approved scope.

**INV-006 — User-work isolation**  
Pre-existing unrelated working-tree changes MUST remain untouched and excluded
from Forge-created commits.

**INV-007 — Honest evidence**  
Unavailable checks, inaccessible sources, or unsupported claims MUST NOT be
represented as verified.

**INV-008 — Specification boundary**  
Specification MUST define WHAT must be true, not arbitrary HOW it must be
implemented.

**INV-009 — Planning readiness**  
An approved plan MUST not require the workhorse implementer to perform new
research, architecture selection, or product clarification.

**INV-010 — Review structure**  
Integrated deterministic verification MUST precede the final semantic review.

**INV-011 — No duplicate portable logic**  
Brain adapters MUST NOT become a second independently maintained implementation
of portable Forge workflow behaviour.

**INV-012 — No gate bypass by orchestration**  
Automatic workflow continuation MUST preserve the same approval gates as manual
stage-by-stage invocation. No invocation wording, including "implement", may make
source-code mutation legal before the required Specification and Plan approvals.

---

## 7. Data and State Semantics

Forge must maintain sufficient workflow state to support:

- stage status
- approval validity
- upstream artifact freshness
- completed execution packets
- verification outcomes
- blocked dependencies
- authorized scope changes
- selected knowledge applicability
- safe resume

The exact storage format, file layout, hashing implementation, identifier
generation mechanism, and persistence mechanism are implementation/design
concerns unless separately established as binding constraints.

A rerun must treat recorded state as evidence to verify, not as unconditional
proof that the underlying repository or artifact state is still unchanged.

---

## 8. Edge Cases and Failure Behaviour

### EC-001 — Previously answered question

If a materially equivalent answer already exists in authoritative current
context, Forge must not ask the question again.

### EC-002 — Conflicting current sources

If current authoritative sources conflict on a material product decision, the
affected decision must be routed to clarification rather than guessed.

### EC-003 — Historical contradiction

If historical evidence conflicts with current intent, current intent remains
authoritative unless the conflict exposes a genuine unresolved decision.

### EC-004 — Inaccessible source

If a relevant source cannot be accessed, Forge must record the missing evidence
and its impact.

### EC-005 — Missing visual reference

If relevant UI evidence is missing, Forge should record a warning or risk unless
the missing reference prevents specification or verification.

### EC-006 — Plan contradiction during implementation

If implementation discovers that an approved packet conflicts with verified
evidence, that packet and dependent work must stop while safe independent work
may continue.

### EC-007 — Unplanned required work

If implementation discovers work outside approved scope, it must request
authorization before implementing that work.

### EC-008 — Unavailable check

If a required check cannot run, its result must be `UNMEASURED`; downstream
completion reporting must preserve that fact.

### EC-009 — Resume after interruption

After interruption, Forge must verify persisted workflow and repository state and
continue from the first incomplete or stale point without duplicating completed
side effects.

### EC-010 — Limited harness

If delegation, subagents, hooks, or other optional host capabilities are
unavailable, Forge must still be able to complete its core workflow correctly.

---

## 9. Non-Functional Requirements

**NFR-001 — Portability**  
Forge MUST remain usable across compatible projects and harnesses without
requiring Brain-specific infrastructure.

**NFR-002 — Token efficiency**  
Forge SHOULD avoid loading irrelevant source material, duplicated portable logic,
full project knowledge profiles, or unrelated quality checks.

**NFR-003 — Determinism where practical**  
Approval state, completion state, retry accounting, dependency blocking, and
verification results SHOULD be represented in a form that can be validated
deterministically.

**NFR-004 — Recoverability**  
Workflow interruption MUST NOT require restarting completed verified work from
scratch.

**NFR-005 — Maintainability**  
Portable behaviour SHOULD have one canonical implementation and Brain-specific
behaviour SHOULD remain isolated in adapters.

**NFR-006 — Evidence-driven behaviour**  
Material conclusions, reopened decisions, blockers, and verification outcomes
SHOULD be supported by identifiable evidence.

**NFR-007 — Context minimisation**  
Forge SHOULD retain or reload only information necessary to preserve correctness,
traceability, and stage continuity.

---

## 10. Security and Safety Requirements

**SEC-001 — Minimal issue-content retention**  
Forge SHOULD persist only issue content materially used by the workflow by
default, reducing unnecessary payload and PII exposure.

**SEC-002 — No silent external mutation**  
Forge MUST NOT automatically publish issue changes or perform unrelated
repository mutations.

**SEC-003 — Explicit delivery authorization**  
Pushes, pull requests, merges, squashes, and equivalent externally visible
delivery actions MUST remain explicitly authorized.

**SEC-004 — Scope safety**  
Unplanned scope MUST be surfaced before mutation.

**SEC-005 — Knowledge repair safety**  
Forge MUST NOT silently repair unrelated knowledge or repository defects.

**SEC-006 — Permission awareness**  
Where permissions materially affect system behaviour, Discovery and
Specification MUST capture those differences.

---

## 11. External Contracts and Dependencies

Forge may interact with:

- issue sources
- conversation context
- repository state
- project knowledge providers
- project-specific validation
- optional harness delegation capabilities
- Brain-specific Jira and OKF integration through adapters

Portable Forge behaviour MUST NOT require any one of those optional integrations
except the inputs genuinely necessary for the requested stage.

When a required dependency or source is unavailable, Forge must report the impact
rather than silently assuming success or empty state.

---

## 12. Existing Behaviour and Required Delta

### Current Behaviour

Brain SDLC skills already provide useful clarification, discovery, specification,
planning, and implementation behaviour.

However, portable workflow behaviour is coupled to Brain-specific systems and
repeated across stages.

### Problems to Correct

The current structure can cause:

- repeated questions
- unnecessary context loading
- duplicated workflow logic
- inconsistent functional coverage
- Brain-specific host/tool assumptions
- quality issues discovered late in review
- difficulty reusing the workflow outside Brain

### Required Behaviour

After this change:

- portable behaviour is provided by Forge
- Brain-specific behaviour is provided by thin adapters
- previously answered decisions are reused
- Discovery is evidence-led
- Specification is behavioural and testable
- Planning produces workhorse-ready execution packets
- Implementation performs applicable prevention checks
- verification is integrated and deterministic where possible
- one final semantic review follows verification
- reruns safely resume
- side effects remain controlled

---

## 13. Binding Constraints

**CON-001 — Five-stage suite**  
The portable suite consists of five separate stage skills:
`forge-clarify`, `forge-discover`, `forge-spec`, `forge-plan`, and
`forge-implement`.

**CON-002 — User-invoked skills**  
All Forge and corresponding Brain skills are user-invoked.

**CON-003 — Harness-agnostic core**  
Portable core correctness must not depend on named models, agents, servers,
hooks, shell commands, or harness-specific invocation syntax.

**CON-004 — BA unchanged**  
The existing BA skill remains unchanged.

**CON-005 — MR Review unchanged**  
The existing MR Review skill remains unchanged and no replacement review skill is
introduced.

**CON-006 — Brain specialisation remains in adapters**  
Brain-specific Jira, OKF, project validation, artifacts, and delivery behaviour
remain adapter concerns.

**CON-007 — Existing package validation**  
Existing repository package validation is extended rather than replaced where it
already provides the required validation seam.

**CON-008 — Existing test seams preferred**  
Existing usable repository test seams are preferred over introducing a separate
evaluation framework solely for Forge.

**CON-009 — Approval-gated implementation sequence**  
For workflows that require both functional and technical approval, the minimum
sequence is:

`Discovery/Clarification → Specification → Specification approval → Planning → Plan approval → Implementation`

A stage may stop earlier, but it MUST NOT reorder or bypass these gates.

---

## 14. Acceptance Scenarios

### AC-001 — Stage-only request stops

**Given** a user invokes only `forge-discover`  
**When** Discovery completes successfully  
**Then** Forge stops at the Discovery boundary unless the user has already
authorized continuation.

Maps to: FR-001, FR-003, INV-003

---

### AC-002 — Full workflow continues without bypassing gates

**Given** the user explicitly requests the complete Forge workflow  
**When** one stage completes  
**Then** Forge may continue automatically only if the next stage's prerequisites
and required approvals are satisfied; otherwise it stops at the gate and requests
the required approval.

Maps to: FR-002, FR-069, FR-070, INV-012

---

### AC-003 — Previously answered question is suppressed

**Given** a materially equivalent current answer exists in available issue
content, BA output, approved artifacts, or current conversation context  
**When** Clarification or Discovery evaluates the decision  
**Then** the user is not asked the same question again.

Maps to: FR-008, FR-009, FR-010

---

### AC-004 — Historical conflict does not silently override current intent

**Given** historical issue content conflicts with a current requirement  
**When** Discovery evaluates that history  
**Then** the history is treated as supporting evidence and any genuinely
unresolved conflict is returned to clarification rather than silently replacing
current intent.

Maps to: FR-012, FR-013

---

### AC-005 — Inaccessible source remains visible

**Given** a materially relevant linked source cannot be accessed  
**When** Discovery completes  
**Then** the source and its potential impact are explicitly recorded and are not
reported as successfully checked.

Maps to: FR-017, INV-007

---

### AC-006 — Specification contains no unresolved product decision

**Given** Discovery has completed  
**When** `forge-spec` produces a Specification  
**Then** the Specification is not marked ready if a material behavioural or
product decision remains unresolved.

Maps to: FR-023, FR-026

---

### AC-007 — Specification does not choose arbitrary implementation

**Given** a behavioural requirement can be satisfied by multiple valid technical
approaches  
**When** `forge-spec` formalizes the requirement  
**Then** it defines required observable behaviour and constraints without
selecting a non-binding implementation mechanism.

Maps to: FR-024, FR-027, INV-008

---

### AC-008 — Workhorse-ready plan

**Given** an approved Specification  
**When** `forge-plan` completes  
**Then** a competent workhorse can implement each ready packet using the packet
and its cited local material without new research, architecture selection, or
user questions.

Maps to: FR-033, FR-034, INV-009

---

### AC-009 — Unrelated working-tree changes remain untouched

**Given** the repository contains pre-existing changes outside approved scope  
**When** `forge-implement` executes and commits approved work  
**Then** those unrelated changes are neither modified nor included in
Forge-created commits.

Maps to: FR-039, INV-005, INV-006

---

### AC-010 — Applicable prevention checks run during implementation

**Given** a packet changes code affected by one or more defined quality concerns  
**When** the packet is implemented  
**Then** Forge runs the applicable narrow checks before dependent work proceeds
and does not load unrelated checks.

Maps to: FR-042, FR-043, FR-046

---

### AC-011 — Integrated verification precedes final semantic review

**Given** all implementation packets are complete or otherwise resolved  
**When** final verification begins  
**Then** Forge performs integrated deterministic verification before one final
semantic review.

Maps to: FR-044, FR-045, INV-010

---

### AC-012 — Deterministic failure does not loop

**Given** an operation has failed deterministically  
**When** no relevant input, code, configuration, dependency, or environment state
has changed  
**Then** Forge does not retry that operation.

Maps to: FR-049

---

### AC-013 — Contradiction blocks only affected work

**Given** implementation discovers a contradiction in an approved packet  
**When** dependent and independent packets remain  
**Then** Forge blocks the affected packet and dependent work while allowing safe
independent work to continue.

Maps to: FR-050, FR-051

---

### AC-014 — Unplanned scope requires authorization

**Given** implementation discovers required work outside approved scope  
**When** Forge evaluates that work  
**Then** it presents the addition and impact for authorization and does not
silently implement it.

Maps to: FR-052, FR-053, FR-054

---

### AC-015 — Unavailable verification is not a pass

**Given** a required check cannot run  
**When** Forge reports verification status  
**Then** the check is recorded as `UNMEASURED` with a reason and contributes no
pass result.

Maps to: FR-055, INV-007

---

### AC-016 — Resume does not duplicate completed work

**Given** a previous Forge run was interrupted after some work was verified  
**When** the workflow is rerun  
**Then** Forge verifies the recorded state and resumes from the first incomplete
or stale point without duplicating verified questions, artifacts, work, commits,
or side effects.

Maps to: FR-056, FR-057, NFR-004

---

### AC-017 — Limited harness still works

**Given** a compatible harness does not support delegation or subagents  
**When** Forge executes a workflow  
**Then** core workflow correctness remains available without those capabilities.

Maps to: FR-047, INV-002

---

### AC-018 — Brain adapter preserves project behaviour

**Given** a Brain workflow is migrated to use Forge  
**When** historical Brain regression fixtures are replayed  
**Then** required Brain behaviour remains preserved while portable workflow logic
is sourced from Forge rather than duplicated.

Maps to: FR-004, FR-005, FR-064, INV-001, INV-011

---

### AC-019 — "Implement using SDLC" does not authorize early code changes

**Given** a user says "Implement BR-21861 using Agentic SDLC" or equivalent  
**And** Discovery/Decision artifacts are complete  
**But** the Specification is not yet approved  
**When** the workflow continues  
**Then** it may create/present the Specification but MUST NOT create the
implementation Plan or modify source code until the Specification approval gate
is satisfied.

Maps to: FR-070, FR-071, FR-073, INV-012, CON-009

---

### AC-020 — Implementation waits for Plan approval

**Given** the Specification is approved  
**And** Planning produces a Plan  
**But** the Plan/technical approval is still pending  
**When** the workflow is asked to continue or implement  
**Then** source code remains unchanged and `forge-implement` does not start until
the Plan approval is valid.

Maps to: FR-069, FR-072, FR-073, CON-009

---

### AC-021 — Post-hoc approval is rejected as a valid gate

**Given** source code was modified before a required approval  
**When** approval is requested after those modifications  
**Then** that approval MUST NOT retroactively validate the earlier mutation; the
workflow reports a gate violation and requires remediation/revalidation according
to project policy.

Maps to: FR-069, FR-073, FR-074

---

### AC-022 — Designated approver is enforced

**Given** the adapter/workflow requires approval from a designated approver  
**When** another actor, the agent itself, or an earlier generic "proceed" intent
is presented as approval  
**Then** the gate remains closed until the configured approval policy is
satisfied.

Maps to: FR-074

---

## 15. Success Criteria

The change is successful when:

**SC-001** — All five Forge stages can operate without Brain-specific
dependencies for their portable core behaviour.

**SC-002** — Brain workflows preserve required existing Brain behaviour through
Forge-backed adapters.

**SC-003** — Previously answered materially equivalent questions are not repeated
in covered evaluation scenarios.

**SC-004** — Specifications produced by Forge contain no unresolved product
decisions and no non-binding technical design leakage.

**SC-005** — Approved plans are executable by a competent workhorse without new
research, architecture selection, or user clarification.

**SC-006** — Implementation verification reports unavailable checks as
`UNMEASURED` rather than successful.

**SC-007** — Interrupted workflows can resume without duplicating verified
questions, completed work, or side effects in covered recovery scenarios.

**SC-008** — Portable validation and Brain regression validation are reported
separately from harness/model-specific trials.

**SC-009** — Correctness results are reported before efficiency metrics such as
token usage, duration, tool calls, loaded references, retries, and questions
asked.

**SC-010** — Covered full-workflow evaluations prove that source code remains
unchanged until required Specification and Plan approvals are valid.

**SC-011** — Covered Brain-adapter evaluations prove that a designated approver
cannot be bypassed by full-workflow wording, agent self-approval, or post-hoc
approval.

---

## 16. Traceability

| Source intent / original story area | Specification |
|---|---|
| Explicit stage invocation and continuation | FR-001 to FR-003 |
| Brain adapters over portable core | FR-004, FR-005, INV-001, INV-011 |
| Clarification and repeated-question prevention | FR-006 to FR-013 |
| Issue and evidence coverage | FR-014 to FR-022 |
| Behavioural Specification | FR-023 to FR-028, INV-008 |
| Approval behaviour | FR-029 to FR-032, FR-069 to FR-075, INV-012, CON-009 |
| Workhorse-ready Planning | FR-033 to FR-037, INV-009 |
| Commit and implementation behaviour | FR-038 to FR-047 |
| Retry, blocking, scope, resume | FR-048 to FR-057 |
| Knowledge integration | FR-058 to FR-062 |
| Evaluation and honest measurement | FR-063 to FR-068, INV-007 |
| Portability and context efficiency | NFR-001 to NFR-007 |
| Safety and mutation controls | SEC-001 to SEC-006 |
| Fixed suite constraints | CON-001 to CON-008 |

Downstream planning and implementation should preserve these identifiers wherever
a task or verification step satisfies a requirement.

Preferred trace:

`Discovery Decision → FR / INV / NFR / SEC / CON → Plan Task → Verification`

---

## 17. Specification Readiness

This Specification is ready for Planning only when:

- all material Discovery decisions are represented without reinterpretation
- no unresolved user-owned behavioural decision remains
- every mandatory behaviour is represented by a stable requirement
- applicable invariants, constraints, security requirements, and NFRs are explicit
- important positive, negative, recovery, and boundary behaviour is testable
- acceptance scenarios cover the material behaviour
- downstream Planning can determine what must be achieved without inventing
  requirements
- Planning remains free to decide non-binding implementation mechanisms
- full-workflow intent cannot be mistaken for approval of future artifacts
- Planning cannot consume an unapproved Specification when approval is required
- Implementation cannot mutate source code before required Specification and Plan
  approvals are valid

If a material ambiguity is discovered later, the affected branch must return to
Discovery/Clarification rather than being silently decided inside Specification,
Planning, or Implementation.

---

## 18. Notes Preserved from the Source Specification

- The existing OKF bundle currently passes its deterministic validator. Forge
  still requires failure behaviour because future broken links, metadata,
  encoding, navigation, or root structure could reduce knowledge coverage.
- The canonical portable source belongs in the plugin's authored skill tree.
  Brain installations should consume verified copies rather than becoming a
  second independently authored source.
- Existing design and implementation-plan documents under the documentation area
  are separate artifacts and must not be overwritten unless separately
  authorized.
- Issue-tracker publication and any `ready-for-agent` label remain outside this
  specification because no project issue-tracker configuration or triage
  vocabulary was supplied.
