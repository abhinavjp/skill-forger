# 01: Structural invocation-policy check

**What to build:** Skill inspection judges a Skill's Codex invocation policy from the parsed `openai.yaml` structure, not a raw text match. Only `policy.allow_implicit_invocation` set to boolean false counts as explicit-only; comments, wrongly-nested keys and malformed YAML can't mask a mismatch with `disable-model-invocation`. (PR #3 Codex P2 finding.)

**Blocked by:** None (can start immediately)

**Status:** done

- [x] Failing tests first: commented-out key, wrongly-nested key, malformed YAML, correct key → only correct key passes
- [x] Malformed YAML reported as a finding, not a crash or silent pass
- [x] Packaging tests + plugin validator green
