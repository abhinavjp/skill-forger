# Install in OpenAI Codex

The primary, reusable route is Codex's Agent Plugin/plugin distribution mechanism against this
repository's root `plugin.json` schema (`packaging/plugin.schema.1.0.0.json`,
Agent Plugins v1.0.0) plus `plugin/skills/`. Use whatever plugin-install command your Codex
build documents for adding a plugin from a GitHub source, pointed at `abhinavjp/skill-forger`
with plugin root `plugin/`.

## If your Codex build cannot consume the repository directly

Some Codex builds only discover Skills placed under a user-level Skills directory rather than
through the plugin route above. If that is the case for your build, create a **derived, local**
link — never a second authored copy, and never something committed back to this repository:

```bash
git clone https://github.com/abhinavjp/skill-forger.git
ln -s "$(pwd)/skill-forger/plugin/skills/merge-sentinel" <codex-skills-dir>/merge-sentinel
ln -s "$(pwd)/skill-forger/plugin/skills/skill-engineer" <codex-skills-dir>/skill-engineer
ln -s "$(pwd)/skill-forger/plugin/skills/skill-prospector" <codex-skills-dir>/skill-prospector
```

Replace `<codex-skills-dir>` with the user-level Skills directory your Codex build documents.
This link is host-owned installation state: it lives outside the clone, is not tracked by Git,
and is safe to delete and recreate at any time.

## Verify

Confirm Codex discovers `skill-engineer`, `merge-sentinel`, and `skill-prospector` by name, then run through
[verify-installation.md](verify-installation.md).

## Update

Re-run the plugin update command for the plugin route, or re-clone/`git pull` and recreate the
derived link for the standalone-link fallback. Either way, the installed Skill content always
traces back to the same `plugin/skills/` tree at the commit you last pulled.

## Uninstall

Remove the plugin through Codex's own plugin-removal command, or delete the derived symlinks for
the fallback route. Neither action touches the `abhinavjp/skill-forger` clone itself.

## Do not also install a standalone copy

Do not use both the plugin route and the derived-link fallback for the same Codex installation.
Running both at once registers the same Skill under two sources and produces duplicate,
conflicting Skill entries.

## Status

This route was documented from the frozen planning-phase decision and was not exercised against
a live Codex build in this implementation session, to avoid mutating this session's own host
configuration: `UNTESTED: host verification skipped in this session`. Re-run
[verify-installation.md](verify-installation.md) against your Codex build before relying on it.
