# 01: Shared contract: drop gates, add shared rules

**What to build:** Forge shared contract where the user's "go" approves. No hashes, approval records, or script gates. Shared rules every Forge skill reaches by pointer: lifecycle + backfill, approval, stops, locations, git rules, progress.md format, one combined stop, conflict rule, phase gate. Keep `PASS / FAIL / UNMEASURED`, retry rule, blocked task blocks dependants.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Decided:** delete `workflow_state.py`; `can_retry` and `block_dependants` become plain-text rules. Scripts stay optional for any harness.

- [ ] No shared Forge file mentions approval hash, revision, freshness, or `can_enter_stage`
- [ ] `workflow_state.py` and its gate tests removed; remaining shared tests pass
- [ ] Rules only some skills need (git rules, progress.md format) live in their own reference files; each rule in one place
- [ ] Terms from root `CONTEXT.md` (work item, high risk, go, stop, blocker, backfill, second reviewer) used as-is, not redefined
- [ ] Lifecycle rule: "run a skill" = read its SKILL.md and follow it (works for user-invoked skills)
- [ ] Phase gate moved here from forge-plan's detailed mode
- [ ] Short sentences; "do not" only for hard safety lines, paired with the positive action
