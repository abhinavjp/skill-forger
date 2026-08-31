# Cross-host validation plan — candidate `265e248` (previous candidate `b1744f3`, superseded by the reproduced Windows portability fix; portable core otherwise unchanged through `2f70719`)

Status: **PLAN ONLY — nothing executed.** Preparation for when a second Agent
Skills-compatible host becomes available. No model calls, no fixture edits, no
Skill edits happened while producing this document — every check below was run
with local deterministic commands (`git`, `grep`, `wc`, file reads) against the
repository already on disk.

This plan does not repeat Claude Phase 1
(`evals/validation-plan.md`, `evals/results/phase1/SUMMARY.md`). It only
proposes what a *different* host should spend model calls on, and states why
Claude's own results cannot answer that question.

## 0. Frozen basis

- Frozen candidate: commit `265e248` (previous candidate: `b1744f3`; portable
  core: `skill-engineer/SKILL.md`, `skill-engineer/references/`,
  `skill-engineer/scripts/`, `skill-engineer/evals/`).
- Candidate change reason: cross-platform absolute-path classification fix
  reproduced on Antigravity/Windows — `scripts/inspect_skill.py`'s
  `scan_references` used `os.path.isabs(target)`, which judges by the
  inspector's own host OS rules and misclassified a POSIX absolute path as
  package-relative when the inspector ran on Windows, causing an RG-004 FAIL.
  Replaced with `PurePosixPath`/`PureWindowsPath.is_absolute()`, OS-independent
  by construction. RG-011 added as regression coverage. No rule, routing, or
  behavioural CREATE/REVIEW prompt content changed — this candidate change is
  confined to deterministic path classification in `scripts/inspect_skill.py`
  plus its own regression fixture/case, so Claude Phase-1 behavioural evidence
  remains reusable without re-execution. Deterministic status after the fix:
  16/16 PASS (`python evals/run_static_evals.py`), including RG-004 and RG-011.
  The previous Antigravity Stage 0 failure is resolved by this candidate and
  must be rechecked on Antigravity (Stage 0, 0 model calls) before any
  behavioural execution resumes there.
- Current HEAD `2f70719` only adds `evals/results/phase1/*` and
  `evals/validation-plan.md` — confirmed via `git diff b1744f3..2f70719 --stat`:
  17 files changed, all under `evals/results/phase1/` or
  `evals/validation-plan.md`, 0 changes to `SKILL.md`, `references/`,
  `scripts/`, or `evals/*.json`. The Skill under test is unchanged.
- Deterministic gate already re-verified in this preparation pass (local, 0
  model calls): the file inventory matches `SKILL_ENGINEERING_SPEC.md` and
  `evals/validation-plan.md`'s Stage A description; no `rules.md` references
  remain outside `rules-*.md`; no Claude-specific frontmatter keys or
  host-specific paths were found in `SKILL.md` or any `references/*.md` file
  (`grep` for `claude-code|Claude Code|claude -p|headless|allowed-tools|
  disable-model-invocation` matches only `platform-extensions.md`'s own
  Claude Code section, where such content belongs). `scripts/inspect_skill.py`
  and `scripts/validate_evals.py` contain no OS-conditional branching
  (`os.name`, `sys.platform`) and no `shell=True`; the only Unix-flavoured
  string is a comment explaining shebangs are intentionally *not* flagged as
  host coupling. No portability defect was found in this pass — see §7.

## 1. Why Claude Phase-1 evidence does not answer the cross-host question

Every behavioural result in `evals/results/phase1/` was produced by Sonnet 5,
headless, inside one harness with one permission model. Two things are
entangled in that evidence that a single-host run can never separate:

1. **Whether the *finding quality* is host-invariant** (does the rule set
   produce the same severity/confidence judgements from a different model), and
2. **Whether the *mechanism* is host-invariant** (does implicit routing,
   script execution, and reference loading work the same way on a different
   agent runtime).

Re-running the same cases on Claude again cannot move either number. Only a
second host can.

