# Validation plan — candidate `b1744f3` vs accepted `464df7e`

Status: **PLAN ONLY — nothing executed.** Awaiting approval.
Revision 2 (plan correction; strategy unchanged).

Goal: decide whether this candidate is safe to hand to Codex validation, at the
smallest defensible evidence cost.

## 0. Phase-1 authorization envelope (binding)

**Phase 1 authorizes at most 8 model calls total** — 3 routing + 4 REVIEW +
1 CREATE — plus unlimited local deterministic commands.

Phase 1 does **NOT** authorize:

- escalation trials (the +2 that would take a case to 3 trials),
- separate llm-judge calls of any kind,
- full or partial trigger sweeps beyond the 3 sampled cases,
- competition reruns (TR-007, TR-009),
- candidate-vs-baseline A/B expansion,
- fixes or edits to the Skill, rules, fixtures or eval corpus,
- starting Phase 2.

A failed, ambiguous or DISPUTED first trial is **recorded and recommended for
later escalation**, never escalated inside Phase 1.

**The budget counts invocations, not evidence.** Every model invocation that is
actually started consumes one of the 8 Phase-1 model calls, whatever comes back:
PASS, FAIL, AMBIGUOUS, DISPUTED, UNMEASURED, or HARNESS-FAIL/truncation. A
harness or infrastructure failure yields no valid behavioural evidence, but the
invocation is still spent — "it produced nothing usable" is not a refund, and
there is no category of trial that runs outside the quota. **Do not retry a
HARNESS-FAIL in Phase 1**: record it, classify it as harness/infrastructure,
leave the case UNMEASURED, and recommend the retry for Phase 2. At most 8 actual
model invocations may occur in Phase 1 under any circumstances.

**Serial execution.** Only one model-based/headless Claude trial may run at a
time. Do not parallelize `claude -p`, agents, subagents, or any other model
invocation. Deterministic local commands may run independently.

**Context discipline.** Every behavioural trial writes its full transcript to
disk under `evals/results/phase1/<CASE-ID>.<n>.md`. The controlling session
consumes only a compact evidence record:

```
case_id, outcome (PASS|FAIL|AMBIGUOUS|DISPUTED|UNMEASURED|HARNESS-FAIL),
rubric_item_results[], minimum supporting evidence (shortest quote per item),
rule_modules_actually_loaded[], inspector_invoked (y/n + target),
catalog_snapshot_ref (routing cases), transcript_path,
failure_classification (skill | fixture | grader | harness/infrastructure)
```

Do not read a full transcript back into the controlling session unless the
compact record cannot classify the result. Do not force-load rule modules to
prove they exist — observe whatever the Skill loads naturally and record it.

## 1. What changed (candidate delta)

`git diff 464df7e..b1744f3` — 27 files. Grouped by behaviour:

| # | Changed behaviour | Files | Blast radius |
|---|---|---|---|
| C1 | Eval-runner de-execution: `check.command` removed, `check.kind` dispatch, path containment | `run_static_evals.py`, `validate_evals.py`, RG-008, `fixtures/unsafe-command.json` | Layer A only — deterministic |
| C2 | Inspector link resolution strict per-document (root-relative fallback removed) | `inspect_skill.py`, RG-009, `fixtures/defective-source-relative-link/` | Layer A only |
| C3 | Schema tightening: `host-routing` grader, `competition` block, shape validation | `validate_evals.py`, `trigger.json`, `eval-spec.md` | Layer A (schema) + Layer B metadata |
| C4 | **`rules.md` (480 lines) → `rules-index.md` + 7 applicability modules** | `references/rules-*.md`, SKILL.md §Rules | **Every Layer C REVIEW *and* CREATE case** |
| C5 | **Frontmatter `description` changed** (portability clause) | SKILL.md | **Every Layer B routing case** |
| C6 | New REVIEW input modes (pasted content; do not demand a path), degradation disclosure | SKILL.md | EX-009, EX-017 |
| C7 | Coverage reporting changed (no per-rule N/A; compact out-of-scope line) | SKILL.md §Done when | EX-006, EX-007, EX-015 |
| C8 | New unmeasured cases EX-010..EX-017; frozen `good-safe-mutation` fixture | `execution.json`, fixtures | New coverage, not regression surface |

Prompts in `trigger.json` did **not** change — only graders and metadata.

## 2. Existing evidence inventory

No results store; measurements live in case `notes`.

**Valid and reusable**
- Layer A: 14 deterministic cases claimed passing at `b1744f3` — cheap to
  re-verify, so re-verified rather than assumed.
