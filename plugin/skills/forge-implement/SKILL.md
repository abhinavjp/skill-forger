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
forge-plan — and whatever forge-plan itself needs to backfill first
(discover always; clarify only for open decisions). Let forge-plan's own
seven-factor assessment choose compact or detailed; do not preset or
suggest a mode. Collect the Goal, any open decisions with suggested
answers, the chosen mode with forge-plan's reason, and the plan path, then
show all of it in one message and ask "review or go?" once, per the shared
contract's one combined stop. Edit nothing before that answer. Re-show the
stop only if the answer changes the plan.

Done when: you have one plan to run, and the user said go.

## 2. Start the record

Create or read `progress.md`. List any other person's uncommitted changes as
"not mine" at the top; never touch them. If the branch is protected (per the
shared contract's git rules): create the suggested branch, switch to it,
and verify the current branch is now that branch — before any file is
touched. This happens automatically as part of starting the record, not as
a separate "go?" stop. On any failure to create, switch to, or verify the
branch, stop and report the exact failure; touch nothing and commit
nothing.

Resume: the first checklist box that is not `[x]` is where you continue.
Files under that task's `changed:` are yours; re-run its proof before
trusting its state. Then reconcile every `[x]` task's `commit:` field
against git, not only the first non-`[x]` box:

- `[x]` with `commit: pending` means a session stopped before its
  checkpoint. Return to step 5's commit checkpoint for it, with a fresh
  "go?", instead of silently moving on to the next task.
- `[x]` with `commit: committed`: verify that some commit actually
  contains that exact `progress.md` state. If none does (a crash between
  marking and committing), report the mismatch and stop — do not re-run
  the checkpoint or otherwise auto-fix it.

Done when: `progress.md` has a baseline, every `[x]` task's `commit:`
field is reconciled against git, and you know where to start.

## 3. Do each ready task

A task is ready when everything in its `Depends on` is done. For each ready
task: read its packet plus the `phase.md`/`plan.md` facts it points to (its
own phase's control-plane invariants and scope — leave unrelated phases
unloaded), write a file under `changed:` before editing it, stay inside
`Write scope`, leave `Must not change` alone, and run its `Proof`. Test
first where the plan names a seam. Record `PASS`, `FAIL`, or `UNMEASURED`
with a reason.

If the code and plan disagree, a needed change falls outside `Write scope`,
or checks still fail after retries: mark the task `[!]`, block its
dependants, keep working other ready tasks, then stop and report. See
[failure recovery](references/failure-recovery.md) for each case.

When the plan's `commit_granularity` is `task`, a passed task is its own
commit checkpoint: run step 5 now, before starting the next ready task.

Done when: every ready task is `[x]` or terminally `[!]`.

## 4. Phase end (or end of a compact plan)

Run the shared [phase gate](../../shared/forge/references/workflow-contract.md):
full checks, review against the Goal and plan, second reviewer for high
risk (ask the human if none is available), at most two fix loops.

Done when: checks pass and no blocking finding remains, or you have stopped
to report one that does.

## 5. Commit checkpoint

One checkpoint per task when `commit_granularity: task`; one at phase end
(or at the end of a compact plan) otherwise. Show the summary and
`progress.md`, and ask "go?" — never commit without asking. On go:

1. Mark this checkpoint's task(s) `commit: pending` -> `commit: committed`
   in `progress.md`, and stage this checkpoint's files together with that
   updated `progress.md`.
2. Create the commit.

**Before the commit exists:** if updating `progress.md`, staging, or the
commit command itself fails, restore `commit: pending` in `progress.md`.
Report the staged `committed` copy as evidence — the worktree and the
index must not quietly disagree — and report the exact failure. Claim
zero commits. Do not retry automatically: a fresh "go?" restarts the
transaction from step 1 and re-stages it.

**After the commit exists:** capture its SHA immediately. Verify against
that exact SHA, never an assumed `HEAD`: the commit's changed-path set is
exactly `progress.md` plus this checkpoint's files, with no unrelated
file added or missing; and the committed `progress.md` blob marks
exactly this checkpoint's task(s) `commit: committed` (never the
commit's own id — see the shared contract's `progress.md` format for why
the field holds `committed`, not a hash).

**If that SHA-bound verification fails:** the commit already exists, and
preserving it is not optional. Keep the commit and the working tree
exactly as they are — no `reset`, `amend`, `revert`, recommit, or other
rewrite of `progress.md` or history. Report the SHA, the expected
files/status, the observed files/status, and the exact mismatch, then
stop and wait for explicit recovery direction. A plain "go?" does not
authorize touching a commit that already exists.

Report the checkpoint as recorded only once both SHA-bound checks pass.
Never push.

Done when one of three distinct end states holds: the checkpoint is
recorded with both SHA-bound checks verified; no commit exists and
`progress.md` still reads `pending`; or a commit exists, unverified,
preserved untouched, and you have stopped for the user's recovery
direction.
