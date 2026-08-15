# Execution rules — R11, R13, R14, R15, R16, R17

Load when the Skill runs a multi-step workflow, ships scripts, calls tools or
MCP servers, spawns subagents, or states a hard invariant. Index:
[rules-index.md](rules-index.md).

## R11. Deterministic extraction and over-extraction

**Check** — Two failure directions. Is the model repeatedly doing mechanically
reproducible work? *And* has flexible reasoning been frozen into an
unnecessarily rigid pipeline?
Prefer determinism when the operation is precisely specifiable, repeatable,
mechanically checkable, frequent, and where model reasoning adds little. Prefer
reasoning when ambiguity, competing objectives, semantics or highly variable
inputs dominate.
**Detect** — Extraction: repeated parsing, filtering, exact sorting, static
inventory, repeated deterministic shell loops. Over-extraction: mandatory
scripts for low-risk work, full validation on trivial requests, complex pipeline
on simple requests. A one-line illustrative command is not an extraction
candidate; the cost of a script is a file, an interface and a dependency.
**Severity** — Medium/High either way.
**Action** — Extract only the stable deterministic portion; return non-critical
decisions to the agent or make gates conditional.
**Validation** — Differential eval against the simpler version, comparing
correctness, context, latency and maintenance cost.
**Automation** — hybrid. **Class** — Strong heuristic. **Applies** — always.

## R13. Script quality

**Check** — Does each script have a stable, inspectable execution contract for
its role? Normal execution should not require loading implementation source:
`script --help`, defined inputs, structured output, meaningful exit codes.
**Detect** — Entry point, inputs, outputs, exit/error behaviour, privileges,
network and filesystem operations. In review/security mode, read the source to
establish trust, side effects, correctness and portability. A script that
executes instructions supplied by its own input data has no trust boundary at
all, however clean its interface looks.
**Severity** — Critical for unsafe privileged behaviour; High for
correctness-critical instability; Medium otherwise.
**Action** — Stabilise the interface, or delete a script that does not earn its
maintenance cost.
**Validation** — Script tests plus the dependent Skill evals.
**Automation** — hybrid. **Class** — Situational. **Applies** — Skills with
scripts.

## R14. Tool and MCP efficiency

**Check** — Are tool calls broader, more repetitive or more numerous than
needed? Use a tool when external capability or live data is genuinely required;
do not expose every tool "just in case".
**Detect** — Duplicate searches, repeated metadata discovery, full enumeration
followed immediately by filtering, refetching the same artifact. The opposite
miss counts too: work done laboriously in context that an available tool would
answer in one call.
**Severity** — Medium; High when cost or latency becomes material.
**Action** — Narrow queries, reuse results, batch where supported, prefilter.
**Validation** — Tool-call count plus correctness comparison.
**Automation** — runtime/eval. **Class** — Strong heuristic. **Applies** —
tool-using Skills.

## R15. Deterministic enforcement

**Check** — Is the Skill asking the model to honour an invariant that must never
be bypassed?
**Detect** — "must always", "must never", security requirements, destructive
action restrictions expressed as prose.
**Severity** — Critical where a bypass causes security or data loss.
**Action** — Move enforcement into a hook, permission, validator or CI gate
where the host allows; keep the explanation in the Skill.
**Validation** — Attempt the violating action in a controlled test.
**Automation** — hybrid. **Class** — Strong heuristic; the enforcement
mechanism is platform-specific. **Applies** — Skills with hard invariants.

## R16. Subagent justification

**Check** — Does delegation return more than it costs? Legitimate reasons:
context isolation, parallel independent work, specialist reasoning, keeping
noisy intermediate data off the main thread.
**Detect** — Task independence, context volume, parallelism potential,
duplicated work, merge/reconciliation cost.
**Severity** — Medium.
**Action** — Single agent for small or serial work; delegate bounded independent
work when it pays.
**Validation** — Delegated vs single-agent success, cost and latency.
**Automation** — hybrid. **Class** — Situational. There is **no validated
universal threshold** for when delegation wins — treat any specific threshold as
Needs validation. **Applies** — Skills that spawn subagents.

## R17. Completion semantics

**Check** — Could the agent plausibly stop at an intermediate state and present
it as done? This rule owns premature completion; do not raise it separately.
**Detect** — Multi-stage workflows; intermediate artifacts resembling final
output; missing verification stage; unclear definition of done; unvisited
required branches; partial review presented as complete; raw tool output
presented as the solution. A failure report that reads as though the work
happened is the same defect wearing a different face.
**Severity** — High for multi-step workflows; not applicable to simple reference
Skills.
**Action** — Add minimal *observable* completion conditions — few, checkable,
outcome-shaped. Conditions that require the agent to narrate its own compliance
are procedure, not completion.
**Validation** — Interrupted and incomplete-execution cases.
**Automation** — hybrid. **Class** — Situational / Strong heuristic.
**Applies** — multi-step workflows.
