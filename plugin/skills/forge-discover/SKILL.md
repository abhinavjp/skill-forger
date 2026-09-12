---
name: forge-discover
description: Use when Forge begins evidence-first discovery for a scoped change, issue, or request and needs verified current behaviour and functional impact before specification.
---

# Forge Discover

Produce a bounded, evidence-backed `context.md` for Specification. Discovery
reconciles what is known; it does not interview people, choose architecture, or
start a later stage. Follow the shared [workflow contract](../../shared/forge/references/workflow-contract.md)
for ownership, freshness, gates, retry, and continuation semantics.

## Gather only material evidence

Consume approved decisions plus available issue/source and selected knowledge
evidence. Establish current repository/product behaviour before describing
impact. For issue sources, inspect materially populated fields and follow only
comments, attachments, linked items, subtasks, parents, dependencies, and
requirement-changing history that can alter scope or behaviour. Preserve each
used item's locator, provenance, and freshness; use selected knowledge leaf
references only. Apply the [issue-source contract](../../shared/forge/references/issue-source-contract.md)
and [knowledge-provider contract](../../shared/forge/references/knowledge-provider-contract.md),
not transport-specific semantics.

Use [impact coverage](references/impact-coverage.md) to assess relevant actors,
states, paths, exclusions and cohorts, permissions, integrations, and
regressions. State why a relevant dimension is unaffected; omit dimensions that
are not material. Do not retain raw all-field payloads; retain a raw fragment
only when it is materially used and cannot be represented faithfully otherwise.

## Resolve evidence boundaries

Record an unreadable or missing source as unavailable evidence, with its reason
and effect on confidence, scope, or correctness; never treat it as empty or
successful. Preserve both sides of a material current/history conflict and its
provenance. Add the affected unresolved human decision to the frontier for
[forge-clarify](../forge-clarify/SKILL.md); do not ask it directly.

For UI work, inspect screenshots or visual references only when they can affect
the requested UI outcome. A missing relevant visual is a warning unless it
prevents correctness verification; unrelated visual material is out of scope.

## Write `context.md`

Write a concise, revisit-able record with these sections:

1. Scope and consumed approved decisions.
2. Evidence ledger and verified current behaviour.
3. Functional-impact coverage and affected surfaces.
4. Material relationships and requirement-changing history.
5. Unavailable evidence, freshness observations, and visual-reference status.
6. Material conflicts and the decision frontier routed to Clarify.
7. Verification results as `PASS`, `FAIL`, or `UNMEASURED`, with reasons.

Stop when this context is bounded enough for Specification. Do not repeat
settled questions or infer a human decision from incomplete evidence.
