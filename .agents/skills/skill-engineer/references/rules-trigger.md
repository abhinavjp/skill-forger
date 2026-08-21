# Trigger rules — R3, R4, R5

Load when the Skill is discovered by the model rather than invoked only by
name. Index: [rules-index.md](rules-index.md).

## R3. Trigger metadata quality

**Check** — Do `name` + `description` communicate what the Skill does and when
it is relevant? Treat them together as the portable routing interface; the
description alone does not determine activation.
**Detect** — Semantic specificity; representative user wording; adjacent tasks;
important synonyms and paraphrases. Trigger-critical meaning belongs early —
some hosts truncate catalog metadata (Strong heuristic). Do not chase "magic"
leading words: distinctive vocabulary is fine when natural, but a wording change
justified only by word order is **Needs validation** until A/B trigger evidence
exists. Several paraphrases of one capability are not keyword stuffing;
enumerating unrelated domains is.
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
precision/recall measurement, and keep execution quality out of it too: a case
that grades what the Skill did after routing is measuring a different layer and
will misattribute its failures.
**Severity** — High, Critical when misrouting reaches a dangerous capability.
**Action** — Change routing metadata or the Skill boundary, not the body.
**Validation** — Re-run the trigger suite across multiple trials where model
variance matters. **Automation** — runtime/eval. **Class** — Universal.
**Applies** — implicitly discovered Skills.

## R5. Catalog competition

**Check** — Does routing survive with realistic neighbouring Skills installed?
**Detect** — Test in isolation, with one deliberately overlapping Skill, in a
realistic production catalog, and in a high-overlap catalog where relevant.
A competition result means nothing unless the competitor was verifiably present
and routable at trial time: capture the catalog before the trial and record a
missing competitor as unmeasured, never as a win. A clean sweep against an
absent competitor is a single-candidate result wearing a competition label.
**Severity** — High where real deployments carry substantial competition.
**Action** — Differentiate descriptions, consolidate redundant Skills, or change
invocation strategy where the host supports it.
**Validation** — Catalog-aware trigger eval with a recorded catalog snapshot.
**Automation** — runtime/eval.
**Class** — Strong heuristic; exact catalog behaviour is platform-specific.
**Applies** — when a catalog exists.
