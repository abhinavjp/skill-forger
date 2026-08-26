# Implementation Compliance

## Authority order

1. explicit user instruction for this review
2. formally approved specification or issue amendment
3. issue description and acceptance criteria
4. approved technical plan for implementation detail
5. MR description as declared scope only
6. tests and code as implementation evidence only

## Requirement inventory

Each requirement record contains `id`, `source`, `citation`, `approval`, `text`, `exclusions`, `dependencies`, `non_functional`, and `status`.

Allowed statuses: `implemented`, `partial`, `contradicted`, `missing`, `not-applicable`, and `unverified`.

## Forward trace

Trace every authoritative requirement to implementation evidence or its status.

## Reverse trace

Trace each material implementation change to an authoritative requirement or declared scope.

## Conflict Detected

Any disagreement or unclear approval emits:

```text
Conflict Detected
Sources: <citations>
Conflict: <two incompatible statements>
Affected requirements: <ids>
Implementation consequence: <what cannot be verified>
Decision required: <specific human choice>
```

## Coverage result

Report implementation compliance as unverified when authoritative requirement evidence cannot be obtained.
