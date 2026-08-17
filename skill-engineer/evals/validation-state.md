# Validation state

- Portable candidate: `265e248` (previous candidate: `b1744f3`)
- Harness revision: `2331f2c`
- Candidate change reason: Cross-platform absolute-path classification fix reproduced on Antigravity/Windows
- Claude Phase-1 status: see `evals/results/phase1/SUMMARY.md`
- Deterministic status: 16/16 PASS (`python evals/run_static_evals.py`)
- RG-004: PASS on Windows after fix (previously FAIL on Antigravity/Windows — OS-dependent `os.path.isabs()` misclassified POSIX absolute paths)
- RG-011: PASS — new regression proving absolute-path classification is OS-independent (`PurePosixPath`/`PureWindowsPath`), covering POSIX, Windows drive-absolute, and Windows UNC paths, while a genuine missing relative reference still reports broken
- EX-015 adjudication status: MIXED / non-blocking — see `evals/results/phase1/EX-015.1.result.md`
- TR-009: accepted known Claude routing FAIL — see `evals/cross-host-validation-plan.md` §2 (Layer B)
- RG-001 pollution issue: RESOLVED as harness hygiene — see `evals/regressions.yaml` (RG-001)
- RG-010: regression protecting the corrected boundary — see `evals/regressions.yaml` (RG-010), `evals/fixtures/defective-eval-evidence-boundary/`
- Behavioural Claude evidence remains reusable: no routing/rules/CREATE/REVIEW prompt behaviour changed by this candidate — the fix is confined to `scripts/inspect_skill.py`'s deterministic path classification
- Cross-host model calls used: 0/5
- CH-1..CH-5: UNMEASURED
- Antigravity behavioural calls used: 0/5
- Previous Antigravity Stage 0 failure (RG-004 FAIL, POSIX-absolute-path misclassification): RESOLVED by candidate `265e248` — must be rechecked on Antigravity (Stage 0) before any behavioural execution resumes
- Current cross-host status: `READY — BLOCKED ON INDEPENDENT HOST`
- No portable-core blocker currently known
