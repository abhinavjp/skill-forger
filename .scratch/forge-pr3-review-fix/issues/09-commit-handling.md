# 09: Honest commit handling in forge-implement

**What to build:** Commit behaviour matches the chosen policy: a stop-and-go checkpoint after each task when granularity is `task`; protected-branch handling actually creates/switches and verifies the branch rather than only suggesting a name; and `progress.md` records commits via a scheme that never needs a commit to contain its own hash. (PR #3 Codex P1 + P2; Merge Sentinel coverage gaps.)

**Blocked by:** 06 (Two-field commit policy in forge-plan evals)

**Status:** done

- [x] Eval: task granularity → one user stop + commit per task (FI-E-015)
- [x] Eval: on protected branch, work proceeds only after verified switch to new branch (strengthened FI-E-011; added FI-E-016 for a failed switch)
- [x] Eval: progress record is consistent after commit (no self-referencing hash) (FI-E-017; workflow-contract.md's `progress.md` format now uses `pending | committed` instead of a commit id)
- [x] Packaging + Forge shared tests green
