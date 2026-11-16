# 03: forge-discover: entry point, writes Goal

**What to build:** User states a problem; forge-discover writes `## Goal` at the top of `context.md` (problem, outcome, done when, not in scope) in the user's words. It asks only to fill Goal, sends other human decisions to clarify, and names the work item slug.

**Blocked by:** 01, 02

**Status:** ready-for-agent

- [ ] context.md template starts with Goal
- [ ] Goal changes only when the user says so
- [ ] Open decisions found → points to clarify next
- [ ] User-invoked per decision 15: `disable-model-invocation: true` + `agents/openai.yaml` policy false; one human-facing description line, narrow enough for Antigravity
- [ ] Gate text replaced by pointer to shared contract; no-op sentences cut
- [ ] Evals: writes Goal first; no Goal → asks; fact refresh leaves Goal unchanged
