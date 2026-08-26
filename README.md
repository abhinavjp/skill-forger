# skill-forger

*Forges Agent Skills. Catches the forgeries.*

An agent-agnostic plugin for engineering Agent Skills and reviewing merge
requests, built around the repository's `SKILL_ENGINEERING_SPEC.md` and a
deterministic review toolkit.

## Canonical payload

`plugin/skills/` is the only authored skill tree. Host manifests and installers point to it or
derive host-owned installation links/copies from it. Generated host copies are never committed.

The plugin includes:

- [skill-engineer](plugin/skills/skill-engineer/SKILL.md) — creates and reviews
  Agent Skills, including trigger design, safety, portability, and eval coverage.
- [merge-sentinel](plugin/skills/merge-sentinel/SKILL.md) — reviews merge
  requests and local diffs for defects, regressions, security risks, unsafe
  scope, and implementation completeness.

Each complete Skill package—including runtime references, scripts, agents
metadata, and canonical eval inputs—lives beneath its canonical directory.
Generated per-Skill `evals/results/` directories are ignored and never packaged.

## Install

One repository payload, four host adapters. The skills are authored once under
plugin/skills/. Claude Code, OpenAI Codex, Cursor, and Google Antigravity use that same
payload through their supported plugin or skill installation route. Manifest and install
commands differ by host; skill content does not.

- [Claude Code](docs/install/claude-code.md)
- [OpenAI Codex](docs/install/openai-codex.md)
- [Cursor](docs/install/cursor.md)
- [Google Antigravity](docs/install/antigravity.md)
- [Verify an installation](docs/install/verify-installation.md)

Do not install the same Skill through two routes on the same host at once — it produces
duplicate, conflicting Skill entries. Each guide states its route's own uninstall step.

## Validate the plugin

```bash
python packaging/validate_plugin.py
```

This validates both manifests, the exact two-Skill layout, unique frontmatter
names, reference resolution and path containment, portable-core checks, and
the absence of tracked host mirrors.

The Skill engineering static corpus remains available at:

```bash
python plugin/skills/skill-engineer/evals/run_static_evals.py
```

It requires Python 3.8+ and PyYAML for YAML cases. Where a host cannot run
Python or scripts, `skill-engineer` reports those checks as unvalidated rather
than claiming they passed.

Inspect any Skill package directly:

```bash
python plugin/skills/skill-engineer/scripts/inspect_skill.py <skill-dir>
```

## Build an optional distribution copy

The repository plugin tree is already installable. To produce an ignored,
unchanged distribution copy without generating host mirrors:

```bash
python packaging/build_plugin.py --out dist/skill-engineer
```

The command only writes beneath `dist/`, refuses to overwrite an existing
output, and never modifies the canonical `plugin/skills/` tree.
