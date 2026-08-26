# Finding Contract

```text
[Severity] Short imperative title
Invariant: <required behavior>
Failure: <concrete execution scenario>
Evidence: <path:line and causal evidence>
Minimum fix: <smallest safe correction>
Verify: <specific test or observation>
```

Severity and confidence are independent. Severity: `blocker`, `critical`, `high`, `medium`, `low`. Confidence: `proven`, `strong`, `plausible`.

Publish proven/strong defects. Present plausible concerns as questions in the local report only unless the user explicitly asks to publish questions. Discard unknown or unresolved hypotheses, or report them as evidence gaps rather than findings. Consolidate repeated manifestations under one root-cause fingerprint.
