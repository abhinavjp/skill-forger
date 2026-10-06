# Failure recovery

Use the shared contract's check, retry, and blocked-task rules. Preserve
evidence; never hide a failure by widening scope, rewriting history, or
relabeling it as passing.

| Event | What to do |
| --- | --- |
| A task's proof fails | Record `FAIL`. Leave it out of the commit. Diagnose only inside that task's write scope. |
| A pre-existing check fails, unrelated to this work | Record it separately as baseline, not this task's failure. |
| Transient failure | Retry, up to the shared contract's small fixed limit. |
| Deterministic failure | Retry only after something relevant actually changed. |
| Unclassifiable failure | Do not retry. Report it as `FAIL` or `[!]`. |
| Plan and code disagree | Mark `[!]`, block dependants, stop that line of work, and say what disagreed. |
| A check cannot run | Record `UNMEASURED` with a reason. It never satisfies a required check. |
| Resuming | Re-read `progress.md`, the plan, and the working tree. Start at the first box that is not `[x]`; re-run its proof before trusting it. |

After a block, keep only what the user needs to decide next. Never
auto-revert, auto-clean, push, or open a pull request.
