# Verify an installation

Run this checklist after installing through any host guide
([Claude Code](claude-code.md), [OpenAI Codex](openai-codex.md), [Cursor](cursor.md),
[Antigravity](antigravity.md)). It applies unchanged to every host.

1. **Only one installation source is enabled.** You installed through exactly one route for this
   host — not the plugin route and a standalone copy at the same time.
2. **`skill-engineer` is discoverable.** The host lists or can invoke a Skill named
   `skill-engineer`.
3. **`merge-sentinel` is discoverable.** The host lists or can invoke a Skill named
   `merge-sentinel`.
4. **An implicit MR-review prompt selects `merge-sentinel`.** Ask the host to "review this merge
   request for defects" (no explicit Skill name) and confirm `merge-sentinel` is the one that
   activates.
5. **A skill-editing prompt selects `skill-engineer`, not `merge-sentinel`.** Ask the host to
   "update this Skill so it does X" and confirm `skill-engineer` activates instead.
6. **Relative references and scripts load from the installed Skill root.** Trigger a reference
   load (for example, ask `merge-sentinel` to review a GitLab MR) and confirm it reads
   `references/*.md` and runs `scripts/*.py` from the installed location without a path error.
7. **Updating the GitHub source and reinstalling/updating changes the installed version.** Pull a
   new commit in the clone, run the host's update step from its install guide, and confirm the
   host reflects the new commit (for example, via a version/description change or an updated
   `SKILL.md` reference).
8. **Uninstalling removes host-owned installation state without deleting the clone.** Run the
   host's uninstall step and confirm the Skills are no longer discoverable, while the
   `abhinavjp/skill-forger` clone on disk is untouched.

Record the result of each numbered item per host. Where a host executable or an isolated test
surface is unavailable, record that item as `UNTESTED: host unavailable` rather than assuming a
pass — do not claim an item passed without having run it.
