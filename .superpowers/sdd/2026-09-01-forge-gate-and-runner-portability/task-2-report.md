# Task 2 Report — Require artifact-approval intent

## Status

Implemented the Task 2 artifact-approval intent hardening in the declared source and test files. The requested commit subject is:

`fix(forge): require artifact-approval intent at workflow gates`

## Implementation details

- Added `ARTIFACT_APPROVAL_INTENTS = {"artifact"}` beside `KNOWN_MUTATION_STAGES` in `plugin/shared/forge/scripts/workflow_state.py`.
- Updated `_valid_approval` to read `approval["intent"]` once via `.get("intent")`.
- Preserved backward compatibility for an absent or `None` intent.
- Rejected every supplied intent other than the exact string `"artifact"`, including non-string values without attempting an unhashable membership lookup.
- Left the hash, revision, actor, policy, stage-entry, and post-hoc mutation checks unchanged.
- Extended `test_full_workflow_intent_is_not_artifact_approval` for `"full_workflow"`, `"full-workflow"`, `"run_workflow"`, `"implement_all"`, and `123` across both planning/Specification and implementation/Plan gates.
- Added a positive test proving an approval with no `intent` key still opens both gates.

## TDD evidence

The test was extended before the production source change.

RED command:

```text
python -m pytest plugin/shared/forge/tests/test_workflow_state.py -q
```

Observed result:

```text
python: The term 'python' is not recognized as a name of a cmdlet, function, script file, or executable program.
```

Therefore the intended behavioral RED failure could not be observed because the required Python runtime/test runner is unavailable in this environment.

GREEN command after the minimal source change:

```text
python -m pytest plugin/shared/forge/tests/test_workflow_state.py -q
```

Observed result was the same unresolved-command error. No pytest tests were executed.

## Test commands and output

- `python -m pytest plugin/shared/forge/tests/test_workflow_state.py -q` — unable to run; `python` is not installed or discoverable.
- `git diff --check` — passed with no output.

## Self-review

- Confirmed the source change is confined to `_valid_approval` and the adjacent module constant.
- Confirmed existing approval fixtures remain unchanged and continue to use `intent: "artifact"`.
- Confirmed the non-string guard occurs before set membership, so list/dict/number intents fail closed without raising an exception.
- Confirmed the existing hash, revision, actor, policy, `can_enter_stage`, and `_has_post_hoc_mutation` logic was not changed.
- Confirmed the working diff contains only the requested source/test changes plus this report; unrelated pre-existing untracked files were not modified.

## Concerns

- Focused unit-test execution and runtime-level validation remain outstanding until a Python interpreter with pytest is available. The commit should be rerun with the narrow verification command in an environment that provides that runtime.
