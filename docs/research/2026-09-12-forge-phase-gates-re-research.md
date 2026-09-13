# Forge detailed mode: phase gates and commit policy

## Verdict

The proposed phase gate is good, with two corrections:

1. Do not wait for **zero findings**. Wait for **zero blocking findings**. “No findings” creates endless review loops over minor advice.
2. Testing is not a choice offered after review. Required automated checks must pass **before** review. The pause may offer extra manual or exploratory testing.

## What the evidence says

- Anthropic’s AI-native SDLC keeps humans in the loop, uses `intent.md`, `spec.md`, and an approved `plan.md`, puts continuous evals inside implementation, and reserves human review for critical decisions. This supports automated task work plus a human phase boundary. It does not prescribe a pause after every phase. [Anthropic AI-Native SDLC](https://claude.com/blog/the-ai-native-sdlc-playbook)
- Google says a change should be one self-contained idea, include its tests, remain healthy when checked in, and be small enough to review thoroughly. It also says dependent changes may be stacked and reviewed in parallel. This supports small tasks and phase-level integration, but argues against one huge phase diff. [Google: Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html)
- Google says review should cover design, functionality, tests, complexity, and system context. It expects authors to test before review. This supports one integrated phase review after the phase checks pass. [Google: What to look for](https://google.github.io/eng-practices/review/reviewer/looking-for.html)
- Google’s acceptance standard is improved code health, not perfection; non-blocking comments should be marked as such. This directly argues against “repeat until the reviewer finds nothing.” [Google: Review standard](https://google.github.io/eng-practices/review/reviewer/standard.html)
- GitHub says pull requests combine commits, checks, discussion, and review; stacked pull requests can split dependent changes into independently reviewable units. Required checks must pass before merge. This supports task commits or stacked work when tasks are independently meaningful, but does not require either. [GitHub: Pull requests](https://docs.github.com/en/pull-requests/get-started/about-pull-requests), [GitHub: Status checks](https://docs.github.com/en/pull-requests/reference/status-checks)
- Fowler’s continuous-integration guidance says frequent integration and self-testing reduce integration risk; long-lived branches allow conflicts to grow. This argues against waiting until the whole project ends to create any useful checkpoints. [Martin Fowler: Continuous Integration](https://martinfowler.com/articles/continuousIntegration.html), [Branching Patterns](https://martinfowler.com/articles/branching-patterns.html)
- OpenAI describes agents working in small building blocks, reviewing their own work, receiving specialist reviews, fixing findings, and re-reviewing. This supports a review/fix loop, but not an unlimited hunt for nits. [OpenAI: Harness engineering](https://openai.com/index/harness-engineering/)
- OpenAI’s Codex safety guidance uses bounded autonomy: low-risk work can proceed, while higher-risk actions stop for review. Its system card describes showing diffs and logs so users can validate changes before commit. This supports an explicit commit policy and human approval where the user wants control. It does not prove every local commit must always require approval. [OpenAI: Running Codex safely](https://openai.com/index/running-codex-safely/), [Codex system card](https://cdn.openai.com/pdf/8df7697b-c1b2-4222-be00-1fd3298f351d/codex_system_card.pdf)

## Recommended detailed-mode workflow

For each vertical phase:

1. Execute its task files in dependency order; run independent tasks in parallel.
2. Run each task’s narrow checks while implementing.
3. Run the phase integration gate: focused tests, type/lint/build checks, acceptance checks, and diff/scope checks.
4. Review the **whole phase** against intent, plan, architecture, security, regressions, and maintainability.
5. Classify findings as `blocking`, `non-blocking`, or `out-of-scope`.
6. Fix blocking findings. Re-run affected checks, then one clean phase review. Repeat only while blocking findings remain.
7. Write a compact phase handoff: outcome, changed files, checks, remaining non-blocking notes, deviations, and next phase.
8. Pause for the user’s decision: continue, run extra testing, commit if not already committed, revise, or stop.

Required checks happen before the pause. “Test the phase” at the pause means **additional** manual, browser, hardware, live-provider, performance, or user-acceptance testing.

## Commit policy to decide during planning

Record two separate fields in `plan.md`:

```yaml
commit_granularity: task | phase | end | none
commit_approval: always_ask | preapproved
history_style: separate | fixup_then_squash | squash
```

Recommended default for detailed mode:

```yaml
commit_granularity: phase
commit_approval: always_ask
```

Why: a clean phase is a useful recovery and review unit; asking protects user control. A commit must never imply push, merge, release, or deployment permission.

- `task`: use for independently revertible tasks, stacked PRs, risky migrations, or long phases. Bad default because it creates noisy history and can preserve broken intermediate states.
- `phase`: best general default. One vertical, verified outcome per commit.
- `end`: acceptable for small work. Bad for long work because recovery, review, bisecting, and integration become harder.
- `none`: use when the user owns Git history or the workspace has unrelated changes.

If `preapproved`, the agent may commit only when the configured gate is clean. It must still pause after the phase. If `always_ask`, it pauses before every commit. Never silently change the policy mid-run.

Stop and ask the user if repeated reviews disagree or two consecutive review loops make no progress.

## Goods

- Phase review sees integration problems that task-by-task review misses.
- Small task files constrain context and improve execution accuracy.
- A human pause prevents the agent from carrying a wrong design across later phases.
- A declared commit policy removes repeated ambiguity.
- Phase commits create useful recovery points without one commit per tiny edit.

## Bads

- A mandatory pause after every small phase slows routine work. Let the plan group tiny slices or preapprove continuation for low-risk phases.
- Phase-only review can produce a large diff. Add a maximum review budget; split a phase when a reviewer cannot understand it in one pass.
- Re-reviewing the entire phase after every fix wastes tokens. Re-run affected checks after each fix; run the full review once the blocking set is closed.
- Separate task files save tokens only if they reference shared contracts instead of copying them.

## Uglies

- “No findings” is a perfection trap. Reviewers can always invent another nit.
- “Test or continue?” is unsafe if basic tests have not run. Passing required checks is a gate, not a menu option.
- Automatic per-task commits can capture partial or failing work and pollute history.
- End-only commits create a giant unreviewable change and weak recovery points.
- A clean AI review is evidence, not proof. Live services, user experience, security, migration safety, and production behaviour may remain unmeasured.

## Add to `intent.md`

- Define a phase as a reviewable vertical outcome, not a technical layer.
- Define the exact gate and finding severity rules above.
- State that exit means zero **blocking** findings and all required checks pass.
- Add the phase pause and its allowed choices.
- Add `commit_granularity` and `commit_approval` as planning decisions, with phase/always-ask defaults.
- Separate commit authority from push, merge, deploy, and release authority.
- Add a phase size guard: if the integrated diff is not reviewable in one focused pass, split it before execution.
- Track unmeasured evidence explicitly; never convert “not tested” into “passed.”
- Require simple English and prohibit duplicated context across `plan.md`, phase files, and task files.

## Remove or avoid

- “Review until there are no findings.”
- Optional basic testing after review.
- Review after every task by default.
- Automatic commits without a plan-level policy.
- Repeating full requirements and research in every task file.

## Applicability limit

These sources support small healthy changes, continuous tests, explicit gates, and bounded human approval. The exact Forge phase protocol is a design recommendation derived from them, not a standard published by Google, GitHub, Fowler, Anthropic, or OpenAI. Its live token savings and defect rate are **UNMEASURED** until tested on real projects.
