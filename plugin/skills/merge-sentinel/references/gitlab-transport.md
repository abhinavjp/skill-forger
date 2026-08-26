# GitLab Transport

## Capability matrix

Build the capability matrix once.

| Operation | MCP | API | browser |
|---|---|---|---|
| `read-metadata` | available | available | available |
| `read-diff` | available | available | available |
| `read-file` | available | available | available |
| `read-discussions` | available | available | available |
| `top-level-note` | available | available | available |
| `reply` | available | available | available |
| `inline-discussion` | available | available | available |
| `resolve` | available | available | available |
| `reopen` | available | available | available |
| `approve` | available | available | available |

## Acquisition

Acquire evidence through the matrix before review.

## Operation routing

Route each operation left-to-right, trying each available layer once. An MCP inline draft is not a published discussion and is unsupported for inline-discussion unless a publish operation also exists. Never silently downgrade a published-discussion request into a draft.

## Freshness

Revalidate remote state and MR head immediately before a final verdict or write.

## Publication ledger

Record every publication attempt and its verification state in the ledger.

## Verification

Read back published remote objects and verify the requested operation completed.
