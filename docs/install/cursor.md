# Install in Cursor

Use Cursor's Agent Plugins-compatible import/plugin route against this repository's root
`plugin.json` (Agent Plugins v1.0.0) and the same `plugin/skills/` payload used by every other
host here. Point Cursor's plugin import at `abhinavjp/skill-forger` with plugin root `plugin/`,
using whatever import command or UI flow your Cursor build documents for a GitHub-sourced
plugin.

Do not create `.cursor/skills/` or `.agents/skills/` inside this repository as a substitute
payload. If your local Cursor build cannot import the repository plugin directly, treat that
route as untested for your build rather than inventing a second authored copy — see Status below.

## Verify

Confirm Cursor discovers both `skill-engineer` and `merge-sentinel` by their portable frontmatter
names, with no second authored copy anywhere, then run through
[verify-installation.md](verify-installation.md).

## Update

Re-run Cursor's plugin update/re-import flow after pulling new commits from
`abhinavjp/skill-forger`.

## Uninstall

Remove the plugin through Cursor's own plugin-removal command. This only removes Cursor's
installation state; it does not touch the clone.

## Do not also install a standalone copy

Installing the plugin twice, or pairing the plugin route with a hand-placed `.cursor/skills/`
copy, produces duplicate, conflicting Skill entries. Use the plugin import route only.

## Status

This route was documented from the frozen planning-phase decision and was not exercised against
a live Cursor build in this implementation session: `UNTESTED: host verification skipped in this
session`. Re-run [verify-installation.md](verify-installation.md) against your Cursor build
before relying on it.
