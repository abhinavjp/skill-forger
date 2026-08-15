# Engineering rules R1–R26

One rule set, both modes.

- **CREATE** asks: how should the Skill be designed to satisfy this rule?
- **REVIEW** asks: does the Skill satisfy it, and what evidence shows that?

Each rule states: **Check**, **Detect**, **Severity**, **Action**,
**Validation**, **Automation** (deterministic / AI judgement / runtime / hybrid),
**Class** (evidence class), **Applies**.

Sub-concepts are folded into their parent rule on purpose — premature
completion belongs to R17, retries to R18. Do not split them back out.

## Contents

| # | Rule | Class |
|---|------|-------|
| R1 | Correct mechanism | Universal dimension |
| R2 | Scope and decomposition | Strong heuristic |
| R3 | Trigger metadata quality | Universal |
| R4 | Trigger precision and recall | Universal |
| R5 | Catalog competition | Strong heuristic |
| R6 | Progressive disclosure | Universal |
| R7 | Reference reachability | Strong heuristic |
| R8 | Branch isolation | Strong heuristic |
| R9 | Context filtering | Strong heuristic |
| R10 | Instruction necessity | Strong heuristic |
| R11 | Deterministic extraction / over-extraction | Strong heuristic |
| R12 | Proportional validation | Strong heuristic |
| R13 | Script quality | Situational |
| R14 | Tool and MCP efficiency | Strong heuristic |
| R15 | Deterministic enforcement | Strong heuristic |
| R16 | Subagent justification | Situational |
| R17 | Completion semantics | Situational |
| R18 | Failure recovery and retries | Situational |
| R19 | Idempotency | Situational |
| R20 | Safety and least privilege | Universal objective |
| R21 | Untrusted resource security | Universal |
| R22 | Portability boundary | Universal when portability claimed |
| R23 | Duplication, drift, source of truth | Strong heuristic |
| R24 | Maintainability | Strong heuristic |
| R25 | Regression preservation | Strong heuristic |
| R26 | Measured utility | Universal for mature engineering |

---

## R1. Correct mechanism

**Check** — Is each responsibility carried by the right mechanism?

Options and their default fit:

| Need | Default mechanism | Class |
|------|-------------------|-------|
| Reusable specialised workflow for relevant tasks only | Skill | Universal concept |
| Persistent project guidance applying to every task | Rule file (`AGENTS.md` / `CLAUDE.md`) | Strong heuristic |
| Exact repeatable operation | Script/code | Strong heuristic |
| Requirement enforced regardless of model compliance | Hook / validator / CI / permissions | Strong heuristic |
| External data or action | MCP / tool / API | Universal concept |
| Independent context-heavy bounded task | Subagent | Situational |
| Fixed user-invoked sequence | Workflow / command | Situational, platform-specific |
| One-off instruction | Prompt | Strong heuristic |

**Detect** — Requirements that apply to *every* task (→ rule file); exact
repeatable logic (→ script); external capability (→ tool); mandatory
security/compliance controls (→ hook/permission); independent parallel work
(→ subagent).
**Severity** — Critical if the wrong mechanism creates a safety failure; High if
it materially harms correctness; Medium otherwise.
**Action** — Move only the misplaced responsibility. Do not restructure the rest.
**Validation** — Before/after behaviour comparison where consequential.
**Automation** — AI judgement. **Class** — Universal review dimension; the
specific mechanisms available are platform-specific. **Applies** — always.

## R2. Scope and decomposition

**Check** — Unrelated capabilities bundled together, or one coherent capability
over-fragmented?
**Detect** — Compare branches across trigger surface, workflow, dependencies,
references and expected outputs. Splitting costs discovery entries, overlapping
descriptions, duplicated guidance and catalog pressure.
**Severity** — High when routing ambiguity or irrelevant context causes
failures; otherwise Medium.
**Action** — Split materially independent capabilities; keep related branches
together behind conditional disclosure.
**Validation** — Trigger tests with neighbouring Skills; execution tests per
branch. **Automation** — AI judgement. **Class** — Strong heuristic.
**Applies** — always.

## R3. Trigger metadata quality

