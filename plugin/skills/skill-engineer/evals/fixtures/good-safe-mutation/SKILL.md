---
name: release-ledger
description: Record a shipped release in the team's release ledger. Use after a release has been tagged and published, when adding an entry to ledger.json, or when the ledger is missing releases that already shipped.
license: Apache-2.0
---

# Release ledger

Append one entry per shipped release to `ledger.json` at the repository root.
The ledger is the audit record other teams query, so a missing entry and a
duplicated entry are both incidents.

## Before writing

1. Read `ledger.json`. If it does not exist, create it as `{"releases": []}`.
2. Confirm the tag actually exists: `git tag --list <tag>` must return it. A
   ledger entry for a tag that was never pushed is worse than a missing one.
3. Search the ledger for an entry whose `tag` equals this tag.

The tag is the entry's identity. If an entry for it already exists, update that
entry in place and say so — never append a second one. Re-running this Skill on
a release that is already recorded must leave the ledger byte-identical apart
from any field whose value genuinely changed.

## Write

Append or update a single object:

```json
{"tag": "v2.4.0", "shipped": "2026-08-16", "artifacts": ["pkg-2.4.0.tgz"]}
```

Write the whole file once, from the structure you read in step 1. Do not
hand-edit surrounding lines: a partial write leaves the ledger unparseable for
everyone else.

## Verify

Before writing, keep the exact serialized text you read for every entry other
than the one you are adding or updating. After writing, read the file back and
compare that kept text, character for character, against the same entries in
the new file. Any difference is a failure — the byte-identical invariant does
not hold until this comparison passes.

## When something fails

- `ledger.json` does not parse → stop and report it. Do not overwrite a file
  you could not read; the existing entries are the thing worth protecting.
- The write fails because the file is locked → retry twice, then stop and
  report. Never loop until it succeeds.
- The tag does not exist → stop. This is not transient and retrying cannot fix
  it.

Report the failure with the ledger left as you found it, not a summary that
implies the entry was recorded.

## Permissions

This workflow reads and writes exactly one file, `ledger.json`, and runs one
read-only git command. It needs no network access, no credentials and no write
access anywhere else — scope it that way if the host lets you.

## Done when

`ledger.json` parses, contains exactly one entry for the tag, every entry
that was there before is still there, and the serialized representation of
every pre-existing entry is character-for-character unchanged from its
pre-write representation.
