# convo-retro — design plan

*Reads the chat. Fixes the setup, so the next run doesn't trip on the same stair.*

Source: Matt Pocock's `retro` ([article](https://www.aihero.dev/skills-retro),
[skill](https://github.com/mattpocock/skills/tree/main/skills/engineering/retro), MIT).
This is an adaptation, not a copy: our text, our evidence rules, our hosts.
Credit him in the skill's README line and CHANGELOG.

## What retro is

User-invoked. Reads one coding session. Proposes changes to the agent's
**environment** (never the code) so the same stumble cannot recur. Proposals
only; the user applies. 7 categories: navigation, automated checks, coding
standards, global AGENTS.md, tool economy, no-ops, information access.

## Good (keep)

- Fixes the environment, not the code. "Not a memory system": no lines that
  say "remember X happened".
- Every candidate traces to a concrete moment in the session.
- Mechanical mistake -> deterministic check. Judgement call -> reviewer doc.
  Reason: implementer has max context pressure, reviewer only sees a diff.
- Steering files (AGENTS.md/CLAUDE.md) hold pointers only. Success = they shrink.
- User-invoked, propose-only, ~40 lines.
- Live version beat the older local copy: read the repo's own check command
  first; an existing-but-unwired check is the finding; no guardrail at all is
  a finding. (`.reference/` copy is stale: still in `in-progress/`.)

## Bad (fix)

| Gap | Our fix |
|---|---|
| "Search session logs on this machine": no paths, formats, size bound | `references/session-sources.md` per host + bounded extractor script |
| Hard dependency on external `writing-for-agents` skill | Use skill-engineer's R10 / 6.1 no-ops / 5.3 leading words; ladder with inline fallback |
| Assumes `CODING_STANDARDS.md`, a reviewer agent, Claude's Skill tool | Name the repo's real review doc as the reviewer standard; SKILL.md names no reviewer agent (merge-sentinel stays a routing neighbour only); no host-only tool names |
| "Global AGENTS.md" and "No-ops" overlap | One category: steering-file pruning |
| "Order of severity" undefined | Rubric: cost incurred x recurrence likelihood. Cap 7 candidates |
| Single session only; admits no pruning audit | Accept N sessions; recurrence raises rank. Whole-repo audit routes to skill-prospector |
| No evals | trigger + execution evals + fixture transcripts |
| Vague description; would sit near skill-prospector in the catalog | Narrow description + "Do not use" routing; run the catalog-overlap check |

## Ugly (guard against)

1. **"Default to building the check."** Auto-hooks that block good changes are
   the author's own named failure. Guard: every proposed check ships with a
   dry run (run it on current tree / last N commits; report hits) and an
   estimated false-positive note. Hooks, CI, lint config = persistent config:
   explicit go per item, never batch-applied.
2. **Transcripts hold secrets and are huge.** Guard: extractor redacts
   token-like strings, bounds output, read-only; agent never loads the raw log.
3. **Self-grading.** The agent that struggled analyses its own session, with
   full bias. Guard: current session allowed but labelled `self-review`;
   prefer a fresh session pointed at the log (same rule as Forge decision 4:
   the writer never reviews own high-risk work).
4. **Claude-flavoured portability.** Skill tool, CLAUDE.md, session path all
   assumed. We ship to Claude Code, Codex, Cursor, Antigravity. Guard:
   capability degradation: no log reachable -> say "partial", use git + progress.md.
5. **Persistent steering line creep.** A retro that adds a line without
   removing one defeats itself. Guard: net-budget rule: each line added to an
   always-loaded file names a line to delete or justifies the load.

## Where it beats the original (our edge)

Forge already records struggle in structured form. `progress.md` has
`FAIL`/`UNMEASURED` checks, `[!]` blocked tasks, `deviation:` lines, retries.
These are cheap, portable, host-independent evidence; plan deviations are
direct plan-quality signals. Original has nothing like it. Primary source
order: `progress.md` -> git range -> transcript signals.

## Decisions to take (recommendation first)

1. **Name:** `convo-retro` (chosen by user 2026-10-06): "retro" is the term people
   search for; "convo" says what it reads. Description must say it reviews a
   past agent session to propose setup fixes, and is not for reviewing code
   (merge-sentinel / code-review). Rejected: retro-fit, forge-temper,
   forge-retro, twice-shy, friction-fix, review-convo.
2. **Standalone, not a 6th Forge stage.** Works on any session, like
   merge-sentinel; reads Forge artifacts when present. Avoids touching the
   "five-stage" contract and every count claim.
3. **Script in v1:** yes, `session_signals.py` for Claude Code JSONL only;
   other hosts use agentic reading + disclosed degradation. (R11: deterministic
   extraction earns its cost on a multi-MB log.)
4. **Output:** chat report; write a file only if asked. Apply nothing in the run; the user asks separately for numbered items (keeps mutation and idempotency rules out of scope).
5. **Confirmed 2026-10-06:** decisions 2 and 3 taken as recommended.

## Skill shape

```
plugin/skills/convo-retro/
  SKILL.md                 ~60 lines, disable-model-invocation: true
  agents/openai.yaml       allow_implicit_invocation: false (kept in sync)
  references/categories.md     rung ladder + use-when per category
  references/session-sources.md  per-host log paths, degradation
  references/report-format.md    candidate fields, severity rubric
  scripts/session_signals.py     struggle signals + locators, redacted, JSON
  scripts/test_session_signals.py
  evals/trigger.json, evals/execution.json, evals/fixtures/*
```

Steps (each ends "Done when"):
1. Pick sources. Done when: sources listed, `self-review` flag set or cleared.
2. Extract signals (progress.md, git range, `session_signals.py`). Done when: every signal has a locator.
3. Read existing guardrails (check scripts, CI, hooks, steering files read in session). Done when: unwired/missing guardrails noted.
4. Classify each signal on the ladder: check > reviewer doc > pointer > tool/access fix > nothing. Done when: each signal has a rung or a rejection reason.
5. Dry-run each proposed check. Done when: hit count recorded.
6. Rank, cap at 7, report. Done when: user can approve items one by one.

Signals the script counts (5, as shipped): `user_correction`, `search_thrash`
(repeated grep/glob/read before the right file), `retry_loop` (fail-then-retry
commands), `reverted_edit`, `heavy_output` (a per-result size threshold, not
one tool dominating). `unused_read` (files read but never used) is deferred to
v2. The agent opens a record only for the first four; `heavy_output` is
reported by size alone.

## Phases

0. **Unblock** pull (see chat); refresh `.reference/mattpocock-skills`; license note (MIT, credit).
1. **Spec** via forge-discover/clarify: confirm decisions above. Goal in user's words.
2. **Skill text + trigger evals. DONE 2026-10-06** (inspector clean, 10 trigger cases validate, not in top overlap pairs). Catalog-overlap check green vs skill-prospector/skill-engineer.
3. **Extractor, test-first. DONE 2026-10-06** (55 tests after review batches; real logs: 0 parse errors, ~0.2s/3MB; `unused_read` signal deferred to v2 as costly to do deterministically). Fixtures: synthetic fixture logs under `scripts/fixtures/` (added in review batch C), never real user logs: `search-thrash`, `retry-revert`, `corrections-heavy`.
4. **Execution evals + packaging.** `plugin_policy` registry, README/manifest counts ("nine"), CHANGELOG 3.1.0, install docs, `validate_plugin.py` green.
5. **Dogfood. DONE 2026-10-07.** Pass = >=3 candidates with real locators, 0 untraceable.
   Result: ran on the forge-implement PR3-fix sessions (two logs, a fresh Sonnet
   subagent following SKILL.md): 5 candidates, 17 locators verified against the
   logs, 0 untraceable. Passed. The candidate list lives in the scratchpad only
   and is not committed.
   Found: `search_thrash` false positives on reads of distinct files (5 of 11);
   the extractor was fixed in the same phase. Found: the agent could not judge a
   `user_correction` without the preceding turn, so SKILL.md now reads up to 3
   records before it; the script path is now stated relative to the skill folder;
   the report format allows `Rung: nothing` and `Dry run`/`Load: n/a`.

## v2 backlog (not now)

Verify the Cursor transcript format on a real file (the adapter is a best guess); cross-session recurrence mining; existing-check
firing-rate audit from CI history (original's admitted weakest area).
Missed by the extractor in dogfooding: repeated slow command; elapsed-time and
call-count cost data; failure text inside piped output with no `is_error`; user
turns that are corrections in substance but carry no keyword.

## Review loop status (2026-10-06)

Phase 4 (execution evals, packaging as 3.1.0) landed 2026-10-07. Phase 5 dogfood done 2026-10-07 (see Phases).

Opus review of phases 2-3, then a Sonnet-implements / Opus-verifies loop with a
closed scope (reviewer may only judge ledger items and regressions from the
round's own diff). Batch A cleared. Batches B, C and D landed (round 1 of the
B-D loop verified by Opus: four minor findings, fixed).
Batch D (SKILL.md, references, trigger evals, this doc) landed: F-M2, F-M3,
F-M4, F-M5, F-M7, F-L2..L7.

**Cleared (batch A, redaction + crash):** F-H1 (secret shapes: JSON keys, sk_live,
AIza, 32-hex, URL credentials incl. empty username, Basic auth incl. quoted,
--password and -p flags, quoted values, truncated PEM incl. literal \n and \r\n),
F-M1 (RecursionError on crafted line). 36 tests.

**Phase 5 review trail:** three Codex gpt-6.1-sol rounds on the read/re-read tracking (5, 10, then 3 findings). The last 3 (escapes in double quotes, quoted `--`, `cat --help`) were fixed directly with tests and not re-reviewed, because the 3-round cap was reached.

**PR #4 review round:** fixed two Codex-bot comments (quoted whitespace in retry identity; non-string `tool_use_id`) and four lens-review findings (unterminated quoted secrets after the 2000-char cap, numeric CLI validation, quoted Bash options, shell comments). Added `--context <line>`, a redacted record viewer, so the skill never opens raw transcript lines. Not fixed: a host-enforced read-only boundary for "edit nothing". `allowed-tools` is a platform extension that the portable-payload policy rejects, so the rule stays prose plus propose-only design, as for the Forge skills.

**Multi-host logs:** `scripts/log_adapters.py` turns Codex rollout records and Cursor transcript records into Claude-shaped records, so one analyzer serves all three; the first record with positive evidence fixes the format. Codex is tested on local logs (74 MB log in under 1 s). Cursor is a best guess: no real transcript was available and Cursor omits tool results, so `retry_loop` cannot fire there. Codex commands are read from `cmd:` strings in `exec` JavaScript, so a `cmd:` inside an unrelated JS string can read as a command (accepted).

**Remaining known limits:** the shell read/search classifier is a heuristic aid: an uncertain command (unbalanced quote, Bash backslash-escaped separator, text after a heredoc marker) is left unclassified, so it can miss real thrash but should not invent it; known gaps are path flavour ambiguity (POSIX backslash filenames vs Windows paths, UNC casing), MSYS drive mapping depending on encounter order, and searches after a heredoc body not being seen; exotic shells are missed; only Claude Code logs are tested; a `-p` glued password containing `.` is not redacted (accepted cost); the v2 backlog above is not started.
