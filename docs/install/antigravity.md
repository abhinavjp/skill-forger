# Install in Google Antigravity

Antigravity discovers Agent Skills from workspace or global Skill directories. Link each canonical
Skill directory from this repository into one of:

- **Workspace-scoped:** `<project-root>/.agents/skills/`
- **Global:** `~/.gemini/config/skills/`

```bash
git clone https://github.com/abhinavjp/skill-forger.git
ln -s "$(pwd)/skill-forger/plugin/skills/skill-engineer" ~/.gemini/config/skills/skill-engineer
ln -s "$(pwd)/skill-forger/plugin/skills/merge-sentinel" ~/.gemini/config/skills/merge-sentinel
ln -s "$(pwd)/skill-forger/plugin/skills/skill-prospector" ~/.gemini/config/skills/skill-prospector
```

Use workspace-scoped links instead if you only want the Skills available in one project. These
links expose the same canonical Skill directories packaged for Claude Code, Codex, and Cursor;
there is no separately authored Antigravity payload. See Google's
[Antigravity Skills codelab](https://codelabs.developers.google.com/getting-started-with-antigravity-skills)
for the current discovery locations.

## Verify

Confirm `skill-engineer`, `merge-sentinel`, and `skill-prospector` appear from the installed plugin, then run
through [verify-installation.md](verify-installation.md).

## Update

Run `git pull` inside the clone. Because each installed Skill is a link to the clone, Antigravity
picks up the new content without copying or reinstalling it. Restart or reload the host if its
current session has already indexed the previous Skill metadata.

## Uninstall

Delete the three links under `.agents/skills/` or `~/.gemini/config/skills/`. This removes only
Antigravity's installation state and never touches the clone.

## Do not also install a standalone copy

Do not link the Skills at both workspace and global scope for the same project, and do not also
copy them into another Antigravity-scanned directory. Duplicate installation sources produce
duplicate, conflicting Skill entries.

## Status

The discovery locations are documented by Google, but this repository was not exercised against
a live Antigravity build in this implementation session: `UNTESTED: host verification skipped in
this session`. Re-run [verify-installation.md](verify-installation.md) against your Antigravity
build before relying on it.
