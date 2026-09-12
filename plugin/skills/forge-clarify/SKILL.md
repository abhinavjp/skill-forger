---
name: forge-clarify
description: Use when a user explicitly invokes Forge clarification, or an authorized Forge workflow reaches its clarification stage with unresolved human decisions.
---

# Forge Clarify

Own the clarification boundary: resolve genuine human decisions from current
evidence, then stop. Do not activate for general questions, evidence gathering
alone, technical architecture, planning, or implementation.

Before asking, inspect the current scoped evidence and `decisions.md`. Apply
the decision-frontier method in [decision-frontier.md](references/decision-frontier.md).
Ask only decisions a human must make; reuse materially equivalent answers and
research facts available from current evidence. Do not broaden this into
Discovery or choose an architecture.

Present independent ready decisions together in one round. Keep dependent
decisions until their prerequisites are settled. Reopen an approved decision
only when evidence shows a contradiction, staleness, or material scope change;
state that evidence and the affected decision.

On an authorized natural-language approval, record the approved decision in
`decisions.md` and bind it through the shared workflow contract. If approval or
binding cannot be established, report the unresolved or blocked state rather
than inferring it. Follow [the shared workflow contract](../../shared/forge/references/workflow-contract.md)
for gate, approval, freshness, retry, resume, and continuation semantics.

Finish with the clarification result. Do not start a later stage unless an
authorized full-workflow continuation already permits it; workflow intent is
not approval.
