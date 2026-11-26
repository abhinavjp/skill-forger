---
name: forge-prototype
description: Forge work item prototype step. Builds a disposable clickable UI for an open UX question in an existing `.forge` work item, logs it in the prototype ledger, and hands choices to forge-clarify. Not for generic quick prototypes or UI design.
---

# Forge Prototype

Optional stage. Runs when the user asks for it; no other skill runs it. Follow
the shared [workflow contract](../../shared/forge/references/workflow-contract.md)
for work-item identification, approval, stops, locations, and git rules.

## 1. Check the input

Identify exactly one work item (0 or 2+ matches: ask). With no `context.md`,
write nothing, say forge-discover must run first, and stop. Backfill nothing.
Read `context.md`, `decisions.md` if present, and any `spec.md`, screenshots,
existing UI, issue links, or example data. A missing prototype assessment does
not block. If it says "skip" and the user still wants one, record the limited
purpose in the ledger header.

Done when: one work item and the UX questions to answer are known.

## 2. Ask before the first file on a protected branch

Before the first file of either kind (ledger or `prototype/`), if the current
branch is protected, ask once whether to switch to a new branch. Say that
forge-implement will later run on and commit to that branch. Ask again in a new
session while the branch is still protected. Only the user's reply to this
question answers it.

- Yes: create and switch to a branch named by the repo's convention and verify
  it is current. On any failure, stop, report it, and touch no file.
- No: write on the current branch.

Unprotected branch: no question.

Done when: the branch is settled.

## 3. Build and record

Work in the repo's artifact location, else `.forge/<work-item>/`. Start with one
question and a minimal design; offer alternatives only for real tradeoffs.
Before building, read the [prototype contract](references/prototype-contract.md).

- `prototype/`: one disposable runnable folder.
- `prototype-decisions.md`: the ledger, written only by this skill. First line:
  `Non-binding. The binding record is decisions.md.`

```markdown
### P-001 — <specific interaction question>
- Scope: <actor / journey / screen / state>
- Alternatives: <materially different options; not manufactured>
- Observation: <what was shown or tested, understandable without opening the folder; evidence path; PASS | FAIL | UNMEASURED with reason>
```

`P-###` ids are local, sequential, never reused; there is no status field. A
changed answer gets a new entry; never rewrite one. A `P-###` with no
`decisions.md` record citing it is open. After a decision, a behaviour change
gets a new entry naming the recorded decision it may affect.

State comes from files: no assessment is unknown; an assessment with no ledger
is skipped or not started; any open `P-###` is pending; a ledger with none open
is decided.

Done when: the question has a runnable prototype and a ledger entry.

## 4. Review and hand off choices

Show the prototype and ask the question. "Looks good" means continue the
review: it picks nothing. Approving a prototype covers that artifact only, never
implementation, a commit, or a later stop. Never call a design approved because
you finished it, checks passed, or nobody objected.

When the user states a choice or drops a question, run
[forge-clarify](../forge-clarify/SKILL.md) inline: read its `SKILL.md` and
follow it with the candidate decision, its alternatives, and the `P-###`. Only
forge-clarify writes `decisions.md`. Say it recorded the choice only after
re-reading that file, then return here. If a choice conflicts with `spec.md`,
show both sides as a blocker; after clarify records the user's resolution, the
user re-invokes forge-spec.

Done when: the question is answered and recorded, or you have reported the
conflict, unusable environment, or failed check that blocks truthful progress.

Never commit or push; the user may commit these files by hand. Never edit
production source.
