# Validation state

- Portable candidate: `b1744f3`
- Harness revision: `2331f2c`
- Claude Phase-1 status: see `evals/results/phase1/SUMMARY.md`
- Deterministic status: 15/15 PASS (`python evals/run_static_evals.py`)
- EX-015 adjudication status: MIXED / non-blocking — see `evals/results/phase1/EX-015.1.result.md`
- TR-009: accepted known Claude routing FAIL — see `evals/cross-host-validation-plan.md` §2 (Layer B)
- RG-001 pollution issue: RESOLVED as harness hygiene — see `evals/regressions.yaml` (RG-001)
- RG-010: regression protecting the corrected boundary — see `evals/regressions.yaml` (RG-010), `evals/fixtures/defective-eval-evidence-boundary/`
- Cross-host model calls used: 0/5
- CH-1..CH-5: UNMEASURED
- Current cross-host status: `READY — BLOCKED ON INDEPENDENT HOST`
- No portable-core blocker currently known
