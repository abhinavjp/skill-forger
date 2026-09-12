# Forge Plan PR #2 Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve every actionable PR #2 review thread while preserving the portable `forge-plan` contract and making local behavioral-evaluation limits explicit.

**Architecture:** Keep one `forge-plan` Skill with shared authority, blocking, and completion semantics in `SKILL.md`; keep mode-specific wording in the existing references. Move packaging roster/eval-dispatch policy to one trusted Python module, and add a `forge-plan`-specific deterministic gate plus an optional three-runner behavioral harness that reports unavailable host execution as `UNMEASURED`.

**Tech Stack:** Markdown Agent Skill package, JSON eval corpus, Python 3.8+ stdlib, `unittest`, existing packaging validator.

**Spec:** `docs/specs/forge-plan-proportional-planning.md`

## Global Constraints

- Every execution packet closes product, architecture, scope, and material alternative decisions before implementation.
- If compact mode cannot close material decisions, evidence, or safety constraints, identify the exact gap and offer scope reduction, detailed mode, or an upstream return.
- Produce an approved, implementation-ready plan; any external publication is outside `forge-plan` and remains separately authorized.
- Planning approval is terminal for the Skill and grants no implementation or external-mutation authority.
- Behavioral claims require fixture-driven candidate, accepted-baseline, and no-Skill trials; unavailable live behavior remains `UNMEASURED`.
- Keep the portable core free of named hosts, models, agents, absolute paths, hooks, and required host-only features.
- Preserve unrelated pre-existing untracked files; do not commit, push, merge, publish external records, or release without separate authorization.

## File Map

- Modify `.claude-plugin/marketplace.json`, `plugin/plugin.json`, and `plugin/.claude-plugin/plugin.json` for the synchronized release version.
- Create `packaging/plugin_policy.py` as the single trusted source for canonical Skill IDs and eval-validator paths.
- Modify `packaging/validate_plugin.py` and `packaging/test_validate_plugin.py` to consume that policy instead of duplicating the roster.
- Modify `plugin/skills/forge-plan/SKILL.md` and `plugin/skills/forge-plan/references/compact-mode.md` for blocked completion and the approved-Plan boundary.
- Create `plugin/skills/forge-plan/evals/run_static_evals.py` for trusted `forge-plan`-specific deterministic checks.
- Create `plugin/skills/forge-plan/evals/run_behavioral_evals.py` for fixture-driven candidate/baseline/no-Skill execution when explicit trusted runner commands are supplied; no commands means `UNMEASURED`, never pass.
- Create `plugin/skills/forge-plan/evals/fixture_schema.py` for the versioned public runner-fixture allowlist and private baseline schema.
- Create `plugin/skills/forge-plan/evals/fixtures/approved-planning-context.json` as the portable approved-authority/repository fixture.
- Modify `plugin/skills/forge-plan/evals/execution.json` with deterministic gate cases that cover the corrected contract and behavioral-harness boundary.

### Task 1: Freeze release and packaging policy

**Files:**
- Create: `packaging/plugin_policy.py`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `plugin/plugin.json`
- Modify: `plugin/.claude-plugin/plugin.json`
- Modify: `packaging/validate_plugin.py`
- Modify: `packaging/test_validate_plugin.py`

**Interfaces:**
- Produces `EXPECTED_SKILL_IDS` and `CANONICAL_EVAL_VALIDATORS` from `packaging.plugin_policy` for both packaging validation and its tests.

- [ ] **Step 1: Add a failing policy-consumption test**

  Assert the packaging test obtains the Skill roster and eval-validator mapping from the trusted policy module rather than a second literal roster.

- [ ] **Step 2: Run the focused test**

  Run: `python packaging\test_validate_plugin.py -v`

  Expected: FAIL until `plugin_policy.py` exists and both consumers use it.

- [ ] **Step 3: Implement the canonical policy and version bump**

  Define the canonical IDs and their validator paths once, import them from both Python consumers, and preserve the synchronized advertised release version (`2.2.0`).

- [ ] **Step 4: Run the focused test and manifest validator**

  Run: `python packaging\test_validate_plugin.py -v`

  Expected: PASS.

  Run: `python packaging\validate_plugin.py`

  Expected: `RESULT: PASS`.

### Task 2: Close blocked plans and preserve the approved-Plan boundary

**Files:**
- Modify: `plugin/skills/forge-plan/SKILL.md`
- Modify: `plugin/skills/forge-plan/references/compact-mode.md`
- Modify: `plugin/skills/forge-plan/references/execution-packet.md`
- Modify: `plugin/skills/forge-plan/evals/execution.json`

**Interfaces:**
- The main Skill owns one observable route: normal proportional planning ending in an approved, implementation-ready Plan.
- A material unresolved decision returns a blocked/upstream outcome and cannot reach plan approval.

- [ ] **Step 1: Add failing contract assertions**

  Add deterministic eval cases for the structural Skill/package contract and the blocked/upstream completion boundary. External publication is outside this Skill.

