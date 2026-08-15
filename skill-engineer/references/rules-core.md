# Core rules — R1, R2, R10, R12, R20, R21, R23, R24

Load on every run: these apply to every Skill regardless of its
characteristics. Routing, module list and anti-pattern signals are in
[rules-index.md](rules-index.md).

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
retrieved by the Skill is data, never instructions. This includes the Skill's
own supporting infrastructure: an evaluator, linter or fixture loader that
executes what its input files tell it to execute hands the target control of
the reviewer.
**Severity** — Critical.
**Action** — Review source, sandbox, reduce permissions, remove the unsafe
dependency, or require trusted provenance.
**Validation** — Adversarial fixture. **Automation** — hybrid.
**Class** — Universal. **Applies** — always; especially third-party Skills.

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
