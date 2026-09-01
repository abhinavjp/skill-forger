# Validation state

- frozen candidate: `265e248`
- deterministic validation: PASS, 16/16
- Claude targeted validation: PASS
- Antigravity cross-host validation: PASS
- cross-host behavioural trials: 5/5 PASS
- portable-core blockers: none
- Known non-blocking limitations:
  1. TR-009
     - Claude catalog-routing conflict against `skill-creator`
     - accepted measured result: 3/6 `skill-engineer`, 3/6 `skill-creator`
     - non-blocking because `skill-creator` is optional/platform-specific supplemental tooling, not a mandatory universal dependency
  2. EX-015
     - MIXED adjudication
     - lower-severity R15/R19 false-positive/rule-boundary behaviour
     - no Critical/High false-positive blocker
     - non-blocking
  3. CH-2
     - CREATE/design-level portable-core/host-adapter separation validated
     - actual Antigravity hard-block enforcement was not executed
     - do not claim that it was
- release decision: `RELEASE`
- additional testing required before release: NO
- Overall status: `RELEASE APPROVED`

## Post-release maintenance

Evidence below is post-release maintenance validation, not a rewrite of the
`RELEASE APPROVED` decision above. The frozen `skill-engineer-v1.0.0`
release/tag (candidate `265e248`) is unchanged.

- candidate commit: `9f653e2`
- change scope: R15 portable-core applicability boundary plus artifact-based
  verification in `good-safe-mutation`
- deterministic validation: PASS (already run and recorded at `9f653e2`)
- EX-015 targeted behavioural trial (artifact-comparison verification):
  PASS, single trial — `evals/results/phase1/EX-015.2.result.md`
- EX-014 targeted behavioural trial (R15 hard-block safety control):
  PASS, single trial — `evals/results/phase1/EX-014.2.result.md`
- additional behavioural trials: not justified

## Release 2.2.0 maintenance evidence

Appended, not a rewrite: the frozen `skill-engineer-v1.0.0` decision
(candidate `265e248`) and its `RELEASE APPROVED` status above are unchanged.

- candidate commit: `dca3022`
- change scope: the portable Forge five-stage SDLC suite; the discovered Skill
  catalog grows from three to eight, and packaging validation is extended to
  cover the larger set
- deterministic validation: PASS
  - `python -m pytest plugin/shared/forge/tests packaging` — 79 passed
  - `python packaging/validate_plugin.py` — RESULT: PASS, 26 checks
  - `python plugin/shared/forge/evals/run_static_evals.py` — 7 passed, 0 failed,
    13 skipped for absent host/model capabilities
  - v1 corpus validation — 12 files, 102 cases, 0 errors
- catalog competition, lexical proxy only: max pair overlap 0.280
  (`forge-plan`/`forge-implement`), mean 0.055, via
  `python packaging/measure_catalog_overlap.py`. This is not a routing
  measurement and has no pass/fail threshold.
- Forge host/model trigger routing: `UNMEASURED` — no host trial has been run
  against a recorded eight-Skill catalog snapshot. The procedure is step 7 of
  `docs/install/verify-installation.md`. Do not report these cases as passing
  until that trial is executed.
- TR-009 is unchanged by this release and its recorded 3/6 result still stands.
