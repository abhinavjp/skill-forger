# Forge Portable SDLC Skills

## Problem Statement

The existing Brain SDLC skills contain useful clarification, discovery,
specification, planning, and implementation behavior, but much of that behavior
is coupled to Brain Payroll, Jira, OKF, project-specific tooling, and host
assumptions. Shared workflow logic is repeated across stages, causing repeated
questions, unnecessary context loading, inconsistent functional coverage, and
quality problems that are discovered late during review instead of prevented
during implementation.

Users need a portable, user-invoked SDLC suite that works across projects and
harnesses. Brain-specific skills should become thin adapters over that suite,
preserving Brain behavior while reusing portable workflow logic. The workflow
must remain token-efficient, evidence-driven, safe to resume, and detailed
enough that a competent workhorse can implement an approved plan without new
research, architecture decisions, or user questions.

## Solution

Create five explicitly user-invoked Forge skills:

- `forge-clarify` resolves unanswered or conflicting human decisions.
- `forge-discover` establishes verified current behavior, affected areas,
  sources, risks, and open decisions.
- `forge-spec` produces an approved, testable behavioral contract.
- `forge-plan` produces an approved, code-grounded implementation plan made of
  closed execution packets.
- `forge-implement` executes approved packets, prevents common quality defects,
  verifies the integrated result, and produces a compact handoff.

Refactor the corresponding Brain skills into thin adapters that supply Brain
Payroll, issue-source, knowledge-provider, artifact, validation, and delivery
specialization. A user invocation of a Brain skill authorizes it to use its
matching Forge core. Workflow stages continue automatically only when the
user's expressed intent authorizes continuation; otherwise they stop at the
stage boundary.

Forge uses shared, approval-bound artifacts to carry knowledge forward. It
automatically inspects existing issue fields, comments, BA output, artifacts,
and conversation context before asking questions. It loads only applicable
leaf knowledge, applies narrow prevention checks during implementation, runs
integrated deterministic verification, and performs one final semantic review.

## User Stories

