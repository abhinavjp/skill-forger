# 03: forge-spec evals match the gate-free contract

**What to build:** forge-spec execution evals stop expecting the removed "awaiting-approval" revision gate; success is `spec.md` ready for forge-plan. FS-E-001 fixed; rest of the file swept for the same leftover. (PR #3 Codex finding.)

**Blocked by:** None (can start immediately)

**Status:** done

- [x] FS-E-001 asserts spec ready for forge-plan, no approval-gate marking
- [x] No other forge-spec eval references the removed gate
- [x] Packaging tests green
