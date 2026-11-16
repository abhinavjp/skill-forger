# 05: Risk determines controls and proof

**What to build:** Add explainable phase risk classification and only the review, recovery, operational, and proof controls warranted by each boundary.

**Blocked by:** 03: Detailed work produces traceable execution packets.

**Status:** ready-for-agent

- [ ] Every phase is classified low, medium, or high with reasons.
- [ ] High-risk and enumerated security, permission, privacy, compliance, irreversible migration, data-loss, and recovery-critical boundaries require independent review.
- [ ] Task-level semantic review appears only for irreversible, security-critical, or unusually uncertain steps.
- [ ] Rollback, idempotency, observability, compatibility, and security controls appear only when their triggering risks exist.
- [ ] Manual, browser, hardware, migration, performance, live-provider, security, or UAT proof is required only where automation cannot cover the risk.
- [ ] Tests prove both required controls and absence of checklist theater on low-risk work.
