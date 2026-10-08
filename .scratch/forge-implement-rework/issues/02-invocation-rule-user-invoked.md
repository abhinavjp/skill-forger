# 02: Repo rule: allow user-invoked skills across hosts

**What to build:** skill-engineer and skill-prospector accept a user-invoked skill: `disable-model-invocation: true` in SKILL.md paired with `agents/openai.yaml` `policy.allow_implicit_invocation: false`. They report the known gaps instead of failing.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Portable-frontmatter rule allows `disable-model-invocation` as the one invocation exception, with reason
- [ ] Inspector: field present without matching `agents/openai.yaml` policy (or reverse) → finding
- [ ] Inspector notes the field fails `skills-ref validate` (known deviation), as info
- [ ] Host table updated: Factory row added; Antigravity marked not enforceable for skills; Claude Code open bugs listed as deviation evidence
- [ ] User-invoked description rule: one human-facing line, no trigger list
- [ ] Tests and evals for both inspectors pass
