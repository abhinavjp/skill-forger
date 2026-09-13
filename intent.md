# Intent: Proportional planning in Forge

## Status

Revision: 2

Resolved decision record; awaiting explicit approval of Intent revision 2 and
Specification revision 1 at `docs/specs/forge-plan-proportional-planning.md`.
The content hashes are presented at the approval checkpoint and are not approval
hashes until the shared workflow contract records valid artifact approval.

## Why

`forge-plan` currently has one planning depth. It works for bounded changes, but complex work may need stronger evidence, traceability, risk analysis, and handoff detail. Applying that depth to every change would create unnecessary context, ceremony, and stale duplication.

The goal is proportional planning: small work stays compact; consequential work becomes implementation-ready without turning the plan into an as-built archive.

## Intended outcome

One `forge-plan` skill supports two modes through one shared workflow:

1. A compact mode for bounded, low-risk changes.
2. A detailed mode for cross-system, migration-heavy, security-sensitive, multi-implementer, or recovery-sensitive changes.

Both modes produce dependency-ordered, executable vertical slices. Detailed mode adds proof and risk coverage, not repeated prose or copied source code.

## Users

- Planner: researches the repository, freezes technical choices, and creates the plan.
- Reviewer: checks scope, evidence, dependencies, risks, and readiness.
- Implementation agent or developer: executes a slice without broad rediscovery or unresolved design choices.

## Core principles

- Keep one model-invoked `forge-plan`; disclose mode-specific guidance only after mode selection.
- Consume approved intent/specification artifacts when present. Preserve their IDs, authority, and unresolved questions.
- Prefer tracer-bullet vertical slices that are independently verifiable.
- State real blocking edges and expose the executable frontier.
- Put narrow tests in each slice; reserve final gates for cross-cutting regression and semantic checks.
- Use one canonical decision/evidence source and reference it; do not restate decisions across artifacts.
- Keep verified paths, symbols, contracts, and commands when they prevent rediscovery. Avoid volatile line numbers and pasted implementation unless they freeze a decision that prose cannot.
- Separate planning from tracker publication, implementation, and as-built/recovery documentation.

## Compact-mode minimum

- Outcome and source basis
- Scope, exclusions, and preserved behaviour
- Verified current-state summary
- Frozen decisions, assumptions, and blockers
- Vertical execution slices with exact change surface
- Per-slice verification and observable acceptance
- Dependency order and final gates

## Detailed-mode additions

Generate only the parts warranted by the change:

- Authority order and evidence ledger
- Requirement, invariant, and acceptance traceability
- Affected systems plus verified paths/symbols/contracts
- Data migration, rollback, compatibility, and deployment ordering
- Permission, security, privacy, failure, concurrency, and operational analysis
- Dependency graph, parallel frontier, prefactoring, or expand-migrate-contract sequence
- Cross-cutting regression/UAT matrix
- Definition of Ready, Definition of Done, and handoff contract

## Detailed-mode phase model

A phase is a small, reviewable vertical outcome. It may align with one module or one portal/module when that boundary delivers working behaviour. Repository layout alone does not define a phase.

Each phase:

- owns one cohesive outcome, contract, and integration point;
- leaves the system working unless an approved exception records the recovery path;
- contains dependency-ordered task files sized for a fresh context window;
- includes narrow checks inside tasks and an integrated phase gate;
- is small enough for one focused review;
- exposes every unblocked task as its parallel frontier.

Enabling work is allowed only when it unlocks a named working phase. Use expand-migrate-contract when a schema, API, or protocol cannot change atomically.

## Detailed-mode artifact architecture

Use progressive context loading. The implementor reads global facts once, phase facts once, and only the active task.

### `plan.md` — control plane

Owns only:

- outcome, scope, exclusions, approved baseline, and source authority;
- canonical requirement, invariant, contract, decision, and risk IDs;
- phase outcomes, `depends_on` edges, parallel frontier, integration points, and gates;
- change, review, commit, and approval policies;
- cross-phase proof and final acceptance.

### Phase file — shared phase context

Owns only:

- phase outcome, contract, invariants, integration point, and risk level;
- ordered task index and local dependency edges;
- shared references needed by more than one task;
- integrated verification gate and review focus;
- phase handoff fields.

### Task file — execution packet

Owns only:

- one observable outcome;
- exact write scope and relevant symbols;
- referenced requirement, contract, decision, invariant, and risk IDs;
- task-local constraints and ordered implementation changes;
- narrow proof command or observation and expected result;
- compact handoff: changed files, checks, deviations, and next blockers.

