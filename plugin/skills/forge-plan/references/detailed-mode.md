# Detailed mode

Use after the user confirms `detailed`. Produce this tree:

```text
<work-item>/
  plan.md
  phases/
    01-<phase-slug>/
      phase.md
      01-<task-slug>.md
```

## Control plane

`plan.md` owns the facts every phase shares. Concise pointers are fine; do
not duplicate a fact a phase or task file already owns.

- Outcome, scope, exclusions, and the approved source basis.
- Stable, canonical IDs for every requirement and invariant in scope, with
  traceability to the phase or task that satisfies each one.
- The phase dependency graph and executable frontier.
- Integration points: where phases connect and what each hands the next.
- Change policy and the default commit policy (`commit_granularity: phase`,
  `history_style: separate`).
- Cross-phase proof: evidence that spans phase boundaries and cannot be
  proven inside any single phase.
- Final acceptance: the observable criteria that close the whole plan, once
  every phase is done.
- Conditional controls, only where their risk exists (see Risk below):
  rollback, idempotency, observability, compatibility
  (expand-migrate-contract), security, and manual/live proof. Point to the
  phase or task that carries each one; do not restate its detail here.

## Phases and tasks

Each phase directory owns one cohesive, independently reviewable outcome.
`phase.md` records its outcome, `risk:` label with reasons, task index, real
start-blocking edges, and review focus. Split independently deployable or
reversible outcomes into separate phases; a wide but cohesive phase is fine
if `phase.md` says why reviewing it in one pass is still safe.

Each task file uses the six headings from
[execution packets](execution-packet.md). Reference `plan.md` facts by
pointer instead of copying them into every task.

## Risk

- `low`: reversible, bounded, locally proven.
- `medium`: real integration, compatibility, or uncertainty risk.
- `high`: severe impact, hard to recover, or touches a sensitive boundary
  (see root `CONTEXT.md`'s definition of high risk).

High risk always needs a second reviewer (root `CONTEXT.md`); add
rollback notes for anything hard to reverse.

## Phase gate

Use the shared contract's Phase gate section in the
[workflow contract](../../../shared/forge/references/workflow-contract.md)
at the end of every phase. It ends in a stop before that phase's commit.
