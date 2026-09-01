# Commit modes

Select one mode once before packet writes. It governs checkpoint timing, never
approval, verification, scope, or delivery. In every mode, first capture the
dirty baseline and stage only exact packet paths that are not baseline paths.
A packet is commit-eligible only when its declared required evidence is `PASS`,
its dependencies are verified, its scope is authorized, and its changes are
not failed or blocked work.

## `review-first`

For each eligible packet: finish its narrow and routed quality checks; review
that packet's scoped diff against its closed packet; resolve or record review
findings; then create its authorized checkpoint commit. This scoped diff review
is not the final semantic review and does not add a second final review.

## `per-task`

For each eligible packet: finish its checks, then create its authorized
checkpoint commit immediately. Do not delay it for a later packet and do not
bundle independent packets merely for convenience. A separate review can occur
only when the approved packet or local policy requires it; delegation is never
mandatory.

## `end-only`

Keep successful packet changes isolated and uncommitted until all eligible
packets have terminal states and integrated deterministic verification passes
for the verified scoped result. Then commit only the verified eligible scope in
the authorized end checkpoint. Do not include failed, blocked, `UNMEASURED`
required, unplanned, or baseline changes.

## Shared safety rules

- Failed or blocked work never enters a commit. Retain it only as explicitly
  recorded diagnostic state; do not discard or rewrite it automatically.
- Pre-existing dirty paths are outside implementation ownership: do not stage,
  amend, clean, commit, or claim them. Re-check the baseline before each
  checkpoint and stop if scope cannot be isolated safely.
- Resume verifies persisted task state, observed hashes, scoped diffs, and
  checkpoint identity. Start at the first incomplete or unverifiable item;
  never repeat a verified write, commit, or other side effect.
- A checkpoint is local version-control state only. Never automatically push,
  squash, create or update a pull request, merge, or perform another delivery
  operation. Those actions need explicit authorization and adapter support.
