# Specification: Proportional planning in Forge

## Status and identity

- Revision: 1
- State: awaiting explicit approval
- Approval: none recorded
- Intent: `intent.md`, revision 2
- This file is the proposed feature authority for the proportional
  `forge-plan` change. It does not authorize implementation or delivery until
  the shared workflow contract records approval for this exact revision.
- The content hash is computed over the exact file bytes at the approval
  checkpoint. It is reported outside the file, so no pre-approval value is an
  approval hash.

## 1. Intent and boundary

Forge needs one planning Skill that scales its planning depth to the risk and
coordination of the work. Bounded work should stay short. Consequential work
should expose enough evidence, traceability, risk control, and dependency
structure for an implementor to act without rediscovery or product decisions.

In scope:

- one model-invoked `forge-plan` Skill with `compact` and `detailed` modes;
- mode recommendation, user confirmation, artifact shape, phase sizing, risk
  routing, and commit-policy boundaries;
- delegation to the canonical Forge workflow, issue-source, and
  knowledge-provider contracts;
- conditional Specification and Plan approval gates;
- trusted static and optional behavioral evaluation of the Skill and its
  proportional artifact contracts;
- packaging and Python 3.8-compatible verification for the changed evaluators.

Out of scope:

- changing or replacing the shared Forge workflow contract or its state helper;
- implementing source changes described by a generated plan;
- creating, publishing, or formatting tracker records for a downstream system;
- requiring a particular host, model, provider, runner, judge, or live service;
- using untracked local specifications, designs, scratch files, or chat
  artifacts as authority;
- claiming live model, runner, judge, portability, token, latency, or defect
  results that were not executed.

The normal terminal result is an approved, ticket-ready Plan, followed by a
stop. Any downstream use is a separate actor and authorization boundary.

## 2. Source basis

The following sources were consumed as evidence or binding constraints:

| ID | Source | Use and authority |
| --- | --- | --- |
| INT-2 | `intent.md`, revision 2 | Product intent and the seven resolved decisions. Awaiting the same explicit approval checkpoint as this Specification. |
| CON-WF | `plugin/shared/forge/references/workflow-contract.md` | Binding approval, state, artifact ownership, freshness, retry, resume, and mutation rules. Sole source for those semantics. |
| CON-ISSUE | `plugin/shared/forge/references/issue-source-contract.md` | Host-neutral issue evidence, provenance, unavailable-source, relationship, history, and freshness obligations. |
| CON-KNOWLEDGE | `plugin/shared/forge/references/knowledge-provider-contract.md` | Host-neutral selected-leaf knowledge, provenance, unavailable-knowledge, validation, and freshness obligations. |
| RES-PHASE | `docs/research/2026-09-12-forge-phase-gates-re-research.md` | Evidence for required checks before review, zero blocking findings, bounded review loops, and explicit commit policy. |
| RES-FUND | `docs/research/2026-09-12-forge-software-fundamentals.md` | Evidence for cohesive vertical outcomes, progressive loading, traceability, conditional risk controls, and reviewability sizing. |
| REVIEW-2 | GitHub PR #2 review `5187697626`, submitted at head `c34838b7d3b92baf1be9366dd43f0579768f0509` | Remediation evidence: six root findings and the required verification boundaries. It does not override product intent or CON-WF. |
| USER-2 | The authorized remediation request for PR #2 | Binding scope for the eval, fixture, regression, terminology, and delivery requirements listed here. |

The tracked research file `docs/research/2026-09-12-forge-plan-modes-research.md`
was not used for downstream-conversion provenance. Any such conversation or
source is excluded from this Specification. The untracked
`docs/specs/2026-09-12-forge-proportional-planning.md`, `docs/designs/`,
`.scratch/`, `.claude/`, `.vscode/`, and `docs/superpowers/specs/` files were
not consumed as authority or staged.

## 3. Resolved decisions

