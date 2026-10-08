# Forge Portable SDLC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add five portable Forge SDLC skills, then refactor the five Brain SDLC skills into thin adapters that reuse Forge without duplicated workflow logic.

**Architecture:** Forge is a co-installed, explicitly invoked suite with shared artifact/state contracts and stage-specific packages. Portable cores depend only on relative resources and generic capabilities; Brain adapters supply Jira, OKF, Brain templates, approval/delivery rules, and `brain-sdlc` integration. Deterministic state and corpus checks are optional stdlib-Python helpers with a disclosed manual degradation path.

**Tech Stack:** Agent Skills Markdown, JSON eval corpora, Python 3.8+ stdlib validators/tests, existing plugin packaging scripts.

**Spec:** `docs/superpowers/specs/2026-09-01-forge-portable-sdlc-design.md`

## Global Constraints

- Do not modify `D:/AI/skills/mr-review/**` or `D:/AI/skills/ba-1/**`; they are reference evidence only.
- Canonical portable authored paths are `plugin/skills/<skill>/`; do not create a repo-root mirror.
- All Forge and Brain skills are user-invoked, not model-invoked.
- Forge cores must remain harness-agnostic: no named model, subagent, MCP server, hook, host invocation syntax, absolute path, or host-only frontmatter.
- An invoked Brain adapter may automatically load its matching Forge core; stage chaining follows already-expressed user intent.
- Jira writes, Git commits, push, PR creation, and `.gitignore` edits require the authority defined in the spec.
- `mr-review` behavior and package remain unchanged.
- Use JSON, not YAML, for canonical eval corpora so stock Python 3.8+ can validate them.
- Report standards-compatible, host-tested, model-tested, known-deviation, and unmeasured coverage separately.
- Preserve unrelated user work. At execution start, inspect status and never reapply the preserved `stash@{0}` onto `main` as part of this feature.

## File map

### Shared portable contract and deterministic helper

- Create `plugin/skills/forge-discover/references/artifact-contract.md`: canonical artifact ownership, stage inputs/outputs, fallback directory, approval and staleness rules.
- Create `plugin/skills/forge-discover/references/knowledge-provider.md`: optional provider interface and leaf-routing contract.
- Create `plugin/skills/forge-discover/references/issue-source-contract.md`: complete-but-filtered issue acquisition and provenance rules.
- Create `plugin/skills/forge-discover/scripts/forge_state.py`: normalization, SHA-256, workflow-state validation/update, stable slug, decision identity, and knowledge-manifest helpers.
- Create `plugin/skills/forge-discover/scripts/test_forge_state.py`: helper unit tests.
- Create `plugin/skills/forge-discover/evals/fixtures/`: shared work-item and source fixtures used by Forge execution cases.

### Stage packages

- Create `plugin/skills/forge-clarify/{SKILL.md,references/decision-frontier.md,evals/execution.json}`.
- Create `plugin/skills/forge-discover/{SKILL.md,references/*.md,scripts/*.py,evals/execution.json}`.
- Create `plugin/skills/forge-spec/{SKILL.md,references/spec-contract.md,evals/execution.json}`.
- Create `plugin/skills/forge-plan/{SKILL.md,references/plan-contract.md,references/design-and-adr.md,evals/execution.json}`.
- Create `plugin/skills/forge-implement/{SKILL.md,references/execution-contract.md,references/quality-gates.md,evals/execution.json}`.

Every downstream Forge `SKILL.md` links explicitly to the canonical shared contracts under sibling `../forge-discover/`. The five skills are a co-installed suite; a missing sibling dependency produces a clear dependency error rather than copied fallback instructions.

### Plugin/catalog/package surfaces

- Modify `packaging/validate_plugin.py`: expand `EXPECTED_SKILL_IDS`; validate Forge state helper/tests and JSON corpora.
- Modify `packaging/test_validate_plugin.py`: expand roster/manifest assertions and add Forge inspection/eval/helper coverage.
- Modify `README.md`: list Forge skills, explicit invocation boundary, and validation commands.
- Modify `SKILL_ENGINEERING_SPEC.md`: update shipped layout/catalog only where it enumerates packaged skills.
- Modify `.claude-plugin/marketplace.json`: update plugin description without claiming implicit routing.

