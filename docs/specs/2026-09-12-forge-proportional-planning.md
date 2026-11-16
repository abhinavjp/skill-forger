# Forge Proportional Planning Specification

## Problem Statement

Forge currently defines one planning depth. That depth can leave consequential work without enough traceability, risk control, or coordination detail, while applying it uniformly to bounded work would add ceremony, context cost, and stale duplication.

Planners need one `forge-plan` Skill that recommends an appropriate planning depth from verified evidence, obtains the user's confirmation, and produces implementation-ready vertical work. Implementors and reviewers need enough detail to act without rediscovering the repository, selecting architecture, interpreting product intent, or reconciling duplicated facts. Planning must retain Forge's approval, provenance, freshness, mutation, and authority boundaries.

## Solution

Extend the single model-invoked `forge-plan` Skill with two progressively disclosed modes: `compact` and `detailed`.

Forge assesses the known size, effort, complexity, impact, reversibility, execution model, and uncertainty. It recommends a mode, explains decisive evidence and uncertainty, and waits for confirmation or override before loading mode-specific guidance. Compact mode produces one semantically closed `plan.md`. Detailed mode produces a control-plane `plan.md`, one directory per cohesive vertical phase, one `phase.md` per phase, and fresh-context-sized task files.

Both modes produce dependency-correct vertical work, observable proof, explicit scope, and a closed implementation handoff. Detailed mode adds traceability and only the risk controls the work warrants. Planning ends after approval. Implementation, commits, tracker publication, push, merge, deployment, and release remain separately authorized actions.

## User Stories

