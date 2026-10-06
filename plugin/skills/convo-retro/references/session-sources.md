# Session sources

Read the cheapest, most structured source first: `progress.md`, then the git
range, then the transcript.

## Transcript locations

| Host | Where | Status |
|------|-------|--------|
| Claude Code | `~/.claude/projects/<encoded-project-path>/<session-id>.jsonl`; newest file is usually the latest session | tested |
| Codex | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` | untested |
| Cursor | no stable path known; ask the user for an export or paste | untested |
| Google Antigravity | no stable path known; ask the user for an export or paste | untested |

Never guess a path. If the user names none and the host row is untested, ask
once, then fall back below.

## Reading a transcript

Transcripts are large and may hold secrets. Search for the signals in step 2
and read a few lines around each hit. Redact tokens, keys, and credentials in
anything you quote.

## No transcript reachable

Say so and mark the report `partial`. Use what remains: the current context
(label `self-review`), `progress.md`, `git log` and `git diff` for the
session's range, and the repo's check output. Findings from these sources
carry a locator like any other; skip any claim you cannot locate.

## Several sessions

A signal found in more than one session ranks higher: recurrence is the
strongest evidence that a fix pays off.