`plugin/plugin.json` and `.claude-plugin/plugin.json` are inspected during Task 1 and modified only if their current descriptions enumerate capabilities; do not change version numbers in this feature.

### Brain adapters outside the repo

- Modify `D:/AI/skills/brain-wave/SKILL.md`.
- Modify `D:/AI/skills/brain-discover/SKILL.md` and keep its four existing reference prompts only if they remain Brain-specific.
- Modify `D:/AI/skills/brain-spec/SKILL.md`; retain Jira reconciliation references as adapter knowledge.
- Modify `D:/AI/skills/brain-plan/SKILL.md`; retain Brain scenarios/evals as adapter integration coverage.
- Modify `D:/AI/skills/brain-implement/SKILL.md`; retain Brain runtime prompts/schemas/adapters as project integration.
- Install generated/co-installed copies of all five `plugin/skills/forge-*` packages into `D:/AI/skills/forge-*` from the verified canonical repo source. These are installation artifacts, not independently authored copies.

## Workhorse execution contract

- Execute tasks in dependency order. A task implementer reads the spec, Global Constraints, its task, and cited files only.
- Use test-first steps for deterministic helpers, validators, and corpus rules.
- Do not redesign approved boundaries or research product requirements during implementation.
- Do not modify Brain files until the portable package and static validation pass.
- Keep semantic review out of the per-step loop; run targeted deterministic checks, then the final integrated review in Task 10.
- Commit only when the user-selected execution mode authorizes it. Suggested messages below do not grant commit authority.
- Any required file outside a task's write scope is a deviation: report it with evidence before editing.

---

### Task 1: Freeze baseline, package roster, and red tests

**Files:**
- Modify: `packaging/test_validate_plugin.py`
- Inspect only: `packaging/validate_plugin.py`, `packaging/build_plugin.py`, `plugin/plugin.json`, `.claude-plugin/marketplace.json`, `README.md`, `SKILL_ENGINEERING_SPEC.md`

**Interfaces:**
- Consumes: current clean `main` and `EXPECTED_SKILL_IDS` roster.
- Produces: failing package tests that require exactly `forge-clarify`, `forge-discover`, `forge-spec`, `forge-plan`, and `forge-implement` in addition to the existing three skills.

- [ ] **Step 1: Verify execution baseline**

Run:

```powershell
git status --short --branch
git rev-parse HEAD
git stash list
```

Expected: `main` is clean and tracks `origin/main`; preserved remediation remains a stash and is not applied.

- [ ] **Step 2: Add roster expectations**

Change `EXPECTED_SKILL_IDS` in `packaging/test_validate_plugin.py` to:

```python
EXPECTED_SKILL_IDS = {
    "forge-clarify",
    "forge-discover",
    "forge-implement",
    "forge-plan",
    "forge-spec",
    "merge-sentinel",
    "skill-engineer",
    "skill-prospector",
}
```

Add assertions that every Forge package has `SKILL.md` and `evals/execution.json`, and that only `forge-discover` owns `scripts/forge_state.py`.

- [ ] **Step 3: Run the targeted roster tests and prove red**

Run:

```powershell
& 'C:\Users\abhin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest packaging.test_validate_plugin.CanonicalPluginLayoutTests -v
```

Expected: FAIL because the five Forge directories do not exist. If it fails for an unrelated baseline reason, record that exact reason before continuing.

- [ ] **Step 4: Record manifest decisions**

Inspect `plugin/plugin.json` and `.claude-plugin/marketplace.json`. Record in the implementation handoff whether either schema requires an explicit skills roster. Do not invent entries when discovery is dynamic.

**Suggested commit:** `test(packaging): require Forge skill suite`

### Task 2: Build the shared state/provenance helper

