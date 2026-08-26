---
name: merge-sentinel
description: Review merge requests and local diffs for code defects, regressions, security risks, unsafe scope, and implementation completeness. Use for initial reviews, read-only safety audits, issue-to-code verification, re-reviews after fixes, or validation of resolved review threads. Do not use to implement feedback, fix CI, summarize changes, explain code, or create review skills.
---

# Merge Sentinel

## Default posture

Every review is adversarial by default. Treat the change as an unproven claim; try to falsify
its correctness, safety, completeness, and compatibility with concrete counterexamples and
counterevidence. Do not invent findings: retain only issues supported by changed-line causality
and the finding contract.

## 1. Establish authority and mode

Record source, target/base/head, initial/re-review mode, requirement source, exact mutation authority, and optional local overlay.

## 2. Acquire a complete snapshot

Inventory every changed file, including deleted, generated, migration, configuration, lock,
test, and rename-only files. Every changed file reaches one terminal state: `reviewed`,
`excluded-with-reason`, or `blocked`. Record pagination and truncation flags; use repository
fallback for incomplete provider diffs. Mark only affected coverage axes partial. A file-count
mismatch or non-terminal file must prohibit a clean verdict.

## 3. Load conditional policy

Load a reference only when its trigger fires:

| Reference | Load only when |
|---|---|
| `references/implementation-compliance.md` | An issue, specification, acceptance criterion, requirement document, or completeness request is in scope |
| `references/gitlab-transport.md` | Source is GitLab or any GitLab read/write operation is required |
| `references/risk-overlays.md` | Changed paths or code touch one of its named risk domains |
| `references/review-patterns.md` | Always; use a supplied or discovered local review policy before judging findings |
| `references/finding-contract.md` | A hypothesis is being retained, reported, or published |
| `references/summary-agent.md` | A final review summary or any publication is required |
| `references/rereview.md` | Prior findings/discussions exist or the user requests re-review |

## 4. Review through the evidence queue

Build a compact internal plan from the changed-file inventory, activated risk overlays, and
cross-file dependency paths. Do not publish the plan unless the user asks or a blocker needs
explanation.

Create an impact queue. Start from each hunk. Expand to enclosing symbols, callers, callees,
persistence, API contracts, tests, configuration, or history only when needed to prove or
disprove behavior, security, performance, requirements, or unwanted impact. Request such
evidence only through controller leases. Stop when proven, disproven, excluded, blocked, or
twice unresolved. Apply the required passes in `references/review-patterns.md`. Use
`review_state.py new-queue`, `request-lease`, and `complete-lease`.

## 5. Adjudicate and deduplicate findings

For each retained candidate, require invariant, concrete failure scenario, changed-line causality, counterevidence checked, confidence, severity, minimum fix, and verification. Format comments according to `references/review-patterns.md`; a concrete fix and targeted verification are mandatory. Pass the raw candidate to `review_state.py normalize-finding`; never write a fingerprint.

## 6. Re-review prior findings

For re-review, run `review_state.py resolve-anchor` and `build-rereview-packet` per prior finding. Act automatically only when the packet says `automatic_actions_allowed=true`.

## 7. Report coverage and verdict

Run the Summary Agent contract in `references/summary-agent.md`. Report separate code-quality, security, implementation-compliance, and evidence-coverage statuses. Use `complete`, `partial`, or `unverified`. Never collapse missing issue-tracker evidence into code-review failure.

Reconcile the changed-file ledger against the provider inventory. Prohibit a clean verdict when
any changed file is missing or non-terminal, any required pass is blocked, or any coverage axis
needed for the verdict is partial or unverified.

## 8. Publish only when authorized

Re-fetch head and diff version, run `validate_publication.py validate --input FILE --ledger FILE` for every intended operation, perform one write at a time, verify it remotely, and update the ledger. Stop on failed or uncertain writes.
