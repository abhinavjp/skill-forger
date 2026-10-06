# Execution packet contract

A packet (a compact slice or a detailed task) is a closed record forge-plan
writes and forge-implement executes, not a place to defer decisions. Use
these six headings, in this order, so forge-implement can find each one by
name:

```markdown
## Outcome
One observable working result, in plain language.

## Write scope
Exact files/paths this packet may change.

## Must not change
Files or behaviour this packet must leave alone.

## Changes
Ordered steps. No pasted code; describe what changes.

## Proof
The narrow command(s) that prove this packet works, and the expected result.

## Depends on
Other packet IDs that must be done first, or "none".
```

## Vertical work, not layers

Each packet delivers one observable outcome across every layer it touches.
Avoid "backend changes" / "frontend changes" as separate packets when they
serve one outcome. List a dependency only when the dependent work truly
cannot start first.

## Risk

Every packet or phase carries `risk: low | medium | high` (see root
`CONTEXT.md`). High risk needs a second reviewer per the shared
[workflow contract](../../../shared/forge/references/workflow-contract.md)'s
Phase gate section.

## Commit policy

Frozen once per plan, in `plan.md`:

```yaml
commit_granularity: task | phase | end
history_style: separate | fixup_then_squash | squash
```

The shared contract always asks before a commit — there is no "preapproved"
setting. Commit authority never implies push, merge, or delivery authority.
