# Eval rules — R25, R26

Load when the Skill has evals, needs them, or has a change history worth
regression-testing. The portable case schema, layers, grading order and failure
classification live in [eval-spec.md](eval-spec.md). Index:
[rules-index.md](rules-index.md).

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
side-effect operations. Never optimise one metric alone. Coverage counts as
evidence only where it is balanced: a suite that tests one mode heavily and the
other barely supports a claim about the first mode only.
**Severity** — High when the candidate is materially worse than baseline without
an explicit accepted trade-off.
**Action** — Fix observed failures rather than adding speculative guidance;
accept a regression only as a stated trade-off.
**Validation** — Layer D differential evals with multiple trials where results
are close. **Automation** — runtime/eval. **Class** — Universal for mature
engineering. **Applies** — whenever a runtime is available; otherwise report as
unvalidated.
