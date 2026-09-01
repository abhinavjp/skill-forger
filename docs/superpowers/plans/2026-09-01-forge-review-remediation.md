# Implementation Plan — Forge final-review remediation

Remediate the five blocking findings raised by the final semantic review of the
Forge portable SDLC suite at `1d5cf7e`, so the branch
`codex/forge-portable-sdlc-spec` can be finished.

- Upstream specification: `docs/specs/forge-portable-sdlc.md`
- Upstream plan: `docs/superpowers/plans/2026-09-01-forge-portable-sdlc.md`
- Review record (source of truth for WHAT must be fixed):
  `.superpowers/sdd/2026-09-01-forge-portable-sdlc-plan-v2/progress.md` § Section 10
- Baseline revision for this plan: `1d5cf7e`

---

## 1. Goal and non-goals

### Goal

Close review findings R1–R5 so that:

- the shipped static eval command measures something and the `brain-adapter`
  fixture is actually exercised;
- the static runner works under its own documented CLI invocation;
- `can_enter_stage` cannot be walked past by an unlabelled or malformed mutation
  record (AC-021 holds);
- packaging validation pins the payload the manifests advertise.

### Non-goals

- No change to Forge stage semantics, Skill prose, spec, or the upstream plan.
- No change to `merge-sentinel`, `skill-engineer`, `skill-prospector`, or
  `.gitignore`.
- No new validator kinds, no general eval framework, no CLI for
  `workflow_state.py` (deferred — see §12).
- No rewrite of Skill `description` frontmatter (deferred — see §12).
- No push, squash, PR, or merge.
- No fixing of the untracked `.claude/` or `inspect_out.json` paths; they are
  external scope and must never be staged.

---

## 2. Relevant existing state

Established by review discovery; do not rediscover.

| Fact | Evidence |
|---|---|
| No committed case carries a `static` wrapper | `grep -c '"static"'` = 0 across `plugin/shared/forge/evals/*.json` and `plugin/skills/forge-*/evals/*.json` |
| Documented command measures nothing | `run_static_evals.py --json` → `{"passed":0,"failed":0,"skipped":13}`, exit 0 |
| `brain-adapter` fixture is orphaned | `fixtures/brain-adapter/{input,expected}.json` exist; no case references them |
| `_load_workflow_state` cannot resolve `plugin.*` as a script | `run_static_evals.py:73-76`; no `sys.path` insertion anywhere in the module |
| `_load_v1_validator` never raises `CorpusError` for a missing file | `run_static_evals.py:65-71`; `spec_from_file_location` returns a spec for a nonexistent path |
| Post-hoc check is keyed on a caller-supplied label | `workflow_state.py:258`; probe: unlabelled mutation at T1 + approval at T2 → `ALLOWED` |
| Malformed `mutations` fails open | `workflow_state.py:254-256` returns `False`; contrast `:133-134` which fails closed |
| Mutation record shape is undocumented | no `mutations` key described in `plugin/shared/forge/references/workflow-contract.md` |
| Only `stage: "implementation"` mutation records exist in tests/fixtures | `test_workflow_state.py:220,237,251`; no fixture depends on stage-based exclusion |
| Packaging pins only three Skills | `packaging/validate_plugin.py:27`, relaxed check at `:118` |
| Test file duplicates the constant | `packaging/test_validate_plugin.py:23`, with `FORGE_SKILL_IDS` already present at `:29-34` |

Corpus contract facts (frozen, from `validate_evals.py`):

- `collect_files` excludes `fixtures/` but collects every other `.json` in an
  eval root — a new `static.json` beside `execution.json` is picked up by both
  the v1 validator and the static runner.
- Required v1 case fields: `version: 1`, `id`, `kind` ∈ {`trigger`,`execution`},
  `category` ∈ {`positive`,`negative`,`boundary`,`adversarial`,`regression`,…},
  `prompt`, non-empty `expected` mapping, non-empty `graders`.
