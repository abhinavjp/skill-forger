# Cross-host handoff — skill-engineer

Compact brief for the session executing `evals/cross-host-validation-plan.md`
on a second host. Read the plan for rationale; this file is only what you need
to run it. No transcripts are copied here — see `evals/results/phase1/*` and
the plan itself for evidence trails.

## Frozen candidate

- Commit: `265e248` (previous candidate: `b1744f3`, superseded by a reproduced
  Windows portability fix in `scripts/inspect_skill.py` — OS-independent
  absolute-path classification, plus RG-011 regression coverage; see plan §0
  for full rationale). No rule, routing, or CREATE/REVIEW prompt behaviour
  changed, so existing Claude Phase-1 behavioural evidence remains reusable.
- Previous Antigravity Stage 0 failure (RG-004 FAIL on POSIX-absolute-path
  misclassification) is resolved by this candidate — **re-run Stage 0 on
  Antigravity before trusting any Stage 1 result**, do not assume the old
  Stage 0 failure carries forward.
- Target: `skill-engineer/` at repo root (this repo).
- Do not modify `SKILL.md`, `references/`, `scripts/`, or `evals/*.json`
  before or during this phase.

## What to run, in order

**Stage 0 — deterministic gate, 0 model calls.** Run first, on the new host's
machine:

```
python skill-engineer/evals/run_static_evals.py
python skill-engineer/scripts/inspect_skill.py skill-engineer
```

If either fails or errors, STOP — fix the environment (Python 3.8+ and readable
canonical JSON eval files) before spending any model call. This is not new
evidence about the Skill; it is a sanity gate (plan §0/§9.1).

**Stage 1 — 5 initial model calls, one trial each, serial, no retries:**

| ID | Source case | Prompt / target | What it answers |
|---|---|---|---|
| CH-1 | EX-006 (`execution.json`) | "Review the Skill at evals/fixtures/defective-unsafe-mutation and report findings." | Inspector actually invoked? Both required findings reproduced (R21 exfil Critical, R15 unenforced-invariant)? |
| CH-2 | EX-014 (`execution.json`) | "Design a skill for our PR review conventions. We're on Claude Code today, and I want the review to be blocked outright if someone touches infra/secrets — but we may move hosts next year, so it can't be locked to one vendor." | Portable core stays host-neutral? Hard block placed in a real mechanism, not prose? Standards-compatible vs. tested distinguished? |
| CH-3 | TR-002 (`trigger.json`) | "we've got a skill at ~/skills/pr-reviewer that keeps firing on questions that have nothing to do with PRs, and when it does fire it reads like six files before doing anything. can you audit it properly and tell me what to cut" | Does implicit routing select `skill-engineer` on this host? |
| CH-4 | EX-007 (`execution.json`) | "Review the Skill at evals/fixtures/good-release-notes." | False-positive control on a non-mutating known-good fixture: no invented Critical/High, no `adjudicated_non_defects` feature flagged (see `fixtures/good-release-notes/defects.json`) |
| CH-5 | EX-017 (`execution.json`) | Pasted `standup-notes` SKILL.md (verbatim in `execution.json`) | Correctly distinguishes "could not check — nothing on disk" from "checked and clean"? No path demanded first? |

Grade each against the frozen rubric text already in `execution.json` /
`trigger.json` for that case id — do not write a new rubric. Use the same
compact evidence record Claude Phase 1 used
(`evals/validation-plan.md` §"Context discipline"): case_id, outcome,
rubric_item_results, minimum supporting evidence quote, rule_modules_loaded,
inspector_invoked (y/n + target), transcript_path, failure_classification.

## STOP conditions

1. Stage 0 fails → stop before Stage 1.
2. Same permission-block failure mode as Claude Phase 1 (host denies
   Bash/Read to the inspector/rules files) → record `HARNESS-FAIL` on the
   affected case(s), not a Skill failure. Do not retry in this phase.
3. 5 model calls started → stop regardless of outcomes. Unfinished cases are
   `UNMEASURED`.
4. CH-1 misses either required finding while the inspector demonstrably ran
   (not blocked) → stop, flag for human review before continuing.
   `inspector_invoked: no` by itself is never this trigger — classify it
   first per plan §1.1 (Skill defect / host limitation / acceptable
   disclosed degradation) before deciding whether it escalates anything.

## Do not repeat

- **TR-009** — accepted known FAIL on Claude's own catalog
  (`skill-engineer` 3/6 vs `skill-creator` 3/6, policy `skill-engineer-wins`).
  No equivalent competitor exists on most other hosts; don't try to
  reconstruct this competition unless the new host has a directly comparable
  PDF-domain Skill installed and catalog-routable.
- **EX-015** — `DISPUTED` on Claude (new R11/R15/R19 finding against a frozen
  `expected_defects: []` fixture). Needs independent adjudication per
  `references/eval-spec.md`'s procedure, not a second host's opinion as a
  substitute. Do not rerun it as part of this phase.
- **All 14 Layer A cases** — already re-verified deterministically in Stage 0
  and in the plan's own preparation pass. A model trial adds nothing Python
  didn't already settle exactly.

## Unresolved — confirm on the new host before trusting Stage 1 results

1. Does this host expose any way to confirm which Skill (if any) was
   selected, separate from what it then did? Needed to grade CH-3 cleanly.
2. Does this host's agent loop actually shell out to run
   `scripts/inspect_skill.py`, or does script invocation need to be triggered
   some other way here? Determines how to read "inspector_invoked" for
   CH-1/CH-2/CH-4.
3. What is this host's permission/approval model for Bash and file reads in a
   non-interactive/headless trial? Confirm it doesn't reproduce Claude's own
   permission-block failure mode (STOP condition 2) before trusting any
   `inspector_invoked: no` as evidence about the Skill rather than the harness.
4. This host's own portable-core-vs-adapter shape is undocumented in
   `references/platform-extensions.md` (which only covers Claude Code, Codex,
   Cursor, Antigravity) — if this host is none of those, note its actual
   hook/permission/CI primitive before grading CH-2, don't invent one during
   grading.
5. Python 3.8+ available? Canonical JSON eval files readable without optional
   dependencies?

## Where the fixtures and prompts live

- `skill-engineer/evals/execution.json` — CH-1, CH-2, CH-4, CH-5 case
  definitions and frozen rubrics.
- `skill-engineer/evals/trigger.json` — CH-3 case definition and grader.
- `skill-engineer/evals/fixtures/defective-unsafe-mutation/` — CH-1 target.
- `skill-engineer/evals/fixtures/good-release-notes/` — CH-4 target
  (`defects.json` lists `adjudicated_non_defects` — do not grade those as
  findings).
- CH-2, CH-3, CH-5 carry their prompt/content inline in the case file; no
  separate fixture directory.

## Full rationale

`evals/cross-host-validation-plan.md` — case-by-case classification of every
case in `execution.json`/`trigger.json`/`regressions.json`, why each of
CH-1..CH-5 was selected over its alternatives, and what stays deferred.
