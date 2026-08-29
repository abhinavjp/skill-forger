# Emitted plan format

The plan is one Markdown document. Keep these top-level headings stable; the
static completion check uses them as an artefact contract:

1. `## Run summary`
2. `## Target and authority`
3. `## Discovery inventory`
4. `## Candidates`
5. `## Rejected and deferred units`
6. `## Host adaptation`
7. `## Capabilities not exercised`
8. `## Follow-up`

The document may have a title and subheadings below these headings, but it is
incomplete when any required heading is absent.

## Candidate block

Under `## Candidates`, give each accepted candidate a `### Candidate: <id>`
block containing these fields, in this order:

```text
id:
name:
boundary:
trigger:
sources:
proposed mechanism:
portable invocation:
host enhancements:
dependencies:
eval outline:
acceptance criteria:
```

`boundary` is one sentence. `sources` contains evidence citations in
`path:heading` form, with line spans when a slice was used. `proposed mechanism`
includes the `skill-engineer` CREATE result and its justification; it is not a
new copy of that Skill's rules. `host enhancements` is optional per detected
host and must retain the status `enforced`,
`enforced-with-known-deviation`, or
`not-enforceable — description discipline only`.

## Inventory terminal states

The inventory table must include every `matched_units[].path` exactly once and
assign exactly one terminal state:

| State | Meaning |
|---|---|
| `covered-by-candidate:<id>` | Evidence is covered by the named accepted candidate |
| `stays-as-<mechanism>` | Leave it in its current or routed mechanism |
| `deferred` | Candidate work is over the cap or needs more evidence |
| `unreadable` | The scanner recorded an error and classification cannot proceed |

## Run accounting

`## Run summary` records target root, output path, discovery mode, scanner
inventory source, slice count, candidate count and rejected-with-reason count.
`## Target and authority` records explicit plan-path confirmation and the
one-write boundary. `## Capabilities not exercised` lists every degraded or
unavailable capability, including host runners and Layers B/D when they have
not run. Do not call a partial run complete.
