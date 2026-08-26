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

Before code review, read MR metadata and description, all notes, and all discussion pages.
Capture developer replies plus resolved/unresolved and last-updated state. Use this snapshot for
deduplication, re-review decisions, and unresolved-thread gating. If pagination or permissions
prevent complete discussion acquisition, mark discussion coverage partial and do not claim all
threads are clear.

If Jira/spec context was supplied or discoverable within authorized tools, load it before code
through the existing implementation-compliance reference. Do not add Jira mutation operations.

## Operation routing

Route each operation left-to-right, trying each available layer once. An MCP inline draft is not a published discussion and is unsupported for inline-discussion unless a publish operation also exists. Never silently downgrade a published-discussion request into a draft.

## Freshness

Revalidate remote state and MR head immediately before a final verdict or write.

## Publication ledger

Record every publication attempt and its verification state in the ledger.

## Verification

Read back published remote objects and verify the requested operation completed.
