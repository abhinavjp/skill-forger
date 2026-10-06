# Changelog

## 3.0.0 — Forge: approval by the user's own words

Major version: the approval model changed, and plans/artifacts made under
2.x do not work with 3.x's Forge skills unchanged (see Migrating below).

### What changed

- **No more approval gates.** The user's own words ("go", "looks good",
  "implement the plan") are approval. There are no approval hashes, approval
  records, or a `workflow_state.py` script deciding this. See the shared
  [workflow contract](plugin/shared/forge/references/workflow-contract.md).
- **forge-discover writes the Goal.** It is now the entry point: it takes the
  user's problem in their own words and writes `## Goal` (problem, outcome,
  done when, not in scope) first in `context.md`. Only the user changes it
  afterward.
- **forge-plan and forge-implement fit together.** forge-plan writes a
  compact `plan.md` or a detailed `phases/` tree using six fixed packet
  headings (`Outcome`, `Write scope`, `Must not change`, `Changes`, `Proof`,
  `Depends on`); forge-implement reads exactly those. forge-implement no
  longer expects `spec.md` + `tasks.md`.
- **Simpler, shorter skills.** Every Forge `SKILL.md` is about 60 lines, each
  step ends "Done when", and "do not" is reserved for hard safety lines
  (never push, never touch someone else's uncommitted changes).
- **All five Forge skills are user-invoked**, not model-invoked: the user
  calls each one by name (`disable-model-invocation: true` in `SKILL.md`,
  paired with `agents/openai.yaml` for Codex). Host support:
  - **Enforced:** Claude Code, Cursor, Factory, OpenAI Codex.
  - **Not enforced:** Google Antigravity — the base Agent Skills spec has no
    Skill-level suppression switch there. Forge relies on a narrow,
    human-facing description instead and discloses this as intent, not a
    guarantee.
  - **Known deviation:** `disable-model-invocation` is outside the open Agent
    Skills spec's allowed frontmatter, so a Forge `SKILL.md` fails
    `skills-ref validate`. This is a disclosed, accepted exception (see R22 in
    `rules-portability.md`), not a defect — the inspector reports it as
    informational rather than an error, and reports a mismatch between the
    two invocation fields as a finding.
  - Three open Claude Code issues affecting this field are recorded as
    deviation evidence only, not spec: #26251, #78523, #43875.
- **`progress.md` replaces `evidence.md`.** One per compact plan, one per
  detailed phase. Checklist per task (`[ ]`/`[~]`/`[x]`/`[!]`) with `check:`,
  `changed:`, `deviation:`, `commit:` lines. Resume starts at the first box
  that is not `[x]`.

### Migrating an existing plan

1. Move the plan under `.forge/<work-item>/` (or your repo's own artifact
   convention) if it is not already there.
2. Add a `progress.md` next to it, following the shared contract's format.
3. Re-run forge-plan if the plan still uses `spec.md` + `tasks.md`, `commit_approval`, or approval-hash language — those are not read by 3.0.0's forge-implement.