- `deterministic` grader requires `check.kind` ∈ {`inspect`,`validate-evals`,
  `file-exists`,`validator`}; `validator` kind requires a string `check.validator`
  and permits no other field. `check.command` is rejected outright.
- The runner's `NONSTATIC_GRADER_CAPABILITIES` does not include `deterministic`,
  so a `deterministic`-graded case without a `static` wrapper is reported
  `skipped: no trusted static validator` — never a false pass.

---

## 3. Planning research and frozen decisions

**D1 — Static cases go in a new `plugin/shared/forge/evals/static.json`, not into
`execution.json`.** Attaching a `static` wrapper to an existing `FORGE-EX-*` case
would make the runner `continue` at `run_static_evals.py:357` and report that case
`passed`, destroying the `skipped: unavailable capabilities: llm-judge` signal that
keeps the 13 behavioural cases honestly UNMEASURED. A separate file adds coverage
without laundering a model-behaviour case into a deterministic pass.

**D2 — Static cases carry a `deterministic` grader with
`check.kind: "validator"`.** This is the only v1 grader that names trusted runner
code rather than a command, and it keeps the case valid under the v1 validator if
the `static` wrapper is ever stripped. It also means a static case degrades to
`skipped`, not to a pass, on a runner that does not understand `static`.

**D3 — Mutation scoping rule for `_has_post_hoc_mutation`.** A mutation record is
in scope for the gate being entered when its `stage` equals the target **or** its
`stage` is not a recognised stage string (absent, `None`, unknown, non-string).
Rejected alternative: consider every mutation regardless of stage — that would
treat legitimate Specification/Plan artifact writes preceding their own approval
as gate violations, contradicting `workflow-contract.md:28-33` where those stages
legitimately write their own artifacts. The chosen rule is fail-closed on exactly
the ambiguous case (an unlabelled mutation) and preserves the contract's stage
ownership model. Existing tests use `stage: "implementation"` and stay green.

**D4 — `mutations` polarity.** A present-but-malformed `mutations` value, and a
malformed entry within it, are violations. An **absent** `mutations` key remains
"no recorded mutations" and is not a violation — that is the documented default
(`state.get("mutations", [])`), and treating absence as a violation would block
every adapter that does not track mutations at all.

**D5 — Loader mechanism.** `_load_workflow_state` uses
`importlib.util.spec_from_file_location` against
`FORGE_ROOT / "scripts" / "workflow_state.py"`, mirroring `_load_v1_validator`.
Rejected alternative: inserting `REPO_ROOT` into `sys.path` — it mutates global
interpreter state from a library function and keeps the load dependent on
`REPO_ROOT = FORGE_ROOT.parents[2]` being positionally correct, which is exactly
the portability assumption a vendored copy of `plugin/shared/forge/` breaks.

**D6 — Packaging constant is the full eight IDs, and the subset check stays.**
The subset relaxation is what lets third-party Skills coexist and is retained;
only the required set grows. The test module's duplicate constant is widened to
match so the two cannot drift.

No user-owned decision is open. Nothing here reopens a settled Discovery decision.

---

## 4. Architecture / mechanism

No architectural change. Four localised mechanism changes:

1. `run_static_evals.py` — module loading becomes path-based and fails as
   `CorpusError`.
2. `workflow_state.py` — `_has_post_hoc_mutation` gains an explicit in-scope rule
   and fail-closed polarity. `can_enter_stage`'s signature, return shape, and all
   other rules are untouched.
3. `plugin/shared/forge/evals/static.json` — new corpus file; no runner change.
4. `packaging/validate_plugin.py` — one constant.

Contract surface changes: the `mutations` record shape becomes documented in
`workflow-contract.md`. No stage Skill changes.

---

## 5. Implementation strategy

Four tasks in dependency order. Tasks 1–3 are sequential (the corpus in Task 3
asserts behaviour fixed in Tasks 1 and 2); Task 4 is independent and last.

`read exact context → make specified change → run narrow deterministic
verification → commit → continue`

