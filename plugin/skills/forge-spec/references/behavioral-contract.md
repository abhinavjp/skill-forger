# Behavioural Specification contract

Use this structure for `spec.md`. Keep the contract implementation-independent:
it records required observable behaviour and binding constraints, not a plan
for building it. The shared [workflow contract](../../../shared/forge/references/workflow-contract.md)
remains the sole source for approval, hash, freshness, check, retry, and resume
semantics.

## Required artifact shape

1. **Intent and boundary** — goal, in-scope outcomes, non-goals, and binding
   upstream constraints.
2. **Source basis** — consumed approved `context.md` and `decisions.md`, with
   material evidence, decision, selected-knowledge, and external-contract
   provenance.
3. **Behavioural landscape** — relevant actors, permissions, scenarios,
   inputs, outputs, data/state meanings, transitions, and existing behaviour.
4. **Behavioural requirements** — one testable statement per stable `REQ-###`
   identity. Preserve an ID when its meaning survives revision; retire rather
   than repurpose an ID when it does not.
5. **Rules and boundaries** — invariants; changed and unchanged behaviour;
   edge and failure outcomes; safety/security rules; NFRs; and external
   request, response, event, file, or dependency obligations.
6. **Acceptance and success** — scenario-based acceptance checks and the
   measurable conditions that show the Specification's intended outcome.
7. **Traceability** — each requirement and acceptance scenario mapped to its
   source basis and to the relevant intent, constraint, or invariant.

## Requirement record

For every meaningful requirement, use this compact record:

| Field | Content |
| --- | --- |
| ID | Stable `REQ-###` identity |
| Behaviour | Observable, unambiguous required outcome |
| Scope | Actor, state, input, output, and applicable boundary |
| Verification | Test, inspection, measurement, or acceptance scenario that can prove it |
| Sources | Approved context evidence, decision, knowledge leaf, or binding constraint |

Keep one behaviour per record when independent verification would distinguish
the outcomes. Reference an invariant or external contract by its named rule
rather than duplicating it into each requirement.

## Behavioural precision

Describe the result an observer receives, the state transition that is allowed
or prohibited, and the effect of malformed, absent, duplicate, unauthorized,
or failed inputs where material. State preserved behaviour explicitly so the
plan cannot accidentally broaden the change. An implementation mechanism is
included only when an upstream source makes it binding; label that source as the
constraint.

An acceptance scenario uses observable Given/When/Then conditions. A success
criterion is a measurable completion condition, not an aspiration. Traceability
must allow a reviewer to travel from a scenario to its requirement and source,
and from a source to every requirement it materially affects.

## Not-ready outcomes

Return not-ready rather than drafting around a material unresolved choice,
untestable statement, ambiguous preservation/change boundary, or non-binding
design instruction. Identify the affected source and requirement area, then
route the frontier to Discovery or Clarify. Specification neither decides that
frontier nor asks the human directly.
