---
name: forge-plan
description: Use when Forge has a current approved Specification and needs an implementation-ready technical Plan before any source-code implementation begins.
---

# Forge Plan

Own `plan.md` and `tasks.md`: turn an approved behavioural Specification into
dependency-ordered, closed execution packets. Planning decides the technical
how; Implementation executes those frozen decisions. Follow the shared
[workflow contract](../../shared/forge/references/workflow-contract.md) for
artifact ownership, state eligibility, approvals, hashes, freshness, checks,
retries, resume, and mutation boundaries.

## Enter only through the Specification gate

Before Planning, confirm that the exact consumed `spec.md` revision is current
and validly approved when the workflow requires Specification approval. Confirm
its material input provenance and freshness remain valid, then consume the
relevant approved Discovery `context.md` and `decisions.md`. A missing, stale,
unauthorized, self, post-hoc, or otherwise unproven approval leaves Planning
blocked-at-gate; report the missing evidence and do not draft a Plan.

A full-workflow request may reach Planning only if the shared workflow says the
stage is eligible. It is not approval of `spec.md` or of a Plan created later.
Use an optional approved `design.md` only when it is material to the specified
outcome; retain its provenance and do not turn a non-binding visual suggestion
into product behaviour. Reuse the Discovery record before looking for new
evidence. Apply the [issue-source contract](../../shared/forge/references/issue-source-contract.md)
and [knowledge-provider contract](../../shared/forge/references/knowledge-provider-contract.md)
when their selected evidence is material.

## Research and freeze the technical solution

Planning owns repository-grounded technical research that Discovery did not
need: find the exact create, modify, delete, or move targets; symbols and
callers; interfaces and contracts; canonical local examples; tests; build,
package, configuration, migration, compatibility, and security mechanisms.
Inspect only enough repository evidence to close the execution surface. Cite
compact conclusions and local evidence locations; do not paste raw research
into the Plan.

Resolve material technical choices before packet creation: architecture and
reuse seams, meaningful alternatives, data or API compatibility, failure and
security mechanisms, test strategy, and dependency order. Select and record
the rationale and rejected alternative when a choice materially affects the
execution surface. Do not ask the user for technical facts Planning can find.
If a product behaviour, scope, or binding constraint is actually missing or
contradictory, do not invent it: return the affected frontier to Specification
or [forge-clarify](../forge-clarify/SKILL.md).

Use an optional `design.md` only when a material visual or interaction outcome
cannot be implemented and verified from `spec.md`, approved context, and
repository evidence alone, or when an approved design is already a binding
input. A design is not required for backend-only work or for UI changes whose
required outcome is already testable from those inputs. Record an ADR only for
a decision with long-lived, cross-cutting, hard-to-reverse, or multi-team
consequences; keep local, reversible implementation choices in the Plan.

## Write an executable Plan

Write `plan.md` with the consumed artifact revisions, source basis, frozen
technical decisions, exact change surface, dependency graph, requirement and
invariant traceability, and readiness result. Preserve upstream stable IDs
(such as `REQ-###`, decision IDs, and invariants); add plan-local IDs only for
new planning records and never reinterpret an upstream ID.

Map every material requirement and invariant to one or more implementation
packets, or to an explicit no-change/protection decision with verification.
Order packets by actual file, contract, migration, and test dependencies—not
by narrative convenience. Keep a small change a small packet; combine coupled
changes whose correctness depends on one another. A packet may cite local
context, but must not require broad rediscovery, product interviews,
architecture selection, or technical research by its workhorse.

Use [the execution-packet contract](references/execution-packet.md) verbatim
for every task in `tasks.md`. Do not require delegation, a semantic review for
each task, or full production code in a packet. Include code only when it is
the smallest reliable way to freeze a meaningful interface, algorithm, or
compatibility decision.

## Readiness and approval boundary

Before presenting the Plan, check Specification coverage, invariant
protection, exact change surface, dependency order, hidden technical choices,
packet scope, narrow verification, observable acceptance, duplicated context,
unresolved research, and cross-packet contradictions. Repair every planning
defect found. A packet is not ready if its workhorse would need to research a
technical fact, choose an architecture or meaningful alternative, find its
change surface, ask a product question, or reinterpret an upstream requirement.

Present the exact completed `plan.md` and `tasks.md` revision as
`awaiting-approval`. Planning may finish during an authorized full workflow,
but it remains non-mutating for source and implementation artifacts while
technical/Plan approval is pending. Only the shared workflow contract can
recognize a valid, independent, artifact-specific approval for that exact Plan
revision. Stop before Implementation unless that approval is already valid.