Global research, requirements, decisions, dependency graphs, and prior task summaries are not copied into task files. Verified paths and symbols stay because they prevent rediscovery. Volatile line numbers and recoverable source listings stay in the repository.

## Phase completion and review gate

For each phase:

1. Execute ready tasks in dependency order or safely in parallel.
2. Run each task's narrow checks during implementation.
3. Run the integrated phase checks before review.
4. Review the complete phase against intent, plan, behaviour, architecture, security, regression risk, maintainability, and scope.
5. Classify findings as `blocking`, `non-blocking`, or `out-of-scope`.
6. Fix blocking findings and rerun affected checks.
7. Run one final integrated review after the blocking set closes.
8. Record remaining non-blocking findings, deviations, proof, and `UNMEASURED` behaviour in the phase handoff.
9. Pause for the user's next instruction.

A phase is clean when required checks pass and zero blocking findings remain. “No findings” is not required. If two review loops make no progress or reviewers materially disagree, stop and ask the user.

At the phase pause, offer only applicable actions: continue, run extra testing, commit, revise, or stop. Required automated checks are already complete. “Extra testing” means manual, browser, hardware, migration, performance, live-provider, security, or user-acceptance testing.

Task-level semantic review is exceptional: use it for irreversible, security-critical, or unusually uncertain work. Do not review every task by default.

## Commit and delivery policy

Planning records these independent choices:

```yaml
commit_granularity: task | phase | end | none
commit_approval: always_ask | preapproved
history_style: separate | fixup_then_squash | squash
```

Recommended detailed-mode default:

```yaml
commit_granularity: phase
commit_approval: always_ask
history_style: separate
```

`always_ask` pauses before every commit. `preapproved` permits commits only after the selected clean gate. Both still pause after every phase. Commit authority never grants push, merge, release, or deployment authority. The policy cannot change silently during execution.

## Software fundamentals expressed as rules

- Information hiding: group work around a cohesive behaviour or decision; state the owned contract and hide unrelated detail.
- Contracts and invariants: define boundary inputs, outputs, errors, compatibility, and preserved truths once; reference their IDs from tasks.
- Incremental delivery: every normal phase produces a working, observable result.
- Small batches: phase size is limited by reviewability, not file count or task count.
- Traceability: map every requirement and invariant once to its owning phase/task and proof.
- Change control: update the canonical decision and affected mappings before dependent work continues.
- Simplicity: include only information that changes implementation, verification, ordering, or risk.
- Proportional risk: risk decides extra test depth, review independence, recovery detail, and human gates.

Risk-specific controls are conditional:

- rollback for deployed, stateful, external, or hard-to-reverse changes;
- idempotency for retries, jobs, webhooks, migrations, and resumable operations;
- observability for runtime behaviour requiring production proof;
- expand-migrate-contract for mixed-version compatibility;
- independent security review for security-sensitive phases;
- additional test levels only when they cover a distinct risk.

Do not add empty risk appendices. Do not use `SOLID`, `DRY`, `YAGNI`, or similar slogans without translating them into an observable rule for this plan.

## Language standard

All Forge plan artifacts use simple English as a correctness control:

- short sentences;
- one meaning per requirement;
- concrete verbs and named owners;
- explicit inputs, outputs, conditions, and expected results;
- explained domain terms;
- no ceremonial prose, unexplained jargon, or vague instructions such as “handle appropriately.”

Simple language must not remove technical precision.

## Skill framing

Keep one model-invoked `forge-plan` skill. Its main `SKILL.md` contains the shared ordered workflow and checkable completion criteria. It selects planning depth during grilling, then loads only the selected mode's reference.

Recommended package shape:

```text
forge-plan/
  SKILL.md
  references/
    compact-mode.md
    detailed-mode.md
    execution-packet.md
  evals/
    trigger.json
    execution.json
```

The detailed reference owns phase architecture, artifact contracts, phase review, risk routing, and commit policy. The compact reference owns only differences from the shared workflow. Shared approval and mutation rules remain in the existing Forge workflow contract.

Every context pointer states the branch that loads its target. Each concept has one source of truth. Each workflow step ends with an observable completion condition. Remove prose that only repeats defaults, repository structure, another reference, or an earlier warning.

## Constraints

- Existing Forge approval, freshness, provenance, mutation, and resume gates remain authoritative.
- A work packet must fit a fresh implementation context and require no product interpretation, architecture selection, or broad technical research.
- Missing product intent returns upstream; planning must not invent it.
- Detailed mode must not copy the BR-21598 folder layout, duplicate decisions, split work mechanically by technical layer, or create a separate final testing phase for checks that belong inside slices.
- Tracker publishing remains outside `forge-plan`.
- Phase review and commits remain implementation responsibilities; `forge-plan` freezes their policy but does not perform them.

