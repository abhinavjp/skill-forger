# Verify an installation

Run this checklist after installing through a host guide
([Claude Code](claude-code.md), [OpenAI Codex](openai-codex.md), [Cursor](cursor.md),
[Antigravity](antigravity.md)). The checks are shared; invocation, delivery and
explicit-only controls are host-specific and must not be inferred from another host.

1. **Record the trial snapshot.** Write down host and version, model, delivery
   route, visible Skill catalog, and the date. Mark unavailable catalog or native
   runners `UNMEASURED`.
2. **Only one installation source is enabled.** Use exactly one route for this
   host, not the plugin route and a standalone copy together.
3. **All eight user-facing Skills are discoverable.** Confirm the host lists
   or can invoke `skill-engineer`, `merge-sentinel`, `skill-prospector`,
   `forge-clarify`, `forge-discover`, `forge-spec`, `forge-plan`, and
   `forge-implement`. `plugin/shared/forge/` is portable shared core material,
   not a user-facing Skill.
4. **Positive project-audit trigger.** Ask: "audit our conventions and tell me
   what should be a Skill". Confirm `skill-prospector` activates and records a
   plan, without authoring a candidate Skill.
5. **Near-neighbour negative trigger.** Ask for direct creation of a new Skill
   from notes, without auditing existing guidance. Confirm this routes to
   `skill-engineer`, not `skill-prospector`.
6. **Existing-Skill review boundary.** Ask to review a `SKILL.md` for broken
   references or trigger problems. Confirm this routes to `skill-engineer`, not
   `skill-prospector`.
7. **Forge stage routing under the real catalog.** With all eight Skills
   installed, capture a catalog snapshot first (host, model, date, and the list
   of Skills the host reports as routable), then run each `competing-skill` and
   `boundary` case in `plugin/skills/forge-*/evals/trigger.json` for the number
   of `trials` it declares. Record which candidate won each trial, not just
   pass/fail. A case whose `required_candidates` were not all present and
   routable in the snapshot is `UNMEASURED: catalog-preconditions-absent` — the
   value its `unmeasured_if` already declares — never a pass.

   The highest-competition pair is `forge-plan` versus `forge-implement`; their
   discriminator is whether a Plan exists yet. `FP-T-004` and `FI-T-001`
   through `FI-T-004` are the cases that settle it. Rank the catalog first with
   `python packaging/measure_catalog_overlap.py` to see which other pairs are
   worth extra trials.
8. **Contained scan smoke.** In an isolated target, place one guidance file
   inside the root and a secret file outside it. Run the project-guidance audit;
   confirm no outside content appears, no inventory or candidate directory is
   written, and exactly one authorised plan path is written. Record the observed
   path/line evidence or the exact failure.
9. **Invocation and delivery status.** Record each candidate policy as
   `automatic`, `both`, or `explicit-only-required`. Test the host's native
   explicit route where available; otherwise record `UNMEASURED` or
   `not-enforceable-portably`. Never promote an unrun trigger or competition
   case to pass.
10. **Relative references and scripts load from the installed Skill root.** Run
   `shared/forge/evals/run_static_evals.py --json` from the installed Skill
   root, record its actual result, and confirm `references/*.md` and
   `scripts/*.py` resolve from the installed location without a path error.
11. **Updating the source changes the installation.** Pull a new commit, run
    the host update step, and confirm the host reflects that commit.
12. **Uninstall preserves the clone.** Run the host uninstall step and confirm
    the Skills are no longer discoverable while the source clone is untouched.

Record every result per host and model. A missing host executable, isolated test
surface, catalog precondition, or native trigger runner is `UNMEASURED: <reason>`,
never a pass. Keep standards compatibility, tested behavior, unmeasured
behavior, and known deviations as separate entries.

## Coverage boundaries

Portable deterministic and static coverage belongs to this repository; run its
available validation commands and record their actual results here. That
coverage does not establish runtime parity for an external Brain adapter.

External Brain runtime parity is `UNMEASURED` until it is run in the owning
Brain repository. Host/model trials are separate from portable coverage and
remain `UNMEASURED` for each host and model combination until that trial is
executed.
