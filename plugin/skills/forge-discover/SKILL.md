---
name: forge-discover
description: Start a Forge work item from the user's own problem statement, writing its Goal and gathering the evidence Specification will need.
disable-model-invocation: true
---

# Forge Discover

The user calls this to start a work item. Follow the shared
[workflow contract](../../shared/forge/references/workflow-contract.md) for
lifecycle, backfill, stops, and locations.

## 1. Take the problem in the user's words

Ask only what is needed to write the Goal: the problem, the wanted outcome,
what "done" looks like, and what is out of scope. Do not interview the user
beyond this — send any other open human decision to
[forge-clarify](../forge-clarify/SKILL.md) instead of asking it here.

Name the work item slug from the request. Match it against any existing
`.forge/<slug>/` before creating a new one; 0 or 2+ matches means ask which
work item this is.

Done when: you can write the Goal in the user's own words.

## 2. Write `context.md`

Start the file with:

```markdown
## Goal
Problem: <what is wrong or missing>
Outcome: <what should be true instead>
Done when: <observable completion condition>
Not in scope: <explicitly excluded>
```

Only the user changes the Goal once written. A later run of this skill (a
fact refresh) may add or correct evidence below it, but leaves the Goal
untouched unless the user says to change it.

Use [impact coverage](references/impact-coverage.md) to check which actors,
states, paths, permissions, integrations, and regressions the change touches.

Below the Goal, record:
- current repository/product behaviour relevant to the Goal;
- evidence used, with enough locator to revisit it;
- anything unavailable or unreadable, and its effect;
- open human decisions.

A decision is open unless the Goal's own words settle it. It stays open even
if it seems implied, a sensible default exists, or the Goal covers something
related but not this exact point. "Done when a guest can complete checkout
on mobile" does not by itself settle a cart-cap, error-copy, or rate-limit
choice for guests — each of those is still open. If closing something
required you to infer, assume, or pick "the obvious answer," it was open:
list it, do not resolve it here. When unsure, list it as open.

Done when: `context.md` exists with Goal first and the evidence below it, and
every choice you had to infer rather than read directly from the Goal is
listed as an open decision, not silently assumed.

## 3. Close open decisions

If step 2 found open human decisions, run [forge-clarify](../forge-clarify/SKILL.md):
read its `SKILL.md` and follow it. After each round it records answers in
`decisions.md` and reports either the next ready round or "no unresolved
human decisions." Run it again while any decision remains open — including
one a prior answer only just unblocked — until it reports none left.

If the Goal itself is materially unclear in a way no decision round can fix,
say what is missing and stop instead of looping.

Done when: forge-clarify reports no unresolved human decisions, or you have
stopped and said why you could not get there.

## 4. Hand off

Report that discovery is done and Specification can proceed when the user
calls forge-spec.

Done when: the user knows forge-spec is next.
