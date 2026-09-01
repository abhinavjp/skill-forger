# Failure recovery

Use the shared workflow state for retry, blocking, resume, and check status.
Preserve evidence; never hide a failure by broadening scope, changing history,
or relabeling it as passing.

| Event | Required transition and action |
| --- | --- |
| Current packet verification fails | Record `FAIL`, keep the packet unverified, exclude its work from commits, and diagnose only inside its authorized scope. |
| Pre-existing unrelated check fails | Record it separately as baseline evidence; do not attribute it to the packet or edit unrelated work. |
| Transient failure | Record classification and attempt count. Retry only while `can_retry` permits it and the configured bound remains. |
| Deterministic failure | Do not retry until a relevant input, implementation state, or authorized correction changes; record that change before retrying. |
| Unknown failure class | Do not retry implicitly. Classify from evidence or leave the packet failed/blocked. |
| Plan/reality contradiction | Record it, block the affected packet and all transitive dependants, and return the frontier upstream. Do not replan. |
| Independent ready packet | Continue only when its dependencies, gates, scope, and baseline isolation remain valid. |
| Required unplanned scope | Stop before its write. Request explicit authorization; reject or hold when it is absent. Material changes return to the relevant approval gate. |
| Unavailable verification | Record `UNMEASURED` with reason. It is not passing evidence and cannot satisfy a required acceptance condition. |
| Resume | Re-observe artifacts, task state, hashes, dirty baseline, scoped diffs, checks, and commits. Resume at the first incomplete or unverifiable item; never duplicate a verified side effect. |

After a terminal failure or block, retain only the bounded evidence necessary
for handoff. Do not automatically clean, revert, amend, push, open a pull
request, squash, or merge.
