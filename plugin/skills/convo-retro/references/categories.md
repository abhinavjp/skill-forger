# Fix ladder and categories

Pick the highest rung that fits the signal. Higher rungs fail loudly; lower
rungs depend on an agent reading and obeying text.

1. **Automated check**: lint rule, type rule, test, hook, CI job, filesystem
   linter. Fails deterministically.
2. **Reviewer standard**: a rule in the repo's review-standards doc
   (`CODING_STANDARDS.md`, `CONTRIBUTING`, an ADR), read at review time.
3. **Navigation pointer**: one line in a steering file or doc the agent
   already reads, pointing at the file or fact.
4. **Tool or access change**: cheaper tool, wider read access.
5. **Prune**: delete or shrink steering text.
6. **Nothing**: a one-off, or a fix that costs more than the friction.

## Why standards go to review, not implementation

The implementing agent carries the most context pressure: exploring, writing,
debugging. The reviewer sees only a diff and has room to apply rules. So
mechanical rules become checks, and judgement calls become review standards.
Neither belongs in an always-loaded steering file.

## Categories

- **Navigation**: the agent took long to find a file or fact, or missed a
  hidden dependency between files. _Fix:_ a navigation pointer in a file it
  already read.
- **Automated check**: the agent made a mistake a check could catch.
  Read the repo's own check command and CI first. An existing check that is
  unwired or silently broken is the finding, not a new check. A repo with no
  pre-commit hook and no CI job running lint, types, or tests is itself a
  finding. _Fix:_ wire the existing check, or add the cheapest new one.
- **Reviewer standard**: the reviewer missed something. Classify first. A
  fixed syntactic pattern, banned API, import shape, or file-location rule is
  mechanical: build the check. Cross-file consistency or "match the
  surrounding style" is a judgement call: write the standard.
- **Steering-file pruning**: a steering file is large, or a line changes no
  behaviour (delete the line, ask whether the agent would act differently).
  Steering files that load every session should hold pointers only. This
  covers the repo's file and the user's global one.
- **Tool economy**: an expensive or low-yield tool call, or a token-heavy
  custom CLI or MCP tool. _Fix:_ narrow, replace, or batch it.
- **Information access**: a crucial fact was out of reach (dev-server logs,
  a read-only view of a third-party service). _Fix:_ widen access, read-only.

## Not a retro fix

A line that says "remember X happened" is memory, not setup. Change the
environment so X cannot recur, or leave it.
