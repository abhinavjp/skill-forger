# Host detection and invocation

Load this reference only after examining the target's evidence. A signal narrows
optional plan content; it never gates the portable candidate plan. A signal is
an inference, not proof of the installed host.

## Detection signals

| Target evidence | Inference | Confidence / record |
|---|---|---|
| `.claude/`, `CLAUDE.md` or `.claude-plugin/` | Claude Code may be in use | UNVERIFIED repository signal; verify with the host |
| `.cursor/rules/`, `.cursorrules` or `.cursor/skills/` | Cursor may be in use | UNVERIFIED repository signal; verify with the host |
| `AGENTS.md` alone | Codex-compatible guidance may be present | UNVERIFIED host proof; other hosts read it too |
| `.gemini/`, `.agents/plugins/` or `_agents/` | Antigravity/Gemini route may be present | UNVERIFIED repository signal; verify with the host |
| Several signal groups | Multi-host target | UNVERIFIED composite signal; keep the plan portable-first |
| No signal group | Unknown host | UNVERIFIED absence signal; portable core only |

## Candidate invocation contract

Every candidate states this portable intent: invoke it deliberately by the
user, not by model auto-selection. If a host cannot enforce that, use narrow
description discipline and disclose the limitation. The `user-invocable`
distinction below is UNVERIFIED until the current host documentation confirms
it. Never use
`user-invocable: false` for this purpose: that control hides a Skill from a
menu while leaving model invocation possible. Setting it together with
`disable-model-invocation` makes the Skill unreachable.

| Host | Optional proposal | Evidence and status |
|---|---|---|
| Claude Code | `disable-model-invocation: true`; leave `user-invocable` at its default | [Claude Code issue #26251](https://github.com/anthropics/claude-code/issues/26251); `enforced-with-known-deviation` because explicit slash invocation was reported unreachable |
| Cursor | Use the key only for project-level Skills, never plugin-delivered Skills | [Cursor forum #155748](https://forum.cursor.com/t/disable-model-invocation-true-completely-hides-plugin-delivered-skills-from-command-palette/155748); `enforced-with-known-deviation` |
| OpenAI Codex | No host key proposed; description discipline only | UNVERIFIED equivalent; `not-enforceable — description discipline only` |
| Google Antigravity | No host key proposed; description discipline only | UNVERIFIED suppression control; `not-enforceable — description discipline only` |

The Claude and Cursor entries describe known deviations, not behavioural
equivalence. Re-check the host's current feature set and `skill-engineer`'s
`platform-extensions.md` before carrying any other host-specific field into a
candidate. Never propose a host key for an undetected host.
