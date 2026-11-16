# Change plan: simple Forge (plan -> implement fit)

Goal and decisions: [intent.md](intent.md). This file says **what to change, in what order**.

Base: `origin/main` @ 21505d0. Local `main` is behind. Start a new branch from `origin/main`.

## Why this change

- forge-implement reads `spec.md` + `tasks.md`. forge-plan makes `plan.md` (+ `phases/`). They do not fit.
- Approval uses hashes and a Python script. Many harnesses cannot run it. Users find it heavy.
- Skills are long and full of "do not". Normal models skim them.

## Rules for every edited file

- Short sentences. Simple words. Say what to do.
- "Do not" only for hard safety lines (never push, never touch other people's changes).
- Each step ends with "Done when: ...".
- One fact in one place. Skills point to shared files. They do not copy them.

## Order of work

Each step depends on the one before it.

### Step 1. Shared contract: remove gates, add shared rules

Files: `plugin/shared/forge/references/workflow-contract.md`, `plugin/shared/forge/scripts/workflow_state.py`, `plugin/shared/forge/tests/`, `plugin/shared/forge/evals/`.

Remove:
- Approval records, hashes, revisions, freshness, post-hoc mutation, approver policy.
- `can_enter_stage`, `_valid_approval`, `normalize_markdown`, `content_hash`, and their tests.

Keep:
- `PASS / FAIL / UNMEASURED` meaning.
- Retry rule (transient: limited retries; deterministic: retry only after a change).
- Blocked task blocks all tasks that depend on it.

Add (short, in the contract or new files under `references/`):
- **Lifecycle and backfill:** discover -> clarify -> spec -> plan -> implement. Missing input: run discover; run clarify only for open decisions; never auto-run spec. "Run a skill" = read its `SKILL.md` and follow it.
- **Approval:** the user's words ("go", "implement the plan") approve. Backfilled artifact: show it, ask "review or go?", wait.
- **Stops:** before each commit (per phase in detailed, before any commit in compact) and on blockers.
- **Locations:** existing convention wins; else `.forge/<work-item>/`, committed.
- **Git rules:** protected branch check, branch name suggestion, convention doc `docs/contributing/git.md` + pointer line.
- **progress.md format** (see Step 5).
- **Work item, high risk, blocker, stop, go, backfill, second reviewer:** use the terms in root `CONTEXT.md`.
- **One combined stop** for backfill (Goal, decisions with suggestions, mode, plan path).
- **Conflict rule:** artifacts disagree -> blocker; user decides; fix the losing file.
- **Phase gate** (moved here from `detailed-mode.md`, so plan and implement share one copy).

Decide in this step: does `workflow_state.py` still earn its place? If only `can_retry` and `block_dependants` remain, move them to plain text and delete the script. Scripts must be optional for any harness.

Done when: no file under `plugin/shared/forge` mentions approval hash, revision, or `can_enter_stage`; shared tests pass.

### Step 2. forge-discover: take the user's problem, write Goal

File: `plugin/skills/forge-discover/SKILL.md`.

- It is now the entry point. It takes the user's problem in their words.
- Write `## Goal` first in `context.md`: problem, outcome, done when, not in scope. Change Goal only when the user says so.
- Replace "does not interview people" with: ask only to fill Goal; send other human decisions to clarify.
- If open decisions exist, run clarify next.

Done when: context.md template starts with Goal; evals cover "no Goal -> ask".

### Step 3. forge-clarify and forge-spec: drop gate text

Files: both `SKILL.md` + evals.

- Remove approval, hash, and continuation-intent text. Point to the shared contract.
- clarify: runs when discover found open decisions, or when the user calls it.
- spec: runs only when the user calls it. Reads Goal from context.md.

Done when: no gate words remain; evals updated.

### Step 4. forge-plan: simplify, fix the handoff

Files: `SKILL.md`, `references/compact-mode.md`, `references/detailed-mode.md`, `references/execution-packet.md`, evals.

- SKILL.md steps 1-2 and 10 (authority, gate, hash, approval record): replace with "read Goal in context.md, decisions.md, spec.md if present; backfill per shared rule".
- Mode: always ask compact or detailed, with suggestion and reason. From implement: suggest compact, confirm. Risky item found later: ask again.
- Fixed packet headings (implement finds them by name): `## Outcome`, `## Write scope`, `## Must not change`, `## Changes`, `## Proof`, `## Depends on`.
- Commit policy: keep `commit_granularity` (task | phase | end). Remove `commit_approval` (always ask now). Keep `history_style`.
- Phase gate text: replace with a pointer to the shared copy.
- Default path `.forge/<work-item>/`. Match request to an existing Goal; 0 or 2+ matches -> ask.
- Mark each slice/phase `risk: low|medium|high` with size, risk, complexity reasons (same rule in both modes).
- Remove the 3 copies of `PAUSED / AWAITING_APPROVAL` text. End: show plan path, ask "review or go?".
- Cut SKILL.md body to about 60 lines.

Done when: plan output matches the headings implement reads; no gate words; evals pass.

### Step 5. forge-implement: rewrite

Files: `SKILL.md`, delete `references/commit-modes.md`, delete `references/quality-routing.md`, simplify `references/failure-recovery.md`, rewrite evals.

New SKILL.md (about 60 lines), steps:
1. **Find the plan** in `.forge/<work-item>/` (or repo convention). None: run forge-plan, ask "review or go?". Done when: user said go.
2. **Start record.** Create or read `progress.md`. List other people's uncommitted files as "not mine". Resume = first box that is not `[x]`. Done when: baseline written.
3. **Branch.** Protected branch: suggest a name (repo convention first) and create it at the first commit stop. Done when: branch is known.
4. **Do each ready task** (all `Depends on` done). Read only its packet. Stay inside `Write scope`. Write a file under `changed:` before editing it. Test first where the plan names a seam. Run its `Proof`. Write the result. Done when: box is `[x]` with PASS, or `[!]` with reason.
5. **Blockers stop the run:** plan vs code conflict, change outside scope, checks still failing after retries, a file that is "not mine". Mark `[!]`, mark tasks that depend on it, continue other ready tasks, then stop and report.
6. **Phase end (or end of compact plan).** Run the full checks once. Review the diff against Goal and plan. High-risk phase: another agent reviews; if none, ask the human. Fix, max 2 loops. Done when: checks PASS and no blocking finding.
7. **Stop before commit.** Show summary and `progress.md`. On go: stage only this work's files, commit (plan's granularity), write commit id. Never push.

