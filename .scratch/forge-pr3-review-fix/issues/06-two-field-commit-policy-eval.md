# 06: Two-field commit policy in forge-plan evals

**What to build:** forge-plan evals expect the current commit policy — `commit_granularity` + `history_style` only — with the removed approval field gone. (PR #3 Codex P1, FP-EX-015.)

**Blocked by:** None (can start immediately)

**Status:** done

- [x] FP-EX-015 requires exactly the two fields
- [x] No forge-plan eval references the removed approval field
- [x] Packaging tests green
