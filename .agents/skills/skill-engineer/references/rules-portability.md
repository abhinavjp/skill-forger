# Portability rule — R22

Load when portability is claimed, or when the Skill will move hosts. Index:
[rules-index.md](rules-index.md).

## R22. Portability boundary

**Check** — Does behaviour claimed portable depend on host-specific features?
A portable core must not require host-only frontmatter, host-only agents, hooks
or permissions, host-specific filesystem paths, or proprietary invocation
syntax — only `SKILL.md` plus relative resources.

Format compatibility is not behavioural compatibility. A Skill whose mandatory
workflow requires shell access, an interpreter, a package install or permission
to execute bundled scripts is claiming more than "any compatible host" can
deliver. Either degrade gracefully — perform the checks the host supports,
report the rest as unvalidated, and never claim a check that did not run — or
narrow the compatibility claim to the capabilities actually required. An
overbroad claim also corrupts cross-host results: the second host looks broken
when the claim was wrong.

**Detect** — Frontmatter keys, hardcoded paths (deterministic), invocation
syntax, hook names, named subagents, assumed platform tools, and mandatory steps
that assume an interpreter, network access or executable resources.
**Severity** — High when portability is claimed.
**Action** — Move the feature into an adapter, add capability detection,
degrade gracefully, or narrow the compatibility claim.
**Validation** — Standards validation plus host-specific tests, including a
host without the assumed capability. Do not equate "parses on multiple hosts"
with "behaves equivalently on multiple hosts"; record standards compatibility,
hosts tested, models tested, known deviations and untested environments
separately. **Automation** — hybrid.
**Class** — Universal for portable Skills. **Applies** — when portability is
claimed.
