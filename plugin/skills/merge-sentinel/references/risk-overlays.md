# Risk Overlays

| Domain | Trigger |
|---|---|
| auth/authorization | authentication, permission, role, policy, token, session |
| tenancy | tenant/company/account scope or tenant identifiers |
| privacy/secrets | personal data, credentials, logging, encryption |
| concurrency/transactions | shared mutation, retry, lock, transaction, async race |
| migrations/dependencies | schema migration, package/configuration change |
| shared APIs | contract, DTO, serialization, public method, event |
| performance | looped I/O, unbounded query/list, hot-path allocation |
| accessibility/UI | interactive UI, keyboard/focus, labels, state feedback |
| deployment | environment variables, feature flags, rollout, rollback |

For an activated domain, require one concrete invariant, one failure path, and counterevidence. Activate only from operative code or change evidence; comments and fixture data do not activate an overlay.

A tenant-escape invariant applies when changed code removes or bypasses an authenticated tenant,
company, or account predicate on data access. Treat a proven cross-tenant read or mutation as
`blocker` unless a supplied local policy defines a stricter or explicitly different severity.
