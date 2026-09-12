# Forge-plan modes: source research and BR-21598 analysis

## Bottom line

Add two planning depths, not two unrelated workflows. Keep one short orchestration core; disclose the detailed-mode contract only when selected. Do **not** copy the BR-21598 folder structure wholesale.

The BR-21598 bundle is strong as an as-built/regeneration dossier. It is weak as a fresh implementation plan: 24 Markdown files, repeated decisions, horizontal backend/frontend/database task buckets, exact code copies, and visible stale contradictions.

## What BR-21598 gets right

Read-only source: `D:\AI\skills\BR-21598-company-timesheet`.

- Strong evidence boundary: authoritative sources, evidence classification, prototype-only facts, and mandatory code-understanding report.
- Explicit execution contract: scope, preserved behaviour, exclusions, roles/access, validation, data, security, and operational guardrails.
- Traceability: numbered functional requirements, acceptance criteria, task mapping, dependency graph, test matrix, Definition of Ready, and Definition of Done.
- Implementation-grade detail where risk warrants it: exact API contracts, persistence rules, authorization gates, compatibility constraints, edge cases, known gaps, and regeneration order.
- Honest status labels distinguish delivered behaviour from planned-but-unimplemented tests.

These are the useful ingredients for the detailed mode.

## Brutal review

- **It is not one plan.** It mixes requirement analysis, proposed design, task plans, as-built truth, code recovery instructions, and QA checklists. Forge-plan should generate a coherent plan, not an archive format.
- **It contradicts itself.** The requirement analysis still proposes a create modal and an optional `IsCompanyCreated` column, while later authoritative sections say routed page and no such column. Its gap table still says initial stage needs confirmation after that decision is resolved elsewhere.
- **It is horizontally sliced.** Separate Database, Backend, Frontend, Mobile, and Testing tasks defer usable behavior and increase integration risk. The plan should prefer narrow end-to-end slices.
- **It duplicates decisions.** Mode source, lifecycle, mobile scope, permissions, and file impacts recur across the requirement analysis, handoff, task files, implementation sequence, and as-built README. This creates drift.
- **It over-specifies volatile implementation.** Exact snippets and “regenerate byte-for-byte” instructions copy facts already recoverable from source. Useful for disaster recovery; brittle and noisy for planning.
- **Testing is late.** A distinct final testing phase conflicts with agent-ready vertical slices. Each slice should carry its own verification; keep only cross-cutting regression/UAT as a final gate.
- **Its scale is costly.** The bundle is about 160 KB of Markdown before the HTML wireframe. An agent must reconcile too much context before acting.

## What to borrow from `to-tickets`

Primary source: [mattpocock/skills — to-tickets](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-tickets/SKILL.md).

Borrow:

- Tracer-bullet vertical slices: each task crosses relevant schema/API/UI/tests and is independently demoable or verifiable.
- A fresh-context size limit per task.
- Explicit `Blocked by` edges and dependency-order output.
- Prefactoring before feature slices when it materially simplifies delivery.
- Expand–migrate–contract for unavoidable wide refactors.
- A user checkpoint on granularity and dependency edges before final publication.

Do not borrow tracker publication into forge-plan. Planning and publishing tickets are separate mutations/responsibilities. Forge-plan may emit ticket-ready sections; another skill can publish them.

Also do not adopt the blanket “avoid file paths” rule. A detailed implementation plan needs verified paths/symbols to reduce rediscovery. Avoid pasted working code and line numbers likely to drift; retain paths, contracts, and decision-rich shapes.

## What to borrow from `writing-for-agents`

Primary sources: [writing-for-agents](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md) and [skill mechanics](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL-MECHANICS.md).

- Keep steps in the main skill; move mode-specific reference/templates behind explicit pointers.
- Inline rules common to both modes. Load detailed artifacts only for the detailed branch.
- Give every stage a checkable, exhaustive completion criterion.
- Co-locate each rule with its caveats; one meaning, one source of truth.
- Delete environment caches: commands, paths, or structures the agent can cheaply inspect.
- Delete no-op prose and repeated warnings; state positive targets, reserving prohibitions for real guardrails.
- Keep one model-invoked `forge-plan` router instead of two separately discoverable skills unless independent invocation proves necessary.

## Recommended two-mode shape

Names intentionally deferred to grilling.

### Current/light mode

For bounded changes with low coordination risk.

One plan file containing: outcome, verified current-state summary, scope/exclusions, decisions/assumptions, vertical slices with paths/contracts and per-slice verification, dependency order, final gates, and unresolved blockers.

### Detailed mode

For cross-system, regulated, migration-heavy, multi-agent, or recovery-sensitive work.

Same core plan plus selectively generated appendices/artifacts:

- evidence ledger and authority order;
- requirement/acceptance traceability;
- affected systems and verified paths/symbols;
- data migration/rollback/compatibility plan;
- permission, security, failure, concurrency, and operational analysis;
- dependency graph and parallel frontier;
- per-slice tests plus final regression/UAT matrix;
- Definition of Ready/Done and handoff contract.

Detailed must mean **more proof and risk coverage**, not more repetition or pasted code. Use one canonical decision table and references from slices.

## Selection rule

Ask during grilling, but recommend detailed mode when any two apply: multiple deployables/repositories; schema or irreversible migration; permissions/security/compliance; external integration; more than one implementer/agent; ambiguous legacy behavior; explicit audit/recovery need. Otherwise default to current/light.

## `intent.md` implications

Anthropic's first-party playbook defines `intent.md` as the reviewed, version-controlled proto-spec containing what is wanted, why, affected users/systems, constraints, and open questions. It explicitly places `intent.md` before `spec.md`, and `spec.md` before `plan.md`; each approved artifact gates the next stage. [Anthropic AI-native SDLC playbook](https://claude.com/blog/the-ai-native-sdlc-playbook)

Therefore forge-plan should consume an approved intent/spec when present, preserve unresolved questions, and never silently invent intent. The final project `intent.md` should describe this skill change's problem and outcome, not duplicate the implementation plan.

The DEV article is a secondary case study, not a normative source. Its useful support is narrower: structured specifications, RFCs, machine-readable tasks, acceptance criteria, and traceability can make complex parallel work more queryable. Its own warning matters: this approach is overkill for prototypes, solo work, or genuinely unknown requirements. [DEV intent-driven case study](https://dev.to/copyleftdev/intent-driven-development-define-the-system-before-you-write-the-code-22pe)

## Proposed forge-plan changes

1. Add a grilling-time mode decision with neutral placeholder labels until names are approved.
2. Keep one shared pipeline: establish intent/source authority → inspect repository → resolve material questions → choose depth → draft vertical slices → validate traceability/dependencies → user approval → write artifacts.
3. Add a detailed-mode reference/template; do not double the main skill body.
4. Replace layer-based task generation with vertical slices; document wide-refactor exception.
5. Put tests and verification inside every slice; retain a short final semantic/regression gate.
6. Add canonical decision and evidence tables. Every later section references IDs rather than restating prose.
7. Preserve verified paths and symbols, but remove copied implementation code unless it captures a decision that prose cannot.
8. Separate plan creation from ticket publishing and from as-built documentation.
9. Add evals for: mode routing, low-risk default, detailed risk trigger, no duplication, vertical slicing, unresolved-question preservation, and stale-source conflict detection.

## Research limits

- BR-21598 inspection was local and read-only. It was assessed as documentation, not verified against its production repositories.
- Anthropic is primary for its own proposed SDLC process. The DEV post is an individual case study; its productivity claims were not independently validated.
