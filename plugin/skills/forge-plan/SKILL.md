---
name: forge-plan
description: Turn a Forge work item's Goal, decisions, and spec into an implementation-ready plan.
disable-model-invocation: true
---

# Forge Plan

The user calls this, or forge-implement backfills it when no plan exists.
Follow the shared [workflow contract](../../shared/forge/references/workflow-contract.md)
for lifecycle, backfill, approval, and stops.

## 1. Read the source

Read the Goal and evidence in `context.md`, `decisions.md`, and `spec.md` if
it exists. If an input is missing, backfill it per the shared contract
(discover always; clarify only for open decisions; never auto-run spec).

Match the request to an existing work item by its Goal. 0 or 2+ matches:
ask which work item this is before continuing.

Done when: you know the Goal, settled decisions, and spec (if any), for
exactly one work item.

## 2. Choose compact or detailed

Assess all seven factors together: size (affected systems, repos,
deployables, contracts, change surface), effort (implementation,
verification, coordination, recovery effort), complexity (dependency depth,
concurrency, legacy ambiguity, integration count), impact (user,
operational, data, security, privacy, compliance, failure blast radius),
reversibility (migration, external side effects, rollback difficulty,
mixed-version operation), execution model (multiple implementers or agents,
handoffs, audit needs), and uncertainty (missing evidence, novel mechanisms,
disputed behavior, unstable boundaries).

Recommend `compact` for small, low-risk, well-understood work; recommend
`detailed` when one factor is severe or several are moderate together. Say
why in one sentence, naming the decisive factor(s).

If the user called forge-plan directly, ask and wait for their confirmation
here before continuing. If forge-implement (or another skill) backfilled
forge-plan because no plan existed, do not ask separately: state the
recommended mode and reason, and carry it into that skill's one combined
stop (shared contract) instead of stopping twice. Either way, if a risky
item shows up after the mode is set, say so and ask again.

Done when: you have a mode — confirmed by the user directly, or carried
into the caller's combined stop for backfill.

## 3. Write the plan

Read exactly one mode reference:
- `compact`: [compact mode](references/compact-mode.md)
- `detailed`: [detailed mode](references/detailed-mode.md)

Then read [execution packets](references/execution-packet.md) for the shared
packet fields. Every packet uses these headings, in this order, so
forge-implement can find them by name:

```markdown
## Outcome
## Write scope
## Must not change
## Changes
## Proof
## Depends on
```

Mark every slice or phase `risk: low | medium | high` (size, risk,
complexity — any one high, or two medium, is high risk; see root
`CONTEXT.md`). Default location: `.forge/<work-item>/`, unless the repo
already has a convention.

Done when: every packet has all six headings and a risk label, and real
dependency edges only (no invented ordering).

## 4. Stop

If the user called forge-plan directly, show the exact plan path, ask
"review or go?", and wait — a plan is default-safe to draft but never to
run. If another skill backfilled forge-plan, do not stop here: hand back
the plan path so that skill can show it as part of its own one combined
stop. Either way, do not implement anything yet.

Done when: the user has replied directly, or the plan path has been handed
back for the caller's combined stop.
