# 06: Phase gates produce controlled handoffs

**What to build:** Make each detailed phase finish through a bounded evidence and review gate, record an honest handoff, and pause for an explicitly authorized next action.

**Blocked by:** 04: Detailed dependencies expose a safe execution frontier; 05: Risk determines controls and proof.

**Status:** ready-for-agent

- [ ] The gate runs task-local checks, integrated checks, whole-phase review, blocking remediation, affected rechecks, and one final integrated review.
- [ ] Findings are classified blocking, non-blocking, or out-of-scope; clean means required checks pass and zero blocking findings remain.
- [ ] Two non-progressing review loops or material reviewer disagreement stop execution and return control to the user.
- [ ] Handoffs record proof, deviations, non-blocking findings, and unavailable behavior as `UNMEASURED`.
- [ ] A clean detailed phase pauses with only applicable continue, named extra testing, commit, revise, or stop actions; required automation precedes the pause.
- [ ] Commit granularity, approval, and history style are frozen independently with specified compact/detailed defaults; no commit authority implies push, merge, deployment, release, tracker, or implementation authority.