---

## 6. Workhorse execution contract

- Execute tasks in the order given. Do not reorder or parallelise.
- Do not redesign this plan. Do not perform new research. The decisions in §3
  are frozen.
- Read only the current task's named files unless a concrete failure requires
  more.
- Do not perform semantic or code review between tasks. Run only the named
  narrow verification.
- Do not perform unrelated cleanup or refactoring. Do not fix the deferred items
  in §12.
- One commit per completed task, using the suggested message.
- Do not revisit a completed task without concrete failing evidence.
- Never stage `.claude/` or `inspect_out.json`.
- Surface blockers and deviations; do not invent replacement design.
- Do not push, squash, open a PR, or merge.
- Finish all four tasks, then run §8, then §10 — once.

---

## 7. Implementation tasks

### Task 1 — Make the static runner loadable and fail as a corpus error

Closes **R2**, and the co-located loader guard **F5**.

**Objective.** `run_static_evals.py` loads `workflow_state` without depending on
`plugin.*` being importable, and reports a missing v1 validator as `CorpusError`.

**Dependencies.** None.

**Files.**
- Modify `plugin/shared/forge/evals/run_static_evals.py` — `_load_v1_validator`
  (`:65-71`), `_load_workflow_state` (`:73-76`).
- Modify `plugin/shared/forge/tests/test_run_static_evals.py` — add tests.

**Implementation.**
1. Add a module constant beside `VALIDATOR_PATH` (`:41`):
   `WORKFLOW_STATE_PATH = FORGE_ROOT / "scripts" / "workflow_state.py"`.
2. Replace the body of `_load_workflow_state` with a
   `spec_from_file_location("forge_workflow_state", WORKFLOW_STATE_PATH)` load
   mirroring `_load_v1_validator`. Raise
   `CorpusError("shared workflow state module cannot be loaded")` when the file
   is absent or the spec/loader is `None`. Cache the loaded module in a
   module-level variable so repeated static cases do not re-execute it.
3. In `_load_v1_validator`, add `if not VALIDATOR_PATH.is_file(): raise
   CorpusError("existing v1 validator cannot be loaded")` before
   `spec_from_file_location`.
4. Add a test that runs `run_static_evals.main(["--evals", <temp root>, "--json"])`
   in a subprocess with `cwd` outside the repository and a temp corpus containing
   one `normalization` static case, asserting exit 0 and `summary.passed == 1`.
   Use `sys.executable` with the script path, not `-m`, to reproduce the reported
   failure mode.
5. Add a test that a missing validator path yields `CorpusError`, not
   `FileNotFoundError` (monkeypatch `run_static_evals.VALIDATOR_PATH` to a
   nonexistent path and assert the raised type).

**Must not change.** The `static` wrapper contract, `VALIDATOR_KINDS`, `CHECKS`,
any check function body, the trust-boundary helpers (`_safe_path`,
`_contains_command`, `_validate_fixture_directory`), or the CLI surface.

**Narrow verification.**
```bash
python -m unittest plugin.shared.forge.tests.test_run_static_evals -v
```
Expected: OK, with the two new tests present and passing.

**Acceptance.** Invoking the script by path from a directory outside the
repository, against a corpus containing a `workflow-transition` or
`normalization` static case, exits 0 and reports the case as passed — no
`ModuleNotFoundError`, no traceback.

**Commit.** `fix(forge): load shared modules by path in the static eval runner`

---

### Task 2 — Close the post-hoc mutation gate hole

Closes **R3** and **R4**. Traces to AC-021 / FR-073 in
`docs/specs/forge-portable-sdlc.md:1079-1086`.

**Objective.** An unlabelled, unknown-stage, or malformed mutation recorded
before an approval blocks the gate with `GATE_VIOLATION`.

**Dependencies.** None on Task 1, but keep the given order so Task 3 has both
behaviours available.

**Files.**
- Modify `plugin/shared/forge/scripts/workflow_state.py` —
  `_has_post_hoc_mutation` (`:253-266`) only.
