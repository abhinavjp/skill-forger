"""Host-neutral, deterministic workflow-state helpers for Forge."""

import hashlib
import json
from collections import deque


_CHECK_STATUSES = {"PASS", "FAIL", "UNMEASURED"}
_FENCE_PREFIXES = ("```", "~~~")


def normalize_markdown(text):
    """Normalize non-semantic Markdown formatting for approval comparisons."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    normalized = []
    in_fence = False
    previous_blank = False

    for line in lines:
        is_fence = line.lstrip().startswith(_FENCE_PREFIXES)
        if in_fence:
            normalized.append(line)
            if is_fence:
                in_fence = False
            continue

        clean = line.rstrip(" \t")
        if clean == "":
            if not previous_blank:
                normalized.append("")
            previous_blank = True
            continue

        normalized.append(clean)
        previous_blank = False
        if clean.lstrip().startswith(_FENCE_PREFIXES):
            in_fence = True

    return "\n".join(normalized)


def content_hash(text):
    """Return the stable approval hash for meaningful Markdown content."""
    return hashlib.sha256(normalize_markdown(text).encode("utf-8")).hexdigest()


def can_retry(failure, attempts, changed_inputs):
    """Return whether a failed operation is eligible for another attempt."""
    if not isinstance(failure, dict) or not isinstance(attempts, int) or attempts < 0:
        return False

    classification = str(
        failure.get("classification", failure.get("kind", failure.get("type", "")))
    ).lower()
    if classification == "transient":
        limit = failure.get("max_attempts", failure.get("retry_limit"))
        return isinstance(limit, int) and limit >= 0 and attempts < limit
    if classification == "deterministic":
        return bool(changed_inputs)
    return False


def block_dependants(tasks, blocked_id):
    """Return the blocked task and every task that transitively depends on it."""
    task_records = _task_records(tasks)
    blocked = {blocked_id}
    pending = deque([blocked_id])

    while pending:
        dependency = pending.popleft()
        for task_id, dependencies in task_records.items():
            if dependency in dependencies and task_id not in blocked:
                blocked.add(task_id)
                pending.append(task_id)
    return blocked


def resume_point(state, observed_hashes):
    """Return the first incomplete or unverifiable workflow item, if any."""
    if not isinstance(state, dict) or not isinstance(observed_hashes, dict):
        raise TypeError("state and observed_hashes must be dictionaries")

    items = state.get("items", state.get("stages", state.get("tasks", [])))
    if isinstance(items, dict):
        items = [dict(value, id=key) for key, value in items.items()]
    if not isinstance(items, list):
        raise ValueError("workflow items must be an ordered list or object")

    for item in items:
        if not isinstance(item, dict) or "id" not in item:
            raise ValueError("each workflow item must have an id")
        item_id = item["id"]
        if not _is_completed(item):
            return item_id
        expected_hash = item.get("hash", item.get("expected_hash"))
        if expected_hash is None or observed_hashes.get(item_id) != expected_hash:
            return item_id
    return None


def record_check(state, check_id, status, reason=None):
    """Return a JSON-compatible copy of state with a deterministic check record."""
    if status not in _CHECK_STATUSES:
        raise ValueError("status must be PASS, FAIL, or UNMEASURED")
    if status == "UNMEASURED" and not reason:
        raise ValueError("UNMEASURED checks require a reason")

    updated = _json_copy(state)
    checks = updated.setdefault("checks", {})
    if not isinstance(checks, dict):
        raise ValueError("checks must be an object")

    record = {"status": status, "passed": status == "PASS"}
    if reason is not None:
        record["reason"] = reason
    checks[check_id] = record
    return updated


def can_enter_stage(state, target_stage, approval_policy=None):
    """Return a non-mutating decision for a workflow stage transition."""
    if not isinstance(state, dict):
        raise TypeError("state must be an object")

    target = _canonical_stage(target_stage)
    if target not in {"planning", "implementation"}:
        return _blocked("UNKNOWN_STAGE")

    artifacts = state.get("artifacts", {})
    if not isinstance(artifacts, dict):
        return _blocked("GATE_REQUIRED")

    required = []
    if target == "planning" and state.get("requires_spec_approval"):
        required.append(("specification", "planning"))
    if target == "implementation":
        if state.get("requires_spec_approval"):
            required.append(("specification", "planning"))
        required.append(("plan", "implementation"))

    required_artifacts = []
    for artifact_name, policy_stage in required:
        artifact = artifacts.get(artifact_name)
        if not _valid_approval(state, artifact, policy_stage, approval_policy):
            return _blocked("GATE_REQUIRED")
        required_artifacts.append(artifact)

    if _has_post_hoc_mutation(state, target, required_artifacts):
        return _blocked("GATE_VIOLATION")
    return {"allowed": True, "code": "ALLOWED", "read_only": False}


def _task_records(tasks):
    if isinstance(tasks, dict):
        iterable = [dict(value, id=key) for key, value in tasks.items()]
    else:
        iterable = tasks
    if not isinstance(iterable, (list, tuple)):
        raise TypeError("tasks must be a list or object")

    records = {}
    for task in iterable:
        if not isinstance(task, dict) or "id" not in task:
            raise ValueError("each task must have an id")
        dependencies = task.get("depends_on", task.get("dependencies", []))
        if not isinstance(dependencies, (list, tuple, set)):
            raise ValueError("task dependencies must be a list")
        records[task["id"]] = set(dependencies)
    return records


def _is_completed(item):
    return item.get("completed") is True or item.get("status") in {
        "COMPLETE",
        "COMPLETED",
        "VERIFIED",
    }


def _json_copy(value):
    try:
        return json.loads(json.dumps(value, sort_keys=True))
    except (TypeError, ValueError) as error:
        raise TypeError("state must contain JSON-compatible values") from error


def _canonical_stage(stage):
    value = str(stage).lower()
    return {"plan": "planning", "implement": "implementation"}.get(value, value)


def _valid_approval(state, artifact, policy_stage, approval_policy):
    if not isinstance(artifact, dict):
        return False
    approval = artifact.get("approval")
    if not isinstance(approval, dict):
        return False

    if approval.get("intent") in {"full_workflow", "implement"}:
        return False
    if approval.get("artifact_hash", approval.get("hash")) != artifact.get("hash"):
        return False
    if approval.get("revision") != artifact.get("revision"):
        return False

    actor = approval.get("actor")
    self_actors = {state.get("current_actor"), artifact.get("author"), artifact.get("created_by")}
    if actor in self_actors:
        return False

    allowed_approvers = _allowed_approvers(approval_policy, policy_stage)
    return not allowed_approvers or actor in allowed_approvers


def _allowed_approvers(approval_policy, stage):
    if not isinstance(approval_policy, dict):
        return set()
    configured = approval_policy.get(stage)
    if configured is None:
        approvers = approval_policy.get("approvers", {})
        if isinstance(approvers, dict):
            configured = approvers.get(stage)
    if isinstance(configured, dict):
        configured = configured.get("approvers", configured.get("allowed", []))
    if isinstance(configured, (list, tuple, set)):
        return set(configured)
    return set()


def _has_post_hoc_mutation(state, target, artifacts):
    mutations = state.get("mutations", [])
    if not isinstance(mutations, list):
        return False
    approval_times = []
    for artifact in artifacts:
        if isinstance(artifact, dict) and isinstance(artifact.get("approval"), dict):
            approval_times.append(artifact["approval"].get("approved_at"))

    for mutation in mutations:
        if not isinstance(mutation, dict) or mutation.get("stage") != target:
            continue
        mutation_time = mutation.get("at")
        for approval_time in approval_times:
            if _is_later(approval_time, mutation_time):
                return True
    return False


def _is_later(left, right):
    if left is None or right is None or type(left) is not type(right):
        return False
    try:
        return left > right
    except TypeError:
        return False


def _blocked(code):
    return {"allowed": False, "code": code, "read_only": True}
