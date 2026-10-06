# Forge shared contract

Every Forge skill points here instead of copying these rules. Terms (work
item, high risk, go, stop, blocker, backfill, second reviewer) are defined in
root `CONTEXT.md` and used as-is.

## Lifecycle and backfill

Order: discover -> clarify -> spec -> plan -> implement. The user calls each
skill by name.

"Run a skill" means: read its `SKILL.md` and follow it. This works the same
whether the user typed the invocation or another skill is backfilling it.

If a skill needs an input that is missing:
- Always run forge-discover first. It writes the Goal.
- Run forge-clarify only if discover (or the current skill) found open human
  decisions.
- Never auto-run forge-spec. Plan and implement work from `context.md` and
  `decisions.md` when no `spec.md` exists.

## Approval

The user's own words are approval. "Go", "implement the plan", "looks good",
or similar means proceed. There are no hashes, approval records, or scripts
that decide this.

A backfilled artifact is shown once, with "review or go?", and the skill
waits. Going ahead before that answer is a bug, not a shortcut.

## Stops

Stop and wait for the user at:
- the one combined backfill stop (see below),
- before every commit,
- any blocker (see [Conflict rule](#conflict-rule) and CONTEXT.md's
  definition of blocker).

Never push. A "go" on one stop does not cover a later stop.

## One combined stop

When a skill backfills more than one thing before it can start, show all of
it in one message: the Goal, open decisions with suggested answers, the mode
chosen (compact/detailed), and the plan path if one exists. Ask once. Only
redo and re-show this stop if the user's answer changes the plan; otherwise
move on.

## Conflict rule

When `context.md`, `decisions.md`, `spec.md`, and the plan disagree, that is a
blocker. Show both sides plainly. The user decides which one is right. Fix the
file that was wrong; do not guess or split the difference.

## Locations

An existing repo convention for where Forge artifacts live wins. Otherwise use
`.forge/<work-item>/`, committed. `progress.md` is committed together with the
phase it records.

## Git rules

- Commit to the current branch unless it is protected (the default branch,
  `main`, `master`, `develop`, `release/*`, or host-protected). If protected,
  create and switch to a suggested branch name, then verify the current
  branch is actually the new one — a suggested name that is never created or
  switched to is not protection, it is a label. Do this before any file is
  touched, not only before the first commit. It happens automatically; it is
  not one of the listed [Stops](#stops). On failure to create, switch to, or
  verify the branch, stop and report the exact failure without touching any
  file or committing. Follow the repo's existing branch-naming convention if
  one exists.
- If the user gives a new naming convention, ask to save it (default:
  `docs/contributing/git.md`, with one pointer line in root `AGENTS.md` or
  `CLAUDE.md` if either exists) and say why: later agents and people use the
  same names.
- Never push.

## progress.md format

One `progress.md` per compact plan, and one per `phases/NN/` in a detailed
plan. Checklist per task:

```markdown
- [ ] TSK-01 <title>      # todo
- [~] TSK-02 <title>      # doing
- [x] TSK-03 <title>      # done
- [!] TSK-04 <title>      # blocked
  - check: <command> -> PASS | FAIL | UNMEASURED
  - changed: <files this task touched>
  - deviation: <what differed from the plan, or "none">
  - commit: pending | committed
- [x] GATE-FIX <phase or plan name>   # phase-gate fix loop, task granularity only
  - changed: <files the fix loop touched>
  - commit: pending | committed
```

`GATE-FIX` records a phase-gate fix-loop change made under
`commit_granularity: task`, where the change belongs to no single task.
It gets its own checkpoint (never folded into or amended onto a task's
commit) and follows the same `pending`/`committed` rule as a task. Under
`commit_granularity: phase` (or a compact plan), no `GATE-FIX` entry is
needed: the single end-of-phase checkpoint already covers fix-loop
changes together with everything else.

`commit` never holds a commit id: `progress.md` is committed together with
the phase (or task) it records, so the id does not exist yet when this file
is written and a commit cannot contain its own hash. `pending` means the
task is done but not yet committed; `committed` means the commit exists and
carries this line together with the task's changes in the same commit.

After creating that commit, its SHA is captured immediately and two checks
are verified against that exact SHA (never an assumed `HEAD`): the
changed-path set is exactly `progress.md` plus the checkpoint's files, and
the committed `progress.md` blob itself marks the right task(s)
`committed`. A commit that exists but fails either check is preserved
untouched — never reset, amended, reverted, or recommitted to fix it — and
reported for explicit recovery direction. `committed` in the worktree does
not by itself mean the checkpoint is trustworthy until both checks pass.
Find the actual id afterward with `git log` against `progress.md` or the
task's files, if needed.

Resume: the first box that is not `[x]` is where work continues. Files listed
under a task's `changed:` are that task's own files. Re-run that task's proof
on resume before trusting its state.

Also reconcile every `[x]` task's `commit:` field against git, not only the
first non-`[x]` box. `[x]` with `commit: pending` means a session stopped
before its checkpoint: return to the commit checkpoint for it, with a fresh
"go?", instead of skipping it. `[x]` with `commit: committed`: verify a
commit actually contains that exact `progress.md` state; if none does,
report the mismatch and stop rather than auto-fixing it.

List other people's uncommitted changes at the top of `progress.md` as
"not mine". Never edit, stage, or commit them.

## Checks

A check is exactly `PASS`, `FAIL`, or `UNMEASURED`. Only `PASS` counts as
passing. `UNMEASURED` always carries a reason and never satisfies a required
check.

## Retry

A transient failure may retry, up to a small fixed limit. A deterministic
failure may retry only after something relevant actually changed (code,
config, or environment) — not by repeating the same action. Do not retry a
failure you cannot classify; report it instead.

## Blocked task blocks dependants

If a task is blocked (`[!]`), every task that depends on it is blocked too.
Keep working on other ready tasks whose dependencies are still met; stop and
report once nothing else is ready.

## Phase gate

At the end of each phase (or at the end of a compact plan): run its checks,
then review the diff against the Goal and the plan. High risk needs a
second reviewer (root `CONTEXT.md`); with none available, ask the human
to review. Fix findings, re-run affected checks, and re-review — at most two
fix loops. If it still is not clean after that, stop and report to the user
rather than looping again. Stop before the commit that follows.
