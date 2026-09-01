# Discovery impact coverage

Use this matrix to make functional impact explicit without turning every
dimension into a checklist. For each material row, record the current condition,
affected or unaffected result, evidence locator/provenance, and uncertainty.

| Dimension | Consider when | Evidence to establish |
| --- | --- | --- |
| Actors and roles | A person, service, tenant, or support role can observe or invoke the change | Eligible and excluded actors, ownership, role-specific outcomes |
| States and transitions | Behaviour depends on lifecycle, status, authentication, entitlement, or failure state | Current transitions, invariants, parallel or retry paths |
| Paths and cohorts | The request can diverge by channel, region, migration state, or cohort | Main path, parallel paths, explicit exclusions, and unassigned cohorts |
| Permissions and policy | Access, approval, data visibility, or compliance affects behaviour | Enforced boundary, applicable policy, and affected authorization outcome |
| Integrations and contracts | Another system, event, API, file, or dependency is touched | Contract/current interface, error or fallback behaviour, dependency impact |
| Regression and history | Prior failures, reversions, or dated changes may constrain the request | Relevant regression path and requirement-changing history |

Assess relationships separately when they change any row: material comments,
attachments, linked work, subtasks, parents, and dependencies. Record an
unavailable item and its impact instead of substituting absence. When current
evidence and material history conflict, preserve the conflict and route its
human decision to Clarify.

For UI work, visual references are evidence only when they affect the requested
visual outcome. Record a relevant missing reference as a warning or correctness
blocker according to its actual impact; do not load unrelated visuals.
