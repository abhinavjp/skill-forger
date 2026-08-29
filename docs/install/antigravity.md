# Install in Google Antigravity

Antigravity reads a plugin's root `plugin.json` plus its `skills/` tree from a workspace or
global plugin location; it does not need a separate Antigravity-specific payload. Place or link
this repository's `plugin/` directory — unchanged — as derived installation state at one of:

- **Workspace-scoped:** `.agents/plugins/skill-forger` or `_agents/plugins/skill-forger`
  (whichever your workspace convention uses), pointed at this clone's `plugin/` directory.
- **Global:** `~/.gemini/config/plugins/skill-forger`, pointed at this clone's `plugin/`
  directory.

```bash
git clone https://github.com/abhinavjp/skill-forger.git
ln -s "$(pwd)/skill-forger/plugin" ~/.gemini/config/plugins/skill-forger
```

Use a workspace-scoped link instead of the global one if you only want the plugin available in
one project. Either way, the link points at the same `plugin/` tree Claude Code, Codex, and
Cursor use — there is no separate Antigravity payload to build or maintain.

## Verify

Confirm `skill-engineer`, `merge-sentinel`, and `skill-prospector` appear from the installed plugin, then run
through [verify-installation.md](verify-installation.md).

## Update

`git pull` inside the clone. Because the plugin location is a link to the clone, Antigravity
picks up the new commit immediately; no reinstall step is required.

## Uninstall

Delete the link under `.agents/plugins/`, `_agents/plugins/`, or `~/.gemini/config/plugins/`.
This removes only Antigravity's installation state and never touches the clone.

## Do not also install a standalone copy

Do not link the plugin at both a workspace-scoped and the global location for the same project,
and do not additionally copy the Skills into another Antigravity-scanned directory. Duplicate
installation sources produce duplicate, conflicting Skill entries.

## Status

This route was documented from the frozen planning-phase decision and was not exercised against
a live Antigravity build in this implementation session: `UNTESTED: host verification skipped in
this session`. Re-run [verify-installation.md](verify-installation.md) against your Antigravity
build before relying on it.