1. As a developer, I want to invoke each Forge stage explicitly, so that the agent does not enter an SDLC workflow unexpectedly.
2. As a developer, I want a full-workflow request to continue across stages, so that I do not need to invoke every stage manually.
3. As a developer, I want a stage-only request to stop at that boundary, so that I retain control over progression.
4. As a Brain developer, I want Brain skills to use Forge cores, so that portable behavior has one source of truth.
5. As a Brain developer, I want Brain-specific Jira, OKF, and delivery behavior preserved in adapters, so that portability does not remove project capability.
6. As a user of another project, I want Forge to work without Brain, Jira, or OKF, so that the suite is genuinely reusable.
7. As a user on any compatible harness, I want Forge to avoid named models, agents, servers, hooks, and invocation syntax, so that core correctness is harness-agnostic.
8. As a product owner, I want previously answered BA questions reused automatically, so that Discovery does not ask me the same thing again.
9. As a product owner, I want only unanswered, conflicting, stale, or newly exposed decisions raised, so that clarification is relevant.
10. As a product owner, I want independent questions grouped into one round, so that clarification is efficient.
11. As a developer, I want evidence-answerable questions researched instead of sent to me, so that I answer only genuine human decisions.
12. As a developer, I want settled decisions reopened only with cited contradictory evidence, staleness, or scope change, so that decisions remain stable.
13. As a developer, I want current issue fields and clarification replies considered together, so that Discovery sees the latest requirements.
14. As a developer, I want all materially populated accessible issue fields considered, so that custom-field information is not missed.
15. As a developer, I want paginated comments, attachments, linked items, subtasks, parent relationships, dependencies, and history considered where available, so that issue context is complete.
16. As a security-conscious user, I want only materially used issue content persisted by default, so that raw payload size and PII exposure are limited.
17. As a product owner, I want requirement-changing history treated as supporting evidence requiring confirmation, so that old edits do not silently override current intent.
18. As a developer, I want Discovery to identify affected actors, states, parallel paths, exclusions, unassigned cohorts, permissions, integrations, and regressions, so that functional impact is complete.
19. As a developer, I want missing screenshots or visual references checked only for relevant UI work, so that unrelated work is not burdened.
20. As a developer, I want missing visual references reported as warnings and risks rather than automatic blockers, so that work can proceed deliberately.
21. As a developer, I want existing system behavior used as a reference when appropriate, so that changes remain consistent.
22. As a developer, I want Specification to preserve discovery decisions and requirement identities, so that intent is traceable.
23. As a product owner, I want Specification to define actors, states, inputs, outputs, permissions, errors, boundaries, and changed and unchanged behavior, so that expected behavior is unambiguous.
24. As a tester, I want acceptance scenarios, edge cases, invariants, constraints, and success criteria, so that behavior is objectively verifiable.
25. As a planner, I want Specification free of unresolved product decisions and non-binding technical design, so that planning does not reinterpret requirements.
26. As a developer, I want natural language such as "proceed" to approve an unambiguous presented revision, so that approval does not require commands or nonces.
27. As a developer, I want approval tied to normalized artifact content, so that meaningful changes invalidate stale approval.
28. As a developer, I want line endings, trailing spaces, and repeated blank lines ignored during approval hashing, so that formatting noise does not invalidate approval.
29. As a developer, I want meaningful indentation and fenced-code whitespace preserved during hashing, so that semantic code changes invalidate approval.
30. As a workhorse implementer, I want exact files, symbols, operations, patterns, interfaces, dependencies, and ordered steps, so that I can implement without rediscovery.
31. As a workhorse implementer, I want required edge behavior, must-not-change boundaries, checks, expected results, and acceptance evidence in each task packet, so that I do not invent missing decisions.
32. As a developer, I want plans to include signatures, schemas, pseudocode, or code sketches only when they freeze a meaningful decision, so that plans are precise without pre-writing the implementation.
33. As a developer, I want optional architecture design when integration, security, migration, compatibility, or hard trade-offs justify it, so that complex plans remain readable.
34. As a maintainer, I want ADRs only for durable, surprising, hard-to-reverse trade-offs, so that architectural history remains useful rather than noisy.
35. As an implementer, I want to choose review-first, per-task, or end-only commit behavior once at implementation start, so that Git behavior matches my workflow.
36. As an implementer, I want unrelated working-tree changes excluded, so that Forge never commits or modifies user work outside approved scope.
37. As an implementer, I want narrow tests and quality checks after each task, so that broken work does not propagate.
38. As a reviewer, I want implementation to proactively check design parity, reusable components and styles, inline styling, duplication, constants, performance, maintainability, security, permissions, and diff scope, so that common review findings are prevented.
39. As a developer, I want quality checks selected from touched concerns, so that unrelated knowledge and checks do not waste tokens.
40. As a developer, I want one integrated deterministic verification stage followed by one final semantic review, so that quality is high without repetitive review cost.
41. As a developer, I want small serial work handled directly and large independent work optionally delegated, so that delegation is beneficial rather than mandatory.
42. As a developer on a limited harness, I want correctness independent of delegation, so that missing subagent support does not break the workflow.
43. As a developer, I want transient retries bounded and deterministic failures retried only after state changes, so that failures do not create loops.
44. As a developer, I want plan contradictions to stop affected and dependent tasks while allowing safe independent work to continue, so that useful progress is preserved.
45. As a developer, I want unplanned scope presented for authorization rather than silently added, so that implementation remains controlled.
46. As a developer, I want unavailable checks recorded as `UNMEASURED` and never represented as passes, so that completion evidence is honest.
47. As a developer, I want knowledge validation problems explained with an option to repair them in the current work item, so that Forge does not silently fix or automatically block.
48. As a developer, I want reruns to resume verified state without duplicate questions, artifacts, commits, or side effects, so that recovery is safe.
49. As a developer, I want a caller-selected work-item directory with a repository-local fallback, so that artifacts are portable and predictably located.
50. As a developer, I want Forge to avoid automatic issue-tracker writes, `.gitignore` edits, commits, pushes, PRs, and squashes without authorization, so that side effects remain explicit.
51. As a developer, I want optional project knowledge routed through a generic provider contract, so that projects can use their own knowledge format.
52. As a Brain developer, I want OKF validated once and routed to leaf knowledge rather than full profiles, so that Brain standards remain available without excessive context.
53. As a developer, I want selected knowledge paths, hashes, and conclusions carried forward, so that later stages reload only stale or newly applicable knowledge.
54. As a maintainer, I want portable static and behavioral evals plus historical Brain regressions, so that improvements do not reintroduce known failures.
55. As a maintainer, I want Forge compared with current Brain behavior and a no-skill baseline, so that utility and token cost are measured rather than assumed.
56. As a maintainer, I want host and model trials reported separately from portable validation, so that unavailable coverage is not overclaimed.

## Implementation Decisions

- The suite consists of five separate stage skills because each stage has a
  distinct user intent, artifact boundary, completion condition, and context
  surface.
- All Forge and Brain skills are user-invoked. Brain adapters may load their
  matching Forge core after user invocation.
- Intent-based chaining is used: explicit full-workflow intent or an
  unambiguous continuation authorizes the next stage; otherwise the stage
  stops.
- Forge cores use only standard skill documents and relative resources.
  Harness-specific bindings are optional adapters and cannot be correctness
  dependencies.
- `forge-clarify` owns human decisions; `forge-discover` owns evidence and
  impact analysis. Discovery invokes clarification only for a real unresolved
  decision frontier.
- Question suppression is context-aware and automatic. Semantic equivalence is
  agent judgement; stable generated decision identities support persistence
  and reruns without becoming a manually maintained suppression list.
- Issue acquisition uses field metadata and populated-field presence to fetch
  materially populated content. Raw all-field payloads are not inserted into
  active context.
- The shared artifact set is `context.md`, `decisions.md`, `spec.md`, optional
  `design.md`, `plan.md`, `tasks.md`, `evidence.md`, and machine-readable
  workflow state.
- An explicit work-item directory wins. The fallback is a repository-local
  `.forge/work-items/<stable-id-or-deterministic-slug>/` directory.
- Workflow state records approvals, normalized hashes, stage status, source
  freshness, and selected knowledge paths and hashes.
