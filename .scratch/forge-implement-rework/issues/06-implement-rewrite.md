# 06: forge-implement: rewrite to run forge-plan output

**What to build:** forge-implement takes a compact or detailed forge-plan and runs it: find plan (none → run forge-plan, ask "review or go?"), start `progress.md` with dirty-tree baseline, branch check, do each ready task inside write scope with its proof, stop on blockers, phase-end checks + review (second reviewer for high risk, else ask human, max 2 fix loops), stop before commit, never push.

**Blocked by:** 05

**Status:** ready-for-agent

- [ ] SKILL.md body about 60 lines; each step ends with "Done when"
- [ ] progress.md uses shared format; resume = first box not `[x]`; files under `changed:` are mine
- [ ] commit-modes and quality-routing references deleted; failure-recovery simplified
- [ ] No mention of `tasks.md`, `evidence.md`, `review-first`, `per-task`, `end-only`, approval hash
- [ ] User-invoked per decision 15: `disable-model-invocation: true` + `agents/openai.yaml` policy false; one human-facing description line, narrow enough for Antigravity
- [ ] Shared rules pointed to, not copied
- [ ] Evals: compact → one stop before commit; detailed 2 phases → stop each; no plan → nothing edited before go; resume mid-phase; one combined backfill stop; Goal vs spec conflict blocker; 1-line auth change → high risk + second reviewer; dirty tree untouched; plan vs code conflict → `[!]` + dependants blocked; high risk no subagent → asks human; protected branch → name suggestion, new convention → ask to save
- [ ] Live model behaviour marked `UNMEASURED` until run
