# Platform adapters

Read this only when a specific host has been selected. Everything here is
**Platform-specific**: useful when targeting that host, never a dependency of
the portable core. Host feature sets change — verify against current host
documentation before relying on any specific field or path, and record the
version you checked.

Portable core = `SKILL.md` + relative resources. Anything below that leaks into
the core is an R22 finding.

## Recording compatibility

Track these four separately, and never collapse them:

```
standards-compatible   — parses and loads under the open Agent Skills format
tested platforms       — hosts where behaviour was actually exercised
untested platforms     — claimed but unverified
known deviations       — where behaviour differs, and how
```

"Parses on multiple hosts" is not "behaves equivalently on multiple hosts".

## Claude Code

- Host-specific frontmatter (for example invocation controls such as
  `disable-model-invocation`, or tool allowlists) stays host-specific — the
  inspector flags these as platform extensions. `disable-model-invocation` is
  the one accepted host-only-field exception in the portable core (R22); the
  inspector notes its `skills-ref validate` failure as informational and
  flags a mismatch against an `openai.yaml` under the skill's `agents` folder
  (its `policy.allow_implicit_invocation` key) as a finding.
- Open bugs affecting this field are deviation evidence only, not spec:
  [#26251](https://github.com/anthropics/claude-code/issues/26251),
  [#78523](https://github.com/anthropics/claude-code/issues/78523),
  [#43875](https://github.com/anthropics/claude-code/issues/43875).
- Hooks enforce invariants deterministically (R15); permissions restrict
  authority (R20).
- Subagents provide context isolation (R16).
- `skill-creator` is **optional supplemental tooling**. Useful pieces: test
  prompt generation, with/without comparison runs, expectation grading,
  execution metrics, and its description-optimisation loop for trigger A/B
  evidence (R3).
  It must not become mandatory, the canonical eval storage, the portable eval
  schema, or the only trigger evaluator — its trigger evaluation has documented
  false negatives, which is exactly why failures need R-classification (see
  `eval-spec.md`).

## OpenAI Codex

- `AGENTS.md` for persistent guidance (R1), Skills for task-scoped workflows.
- Hooks, subagents, sandbox/permission controls, and platform eval tooling.
- Catalog limits matter: descriptions may be truncated and Skills omitted as the
  catalog grows — front-load trigger-critical meaning (R3) and watch R5.

## Cursor

- Rules and Skills are distinct layers (R1); Rules-only frontmatter such as
  `alwaysApply` or `globs` is host-specific.
- Hooks, subagents, MCP/tools, and explicit Skill invocation — evaluate explicit
  invocation separately from implicit routing (R4).

## Google Antigravity

- Skills, Rules, workflows, hooks, subagents, permission controls.
- Treat scripts as executable resources rather than context to load (R13).
- No user-invoked-only switch exists for Skills; the base Agent Skills spec
  defines none here. Disclose "user-invoked" as not enforceable on this host
  and rely on a narrow description instead.

## Factory

- Skills and explicit invocation, similar to Claude Code and Cursor.
- Honours `disable-model-invocation: true` in `SKILL.md` frontmatter directly.

## Adapter shape

When a host feature is genuinely needed, isolate it:

```
adapters/<host>/…      host-specific files, hooks, permissions, runners
```

The core must degrade gracefully without it, or narrow its compatibility claim.
Create an adapter only when a real requirement forces it — an empty or
speculative adapter directory is itself a finding.