| ID | Decision | Observable consequence | Basis |
| --- | --- | --- | --- |
| DEC-001 | The modes are named `compact` and `detailed`. | Skill text, references, prompts, and current-shape evals use these names consistently. | INT-2, USER-2 |
| DEC-002 | Forge recommends a mode during grilling from verified evidence. The user must confirm or explicitly override before mode-specific guidance loads. | No silent mode switch; an explicit override is recorded and does not grant mutation authority. | INT-2, RES-FUND |
| DEC-003 | Compact is the default for verified bounded low-risk work with no unresolved material decision. Detailed is recommended for one severe factor or connected moderate factors whose combined impact, coordination, or uncertainty makes compact unsafe. No fixed signal count decides the mode. | Evidence and uncertainty explain the recommendation. A small file count cannot suppress a severe risk. | INT-2, RES-FUND, REVIEW-2 |
| DEC-004 | Detailed artifacts use a control `plan.md`, then `phases/<phase>/phase.md`, then ordered task files inside each phase directory. | There is no `tasks.md` control file and no mechanically split repository-layer plan. | INT-2, REVIEW-2 |
| DEC-005 | Compact artifacts use one `plan.md` with inline dependency-ordered vertical slices and the reduced compact contract. | Compact mode creates no phase or task files and does not inherit obsolete packet sections. | INT-2, REVIEW-2 |
| DEC-006 | A phase is one cohesive working outcome with one integration point. Split before execution when independently deployable or reversible outcomes exist, or when one reviewer cannot understand and verify the complete phase in one focused pass. Do not split by repository layer, task count, or line count. | The reviewability decision is recorded with the phase boundary; a second review pass caused by an unreviewable scope is a split signal. | INT-2, RES-FUND |
| DEC-007 | Independent review is mandatory for high-risk work and for security, permission, privacy, compliance, irreversible-migration, credible-data-loss, or recovery-critical boundaries. Low risk uses same-agent integrated review. Medium risk uses same-agent review unless novelty weakens independence. | Risk controls and review ownership are conditional and named; “no findings” is not the clean criterion. | INT-2, RES-PHASE, RES-FUND |

The planning commit defaults remain independent policy values: compact uses
`commit_granularity: end`, `commit_approval: always_ask`,
`history_style: separate`; detailed uses `commit_granularity: phase`,
`commit_approval: always_ask`, `history_style: separate`. Commit authority does
not grant implementation, tracker, push, merge, deploy, or release authority.

## 4. Behavioural landscape

Actors and boundaries:

- The planner consumes approved authority, repository evidence, and selected
  host-neutral sources. It resolves technical choices and writes only planning
  artifacts.
- The user confirms or overrides the mode and separately approves the exact
  Plan artifact when authorized to do so.
- The reviewer checks the complete plan or phase against the authority,
  behavior, proof, risk, and scope. Findings are `blocking`, `non-blocking`,
  or `out-of-scope`.
- The implementation actor receives an approved, closed Plan only after the
  shared gate permits entry. It is not asked to choose product behavior,
  architecture, or broad repository research.
- Optional runner and judge processes are trusted maintainer-supplied tools.
  Corpus data never supplies commands, grading authority, or execution secrets.
- Packaging and eval runners provide deterministic evidence and disclose
  unavailable live behavior as `UNMEASURED`.

Relevant states and transitions:

```text
approved intent/spec evidence
  -> planning active
  -> plan awaiting-approval
  -> plan approved
  -> implementation active

missing, stale, mismatched, unauthorized, self, undesignated, same-order,
post-hoc, or full-workflow approval
  -> blocked-at-gate
```

The shared contract owns the actual state transition. A full-workflow request
is continuation intent, not artifact approval. An unavailable live runner is
`UNMEASURED`, not a pass.

## 5. Existing behaviour and required delta

Existing repository behavior relevant to this change:

- the shared Forge contract already defines artifact-specific approvals,
  freshness, mutation ownership, retries, resume, and `UNMEASURED` checks;
- the PR adds proportional mode references and optional evaluation runners;
- the PR's latest review found local workflow restatement, an untracked spec
  authority, obsolete compact/detailed corpus expectations, a structural case
  that claimed behavioral proof, and insufficient custom-fixture isolation.

Required delta:

- make the new Skill and evaluators consume the shared authority rather than
  restate or weaken it;
- make the new Specification and its revision/hash the authority for the
  proportional artifact shapes;
- make static claims structural and behavioral claims independently graded;
- make public runner input allowlisted and oracle-free at every nested level;
- preserve all unrelated worktree files and all generic negative mutation
  boundaries.

Unchanged behavior:

- one Forge workflow remains the host-neutral entry point;
- source and implementation artifacts remain outside Planning authority;
- issue and knowledge transports remain optional adapters;
- missing live provider, runner, judge, browser, manual, or UAT evidence stays
  `UNMEASURED`;
- no downstream tracker actor is required for forge-plan completion.

## 6. Behavioural requirements

