---
name: forge-spec
description: Turn a Forge work item's Goal and decisions into a testable behavioural spec.
---

# Forge Spec

Runs when the user calls it or the host selects it; never auto-run this from
another skill. Read the Goal and evidence in `context.md` and any
`decisions.md`. Follow the shared
[workflow contract](../../shared/forge/references/workflow-contract.md) for
approval and the conflict rule.

## 1. Read the source

Read the Goal in `context.md`, its evidence, and `decisions.md`. Keep a
settled decision unless the evidence you read shows it is now stale or
contradicted; if so, that is a conflict — apply the shared contract's
conflict rule instead of picking a side yourself.

If `prototype-decisions.md` exists, every `P-###` that no `decisions.md` record
cites is an open decision: report not-ready and route to forge-clarify.

Done when: you know what is settled and what still needs Clarify.

## 2. Write `spec.md`

Use [the behavioural contract](references/behavioral-contract.md) for shape.
Turn the Goal and decisions into observable, testable requirements
(`REQ-###`), not a technical design: no endpoint, class, function, or
algorithm unless the source made it a binding constraint.

For a prototype-backed choice, write the requirement from the decision text and
cite that decision as its source. Read the ledger Observation for context only;
it is never a source. Do not import prototype-only styling or accidental
behaviour. A record of a dropped question yields no requirement.

Done when: every requirement is observable, testable, and traced back to the
Goal, a decision, or evidence.

## 3. Check readiness

Not ready when a material decision is still open, a requirement cannot be
tested, or the boundary between changed and unchanged behaviour is unclear.
Say exactly what is missing and point to forge-clarify; do not guess the
missing behaviour yourself.

Done when: `spec.md` is ready for forge-plan, or you have named the gap and
where to resolve it.
