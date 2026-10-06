---
name: forge-clarify
description: Resolve the open human decisions in a Forge work item, then stop.
disable-model-invocation: true
---

# Forge Clarify

The user calls this, or forge-discover points here because it found open
human decisions. Follow the shared
[workflow contract](../../shared/forge/references/workflow-contract.md) for
approval, stops, and the conflict rule.

## 1. Build the decision frontier

Read the Goal in `context.md`, its evidence, and any existing `decisions.md`.
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
that evidence is.

Done when: `decisions.md` reflects every answered decision, or you report
that nothing is unresolved.