- Modify `plugin/shared/forge/references/workflow-contract.md` — the "Gates,
  approval, and freshness" section (around `:40-50`).
- Modify `plugin/shared/forge/tests/test_workflow_state.py` — add regression
  tests near the existing post-hoc tests (`:220`, `:237`, `:251`).

**Implementation.**
1. Add a module constant `KNOWN_MUTATION_STAGES = {"discovery", "clarification",
   "specification", "planning", "implementation"}`. If the module already has a
   canonical stage set used by `_canonical_stage`, reuse it rather than adding a
   second source of truth.
2. In `_has_post_hoc_mutation`, change the malformed guard to fail closed:
   a non-list `mutations` returns `True`.
3. Change the per-entry guard: a non-dict entry returns `True`.
4. Replace the skip condition `mutation.get("stage") != target` with the D3 rule
   — evaluate the mutation when its `stage` equals `target`, **or** when its
   `stage` is not a member of `KNOWN_MUTATION_STAGES`; skip only a mutation
   labelled with a different *recognised* stage.
5. Leave `_precedes` unchanged — it already fails closed on missing or
   type-mismatched timestamps.
6. Document the record shape in `workflow-contract.md`: `state.mutations` is a
   list of objects with a `stage` (one of the recognised stages) and an `at`
   ordering value comparable with `approval.approved_at`; an unlabelled,
   unrecognised, or malformed record is treated as in scope for every gate and
   therefore blocks. State that adapters that do not track mutations may omit the
   key entirely.

**Must not change.** `can_enter_stage`'s signature or return shape;
`_valid_approval` (the intent allowlist is deferred, §12); `_precedes`;
`normalize_markdown`; the `requires_spec_approval` behaviour.

**Narrow verification.**
```bash
python -m unittest plugin.shared.forge.tests.test_workflow_state -v
```
Expected: OK. Then this probe must print `GATE_VIOLATION` on all three lines:
```bash
python -c "import sys;sys.path.insert(0,'plugin/shared/forge/scripts');from workflow_state import can_enter_stage as c;import copy;b={'requires_spec_approval':False,'current_actor':'agent','artifacts':{'plan':{'hash':'h','revision':2,'author':'agent','approval':{'actor':'human','artifact_hash':'h','revision':2,'approved_at':'2026-01-02'}}}};[print(c(dict(b,mutations=m),'implementation')['code']) for m in ([{'at':'2026-01-01'}],[{'stage':'bogus','at':'2026-01-01'}],'oops')]"
```

**Acceptance.** The three probe cases return `GATE_VIOLATION` with
`read_only: True`; a mutation labelled with a different recognised stage (e.g.
`specification`) still does **not** block implementation; existing tests unchanged
and green.

**Commit.** `fix(forge): fail closed on unlabelled and malformed mutation records`

---

### Task 3 — Give the shared static corpus real coverage

Closes **R1**.

**Objective.** The documented command reports `passed > 0`, exercises the
`brain-adapter` fixture, and regression-guards Task 2.

**Dependencies.** Tasks 1 and 2 complete and committed. Case ST-004 asserts Task
2's behaviour and will fail without it.

**Files.**
- Create `plugin/shared/forge/evals/static.json`.
- Modify `packaging/test_validate_plugin.py` —
  `test_shared_static_runner_classifies_current_v1_corpus_without_false_passes`
  (`:251-259`).
- Modify `README.md:73-79` if the surrounding prose implies coverage that the
  numbers now contradict.

**Implementation.**
1. Write `static.json` as a JSON list of v1-valid cases. Each case carries
   `version: 1`, `kind: "execution"`, a `category`, a `prompt`, a non-empty
   `expected` block, a `deterministic` grader
   (`{"type":"deterministic","check":{"kind":"validator","validator":"<kind>"}}`
   per D2), and a `static` wrapper. Canonical shape to copy: the module docstring
   at `run_static_evals.py:9-13` plus `static_corpus_case` in
   `plugin/shared/forge/tests/test_run_static_evals.py:31-46`.
