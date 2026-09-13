---
name: forge-implement
description: Run a Forge work item's approved plan against the code, one task or phase at a time.
disable-model-invocation: true
---

# Forge Implement

The user calls this to run a plan. Follow the shared
[workflow contract](../../shared/forge/references/workflow-contract.md) for
approval, stops, `progress.md` format, checks, retry, and the phase gate.

## 1. Find the plan

Look for a compact `plan.md` or a detailed `phases/` tree in `.forge/<work-item>/`
(or the repo's own convention). None found: backfill it by running
forge-plan (suggest compact mode) — and whatever forge-plan itself needs to
backfill first (discover always; clarify only for open decisions). Collect
the Goal, any open decisions with suggested answers, the mode, and the plan
path, then show all of it in one message and ask "review or go?" once, per
the shared contract's one combined stop. Edit nothing before that answer.
Re-show the stop only if the answer changes the plan.

Done when: you have one plan to run, and the user said go.

## 2. Start the record

Create or read `progress.md`. List any other person's uncommitted changes as
"not mine" at the top; never touch them. If the branch is protected, suggest
a name per the shared contract's git rules.

Resume: the first checklist box that is not `[x]` is where you continue.
Files under that task's `changed:` are yours; re-run its proof before
trusting its state.

Done when: `progress.md` has a baseline and you know where to start.

## 3. Do each ready task

A task is ready when everything in its `Depends on` is done. For each ready
task: read only its packet, write a file under `changed:` before editing it,
stay inside `Write scope`, leave `Must not change` alone, and run its `Proof`.
Test first where the plan names a seam. Record `PASS`, `FAIL`, or
`UNMEASURED` with a reason.

If the code and plan disagree, a needed change falls outside `Write scope`,
or checks still fail after retries: mark the task `[!]`, block its
dependants, keep working other ready tasks, then stop and report. See
[failure recovery](references/failure-recovery.md) for each case.

Done when: every ready task is `[x]` or terminally `[!]`.

## 4. Phase end (or end of a compact plan)

Run the shared [phase gate](../../shared/forge/references/workflow-contract.md):
full checks, review against the Goal and plan, second reviewer for high
risk (ask the human if none is available), at most two fix loops.

Done when: checks pass and no blocking finding remains, or you have stopped
to report one that does.

## 5. Stop before commit

Show the summary and `progress.md`. On go: stage only this work's files,
commit at the plan's `commit_granularity`, write the commit id into
`progress.md`. Never push.

Done when: the user said go and the commit is recorded, or they said no and
you stopped.
