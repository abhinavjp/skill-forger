# Decision frontier

Build the frontier from only the current task scope: request/issue evidence,
approved artifacts, selected knowledge, repository evidence, and `decisions.md`.
Preserve each item's source, freshness observation, and scope instead of
copying raw payloads or conducting broad Discovery.

Classify every candidate before asking:

| Status | Treatment |
| --- | --- |
| Answered | Reuse a materially equivalent, current answer and cite it. |
| Evidence-answerable | Retrieve and reconcile the available evidence first. |
| Decision-ready | Ask the accountable human; include the decision, material options or consequence, and evidence gap. |
| Settled | Keep it closed. Reopen only for evidenced contradiction, staleness, or material scope change. |

Ask all independent `Decision-ready` items in one numbered round. Defer an item
whose options depend on another decision. Do not turn preference, policy, or
technical design choice into an assumed answer.

For each answer, append one `decisions.md` record: the decision, its scope,
who answered and their own words, and the supporting evidence. Note any
decision it supersedes. This is a plain record, not a gate: the user's words
are the approval (see the [shared workflow contract](../../../shared/forge/references/workflow-contract.md)).

Return one of: the grouped decision round; the recorded answer; or "no
unresolved human decisions." Then stop.