2. Cases:
   - `FORGE-ST-001` — `adapter-parity`, `fixture: "fixtures/brain-adapter"`,
     `result.status: "passed"`. Category `positive`. This is the case that wires
     the orphaned fixture.
   - `FORGE-ST-002` — `workflow-transition`, implementation target with no
     approvals, `expected_allowed: false`, `expected_code: "GATE_REQUIRED"`,
     `require_read_only: true`. Category `boundary`.
   - `FORGE-ST-003` — `workflow-transition`, implementation target with valid
     Spec and Plan approvals, `expected_allowed: true`. Category `positive`.
   - `FORGE-ST-004` — `workflow-transition`, implementation target with a valid
     plan approval and an **unlabelled** mutation preceding it,
     `expected_allowed: false`, `expected_code: "GATE_VIOLATION"`,
     `require_read_only: true`. Category `regression`. This is the R3 guard.
   - `FORGE-ST-005` — `normalization`, a `source`/`normalized` pair that
     distinguishes formatting noise from semantic whitespace per FR-031/FR-032.
     Category `boundary`.
3. Do not add a `command`, `program`, `import`, or callable field to any case —
   `_contains_command` rejects them and the trust boundary forbids them.
4. Update the packaging test: replace `assertEqual(0, summary["passed"])` with
   `assertGreaterEqual(summary["passed"], 5)`, keep `assertEqual(0,
   summary["failed"])`, keep `assertGreater(summary["skipped"], 0)` and
   `assertEqual([], results["unmeasured"])`. Add an assertion that all 13
   `FORGE-EX-*` ids are still in the `skipped` bucket — the point of D1 is that
   static coverage must not convert a model case into a pass.

**Must not change.** `execution.json` — none of its 13 cases gains a `static`
wrapper. The runner code. The fixture files.

**Narrow verification.**
```bash
python plugin/skills/skill-engineer/scripts/validate_evals.py plugin/shared/forge/evals
python plugin/shared/forge/evals/run_static_evals.py --json
python -m unittest packaging.test_validate_plugin -v
```
Expected: validator 0 errors; runner `passed: 5`, `failed: 0`, `skipped: 13`,
`unmeasured: 0`, exit 0; packaging tests OK.

**Acceptance.** `grep -c '"static"' plugin/shared/forge/evals/static.json` > 0;
the runner passes five cases including the `brain-adapter` parity case; all
thirteen `FORGE-EX-*` remain `skipped` with the `llm-judge` reason; reverting
Task 2 makes `FORGE-ST-004` fail.

**Commit.** `test(forge): add deterministic static coverage to the shared corpus`

---

### Task 4 — Pin the shipped Skill payload in packaging validation

Closes **R5**, and **F4** falls out of it.

**Objective.** Removing any of the eight shipped Skills fails
`validate_plugin.py`.

**Dependencies.** None. Do this last.

**Files.**
- Modify `packaging/validate_plugin.py:27` — `EXPECTED_SKILL_IDS`.
- Modify `packaging/test_validate_plugin.py:22` — the duplicate constant, and
  `test_discovery_rejects_missing_required_baseline_skill` at `:104-105`.

**Implementation.**
1. In `validate_plugin.py`, widen `EXPECTED_SKILL_IDS` to all eight IDs:
   the existing three plus `forge-clarify`, `forge-discover`, `forge-spec`,
   `forge-plan`, `forge-implement`. Keep the subset check at `:118` as-is — it is
   what permits third-party Skills and is a deliberate ruling, not a defect.
2. In `test_validate_plugin.py`, define `EXPECTED_SKILL_IDS` as the union of the
   three baseline IDs and the existing `FORGE_SKILL_IDS` constant (`:29-34`),
   moving the definition below `FORGE_SKILL_IDS` so it can reference it.
