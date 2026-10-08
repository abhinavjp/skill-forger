# 04: Detailed dependencies expose a safe execution frontier

**What to build:** Make detailed plans express cohesive vertical phases and only genuine blocking edges so coordinators can see all work that is safe to start without artificial serialization.

**Blocked by:** 03: Detailed work produces traceable execution packets.

**Status:** ready-for-agent

- [ ] Phase boundaries follow cohesive behavior, one-pass reviewability, and independent reversibility rather than repository layers or numeric thresholds.
- [ ] Every dependency is a real start-blocking edge, and the executable frontier contains every task whose dependencies are complete.
- [ ] Enabling work is allowed only when it unlocks a named working phase; normal phases leave the system working.
- [ ] Independently deployable or reversible outcomes are split.
- [ ] Unsafe non-atomic boundaries use expand-migrate-contract sequencing while keeping viable intermediate states.
- [ ] Behavioral tests cover wide cohesive changes, false-edge rejection, valid parallel frontiers, and mixed-version sequencing.