**Files:**
- Create: `plugin/skills/forge-discover/scripts/forge_state.py`
- Create: `plugin/skills/forge-discover/scripts/test_forge_state.py`

**Interfaces:**
- Consumes: an artifact path or workflow JSON object; no third-party dependency.
- Produces CLI subcommands:
  - `normalize <artifact>`: normalized UTF-8 text to stdout.
  - `hash <artifact>`: lowercase 64-character SHA-256.
  - `slug <stable-id-or-text>`: safe deterministic folder segment.
  - `decision-id <question>`: stable semantic-normalization fingerprint input hash; agents still judge semantic equivalence.
  - `validate <workflow.json>`: structured JSON report and exit 0/1.
  - `approve <workflow.json> <stage> <artifact> --actor <text>`: atomic state update.
  - `knowledge-stale <workflow.json>`: JSON list of missing/changed selected knowledge files.

- [ ] **Step 1: Write failing normalization tests**

Tests must prove CRLF/LF, trailing spaces, and repeated blank lines hash equally; indentation and fenced-code whitespace hash differently.

```python
def test_normalized_hash_ignores_nonsemantic_markdown_whitespace(self):
    self.assertEqual(hash_text("A  \r\n\r\n\r\nB\r\n"), hash_text("A\n\nB\n"))

def test_normalized_hash_preserves_indentation_and_fenced_code(self):
    self.assertNotEqual(hash_text("  item\n"), hash_text("item\n"))
    self.assertNotEqual(hash_text("```py\nx = 1\n```\n"), hash_text("```py\nx=1\n```\n"))
```

- [ ] **Step 2: Write failing state tests**

Cover missing keys, unknown stages, stale approval after meaningful edit, preserved approval after allowed whitespace changes, invalid hashes, atomic replace, stable slugs, collision suffix input, knowledge hash drift, and no mutation on validation failure.

- [ ] **Step 3: Run tests and prove red**

Run:

```powershell
& 'C:\Users\abhin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest plugin.skills.forge-discover.scripts.test_forge_state -v
```

Expected: import/path failure until implementation exists. If hyphenated package paths prevent module import, run the test file directly; keep production imports file-relative and stdlib-only.

- [ ] **Step 4: Implement normalization and pure functions**

Use `pathlib`, `hashlib`, `json`, `re`, `tempfile`, and `os.replace`. Never evaluate workflow content or execute commands from it. Normalize only outside fenced blocks; preserve leading whitespace everywhere.

- [ ] **Step 5: Implement structured CLI and atomic mutation**

All success output is JSON except `normalize`/`hash`/`slug`/`decision-id`. Exit 2 for invalid invocation/input, 1 for a valid check that fails, 0 for success. `--help` documents inputs, outputs, side effects, and exit codes.

- [ ] **Step 6: Run helper tests**

Run the direct test file and `forge_state.py --help`.

Expected: all tests PASS; help exits 0; no file outside the supplied workflow path is written.

**Suggested commit:** `feat(forge): add deterministic workflow state helper`

### Task 3: Create shared artifact, issue-source, and knowledge contracts

**Files:**
- Create: `plugin/skills/forge-discover/references/artifact-contract.md`
- Create: `plugin/skills/forge-discover/references/issue-source-contract.md`
- Create: `plugin/skills/forge-discover/references/knowledge-provider.md`
- Create: `plugin/skills/forge-discover/evals/fixtures/issue-complete/issue.json`
- Create: `plugin/skills/forge-discover/evals/fixtures/issue-complete/expected.json`
- Create: `plugin/skills/forge-discover/evals/fixtures/ba-answered/context.md`
- Create: `plugin/skills/forge-discover/evals/fixtures/ba-answered/decisions.md`
- Create: `plugin/skills/forge-discover/evals/fixtures/ba-answered/issue.json`

**Interfaces:**
- Consumes: generic issue-source/knowledge capabilities.
- Produces: canonical contracts referenced by all five Forge skills.

- [ ] **Step 1: Write `artifact-contract.md`**

