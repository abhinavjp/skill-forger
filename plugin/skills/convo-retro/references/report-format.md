# Report format

Open with one line: sources used, `self-review` or not, `partial` or not.

Then up to 7 candidates, ranked by **cost times recurrence**: how much the
friction cost (tool calls, retries, user corrections, time) multiplied by how
likely it is to happen again. A signal seen in several sessions outranks a
one-off of equal cost.

Each candidate:

```
N. <title>
   Signal:   <what happened> (<locator>; one quoted line at most)
   Rung:     check | reviewer standard | pointer | tool/access | prune
   Tag:      apply alone, confirm first   (rung writes hook, CI, or lint config)
   Change:   <exact file and exact line, rule, or check to add or remove>
   Load:     <lines added to always-loaded files, and which line is removed>
   Dry run:  <hits on the current tree, and false-positive risk> | not run: <reason>   (checks only)
   Verify:   <how to see the friction is gone next run>
```

Rules:

- No candidate without a locator. List dropped signals in one closing line.
- A check that hits good code today is reported with its hits, not hidden.
- Net load: a line added to an always-loaded file names a line to delete, or
  says why the load is worth it.
- End with: "Say which numbers to apply."
