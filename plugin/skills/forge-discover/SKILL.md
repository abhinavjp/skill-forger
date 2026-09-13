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
- open human decisions, if any — do not resolve them here.

Done when: `context.md` exists with Goal first and the evidence below it.

## 3. Hand off

If step 2 found open human decisions, say so and point to forge-clarify. If
scope reduction or the Goal itself is materially unclear, say what is missing
and stop. Otherwise report that discovery is done and Specification can
proceed when the user calls forge-spec.

Done when: the user knows whether to run forge-clarify or forge-spec next.
