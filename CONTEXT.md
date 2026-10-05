# Forge glossary

**Work item** — one piece of user-requested change with one Goal and one outcome. It has a short name (slug) shared by its artifacts, branch, and commits. A new request whose Goal matches an existing work item belongs to it; otherwise it is a new work item.

**High risk** — a slice or phase where any one of size, risk, or complexity is high, or two are medium. Risk is high when the change touches authentication, permissions, secrets, personal data, payments, data loss or migration, or is hard to undo. A small change can be high risk.

**Goal** — the user's own statement of a work item's problem, outcome, done-when, and not-in-scope. Only the user changes it.

**Go** — any user reply that means "proceed". Go on a shown artifact is its approval. Go never covers a later stop.

**Stop** — a point where the skill waits for the user: the combined check before code, before each commit, or at a blocker.

**Blocker** — something only the user can resolve: artifacts that disagree, plan that does not match the code, a change outside write scope, a file changed by someone else, checks still failing after retries, or high-risk work with no second reviewer.

**Backfill** — running an earlier stage because its artifact is missing. Backfilled results are shown at one combined stop.

**Second reviewer** — any reviewer that did not write the change: another agent with fresh context, or a human.
