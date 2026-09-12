# Forge Brain adapter contract

The Brain adapter is a host integration boundary, not a workflow authority. It
may supply these optional capabilities:

- issue source;
- OKF provider;
- artifact-location conventions;
- project validators;
- authorized delivery operations; and
- designated approver or approval-policy metadata.

Its results use the issue-source and knowledge-provider contracts. Artifact
locations are conventions to preserve, not a requirement to relocate artifacts.
The adapter may report unavailable capabilities and return `UNMEASURED` evidence
with a reason. It may refuse a delivery operation outside its authorization.

The adapter must not override Forge workflow semantics, make Jira or OKF
mandatory, infer approval, open a missing/stale/unauthorized gate, or weaken
the requirement for artifact-specific approval before mutation. It exposes
capabilities and evidence; Forge owns the portable gate decision.
