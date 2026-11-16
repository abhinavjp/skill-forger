# 07: Approved plans expose a read-only ticket handoff

**What to build:** Let an approved plan expose a formal, lossless `to-tickets` handoff while preserving the boundary between planning and separately authorized tracker publication.

**Blocked by:** 06: Phase gates produce controlled handoffs.

**Status:** ready-for-agent

- [ ] The handoff references the approved plan hash, stable IDs, ticket outcomes, dependency edges, executable frontier, scope, acceptance, risk, review, and approval policies.
- [ ] Ticket prose derives from canonical plan content without duplicating requirements or inventing tracker structure.
- [ ] Missing tracker capability is reported without invalidating the approved local handoff.
- [ ] Producing the handoff performs no tracker write, labeling, implementation, commit, push, merge, deployment, or release action.
- [ ] Tests prove successful read-only conversion and refusal of implicit publication.