1. As a planner, I want one `forge-plan` entry point, so that planning behavior remains discoverable and consistent.
2. As a planner, I want Forge to distinguish `compact` and `detailed` planning, so that planning depth is proportional to the work.
3. As a planner, I want Forge to assess size, effort, complexity, impact, reversibility, coordination, and uncertainty together, so that its recommendation reflects the whole change.
4. As a planner, I want Forge to avoid a hard signal-count threshold, so that one severe risk can justify detailed planning.
5. As a planner, I want bounded low-risk work to default toward compact mode, so that routine work stays concise.
6. As a planner, I want Forge to recommend detailed mode for material migration, security, privacy, compliance, recovery, integration, mixed-version, multi-implementer, audit, or legacy-ambiguity risk, so that consequential work receives adequate control.
7. As a user, I want the recommendation, decisive evidence, and uncertainty stated plainly, so that I can judge it.
8. As a user, I want to confirm or override the recommendation, so that Forge never chooses planning depth silently.
9. As a user, I want Forge to honor an explicit detailed-mode request, so that I can require stronger traceability for any work.
10. As a user, I want Forge to reject an unsafe compact packet with the exact unresolved gap, so that reduced detail never weakens readiness.
11. As a user, I want options to narrow scope, accept detailed mode, or return upstream when compact cannot close the work, so that I retain control.
12. As a user, I want Forge to pause and reconfirm if later evidence changes the recommendation, so that the selected mode remains informed.
13. As a planner, I want approved upstream artifacts loaded in authority order, so that lower-authority evidence cannot overwrite settled decisions.
14. As a planner, I want source provenance, approval hashes, and freshness verified, so that plans are based on current authorized inputs.
15. As a planner, I want stale or contradictory evidence surfaced, so that it is not silently treated as current truth.
16. As a planner, I want missing product intent returned to discovery or clarification, so that planning does not invent requirements.
17. As an implementor, I want every execution packet to close product, architecture, scope, and material alternative decisions, so that implementation needs no design interview.
18. As an implementor, I want verified paths, symbols, contracts, and commands retained where useful, so that I avoid broad rediscovery.
19. As a maintainer, I want volatile line numbers, copied source listings, and recoverable repository facts omitted, so that plans resist staleness.
20. As a compact-plan implementor, I want one `plan.md` with outcome, source basis, scope, exclusions, preserved behavior, current state, frozen decisions, slices, proof, acceptance, gates, and handoff fields, so that bounded work is semantically closed.
21. As a compact-plan reader, I want empty risk sections omitted, so that concision does not become checklist theater.
22. As a Forge user, I want compact mode to preserve approval, provenance, freshness, and mutation gates, so that shorter planning is not weaker governance.
23. As a detailed-plan reader, I want `plan.md` to be the control plane, so that global facts and policies have one source of truth.
24. As a detailed-plan implementor, I want each phase in its own directory with `phase.md` and ordered task files, so that I can load only current context.
25. As a detailed-plan implementor, I want each phase to own one cohesive working outcome, contract, and integration point, so that work is vertically sliced.
26. As a reviewer, I want phase boundaries based on one-pass reviewability and independent reversibility, so that phases remain understandable.
27. As a planner, I want numeric file, task, or boundary counts treated only as warnings, so that cohesive wide changes are not split mechanically.
28. As a planner, I want enabling work allowed only when it unlocks a named working phase, so that horizontal scaffolding does not become an end state.
29. As a planner, I want expand-migrate-contract sequencing for non-atomic boundaries, so that mixed versions can coexist safely.
30. As an implementor, I want the system left working after each normal phase, so that integration risk appears early.
31. As a detailed-plan reader, I want stable requirement, invariant, contract, decision, risk, phase, and task IDs, so that traceability does not require repeated prose.
32. As an implementor, I want task files to reference canonical IDs, so that binding decisions remain consistent.
33. As an implementor, I want each task to name one observable outcome, exact write scope, relevant symbols, constraints, ordered changes, narrow proof, expected result, and handoff fields, so that it fits a fresh context.
34. As a coordinator, I want explicit `depends_on` edges and the current executable frontier, so that safe parallel work is visible.
35. As a coordinator, I want only real blocking edges recorded, so that false sequencing does not reduce throughput.
36. As a reviewer, I want every phase classified as low, medium, or high risk with reasons, so that review depth is explainable.
37. As a reviewer, I want high-risk phases independently reviewed, so that severe impact or difficult recovery receives independent scrutiny.
38. As a reviewer, I want security, permission, privacy, compliance, irreversible migration, data-loss, and recovery-critical boundaries independently reviewed regardless of aggregate label, so that sensitive risks cannot be averaged away.
39. As a planner, I want task-level semantic review only for irreversible, security-critical, or unusually uncertain steps, so that routine tasks avoid redundant review.
40. As an operator, I want rollback specified only for deployed, stateful, external-side-effect, or hard-to-reverse work, so that recovery detail appears where meaningful.
41. As an operator, I want idempotency specified for retries, jobs, webhooks, migrations, and resumable operations, so that repeated execution cannot duplicate effects.
42. As an operator, I want observability specified for runtime behavior needing operational proof, so that success and failure can be seen.
43. As a tester, I want manual, browser, hardware, migration, performance, live-provider, security, or UAT proof required only when automation cannot cover the relevant risk, so that evidence is proportional.
44. As an implementor, I want task-local checks run during work and integrated checks run before phase review, so that defects are found near their source.
45. As a reviewer, I want the complete phase reviewed for intent, behavior, architecture, security, regressions, maintainability, and scope, so that integration defects are visible.
46. As a reviewer, I want findings classified as blocking, non-blocking, or out-of-scope, so that completion is not confused with perfection.
47. As a reviewer, I want affected checks rerun after blocking fixes and one final integrated review after the blocking set closes, so that closure is verified without endless full reviews.
48. As a user, I want execution stopped when two review loops make no progress or reviewers materially disagree, so that disagreement is not hidden.
49. As a user, I want a clean phase to mean required checks pass and zero blocking findings remain, so that minor advice does not block progress.
50. As a user, I want a phase handoff to record proof, deviations, non-blocking findings, and `UNMEASURED` behavior, so that evidence limits remain explicit.
51. As a user, I want each detailed phase to pause after its clean gate, so that I control continuation.
52. As a user, I want the pause to offer only applicable actions—continue, named extra testing, commit, revise, or stop—so that the next decision is concrete.
53. As a user, I want required automated checks completed before the pause, so that “extra testing” never substitutes for basic validation.
54. As a user, I want every plan to freeze commit granularity, commit approval, and history style independently, so that Git behavior is unambiguous.
55. As a compact-mode user, I want the default commit policy to be end, always-ask, and separate, so that small work remains controlled.
56. As a detailed-mode user, I want the default commit policy to be phase, always-ask, and separate, so that verified phases form useful checkpoints.
57. As a user, I want preapproved commits allowed only after their configured clean gate, so that preapproval cannot bypass verification.
58. As a user, I want commit authority separated from push, merge, deployment, and release authority, so that one mutation never implies another.
59. As a user, I want policy changes to require explicit approval, so that Forge cannot silently broaden authority.
60. As a tracker user, I want an optional formal read-only `to-tickets` handoff, so that an approved plan can be converted without rewriting it.
61. As a tracker user, I want the handoff to contain the approved plan hash, stable IDs, ticket outcomes, dependency edges, frontier, scope and acceptance references, and risk/review/approval references, so that publication preserves the plan contract.
62. As a tracker user, I want ticket publication to remain a separate authorized invocation, so that planning never writes externally.
63. As a maintainer, I want the portable core to rely only on `SKILL.md` and relative resources, so that it remains harness-agnostic.
64. As a maintainer, I want host runners, hooks, permissions, and invocation adapters optional, so that unavailable host features do not invalidate portable behavior.
65. As a maintainer, I want the shared workflow in the main Skill and mode-specific details loaded only after selection, so that context use stays proportional.
66. As a maintainer, I want every concept to have one authoritative definition, so that mode references cannot drift.
67. As an evaluator, I want static, trigger, execution, and differential evidence reported separately, so that each claim has a clear basis.
68. As an evaluator, I want positive, negative, boundary, adversarial, regression, paraphrase, near-neighbor, competing-Skill, large-input, and failure-injection cases where applicable, so that routing and behavior are robust.
69. As an evaluator, I want candidate behavior compared with the accepted `forge-plan` baseline and a no-Skill baseline where informative, so that improvements are attributable.
70. As an evaluator, I want correctness and material omission measured before efficiency, so that token savings cannot excuse lower quality.
71. As an evaluator, I want requirement coverage, dependency errors, scope errors, blocking questions, rediscovery, context tokens, output tokens, loaded references, tool calls, duration, retries, errors, review findings, and deviations measured per mode, so that tradeoffs are observable.
72. As a user, I want unavailable runtime, catalog, model, provider, live-service, and production evidence labeled `UNMEASURED`, so that missing proof is never reported as passing.
73. As a user, I want accuracy, token, latency, and defect-rate claims withheld until repeated representative differential trials exist, so that Forge makes no unsupported benefit claims.
74. As a user, I want planning to stop after plan approval, so that specification work grants no implementation or publication authority.