3. Fix the now-stale literal in
   `test_discovery_rejects_missing_required_baseline_skill:104-105`: replace the
   hardcoded `{"skill-engineer", "skill-prospector"}` with
   `EXPECTED_SKILL_IDS - {"merge-sentinel"}`. **This is the one place the
   widening silently breaks an assertion — check it explicitly.**
4. The synthetic-tree helpers at `:94`, `:114`, `:138`, `:189` write a minimal
   `SKILL.md` per ID and scale to eight without change. Do not restructure them.
5. Add a test asserting `validate_plugin.EXPECTED_SKILL_IDS` equals the test
   module's constant, so the two copies cannot drift again.

**Must not change.** The subset comparison at `:118-122`; `CANONICAL_EVAL_VALIDATORS`
(the Forge Skills have no canonical validator entry and need none); any Skill
package; any manifest.

**Narrow verification.**
```bash
python packaging/validate_plugin.py
python -m unittest packaging.test_validate_plugin -v
```
Then the negative proof:
```bash
git stash -u -- plugin/skills/forge-plan && python packaging/validate_plugin.py; git stash pop
```
Expected: clean run PASS / tests OK; the stashed run **FAILS** naming
`forge-plan`.

**Acceptance.** `validate_plugin.py` fails when any one of the eight Skill
directories is absent, and
`test_canonical_skill_names_are_unique_and_inspect_cleanly` now inspects all
eight.

**Commit.** `fix(packaging): pin all eight shipped Skill IDs in validation`

---

## 8. Full deterministic verification

Run once, after all four tasks, from the repository root.

### PASS REQUIRED

```bash
python packaging/validate_plugin.py
python -m unittest discover -s packaging -p "test_*.py"
python -m unittest plugin.shared.forge.tests
python plugin/shared/forge/evals/run_static_evals.py --json
python plugin/skills/skill-engineer/evals/run_static_evals.py
python plugin/skills/skill-prospector/evals/run_static_evals.py
python plugin/skills/merge-sentinel/evals/validate_corpus.py plugin/skills/merge-sentinel/evals
python plugin/skills/skill-engineer/scripts/inspect_skill.py plugin/skills/forge-clarify plugin/skills/forge-discover plugin/skills/forge-spec plugin/skills/forge-plan plugin/skills/forge-implement
python plugin/skills/skill-engineer/scripts/validate_evals.py plugin/shared/forge/evals
git diff --check
git status --short
```

Expected, against the `1d5cf7e` baseline:

- `validate_plugin.py` → `RESULT: PASS`, now listing eight required IDs.
- packaging tests → OK, count ≥ 30 (one added in Task 4, assertions changed in
  Task 3).
- `plugin.shared.forge.tests` → OK, count ≥ 31 (Tasks 1 and 2 add tests).
- shared static runner → `passed: 5, failed: 0, skipped: 13, unmeasured: 0`,
  exit 0. **A `passed: 0` here means Task 3 did not land — that is a failure,
  not a pass.**
- skill-engineer 16/16, skill-prospector 18/18 deterministic.
- inspector → exit 0, `errors: []` for each Forge Skill.
- `git diff --check` clean; `git status --short` shows **only** the untracked
  `.claude/` and `inspect_out.json`.

Also re-run the Task 3 and Task 4 negative proofs once at this stage.

### ALLOWED SKIP

- `merge-sentinel/evals/validate_corpus.py` against Forge eval directories — it
  is corpus-specific to merge-sentinel and reports spurious "canonical file is
  missing" errors there. Forge eval dirs are validated by
  `skill-engineer/scripts/validate_evals.py`. Record the reason.

### UNAVAILABLE / UNMEASURED — never report as PASS

- Live host trials; live model trials.
- External Brain runtime/adapter parity (that repository is not available here).
- The 13 `llm-judge` cases in `plugin/shared/forge/evals/execution.json` — these
  stay `skipped` by design.
- Host-runner-gated skill-engineer / skill-prospector cases.
- Trigger precision/recall and cross-stage routing collision.

