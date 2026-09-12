# Compact mode

Use after the user confirms `compact`. Create one `plan.md`; create no phase or
task files.

The plan is semantically closed and contains:

- outcome and approved source basis, including provenance, approval hash, and
  freshness result;
- scope, exclusions, preserved behavior, and verified current state;
- frozen decisions and bounded assumptions; unresolved material decisions block
  approval and must return upstream, narrow scope, or escalate to detailed mode;
- dependency-ordered vertical slices with exact write scope, relevant symbols,
  constraints, ordered changes, and narrow proof with expected results;
- observable acceptance, final integrated gates, and implementation handoff;
- commit policy defaulting to `commit_granularity: end`,
  `commit_approval: always_ask`, and `history_style: separate`.

Include rollback, compatibility, security, observability, idempotency, manual,
live-provider, performance, migration, browser, hardware, or UAT material only
when verified risk requires it. Omit empty conditional sections.

Review the complete plan once for intent, behavior, architecture, regression,
scope, and proof. Do not request or record approval while a material decision is
unresolved. Planning ends after explicit approval.