Define exact owners, required/optional sections, `.forge/work-items/<id-or-slug>/` fallback, collision handling, workflow JSON keys, natural approval, normalized hashes, staleness, intent-based chaining, and rerun behavior. Include this minimum state shape:

```json
{
  "version": 1,
  "work_item": {"id": "", "slug": "", "root": ""},
  "stages": {},
  "approvals": {},
  "sources": [],
  "knowledge": [],
  "commit_mode": null
}
```

- [ ] **Step 2: Write `issue-source-contract.md`**

Define two-pass acquisition: field metadata/non-empty presence, then materially populated fields. Require pagination for comments and linked collections, attachment accessibility records, links/subtasks/parent/dependencies/history, provenance and freshness. Explicitly forbid raw `*all` context dumping and issue-tracker writes.

- [ ] **Step 3: Write `knowledge-provider.md`**

Define optional `validate`, `route`, `read`, and `freshness` capabilities; small-index-first routing; leaf selection; path/hash/conclusion manifest; `UNMEASURED` degradation; and the user choice offered when provider validation fails.

- [ ] **Step 4: Create realistic fixtures**

`issue-complete` must contain description, acceptance criteria, nonempty custom field, two paginated comments, attachment metadata, linked issue, subtask, parent, and changelog conflict. `ba-answered` must contain a BA question and PO answer whose wording differs from the candidate discovery question.

- [ ] **Step 5: Inspect references**

Run `inspect_skill.py` on `plugin/skills/forge-discover` after Task 4 creates its `SKILL.md`; until then, verify every relative target manually and record this check as pending rather than passed.

**Suggested commit:** `docs(forge): define shared workflow contracts`

### Task 4: Create `forge-clarify` and `forge-discover`

**Files:**
- Create: `plugin/skills/forge-clarify/SKILL.md`
- Create: `plugin/skills/forge-clarify/references/decision-frontier.md`
- Create: `plugin/skills/forge-clarify/evals/execution.json`
- Create: `plugin/skills/forge-discover/SKILL.md`
- Create: `plugin/skills/forge-discover/evals/execution.json`

**Interfaces:**
- `forge-clarify` consumes verified facts plus `decisions.md`; produces settled/open decision updates and confirmation summary.
- `forge-discover` consumes user sources and optional providers; produces `context.md`, `decisions.md`, source/knowledge manifests, and automatically invokes clarification only for unresolved/conflicting human choices.

- [ ] **Step 1: Write failing eval cases first**

Use portable JSON schema. Required cases:

- Explicit clarification request with two independent open decisions asks one round.
- Candidate question already answered semantically in BA/Jira/context is not asked.
- Conflicting current requirement and changelog asks for confirmation.
- Evidence-answerable question causes research, not interview.
- Excluded/unassigned and parallel paths appear in impact coverage.
- UI task missing a visual reference warns; backend-only task does not.
- Complete issue fixture consumes every materially populated source category.
- Inaccessible field/attachment is recorded, not silently omitted.
- No decision frontier yields a summary without forced confirmation question.

- [ ] **Step 2: Validate the corpus and prove red**

Run `validate_evals.py` against both `execution.json` files.

Expected: schema passes; execution remains unmeasured until the skills exist and runtime cases run.

- [ ] **Step 3: Author `forge-clarify/SKILL.md`**

Frontmatter name is `forge-clarify`; description states explicit/user invocation only and distinguishes decisions from evidence research. Body stays stage-focused, loads `decision-frontier.md` only while deriving/asking the frontier, groups independent questions, and updates the canonical decision ledger.

- [ ] **Step 4: Author the automatic suppression contract**

`decision-frontier.md` must require inspecting available issue fields/comments, BA output, artifacts, and current conversation before asking. Semantic equivalence is agent judgement; the helper supplies persistence identity only. Reopen settled decisions solely for cited contradiction, staleness, or scope change.

- [ ] **Step 5: Author `forge-discover/SKILL.md`**

