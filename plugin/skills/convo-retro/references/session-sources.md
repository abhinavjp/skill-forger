# Session sources

Read the cheapest, most structured source first: `progress.md` (if the repo
uses Forge), then the git range, then the transcript.

## Transcript locations

| Host | Where | Status |
|------|-------|--------|
| Claude Code | `~/.claude/projects/<encoded-project-path>/<session-id>.jsonl`; newest file is usually the latest session | tested |
| Codex | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`; records are `session_meta`, `response_item` (`message`, `function_call`, `custom_tool_call` plus `*_output`) and `event_msg`; shape seen locally, `scripts/session_signals.py` does not parse it, so search by hand | untested |
| Cursor | users report `~/.cursor/projects/<project>/agent-transcripts/*.jsonl`, and chats in the SQLite `User/globalStorage/state.vscdb` (`cursorDiskKV`, `bubbleId` rows); not verified here, so confirm the path with the user | untested |
| Google Antigravity | no stable path known; ask the user for an export or paste | untested |

Never guess a path. When the user asks for an external transcript on an untested
host, ask once for its location, then fall back below.

## Reading a transcript

Transcripts are large and may hold secrets. Search for the signals in step 2
and read the record at each hit, not the whole log (step 2 lists the
exception for `heavy_output`).

## No transcript reachable

Say so and mark the report `partial`. Use what remains: the current context
(label `self-review`), `progress.md`, `git log` and `git diff` for the
session's range, and the repo's check output. Findings from these sources
carry a locator like any other; skip any claim you cannot locate.

## Several sessions

Rank signals seen in several sessions as the report format says.