---

## 9. Final review handoff

Produce, and append to
`.superpowers/sdd/2026-09-01-forge-portable-sdlc-plan-v2/progress.md`:

- this plan's path and the review record it closes (Section 10, findings R1–R5);
- baseline `1d5cf7e` and the final revision;
- the four task commits;
- changed artifacts (expected: `run_static_evals.py`, `workflow_state.py`,
  `workflow-contract.md`, `static.json` (new), both `plugin/shared/forge/tests/`
  files, `validate_plugin.py`, `test_validate_plugin.py`, possibly `README.md`);
- the §8 command results verbatim;
- deviations, blockers, pre-existing failures;
- the UNMEASURED list, unchanged.

No chain-of-thought, no replay of the implementation.

---

## 10. Final semantic review

One review of the integrated result, after §8 is green. Judge only:

- Findings R1–R5 are actually closed, not merely made green — in particular that
  Task 3 did not launder any model-behaviour case into a deterministic pass (D1).
- The D3 mutation-scoping rule did not over-block: a mutation labelled with a
  different recognised stage must still not block a later gate.
- No stage Skill prose, spec, or upstream plan changed.
- No scope expansion beyond the four tasks; the §12 deferrals are still deferred.
- `workflow-contract.md`'s new mutation-record paragraph matches what the code
  actually enforces.

If findings exist, produce a bounded remediation set for those findings only.
Do not restart this cycle.

---

## 11. Acceptance criteria

1. `python plugin/shared/forge/evals/run_static_evals.py --json` reports
   `passed >= 5`, `failed: 0`, `unmeasured: 0`, and all 13 `FORGE-EX-*` still
   `skipped`.
2. The `brain-adapter` fixture is referenced by exactly one passing case.
3. Invoking `run_static_evals.py` by path from outside the repository, against a
   corpus with a `workflow-transition` case, succeeds.
4. `can_enter_stage` returns `GATE_VIOLATION` + `read_only: True` for an
   unlabelled mutation, an unknown-stage mutation, and a malformed `mutations`
   value, each preceding the approval.
5. A mutation labelled with a different recognised stage does not block.
6. `workflow-contract.md` documents the `mutations` record shape.
7. `validate_plugin.py` fails when any of the eight Skill directories is removed.
8. §8 PASS REQUIRED is green; the ALLOWED SKIP and UNMEASURED lists are recorded
   with reasons and nothing is upgraded.
9. Four commits, one per task. Nothing pushed, squashed, PR'd, or merged.
10. `git status --short` shows only `.claude/` and `inspect_out.json`.

---

## 12. Assumptions, deferrals, unmeasured

### Assumptions

- The review record in progress.md § Section 10 is the authoritative statement of
  what must be fixed; no upstream requirement changed.
- `plugin/shared/forge/` may be vendored, which is why D5 avoids `REPO_ROOT`.

### Deferred — recorded, deliberately out of scope

Non-blocking findings from the same review. Each is a separate decision, not a
silent omission. Do not fix them in this plan.

- `_valid_approval:222-223` denies `full_workflow`/`implement` intents rather
  than requiring an artifact-approval intent. Damage is bounded by hash+revision
  binding. Inverting to an allowlist is a contract change affecting adapters and
  needs its own decision.
- `workflow_state.py` has no `__main__`/CLI and is not linked from
  `forge-implement/SKILL.md:9`; `forge-implement` states no fallback for an
  unexecutable gate. Adding a CLI is a new public interface.
- Skill `description` frontmatter gates on workflow state the router cannot
  observe, and none carries a negative boundary clause. Rewriting descriptions
  changes routing behaviour that cannot be measured here.
- Trigger eval cases record no catalog snapshot; cross-stage negatives are
  unbalanced (`forge-implement` has one).

### Unmeasured by this plan

Everything in §8's UNMEASURED list. This plan does not change what is
measurable — it changes only what is *asserted* among the things that already
were.