Make source acquisition, current-state verification, impact matrix, conditional reference readiness, provider routing, clarification boundary, artifacts, validation, and observable done conditions explicit. Link shared resources with correct relative paths. Do not name Jira, Brain, OKF, MCP, or a host in the portable body.

- [ ] **Step 6: Inspect both packages**

Run the canonical inspector on each directory.

Expected: zero broken references/hardcoded paths/platform extensions; parser degradation is disclosed if PyYAML is absent.

**Suggested commit:** `feat(forge): add clarification and discovery skills`

### Task 5: Create `forge-spec`

**Files:**
- Create: `plugin/skills/forge-spec/SKILL.md`
- Create: `plugin/skills/forge-spec/references/spec-contract.md`
- Create: `plugin/skills/forge-spec/evals/execution.json`

**Interfaces:**
- Consumes: approved/current `context.md`, `decisions.md`, sources, knowledge manifest.
- Produces: `spec.md` with stable requirement IDs and natural-language approval state.

- [ ] **Step 1: Convert checklist requirements into evals**

Add positive, boundary, regression, and failure cases covering actors, goal/scope/non-goals, functional requirements, changed/unchanged paths, invariants, state semantics, edge/failure behavior, NFR/security/dependencies, acceptance scenarios, traceability, and no unresolved questions/design leakage.

- [ ] **Step 2: Add the functional-coverage regression**

Fixture must require excluded employees and unassigned payroll employees. Expected spec maps both to changed behavior, unchanged behavior, or explicit exclusion; omission fails.

- [ ] **Step 3: Author `spec-contract.md`**

Translate `C:/Users/abhin/Downloads/Skill Engineer Checklist/specification-skill-checklist.md` into concise conditional contract. Do not copy explanatory prose or always load irrelevant sections. Add the planability gate: planning can determine what must be achieved without inventing requirements.

- [ ] **Step 4: Author `SKILL.md`**

Define route/current-approval checks, reconcile inputs, write behavioral contract, validate both coverage directions, present exact revision, recognize unambiguous natural approval, and stop/chain according to user intent. Technical design belongs to `forge-plan`.

- [ ] **Step 5: Validate and inspect**

Run eval-schema validation and `inspect_skill.py`.

Expected: zero schema errors and broken references.

**Suggested commit:** `feat(forge): add behavioral specification skill`

### Task 6: Create `forge-plan`

**Files:**
- Create: `plugin/skills/forge-plan/SKILL.md`
- Create: `plugin/skills/forge-plan/references/plan-contract.md`
- Create: `plugin/skills/forge-plan/references/design-and-adr.md`
- Create: `plugin/skills/forge-plan/evals/execution.json`

**Interfaces:**
- Consumes: approved `spec.md`, discovery artifacts, current source baselines, applicable knowledge.
- Produces: `plan.md`, conditional `design.md`, conditional ADR, approval-bound revision.

- [ ] **Step 1: Add blind-workhorse eval fixtures**

Include one multi-file UI/backend fixture and one small change. Grade exact files/symbols, canonical examples, contracts/signatures/schema, ordered steps, edge cases, scope boundaries, commands/expected results, developer acceptance, failure behavior, and requirement traceability. Fail prompts that leave research, architecture choice, or user questions to the implementer.

- [ ] **Step 2: Add code-detail boundary cases**

One fixture requires a signature/code sketch to freeze an interface; another contains obvious boilerplate where copying a full implementation is excessive. The expected outcome distinguishes necessary decision-freezing code from context inflation.

- [ ] **Step 3: Author `plan-contract.md`**

Translate the implementation-plan checklist into closed packet fields and the exact readiness test from the spec. Define dependency ordering, per-task write scope, `Must not change`, narrow checks, expected output, acceptance, and optional checkpoint message.

- [ ] **Step 4: Author `design-and-adr.md`**

Encode approved `design.md` thresholds and three-part ADR test. Define fallback `docs/adr/` and require exact design-section/ADR links instead of duplicated content.

- [ ] **Step 5: Author `SKILL.md`**

