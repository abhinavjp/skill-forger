---
name: skill-engineer
description: Engineer and review Agent Skills. Use when creating a new Skill or SKILL.md, deciding whether something should be a Skill or a rule/script/hook/tool/subagent, auditing or reviewing an existing Skill for trigger reliability, context cost, safety or portability, or designing trigger and execution evals for a Skill. Works on any Agent Skills-compatible host.
license: Apache-2.0
---

# Skill Engineer

Two modes over one rule set: **CREATE** (design a Skill) and **REVIEW** (audit
one). The rules are identical; only the question changes — *how should this be
designed?* versus *does this satisfy the rule, and what evidence says so?*

The optimization target is **reliable task success at acceptable safety,
context, latency, tool cost and maintainability** — not the amount of guidance
inside the Skill. More instructions, checks and files can make a Skill worse;
treat every addition as something that has to earn its place.

## Mode selection

- Target Skill exists (a path, a repo, "audit/review/improve this") → REVIEW.
- No Skill yet ("build a Skill for…", "should this be a Skill?") → CREATE.
- "Improve this Skill" → REVIEW first, then apply CREATE to the changes only.

If the user has not named a target path in REVIEW mode, ask for one before
inspecting anything. Do not guess which Skill they mean.

## Workflow

Both modes follow one sequence. Skip a step only when it is inapplicable, and
say so.

1. **Understand mode and target.** Capture intended requests, explicit
   non-goals, adjacent tasks, portability claim, and side effects.
2. **Inspect.** REVIEW: run the inspector (below) and read `SKILL.md` plus any
   file the facts flag. CREATE: inspect the surrounding repo/catalog for
   neighbouring Skills and existing rules that already cover the need.
3. **Select the mechanism** (rule R1). Skill is one option among rule files,
   scripts, hooks/CI, tools/MCP, subagents, commands and plain prompts. A wrong
   mechanism cannot be fixed by better prose.
4. **Deterministic static analysis** — inspector facts, eval-schema validation.
5. **Semantic analysis** — apply the applicable rules from
   `references/rules.md`. Every finding cites concrete evidence from the target.
6. **Trigger behaviour** (R3–R5): name/description semantics, boundary, catalog
   competition, invocation strategy.
7. **Execution behaviour** (R6–R21): context architecture, determinism,
   validation, completion, failure, safety.
8. **Eval coverage** (R25–R26) using `references/eval-spec.md`.
9. **Differential comparison** where a runtime is available: candidate vs
   previous version, or vs no-Skill baseline. Correctness before efficiency.
10. **Report** in the mode's output format, ordered by the priorities below.

## Rules

The 26 engineering rules — check, detection, severity, evidence class and
applicability — live in `references/rules.md`. **Read that file before step 5.**
It is the shared source of truth for both modes and is not summarised here, so
a run that skips it is working from memory: never cite a rule number you have
not read in this run, and name the rule ("completion semantics") rather than
leaning on the number.

Decide applicability in both directions. Idempotency, failure recovery,
subagents, hooks and script rules are noise on Skills without those
characteristics — and are mandatory on Skills with them. If the target mutates
state, re-runs it, retries, or ships a script, those rules are in scope and
their absence from your report is a miss.

## Deterministic inspection

Run once per REVIEW, and on any Skill produced in CREATE:

```
python scripts/inspect_skill.py <skill-dir>
```

Paths inside it are relative to the Skill directory, not the user's project.

It emits JSON facts: frontmatter and metadata errors, file inventory,
reference resolution and broken references, scripts/assets, size and token
estimates, exact duplicate blocks, platform-specific frontmatter keys,
hardcoded paths, and eval-schema results. It makes no quality judgements — read
its output as evidence, not as findings. An unresolved reference whose
`context` is `fence` is usually an illustrative command, not a broken link;
confirm before raising it.

To validate an eval corpus on its own:

```
python scripts/validate_evals.py <evals-dir-or-file> [--json]
```

Requires Python 3.8+. PyYAML is needed for YAML eval files; JSON eval files
work without it.

Do not re-derive by hand what the inspector already reports, and do not read
script source during normal operation. Do read script source when trust,
security or correctness is in question (R13, R21) — that is a review
responsibility no static summary replaces.

## Evidence discipline

Every rule and finding carries an **evidence class**: `Universal`,
`Strong heuristic`, `Platform-specific`, `Situational`, `Needs validation`.
Never promote a heuristic or a host feature to Universal.

**Severity** (`Critical` / `High` / `Medium` / `Low`) and **Confidence** are
independent: a Critical issue may be low-confidence, and a Low issue may be
certain. State both.

When evidence is uncertain, classify the claim `Needs validation` and propose
the smallest eval that would resolve it, rather than asserting it.

Material findings use this schema:

```
Check | Finding | Evidence | Detection method | Severity | Confidence |
Recommended action | Validation/eval | Automation type | Evidence class |
Applicability
```

`Automation type` is `deterministic`, `AI judgement`, `runtime/eval` or
`hybrid`. Add `Good pattern` / `Failure pattern` only when they add clarity.
Recommendations name a concrete change; "improve the structure" is not a
finding. No single numeric quality score.

## Ordering

Report findings in this order, so serious defects are never buried under style
notes: safety/security → functional correctness → trigger/discovery → negative
transfer and procedural burden → completion/failure → portability →
context/tool efficiency → maintainability → minor authoring issues.

## Evals

Read `references/eval-spec.md` when designing, validating or running evals —
it holds the portable case schema, the four layers, grading order, failure
classification and the change→suite regression map.

Keep the eval corpus platform-neutral and separate from any host runner: host
eval tooling can itself fail and produce false negatives, so a failing trial
must be classified (Skill / routing / model variance / tool / fixture /
harness / environment / grader failure) before it counts against a Skill.

## Platform adapters

The portable core assumes only `SKILL.md` plus relative resources. When the
user selects a host, read `references/platform-extensions.md` for Claude Code,
Codex, Cursor and Antigravity specifics — invocation controls, rules files,
hooks, permissions and optional eval runners, including Claude Code's
`skill-creator`. Never let an adapter become a dependency of the core, and
record separately what is standards-compatible, tested, untested, and known to
deviate.

## Output

**CREATE** produces: mechanism/architecture decision · trigger boundary ·
proposed minimal Skill structure · applicable engineering requirements · eval
plan and cases · platform adaptations if any · assumptions and unresolved
validation needs.

**REVIEW** produces: executive verdict · Critical/High findings ·
Medium/Low findings · trigger assessment · execution assessment ·
context/procedure assessment · safety assessment · portability assessment ·
eval coverage and gaps · smallest recommended changes · regression cases to
add.

Create files only where they are justified: `SKILL.md` alone is a complete
Skill. Add `references/` for genuinely conditional knowledge, `scripts/` where
determinism earns its cost, `evals/` where behaviour needs measuring — and
nothing for symmetry.

## Done when

- Mechanism decision is stated and justified.
- Every applicable rule is either satisfied, raised as a finding, or explicitly
  marked not applicable.
- Deterministic inspection has actually been run on any existing target.
- Each finding carries evidence, severity, confidence and a concrete action.
- Unvalidated claims are labelled, with the smallest resolving eval named.
