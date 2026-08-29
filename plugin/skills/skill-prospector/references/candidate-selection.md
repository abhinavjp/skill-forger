# Candidate selection

Use this reference at stage 5, after the inventory exists. `skill-engineer`'s
mechanism and scope rules are the authority for the proposed mechanism; this
file supplies the candidate clustering and rejection procedure without
copying those rules.

## Accept a unit into a candidate

All four conditions must hold:

1. It describes a workflow or procedure invoked for some tasks, not every task.
2. It is reusable across more than one prompt shape.
3. It carries specialised knowledge or sequencing the base model would not
   reliably reproduce.
4. Its size or conditionality makes progressive disclosure worth its cost.

## Route elsewhere

| Evidence in the unit | Proposed route |
|---|---|
| Applies to every repository task | Rule file; leave the live rule in place |
| Fixed inputs and outputs with an exact repeatable operation | Script |
| Must hold regardless of model compliance | Hook, CI, permission or other enforcement |
| Requires external data or an outside-repository action | Tool or MCP |
| Fixed user-named sequence with no branching | Command or workflow |
| Reference material with no procedure | Plain document, or a reference of an existing Skill |
| Independent, bounded and context-heavy | Subagent |
| One-off, stale or superseded | Leave it; flag stale contradiction when relevant |

## Reject or defer

Record every rejection with one criterion and its routed mechanism.

- **Overlap:** merge into or reject against the existing Skill; route any
  remaining deterministic part to a script.
- **Fragmentation:** merge units that always travel together into one Skill
  with conditional branches; route universal parts to a rule file.
- **Thin candidate:** route prose already carried by a repository-wide rule to
  that rule file, rather than creating a Skill.
- **Unstaffed candidate:** defer until an observable completion condition exists;
  use a command, script or plain document if that is the actual mechanism.
- **Speculative candidate:** reject it because no inventory evidence supports
  it; leave the evidence in its current mechanism or route it to a plain
  document, and do not invent a Skill from a filename or keyword.

## Merge, rank and cap

First merge overlapping or fragmented clusters. Then state each surviving
boundary in one sentence and rank by reuse, specialised knowledge, evidence
strength and actionability. Accept at most seven by default. Mark the rest
`deferred` with its rank and reason. A candidate is not accepted merely because
the source file was matched by the catalogue.