| ID | Behaviour | Scope | Verification | Sources |
| --- | --- | --- | --- | --- |
| REQ-001 | `forge-plan` remains one model-invoked Skill. It owns proportional planning only and does not own implementation or downstream tracker mutation. | Trigger and lifecycle boundary. | Inspect Skill frontmatter, trigger corpus, negative routing cases, and package references. | DEC-001, CON-WF, USER-2 |
| REQ-002 | The planner evaluates verified risk and coordination evidence, recommends `compact` or `detailed`, states the decisive evidence, and waits for confirmation or explicit override before loading mode-specific guidance. | Mode selection. | FP-EX-001/002/003/021 behavioral cases and review of the ordered Skill steps. | DEC-001, DEC-002, DEC-003 |
| REQ-003 | Compact mode produces exactly one `plan.md` with outcome/source basis, scope and exclusions, preserved behavior, verified current state, frozen decisions and bounded assumptions, inline dependency-ordered vertical slices, per-slice proof and acceptance, final gates, implementation handoff, and independent commit policy. It produces no task or phase files. | Low-risk plan artifact. | FP-E-001 shape assertions and compact-reference inspection. | DEC-005, CON-WF |
| REQ-004 | Detailed mode produces `plan.md`, one `phase.md` per phase directory, and ordered task files. The control plane owns global IDs, phase graph, frontier, integration points, policies, cross-phase proof, and final acceptance. | Consequential plan artifact. | FP-E-002 shape assertions, detailed-reference inspection, and progressive-loading inspection. | DEC-004, CON-WF |
| REQ-005 | Every inline slice or task is a closed execution packet: stable ID/title, observable outcome, canonical IDs, exact write scope and symbols, preserved and must-not-change behavior, ordered changes, narrow proof with expected result, conditional manual/live proof, and compact handoff fields. | Implementor-facing packet boundary. | Packet-shape mapping test and FP-E-001/002 grading. | CON-WF, DEC-005 |
| REQ-006 | Each detailed phase has one cohesive working outcome, contract, integration point, real blocking edges, full executable frontier, integrated gate, and review focus. Enabling work is allowed only when it unlocks a named working phase. | Phase graph and splitting. | Phase-splitting and wide-refactor cases; mutation tests for false edges and mechanical layer splits. | DEC-006, RES-FUND |
| REQ-007 | Risk controls are conditional. Severe or sensitive risk can require detailed mode and independent review even when the change is small. Rollback, idempotency, observability, compatibility, security, and manual/live proof appear only when their risk exists. | Risk routing and review. | FP-EX-002/011/012 plus structural inspection of conditional references. | DEC-003, DEC-007, RES-PHASE |
| REQ-008 | `forge-plan` links the shared workflow contract near entry and delegates eligibility, artifact ownership, approval, hashes, freshness, resume, retries, and mutation boundaries to that contract and its state helper. It does not implement a weaker local algorithm. | Skill workflow. | Static reference check and source inspection for absence of duplicate gate logic. | CON-WF, REVIEW-2 |
| REQ-009 | Before Planning, the planner applies the shared conditional Specification gate only when `requires_spec_approval` is true. The accepted approval must bind the exact current revision and content hash, use the designated policy when supplied, be independent and non-self, precede the claimed mutation, and use artifact approval intent. | Specification admission. | Regression matrix for self, undesignated, generic, stale, revision-mismatched, same-order, post-hoc, and full-workflow records; shared state-helper tests. | CON-WF, REVIEW-2 |
| REQ-010 | At completion, the planner presents the exact Plan path, revision, and content hash as `awaiting-approval`. It records only a contract-valid artifact approval, then stops. A pre-approval content hash is never called an approval hash. | Plan completion and approval. | FP-EX-005/026 and plan-finalizer inspection; full-workflow and post-hoc cases remain closed. | CON-WF, REVIEW-2 |
| REQ-011 | When issue or knowledge evidence is consumed, the Skill preserves host-neutral provenance, selected references, unavailable evidence, relationship/history conflicts, hashes, and freshness according to the shared source contracts. | Optional source adapters. | Contract-link inspection and unavailable/conflict behavioral cases. | CON-ISSUE, CON-KNOWLEDGE |
| REQ-012 | Every implementation plan's `**Spec:**` path resolves to a tracked Specification whose current revision is not Draft or unresolved. Missing, untracked, stale, or unresolved authority blocks readiness. | Repository authority gate. | Validator test with tracked, missing, untracked, Draft, and resolved fixtures. | INT-2, CON-WF, REVIEW-2 |
| REQ-013 | Repository-static evals make only structural/package claims. FP-EX-020 is labeled structural-only and checks structural facts only; it does not fabricate three role grades or claim no-runner runtime behavior. The behavioral CLI separately proves default `UNMEASURED` and strict nonzero without runners. | Static/behavioral boundary. | Structural mutation tests retain names/options while breaking each structural claim; no-runner CLI tests. | USER-2, REVIEW-2 |
| REQ-014 | The behavioral harness accepts a versioned public fixture only through an explicit nested allowlist. Public runner input contains non-oracle authority, repository, and plan context only. Accepted baselines, expected assertions, graders, rubrics, known answers, and derived labels remain private control data. Oracle-only keys at any nested level are rejected before any process spawn with exit 2 and zero runner calls. | Fixture and oracle isolation. | Custom fixtures placing each forbidden key under authority, repository, and plan; recursive capture and spawn-count assertions. | USER-2, REVIEW-2 |
| REQ-015 | Runner and judge commands are maintainer-supplied JSON argv arrays of non-empty strings with NUL rejection. The harness passes them directly to `subprocess.run(..., shell=False)` and preserves Windows backslashes, spaces, quoted values, and shell metacharacters as literal arguments. | Process execution boundary. | Windows/POSIX argv tests, empty/non-string/NUL rejection, and subprocess capture. | USER-2, CON-WF |
| REQ-016 | The harness validates positive integer `trials` before spawning, defaults omitted trials to 1, sends a stable one-based `trial_index`, requires every role/trial, and reports a missing, malformed, or failed trial as incomplete rather than executed. It compares matching trials and never hides an assertion regression in aggregation. | Trial cardinality and comparison. | One three-trial case produces 9 runner and 9 judge calls; partial-trial and mixed-outcome tests remain visible and fail the required run. | USER-2, REVIEW-2 |
| REQ-017 | Runner output is normalized execution evidence, never self-attested correctness. Trusted graders receive private expected data and evidence, return strict assertion records, and determine correctness and material omissions. Comparisons report candidate versus accepted baseline and no-Skill per assertion, including lost/gained assertions, deltas, improvement, and regression. Baseline/no-Skill incorrectness alone is comparison evidence. | Grading and differential evidence. | Parroting-runner, malformed judge, failed-assertion, candidate-regression, and candidate-improvement tests. | CON-WF, USER-2, REVIEW-2 |
| REQ-018 | Metric values use a versioned schema. `mode` is `compact`, `detailed`, or `UNMEASURED`; booleans are typed; count/token/duration/retry fields are nonnegative integers; coverage is numeric in `[0,1]`; collection fields have declared JSON types; omitted values are `UNMEASURED`; unknown, malformed, negative, or out-of-range values are incomplete. | Runner and judge metric evidence. | Boundary/type tests for every field class and valid partial metrics. | USER-2, REVIEW-2 |
| REQ-019 | The changed evaluators remain importable and compilable on Python 3.8, package policy remains canonical, and packaging/validator gates reject stale or duplicated policy. | Build and packaging behavior. | Python 3.8 compile/CI job, package tests, validator, static runner, and diff check. | USER-2, CON-WF |
| REQ-020 | No active Skill, trigger, eval, research, or plan text assigns downstream conversion ownership to `forge-plan` or uses unrelated downstream conversation as feature provenance. Generic negative tracker-routing/publication cases remain. | Provenance and trigger boundary. | Repository-wide search, trigger/eval negative cases, and clean-room diff review. | INT-2, USER-2, REVIEW-2 |

