# Install in Claude Code

Claude Code consumes the `skill-forger` marketplace directly from GitHub. It reads
`.claude-plugin/marketplace.json` at the repository root and `plugin/.claude-plugin/plugin.json`
inside the plugin, then loads all three Skills straight from `plugin/skills/`. There is no build step
and no separate authored copy — the plugin payload is the same `plugin/skills/` tree used by
every other host in this repository.

## Add the marketplace and install the plugin

```bash
claude plugin marketplace add abhinavjp/skill-forger
claude plugin install skill-engineer@skill-forger
```

`skill-engineer` is the plugin identity (see `plugin/plugin.json`); it packages
`skill-engineer`, `merge-sentinel`, and `skill-prospector` under Claude's plugin namespace.

## Verify

```bash
claude plugin list
```

Confirm `skill-engineer@skill-forger` is installed and all three Skills are discoverable, then run through
[verify-installation.md](verify-installation.md).

## Update

```bash
claude plugin marketplace update skill-forger
claude plugin update skill-engineer@skill-forger
```

Pulling a new commit from `abhinavjp/skill-forger` and re-running the update command changes the
installed version — there is nothing else to sync.

## Uninstall

```bash
claude plugin uninstall skill-engineer@skill-forger
claude plugin marketplace remove skill-forger
```

Uninstalling removes only Claude Code's own installation state. It never touches your clone of
`abhinavjp/skill-forger`.

## Status

This route was documented from the frozen planning-phase decision and was not exercised against
a live Claude Code build in this implementation session: `UNTESTED: host verification skipped in
this session`. Re-run [verify-installation.md](verify-installation.md) against your Claude Code
build before relying on it.

## Do not also install a standalone copy

Do not additionally place `skill-engineer` or `merge-sentinel` under a personal
`.claude/skills/` directory, or link them there by hand. Claude Code would then discover the
same Skill twice — once through the plugin, once through the standalone copy — which produces
duplicate, conflicting Skill entries. Use the plugin route only.
