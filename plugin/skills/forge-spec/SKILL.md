---
name: forge-spec
description: Use when Forge has approved Discovery context and decisions and the current eligible stage is Specification before planning.
---

# Forge Spec

Own `spec.md`: turn approved Discovery facts and decisions into a concise,
plan-ready behavioural contract. Specification defines what must be observably
true; Planning chooses how work is organized. Follow the shared [workflow
contract](../../shared/forge/references/workflow-contract.md) for artifact
ownership, gates, approvals, hashes, freshness, checks, retries, and resume.

## Establish the contract boundary

Consume only approved `context.md` and `decisions.md`. Preserve settled
decisions unless the consumed evidence demonstrates a contradiction, staleness,
or authorized scope change. Use the [issue-source contract](../../shared/forge/references/issue-source-contract.md)
and [knowledge-provider contract](../../shared/forge/references/knowledge-provider-contract.md)
when their provenance is material to a requirement.

Convert the approved inputs into observable requirements and binding
constraints. A requirement says what an actor, system, or external party can
observe and how it can be verified; keep the upstream source and decision that
justify it. Treat a technology, architecture, endpoint, file, class, function,
database, queue, or algorithm as out of the contract unless it is an explicit
binding upstream constraint. Do not interview the user from this stage.

## Write `spec.md`

Use [the behavioural contract](references/behavioral-contract.md) as the
artifact shape. Cover every material section and state why an apparently
relevant dimension is unchanged or out of scope. Give every meaningful
requirement a stable `REQ-###` identity; retain its identity across revisions
when its meaning is unchanged, and never reuse a retired identity for a
different meaning.

Each requirement, invariant, edge/failure outcome, NFR, safety rule, and
external-contract obligation must be observable and testable. State the
existing behaviour and expected behavioural delta separately, including what
must remain unchanged. Trace every requirement and acceptance scenario to the
approved context evidence, decisions, selected knowledge, or binding
constraint that makes it necessary.

## Decide readiness

The Specification is not ready when a material behavioural decision remains
unresolved, a requirement is not testable, changed or unchanged behaviour is
ambiguous, or the contract contains non-binding technical design. Report it as
not-ready and route the affected frontier to Discovery or
[forge-clarify](../forge-clarify/SKILL.md); do not choose the missing behaviour
or technical mechanism.

When ready, present the exact `spec.md` revision and enter `awaiting-approval`.
Creating or revising the artifact never approves it. Only the shared workflow
contract can recognize a valid, artifact-specific approval for the exact
revision and content; full-workflow intent cannot open this gate. Stop at that
gate unless that contract already proves the current revision approved.

Hand approval language and content comparison to that shared binding. An
unambiguous, authorized natural-language approval may bind a clearly presented
pending revision only when the shared contract validates it. The shared binding
also owns the distinction between formatting noise and meaningful whitespace;
Specification adds no parallel comparison rule.
