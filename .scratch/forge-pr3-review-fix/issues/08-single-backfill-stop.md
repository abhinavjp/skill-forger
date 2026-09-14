# 08: One combined stop in the backfill flow

**What to build:** When forge-implement backfills a missing Goal/plan, the user hits exactly one combined stop (Goal + decisions + mode + plan path) before any source edit; the duplicate "review or go?" is gone and intent decisions 9/18 are reconciled into one contract. (Merge Sentinel High.)

**Blocked by:** 04 (Restore seven-factor mode selection)

**Status:** done

- [x] Intent decision record states the single chosen contract (decision 18 is now the authoritative backfill-stop contract; decision 9 points to it instead of re-asserting its own ask)
- [x] forge-implement and forge-plan agree on who asks, once (forge-plan step 2/4 only ask directly when the user called it directly; when backfilled, it hands mode + plan path back for the caller's one combined stop; forge-implement step 1 collects Goal/decisions/mode/plan path into that single stop)
- [x] Eval counts every user stop through first source edit = 1, including no-Goal/no-plan case (strengthened FI-E-005; added FI-E-014 for the full discover→clarify→plan→implement backfill chain)
- [x] Packaging tests green
