# Forge execution-packet contract

Use this readable structure for every task in `tasks.md`. It is a closed
execution packet: a competent workhorse can execute it using the packet and
the cited local context without new research, architecture selection, product
questions, or requirement interpretation. The shared
[workflow contract](../../../shared/forge/references/workflow-contract.md)
owns approval and mutation gate semantics; do not repeat them here.

```text
Task N — <outcome>

Objective
<One observable task outcome.>

Requirements
<Stable REQ-/INV-/constraint IDs, each with its planned handling.>

Dependencies
<Completed task IDs, required artifacts/contracts, or “None”.>

Write Scope
<Exact files and symbols to create, modify, delete, or move.>

Read / Reference Context
<Exact upstream artifact sections, repository paths/symbols, local rules, and
frozen decision records needed to perform this task.>

Implementation
<Ordered, concrete changes: interfaces, algorithms, data/config/migration,
compatibility/security handling, and the selected local patterns.>

Must Not Change
<Explicit preserved behaviours, untouched files/symbols, contracts, cohorts,
or compatibility boundaries.>

Narrow Verification
<Exact commands, tests, inspection, and expected result or evidence.>

Acceptance
<Observable proof that the listed requirements are satisfied.>

Checkpoint
<The authorized checkpoint action or the explicit no-commit condition.>
```

## Closure rules

- Name actual paths and symbols, not folders to investigate or “the relevant
  service.” State whether each target is created, modified, deleted, or moved.
- Cite the specific caller, contract, example, test, build target, and config
  that explains the chosen change. Summarize evidence; do not embed a raw
  research dump.
- Record a resolved meaningful alternative and why it was rejected when it
  affects implementation. A workhorse never chooses among material options.
- Give each requirement and invariant a packet mapping or an explicit
  no-change/protection mapping with verification. Do not lose unchanged
  behaviour in a generic “regression test” claim.
- Use real prerequisites to order packets. A contract, migration, fixture, or
  shared component precedes its consumers only when the dependency is real.
- Keep coupled work together when splitting it would force the workhorse to
  infer an interface or run a broad intermediate search. Do not create
  meaningless micro-steps.

## Reject before approval

Return the Plan to Planning when a packet says any equivalent of:

- “research which files or symbols are affected”;
- “choose the service, schema, protocol, or architecture”;
- “ask the user whether the requirement means X or Y”;
- “determine the test/build command”; or
- “interpret the Specification and implement it.”

Resolve the fact or choice in Planning. If it is an unresolved product decision
or a contradiction in the approved inputs, route it back to Specification or
Clarify rather than hiding it in a task.

## Decision-record thresholds

An approved `design.md` is an input only when a visual or interaction outcome
cannot otherwise be implemented and verified, or when that design is already
binding. An ADR is warranted only for a long-lived, cross-cutting,
hard-to-reverse, or multi-team decision. Reference the relevant record in
`Read / Reference Context`; do not create ceremony for a local reversible
choice.
