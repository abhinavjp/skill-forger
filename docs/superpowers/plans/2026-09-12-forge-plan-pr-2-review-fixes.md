# Forge Plan PR #2 Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve every actionable PR #2 review thread while preserving the portable `forge-plan` contract and making local behavioral-evaluation limits explicit.

**Architecture:** Keep one `forge-plan` Skill with shared authority, blocking, and handoff semantics in `SKILL.md`; keep mode-specific wording in the existing references. Move packaging roster/eval-dispatch policy to one trusted Python module, and add a `forge-plan`-specific deterministic gate plus an optional three-runner behavioral harness that reports unavailable host execution as `UNMEASURED`.

**Tech Stack:** Markdown Agent Skill package, JSON eval corpus, Python 3.8+ stdlib, `unittest`, existing packaging validator.

**Spec:** `docs/specs/2026-09-12-forge-proportional-planning.md`

## Global Constraints

- Every execution packet closes product, architecture, scope, and material alternative decisions before implementation.
- If compact mode cannot close material decisions, evidence, or safety constraints, identify the exact gap and offer scope reduction, detailed mode, or an upstream return.
- Provide a formal read-only `to-tickets` handoff when requested or approved as the next step; it references canonical plan content and never publishes.
- Planning approval is terminal for the Skill and grants no implementation or external-mutation authority.
- Behavioral claims require fixture-driven candidate, accepted-baseline, and no-Skill trials; unavailable live behavior remains `UNMEASURED`.
- Keep the portable core free of named hosts, models, agents, absolute paths, hooks, and required host-only features.
- Preserve unrelated pre-existing untracked files; do not commit, push, merge, publish tickets, or release without separate authorization.

## File Map

- Modify `.claude-plugin/marketplace.json`, `plugin/plugin.json`, and `plugin/.claude-plugin/plugin.json` for the synchronized release version.
- Create `packaging/plugin_policy.py` as the single trusted source for canonical Skill IDs and eval-validator paths.
- Modify `packaging/validate_plugin.py` and `packaging/test_validate_plugin.py` to consume that policy instead of duplicating the roster.
- Modify `plugin/skills/forge-plan/SKILL.md` and `plugin/skills/forge-plan/references/compact-mode.md` for blocked completion and direct approved-plan handoff semantics.
- Create `plugin/skills/forge-plan/evals/run_static_evals.py` for trusted `forge-plan`-specific deterministic checks.
- Create `plugin/skills/forge-plan/evals/run_behavioral_evals.py` for fixture-driven candidate/baseline/no-Skill execution when explicit trusted runner commands are supplied; no commands means `UNMEASURED`, never pass.
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

  Define the four canonical IDs and their validator paths once, import them from both Python consumers, and set all four advertised versions to `2.1.1`.

- [ ] **Step 4: Run the focused test and manifest validator**

  Run: `python packaging\test_validate_plugin.py -v`

  Expected: PASS.

  Run: `python packaging\validate_plugin.py`

  Expected: `RESULT: PASS`.

### Task 2: Close blocked plans and add the direct approved-plan handoff branch

**Files:**
- Modify: `plugin/skills/forge-plan/SKILL.md`
- Modify: `plugin/skills/forge-plan/references/compact-mode.md`
- Modify: `plugin/skills/forge-plan/references/execution-packet.md`
- Modify: `plugin/skills/forge-plan/evals/execution.json`

**Interfaces:**
- The main Skill owns two observable routes: normal proportional planning and a direct read-only handoff from a fresh approved plan.
- A material unresolved decision returns a blocked/upstream outcome and cannot reach plan approval.

- [ ] **Step 1: Add failing contract assertions**

  Add deterministic eval cases asserting that the Skill has an explicit blocked/upstream outcome, forbids approval with material unresolved decisions, validates freshness in the direct handoff route, and emits a read-only handoff when tracker conversion is an approved next step.

- [ ] **Step 2: Run the target eval gate**

  Run: `python plugin\skills\forge-plan\evals\run_static_evals.py --json`

  Expected: FAIL because the current Skill has no direct handoff branch and permits explicitly blocked decisions at completion.

- [ ] **Step 3: Implement the smallest wording/contract change**

  Add the direct branch before mode selection; require approval-hash/freshness validation; state that stale or unresolved material decisions block approval and return upstream; update compact-mode and packet completion language to remove “unresolved blockers” as an acceptable approved state; state that an approved tracker-conversion next step produces a read-only handoff without tracker mutation.

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
- `run_behavioral_evals.py [--fixture FILE] [--candidate-command CMD] [--baseline-command CMD] [--no-skill-command CMD] [--json]` sends each selected case and fixture to the explicitly supplied trusted runner commands; absent any required runner reports `UNMEASURED`.
- Runner input is a JSON envelope containing case ID, prompt, expected assertions, fixture content, and role (`candidate`, `baseline`, or `no-skill`). Runner output must be JSON; malformed output or nonzero exit is a recorded failure.

- [ ] **Step 1: Add failing packaging tests**

  Assert the canonical policy dispatches `forge-plan` to its target-specific static runner, the runner executes at least one deterministic case, the fixture is loaded, and a no-command behavioral run reports `UNMEASURED` rather than PASS.

- [ ] **Step 2: Run the focused tests**

  Run: `python packaging\test_validate_plugin.py -v`

  Expected: FAIL because the target-specific runner, fixture, and policy dispatch do not yet exist.

- [ ] **Step 3: Implement the trusted static runner and fixture**

  Implement named validators for the blocked-completion contract, direct handoff contract, single-authority references, and behavioral-harness boundary. Keep the corpus as data and refuse command fields from eval files. Add deterministic cases to `execution.json` that invoke those named validators.

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

  Confirm: all four PR inline threads are addressed; material blockers cannot be approved; direct handoff freshness and read-only boundaries are explicit; the approved-next-step handoff is present; the release version is synchronized; static and behavioral evidence are separated; unavailable live behavior is labeled `UNMEASURED`.