## 7. Rules and external contracts

### Artifact shapes

Compact mode has one file:

```text
plan.md
```

Its inline slice records use the execution-packet fields required by REQ-005,
but they are not separate task files. `tasks.md`, a separate dependency-ready
task, a former ten-section packet, and any mismatched approval wording are not
valid compact output.

Detailed mode has this progressively loadable shape:

```text
<work-item>/
  plan.md
  phases/
    01-<phase-slug>/
      phase.md
      01-<task-slug>.md
```

Additional ordered task files are allowed within a phase when the phase contract
requires them. The phase directory, not a flat `tasks.md`, owns its task index.

### Workflow approval

The shared workflow contract is the only approval algorithm. The implementation
must call or delegate to its state helper and must preserve these observable
rules:

- conditional Specification approval is required only when the shared contract
  says it is required;
- current revision and content hash must match;
- a supplied designated-approver policy narrows, but never weakens, the gate;
- self, undesignated, unknown, stale, mismatched, same-order, post-hoc, and
  non-artifact/full-workflow approvals keep the gate closed;
- a material artifact change invalidates its approval and dependent gates;
- source mutation is forbidden before the Implementation gate;
- the final Plan content hash is presented before approval and is not called an
  approval hash until a valid approval record exists.

### Public fixture schema, version 1

