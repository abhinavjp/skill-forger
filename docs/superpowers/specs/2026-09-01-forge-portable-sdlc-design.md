# Forge Portable SDLC Design

## Status

Approved in conversation on 2026-09-01. This document records the approved
design; it does not authorize implementation.

## Goal

Create a user-invoked, harness-agnostic Forge skill suite for clarification,
discovery, specification, planning, and implementation. Refactor the existing
Brain skills into thin project adapters that automatically use their matching
Forge core without duplicating portable workflow logic.

## Suite and boundaries

| Portable skill | Responsibility | Brain adapter |
|---|---|---|
| `forge-clarify` | Resolve unanswered or conflicting human decisions from an existing evidence/decision ledger | `brain-wave` |
| `forge-discover` | Gather sources, current behavior, affected functionality, risks, references, and open decisions | `brain-discover` |
| `forge-spec` | Produce an approved, testable behavioral contract | `brain-spec` |
| `forge-plan` | Produce a code-grounded plan a workhorse can implement without research, design, or questions | `brain-plan` |
| `forge-implement` | Execute approved task packets, prevent common quality failures, verify, and hand off | `brain-implement` |

All skills are user-invoked rather than model-invoked. A user invocation of a
Brain adapter authorizes that adapter to load its matching Forge core. Intent
controls chaining: a stage-only request stops at the stage boundary; a request
for the full workflow, or an unambiguous "proceed", authorizes continuation.

`ba-1` and `mr-review` are reference inputs only and are not changed.

## Artifact contract

An explicit caller-supplied work-item directory wins. Otherwise Forge uses:

```text
.forge/work-items/<stable-id-or-deterministic-slug>/
```

The directory may contain:

- `context.md`: verified current state, sources, impacts, references, risks.
- `decisions.md`: answered/open decisions with provenance.
- `spec.md`: approved behavioral contract.
- `design.md`: optional architecture/contracts for cross-system, security,
  migration, compatibility, or hard-trade-off work.
- `plan.md`: approved technical execution design.
- `tasks.md`: execution progress and commit mode.
- `evidence.md`: checks, revisions, deviations, and unmeasured coverage.
- `workflow.json`: stage state, normalized hashes, approvals, source freshness,
  and selected knowledge paths/hashes.

ADRs are created only for durable, surprising, hard-to-reverse choices reached
through a real trade-off. Use the project's ADR convention, falling back to
`docs/adr/`.

Natural approval language (for example, "proceed", "go ahead", or "continue")
counts when the pending artifact/action is unambiguous. Approval binds to a
normalized artifact hash. Normalization ignores line-ending differences,
trailing spaces, and repeated blank lines; it preserves meaningful indentation
and fenced-code whitespace. Meaningful edits invalidate approval.

Forge never changes `.gitignore`, commits artifacts, pushes, opens a PR, or
writes to an issue tracker without appropriate user authorization.

## Discovery and clarification

Issue-backed discovery inspects available field metadata and populated-field
presence, then fetches materially populated fields without placing raw `*all`
payloads in active context. It includes paginated comments, accessible
attachments, links, subtasks, parent/epic relationships, dependencies, custom
fields, and history. Persist only provenance plus materially used content by
default to limit size and PII exposure.

Current Jira fields and BA clarification comments/replies are current input.
History/changelog is supporting evidence; a history entry that changes a
requirement requires human confirmation.

Question suppression is automatic. Before asking, Forge inspects issue fields,
comments, BA output, context, decisions, and the current conversation. It uses
semantic equivalence rather than exact wording and generates stable decision
identities for persistence. It asks only when information is absent,
contradictory, stale, or materially ambiguous. Independent questions are asked
in one round.

Discovery covers actors, states, parallel paths, excluded/unassigned cohorts,
permissions, integrations, regressions, and edge/failure behavior. It checks
for screenshots/design references only when UI, visual parity, layout, copy, or
examples make them relevant. Missing references create a warning/risk and do
not automatically block work.

## Knowledge and token control