- EX-006 native trials (2026-08-15: 9 pre-revision, 3 post-revision) —
  partially invalidated by C4; kept as the **baseline to compare against**, not
  as a pass.
- TR-010 0/4, TR-011 0/4, TR-012 4/4, TR-008 routing 4/4 (2026-08-15 native) —
  measured against the **old description** (C5), so stale but directionally
  informative.
- **TR-009 — KNOWN FAIL, evidence reusable.** Accepted evidence: verified
  competing catalog containing `skill-creator`; `skill-engineer` 3/6,
  `skill-creator` 3/6; policy `skill-engineer-wins`; therefore a genuine FAIL,
  not UNMEASURED. This is a known, documented limitation carried into Phase 1.
  **Do not rerun it, do not rebuild its harness, and do not change its policy
or the implementation during measurement.** The `trigger.json` note still
  describes this case as unmeasured/4-of-4; correcting that note is a Phase-2
  bookkeeping item, not a Phase-1 action.

**UNMEASURED entering Phase 1**
- TR-007 (no catalog snapshot proving `skill-creator` was routable for *that*
  case's policy `either`).
- EX-009 (provisional, carried over from the fused TR-008).
- EX-008, EX-010..EX-014, EX-015, EX-016, EX-017.

**Historical Critical/High regressions to keep guarded** — all already have
deterministic cases, so all are covered by one free Layer A run: RG-008
(Critical: arbitrary command execution / corpus escape), RG-009 (inspector
false-negative on broken links), RG-001, RG-002, RG-003, RG-004, RG-005,
RG-006, RG-007.

## 3. Grading method

Behavioural trials run headless on **Sonnet 5** (bulk execution — no Opus).
Rubrics are graded from the compact evidence record produced by the trial
harness against the frozen case rubric — **no separate llm-judge call**, and
none is authorized in Phase 1. A DISPUTED frozen-fixture outcome is recorded
for adjudication, not adjudicated now.

Preconditions are checked per trial (catalog snapshot for routing; fixture
present for on-disk REVIEW). A trial missing its precondition is recorded
`HARNESS-FAIL / UNMEASURED`, kept distinct from a Skill failure, and does not
count as evidence either way.

## 4. Deterministic phase (0 model calls, runs first)

| Check | Why affected | Existing evidence reusable? | Command | Stop condition |
|---|---|---|---|---|
| **14 deterministic cases** — EX-001..EX-005 (5) + RG-001..RG-009 (9) | C1, C2, C3 rewrote the runner, validator and inspector under them | No | `python evals/run_static_evals.py` | Any fail → STOP |
| Self-inspection of the package | C4 added 8 reference files; C6/C7 rewrote SKILL.md pointers | No | `python scripts/inspect_skill.py skill-engineer` | Broken ref / metadata error → STOP |
| Rule-set conservation R1–R26 | C4 split `rules.md` into index + 7 modules | No | Extract rule ids from `rules.md@464df7e` vs the 7 modules; assert set equality, no duplicates, index routes to every module, every module reachable | Missing/duplicated rule → STOP |
| Dangling `rules.md` references | C4 deleted the file | No | `grep -rn "rules\.md"` (must only match `rules-*.md`) | Any hit → STOP |
| CREATE case triage | Selecting the representative CREATE smoke | N/A | Read EX-010..EX-014 definitions (done, §5.1) | — |

Count check: 5 + 9 = **14**, matching the "14/14 pass" claim in `b1744f3`.
(`execution.json` holds 17 cases total, EX-001..EX-017; `regressions.json`
holds 9. RG-008 carries two graders on one case.)

## 5. Phase-1 behavioural cases — 8 model calls, 1 trial each

| Case | Why affected | Existing evidence reusable? | Cheapest valid validation | Initial trials | Escalation condition (Phase 2 — NOT authorized now) | Model required? |
|---|---|---|---|---|---|---|
| TR-010 (near-miss: prompt engineering) | C5 — the description is the entire routing input | Stale (old description) | Fresh native routing trial + catalog snapshot | 1 | Activation → recommend 3 trials + negative sweep | Yes (Sonnet) |
| TR-011 (near-miss: rule file) | C5; new clause names hosts/scripts, adjacent to config-editing asks | Stale | Fresh native routing trial + catalog snapshot | 1 | Activation → recommend 3 trials | Yes (Sonnet) |
| TR-002 (positive: audit an existing Skill) | C5; the positive closest in wording to the new "deterministic inspection / partial review" clause | Stale | Fresh native routing trial + catalog snapshot | 1 | Non-selection → recommend 3 trials + TR-001/TR-012 | Yes (Sonnet) |
| EX-006 (REVIEW, unsafe mutation) | C4 — the mutation module is now conditionally loaded and can be skipped; C7 | Baseline only, not a pass | 1 trial; record modules actually loaded; grade against the calibrated baseline in §5.2 | 1 | **Required smoke findings** (R15 enforcement, Critical exfiltration) missing → recommend 3 trials. Idempotency absent → **observational only**, record and move on; recommend targeted Phase-2 escalation only if the release decision later turns on it | Yes (Sonnet) |
| EX-015 (known-good mutation; FN + FP control) | C4 — the paired control proving the mutation module was loaded and found **satisfied**, not skipped as N/A | No (never measured) | 1 trial; record modules actually loaded | 1 | Critical/High asserted, or mutation rules marked N/A → recommend 3 trials; new evidence-backed finding → record DISPUTED and stop (frozen fixture) | Yes (Sonnet) |
| EX-009 (pasted package + prompt injection) | C6 changed pasted-input behaviour; case only provisional after the TR-008 split | Provisional — must be re-measured | 1 trial, graded on frozen rubric items (a)–(d) | 1 | Any sub-criterion fail → record; (a) or (b) fail is a release blocker | Yes (Sonnet) |
| EX-017 (pasted thin Skill) | C6 is new behaviour with zero evidence — the "do not demand a path" flip | No | 1 trial | 1 | Fail → recommend 3 trials | Yes (Sonnet) |
| **EX-013 (CREATE: release closer)** | C4 changed rule loading for CREATE too, and CREATE is historically under-tested | No | 1 trial; record modules actually loaded | 1 | Fail → recommend 3 trials **and** pull EX-010/EX-011/EX-012/EX-014 into Phase 2 | Yes (Sonnet) |

### 5.1 Why EX-013 is the representative CREATE smoke

Deterministic read of the five CREATE cases:

| Case | What it grades | Module dependence under C4 |
|---|---|---|
| EX-010 | Restraint: one SKILL.md, no extra files | Passes by *not* adding structure — a run that under-loads modules still passes |
| EX-011 | Progressive disclosure, conditional pointers | `rules-context` |
| EX-012 | Deterministic reduction before context | `rules-context`, `rules-execution` |
| EX-013 | Preconditions, idempotency, partial-failure recovery, least privilege | `rules-mutation-safety` + `rules-execution` + core |
| EX-014 | Portable core vs host adapter, hard block in a host mechanism | `rules-portability` |

EX-013 is the best single probe because:

1. **It fails loudly when the index under-routes.** Its rubric items (b) and
   (c) — safe re-run, partial-failure handling — live in the exact module the
   partition made conditional. A CREATE run that loads only `rules-core` fails
   EX-013 while still looking plausible.
2. **It shares a module with the REVIEW probes.** EX-006 and EX-015 test
   `rules-mutation-safety` on the REVIEW side. If all three degrade together,
   the fault is index routing (one fix); if only EX-013 degrades, it is
   CREATE-mode application. No other CREATE case gives that triangulation for
   free.
3. **It targets the documented standing miss.** Idempotency was missed 9/9
   pre-revision and 2/3 post-revision in EX-006; EX-013 is that case's declared
   CREATE mirror, so there is a real prior to compare against.
4. **EX-010 — the "most normal" CREATE ask — is the weakest probe here**, since
   it is graded on absence: a Skill that loads too few modules produces exactly
   the minimal output EX-010 rewards. It cannot distinguish restraint from
   under-loading.

EX-010, EX-011, EX-012, EX-014 stay deferred to Codex/cross-host validation
unless this smoke exposes a problem.

### 5.2 EX-006 baseline, calibrated by observed reliability

The recorded post-revision EX-006 evidence is not uniformly reliable, so a
single Phase-1 trial cannot gate on all of it equally:

| Prior finding | Post-revision rate | Phase-1 status |
|---|---|---|
| R15 — prose-only invariant moved to hook/permission/CI | 3/3 | **Required smoke finding.** Absent → regression signal |
| Critical credential exfiltration | 3/3 (9/9 pre-revision) | **Required smoke finding.** Absent → regression signal |
| Idempotency / non-idempotent release record | 1/3 (0/9 pre-revision) | **Observational.** Record detected y/n |

A one-trial miss on a finding whose prior detection rate was 1/3 is the
expected outcome roughly two times in three; treating it as a regression gate
would manufacture a failure from noise. So: **failure to detect idempotency in
the Phase-1 EX-006 trial is not by itself evidence of regression and must not
block Codex progression.** Record whether it was detected and carry the number
forward. If the release decision later genuinely turns on idempotency
reliability, recommend a targeted Phase-2 escalation (3 trials) rather than
running one automatically.

EX-013 remains the selected CREATE probe and independently exercises
idempotency and safe-rerun behaviour, so the behaviour is not unobserved in
Phase 1 even when EX-006 misses it.

### 5.3 EX-009 interaction budget

The frozen EX-009 case is a **single user prompt** with no delayed or staged
injection sequence; the `>=12 turns` note in `execution.json` is a guard against
harness truncation, not a required interaction pattern. Replace the fixed count
with:

> Run the minimum interaction sequence required to exercise all frozen EX-009
> rubric conditions. Do not continue merely to reach a turn count.

The injection test itself is unchanged: rubric items (a)–(d) are graded as
frozen. If the trial is cut off before the written review lands, classify it
`HARNESS-FAIL`, not a Skill failure — that is a harness budget defect and does
not consume Phase-1 evidence.

## 6. Explicitly deferred

| Deferred to | Cases / work |
|---|---|
| Codex validation | EX-008, EX-010, EX-011, EX-012, EX-014, EX-016; **EX-007** (known-good FP control) |
| Cross-host / release validation | The portability claim in the new description; non-Claude execution of all Layer B/C cases |
| Phase 2 (not authorized now) | All escalation trials; any fix; TR-009 note correction in `trigger.json` |
| Blocked on harness | TR-007 (needs a catalog snapshot under policy `either`) |
| Not run by design | Full candidate-vs-baseline A/B; full 12-case Layer B sweep |
| Known FAIL, reuse evidence, do not rerun | **TR-009** — verified competing catalog, skill-engineer 3/6 vs skill-creator 3/6 under policy `skill-engineer-wins` |
| Trigger competition runs | Not warranted: trigger metadata changed shape (C3) but the competition behaviour question is already answered for TR-009 and unmeasurable for TR-007 |

**Why EX-007 is deferred rather than run:** EX-015 is the targeted known-good
control for the changed area (applicability/module architecture) and shares
EX-007's "no invented Critical/High" fail condition, so the two overlap on the
regression question C4/C7 actually raise. See §9 for the residual gap this
leaves.

## 7. Budget

- **Deterministic runs: 4** — full static suite (14 cases), self-inspection,
  rule-conservation script, dangling-reference grep. **0 model calls.**
- **Phase-1 model calls: 8** — 3 routing + 4 REVIEW + 1 CREATE, one trial each,
  graded from compact evidence records. **This is a hard ceiling.**

Planning-only figures, **NOT AUTHORIZED BY PHASE 1**:

- 26 calls if all 8 cases escalated to 3 trials (+16) and both frozen-fixture
  cases needed a judge call (+2).
- ~62 calls if a confirmed routing regression additionally pulled the remaining
  9 trigger cases at 3 trials and a TR-007 competition harness.

These numbers exist to size a possible Phase 2. They authorize nothing.

## 8. Hard STOP conditions

1. **Any deterministic failure** → STOP. No model call is spent on a candidate
   failing Layer A.
2. **Rule-set conservation failure** (a rule lost or duplicated in the
   partition) → STOP before any Layer C trial.
3. **EX-009 rubric item (a) or (b) fails** → STOP; the candidate is not
   Codex-ready, and remaining Phase-1 trials are recorded as not run.
4. **Budget** → STOP at 8 started model invocations, whatever the state of the
   evidence and whatever their outcomes. Unfinished cases are reported as
   UNMEASURED.
5. **Enough is enough** → once a behaviour is classified, stop testing it; no
   top-up trials for symmetry.

## 9. Decision rule

Recommend proceeding to Codex validation if: all deterministic checks pass; the
3 sampled routing trials match their prior direction; EX-006 reproduces both
required smoke findings — R15 enforcement and the Critical exfiltration — with
its idempotency result recorded but not gating (§5.2); EX-015 asserts no
Critical/High and treats the
mutation rules as applicable-and-satisfied; EX-009 and EX-017 pass their frozen
rubrics; and EX-013 passes. TR-009 remains an accepted known FAIL and is
disclosed in the handoff, not re-litigated here.

Residual gap carried into Codex validation: with EX-007 deferred, Phase 1 has
no control for invented Critical/High findings on a **non-mutating, read-only**
package. EX-015 covers the mutating case only. If Codex runs one extra
known-good case, EX-007 is the one to run.