- Approval uses natural language when the pending revision is unambiguous.
  Normalized hashes ignore non-semantic Markdown whitespace while preserving
  meaningful indentation and fenced-code whitespace.
- Specification owns observable behavior and planability. It does not own
  implementation design.
- Planning produces dependency-ordered closed execution packets. A packet is
  ready only when a competent workhorse can implement it from the packet and
  cited local material without research, architecture selection, or questions.
- Optional design documents are used for cross-system integration,
  security-sensitive architecture, migration, material compatibility
  contracts, hard-to-reverse trade-offs, or complexity that would make the
  execution plan unreadable.
- ADRs use the project's convention, with a documentation ADR directory as the
  fallback, and are created only when the agreed three-part threshold is met.
- Implementation asks once for `review-first`, `per-task`, or `end-only`
  commit behavior. It never automatically squashes, pushes, or opens a PR.
- Per-task validation is narrow and applicable. Full deterministic verification
  occurs after integration, followed by one semantic review and bounded
  remediation.
- Delegation is capability-sensitive and optional. Correctness must not depend
  on a particular model, agent type, or harness feature.
- A generic optional knowledge-provider contract separates portable workflow
  behavior from project knowledge formats. The Brain adapter supplies OKF.
- Knowledge validation failures do not cause automatic repair or automatic
  blocking. The user receives the exact impact and chooses whether repair is
  added to the current work item.
- Brain BA and MR Review packages are reference evidence and remain unchanged.
  MR Review feedback informs Forge implementation prevention checks but does
  not add a new review skill.

## Testing Decisions

- Tests should assert externally observable artifacts, state, questions,
  mutations, and verification results rather than exact reasoning traces or
  prose wording.
- The highest behavioral seam is a Forge stage receiving fixture inputs and
  producing expected artifacts and workflow state. This is the primary seam
  for clarification, discovery, specification, planning, and implementation.
- A Brain adapter integration seam replays historical issue, BA, knowledge, and
  project fixtures through Forge-backed Brain workflows. It verifies preserved
  Brain behavior and the absence of duplicate portable logic.
- A deterministic seam covers normalization, hashing, approval state,
  freshness, knowledge routing, package structure, reference reachability, and
  eval-schema validation.
- Automatic question suppression tests provide semantically equivalent answers
  across issue fields, comments, BA output, artifacts, and conversation context
  and verify that no repeated question is asked.
- Discovery tests include materially populated custom fields, paginated
  comments, inaccessible sources, linked work, excluded and unassigned cohorts,
  parallel behavior, and conditional visual-reference warnings.
- Specification tests verify both directions of requirement coverage,
  changed/unchanged behavior, invariants, edge cases, constraints, acceptance
  scenarios, traceability, and absence of unresolved questions or design
  leakage.
- Planning tests include small and multi-system fixtures. They verify blind
  workhorse readiness, necessary code-detail decisions, avoidance of copied
  boilerplate, task dependency order, scope boundaries, exact checks, and
  developer-verifiable acceptance.
- Implementation tests cover all commit modes, dirty-tree isolation,
  idempotent resume, design parity, component/style reuse, inline CSS,
  duplication, constants, performance, maintainability, security, plan
  contradictions, retries, unavailable capabilities, and final review flow.
- Differential tests compare Forge-backed behavior with preserved Brain
  behavior and a no-skill baseline. Correctness is evaluated before tokens,
  duration, tool calls, references loaded, retries, and questions asked.
- Host/model trials are reported separately. Missing capabilities, competitors,
  or runners are `UNMEASURED`, not passes.
- Existing repository package validation is extended rather than replaced, and
  existing test seams are preferred over introducing a separate evaluation
  framework.

## Out of Scope

- Changing the existing BA skill.
- Changing the existing MR Review skill or creating a replacement review skill.
- Automatically publishing Forge artifacts to Jira or another issue tracker.
- Requiring OKF in projects that do not use it.
- Requiring a specific harness, model, subagent system, MCP server, hook, shell,
  or interpreter for core workflow correctness.
- Automatically fixing unrelated knowledge-bundle, repository, or baseline
  defects.
- Automatically editing `.gitignore`, committing, squashing, pushing, opening
  pull requests, or merging without the required user authorization.
- Treating every missing screenshot or visual sample as a blocker.
- Copying entire project knowledge profiles into Forge context.
- Moving technical implementation decisions into the behavioral specification.
- Pre-writing complete implementations inside plans when a concise contract or
  sketch is sufficient.

## Further Notes

- The existing OKF bundle currently passes its deterministic validator. Forge
  still needs failure behavior because future broken links, metadata, encoding,
  navigation, or root structure could reduce knowledge coverage.
- The canonical portable source belongs in this plugin's authored skill tree.
  Brain installations should consume verified copies rather than becoming a
  second independently authored source.
- The design and implementation plan already present under the documentation
  area are separate untracked artifacts and should not be overwritten without
  explicit scope.
- Issue-tracker publication and the `ready-for-agent` label could not be
  performed because no project issue-tracker configuration or triage vocabulary
  was supplied.
