# Mutation-safety rules — R18, R19

Load when the Skill mutates state, calls external services, retries, or is
long-running. On a read-only Skill these are noise; on a mutating one their
absence from a review is a miss. Least privilege (R20) and untrusted resources
(R21) are always-on and live in [rules-core.md](rules-core.md). Index:
[rules-index.md](rules-index.md).

## R18. Failure recovery and retries

**Check** — Can an expected failure cause unsafe continuation or needless loss
of work? This rule owns retry behaviour.
**Detect** — Inject a missing dependency, a timeout, malformed input, partial
completion. Where a workflow has several side effects, check what happens when
the second one fails after the first succeeded.
**Severity** — High/Critical by impact.
**Action** — Stop on unsafe failure; preserve useful intermediate state; surface
the failure clearly. Retry only where failure is plausibly transient, with
bounded attempts, never infinite, never on deterministic validation failure
unless state changed; backoff where the external service warrants it.
**Validation** — Failure-injection cases, executed under controlled conditions
rather than graded on whether the Skill's prose mentions failure.
**Automation** — runtime/eval.
**Class** — Situational. **Applies** — external tools, network, stateful or
long-running workflows.

## R19. Idempotency

**Check** — Can rerunning a mutating Skill duplicate or corrupt state?
**Detect** — Execute the operation twice against controlled state.
**Severity** — Critical/High for dangerous mutations.
**Action** — Precondition/state check, stable identifier, update instead of
duplicate, or explicit user confirmation where non-idempotence is unavoidable.
**Validation** — Re-run test. **Automation** — runtime/eval. **Class** —
Situational. **Applies** — mutating Skills only.