The public runner fixture is an object with exactly these root keys:

```text
schema_version: positive integer 1
authority: list of authority records
repository: repository record
plan: plan record
```

Each authority record has only `path` (non-empty relative string), `revision`
(positive integer), `status` (`approved` or `awaiting-approval`), and `fresh`
(boolean). The repository record has only `state` (non-empty string) and
`changed_paths` (list of non-empty relative strings). The plan record has only
`revision` (positive integer), `status` (`approved` or `awaiting-approval`),
and `ticket_ready` (boolean). Objects and arrays are validated recursively;
unknown fields and wrong value types are rejected.

The private control plane may retain the fixture source locator, accepted
baseline scenarios, case prompts, expected assertions, grader declarations,
rubrics, known answers, and derived comparison labels. Only the minimum
evidence needed for a trusted judge is sent to that judge. None is sent to an
execution runner.

At any depth, case-insensitive keys equivalent to
`accepted_baseline`, `accepted_baseline_fixture`, `expected`, `grader`,
`graders`, `rubric`, `known_answer`, `answer_key`, `oracle`, or `gold` are
forbidden in public input. Known-answer material under an otherwise allowed
field is also rejected by the typed allowlist. Rejection happens before the
first runner or judge spawn and returns exit 2.

### Runner, judge, trial, and metric records

Runner output may contain only normalized evidence keys: `response`,
`artifacts`, `trace`, `mutations`, `errors`, and `metrics`. It has no `passed`
or correctness field. Judge output has only `assertions` and `metrics`; each
assertion has exactly non-empty string `text`, boolean `passed`, and non-empty
string `evidence`, and every expected assertion appears exactly once.

Metric schema version 1 permits `UNMEASURED` for any metric. `mode` is
`compact` or `detailed`; `correctness` is boolean; count fields are nonnegative
integers; coverage fields are numbers in `[0,1]`. `errors` is an array of
`{"message": non-empty string}`; `review_findings` is an array of
`{"severity": non-empty string, "summary": non-empty string}`; and
`deviations` is an array of `{"description": non-empty string}`. Cross-type
substitutions are invalid. The report metadata includes this exact schema.

The harness uses one-based trial indices. For a case with `trials: 3`, it
requires candidate, baseline, and no-Skill results for trials 1, 2, and 3 and
the corresponding nine judge results. Any missing or failed required result
prevents `COMPARED`/`EXECUTED`. Aggregate comparison retains all trial
comparisons and marks regression if any required trial loses an assertion.

### Static-only choice

FP-EX-020 is structural-only. Its rubric may assert function/option/import,
`shell=False`, schema, and static/behavioral separation facts. It may not assert
that a runner was executed, that three roles were compared, or that no-runner
behavior was `UNMEASURED`. Those runtime outcomes belong to the behavioral CLI
and its subprocess tests.

## 8. Acceptance and success

The following scenarios are required. Each is observable and can be executed
without a live model unless the scenario is explicitly marked `UNMEASURED`.

