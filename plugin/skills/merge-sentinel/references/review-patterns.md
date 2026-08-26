# Review Patterns

## Adversarial posture

For each material change, state the implementation claim. Competing hypothesis: a concrete
alternative that would make the claim wrong, expressed as a specific input, state transition,
caller path, permission boundary, failure path, concurrency schedule, data shape, or requirement
mismatch. Try to prove the competing hypothesis with that concrete evidence. Then seek the
strongest counterevidence: guards, contracts, tests, transaction boundaries, local policy, or
unchanged paired behavior.

Retain a hypothesis only when changed-line causality and a concrete failure scenario survive
counterevidence. Mark it disproven when evidence defeats it. Mark it blocked when the smallest
required evidence cannot be obtained. Do not convert suspicion, missing context, or checklist
intuition into a defect.

## Execution sizing

- Small review: review directly.
- Medium review: delegate only an expensive, independent investigation when isolation or
  parallelism materially helps.
- Large or huge review: partition by independent component, risk domain, or requirement when
  doing so preserves file coverage and keeps cross-file dependencies visible to the main reviewer.

Do not delegate when direct review is cheaper. The main reviewer owns cross-file reasoning,
deduplication, final findings, publication, and the verdict. Delegated work must be read-only,
bounded to named files/questions, and return findings and evidence, not raw code. A delegated
result is a hypothesis until the main reviewer reconciles it with the full diff and local policy.

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
   returned values, null/error paths, persistence, API boundaries, and relevant tests. Test
   normal, null/empty, error, partial-success, retry, and returned-value paths only when
   applicable to the changed contract.
3. Boundary pass: when triggered, trace tenant or authorization boundary, secrets/PII,
   permission checks, feature-disabled paths, and cross-client/portal parity. When a security
   overlay activates, perform a compact threat model containing asset, trust boundary, attacker
   capability, abuse path, existing control, and residual impact.
4. Consistency pass: compare paired actions, interface/implementation, request/response,
   migration/dependency, and UI/API changes where the diff or local policy indicates a pair.
   Check cross-file and cross-component pairings, including callers, DTO/API shapes,
   migrations/runtime expectations, UI/API parity, and feature-disabled behavior.
5. Requirement pass: use the implementation-compliance reference only when an authoritative
   requirement source exists; absence is an evidence status, not a code defect. Check critical
   impact not mentioned in Jira/spec as an out-of-scope impact observation unless it is also a
   changed-line defect.
6. Performance pass: add only when operative evidence activates it: query/I/O multiplicity,
   unbounded work, hot-path allocation, locking, and payload growth.

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

Use short sentences and simple words. State the exact issue or question, the concrete failure,
and the expected behavior or check. Avoid vague wording, unnecessary jargon, and repeated
background. Keep technical identifiers exact.
