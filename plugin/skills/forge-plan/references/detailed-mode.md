# Detailed mode

Use after the user confirms `detailed`. Produce this progressively loadable tree:

```text
<work-item>/
  plan.md
  phases/
    01-<phase-slug>/
      phase.md
      01-<task-slug>.md
```

## Detailed artifact tree

A complete draft awaiting approval is `PAUSED` / `AWAITING_APPROVAL`, not
success. `COMPLETE` requires a contract-valid recorded approval for that exact
Plan; Forge then stops without implementation.

`plan.md` is the control plane. Each `phases/<phase>/phase.md` is shared phase
context. Ordered task files inside that phase directory are execution packets;
they are not a flat second plan. Do not create a separate repository-wide task
index or copy global facts into packets.

## Control plane

`plan.md` owns all global facts: outcome, scope, exclusions, approved baseline
and authority, stable requirement (`REQ`), invariant (`INV`), contract (`CON`),
decision (`DEC`), and risk (`RSK`) IDs, phase graph, executable frontier,
integration points, change and commit policies, cross-phase proof, and final
acceptance. Default commit policy is `phase`, `always_ask`, `separate`.

## Phases

Each numbered phase directory owns one cohesive working vertical outcome. Its
`phase.md` records a stable `PHS` ID, outcome, owned contract and integration
point, referenced invariants, risk level with reasons, task index, real local
start-blocking edges, integrated gate, review focus, and handoff contract.

Split independently deployable or independently reversible outcomes. File,
requirement, module, or boundary counts are warning heuristics only; a wide
cohesive phase records why one-pass review remains safe. Enabling work is valid
only when it unlocks a named working phase. For unsafe non-atomic boundaries,
use expand-migrate-contract with viable mixed-version states.

Each ordered task file owns one stable `TSK` ID and follows the shared execution
packet contract. Phase/task packets reference control-plane IDs instead of
copying global prose. Retain verified paths, symbols, contracts, and useful
commands; omit volatile line numbers, source listings, and cheaply recoverable
repository facts.

## Risk routing

Classify every phase:

- `low`: reversible, bounded, locally proven; same-agent integrated review;
- `medium`: meaningful integration, compatibility, operational, or uncertainty
  risk; same-agent review unless novelty weakens independence;
- `high`: severe impact, difficult recovery, or sensitive boundary; independent
  review required.

Independent review is mandatory for security, permission, privacy, compliance,
irreversible migration, credible data loss, and recovery-critical boundaries,
regardless of aggregate label. Task-level semantic review is reserved for an
irreversible step, security-critical boundary, or unusually uncertain work.

Add rollback for deployed, stateful, external-side-effect, or hard-to-reverse
work; idempotency for retries, jobs, webhooks, migrations, or resumable work;
observability for runtime proof; compatibility sequencing for mixed versions;
and manual/browser/hardware/migration/performance/live-provider/security/UAT
proof only where automation cannot cover the identified risk.

## Phase gate

For each phase: run task-local checks; integrated checks; whole-phase semantic
review; classify findings `blocking`, `non-blocking`, or `out-of-scope`; remediate
blocking findings; rerun affected checks; run one final integrated review; then
record proof, deviations, non-blocking findings, and `UNMEASURED` behavior.

Clean means required checks pass and zero blocking findings remain. Two review
loops without progress, or material reviewer disagreement, returns control to
the user. After required automation, pause and offer only applicable actions:
continue to the next ready phase, named extra testing, commit under the approved
policy, revise, or stop.