Require approved spec hash, code/rule grounding, technical research completion, exact change surface, full traceability, validation, natural approval, and intent-based chain to implementation. Planning does not interview users; product ambiguity routes back through discovery/clarification.

- [ ] **Step 6: Validate and inspect**

Expected: JSON corpus valid; inspector clean; blind-workhorse fixture has no placeholder language.

**Suggested commit:** `feat(forge): add blind-workhorse planning skill`

### Task 7: Create `forge-implement`

**Files:**
- Create: `plugin/skills/forge-implement/SKILL.md`
- Create: `plugin/skills/forge-implement/references/execution-contract.md`
- Create: `plugin/skills/forge-implement/references/quality-gates.md`
- Create: `plugin/skills/forge-implement/evals/execution.json`

**Interfaces:**
- Consumes: approved plan/spec, optional design/ADR, task packets, repository baseline, applicable knowledge.
- Produces: product edits, `tasks.md`, `evidence.md`, optional authorized commits, integrated verification and semantic-review handoff.

- [ ] **Step 1: Write commit-mode and idempotency cases**

Cover `review-first`, `per-task`, and `end-only`; no automatic squash/push/PR; unrelated dirty files excluded; rerun does not duplicate commit/artifact/task state; natural start authorization is recorded once.

- [ ] **Step 2: Write quality-prevention cases**

Use fixtures derived from supplied feedback: inline CSS instead of reusable style, duplicated component/logic, repeated message literal instead of constant, realistic-volume performance issue, missed UI reference, and maintainability regression. Expected behavior catches applicable issues before task completion without loading unrelated knowledge.

- [ ] **Step 3: Write orchestration/failure cases**

Cover narrow per-task validation, one final semantic review, independent workhorse delegation only when beneficial, unavailable delegation fallback, plan contradiction stopping dependent work only, unplanned scope authorization, transient bounded retry, deterministic no-retry, and `UNMEASURED` checks.

- [ ] **Step 4: Author `execution-contract.md`**

Define task lifecycle, commit-mode prompt, scope/dirty-tree protection, verification evidence, retry/recovery, delegation capability, integration, and compact handoff. Never name a harness model or require subagents.

- [ ] **Step 5: Author `quality-gates.md`**

Define applicability routing for design parity, reuse/components/styles, constants, duplication/parallel paths, performance, maintainability, security/permissions, tests, and diff hygiene. Per-task gates are narrow; integrated deterministic verification precedes one final semantic review.

- [ ] **Step 6: Author `SKILL.md`, validate, and inspect**

Expected: package clean; eval schema valid; completion cannot be satisfied by narrated compliance alone.

**Suggested commit:** `feat(forge): add verified implementation runner`

### Task 8: Integrate Forge into plugin packaging and documentation

**Files:**
- Modify: `packaging/validate_plugin.py`
- Modify: `packaging/test_validate_plugin.py`
- Modify: `README.md`
- Modify: `SKILL_ENGINEERING_SPEC.md`
- Modify: `.claude-plugin/marketplace.json`
- Modify if Task 1 proves needed: `plugin/plugin.json`, `.claude-plugin/plugin.json`

**Interfaces:**
- Consumes: five statically valid Forge packages.
- Produces: discoverable packaged suite with deterministic validation.

- [ ] **Step 1: Update production roster**

Set `packaging/validate_plugin.py::EXPECTED_SKILL_IDS` to the exact eight-skill set from Task 1. Extend canonical validation to require Forge JSON corpora and run `forge_state.py --help` plus its unit tests. Do not add a fallback that converts failures into passes.

- [ ] **Step 2: Complete package tests**

Add test cases for missing Forge package, invalid Forge eval, broken sibling shared-contract link, helper test failure, and build output containing all five Forge packages/resources.

- [ ] **Step 3: Update docs/catalog text**

README lists each Forge capability and explicitly says user-invoked. Marketplace description names the portable SDLC suite without claiming implicit discovery. Update only actual enumerations in `SKILL_ENGINEERING_SPEC.md`; do not paste the feature design into that specification.

- [ ] **Step 4: Run targeted and full packaging validation**

