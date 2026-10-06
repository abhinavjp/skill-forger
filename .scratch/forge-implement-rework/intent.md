# Intent: forge-implement runs what forge-plan makes

## Problem
forge-plan changed. It now makes a compact `plan.md` or a detailed tree
(`plan.md`, `phases/NN/phase.md`, task files). forge-implement still expects
`spec.md` + `plan.md` + `tasks.md` and its own commit modes. So the plan cannot
be implemented. Also the skill is long, full of "do not", and hard for a normal
model to follow.

## Outcome
Any workhorse model, in any harness, can take an approved forge-plan and:
1. check the gate,
2. do the work slice by slice (or phase by phase),
3. prove each step,
4. stop at the right points,
5. leave a clear record to resume or review.

## Users
- Implementor: a normal coding model, maybe no subagents, maybe no Python.
- Human owner: approves plan, answers pause menus, approves commits.
- Reviewer: another agent or person for high-risk phases.

## Must have
- Read both plan shapes: compact and detailed. Load one phase at a time.
- No plan: run forge-plan (compact), ask "review or go?", edit nothing before "go".
- Follow plan's commit granularity. Ask before every commit. No second commit setting.
- Per task: narrow proof. TDD where plan names a seam.
- Detailed: per phase run checks + review (max 2 fix loops), then stop before commit.
- High risk / security / data / migration: review by someone other than the writer (see decision 4).
- Write status and proof to `progress.md`. `PASS / FAIL / UNMEASURED` only.
- Protect pre-existing changes. Stay inside write scope.
- Plan vs reality conflict: stop affected work, send back to planning.

## Not in scope
- Planning, spec, or design choices during implementation.
- Push, PR, merge, deploy, release, tracker updates.
- Nothing else in the shared contract beyond removing hash/approval gates (decision 2).

## Constraints
- Simple English. Short sentences.
- SKILL.md body about 60 lines. Steps end with a clear "done when".
- Say what to do; use "do not" only for hard safety lines.
- One source of truth: contract rules stay in the shared contract; packet format stays in forge-plan.

## Done when
- Evals pass for: compact plan, detailed plan (2 phases), no plan (backfill + ask),
  no subagent harness, high-risk phase in single-agent harness,
  plan/reality conflict, resume mid-phase from progress.md, dirty working tree, stop before commit.
- No reference to `tasks.md`, `evidence.md`, `review-first`, `per-task`, `end-only`, approval hashes remains.
- forge-plan names the `progress.md` fields and fixed packet headings implement reads.

## Decisions (grill session, 2026-09-13)
1. **Lifecycle.** discover -> clarify -> spec -> plan -> implement. The user calls each skill.
   If an input is missing, the skill reads the earlier skill's SKILL.md and runs it first.
   forge-implement with no plan runs forge-plan (compact), then asks "review or go?".
2. **Approval = user's words.** "Go", "implement the plan", or similar = approval. No hashes,
   no approval records, no script gates. Applies to all Forge skills. Remove the gate parts of the
   shared contract and `workflow_state.py`. Keep `PASS / FAIL / UNMEASURED`.
3. **Stops.** Detailed plan: stop after each phase, before its commit. Compact plan: stop before
   any commit. Also stop on blockers: plan vs code conflict, change outside scope, checks still
   failing after retries, high-risk review with no second reviewer. Never push.
   `commit_approval: preapproved` is no longer needed in forge-plan.
4. **High-risk review (ladder).** Use a separate reviewer agent if the harness has one. If not,
   ask the human to review or open a fresh session. The writer never reviews its own high-risk work.
5. **Record.** No `evidence.md`. Plan files stay unchanged. Write `progress.md` next to
   compact `plan.md`, and one per `phases/NN/`. Per task ID: status, commands + result,
   deviations, commit. Top-level `progress.md` also holds the dirty-tree baseline.
6. **Goal.** No `intent.md` artifact. forge-discover writes `## Goal` at the top of
   `context.md` in the user's words (problem, outcome, done when, not in scope).
   Goal changes only when the user says so. Plan, spec, implement check against it.
8. **Backfill depth.** Missing inputs: always run discover. Run clarify only if discover found
   open human decisions. Never auto-run spec; plan works from context.md + decisions.md.
9. **Plan mode.** forge-plan always recommends compact or detailed, with its reason. When the
   user calls forge-plan directly, it asks and waits right there. When forge-implement (or
   another skill) backfills forge-plan, forge-plan does not ask separately — see decision 18,
   which is the single authoritative stop contract for backfill. If a risky item shows up after
   the mode is set, say so and ask again either way.
10. **progress.md format.** Checklist per task: `- [ ]` todo, `[~]` doing, `[x]` done, `[!]` blocked,
    with indented `check:`, `changed:`, `deviation:`, `commit:` lines. Resume = first box not `[x]`.
11. **Dirty tree.** List other people's changes in progress.md. Never edit, stage, or commit them.
    If a task must touch one, stop and ask.
12. **Branch.** Commit to the current branch unless it is protected (default branch, main, master,
    develop, release/*, or host-protected). Then suggest a name that follows the repo's branch
    convention if one exists. If the user gives a new convention, ask to save it and say why
    (next agents and people use the same names).
13. **Convention doc.** Existing doc wins. Default: `docs/contributing/git.md`, plus one pointer
    line in root AGENTS.md or CLAUDE.md if present. Ask before writing.
14. **Artifact location.** Existing convention wins. Default: `.forge/<work-item>/`, committed.
    progress.md is committed with the phase it records.
16. **Work item** = one `.forge/<slug>/` folder. discover makes the slug. Later skills match the
    request to a Goal; 0 or 2+ matches -> ask. Branch reuses the slug.
17. **High risk** = any one of size, risk, complexity is high, or two are medium. Plan marks it;
    implement re-checks the real diff. Same rule in both modes.
18. **One combined stop** when backfilling: Goal, open decisions (with suggestions), mode, plan path
    in one message. Redo and show again only if the answer changes the plan. This is the only stop
    before the first source edit in a backfill: forge-plan's own mode-confirmation ask and its own
    end-of-draft "review or go?" both fold into this single message when forge-plan was backfilled
    rather than called directly by the user (resolves the former conflict with decision 9).
19. **Resume.** Write a file under the task's `changed:` before editing it. On resume, those files
    are "mine"; re-run the task's proof.
20. **Conflicts.** Goal, decisions.md, spec.md, and plan disagree -> blocker. Show both, user decides,
    fix the losing file.

Terms: see root `CONTEXT.md`.

15. **Invocation.** All 5 Forge skills are user-invoked (workflow stages; Matt Pocock pattern,
   `.reference/mattpocock-skills/.agents/invocation.md`). Per host:
   - Claude Code, Cursor, Factory: `disable-model-invocation: true` in SKILL.md.
   - Codex: `agents/openai.yaml` with `policy.allow_implicit_invocation: false`. Keep both in sync.
   - Antigravity: no switch (base Agent Skills spec has none). Narrow description; disclosed not enforceable.
   Known deviation: the field fails `skills-ref validate` (spec allows only name, description,
   license, compatibility, metadata, allowed-tools). Repo rule updated to allow it (ticket 02).
   Description = one human-facing line. Backfill reads the earlier skill's SKILL.md; no host invocation.