## Implementation Decisions

- Keep one model-invoked `forge-plan` Skill. Do not create separately discoverable mode Skills.
- Define exactly two modes: `compact` and `detailed`.
- The main Skill owns the shared ordered workflow: establish authority and freshness; verify the repository; resolve or route missing intent; recommend and confirm mode; load one mode reference; create dependency-correct vertical work; validate readiness; obtain approval; stop.
- Recommend a mode using the combined evidence for size, effort, complexity, impact, reversibility, execution model, and uncertainty. No fixed signal count decides the mode.
- Default toward compact only when evidence supports bounded, low-risk work. A single severe factor or several moderate factors may justify detailed mode.
- Require user confirmation or override before loading mode-specific instructions. Reconfirm after later evidence materially changes the recommendation.
- If compact mode cannot close material decisions, evidence, or safety constraints, identify the exact gap and offer scope reduction, detailed mode, or an upstream return.
- Compact mode emits one semantically closed `plan.md`. It omits empty conditional sections but preserves all shared authority and safety gates.
- Detailed mode emits a control-plane `plan.md`, a `phases` collection containing one directory per phase, a `phase.md` per phase, and ordered task files.
- The control plane owns global outcome, scope, exclusions, baseline, authority, stable IDs, phase graph, frontier, integration points, policies, cross-phase proof, and final acceptance.
- A phase owns one cohesive working outcome, contract, invariants, integration point, risk classification, task index, local dependencies, shared references, integrated gate, review focus, and handoff contract.
- A task owns one observable outcome, exact write scope and relevant symbols, referenced canonical IDs, local constraints, ordered changes, narrow proof with expected result, and compact handoff fields.
- Define phases by cohesive behavior and one-pass reviewability, not repository layers or numeric counts. Treat the existing requirement/file/boundary counts only as warnings requiring a cohesion rationale.
- Split independently deployable or independently reversible outcomes. Allow enabling work only when it unlocks a named working phase. Use expand-migrate-contract when atomic boundary change is unsafe.
- Record only real dependency edges. The executable frontier is every task whose dependencies are complete.
- Assign low, medium, or high phase risk with reasons. Require independent review for high risk and for the enumerated sensitive or recovery-critical boundaries.
- Add rollback, idempotency, observability, compatibility, security, and extra proof only when the corresponding risk exists.
- The detailed phase gate runs task checks, integrated checks, whole-phase review, blocking remediation, affected rechecks, one final integrated review, handoff recording, then a user pause.
- Define clean as all required checks passing with zero blocking findings. Preserve non-blocking and out-of-scope findings. Stop on two non-progressing loops or material reviewer disagreement.
- Freeze `commit_granularity`, `commit_approval`, and `history_style` independently. Compact defaults are end, always-ask, separate. Detailed defaults are phase, always-ask, separate.
- Commit permission never grants push, merge, deployment, release, tracker, or implementation permission. Policy changes require explicit approval.
- Provide a formal read-only `to-tickets` handoff when requested or approved as the next step. It references canonical plan content and never publishes.
- Package shared orchestration in the main Skill, mode differences in compact and detailed references, and common packet semantics in one execution-packet reference.
- Keep the portable core free of named hosts, models, agents, absolute paths, hooks, or required host-only features.
- Use simple English, stable identifiers, and references to one canonical fact. Retain stable artifact names and contract vocabulary where they define behavior.
- Planning approval is terminal for this Skill. It authorizes no implementation or external mutation.

