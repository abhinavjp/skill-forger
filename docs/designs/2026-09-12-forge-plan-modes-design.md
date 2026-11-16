# Forge proportional planning design

## Status

Approved on 2026-09-12. Design only. Implementation is not authorized.

## Decision

`forge-plan` remains one model-invoked Skill with two planning modes:

- `compact`: bounded work whose implementation and proof fit one concise plan.
- `detailed`: consequential work needing phased coordination, stronger traceability, or risk-specific controls.

Both modes produce dependency-ordered, implementation-ready vertical work. Detailed mode adds warranted control and evidence. It does not repeat source material or create an as-built archive.

## Mode recommendation and confirmation

Forge recommends a mode from what is currently known. It explains the recommendation, uncertainty, and decisive factors. The user confirms or overrides before mode-specific guidance loads.

Assess these factors together:

- size: affected systems, repositories, deployables, contracts, and change surface;
- effort: implementation, verification, coordination, and recovery effort;
- complexity: dependency depth, concurrency, legacy ambiguity, and integration count;
- impact: user, operational, data, security, privacy, compliance, and failure blast radius;
- reversibility: migration, external side effects, rollback difficulty, and mixed-version operation;
- execution model: multiple implementers or agents, handoffs, and audit needs;
- uncertainty: missing evidence, novel mechanisms, disputed behavior, or unstable boundaries.

Default recommendation is `compact` when known evidence supports bounded, low-risk work. Use no hard signal count. One severe factor can justify `detailed`; several moderate factors can do the same.

Recommend `detailed` when any of these is material:

- irreversible or recovery-critical data change;
- high-impact security, permission, privacy, or compliance change;
- cross-repository, cross-deployable, or mixed-version coordination;
- external integration with consequential failure modes;
- several implementers or agents with meaningful dependency edges;
- ambiguous legacy behavior that must be preserved;
- explicit audit, rollback, migration, or recovery requirements;
- a change surface too large or coupled for one focused review.

The user may request `detailed` for any work. If the user requests `compact` but the compact packet cannot close material decisions, evidence, or safety constraints, Forge identifies the exact gap and asks the user to reduce scope, accept `detailed`, or return upstream. It never silently weakens readiness.

If later research changes the recommendation, Forge pauses, shows the new evidence, and asks for confirmation. It may not silently switch modes.

## Shared workflow and invariants

The main `SKILL.md` owns the shared ordered workflow:

1. Load approved upstream artifacts and establish authority, provenance, freshness, and scope.
2. Research the repository until the current state and change surface are verified.
3. Grill unresolved product and technical decisions; return missing product intent upstream.
4. Recommend and confirm the planning mode.
5. Load only the selected mode reference.
6. Produce dependency-correct vertical work with observable proof.
7. Review the plan for readiness and obtain approval.
8. Stop. Tracker publication and implementation are separate invocations.

Existing Forge approval hashes, freshness checks, provenance, mutation controls, and resume behavior remain authoritative. A planning approval grants no authority to implement, commit, publish tickets, push, merge, deploy, or release.

Every execution packet must remove product interpretation, architecture selection, broad rediscovery, and unresolved material alternatives from implementation.

## Compact mode

Compact mode uses one `plan.md`. It retains semantic closure, not every detailed-mode section.

Required content:

- outcome and approved source basis;
- scope, exclusions, and preserved behavior;
- verified current state;
- frozen decisions, assumptions, and blockers;
- dependency-ordered vertical slices;
- exact write scope and relevant symbols for each slice;
- change instructions and must-not-change constraints;
- narrow verification with expected results;
- observable acceptance and final gates;
- compact implementation handoff fields.

Risk overlays appear only when triggered. Empty sections are omitted. Existing approval, provenance, freshness, and mutation gates are never reduced.

## Detailed artifact architecture

Use one directory per phase:

```text
<work-item>/
  plan.md
  phases/
    01-<phase-slug>/
      phase.md
      01-<task-slug>.md
      02-<task-slug>.md
```

`plan.md` is the control plane. It owns outcome, scope, exclusions, approved baseline, source authority, canonical IDs, the phase dependency graph, executable frontier, integration points, change policy, commit policy, cross-phase proof, and final acceptance.

Each `phase.md` owns one phase outcome, contract, invariants, integration point, risk classification, task index, local dependency edges, shared references, integrated gate, review focus, and phase handoff contract.

Each task file owns one observable outcome, exact write scope and symbols, referenced canonical IDs, local constraints, ordered changes, narrow proof and expected result, and compact handoff fields.

Global research, decisions, requirements, graphs, and prior task summaries are referenced, not copied. Paths, symbols, contracts, and commands remain where they prevent rediscovery. Volatile line numbers and recoverable source listings remain in the repository.

## Phase boundary and size

A phase is one cohesive, working vertical outcome with an owned contract and integration point. Repository layers, modules, portals, file counts, and task counts do not define phases.

Split a phase before execution when either is true:

- one focused reviewer cannot understand its behavior, contract, risks, and integrated diff in one pass;
- it contains more than one independently deployable or independently reversible outcome.

The existing `3 requirements / 8 files / 2 boundaries` rule may be used as a warning heuristic only. Exceeding it requires a short cohesion rationale, not automatic rejection. Generated changes and cohesive cross-cutting refactors may exceed file counts.

Normal phases leave the system working. Enabling work is allowed only when it unlocks a named working phase. Use expand-migrate-contract when a boundary cannot change atomically.

## Risk routing

Each phase records `low`, `medium`, or `high` risk with reasons.