Run:

```powershell
& 'C:\Users\abhin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest packaging.test_validate_plugin -v
& 'C:\Users\abhin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' packaging/validate_plugin.py
& 'C:\Users\abhin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' packaging/build_plugin.py --out dist/skill-engineer
```

Expected: all pass and build output contains exactly the eight expected skills. If the known root-mirror baseline defect exists, classify it separately; do not delete the mirror without authorization.

**Suggested commit:** `feat(plugin): package Forge SDLC suite`

### Task 9: Refactor Brain skills into Forge adapters

**Files:**
- Modify: `D:/AI/skills/brain-wave/SKILL.md`
- Modify: `D:/AI/skills/brain-discover/SKILL.md`
- Modify: `D:/AI/skills/brain-spec/SKILL.md`
- Modify: `D:/AI/skills/brain-plan/SKILL.md`
- Modify: `D:/AI/skills/brain-implement/SKILL.md`
- Install from canonical source: `D:/AI/skills/forge-clarify/**`, `forge-discover/**`, `forge-spec/**`, `forge-plan/**`, `forge-implement/**`
- Test/inspect only: all retained Brain references/evals and `D:/AI/skills/knowledge/**`
- Do not modify: `D:/AI/skills/ba-1/**`, `D:/AI/skills/mr-review/**`

**Interfaces:**
- Consumes: verified co-installed Forge suite and current Brain project resources.
- Produces: thin adapters containing only Brain/Jira/OKF/`brain-sdlc`/approval-delivery specializations.

- [ ] **Step 1: Obtain external-write authorization and snapshot**

Resolve exact absolute targets, verify they remain beneath `D:/AI/skills`, inventory/hash every file to be changed, and preserve a recoverable copy or Git baseline. Do not use recursive deletion/move.

- [ ] **Step 2: Install verified Forge packages**

Copy from built/canonical source with a deterministic installer or reviewed file-by-file operation. Verify source/destination inventories and SHA-256 equality. Never author changes in both locations independently.

- [ ] **Step 3: Refactor `brain-wave`**

Replace portable frontier/interview logic with explicit loading of `../forge-clarify/SKILL.md`. Keep only Brain naming, `brain-sdlc wave` recording, and Brain artifact mapping. Remove mandatory empty-frontier confirmation; Forge automatically suppresses already answered BA/Jira/context questions.

- [ ] **Step 4: Refactor `brain-discover`**

Load `../forge-discover/SKILL.md`, then configure the existing Brain ticket folder, Jira source capability, all-material-fields/comments acquisition, Brain templates, OKF provider, branch identity, and `brain-sdlc` validation. Remove duplicated generic discovery/impact/interview procedure. Missing visual references warn only when applicable. Do not write Jira.

- [ ] **Step 5: Refactor `brain-spec` and `brain-plan`**

Each loads its sibling Forge core and retains only Brain artifact templates, Jira reconciliation/read behavior, `brain-sdlc` validators/gates, branch/delivery specialization, and existing project scenario oracles. Replace nonce/command-centric user UX where it conflicts with natural unambiguous approval, while retaining deterministic ledger recording internally.

- [ ] **Step 6: Refactor `brain-implement`**

Load `../forge-implement/SKILL.md`. Retain Brain slice preparation/runtime, Brain-specific model-binding adapter as optional capability, project branches, existing prompts/result schemas, and final Brain handoff. Adopt startup commit mode and Forge per-task quality prevention. Do not call or change `mr-review`; any existing final `mr-review` step remains unchanged.

- [ ] **Step 7: Validate adapters and references**

Run `inspect_skill.py` on each Brain and Forge destination package. Classify links intentionally supplied by the wider Brain installation separately from actual broken links. Run existing Brain JSON eval validators; current schema defects must be repaired only when they concern modified adapter behavior, otherwise recorded as pre-existing.

- [ ] **Step 8: Run historical adapter scenarios**

