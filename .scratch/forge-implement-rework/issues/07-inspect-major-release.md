# 07: Inspect and major release

**What to build:** All 5 Forge skills pass skill-engineer inspection; plugin ships as a major version with migration notes.

**Blocked by:** 04, 06

**Status:** ready-for-agent

- [ ] Inspection clean on all 5 skills (length, wording, portability)
- [ ] No meaning duplicated between skills and shared files
- [ ] Inspector passes with the invocation rule from 02
- [ ] Release notes list host support: enforced on Claude Code, Cursor, Factory, Codex; not on Antigravity; `skills-ref validate` deviation
- [ ] Major version bump (approval model changed)
- [ ] Release notes: what changed; move old plan to `.forge/<work-item>/` and add `progress.md`
