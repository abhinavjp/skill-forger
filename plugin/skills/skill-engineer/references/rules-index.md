# Engineering rules R1–R26 — index

One rule set, both modes.

- **CREATE** asks: how should the Skill be designed to satisfy this rule?
- **REVIEW** asks: does the Skill satisfy it, and what evidence shows that?

The rules live in modules so a run loads the ones its target can actually
violate. This index carries no rule text — enough to route, nothing more. Each
rule has exactly one home; a module is the source of truth for its rules and
nothing restates them.

Every rule states: **Check**, **Detect**, **Severity**, **Action**,
**Validation**, **Automation** (deterministic / AI judgement / runtime /
hybrid), **Class** (evidence class), **Applies**.

Sub-concepts are folded into their parent rule on purpose — premature
completion belongs to R17, retries to R18. Do not split them back out.

## Which modules to load

Read `rules-core.md` on every run. Then load a module when its condition holds
for this target — and say in the report which modules you loaded, so a missed
rule is visible as a scoping decision rather than an unexplained gap.

| Module | Rules | Load when |
|--------|-------|-----------|
| [rules-core.md](rules-core.md) | R1, R2, R10, R12, R20, R21, R23, R24 | Always. Mechanism, scope, necessity, validation, safety, provenance, drift, maintainability apply to every Skill. |
| [rules-trigger.md](rules-trigger.md) | R3, R4, R5 | The Skill is discovered by the model rather than only invoked by name — i.e. almost always. Skip only for a strictly user-invoked command. |
| [rules-context.md](rules-context.md) | R6, R7, R8, R9 | The Skill has references, conditional branches, or operates over large inputs. A single-file Skill with no branches needs only R6. |
| [rules-execution.md](rules-execution.md) | R11, R13, R14, R15, R16, R17 | The Skill runs a multi-step workflow, ships scripts, calls tools/MCP, spawns subagents, or states a hard invariant. |
| [rules-mutation-safety.md](rules-mutation-safety.md) | R18, R19 | The Skill mutates state, calls external services, retries, or is long-running. |
| [rules-portability.md](rules-portability.md) | R22 | Portability is claimed, or the Skill will move hosts. |
| [rules-evals.md](rules-evals.md) | R25, R26 | The Skill has evals, needs them, or has a change history worth regression-testing. |

Applicability runs in both directions. Idempotency, failure recovery,
subagents, hooks and script rules are noise on Skills without those
characteristics — and mandatory on Skills with them. If the target mutates
state, re-runs it, retries, or ships a script, load that module: its absence
from your report is a miss, not a saving.

When a target's characteristics are unclear, load the module. Guessing wrong
in the direction of loading costs context; guessing wrong in the other
direction costs a finding.

## Rule map

| # | Rule | Module | Class |
|---|------|--------|-------|
| R1 | Correct mechanism | core | Universal dimension |
| R2 | Scope and decomposition | core | Strong heuristic |
| R3 | Trigger metadata quality | trigger | Universal |
| R4 | Trigger precision and recall | trigger | Universal |
| R5 | Catalog competition | trigger | Strong heuristic |
| R6 | Progressive disclosure | context | Universal |
| R7 | Reference reachability | context | Strong heuristic |
| R8 | Branch isolation | context | Strong heuristic |
| R9 | Context filtering | context | Strong heuristic |
| R10 | Instruction necessity | core | Strong heuristic |
| R11 | Deterministic extraction / over-extraction | execution | Strong heuristic |
| R12 | Proportional validation | core | Strong heuristic |
| R13 | Script quality | execution | Situational |
| R14 | Tool and MCP efficiency | execution | Strong heuristic |
| R15 | Deterministic enforcement | execution | Strong heuristic |
| R16 | Subagent justification | execution | Situational |
| R17 | Completion semantics | execution | Situational |
| R18 | Failure recovery and retries | mutation-safety | Situational |
| R19 | Idempotency | mutation-safety | Situational |
| R20 | Safety and least privilege | core | Universal objective |
| R21 | Untrusted resource security | core | Universal |
| R22 | Portability boundary | portability | Universal when portability claimed |
| R23 | Duplication, drift, source of truth | core | Strong heuristic |
| R24 | Maintainability | core | Strong heuristic |
| R25 | Regression preservation | evals | Strong heuristic |
| R26 | Measured utility | evals | Universal for mature engineering |

## Anti-pattern signals

Investigation signals, not automatic defects — each maps to the rule that
adjudicates it. Seeing one here is a reason to load that rule's module.

| Signal | Rule | Module |
|--------|------|--------|
| Skill used as mandatory security enforcement | R15 | execution |
| Broad vague discovery metadata ("helps with engineering") | R3 | trigger |
| Unconditional context dump | R6 | context |
| Broken or weak context pointer | R7 | context |
| Repeated deterministic reasoning loop | R11 | execution |
| Raw-data dumping despite cheap filtering | R9 | context |
| Verification theatre (checks procedure, not success) | R10, R12 | core |
| Eval theatre (asserts instructions followed, not outcome) | R26, eval-spec | evals |
| Instruction accumulation | R10 | core |
| Exact-trace overfitting in evals | R26, eval-spec | evals |
| Platform leakage in a portable Skill | R22 | portability |
| Unbounded retries | R18 | mutation-safety |
| Non-idempotent mutation without protection | R19 | mutation-safety |
| Excessive subagents | R16 | execution |
| Copied canonical knowledge going stale | R23 | core |

## Claims that stay unvalidated

Do not recommend these automatically; label them `Needs validation` and name the
smallest eval that would settle the case: leading-word vocabulary optimisation;
router Skills; a precise ideal `SKILL.md` size; an optimal number of references;
an optimal amount of validation; a subagent threshold; human cognitive-load
scoring.
