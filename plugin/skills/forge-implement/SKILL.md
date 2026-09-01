---
name: forge-implement
description: Use when Forge has current approved Specification and Plan artifacts with closed execution packets that must be implemented safely.
---

# Forge Implement

Execute approved `tasks.md` packets; do not plan them. The shared
[workflow contract](../../shared/forge/references/workflow-contract.md) and
`workflow_state.can_enter_stage` own approval, freshness, retry, blocking,
resume, and check semantics. This Skill owns only implementation-stage
orchestration and its evidence.

## Gate before every implementation mutation

Start read-only. Before a source-code or implementation-artifact write, obtain
the current artifact contents and state, then require all of the following:

- the exact current `spec.md` revision/hash has its required valid approval;
- the exact current `plan.md` revision/hash has valid technical/Plan approval;
- `tasks.md` records correspondence to that exact approved Plan revision/hash;
- any adapter implementation approver policy is supplied to the shared gate
  decision and is satisfied; and
- neither approval nor a materially used input is stale.

Call the shared implementation gate decision; do not recreate its rules. It
rejects missing, stale, unauthorized, self, full-workflow, `implement`-intent,
and post-hoc approvals. “Implement this using Agentic SDLC” and any other
full-workflow request are continuation intent, never artifact approval. An
adapter may narrow acceptable approvers; it cannot open or weaken a gate.

If any condition is absent, mismatched, unproven, or denied, transition to
`blocked-at-gate`, remain read-only for source and implementation artifacts,
and report the exact missing or invalid evidence. Do not begin a packet, choose
a workaround, or seek approval after mutation. A recorded prior mutation with
later approval is `GATE_VIOLATION`, not retroactive success.

When every condition holds, transition to `implementation-active`. Capture the
pre-existing working-tree baseline before the first packet: paths, staged or
unstaged state, untracked paths, and relevant hashes. Those paths are external
scope. Never edit, stage, clean, claim, commit, or deliver them without
separate authorization.

## Establish execution controls once

Select or confirm one configured commit mode before packet writes. If no mode
is configured or authorized, ask for that choice while preserving the gate and
working tree; do not silently choose. Apply
[commit modes](references/commit-modes.md) exactly. A commit checkpoint is not
delivery authorization: never automatically push, squash, open a pull request,
or merge.

For each recorded check use exactly `PASS`, `FAIL`, or `UNMEASURED` through the
shared check record. `UNMEASURED` includes a reason and is never passing
evidence. Record the baseline separately from failures caused by this work.

## Execute closed packets

1. Use the dependency graph and verified state to select a dependency-ready,
   unblocked packet. Read only its `Read / Reference Context`, exact write
   scope, frozen decisions, and verification. Expand context only when concrete
   evidence contradicts a stated packet fact; record why and what expanded.
2. Keep every edit inside the packet scope and preserve its `Must Not Change`
   protections. Implement the frozen solution without research, architecture
   selection, user interviews, or replanning.
3. Run the packet's narrow verification and only the concern-specific guidance
   in [quality routing](references/quality-routing.md). Record every run and
   result. Do not invent a pass for an unrun or unavailable check.
4. Mark a packet verified only when its required evidence is `PASS`; apply its
   selected authorized checkpoint mode. Failed, blocked, or `UNMEASURED`
   required work is excluded from every commit.

If evidence shows that the Plan is contradictory or cannot meet a binding
requirement, stop that packet and every transitive dependant using the shared
blocking semantics. Record the contradiction and route the affected frontier
to Planning, Specification, or Clarify as appropriate; do not replan in place.
Continue only safe independent packets whose gates, dependencies, and scopes
remain valid.

If a required change lies outside the packet, stop the affected packet before
that write and request explicit scope authorization. Treat a material change as
an approved-Plan/SPEC revision and gate concern when it changes their approved
meaning. Do not silently broaden the diff. Apply
[failure recovery](references/failure-recovery.md) for failures, retries,
unavailable checks, and resume.

## Integrate once, review once, report compactly

After every packet is verified or terminally failed/blocked, run the approved
integrated deterministic verification over the verified scoped result. Record
each result exactly; separate pre-existing failures. Then perform exactly one
final semantic review against the approved Specification, Plan, packets,
scope, and shared contracts. This is distinct from per-packet narrow checks or
review-first diff review.

If that one review finds defects, create a bounded remediation list containing
only its findings. Remediate only that list, rerun affected checks and
integration when the finding affects integration, and do not run another
semantic review. Do not claim complete if required evidence remains `FAIL` or
`UNMEASURED`.

Write compact `evidence.md`: artifact revisions/hashes and gate decision;
adapter policy result; dirty baseline; selected commit mode and checkpoints;
packet status, scoped paths, checks, retries, blocks, and scope decisions;
integrated results; semantic-review count/result; remediation; pre-existing
failures; `UNMEASURED` reasons; and delivery actions explicitly not performed.
It is a handoff, not a replay of reasoning.
