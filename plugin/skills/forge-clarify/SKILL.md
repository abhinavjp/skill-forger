---
name: forge-clarify
description: Resolve the open human decisions in a Forge work item, then stop.
---

# Forge Clarify

Runs when the user calls it, the host selects it, forge-discover points here
because it found open human decisions, or forge-prototype hands over a
candidate choice. Follow the shared
[workflow contract](../../shared/forge/references/workflow-contract.md) for
approval, stops, and the conflict rule.

## 1. Build the decision frontier

Read the Goal in `context.md`, its evidence, and any existing `decisions.md`.
If `prototype-decisions.md` exists, every `P-###` that no `decisions.md` record
cites is also a candidate decision.
Apply [decision-frontier.md](references/decision-frontier.md) to classify
every candidate decision: already answered, answerable from evidence,
ready to ask, or already settled. Do not turn this into Discovery or choose
an architecture yourself.

Done when: you know exactly which decisions are ready to ask.

## 2. Ask, once, in one round

Present every independent ready decision together, each with the decision,
its material options, and the evidence gap. Hold back a decision that
depends on another one until its prerequisite is settled.

Done when: the user has answered, or there is nothing left to ask.

## 3. Record the answer

On the user's approval, append the decision to `decisions.md`: the decision,
its scope, who approved it and their own words, and the evidence behind it.
Reopen a settled decision only when new evidence contradicts it, and say what
that evidence is. A user changing their own earlier answer is a new answer, not
a reopen: append it and note the record it supersedes.

For a prototype candidate (`P-###`), handed over by forge-prototype or found in
step 1, record only when the user names the chosen option or drops the question
in their own words ("looks good" does neither); otherwise ask as in step 2. Use
the record form in
[decision-frontier.md](references/decision-frontier.md). If forge-prototype
handed it over, return to the prototype session.

Done when: `decisions.md` reflects every answered decision, or you report
that nothing is unresolved.