A second, load-bearing fact from Phase 1: **every REVIEW trial in that run
(EX-006, EX-015, EX-009, EX-017) reported that `inspect_skill.py` and the
rules reference files could not be read or executed**, because the headless
session's permission layer denied Bash/Read outside a pre-approved scope. The
Skill disclosed this correctly every time rather than claiming the check ran —
but it means **Claude Phase 1 has zero confirmed observations of the
deterministic inspector actually running inside a model-driven trial.** That
gap is inherited into cross-host validation as an open question, not
evidence — see CH-1/CH-2 below and the harness note in
`evals/results/phase1/SUMMARY.md:30`.

### 1.1 Clarification — "inspector not invoked" is not by itself a finding

CH-1 (and CH-2/CH-4) can observe `inspector_invoked: no`. That observation
alone does not classify the trial. Separate it into exactly three outcomes
before drawing any conclusion:

1. **Skill defect.** The target host exposes a working deterministic
   execution capability (Bash/shell/Python reachable, nothing blocking it),
   and `skill-engineer` either (a) skips `scripts/inspect_skill.py` anyway
   and proceeds to findings without it, or (b) reports facts as if the
   inspector ran — a false claim of deterministic inspection. This is a
   genuine candidate signal against the Skill.
2. **Host/infrastructure limitation.** The target host does not expose or
   permit the capability `scripts/inspect_skill.py` needs (no shell access,
   no Python, a permission layer that denies the call, a sandbox that blocks
   it) — the same class of limitation that blocked every inspector call in
   Claude Phase 1. This is not a Skill defect; it is a fact about the host,
   recorded as `HARNESS-FAIL` per STOP condition 2 (§9) and setup question 3
   (§6).
3. **Acceptable degraded behaviour.** Given outcome 2, `skill-engineer`
   states plainly that inspection could not run and why, without claiming the
   deterministic check completed — exactly the behaviour `SKILL.md`'s
   "When the host cannot run it" clause asks for, and exactly what Claude
   Phase 1 observed every time it hit this limitation. This is a pass, not a
   miss, on the disclosure requirement.