- [ ] **Step 2: Run the target eval gate**

  Run: `python plugin\skills\forge-plan\evals\run_static_evals.py --json`

  Expected: FAIL until the structural contract and blocked/upstream wording are aligned.

- [ ] **Step 3: Implement the smallest wording/contract change**

  State that stale or unresolved material decisions block approval and return upstream; update compact-mode and packet completion language to remove “unresolved blockers” as an acceptable approved state; stop at the approved, implementation-ready Plan and leave external publication to a separately authorized downstream actor.

- [ ] **Step 4: Run target and corpus checks**

  Run: `python plugin\skills\forge-plan\evals\run_static_evals.py --json`

  Expected: all deterministic contract cases PASS; host-dependent cases are reported as `UNMEASURED`.

### Task 3: Add executable behavioral-evaluation seams without overstating live proof

**Files:**
- Create: `plugin/skills/forge-plan/evals/run_static_evals.py`
- Create: `plugin/skills/forge-plan/evals/run_behavioral_evals.py`
- Create: `plugin/skills/forge-plan/evals/fixtures/approved-planning-context.json`
- Modify: `plugin/skills/forge-plan/evals/execution.json`
- Modify: `packaging/test_validate_plugin.py`

**Interfaces:**
- `run_static_evals.py [--evals DIR] [--json]` validates the corpus and runs only trusted in-process checks; it returns schema `case_count`/`errors` plus deterministic results and never executes corpus-provided commands.
- `run_behavioral_evals.py [--fixture FILE] [--candidate-argv-file FILE] [--baseline-argv-file FILE] [--no-skill-argv-file FILE] [--judge-argv-file FILE] [--json]` sends each selected case and fixture to the explicitly supplied trusted argv commands; absent any required runner reports `UNMEASURED`.
- Runner input is a JSON envelope containing case ID, trial index, prompt, public fixture content, and role (`candidate`, `baseline`, or `no-skill`); expected assertions, rubrics, and accepted-baseline scenarios stay in the trusted control plane. Runner output must be normalized evidence JSON; malformed output or nonzero exit is a recorded failure.

- [ ] **Step 1: Add failing packaging tests**

  Assert the canonical policy dispatches `forge-plan` to its target-specific static runner, the runner executes at least one deterministic case, the fixture is loaded, and a no-command behavioral run reports `UNMEASURED` rather than PASS.

- [ ] **Step 2: Run the focused tests**

  Run: `python packaging\test_validate_plugin.py -v`

  Expected: FAIL because the target-specific runner, fixture, and policy dispatch do not yet exist.

- [ ] **Step 3: Implement the trusted static runner and fixture**

  Implement named validators for the blocked-completion contract, approved-Plan boundary, single-authority references, and behavioral-harness boundary. Keep the corpus as data and refuse command fields from eval files. Add deterministic cases to `execution.json` that invoke those named validators.

- [ ] **Step 4: Implement the optional three-role behavioral harness**

  Load the fixture and execution cases, invoke only maintainer-supplied commands, capture role/case/exit/output metadata, and classify missing runtime/catalog/model/provider evidence as `UNMEASURED`. Add a strict option that exits nonzero when required roles were not run, without changing the default package validation result.

- [ ] **Step 5: Run static and harness checks**

  Run: `python plugin\skills\forge-plan\evals\run_static_evals.py --json`

  Expected: schema valid, deterministic contract cases PASS, host cases `UNMEASURED`.

  Run: `python plugin\skills\forge-plan\evals\run_behavioral_evals.py --json`

  Expected: explicit `UNMEASURED` status and no false PASS.

### Task 4: Integrated verification and final semantic review

**Files:**
- Test: `packaging/test_validate_plugin.py`
- Verify: all files in the preceding tasks

- [ ] **Step 1: Run the complete focused package test**

  Run: `python packaging\test_validate_plugin.py -v`

  Expected: all tests PASS.

- [ ] **Step 2: Run package validation and inspect every Skill**

  Run: `python packaging\validate_plugin.py`

  Expected: `RESULT: PASS`, with no broken references, personal paths, or platform extensions.

- [ ] **Step 3: Run diff hygiene checks**

  Run: `git diff --check HEAD`

  Expected: no whitespace errors; unrelated pre-existing untracked files remain untouched.

- [ ] **Step 4: Perform final semantic review**

  Confirm: all PR threads are addressed; material blockers cannot be approved; the Plan stops at approved implementation-ready output; the release version is synchronized; static and behavioral evidence are separated; unavailable live behavior is labeled `UNMEASURED`.

### Re-review addendum: strict behavioral grading

The re-review at head `3291c74` found two additional issues. Remove the
hardcoded release literal from `packaging/test_validate_plugin.py`; synchronized
manifest equality is the only release check. Replace the behavioral harness's
zero-exit/JSON-only acceptance with a strict runner contract:

- runner output contains only `assertions` and optional `metrics`;
- every expected assertion appears exactly once with exact text, boolean
  `passed`, and non-empty `evidence`;
- missing, unknown, malformed, or non-JSON assertion evidence is incomplete and
  fails the run;
- a complete response with failed assertions is graded incorrect, not treated
  as incomplete;
- candidate, accepted-baseline, and no-Skill results are compared per case;
- correctness and material omissions are reported before optional efficiency
  metrics; candidate regression against baseline fails the run;
- missing roles remain `UNMEASURED`, and `--strict` exits nonzero;
- runner commands remain explicit maintainer input and execute with `shell=False`.

Regression coverage uses temporary trusted runners for empty output, malformed
JSON, nonzero exit, missing assertions, complete three-role comparison,
candidate regression, and strict missing-role behavior. Required checks:

```text
python packaging/test_validate_plugin.py -v
python packaging/validate_plugin.py
python plugin/skills/forge-plan/evals/run_static_evals.py --json
python plugin/skills/forge-plan/evals/run_behavioral_evals.py --json
python plugin/skills/forge-plan/evals/run_behavioral_evals.py --strict --json
git diff --check 2fcb82ce50332de2ce5ff97d15d652098d7a3655...HEAD
```

### Re-review addendum: trusted graders and differential semantics

The re-review at head `b572dc6` found that the behavioral runner could
self-attest `passed` assertions and that any incorrect baseline or no-Skill
result incorrectly failed the whole comparison. The runner now emits only
normalized execution evidence. Correctness is derived centrally from the
case-declared grader: deterministic validators run in-process, while
`llm-judge` requires an explicit maintainer-supplied judge command and a
strict assertion-result schema. Unsupported or unavailable graders remain
`UNMEASURED`; a runner that parrots expected assertions cannot pass.

Comparisons are per assertion and report both `candidate_vs_baseline` and
`candidate_vs_no_skill`, including correctness and material-omission deltas.
Baseline/no-Skill incorrectness is comparison evidence; execution fails only
for runner/grader errors, incomplete required roles, candidate incorrectness,
or candidate regressions. Regression coverage includes candidate improvement
over both comparators, no-Skill regression detection, malformed judge output,
and self-attesting runner rejection.

### Re-review addendum: clean-room harness, corpus, and branch integration

The clean-room review at head `61aec34` found seven remaining findings. This
pass freezes the following contracts before implementation:

- Runner and judge process inputs use validated JSON argv files, never shell
  command strings or `shlex`; arguments are passed directly with `shell=False`.
- Runner input contains only case ID, prompt, tags, role, and fixture. Expected
  assertions and rubrics are grader-only data and are never exposed to the
  execution adapter.
- Repository-static validators run only through `run_static_evals.py`. The
  behavioral harness excludes static-only cases and reports explicit
  `UNMEASURED` classification when selected.
- One assertion finalizer owns schema completeness, duplicate/conflict handling,
  failed behavioral assertions, correctness, and omission counts. Complete
  grading reports `failed_assertions` as material omissions; missing grader
  assertions remain a separate schema field.
- Differential reports index every expected assertion and emit lost/gained
  assertions, pass-count deltas, omission deltas, improvement, and regression.
  Any candidate loss against either comparator fails the run.
- Behavioral corpus loading validates the canonical case schema before spawning
  processes, rejects empty/duplicate/malformed cases, and classifies missing
  versioned metrics as `UNMEASURED` rather than zero or silently omitting them.

The current PR branch is also merged with the latest `main`; conflict
resolution preserves the intended proportional `forge-plan` package while
retaining unrelated current-main packaging and repository changes. Verification
must cover argv paths containing spaces/backslashes, oracle-free runner input,
static-only routing, mixed assertion losses, malformed corpora, and the full
package/validator/static/harness gates before delivery.

### Re-review addendum: trials, metrics, portability, and scope correction

The clean-room re-review at head `93eb3e0` found five remaining roots and
retracted the earlier downstream-conversion requirement as unsupported by committed
authority. This pass therefore:

- keeps accepted-baseline scenarios private to the trusted judge/control plane;
- validates positive integer `trials` (default `1` when omitted), sends one-based `trial_index` to runner
  and judge, requires every role/trial, and compares matching trials without
  hiding any trial regression;
- validates metric enums, booleans, nonnegative integer counts, bounded
  coverage, and typed collection fields, with per-field `UNMEASURED` defaults;
- keeps the new eval runners compatible with Python 3.8+ typing syntax;
- treats the static evaluator as structural/package evidence only, not a
  semantic heading-presence claim; and
- removes downstream-conversion ownership from forge-plan, its trigger/eval case,
  and the tracked plan/research language. Forge-plan ends at an approved
  implementation-ready Plan; later publication is a separate actor and
  authorization.

Regression coverage includes recursive oracle-key checks, 3-trial/9-invocation
cardinality, missing-trial failure, metric boundary/type validation, and the
existing static/package/harness gates.
