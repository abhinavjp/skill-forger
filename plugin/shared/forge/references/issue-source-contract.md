# Forge issue-source contract

An issue source is optional transport behind a host-neutral result. Jira or any
other tracker may provide it, but Forge requires only these semantics:

```text
issue-source result
  current_fields: materially relevant current values
  sources: provenance for each value or evidence item
  unavailable_sources: requested evidence that could not be read, with reason
  relationships: relevant linked work and relationship type
  requirement_changing_history: dated changes or contradictions that alter scope
  freshness: observation time, source/version identifiers, and hashes when available
```

`current_fields` contains the normalized values that affect the artifact, not a
copy of every remote field. `sources` identifies where each material value came
from (for example field, comment, attachment, or linked item). Preserve enough
locator and freshness metadata to revisit the evidence. Do not persist raw
source payloads by default; retain a raw fragment only when it was materially
used and cannot be represented faithfully otherwise.

An unavailable source is evidence of unavailability, not absence or success.
If current fields and requirement-changing history conflict materially, expose
the contradiction for clarification; do not silently select one history. The
result feeds the workflow contract's freshness and blocking semantics.
