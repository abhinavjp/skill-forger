# 04: Restore seven-factor mode selection

**What to build:** forge-plan chooses lightweight vs detailed mode on all seven approved factors — size, effort, complexity, impact, reversibility, execution model, uncertainty — with "one severe or several moderate → detailed". (Merge Sentinel High; source: proportional-planning design/spec.)

**Blocked by:** None (can start immediately)

**Status:** done

- [x] Skill lists all seven factors and the severe/moderate rule
- [x] FP-EX-001 updated (already asserted "all seven factors"; verified against restored SKILL.md text)
- [x] One eval per previously-omitted factor (impact, reversibility, execution model/coordination, uncertainty, effort) where it alone decides detailed — impact already covered by FP-EX-002 (retagged `impact-alone`); added FP-EX-029..032 for the rest
- [x] Packaging tests green
