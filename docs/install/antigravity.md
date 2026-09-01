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
ln -s "$(pwd)/skill-forger/plugin/skills/forge-clarify" ~/.gemini/config/skills/forge-clarify
ln -s "$(pwd)/skill-forger/plugin/skills/forge-discover" ~/.gemini/config/skills/forge-discover
ln -s "$(pwd)/skill-forger/plugin/skills/forge-spec" ~/.gemini/config/skills/forge-spec
ln -s "$(pwd)/skill-forger/plugin/skills/forge-plan" ~/.gemini/config/skills/forge-plan
ln -s "$(pwd)/skill-forger/plugin/skills/forge-implement" ~/.gemini/config/skills/forge-implement

# Required by the five forge-* Skills: the portable shared core they reference.
ln -s "$(pwd)/skill-forger/plugin/shared" ~/.gemini/config/shared
```

Use workspace-scoped links instead if you only want the Skills available in one project. These
links expose the same canonical Skill directories packaged for Claude Code, Codex, and Cursor;
there is no separately authored Antigravity payload. See Google's
[Antigravity Skills codelab](https://codelabs.developers.google.com/getting-started-with-antigravity-skills)
for the current discovery locations.

### The forge-* Skills need the shared core alongside them

The five `forge-*` Skills reference `../../shared/forge/` for their workflow
contract, which owns every gate, approval, and mutation-safety rule. Under the
plugin route that tree ships inside the plugin and resolves automatically. Under
this per-Skill link route it does not, so the `shared` link above must sit one
level *above* the Skills directory — pair `<skills-dir>/forge-spec` with
`<skills-dir>/../shared`. Link the whole set or none of it: linking a `forge-*`
Skill without the shared core leaves its safety contract unreachable.

If your host resolves `..` through the link target rather than lexically, the
shared link is redundant but harmless. Which behaviour your build has is
`UNMEASURED` until you check it during
[verify-installation.md](verify-installation.md) step 9.

## Verify

Confirm `skill-engineer`, `merge-sentinel`, `skill-prospector`, `forge-clarify`,
`forge-discover`, `forge-spec`, `forge-plan`, and `forge-implement` appear
from the installed plugin, then run through
[verify-installation.md](verify-installation.md).

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
