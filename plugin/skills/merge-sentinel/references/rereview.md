# Re-review

## Skip decision

Always read current discussions before deciding to skip. Compare the latest reviewed head with
the current head, then compare prior discussion resolution and update state with the state seen
at that review.

Skip code re-review only when the latest reviewed head equals the current head and no prior
discussion changed in a way that needs verification. Re-review when the head changed, or when a
discussion changed, was resolved, was reopened, or received a developer reply that requires
verification. A skip applies only to code analysis; discussion and gate checks still run.

If the latest reviewed head or prior discussion snapshot is unavailable, do not infer equality.
Mark the comparison unverified and perform the review needed to support the requested verdict.

## Snapshot comparison

Compare the current snapshot with the reviewed snapshot before classifying prior findings.

## Per-finding packet

Validate fixes against current raw packet context.

## Semantic classification

Allowed semantic groups are `fixed`, `persistent`, `reopened`, `obsolete`, and `new`.

## Remote discussion action

`ambiguous` or `missing` anchors prohibit resolve, reopen, and reply; produce an evidence-gap entry. When authorized and a resolved discussion remains persistent, reopen first, verify reopened state, then reply.

## Summary groups

Summarize findings by their semantic group.
