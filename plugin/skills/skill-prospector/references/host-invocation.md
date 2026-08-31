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
| `.gemini/`, `.agents/skills/` or `GEMINI.md` | Antigravity/Gemini route may be present | UNVERIFIED repository signal; verify with the host |
| Several signal groups | Multi-host target | UNVERIFIED composite signal; keep the plan portable-first |
| No signal group | Unknown host | UNVERIFIED absence signal; portable core only |

## Candidate invocation contract

Each candidate records one policy: `automatic`, `both`, or
`explicit-only-required`, plus one sentence of evidence/risk justification.
Default to `both` for safe reusable workflows. Use `automatic` when
discoverability is essential and false positives are low. Use
`explicit-only-required` only when accidental activation has meaningful cost or
risk. A strict explicit-only requirement must use a host-enforceable
command/workflow, or be disclosed as non-enforceable and deferred unless the
user accepts automatic-routing risk.

Host statements have separate status: `standards-compatible`, `tested`,
`untested`, or `known deviation`. Repository signals do not prove an installed
host, and no host-only field belongs in portable `SKILL.md` frontmatter.

| Host | Automatic routing | Explicit route | Explicit-only enforcement | Status/evidence |
|---|---|---|---|---|
| Claude Code | Skills are automatically loaded when relevant | `/skill-name` | `disable-model-invocation: true`; `user-invocable: false` is a visibility control, not suppression | `standards-compatible`; official contract verified 2026-08-30 at [Claude Code Skills/slash commands](https://code.claude.com/docs/en/slash-commands). Plugin delivery `untested`; dated reports such as [issue #26251](https://github.com/anthropics/claude-code/issues/26251) are deviation evidence only. |
| OpenAI Codex | Portable `name`/`description` catalog routing | Named Skill / `$skill-name` where surfaced | No portable suppression field established; use `not-enforceable-portably` or another host mechanism | `standards-compatible`; official sample/source verified 2026-08-30 at [Codex skill creator](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/skill-creator/SKILL.md). Native catalog trial `untested`. |
| Cursor | Agent Skill routing where installed | `/skill-name` | `disable-model-invocation: true` in the current Cursor contract | `standards-compatible`; official contract verified 2026-08-30 at [Cursor Agent Skills](https://cursor.com/docs/skills). Exact project/plugin delivery `untested`; [forum report #155748](https://forum.cursor.com/t/disable-model-invocation-true-completely-hides-plugin-delivered-skills-from-command-palette/155748) is dated deviation evidence only. |
| Antigravity | On-demand Skill selected from its `description` | User-triggered `/` Workflow; some surfaces expose Skill slash invocation | Workflow is the documented strict user-triggered mechanism; no portable Skill suppression key established | `standards-compatible`; official behavior verified 2026-08-30 at [Antigravity SDD codelab](https://codelabs.developers.google.com/sdd-adk-antigravity) and [Antigravity Skills codelab](https://codelabs.developers.google.com/getting-started-with-antigravity-skills). Native trial `untested`. |

For an unknown host, keep the portable core only and label runtime behavior
`untested`. Never present a repository issue, forum report, or signal as a host
contract, and never propose a host key for an undetected host.
