# Context rules — R6, R7, R8, R9

Load when the Skill has references, conditional branches, or operates over
large inputs. A single-file Skill with no branches needs only R6. Index:
[rules-index.md](rules-index.md).

## R6. Progressive disclosure

**Check** — Is information loaded at the lowest level needed for the current
branch? The chain is `name + description` → `SKILL.md` → conditional
references/scripts/resources.
**Detect** — Inspect always-loaded instructions, map branch-specific content,
inspect which references eval traces actually load. `SKILL.md` under ~500 lines
/ ~5k tokens is a **budget heuristic, not a correctness threshold**. A small
reference read by a minority of runs can still beat inlining it, which charges
every run for knowledge most runs never use — compare loaded cost against
inlined cost rather than counting files.
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
chains, evals where a required resource never loads. Markdown links resolve
relative to the document containing them; a link that only resolves from the
package root is broken even where a same-named file exists there.
**Severity** — High when an unloaded reference affects correctness; Low when the
target is decorative and no workflow step reads it. Severity here follows
execution impact, not the fact of breakage.
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
**Detect** — Compare consumed evidence against raw input size. A reduction that
discards provenance is not a reduction, it is a guess generator: what survives
must still be citable.
**Severity** — High for large-input Skills.
**Action** — Add retrieval/filter/extraction that preserves provenance.
**Validation** — Correctness before/after, context reduction, missed-evidence
tests. **Automation** — hybrid. **Class** — Strong heuristic. **Applies** —
Skills over large inputs.
