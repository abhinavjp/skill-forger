# 05: Restore detailed-mode control plane

**What to build:** Detailed plans again carry the approved control plane: stable IDs, requirement/invariant traceability, integration points, cross-phase proof, final acceptance, and conditional compatibility/security/observability/idempotency controls (concise pointers OK). (Merge Sentinel High.)

**Blocked by:** 04 (Restore seven-factor mode selection) — same skill, avoids edit conflicts

**Status:** done

- [x] Reference names every required control-plane field (detailed-mode.md `## Control plane`: stable IDs, traceability, integration points, cross-phase proof, final acceptance, plus conditional controls)
- [x] Shape validator rejects a detailed plan missing any required field (test per field) — FP-EX-033..037, one llm-judge case per field, each expects the gap named and the plan not marked ready
- [x] Behavioral evals cover each conditional control triggering and not triggering — not-triggering already covered by FP-EX-011; rollback/idempotency (FP-EX-012) and compatibility (FP-EX-010) already covered; added FP-EX-038 (observability) and FP-EX-039 (security)
- [x] Packaging + Forge shared tests green