The portable suite supports an optional knowledge-provider contract and does
not require OKF. It reads a small routing index, selects candidates from task,
repository, paths, symbols, and changed hunks, and loads exact leaf knowledge.
It records selected paths, hashes, and conclusions so later stages reload only
stale/applicable knowledge.

The Brain adapter uses the existing OKF bundle. It validates the configured
bundle once before routing and avoids loading whole compatibility profiles when
granular files exist. If validation fails, it explains the exact impact and
asks whether the user wants the AI to repair the problem in the current work
item. If declined, work continues with reduced coverage marked `UNMEASURED`.

## Specification

`forge-spec` consumes approved discovery artifacts and defines exact actors,
states, inputs, outputs, permissions, errors, boundaries, changed/unchanged
behavior, impacted paths/cohorts, state semantics, constraints, non-goals,
acceptance scenarios, and traceability. It contains no unresolved user choice
and no non-binding technical design. Missing product decisions route through
clarification. Natural-language approval is required before planning.

## Planning

`forge-plan` reuses upstream conclusions and researches only implementation-
owned facts. It freezes architecture, reuse choices, interfaces, compatibility,
exact files/symbols, dependencies, checks, and risks. Each task is a closed,
dependency-ordered packet containing exact context, create/modify/delete intent,
canonical examples, ordered steps, required contracts, edge cases,
must-not-change boundaries, verification commands with expected results, and
developer-verifiable acceptance.

The plan includes signatures, schemas, pseudocode, or code sketches where they
freeze a decision the implementer could otherwise get wrong. It does not copy
obvious boilerplate or pre-write the whole implementation. Readiness criterion:
a competent workhorse can execute each packet using only the packet and cited
local files, without research, architecture selection, or user questions.

## Implementation

At start, `forge-implement` asks once for commit mode:

- `review-first`: no commits until the user inspects and authorizes.
- `per-task`: commit each verified packet.
- `end-only`: commit verified implementation once at completion.

It never auto-squashes. Push/PR remains separate authorization.

Implementation runs tasks in dependency order. Small/serial work stays with the
current agent; large independent slices may use bounded workhorses when the
harness supports them. Correctness never depends on delegation. Each task uses
only its packet and cited context, performs narrow deterministic verification,
and applies relevant prevention checks for design parity, reusable components
and styles, inappropriate inline CSS, duplication, constants, performance,
maintainability, security, permissions, tests, and diff scope.

After all tasks: run integrated deterministic verification, then one independent
semantic review where available. Fix only bounded findings and revalidate. Do
not repeat a full semantic review after every edit.

## Failure and completion

Preserve verified work. Retry only plausibly transient failures with bounded
attempts. Do not retry deterministic failures without changed state. A plan
contradiction stops the affected and dependent tasks; independent tasks may
continue. Required unplanned scope is reported for approval. Pre-existing
failures are evidenced, recorded, and not repaired automatically.

Missing mandatory safety/correctness validation is presented to the user for a
decision and never described as passing. Other unavailable checks are
`UNMEASURED`. Reruns resume verified state without duplicating artifacts,
decisions, commits, or side effects.

Completion requires observable requirement/task coverage, approved-scope diff,
actual verification results, current approval hashes, and an integrated result
consistent with spec, optional design/ADR, plan, and applicable knowledge.

## Portability

Forge cores use standard `SKILL.md` plus relative resources. They contain no
named models, agents, MCP servers, host invocation syntax, absolute paths,
hooks, or host-only frontmatter. Capabilities are generic and detected at
runtime. Missing optional capabilities degrade honestly. Host bindings stay in
adapters.

## Evaluation

Each package receives static inspection and portable JSON evals. Coverage
includes automatic context-aware question suppression, issue-field/comment
coverage, changelog confirmation, impact completeness, conditional reference
warnings, spec completeness, blind-workhorse plan readiness, implementation
quality prevention, knowledge routing/staleness, natural approval and
whitespace normalization, rerun/idempotency, commit modes, contradictions, and
capability degradation.

Measure explicit-invocation execution, historical Brain fixtures, Forge versus
current Brain behavior, Forge versus no-skill baseline, and token/tool/reference
cost. Host/model trials are separate; absent coverage is `UNMEASURED`.