| ID | Given / When / Then | Covers |
| --- | --- | --- |
| AC-001 | Given a verified bounded low-risk change, when the planner recommends a mode, then it recommends compact, states evidence, waits for confirmation, and loads only compact guidance after confirmation. | REQ-002, DEC-001..003 |
| AC-002 | Given one severe security or permission factor, when the planner sizes the work, then it recommends detailed and names independent review and security proof despite small file count. | REQ-002, REQ-007 |
| AC-003 | Given confirmed compact mode, when the plan is produced, then exactly one `plan.md` contains inline dependency-ordered slices and current compact fields, with no phase/task files or obsolete packet sections. | REQ-003, REQ-005 |
| AC-004 | Given confirmed detailed mode, when the plan is produced, then `plan.md`, phase files, and ordered task files form a progressive tree with current packet fields and real edges. | REQ-004, REQ-006 |
| AC-005 | Given an unresolved product or material architecture decision, when completion is attempted, then the planner names the gap and blocks/returns upstream; it does not relabel the blocker as resolved. | REQ-005, REQ-007, REQ-010 |
| AC-006 | Given each self, undesignated, generic, stale, revision-mismatched, same-order, post-hoc, and full-workflow approval record, when Planning or Implementation entry is checked, then the shared state helper keeps the gate closed. | REQ-008, REQ-009, REQ-010 |
| AC-007 | Given a completed Plan, when it is presented, then path, revision, and content hash are shown as awaiting-approval; only a later exact artifact approval can be recorded, and the process stops. | REQ-010 |
| AC-008 | Given an implementation plan whose `**Spec:**` path is missing, untracked, Draft, or unresolved, when the repository gate runs, then readiness fails; a tracked resolved Specification passes that gate. | REQ-012 |
| AC-009 | Given a custom fixture with `expected`, `grader`, `rubric`, `accepted_baseline`, or known-answer data nested under authority, repository, or plan, when `--fixture` is parsed, then exit is 2 and runner invocation count is zero. | REQ-014 |
| AC-010 | Given a trusted three-trial case, when the harness runs, then it makes exactly 9 runner and 9 judge calls with matching one-based indices; a partial trial produces incomplete/non-executed output. | REQ-016 |
| AC-011 | Given malformed metric types, negative counts, booleans in count fields, invalid mode, or coverage outside `[0,1]`, when output is normalized, then grading is incomplete; valid partial metrics retain `UNMEASURED` fields. | REQ-018 |
| AC-012 | Given Windows paths with spaces/backslashes and shell metacharacters in argv files, when a runner is invoked, then each argument arrives unchanged and no shell is used. | REQ-015 |
| AC-013 | Given a runner that parrots expected text or a judge that omits/mangles an assertion, when grading runs, then no correctness pass is produced. Given candidate passes while baseline/no-Skill fail, the comparison executes and records positive per-assertion deltas. | REQ-017 |
| AC-014 | Given a mutation that retains FP-EX-020 AST names/options but removes a claimed structural invariant, when static evals run, then the mutation fails. The static case does not fabricate role comparison. | REQ-013 |
| AC-015 | Given no trusted live runner or judge, when default and strict behavioral commands run, then default reports `UNMEASURED` and strict exits nonzero. | REQ-013, REQ-017 |
| AC-016 | Given generic requests to publish or prepare tracker records, when routing is evaluated, then forge-plan is not selected and its negative tracker boundary remains intact. | REQ-001, REQ-020 |
| AC-017 | Given Python 3.8, when changed evaluator modules compile and required CI commands run, then syntax and package gates pass without newer annotation syntax. | REQ-019 |

Success means all deterministic acceptance checks and required package gates
pass, no blocking semantic finding remains, the current compact/detailed
corpora map to this Specification and the packet reference, and unavailable
live behavior is explicitly `UNMEASURED`. It does not include a claim about
live model quality, provider readiness, or production performance.

## 9. Traceability

| Requirement group | Authority / decision | Acceptance |
| --- | --- | --- |
| REQ-001, REQ-020 | INT-2, DEC-001, CON-WF, USER-2 | AC-016 |
| REQ-002, REQ-007 | DEC-001, DEC-002, DEC-003, DEC-007, RES-FUND | AC-001, AC-002, AC-005 |
| REQ-003, REQ-005 | DEC-005, CON-WF, USER-2 | AC-003 |
| REQ-004, REQ-006 | DEC-004, DEC-006, RES-FUND | AC-004 |
| REQ-008, REQ-009, REQ-010 | CON-WF, REVIEW-2 | AC-006, AC-007 |
| REQ-011 | CON-ISSUE, CON-KNOWLEDGE | AC-005 |
| REQ-012 | INT-2, CON-WF, REVIEW-2 | AC-008 |
| REQ-013, REQ-014, REQ-015 | USER-2, REVIEW-2 | AC-009, AC-012, AC-014, AC-015 |
| REQ-016, REQ-017, REQ-018 | USER-2, REVIEW-2, CON-WF | AC-010, AC-011, AC-013, AC-015 |
| REQ-019 | USER-2, CON-WF | AC-017 |

Every artifact-shape assertion in FP-E-001 and FP-E-002 must carry a mapping
to one of REQ-003, REQ-004, or REQ-005 and the corresponding compact,
detailed, or execution-packet clause. A mapping with no current clause, an
obsolete `tasks.md`/ten-section assertion, or an awaiting-approval claim that
does not match REQ-010 is invalid and fails the deterministic mapping test.

## Readiness decision

All seven Intent decisions are resolved in section 3 and in `intent.md`
revision 2. The Specification is implementation-ready in content but remains
`awaiting explicit approval` until the user approves these exact Intent and
Specification revisions and the shared workflow contract records their hashes.
