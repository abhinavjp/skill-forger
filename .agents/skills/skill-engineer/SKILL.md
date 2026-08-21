---
name: skill-engineer
description: Engineer and review Agent Skills. Use when creating a new Skill or SKILL.md, deciding whether something should be a Skill or a rule/script/hook/tool/subagent, auditing or reviewing an existing Skill for trigger reliability, context cost, safety or portability, or designing trigger and execution evals for a Skill. Portable across Agent Skills-compatible hosts; deterministic inspection runs where scripts can, and degrades to a disclosed partial review where they cannot.
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

REVIEW takes its target three ways:

- **A package on disk** — run the deterministic inspection below, then review.
- **Pasted content**, whole or partial — review what you were given. Say which
  package-level checks (reference resolution, inventory, script inspection,
  eval coverage) you could not perform and why. Do not ask for a path first,
  and do not report unperformed checks as clean.
- **Neither a path nor content** — ask which Skill they mean. Do not guess.

## Workflow

Both modes follow one sequence. Skip a step only when it is inapplicable, and
say so.

1. **Understand mode and target.** Capture intended requests, explicit
   non-goals, adjacent tasks, portability claim, and side effects.
2. **Inspect.** REVIEW: run the inspector (below) where the target is on disk
   and the host can run it, and read `SKILL.md` plus any file the facts flag.
   CREATE: inspect the surrounding repo/catalog for neighbouring Skills and
   existing rules that already cover the need.
3. **Select the mechanism** (rule R1). Skill is one option among rule files,
   scripts, hooks/CI, tools/MCP, subagents, commands and plain prompts. A wrong
   mechanism cannot be fixed by better prose.
4. **Deterministic static analysis** — inspector facts, eval-schema validation.
5. **Semantic analysis** — apply the rule modules this target calls for, routed
   by `references/rules-index.md`. Every finding cites concrete evidence from
   the target.
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
applicability — live in `references/`, split into modules by applicability.
**Read `references/rules-index.md` before step 5**, then load
`references/rules-core.md` plus the modules the index routes you to for this
target. They are the shared source of truth for both modes and are not
summarised here, so a run that skips them is working from memory: never cite a
rule number you have not read in this run, and name the rule ("completion
semantics") rather than leaning on the number.

Decide applicability in both directions, and state which modules you loaded. A
module you skip is a scoping decision you own: if the target mutates state,
re-runs it, retries, or ships a script, those rules are in scope and their
absence from your report is a miss. When in doubt, load it.

## Deterministic inspection

Run once per REVIEW of an on-disk package, and on any Skill produced in CREATE:

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

**When the host cannot run it** — no Python, no shell, scripts disabled, or the
target is pasted rather than on disk — do not stop and do not pretend. Perform
the static checks you can make by reading (frontmatter shape and length, link
targets you can see, always-loaded size, duplication, absolute paths,
host-specific keys), then list the checks you could not run and mark them
unvalidated. A partial review that is honest about its scope is the correct
output; a claim that deterministic inspection happened when it did not is a
defect in this Skill, not a detail.

The inspector and the eval runner treat their inputs as data. They execute
nothing a target or an eval corpus supplies — pointing them at a hostile
package is safe by construction, which is the only basis on which a reviewer
can be pointed at untrusted work.

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
- Every applicable rule has been assessed. Coverage is internal: report material
  findings, the satisfied controls that carry the verdict, and one compact line
  for what was out of scope — "mutation, retry and script rules: not applicable,
  read-only single-file Skill". Never a visible entry per irrelevant rule.
- Deterministic inspection has been run wherever the host and target allowed it,
  and its unavailability is disclosed wherever they did not.
- Each finding carries evidence, severity, confidence and a concrete action.
- Unvalidated claims are labelled, with the smallest resolving eval named.

The output is a decision a reader can act on, not a transcript proving the
procedure ran. Ceremony that grows with the rule count and not with the target
is exactly the negative transfer this Skill exists to catch elsewhere.