**Check** — Do `name` + `description` communicate what the Skill does and when
it is relevant? Treat them together as the portable routing interface; the
description alone does not determine activation.
**Detect** — Semantic specificity; representative user wording; adjacent tasks;
important synonyms and paraphrases. Trigger-critical meaning belongs early —
some hosts truncate catalog metadata (Strong heuristic). Do not chase "magic"
leading words: distinctive vocabulary is fine when natural, but a wording change
justified only by word order is **Needs validation** until A/B trigger evidence
exists.
**Invocation strategy** — Decide, and state, whether the Skill should be
model/agent invoked, explicitly user invoked, or both where the host supports
it. Weigh automatic discoverability against persistent catalog/context cost,
routing uncertainty and the user's cognitive burden of remembering it exists.
The mechanics are Platform-specific; the trade-off is a Strong heuristic. Token
cost alone is not a reason to make a Skill manual — recommend a change of
invocation mode only with evidence that the trade is beneficial.

**Severity** — Critical for implicitly activated Skills whose routing materially
fails.
**Action** — State the capability, include real trigger concepts, communicate
boundaries, delete generic language.
**Validation** — Positive/negative/boundary trigger suite.
**Automation** — hybrid. **Class** — Universal. **Applies** — always.

## R4. Trigger precision and recall

**Check** — Does it activate when intended and stay inactive when not?
**Detect** — Positive, negative, paraphrase, boundary, near-neighbour,
adversarial and competing-Skill queries. Keep explicit invocation out of implicit
precision/recall measurement.
**Severity** — High, Critical when misrouting reaches a dangerous capability.
**Action** — Change routing metadata or the Skill boundary, not the body.
**Validation** — Re-run the trigger suite across multiple trials where model
variance matters. **Automation** — runtime/eval. **Class** — Universal.
**Applies** — implicitly discovered Skills.

## R5. Catalog competition

**Check** — Does routing survive with realistic neighbouring Skills installed?
**Detect** — Test in isolation, in a realistic catalog, and in a high-overlap
catalog where relevant.
**Severity** — High where real deployments carry substantial competition.
**Action** — Differentiate descriptions, consolidate redundant Skills, or change
invocation strategy where the host supports it.
**Validation** — Catalog-aware trigger eval. **Automation** — runtime/eval.
**Class** — Strong heuristic; exact catalog behaviour is platform-specific.
**Applies** — when a catalog exists.

## R6. Progressive disclosure

**Check** — Is information loaded at the lowest level needed for the current
branch? The chain is `name + description` → `SKILL.md` → conditional
references/scripts/resources.
**Detect** — Inspect always-loaded instructions, map branch-specific content,
inspect which references eval traces actually load. `SKILL.md` under ~500 lines
/ ~5k tokens is a **budget heuristic, not a correctness threshold**.
**Severity** — High when excess context measurably harms performance; otherwise
Medium.
**Action** — Keep core instructions in `SKILL.md`, defer conditional detail,
delete always-loaded content nothing needs.
**Validation** — Compare token/context use and confirm correctness does not
regress. **Automation** — hybrid. **Class** — Universal for standard-compatible
hosts. **Applies** — always.

## R7. Reference reachability

**Check** — Can the agent reliably tell when a deferred reference is needed?
**Detect** — Broken paths (deterministic), vague pointers, deep reference
chains, evals where a required resource never loads.
**Severity** — High when an unloaded reference affects correctness.
**Action** — Give each pointer an explicit condition — "If authentication code
changed, read `references/<that-topic>.md`" — not "see references for more".
**Validation** — Cases that exercise that branch. **Automation** — hybrid.
**Class** — Strong heuristic. **Applies** — Skills with references.

## R8. Branch isolation

**Check** — Do materially different branches load only their own knowledge?
**Detect** — Build a branch→reference map; look for resource loads a branch
never needs; compare branch traces.
**Future-stage visibility** (Situational) — Where a multi-stage workflow keeps
underperforming on an early stage because the agent is racing toward a visible
later goal, evaluate whether hiding the later stage improves the earlier one.
Mechanisms: conditional disclosure, separate invocation, an isolated
subagent/context, or a separate Skill where genuinely justified. Structure alone
never justifies the split — require differential eval evidence of better
current-stage quality or effort first. Completion effects of the same problem
belong to R17.

**Severity** — Medium/High. **Action** — Route first, then load.
**Validation** — Context and execution comparison per branch.
**Automation** — hybrid. **Class** — Strong heuristic. **Applies** —
multi-branch Skills.

## R9. Context filtering

