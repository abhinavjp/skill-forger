# 01: Bounded work produces an approved compact plan

**What to build:** Extend the single `forge-plan` entry point so verified bounded, low-risk work receives a plainly explained compact recommendation and, after user confirmation, one semantically closed plan that preserves Forge authority, freshness, mutation, and approval boundaries.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] Recommendation considers size, effort, complexity, impact, reversibility, execution model, and uncertainty without a fixed signal-count threshold.
- [ ] Forge states decisive evidence and uncertainty, waits for confirmation or override, then loads only compact guidance.
- [ ] Compact output contains the required outcome, source basis, scope, exclusions, preserved behavior, current state, frozen decisions, vertical slices, proof, acceptance, gates, and handoff fields while omitting empty conditional risk sections.
- [ ] Approved upstream artifacts are checked in authority order with provenance, approval hash, and freshness; missing product intent routes upstream.
- [ ] Planning stops after approval and grants no implementation or external-mutation authority.
- [ ] Deterministic and behavioral tests prove the bounded compact path and explicit confirmation boundary.
