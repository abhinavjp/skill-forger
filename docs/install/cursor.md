# Install in Cursor

Use Cursor's Agent Plugins-compatible marketplace route against this repository's root
`plugin.json` (Agent Plugins v1.0.0) and the same `plugin/skills/` payload used by every other
host here. For repeatable GitHub updates, import the repository as a team marketplace, add the
plugin with root `plugin/`, and enable Auto Refresh or use the marketplace's manual Refresh action.
Cursor documents this flow in [Plugins](https://cursor.com/docs/plugins).

Do not create `.cursor/skills/` or `.agents/skills/` inside this repository as a substitute
payload. If your local Cursor build cannot import the repository plugin directly, treat that
route as untested for your build rather than inventing a second authored copy — see Status below.

## Verify

Confirm Cursor discovers `skill-engineer`, `merge-sentinel`, `skill-prospector`, `forge-clarify`,
`forge-discover`, `forge-spec`, `forge-plan`, and `forge-implement`
by their portable frontmatter names, with no second authored copy anywhere, then run through
[verify-installation.md](verify-installation.md).

## Update

Use the team marketplace's manual Refresh action, or enable Auto Refresh with the Cursor GitHub
App installed for this repository. Cursor re-indexes the tracked branch and clients receive the
updated plugin on restart or focus. A direct one-off GitHub import can remain pinned to its
original commit, so do not use that route as the release update mechanism.

## Uninstall

Remove the plugin through Cursor's own plugin-removal command. This only removes Cursor's
installation state; it does not touch the clone.

## Do not also install a standalone copy

Installing the plugin twice, or pairing the plugin route with a hand-placed `.cursor/skills/`
copy, produces duplicate, conflicting Skill entries. Use the plugin import route only.

## Status

The team-marketplace refresh behavior is documented by Cursor, but this repository was not
exercised against a live Cursor build in this implementation session: `UNTESTED: host verification
skipped in this session`. Re-run [verify-installation.md](verify-installation.md) against your
Cursor build before relying on it.
