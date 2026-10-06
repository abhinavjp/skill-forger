# 02: Invocation-policy evals for explicit-only Forge skills

**What to build:** The five Forge skills are explicit-only, so their trigger corpora stop testing implicit routing. They instead verify: implicit non-selection, explicit selection succeeds, required host metadata present, and an honest `UNMEASURED` where a host can't enforce suppression. (Merge Sentinel High.)

**Blocked by:** 01 (Structural invocation-policy check)

**Status:** done

- [x] No Forge trigger suite expects implicit selection (flipped FP-TR-001/002/003/007 and each skill's FD/FC/FS/FP/FI-T-002 natural-language paraphrase case to `trigger: false`)
- [x] Each Forge skill has implicit-suppression + explicit-selection cases per host (`platforms.required`/`optional` on suppression cases; `explicit-invocation` tag on the "Use forge-X..." cases)
- [x] Hosts lacking enforcement report `UNMEASURED`, not PASS (documented in each case's `notes`: Codex without a matching `agents/openai.yaml` policy cannot be graded PASS; the shared static runner already reports host-routing cases as `unmeasured`/`skipped`, never `passed`, absent a live capability)
- [x] Packaging tests + validator green