## Testing Decisions

- Test external Skill behavior, generated artifact contracts, authority boundaries, and observable failure behavior. Do not assert private prompt wording or internal reasoning steps.
- Use the highest viable behavioral seam: fixture-driven invocation of `forge-plan` with approved upstream artifacts and repository state, followed by assertions over recommendation/confirmation behavior and generated artifacts.
- Reuse the existing `brain-plan` fixture scenarios as the accepted behavioral baseline for differential evaluation. The Forge package does not yet exist, so candidate runtime behavior is currently `UNMEASURED`.
- Validate compact scenarios for bounded defaulting, explicit override, closed single-file output, vertical slices, exact scope, proof, approval, and absence of unwarranted risk sections.
- Validate detailed scenarios for severe single-factor and cumulative moderate-factor recommendations, explicit requests, artifact hierarchy, stable traceability, phase cohesion, dependencies, frontier, conditional risk controls, review routing, gates, pauses, and commit policy.
- Validate late evidence escalation, stale-source conflicts, unresolved product intent, unsafe compact requests, duplicate knowledge, wide cohesive refactors, phase splitting, stalled review loops, and planning/implementation separation.
- Keep trigger tests separate from execution tests. Trigger tests cover planning requests, proportional-depth language, near neighbors, competing Skills, and requests that belong to implementation or ticket publication.
- Run deterministic static validation over package shape, relative references, frontmatter, portable-resource rules, and JSON corpus schema. Static success does not prove model behavior.
- Validate failure behavior for missing sibling resources, unavailable optional capabilities, invalid or stale approvals, contradictory baselines, missing tracker capability, and unavailable live checks. Preserve verified work and classify unavailable behavior as `UNMEASURED`.
- Compare the candidate against the accepted `forge-plan` behavior and, where informative, a no-Skill baseline. Adjudicate disputed expectations before attributing failures.
- Measure correctness and material omission first. Then measure blocking questions, rediscovery, traceability and acceptance coverage, dependency and scope errors, context/output tokens, references, tool calls, duration, retries, errors, review findings, and implementation deviations per mode.
- Require repeated representative compact and detailed trials before claiming improved accuracy, token use, latency, or defect rate.
- Use package validators and inspectors as deterministic supporting seams. They complement but do not replace fixture-driven behavioral evaluation.

## Out of Scope

- Implementing or modifying `forge-plan`.
- Creating any of the Forge Skill directories or package resources.
- Modifying Brain adapters or their fixtures.
- Publishing an issue, applying `ready-for-agent`, or configuring an issue tracker.
- Creating tracker tickets from the `to-tickets` handoff.
- Implementing, committing, staging, pushing, merging, deploying, releasing, or changing Git policy.
- Changing `forge-clarify`, `forge-discover`, `forge-spec`, or `forge-implement` behavior beyond preserving their established contracts.
- Changing reference packages such as `ba-1` or `mr-review`.
- Copying the BR-21598 dossier structure or creating an as-built/recovery archive.
- Claiming live accuracy, efficiency, portability, provider behavior, or defect-rate improvement without executed evidence.

## Further Notes

- The approved proportional-planning design is authoritative where earlier intent, research, or implementation-plan assumptions differ.
- Repository inspection on 2026-09-12 found no `forge-*` directories under the canonical packaged Skill location. The nearest existing behavioral reference is the external `brain-plan` package with scenario fixtures.
- Existing unrelated untracked `.claude`, `.vscode`, design, and prior planning paths are outside this specification's mutation scope and must remain untouched.
- The approved proportional-planning design itself is currently untracked. This does not reduce its authority for this local synthesis.
- No issue-tracker provider, project, or `ready-for-agent` vocabulary is configured. This specification is local only; tracker publication and labeling are unperformed.
- Static and repository facts above are verified. Candidate model/runtime behavior and the claimed accuracy or token benefits remain `UNMEASURED`.