At minimum replay BA-answer suppression, excluded/unassigned impact coverage, Jira comments/custom fields, missing UI reference warning, blind-workhorse plan, commit mode, and implementation quality feedback. Confirm `ba-1` and `mr-review` hashes are unchanged.

**Suggested commit (only if `D:/AI/skills` is version-controlled and authorized):** `refactor(brain): delegate SDLC workflow to Forge`

### Task 10: Integrated verification, differential evaluation, and final review

**Files:**
- Modify only if defects are found within approved scope: Forge packages, packaging integration, Brain adapters, and their tests/evals.
- Produce runtime results only under ignored/eval-result locations; do not commit generated reports unless repository policy requires them.

**Interfaces:**
- Consumes: Tasks 1–9 completed.
- Produces: verified handoff with measured/unmeasured matrix and no Critical/High semantic findings.

- [ ] **Step 1: Run deterministic repo suite**

Run helper tests, all Forge eval-schema validators, all Forge inspectors, existing skill-engineer static evals, packaging unit tests, production validator, and build. Record command, exit code, and concise result.

- [ ] **Step 2: Run deterministic Brain adapter suite**

Run OKF validator, Brain package inspections, applicable existing Brain evals, and source/destination Forge hash comparison. Record pre-existing failures independently.

- [ ] **Step 3: Run execution regressions**

Exercise every feedback-derived and contract-derived case. Multiple trials are required only for semantic/model variance. Classify failures as skill, model, tool, fixture, harness, environment, grader, unmeasured, or disputed.

- [ ] **Step 4: Run differential comparisons**

Compare candidate Forge-backed Brain behavior with preserved current Brain fixtures and a no-Forge baseline. Correctness first; then record context tokens, files/references loaded, tool calls, duration, retries, and questions asked. Automatic suppression passes when available context answers the candidate question semantically and no repeat is asked.

- [ ] **Step 5: Run one independent semantic review**

Review final diff/artifacts against the design and plan using `skill-engineer` rules: mechanism, decomposition, explicit invocation metadata, progressive disclosure, reference reachability, extraction balance, tools, completion, mutation/retry/idempotency, safety, portability, regression preservation, and measured utility. Also verify no `mr-review`/`ba-1` changes and no duplicated portable logic remains in Brain adapters.

- [ ] **Step 6: Remediate bounded findings and rerun affected checks**

Do not restart the entire workflow unless the architecture is invalid. Any edit invalidates the relevant inspection/review result and requires that exact check again.

- [ ] **Step 7: Produce compact handoff**

Include spec/plan paths, baseline/final revisions, changed artifacts, commit mode/commits, deterministic results, semantic-review verdict, deviations, pre-existing failures, unmeasured host/model/provider coverage, and external installation status. Do not claim native cross-host behavior that was not run.

**Suggested commit:** `test(forge): verify portable SDLC integration`

## Final acceptance criteria

- Exactly five Forge skills ship from canonical `plugin/skills/` paths and pass static/package validation.
- Forge cores are user-invoked and harness-agnostic; Brain adapters auto-load matching cores only after user invocation.
- Automatic context-aware suppression prevents repeated BA/Discovery questions without a manually maintained suppression list.
- Issue-backed discovery accounts for all materially populated accessible fields/comments and preserves provenance without raw-payload context dumping.
- `forge-spec` covers impacted existing functionality and creates a testable behavioral contract.
- `forge-plan` produces closed packets a competent workhorse can implement without research, design, or questions, including code sketches only where necessary.
- `forge-implement` prevents applicable design/reuse/inline-style/duplication/constants/performance/maintainability issues before completion and performs only one final semantic review.
- Natural approvals, whitespace normalization, conditional `design.md`/ADR, commit modes, failure recovery, idempotency, knowledge routing, and `UNMEASURED` degradation behave as specified.
- Brain skills contain project specialization rather than duplicated portable workflow logic.
- `D:/AI/skills/ba-1/**` and `D:/AI/skills/mr-review/**` remain byte-for-byte unchanged.
- All unavailable host/model/runtime trials are explicitly `UNMEASURED`.