- `low`: reversible, bounded, locally proven; same-agent integrated review.
- `medium`: meaningful integration, compatibility, operational, or uncertainty risk; same-agent review unless novelty or uncertainty weakens independence.
- `high`: severe impact, difficult recovery, or sensitive boundary; independent review required.

Independent review is mandatory regardless of aggregate label for:

- security, permission, privacy, or compliance-sensitive behavior;
- irreversible migration or credible data-loss risk;
- recovery-critical behavior where a failed plan could prevent restoration.

Task-level semantic review is exceptional. Require it only for an irreversible step, a security-critical boundary, or unusually uncertain work that should not wait for phase integration.

Add controls only when their risk exists:

- rollback for deployed, stateful, external-side-effect, or hard-to-reverse work;
- idempotency for retries, jobs, webhooks, migrations, and resumable operations;
- observability for runtime behavior requiring operational proof;
- expand-migrate-contract for mixed-version boundaries;
- manual, browser, hardware, migration, performance, live-provider, security, or UAT proof when automated checks cannot cover the risk.

## Phase gate and pause

For each detailed phase:

1. Execute ready tasks by dependency order or safe parallel frontier.
2. Run task-local checks during implementation.
3. Run the integrated phase checks.
4. Review the complete phase against intent, plan, behavior, architecture, security, regression risk, maintainability, and scope.
5. Classify findings as `blocking`, `non-blocking`, or `out-of-scope`.
6. Fix blocking findings and rerun affected checks.
7. Run one final integrated review after the blocking set closes.
8. Record proof, deviations, remaining non-blocking findings, and `UNMEASURED` behavior in the phase handoff.
9. Pause for the user.

A phase is clean when required checks pass and zero blocking findings remain. A finding-free review is not required. Stop for user direction when two review loops make no progress or reviewers materially disagree.

At a clean phase pause, offer only applicable actions:

- continue to the next ready phase;
- run named extra testing;
- commit under the approved policy;
- revise the plan or completed phase;
- stop.

Required automated checks are complete before this menu appears. Extra testing names the manual or live evidence still absent.

## Commit policy

Every plan freezes three independent fields:

```yaml
commit_granularity: task | phase | end | none
commit_approval: always_ask | preapproved
history_style: separate | fixup_then_squash | squash
```

Defaults:

- compact: `end`, `always_ask`, `separate`;
- detailed: `phase`, `always_ask`, `separate`.

Use task commits only when tasks are independently revertible, are intentionally stacked, or need recovery checkpoints inside a long or risky phase. Use `none` when the user owns history or the worktree cannot be narrowed safely.

`preapproved` permits a commit only after its selected gate is clean. `always_ask` pauses before every commit. Both retain the phase pause. Commit authority never includes push, merge, release, or deployment. Policy changes require explicit user approval.

## Ticket-ready handoff

`forge-plan` produces a formal, read-only `to-tickets` handoff when requested or when tracker conversion is an approved next step. It does not publish tickets.

The handoff contains only:

- approved plan path and artifact hash;
- stable phase and task IDs;
- title and outcome for each ticket candidate;
- exact dependency edges and current frontier;
- scope and acceptance references;
- relevant risk, review, and approval policy references.

Ticket prose must derive from canonical plan content. The handoff may not duplicate requirements or invent tracker structure. Publishing remains a separate invocation with separate authorization and live verification.

## Skill package

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

The model-facing description covers planning requests, proportional depth, and the boundary from implementation or ticket publication. `SKILL.md` holds shared steps and observable completion criteria. Each mode pointer states exactly when to load its reference. `execution-packet.md` owns shared packet semantics. No concept has two independent sources of truth.

The portable core assumes only `SKILL.md` and relative resources. Host-specific runners, invocation controls, hooks, and permission adapters remain optional and cannot be required for claimed portable behavior.

## Evaluation and claims

Correctness is the first gate. Compare the candidate with the current accepted `forge-plan`, and with no Skill where informative.

The corpus covers:

- compact defaulting and explicit detailed requests;
- severe single-factor and cumulative moderate-factor recommendations;
- user override, late escalation, and unresolved-intent return;
- vertical slicing, cohesive wide refactors, and phase splitting;
- dependency/frontier correctness and progressive loading;
- compact packet closure and detailed traceability;
- conditional risk controls and independent-review routing;
- phase review closure, stalled loops, pauses, and commit authorization;
- stale-source conflicts, duplicate knowledge, ticket handoff, and planning/implementation separation;
- positive, negative, boundary, adversarial, regression, paraphrase, near-neighbor, competing-Skill, large-input, and failure-injection cases where applicable.

Keep trigger and execution cases separate. Validate the static corpus deterministically. Classify failures before attributing them to the Skill. Missing runtime or catalog preconditions are `UNMEASURED`; disputed known-good expectations require adjudication.

Measure per mode:

- correctness and material omission rate;
- implementation-blocking questions or rediscovery;
- requirement/invariant/acceptance coverage;
- dependency and scope errors;
- input/context tokens, output tokens, references loaded, tool calls, duration, retries, and errors;
- review blocking findings and implementation deviations.

Do not claim improved accuracy, token use, latency, or defect rate without repeated differential trials on representative compact and detailed work. Until then those live benefits remain `UNMEASURED`.

## Completion criteria

The design is satisfied when implementation preserves the shared Forge gates, selects and confirms planning depth from known evidence, loads only the chosen branch, produces closed dependency-correct work, routes risk-specific controls, stops after approved planning, and passes the relevant static, trigger, execution, and differential evaluations.
