# Forge knowledge-provider contract

A knowledge provider is optional transport behind a host-neutral selection
result:

```text
knowledge result
  selected_references: leaf references used by the artifact
  selection_reason: why each reference is material
  hashes_freshness: content hash/version and observation freshness when available
  unavailable_knowledge: requested but unreadable or missing knowledge, with reason
  validation_result: PASS, FAIL, or UNMEASURED evidence and reason when unmeasured
```

Load and cite only selected leaf references; a container, catalogue, or parent
path is not itself selected knowledge. Do not require OKF, a particular
transport, or a provider implementation. Unavailable knowledge must remain
explicit and may not be represented as `PASS`. Keep provider payloads out of
active context unless their material content is used. The selected hashes and
freshness observations participate in the workflow contract's source-freshness
rules.
