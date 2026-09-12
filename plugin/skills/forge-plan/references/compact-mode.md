# Compact mode

Use after the user confirms `compact`. Create one `plan.md`; create no phase or
task files.

The plan is semantically closed and contains:

- outcome and approved source basis, including provenance, approval hash, and
  freshness result;
- scope, exclusions, preserved behavior, and verified current state;
- frozen decisions, assumptions, and unresolved blockers;
- dependency-ordered vertical slices with exact write scope, relevant symbols,
  constraints, ordered changes, and narrow proof with expected results;
- observable acceptance, final integrated gates, and implementation handoff;
- commit policy defaulting to `commit_granularity: end`,
  `commit_approval: always_ask`, and `history_style: separate`.

Include rollback, compatibility, security, observability, idempotency, manual,
live-provider, performance, migration, browser, hardware, or UAT material only
when verified risk requires it. Omit empty conditional sections.

Review the complete plan once for intent, behavior, architecture, regression,
scope, and proof. Planning ends after explicit approval.
