# Compact mode

Use after the user confirms `compact`. Create exactly one `plan.md`; no phase
or task files.

## Compact plan contract

The plan is self-contained:

- outcome and the source it is based on (`context.md` Goal, `decisions.md`,
  `spec.md` if present);
- scope, exclusions, and preserved behaviour;
- dependency-ordered vertical slices, each with the six packet headings from
  [execution packets](execution-packet.md) and a `risk:` label;
- observable acceptance and the final check;
- `commit_granularity: end` and `history_style: separate` unless the repo's
  convention says otherwise.

## Vertical slices and dependencies

Keep each slice independently observable where the change allows it. Record
only real start-blocking edges. Do not turn this into a list of repository
layers.

Include rollback, compatibility, security, observability, or migration
material only when a real risk in this change needs it. Omit sections that
would be empty.

End by showing the exact path and asking "review or go?" — see the shared
[workflow contract](../../../shared/forge/references/workflow-contract.md)
for what counts as approval.
