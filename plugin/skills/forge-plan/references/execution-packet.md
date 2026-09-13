# Execution packet contract

## Packet fields

Each packet is a closed execution record, not a place to defer product or
architecture choices. It is owned by its compact plan or detailed phase and
uses the current artifact tree selected by the mode reference.

## Vertical work and dependencies

Each slice or task delivers one observable working outcome across every relevant
layer. Avoid repository-layer buckets. Record `blocked_by` only when unfinished
work truly prevents the dependent work from starting. The executable frontier
is every incomplete task whose dependencies are complete; show the whole set.

Each packet states the closed product, architecture, scope, and material
alternative decisions needed for implementation. A packet with an unresolved
material decision is blocked and returns upstream; it is not approvable.

Each packet states:

- stable ID, title, observable outcome, and referenced canonical IDs;
- exact write scope, relevant symbols, preserved behavior, and must-not-change
  constraints;
- ordered implementation changes without copied working code;
- narrow automated proof, command where stable, and expected result;
- conditional manual/live proof and why automation is insufficient;
- handoff status, evidence, deviations, findings, and `UNMEASURED` behavior.

## Acceptance and gates

Acceptance describes observable behavior. Every task carries local proof; every
phase or compact plan carries an integrated gate and final semantic review.
Required checks precede any approval or next-action menu.

## Authority

Freeze these independently:

```yaml
commit_granularity: task | phase | end | none
commit_approval: always_ask | preapproved
history_style: separate | fixup_then_squash | squash
```

`preapproved` permits commits only after the selected clean gate. Commit authority
does not imply implementation, tracker, push, merge, deployment, or release
authority. Record every separately authorized action; otherwise pause.
