# Software fundamentals for Forge detailed planning

## Blunt verdict

Adopt the fundamentals that reduce hidden dependencies, late integration, and repeated reading. Make risk-specific practices conditional. Reject checklist theatre.

The key change: `forge-plan` should make each phase a **small, working vertical outcome with a clear boundary and proof**. A phase is not automatically a module, portal, or technical layer. Those are good boundaries only when they deliver usable behaviour and hide a coherent decision.

## Adopt

| Fundamental | Rule for detailed mode | If adopted | If ignored |
|---|---|---|---|
| Information hiding and high cohesion | Group work around one behaviour or decision that can change without forcing unrelated changes. Name the owned contract and hidden detail. | Smaller task context; safer parallel work. | “Module phases” can still spread one decision across many files and phases. |
| Explicit contracts and invariants | For every changed boundary, state inputs, outputs, errors, compatibility rules, and facts that must remain true. Reference these from tasks; define them once. | Implementors know what may change and what must not. | Each task guesses; individually correct work fails when joined. |
| Vertical, incremental delivery | Every phase must leave the system working and prove a user-visible or operator-visible outcome. Allow enabling work only when it unlocks a named later phase. | Problems appear early; progress is real. | Horizontal phases defer value and integration risk. |
| Small batches and fast feedback | Keep phases reviewable in one focused pass. Run narrow checks during tasks, then integrated phase checks. | Faster diagnosis, review, and rollback. | Large phases hide defects and make review shallow. |
| Traceability | Give requirements, invariants, decisions, risks, and acceptance checks stable IDs. Map each once to its owning phase/task and proof. | Gaps and unowned requirements are visible without repeating prose. | Important intent is lost, or copied text drifts. |
| Dependency graph | `plan.md` records only real blocking edges, the current parallel frontier, and integration points. Tasks do not restate the graph. | Safe parallelism; no false ordering. | Agents collide or wait unnecessarily. |
| Reviewability | Phase gate covers design, behaviour, tests, complexity, scope, and integration. Split before execution if one reviewer cannot understand the phase in one pass. | Review can find important defects. | “Phase review” becomes a rubber stamp over a giant diff. |
| Configuration and change control | Record the approved baseline and changes to scope/decisions. A deviation updates the canonical source and impacted mappings, not every task file. | Resume and handoff remain trustworthy. | The plan and implementation silently diverge. |
| Simplicity | Include only information that changes implementation, verification, ordering, or risk. One source per fact. | Lower context cost without losing decisions. | Detailed mode becomes an archive that consumes tokens and goes stale. |
| Proportional risk | Give each phase a short risk level with reasons. Use risk to increase test depth, review independence, and recovery detail. | Effort goes where failure hurts. | Uniform detail over-plans safe work and under-plans dangerous work. |

