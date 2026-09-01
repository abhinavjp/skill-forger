# Forge workflow contract

This is the portable source of truth for Forge workflow boundaries. Adapters
and stage Skills use the deterministic terms and decisions in
`plugin/shared/forge/scripts/workflow_state.py`; they do not redefine them.

## State and boundaries

```text
discover/clarify complete
  -> spec active
  -> spec awaiting-approval
  -> spec approved
  -> plan active
  -> plan awaiting-approval
  -> plan approved
  -> implementation active

any required gate missing/stale/unauthorized
  -> blocked-at-gate (read-only for source/implementation artifacts)

approved artifact materially changes
  -> approval stale
  -> downstream dependent gates invalid
```

Discovery/clarification is evidence gathering and reconciliation. Specification
owns the Specification artifact; Planning owns the Plan artifact; Implementation
owns source and implementation artifacts. A stage may change only its owned
artifact and only within its authorized scope. Discovery is read-only.
Specification and Planning may write their own artifacts, but neither may mutate
source or implementation artifacts. Implementation is mutation-capable only
after all of its gates allow entry. Delivery operations are separate mutations:
they require explicit scope authorization and an adapter-authorized operation.

There is no direct transition from Discovery or Specification draft to
Implementation. A full-workflow request may continue through eligible stages,
but it stops at every required approval gate; it is never approval of an
artifact.

## Gates, approval, and freshness

Planning requires a valid Specification approval when `requires_spec_approval`
is true. Implementation requires a valid Plan approval and, when required, the
valid Specification approval. Gate decisions use the state helper's
`can_enter_stage` rules: an approval is artifact-specific, matches the current
artifact hash and revision, is not by the current actor or artifact author, and
precedes every mutation it is claimed to authorize. A full-workflow or
implementation intent is not artifact approval. Approval after a mutation is
post-hoc and does not validate that mutation.

When an adapter supplies designated approvers or approval policy, it narrows
the acceptable actors for its `planning` and `implementation` policy stages; it
does not override, infer, or weaken Forge gates. A mismatch, self-approval,
unknown authorization, stale hash/revision, or unproven approval ordering keeps
the gate closed. Material change to an approved artifact makes its approval
stale and invalidates dependent downstream gates.

Requirement sources and selected knowledge are fresh only when their recorded
provenance and hashes/freshness observations still match the artifact's
materially used inputs. A requirement-changing historical contradiction stays
unresolved until clarified; it blocks the affected artifact and its dependants.

## Checks, retries, and resume

Checks are exactly `PASS`, `FAIL`, or `UNMEASURED`. `PASS` alone is passing.
`FAIL` records failed evidence. `UNMEASURED` requires a reason and is not a
pass; a required gate that needs it remains unsatisfied unless a separately
authorized replacement evidence path is recorded.

Retry is explicit: transient failures may retry only below their configured
attempt limit; deterministic failures may retry only after relevant inputs
change. Do not retry an unknown classification implicitly. A blocked artifact
blocks every transitive dependant. Resume is idempotent: begin at the first
incomplete or unverifiable ordered item (including hash drift), and return no
resume point only when every completed item is verified.

## Safety invariants

- Do not infer approval from intent to run the full workflow.
- Do not mutate source code before the Implementation gate; do not silently
  mutate delivery state at any stage.
- Refuse unauthorized scope or delivery requests, and record the refusal.
- Isolate pre-existing changes: neither overwrite, clean up, claim, nor deliver
  them unless separately authorized.
- Propagate contradictions, stale approvals, and missing required gates to all
  affected downstream work as `blocked-at-gate`.
