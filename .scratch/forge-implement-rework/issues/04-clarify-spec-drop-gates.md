# 04: forge-clarify and forge-spec: drop gate text

**What to build:** clarify runs when discover found open decisions or the user calls it. spec runs only when the user calls it and reads Goal from context.md. Both point to the shared contract for approval.

**Blocked by:** 01, 03

**Status:** ready-for-agent

- [ ] No approval, hash, or continuation-intent text remains
- [ ] User-invoked per decision 15: `disable-model-invocation: true` + `agents/openai.yaml` policy false; one human-facing description line, narrow enough for Antigravity
- [ ] No-op sentences cut; shared rules pointed to, not copied
- [ ] Gate evals removed; evals for new run conditions pass
