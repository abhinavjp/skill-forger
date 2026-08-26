# Review Patterns

## Domain overlay

Always load a supplied or discovered local review policy before judging findings. Record the
policy path, every activated overlay, why it activated, and the evidence examined. Apply its
severity rules, known exceptions, and **Do NOT Flag** conventions. Do not invent a domain rule
when no authoritative local policy is available.

## Required passes

Run these passes after the diff-first evidence queue and before adjudication:

1. Diff scope: retain only defects caused by changed lines; put pre-existing concerns in the
   summary as out-of-scope observations.
2. Contract pass: trace changed symbols through caller and callee contracts, state transitions,
   returned values, null/error paths, persistence, API boundaries, and relevant tests.
3. Boundary pass: when triggered, trace tenant or authorization boundary, secrets/PII,
   permission checks, feature-disabled paths, and cross-client/portal parity.
4. Consistency pass: compare paired actions, interface/implementation, request/response,
   migration/dependency, and UI/API changes where the diff or local policy indicates a pair.
5. Requirement pass: use the implementation-compliance reference only when an authoritative
   requirement source exists; absence is an evidence status, not a code defect.

Each pass must either produce evidence, be excluded by scope, or be marked blocked. Do not
report checklist intuition as a finding.

## Comment quality

One root cause is one thread on the exact changed line. A retained inline comment must use the
following format, with blank lines between fields:

```text
**Severity:** <Blocker | Critical | High | Medium | Low>

**Issue:** <one concrete defect>

**Why it matters:** <specific failure scenario and impact>

**Fix:** <smallest safe correction>

<small, directly relevant replacement or pseudocode when it removes ambiguity>

**Verify:** <targeted verification: test, repro, or state transition>
```

The fix must preserve the nearest established local pattern (including error handling,
transactions, naming, and authorization boundaries) and name the smallest safe change. Provide a
safe replacement whenever the exact changed-line correction is local and supported by evidence.
If a replacement would require unseen callers, schema, or a broad design choice, say that plainly
and give the narrowest pattern-aligned direction instead. Include a code example only when it is
safe, short, and materially clearer than prose. Do not praise, bundle concerns, suggest unrelated
refactors, or comment on correct code. End every published comment with
`— Merge Sentinel · evidence-led review · head <short-sha>`.