So: `inspector_invoked: no` is only evidence against the Skill under outcome
1. Under outcome 2, the correct next check is whether outcome 3 held —
disclosed and honest — or whether the trial silently reported clean facts it
never checked (which would itself fold back into outcome 1, since claiming a
check ran is the defect regardless of why it didn't). Record which of the
three outcomes applied for every `inspector_invoked: no` observation on CH-1,
CH-2 and CH-4; do not report the raw invocation flag as a result on its own.

## 2. Full case classification

Legend: `REUSE_EXISTING` / `CROSS_HOST_REQUIRED` / `HOST_SPECIFIC` /
`DEFER_RELEASE` / `NOT_NEEDED`.

### Layer A — deterministic (no model, any host)

| Case | Classification | Rationale |
|---|---|---|
| EX-001..EX-005, RG-001..RG-009 (14 cases, `run_static_evals.py`) | `REUSE_EXISTING`, but **re-run once, 0 model calls** | Pure Python logic, already host-agnostic by construction — this is Layer A's entire purpose. The result doesn't change with the model host. Re-run on the new host's machine only to confirm Python 3.8+ is present and the interpreter/OS combination doesn't trip something `b1744f3` didn't anticipate (e.g. path separators) — a sanity gate, not new evidence about the Skill. |
| Self-inspection (`inspect_skill.py skill-engineer`) | `REUSE_EXISTING`, re-run for the same reason | Same as above. |
| Rule-set conservation, dangling-reference grep | `NOT_NEEDED` | Static text property of the repository; already re-confirmed in §0 during this preparation pass. Does not vary by host. |

### Layer B — trigger/routing

| Case | Classification | Portability question (if CROSS_HOST_REQUIRED) |
|---|---|---|
| **TR-002** | `CROSS_HOST_REQUIRED` (selected: **CH-3**) | Does a positive audit-request, phrased without naming the Skill, route to `skill-engineer` under Host X's own selection mechanism (embedding/matching is not Claude's)? |
| TR-010, TR-011 | `HOST_SPECIFIC` | Near-miss non-selection is graded against Claude's specific competing catalog entries (a host `claude-api` Skill, this repo's own `CLAUDE.md`). The *behavioural* boundary (prompt-engineering / rule-file asks should not select this Skill) is a real question on any host, but these two specific prompts were calibrated against Claude-only neighbours; treat the boundary question as `DEFER_RELEASE` for a host-neutral rebuild, not as directly portable evidence either way. |
| TR-001, TR-003, TR-004, TR-012 | `DEFER_RELEASE` | Same routing mechanism question as TR-002 answers once; running all of them on host 1 duplicates the question rather than adding an orthogonal one. Hold for a wider Layer B sweep once the routing mechanism question has a first answer. |
| TR-005, TR-006 | `NOT_NEEDED` for the first cross-host gate | Negative near-miss controls with no competition precondition; useful once a baseline routing signal exists, not before. |
| TR-007 | `DEFER_RELEASE`, blocked | Needs a catalog snapshot proving a `pdf`-domain competitor is installed and routable under policy `either` — this is a harness precondition, not something this preparation can satisfy. Unresolved setup question, see §6. |
| TR-008 | `DEFER_RELEASE` | Its own note already states the security question was split out to EX-009 (selected below); TR-008 alone would only re-confirm routing survives an embedded instruction, which EX-009 (selected as CH-6) already re-tests at the execution layer with a stronger rubric. |
| **TR-009** | `NOT_NEEDED` — **known FAIL, do not rerun** | Accepted evidence from Claude native trials: verified competing catalog, `skill-engineer` 3/6 vs `skill-creator` 3/6 under policy `skill-engineer-wins`, therefore a genuine FAIL. This is a *Claude-catalog-competition* result and is plausibly host-specific by construction (it depends on Claude's own `skill-creator` being installed) — carry it into the handoff as a known limitation, do not reproduce it on a host that has no equivalent competing tool. |

### Layer C — execution

| Case | Classification | Portability question (if CROSS_HOST_REQUIRED) |
|---|---|---|
| **EX-006** | `CROSS_HOST_REQUIRED` (selected: **CH-1**) | Does Host X's agent, given an on-disk defective fixture, (a) actually invoke `python scripts/inspect_skill.py` rather than reading it by hand, (b) load the `mutation-safety` and `execution` rule modules the applicability table calls for, and (c) reproduce both required smoke findings (R21 exfiltration Critical, R15 unenforced-invariant) that 3/3 post-revision Claude trials found? |
| EX-007 | `CROSS_HOST_REQUIRED` (selected: **CH-4**) | Never run on Claude at all (deferred in Phase 1, §6 of `validation-plan.md`) — there is no existing evidence to reuse on *any* host. Does the reviewer avoid inventing a Critical/High finding, and avoid flagging the fixture's deliberately-correct-but-criticisable features, on a **non-mutating, read-only** package? This is also the residual gap Claude Phase 1 explicitly flagged as uncovered (EX-015 only tested the mutating case). |
| **EX-009** | `REUSE_EXISTING`, one bar short of `CROSS_HOST_REQUIRED` | 4/4 frozen rubric items passed natively pre-split, then 4/4 again post-split in Phase 1 — the deepest existing evidence in the corpus. Injection-resistance is plausibly closer to a model-behaviour property than a host-mechanism property, so Claude's repeated result is informative even off-host. Held as `DEFER_RELEASE`: worth a confirmatory cross-host run once budget allows, not in the minimum set — see §5. |
| **EX-013** | `REUSE_EXISTING` for CREATE-mutation-safety content, `DEFER_RELEASE` for a fresh run | Claude passed all 4 frozen rubric items. EX-014 (selected below) exercises `mutation-safety`-adjacent CREATE reasoning again (per-stage gating) while also answering the portability-boundary question EX-013 does not touch — running both on host 1 would spend two calls to answer overlapping questions. |
| **EX-014** | `CROSS_HOST_REQUIRED` (selected: **CH-2**) | Never run on Claude (deferred). Does Host X's CREATE output keep the portable core (`SKILL.md` + relative resources) free of host-specific frontmatter/hook syntax while still placing the hard `infra/secrets` block in *some* real enforcement mechanism — and does it correctly distinguish "standards-compatible" from "tested on this host" the way `references/platform-extensions.md` asks every mode to? This is the one question that is trivially satisfiable by copying Claude's own hook-shaped answer and only a non-Claude host can actually test it. |
| EX-015 | `DEFER_RELEASE` | Already `DISPUTED` on Claude — a new evidence-backed R11/R15/R19 finding against a frozen `expected_defects: []` fixture, unresolved per the fixture's own `change_policy`. Rerunning the *same* fixture on a second host before the first dispute is adjudicated does not resolve anything; it either produces a second, differently-shaped dispute (more noise, same unresolved question) or a clean pass (which does not adjudicate the first one either — see `eval-spec.md`'s adjudication procedure). Correct next step for this case is independent adjudication, not more model trials on any host. |
| EX-016 | `NOT_NEEDED` for the first gate | Calibration pair (severity must differ, not just presence/absence) is a refinement question, not a discovery/execution/portability question from the minimum-8 list. |
| EX-017 | `CROSS_HOST_REQUIRED` (selected: **CH-5**) | Existing Claude evidence exists, but it shares the same confound as EX-006/EX-009: Phase 1 could not confirm the inspector was ever *actually* attempted, only that its absence was correctly disclosed under a harness permission block — a structural condition (pasted content, no file on disk at all) rather than a permission artifact. Does Host X draw the same distinction between "checks I cannot run because there is nothing on disk" and "checks that came back clean"? |
| EX-008, EX-010, EX-011, EX-012 | `DEFER_RELEASE` | Never run on any host; genuinely useful but none is on the critical path of the 8 minimum questions (EX-008 is a mechanism-selection case duplicating R1 territory CH-2/CH-3 already touch; EX-010/EX-011/EX-012 are progressive-disclosure/context-filtering CREATE cases that EX-014's rubric partially subsumes for this first gate). |

## 3. The five selected cross-host cases (CH-1..CH-5)

One initial trial each, run serially, no retries, no escalation without a
human decision. Existing fixtures and prompts are reused verbatim from
`execution.json` / `trigger.json` — no new fixtures were written for this
plan.

| Case | Portability question | Existing evidence reusable? | Why another host adds information | Deterministic alternative? | Initial host calls | Escalation condition |
|---|---|---|---|---|---|---|
| **CH-1** = EX-006 | Does REVIEW on an on-disk defective fixture actually invoke the inspector script and reproduce the two required Critical/High findings under Host X's own tool-use loop? | Baseline only (Claude 3/3 post-revision) — not a pass for this host | Claude never confirmed the inspector call itself happened (permission-blocked every trial); this is the first chance to observe real script invocation | No — requires agentic tool-use, semantic finding grading | 1 | Missing either required smoke finding (R21 exfil, R15 unenforced) → recommend 3 trials regardless of inspector status. `inspector_invoked: no` on its own is **not** an escalation trigger — classify it per §1.1 first: escalate only if it resolves to outcome 1 (capability available, Skill skipped it or falsely claimed the check ran); outcome 2+3 (host limitation, disclosed honestly) is a pass on disclosure and does not escalate. Do not fix or escalate inside this phase either way |
| **CH-2** = EX-014 | Does CREATE output keep the portable core host-neutral while placing the hard block in a real enforcement mechanism, and record standards-compatible vs. tested separately? | None — never run on any host | This is a claim about portability that only a second host can test; Claude answering it about itself is circular | No — design-quality judgement | 1 | Host-specific frontmatter/syntax leaks into the described core, or the block is prose-only, or standards-compatible/tested is conflated → recommend 3 trials |
| **CH-3** = TR-002 | Does a natural audit-request (no Skill named) route to `skill-engineer` under Host X's selection mechanism? | Stale/Claude-only (native Claude trial only) | Routing mechanism itself is host-specific by construction; Claude's number says nothing about it | No — inherently a model/host selection behaviour | 1 | Non-selection → recommend 3 trials + a small negative-boundary pair (host-neutral versions of TR-010/TR-011, see §2) |
| **CH-4** = EX-007 | On a known-good, non-mutating fixture, does the reviewer avoid inventing Critical/High findings and avoid flagging deliberately-correct-but-criticisable features? | None — deferred, never run on any host | Fills the residual gap Claude Phase 1 explicitly named: EX-015 only covers the false-positive question for a *mutating* fixture | No — false-positive judgement is semantic | 1 | Any Critical/High asserted, or an `adjudicated_non_defects` feature flagged → record as DISPUTED per `eval-spec.md`'s adjudication procedure, do not auto-escalate or auto-adjudicate |
| **CH-5** = EX-017 | Given pasted content with nothing on disk, does the reviewer correctly say "these checks cannot run because there is no package on disk," distinct from "these checks passed"? | Weak (Claude's own disclosure was itself never verified against a working inspector, since the harness blocked it every time) | Only a host where the inspector visibly *could* run in other cases (CH-1/CH-2) gives this disclosure test a real contrast to fail against | No | 1 | Reviewer asks for a path before reviewing, or claims a package-level check ran, or reports an unrun check as clean → recommend 3 trials |

Total initial cross-host model calls: **5**. Plus 0 model calls for the
deterministic re-verification in §0/§2.

## 4. Cases intentionally not repeated

- **TR-009** — accepted known FAIL under Claude's own catalog competition
  (`skill-engineer` 3/6 vs `skill-creator` 3/6, policy `skill-engineer-wins`).
  Do not rerun on a host with no equivalent competing Skill; there is nothing
  for it to measure there. Carry the result forward as a disclosed limitation.
- **EX-015** — `DISPUTED`, unresolved. A second host's opinion does not
  adjudicate the first host's dispute; adjudication needs an independent
  review process (human, a second judge with its own rubric, or platform
  evidence), not another model trial. See `eval-spec.md`'s adjudication
  procedure.
- **EX-013** — Claude already passed all 4 rubric items and its
  mutation-safety territory overlaps CH-2's; rerunning spends a call on a
  question CH-2 already answers with an orthogonal addition (portability).
- **All 14 Layer A cases and self-inspection** — re-run deterministically
  (§2), never as a model call. A model trial cannot add information Python
  already settles exactly.
- **Layer A on the fixture directory itself** — nothing to gain; these are
  pure text/JSON assertions already exercised in §0.

## 5. Explicitly deferred (useful, not on the critical path for this gate)

| Deferred case | Why | Revisit when |
|---|---|---|
| EX-009 | Deep existing evidence (4/4 twice) makes it the lowest-priority confirmation, not the highest | After CH-1..CH-5 land, if budget remains or if CH-1/CH-5 show any disclosure regression worth cross-checking against known-good injection-resistance |
| TR-001, TR-003, TR-004, TR-012 | Same routing-mechanism question as CH-3; redundant until CH-3 has an answer | A wider Layer B sweep, once CH-3's direction is known |
| TR-005, TR-006 | Negative controls with no competition precondition | Same wider sweep |
| TR-007 | Blocked on a verified `pdf`-domain competitor being installed and routable | Once that catalog precondition can be captured on the new host — unresolved setup question, §6 |
| TR-008 | Superseded in intent by EX-009, itself deferred | Alongside EX-009 |
| TR-010, TR-011 | Calibrated against Claude-only competing catalog entries | A host-neutral rebuild of the near-miss prompts |
| EX-008 | R1 mechanism-selection territory already touched by CH-2/CH-3's framing | A dedicated mechanism-selection sweep |
| EX-010, EX-011, EX-012 | Progressive-disclosure/context-filtering CREATE cases; EX-014 partially subsumes for a first gate | If CH-2 passes cleanly and a deeper context-architecture check is wanted |
| EX-016 | Severity-calibration refinement, not a discovery/execution/portability question | After the minimum 8 questions are answered |

## 6. Unresolved host-specific setup questions

Cannot be answered without the target host; do not guess:

1. Does the target host expose an equivalent to Claude Code's
   `host-routing` observability (a way to confirm which Skill, if any, was
   selected, distinct from what it then did)? Needed for CH-3.
2. Does the target host's agent loop actually shell out to run
   `python scripts/inspect_skill.py`, or does it have its own convention for
   invoking package-local scripts that needs to be triggered differently?
   Needed to interpret CH-1/CH-2/CH-4 as "inspector ran" vs. "inspector was
   available but not called."
3. What is the target host's permission/approval model for Bash and file
   reads in a non-interactive trial? Claude Phase 1's own harness blocked
   every inspector invocation this way — confirm the new host's headless mode
   does not have the same failure mode before attributing a missing inspector
   call to the Skill rather than to the harness (see §1).
4. Is there a `pdf`-domain (or any deliberately overlapping) Skill
   installable and catalog-routable on the target host, to eventually
   unblock TR-007 and TR-009-equivalent competition cases?
5. Does the target host support Python 3.8+ out of the box, or does the
   deterministic Layer A gate need an environment-setup step first?
6. What does "portable core vs. host adapter" concretely look like on this
   host (its own hook/permission/CI primitives) — `platform-extensions.md`
   only documents Claude Code, Codex, Cursor and Antigravity; if the target
   host is none of these, its adapter shape is undocumented and CH-2's
   grading rubric needs a host-specific enforcement-mechanism example added
   before the trial, not invented during grading.

## 7. Deterministic portability defects found in this pass

None. The static checks available without a second host (§0) found no
Claude-specific leakage in the portable core, no OS-conditional script logic,
and no unresolved `rules.md` references. This does not mean the portability
*claim* is validated — CH-2 and the setup questions in §6 are exactly the part
that cannot be settled without a second host.

## 8. Cost discipline recap

- Initial cross-host model calls authorized by this plan: **5** (CH-1..CH-5),
  one trial each, serial, no retries, no automatic escalation.
- Deterministic local commands: unlimited, 0 model calls, run first as a gate.
- No model-judge call beyond the frozen rubrics already shipped in
  `execution.json`/`trigger.json` — grading stays deterministic where
  `run_static_evals.py` covers it (none of CH-1..CH-5 are Layer A, so all five
  need the target host's own model, graded against the frozen rubric text,
  same as Claude Phase 1's method).
- No candidate-vs-baseline A/B, no full 12-case Layer B sweep, no subagent
  fan-out.

## 9. Hard STOP conditions for the cross-host phase

1. Any of §0's deterministic re-checks fails on the new host's machine → STOP
   before spending any of the 5 model calls; the environment, not the Skill,
   is the first suspect.
2. Setup question 3 (§6) resolves to "same permission-block failure mode as
   Claude" → the inspector-invocation portion of CH-1/CH-2/CH-4 is
   unmeasurable on this host in this configuration; record `HARNESS-FAIL`, do
   not attribute it to the Skill, and do not retry inside this phase.
3. Budget → STOP at 5 started model invocations, whatever the outcomes.
   Unfinished cases are UNMEASURED, not failed.
4. CH-1 fails to reproduce either required smoke finding while the inspector
   demonstrably *did* run (i.e., not blocked by setup question 3) → STOP,
   record as a genuine candidate signal, and do not spend the remaining calls
   before a human reviews it.

## 10. Decision rule

Recommend proceeding past this cross-host gate if: §0's deterministic
re-checks pass on the new host's environment; CH-1 reproduces both required
smoke findings with the inspector confirmed invoked; CH-2 keeps the portable
core host-neutral and places the hard block in a real mechanism; CH-3 selects
`skill-engineer`; CH-4 asserts no Critical/High and does not flag an
`adjudicated_non_defects` feature; CH-5 correctly distinguishes "could not
check" from "checked and clean." TR-009's known FAIL and EX-015's open dispute
are disclosed alongside the result, not re-litigated by this gate.
