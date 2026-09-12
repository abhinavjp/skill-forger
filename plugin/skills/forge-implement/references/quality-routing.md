# Quality routing

Load and run only guidance justified by the current packet's touched files,
symbols, requirements, binding design, or observed diff. Record a run as
`PASS`, `FAIL`, or `UNMEASURED`; do not manufacture `PASS` for a concern that
does not apply or cannot be measured.

| Touched concern | Route and inspect |
| --- | --- |
| Binding visual or interaction outcome | Design parity against approved `design.md` or packet acceptance evidence. |
| UI component or stylesheet | Reuse existing components and style primitives before adding equivalents; inspect inline styling. |
| Inline style or presentational attribute | Verify it is required and consistent with the reusable style system; otherwise use the established primitive. |
| Repeated behavior, literal, configuration value, or near-copy | Check duplication and named constants at the existing ownership seam. |
| Hot path, large input, I/O loop, cache, query, or rendering path | Check performance against the packet's stated measure or local evidence; do not infer performance from style. |
| Public interface, complex control flow, error handling, or modified ownership seam | Check maintainability: names, local boundaries, tests, compatibility, and clarity of the changed path. |
| Trust boundary, input handling, secret, audit, data exposure, or external call | Check security requirements and preserved controls. |
| Role, identity, authorization decision, tenancy, or privileged action | Check permissions and denial/default behavior. |
| Every scoped implementation diff | Compare changed paths and symbols with packet scope and `Must Not Change`; record unintended scope as a failure or authorization frontier. |

Do not load design guidance for backend-only work, performance guidance for a
non-hot formatting change, or security/permission guidance merely because a
packet exists. When a concern is genuinely unavailable to inspect, record
`UNMEASURED` with the capability/reason and keep required evidence unsatisfied.