**Check** — Could raw inputs be reduced before reasoning without losing needed
evidence? (Changed files not whole repo; relevant log clusters not full logs;
schema subset not whole catalog; search hits plus context not whole documents.)
**Detect** — Compare consumed evidence against raw input size.
**Severity** — High for large-input Skills.
**Action** — Add retrieval/filter/extraction that preserves provenance.
**Validation** — Correctness before/after, context reduction, missed-evidence
tests. **Automation** — hybrid. **Class** — Strong heuristic. **Applies** —
Skills over large inputs.

## R10. Instruction necessity and procedural burden

**Check** — Does each substantial instruction address an observed or credible
failure mode?
**Detect** — Generic no-ops ("think carefully", "be accurate", "use good
practices") are removal *candidates*, not automatic defects; duplicated
constraints; expensive procedural rules; verification theatre that measures
procedure rather than outcome. Where impact is uncertain, ablate.
**Severity** — Medium; High where unnecessary procedure causes a measurable
regression (negative transfer).
**Action** — Remove, weaken, or make conditional. Prefer fixing the root cause
over appending another paragraph.
**Validation** — With-instruction vs without-instruction comparison.
**Automation** — hybrid. **Class** — Strong heuristic. **Applies** — always.

## R11. Deterministic extraction and over-extraction

**Check** — Two failure directions. Is the model repeatedly doing mechanically
reproducible work? *And* has flexible reasoning been frozen into an
unnecessarily rigid pipeline?
Prefer determinism when the operation is precisely specifiable, repeatable,
mechanically checkable, frequent, and where model reasoning adds little. Prefer
reasoning when ambiguity, competing objectives, semantics or highly variable
inputs dominate.
**Detect** — Extraction: repeated parsing, filtering, exact sorting, static
inventory, repeated deterministic shell loops. Over-extraction: mandatory
scripts for low-risk work, full validation on trivial requests, complex pipeline
on simple requests.
**Severity** — Medium/High either way.
**Action** — Extract only the stable deterministic portion; return non-critical
decisions to the agent or make gates conditional.
**Validation** — Differential eval against the simpler version, comparing
correctness, context, latency and maintenance cost.
**Automation** — hybrid. **Class** — Strong heuristic. **Applies** — always.

## R12. Proportional validation

**Check** — Is probabilistic work validated where failure matters, without
procedure that buys nothing? Use the cheapest validator that materially reduces
the relevant failure risk: generated JSON → schema parser; code edit → targeted
tests; config edit → config parser; migration → migration checker.
**Detect** — Identify outputs with available deterministic validators, assess
failure impact, inspect validation cost.
**Severity** — Critical/High where incorrect output has serious consequence;
Medium otherwise.
**Action** — Add the cheapest adequate validator; remove validation that does
not reduce a real risk.
**Validation** — Measure error reduction against added cost.
**Automation** — hybrid. **Class** — Strong heuristic. **Applies** — always.

## R13. Script quality

**Check** — Does each script have a stable, inspectable execution contract for
its role? Normal execution should not require loading implementation source:
`script --help`, defined inputs, structured output, meaningful exit codes.
**Detect** — Entry point, inputs, outputs, exit/error behaviour, privileges,
network and filesystem operations. In review/security mode, read the source to
establish trust, side effects, correctness and portability.
**Severity** — Critical for unsafe privileged behaviour; High for
correctness-critical instability; Medium otherwise.
**Action** — Stabilise the interface, or delete a script that does not earn its
maintenance cost.
**Validation** — Script tests plus the dependent Skill evals.
**Automation** — hybrid. **Class** — Situational. **Applies** — Skills with
scripts.

## R14. Tool and MCP efficiency

**Check** — Are tool calls broader, more repetitive or more numerous than
needed? Use a tool when external capability or live data is genuinely required;
do not expose every tool "just in case".
**Detect** — Duplicate searches, repeated metadata discovery, full enumeration
followed immediately by filtering, refetching the same artifact.
**Severity** — Medium; High when cost or latency becomes material.
**Action** — Narrow queries, reuse results, batch where supported, prefilter.
**Validation** — Tool-call count plus correctness comparison.
**Automation** — runtime/eval. **Class** — Strong heuristic. **Applies** —
tool-using Skills.

## R15. Deterministic enforcement

**Check** — Is the Skill asking the model to honour an invariant that must never
be bypassed?
**Detect** — "must always", "must never", security requirements, destructive
action restrictions expressed as prose.
**Severity** — Critical where a bypass causes security or data loss.
**Action** — Move enforcement into a hook, permission, validator or CI gate
where the host allows; keep the explanation in the Skill.
**Validation** — Attempt the violating action in a controlled test.
**Automation** — hybrid. **Class** — Strong heuristic; the enforcement
mechanism is platform-specific. **Applies** — Skills with hard invariants.

## R16. Subagent justification

**Check** — Does delegation return more than it costs? Legitimate reasons:
context isolation, parallel independent work, specialist reasoning, keeping
noisy intermediate data off the main thread.
**Detect** — Task independence, context volume, parallelism potential,
duplicated work, merge/reconciliation cost.
**Severity** — Medium.
**Action** — Single agent for small or serial work; delegate bounded independent
work when it pays.
**Validation** — Delegated vs single-agent success, cost and latency.
**Automation** — hybrid. **Class** — Situational. There is **no validated
universal threshold** for when delegation wins — treat any specific threshold as
Needs validation. **Applies** — Skills that spawn subagents.

## R17. Completion semantics

**Check** — Could the agent plausibly stop at an intermediate state and present
it as done? This rule owns premature completion; do not raise it separately.
**Detect** — Multi-stage workflows; intermediate artifacts resembling final
output; missing verification stage; unclear definition of done; unvisited
required branches; partial review presented as complete; raw tool output
presented as the solution.
**Severity** — High for multi-step workflows; not applicable to simple reference
Skills.
**Action** — Add minimal *observable* completion conditions — few, checkable,
outcome-shaped.
**Validation** — Interrupted and incomplete-execution cases.
**Automation** — hybrid. **Class** — Situational / Strong heuristic.
**Applies** — multi-step workflows.

## R18. Failure recovery and retries

**Check** — Can an expected failure cause unsafe continuation or needless loss
of work? This rule owns retry behaviour.
**Detect** — Inject a missing dependency, a timeout, malformed input, partial
completion.
**Severity** — High/Critical by impact.
**Action** — Stop on unsafe failure; preserve useful intermediate state; surface
the failure clearly. Retry only where failure is plausibly transient, with
bounded attempts, never infinite, never on deterministic validation failure
unless state changed; backoff where the external service warrants it.
**Validation** — Failure-injection cases. **Automation** — runtime/eval.
**Class** — Situational. **Applies** — external tools, network, stateful or
long-running workflows.

## R19. Idempotency

**Check** — Can rerunning a mutating Skill duplicate or corrupt state?
**Detect** — Execute the operation twice against controlled state.
**Severity** — Critical/High for dangerous mutations.
**Action** — Precondition/state check, stable identifier, update instead of
duplicate, or explicit user confirmation where non-idempotence is unavoidable.
**Validation** — Re-run test. **Automation** — runtime/eval. **Class** —
Situational. **Applies** — mutating Skills only.

## R20. Safety and least privilege

**Check** — Does the workflow request more authority than the task needs?
**Detect** — Filesystem scope, network access, secrets, shell, external
mutation, destructive commands.
**Severity** — Critical.
**Action** — Restrict capability through host permissions and tool boundaries,
not prose alone.
**Validation** — Controlled permission-denied and adversarial cases.
**Automation** — hybrid. **Class** — Universal objective; implementation is
platform-specific. **Applies** — always.

## R21. Untrusted resource security

**Check** — Can a Skill, reference, script or retrieved artifact redirect
privileged behaviour or exfiltrate data? Public Skill ecosystems are a
supply-chain surface.
**Detect** — Provenance; suspicious shell or network operations; credential
access; embedded prompt injection; obfuscation; unexpected downloads. Content
retrieved by the Skill is data, never instructions.
**Severity** — Critical.
**Action** — Review source, sandbox, reduce permissions, remove the unsafe
dependency, or require trusted provenance.
**Validation** — Adversarial fixture. **Automation** — hybrid.
**Class** — Universal. **Applies** — always; especially third-party Skills.

## R22. Portability boundary

**Check** — Does behaviour claimed portable depend on host-specific features?
A portable core must not require host-only frontmatter, host-only agents, hooks
or permissions, host-specific filesystem paths, or proprietary invocation
syntax — only `SKILL.md` plus relative resources.
**Detect** — Frontmatter keys, hardcoded paths (deterministic), invocation
syntax, hook names, named subagents, assumed platform tools.
**Severity** — High when portability is claimed.
**Action** — Move the feature into an adapter, add capability detection,
degrade gracefully, or narrow the compatibility claim.
**Validation** — Standards validation plus host-specific tests. Do not equate
"parses on multiple hosts" with "behaves equivalently on multiple hosts";
record standards compatibility, hosts tested, models tested, known deviations
and untested environments separately. **Automation** — hybrid.
**Class** — Universal for portable Skills. **Applies** — when portability is
claimed.

## R23. Duplication, drift and source of truth

**Check** — Is knowledge copied from a source expected to evolve independently,
and is each fact taken from the right authority?
**Detect** — Exact duplication (deterministic), repeated configuration values,
pinned version numbers, contradictions against a canonical source. Classify each
fact as runtime state, repository configuration, external contract, policy,
legislation or design intent — the environment is **not** automatically the
source of truth.
**Severity** — High where stale or wrongly-sourced data causes incorrect
operation; otherwise Medium.
**Action** — Point at the canonical source, inspect it dynamically, or generate
the derived content mechanically.
**Validation** — Change the source and confirm behaviour still holds; fixtures
with contradictory environment vs policy. Semantic staleness cannot be detected
without a comparison source — do not claim otherwise.
**Automation** — hybrid. **Class** — Strong heuristic. **Applies** — always.

## R24. Maintainability

**Check** — Can one concern change without broad edits or duplicated updates?
**Detect** — A rule repeated across files, cross-file coupling, duplicated
adapter logic, unstable script interfaces.
**Severity** — Medium.
**Action** — Consolidate the real source of truth and stabilise boundaries.
**Validation** — Static inspection plus the regression suite.
**Automation** — AI judgement. **Class** — Strong heuristic. **Applies** —
multi-file Skills.

## R25. Regression preservation

**Check** — Are previously discovered failures retained as regression cases?
**Detect** — Compare change history, issues and the eval corpus.
**Severity** — High for mature Skills.
**Action** — Add each historical failure as a minimal reproducible eval case.
**Validation** — The candidate must keep passing it.
**Automation** — hybrid. **Class** — Strong heuristic. **Applies** — Skills with
history.

## R26. Measured utility

**Check** — Is there evidence the Skill improves outcomes over the baseline?
A Skill must not be assumed to improve the base model; procedures and
verification taken to excess cause functional and efficiency regressions
(negative transfer).
**Detect** — Differential evaluation: candidate vs previous accepted version,
and vs no-Skill where informative. Correctness first, then context tokens,
duration, tool calls, retries, errors, references loaded, subagents spawned and
side-effect operations. Never optimise one metric alone.
**Severity** — High when the candidate is materially worse than baseline without
an explicit accepted trade-off.
**Action** — Fix observed failures rather than adding speculative guidance;
accept a regression only as a stated trade-off.
**Validation** — Layer D differential evals with multiple trials where results
are close. **Automation** — runtime/eval. **Class** — Universal for mature
engineering. **Applies** — whenever a runtime is available; otherwise report as
unvalidated.

---

## Anti-pattern signals

Investigation signals, not automatic defects — each maps to the rule that
adjudicates it.

| Signal | Rule |
|--------|------|
| Skill used as mandatory security enforcement | R15 |
| Broad vague discovery metadata ("helps with engineering") | R3 |
| Unconditional context dump | R6 |
| Broken or weak context pointer | R7 |
| Repeated deterministic reasoning loop | R11 |
| Raw-data dumping despite cheap filtering | R9 |
| Verification theatre (checks procedure, not success) | R10, R12 |
| Eval theatre (asserts instructions followed, not outcome) | R26, eval-spec |
| Instruction accumulation | R10 |
| Exact-trace overfitting in evals | R26, eval-spec |
| Platform leakage in a portable Skill | R22 |
| Unbounded retries | R18 |
| Non-idempotent mutation without protection | R19 |
| Excessive subagents | R16 |
| Copied canonical knowledge going stale | R23 |

## Claims that stay unvalidated

Do not recommend these automatically; label them `Needs validation` and name the
smallest eval that would settle the case: leading-word vocabulary optimisation;
router Skills; a precise ideal `SKILL.md` size; an optimal number of references;
an optimal amount of validation; a subagent threshold; human cognitive-load
scoring.