Parnas shows that good modularisation hides design decisions likely to change; grouping by processing steps is not enough. Google says a review change should be one self-contained idea, keep the system working, include tests, and stay small enough for thorough review. NASA requires bidirectional requirements traceability and controlled requirement changes. These directly support the rules above. [Parnas, 1972](https://doi.org/10.1145/361598.361623), [Google: Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html), [NASA Systems Engineering Handbook](https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf)

## Adopt only when the risk exists

| Fundamental | Trigger and plan rule | Why conditional |
|---|---|---|
| Risk-based test depth | Always require the cheapest test that proves the task. Add contract, integration, end-to-end, performance, security, migration, manual, or live tests only for affected risks. | A fixed test pyramid is a useful hint, not a universal quota. Repeated high-level tests are slow and brittle. [Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html) |
| Reversibility and rollback | Require rollback triggers, method, owner/authority, and rollback proof for data, deployment, permission, external-side-effect, or hard-to-reverse changes. | A rollback section on a local refactor is noise. For stateful cutovers, an untested rollback plan can be false safety. [AWS cutover guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/best-practices-migration-cutover/cutover-stage.html) |
| Idempotency | Require an idempotency key/identity and retry proof for retryable writes, jobs, webhooks, migrations, and resumable automation. | It is irrelevant to pure reads and many local transformations. Without it, retries can duplicate side effects. [AWS idempotency guidance](https://docs.aws.amazon.com/wellarchitected/2022-03-31/framework/rel_prevent_interaction_failure_idempotent.html) |
| Observability | For runtime behaviour, name the signal that proves success/failure: log, metric, trace, audit event, or visible state. Include signal ownership and noise limits for alerts. | Compile-time changes need no fake monitoring requirement. Runtime changes without a signal remain hard to verify and debug. [Google SRE: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) |
| Fail fast | Validate cheap, deterministic preconditions before expensive or irreversible work. Stop on broken baseline, missing authority, contract mismatch, or failed required gate. | “Fail fast” must not mean crashing on recoverable user/runtime errors. Used blindly, it reduces resilience. |
| Expand–migrate–contract | Use for schemas, public APIs, protocols, and rolling deployments that cannot change atomically. State when old and new forms coexist and when removal is safe. | Unneeded for atomic internal changes. Without it, mixed versions can break. AWS likewise recommends backward compatibility and a rollback path during decomposition. [AWS database decomposition](https://docs.aws.amazon.com/pdfs/prescriptive-guidance/latest/database-decomposition/database-decomposition.pdf) |
| Security overlay | For security-sensitive phases, map the relevant secure-development outcome and require independent review where the risk warrants it. | NIST SSDF is risk-based and outcome-focused; copying the whole framework into every plan is waste. [NIST SSDF](https://csrc.nist.gov/projects/ssdf) |

## Do not turn these into hard rules

- **One phase per module or portal:** reject as a rule. Use it only when the boundary is cohesive and produces a working outcome. Otherwise it recreates horizontal slicing.
- **DRY everywhere:** reject. Remove repeated *knowledge*, but allow small local duplication when sharing would couple unrelated work. The Forge-specific rule should be “one canonical decision,” not “abstract every repeated sentence or code shape.”
- **YAGNI as “ignore future compatibility”:** reject. Avoid speculative features, but plan known compatibility, migration, rollback, and extension constraints.
- **Mandatory task review:** reject. Review the integrated phase. Escalate task-level review only for irreversible, security-critical, or unusually uncertain work.
- **Full phase re-review after every fix:** reject. Run affected checks per fix; perform one final integrated review after blocking findings close.
- **Formal critical-path calculation:** reject for normal software plans. Record blocking edges and the executable frontier. Estimates are usually too weak to justify scheduling mathematics.
- **Observability, rollback, idempotency, and security appendices in every plan:** reject. Trigger them by risk. Empty sections cost tokens and create false confidence.

## Minimal detailed-mode contract

`plan.md` should contain only:

1. Outcome, scope, exclusions, and approved baseline.
2. Canonical contracts, invariants, decisions, risks, and their IDs.
3. Phase graph: outcome, dependencies, parallel frontier, integration point, and gate.
4. Change/commit/approval policy.
5. Cross-phase proof and final acceptance.

Each phase file should contain only shared phase context, its task index, integration contract, gate, and review focus.

Each task file should contain only its outcome, exact write scope, referenced IDs, local constraints, steps, proof command/observation, and compact handoff fields.

This is the token-saving principle: **progressive context loading plus references, not compressed ambiguity**. The implementor reads global facts once, phase facts once, and only the active task. Do not copy research, requirements, contracts, or prior task summaries into every file.

## Add to `intent.md`

- Phase boundaries follow cohesive working outcomes, not repository layout by default.
- Each phase names its contract, invariants, integration point, and observable proof.
- The system must remain usable after each phase unless the plan records an approved exception and recovery path.
- `plan.md` owns the dependency graph and parallel frontier.
- Stable IDs provide traceability without duplicated prose.
- Use explicit `depends_on` fields; parallel work is everything whose dependencies are already complete. Avoid prose-only ordering.
- Risk triggers decide extra tests, rollback, idempotency, observability, compatibility, security, and manual/live proof.
- Phase size is limited by reviewability, not task count or line count.
- Plan deviations update the canonical decision and affected mappings before later phases continue.
- Prefer the cheapest proof that covers the risk; do not duplicate the same assertion at every test level.
- Simple English is a correctness control: short sentences, one meaning per requirement, concrete verbs, and no unexplained jargon.

## Remove or avoid in `intent.md`

- Treating module/portal boundaries as automatically vertical.
- Mandatory empty sections for risks that do not exist.
- Exact task-by-task prose repeated in `plan.md`.
- A universal test pyramid, rollback requirement, or formal critical path.
- “DRY,” “YAGNI,” “SOLID,” or “separation of concerns” as unexplained slogans. Convert each accepted idea into an observable planning rule.

## Evidence limit

The sources support modular boundaries, small self-contained changes, fast integration feedback, traceability, controlled change, layered tests, rollback, idempotency, and runtime monitoring. The proposed Forge file split and token-saving effect are derived design choices. Their implementation accuracy, token savings, and defect rate remain **UNMEASURED** until compared on real plans.

Additional sources: [Agile principles](https://agilemanifesto.org/principles), [Meyer: Applying Design by Contract](https://www.state-machine.com/doc/Mayer92.pdf), [ISTQB risk-based testing](https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf), [Fowler and Foemmel: Continuous Integration](https://martinfowler.com/articles/originalContinuousIntegration.html), [Google: What to look for in review](https://google.github.io/eng-practices/review/reviewer/looking-for.html), [Google: Review standard](https://google.github.io/eng-practices/review/reviewer/standard.html).
