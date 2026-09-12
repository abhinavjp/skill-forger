# Compact mode

Use after the user confirms `compact`. Create exactly one `plan.md`; create no
phase or task artifacts.

## Compact artifact contract

The plan is semantically closed and contains:

- outcome and the approved source basis, with path, revision, current content
  hash, provenance, and freshness result;
- scope, exclusions, preserved behaviour, and verified current state;
- frozen decisions and bounded assumptions; unresolved material decisions block
  approval and require an upstream return, scope reduction, or detailed mode;
- inline dependency-ordered vertical slices with exact write scope, relevant
  symbols, constraints, ordered changes, narrow proof, and expected results;
- observable acceptance, final integrated gates, and implementation handoff;
- commit policy defaulting to `commit_granularity: end`,
  `commit_approval: always_ask`, and `history_style: separate`.

## Vertical slices and dependencies

Keep each slice independently observable where the change permits it. Record
only real start-blocking edges and show the initial executable frontier. Do not
turn the compact plan into a list of repository layers or mechanical subtasks.

Include rollback, compatibility, security, observability, idempotency, manual,
live-provider, performance, migration, browser, hardware, or UAT material only
when verified risk requires it. Omit empty conditional sections.

Review the complete plan once for intent, behaviour, architecture, regression,
scope, and proof. Use the shared Forge workflow contract for artifact approval
and mutation boundaries. At completion, present the exact Plan path, revision,
and content hash as `awaiting-approval`; do not label that pre-approval hash an
approval hash. Planning ends only after a contract-valid artifact approval is
recorded, then stops.
