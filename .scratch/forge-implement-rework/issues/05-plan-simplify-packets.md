# 05: forge-plan: simplify, fixed packet headings

**What to build:** forge-plan reads Goal, decisions.md, spec.md if present; backfills per shared rule. Always asks compact or detailed with suggestion + reason (from implement: suggests compact). Writes to `.forge/<work-item>/` with fixed packet headings implement finds by name: `## Outcome`, `## Write scope`, `## Must not change`, `## Changes`, `## Proof`, `## Depends on`. Marks each slice/phase `risk: low|medium|high`. Ends: shows plan path, asks "review or go?".

**Blocked by:** 01, 03

**Status:** ready-for-agent

- [ ] SKILL.md body about 60 lines; steps end with "Done when"
- [ ] `commit_approval` removed; `commit_granularity` and `history_style` kept
- [ ] `PAUSED / AWAITING_APPROVAL` copies removed; phase gate is a pointer
- [ ] Request matched to Goal; 0 or 2+ matches → asks
- [ ] User-invoked per decision 15: `disable-model-invocation: true` + `agents/openai.yaml` policy false; one human-facing description line, narrow enough for Antigravity
- [ ] No-op sentences cut
- [ ] Evals: asks mode with suggestion; packet headings present; from implement suggests compact; 2 work items → asks which
