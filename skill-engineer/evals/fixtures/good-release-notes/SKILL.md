---
name: release-notes
description: Draft release notes from merged pull requests between two git tags. Use when preparing a release announcement, summarising what changed since the last tag, or turning a merge log into user-facing notes.
license: Apache-2.0
---

# Release notes

Turn the merge log between two tags into user-facing notes. The point is that
users care about what changed for them, not about commit hygiene — so group by
user-visible effect, not by author or file.

## Workflow

1. Resolve the range. Default to the two most recent tags; ask if the repo has
   none.
2. Collect merges: `git log <from>..<to> --merges --pretty=%s%n%b`. If that
   returns nothing the repository squash-merges, so use
   `git log <from>..<to> --pretty=%s%n%b` instead.
3. Group into Added / Changed / Fixed / Removed. Drop internal-only changes
   (CI, formatting, dependency bumps with no user effect).
4. Write one line per entry in the user's own product vocabulary.

If the repository declares a release-notes format — a `.release-notes.md`
template, or a changelog section in `CONTRIBUTING.md` — read
`references/house-format.md` and follow it instead of the default grouping.

## Done when

Every user-visible merge in the range appears exactly once, and the notes
mention no internal-only change.
