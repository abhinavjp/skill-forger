# 02: Unsafe compact planning escalates explicitly

**What to build:** Make `forge-plan` reject or reconsider compact planning when verified evidence cannot support a safe, closed packet, while keeping the user's mode choice explicit and reversible.

**Blocked by:** 01: Bounded work produces an approved compact plan.

**Status:** ready-for-agent

- [ ] One severe factor or cumulative moderate factors can recommend detailed mode; bounded low-risk evidence favors compact mode.
- [ ] Explicit detailed requests are honored, while unsafe compact requests identify the exact unresolved gap.
- [ ] Unsafe compact handling offers only scope reduction, detailed mode, or the applicable upstream return.
- [ ] Stale, contradictory, or late evidence is surfaced; material recommendation changes pause for reconfirmation.
- [ ] Behavioral cases cover severe single-factor, cumulative-risk, override, stale-source, unresolved-intent, and late-escalation paths.
