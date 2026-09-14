# 07: Implementer loads task packet plus its shared facts

**What to build:** forge-implement reads the current task packet **and** the `phase.md`/`plan.md` facts it points to, leaving unrelated phases unloaded — so invariants and scope from the control plane reach the implementer. (Merge Sentinel High.)

**Blocked by:** 05 (Restore detailed-mode control plane)

**Status:** done

- [x] Step text no longer says "only its packet" (now reads its packet plus the phase.md/plan.md facts it points to; unrelated phases stay unloaded)
- [x] Eval: task passes only by preserving an invariant stated in the control plane, not in the packet (FI-E-018)
- [x] Eval: unrelated phase files not loaded (FI-E-019)
- [x] Packaging tests green