## Resolved mode selection

The two modes are `compact` and `detailed`. Selection happens during grilling.
Forge recommends a mode from the verified risk and coordination evidence, then
waits for the user's confirmation or explicit override before loading
mode-specific guidance. It never switches modes silently.

Compact is the default only for verified bounded, low-risk work with no
unresolved material decision. Detailed is recommended when one severe factor or
several connected moderate factors make a single compact packet unsafe. The
decision is evidence-based; no fixed signal count decides it.

## Success criteria

- A bounded change yields a short executable plan without unnecessary appendices.
- A consequential change closes material evidence, compatibility, security, data, failure, and handoff risks.
- Every requirement/invariant maps to a slice or an explicit protection/no-change decision.
- Slices are vertical where feasible, independently verifiable, dependency-correct, and fresh-context sized.
- No decision is duplicated as independent prose across artifacts.
- The implementation agent can execute without rediscovering the change surface or choosing a material alternative.
- Candidate behavior beats or matches the current skill on correctness, then improves proportionality/context cost.
- A detailed implementor can load one global control file, one phase file, and one active task without losing any binding decision.
- Every completed phase has passing required checks, zero blocking findings, a compact handoff, and an explicit user decision before continuation.
- No commit occurs outside the planned granularity and approval policy.

## Evaluation intent

Add differential cases for compact defaulting, detailed risk selection, explicit user override, vertical slicing, cohesive phase boundaries, phase size, wide-refactor handling, blocker/frontier correctness, phase review closure, stalled review loops, commit authorization, stale-source conflict detection, unresolved-intent preservation, duplication avoidance, simple language, conditional risk controls, progressive context loading, and work-packet closure. Compare candidate versus current `forge-plan`; leave unrun model behavior `UNMEASURED`.

## Resolved decisions for Specification

1. `DEC-001` — Use the mode names `compact` and `detailed`.
2. `DEC-002` — Forge recommends a mode during grilling from verified evidence;
   the user must confirm or override before mode-specific guidance loads.
3. `DEC-003` — Default to compact for verified bounded low-risk work. Recommend
   detailed for one severe factor or connected moderate factors whose combined
   coordination, uncertainty, or impact makes compact unsafe. Do not use a fixed
   signal count.
4. `DEC-004` — Detailed output uses `plan.md`, then
   `phases/<phase>/phase.md`, then ordered task files in each phase directory.
5. `DEC-005` — Compact output is one `plan.md` with inline,
   dependency-ordered vertical slices. It uses the reduced compact contract and
   creates no phase or task files.
6. `DEC-006` — A phase is one cohesive working outcome with one integration
   point. Split before execution when independent deployable/reversible outcomes
   exist or one reviewer cannot understand and verify the complete phase in one
   focused pass. Do not split by repository layer, task count, or line count.
7. `DEC-007` — Independent review is mandatory for high-risk work and for any
   security, permission, privacy, compliance, irreversible-migration,
   credible-data-loss, or recovery-critical boundary. Low risk uses same-agent
   integrated review; medium risk does so unless novelty makes independence
   necessary.

Ticket-ready output is sufficient. Any downstream ticket conversion is outside
`forge-plan` and belongs to a separately invoked, separately authorized actor.

## Non-goals

- Renaming the modes before grilling
- Implementing the skill change in this artifact
- Publishing tracker tickets
- Replacing `forge-spec`, `forge-implement`, or the shared workflow contract
- Turning every plan into compliance documentation or disaster-recovery instructions

## Source basis

- Local BR-21598 planning/as-built dossier: `D:\AI\skills\BR-21598-company-timesheet`
- [Anthropic: The AI-native software development lifecycle](https://claude.com/blog/the-ai-native-sdlc-playbook)
- [mattpocock/skills: writing-for-agents](https://github.com/mattpocock/skills/tree/main/skills/productivity/writing-for-agents)
- [Intent-Driven Development case study](https://dev.to/copyleftdev/intent-driven-development-define-the-system-before-you-write-the-code-22pe) — secondary source; not normative.
- [Google Engineering Practices: Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html)
- [Parnas: On the Criteria To Be Used in Decomposing Systems into Modules](https://doi.org/10.1145/361598.361623)
- [NASA Systems Engineering Handbook](https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf)
- Research synthesis: `docs/research/2026-09-12-forge-plan-modes-research.md`
- Phase-gate research: `docs/research/2026-09-12-forge-phase-gates-re-research.md`
- Software-fundamentals research: `docs/research/2026-09-12-forge-software-fundamentals.md`