progress.md format:

```markdown
# Progress: <work-item>
Branch: <name>   Not mine: <files or none>

## PHS-01 <title>
- [x] TSK-01 <title>
  - check: `npm test auth` -> PASS
  - changed: src/auth.ts
  - deviation: none
  - commit: abc1234
- [!] TSK-02 <title>
  - blocked: plan says X, code does Y
```

Done when: no mention of `tasks.md`, `evidence.md`, `review-first`, `per-task`, `end-only`, approval hash.

### Step 6. Evals

Remove gate cases (stale hash, self-approval, post-hoc approval, full-workflow intent).

Add implement cases:
- compact plan runs to one stop before commit
- detailed plan, 2 phases, stop after each phase
- no plan: runs plan, asks "review or go?", edits nothing before go
- resume from `progress.md` mid-phase: own `[~]` files treated as mine, proof re-run
- backfill shows ONE combined stop, not four
- Goal vs spec conflict: blocker, both lines shown
- 1-line auth change in compact plan: high risk, second reviewer
- request matches 2 work items: asks which
- dirty tree: other files untouched; stop when a task needs one
- plan vs code conflict: `[!]`, dependants blocked
- high-risk phase, no subagent: asks human
- protected branch: suggests name from convention; new convention -> asks to save to `docs/contributing/git.md`

Add plan cases: asks mode with suggestion; packet headings present; from implement suggests compact.

Add discover case: writes Goal first; asks when Goal missing.

Done when: all static and behavioral evals pass. Live model behavior = `UNMEASURED` until run.

### Step 7. Check and release

- Run skill-engineer inspection on all 5 skills (length, wording, portability).
- Update plugin version: **major bump** (approval model changed; old artifacts do not work).
- Release notes: what changed, how to move an old plan (put it in `.forge/<work-item>/`, add `progress.md`).

Done when: inspection clean, version bumped, notes written.

## Risks

| Risk | Effect | Guard |
| --- | --- | --- |
| No hash gate | Plan can change after "go" without notice | "Go" always means the plan as it is now. Implement reads plan at start of each phase. |
| Backfilled plan gets auto-approved | Code without a seen plan | Hard step: ask "review or go?" before any edit. Eval for it. |
| `.forge/` hidden folder | Reviewers miss plan in PR | PR description names the `.forge/<work-item>/` path. |
| Big change across 5 skills | Long branch, merge pain | Do steps in order; one commit per step. |
| Goal rewritten by fact refresh | Review checks against wrong goal | Rule: Goal changes only when user says so. Eval for it. |
