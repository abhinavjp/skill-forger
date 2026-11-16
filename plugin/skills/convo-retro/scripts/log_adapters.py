"""Translate Codex and Cursor records into the conversation analyzer's input."""

import json
import re

FORMATS = ("claude", "codex", "cursor")

_LIMIT = 20000
_CODEX_TYPES = {"response_item", "event_msg", "turn_context"}
_CLAUDE_TYPES = {
    "user",
    "assistant",
    "system",
    "summary",
    "progress",
    "file-history-snapshot",
    "queue-operation",
    "custom-title",
    "last-prompt",
    "pr-link",
    "saved_hook_context",
}
_TEXT_TYPES = {"text", "input_text", "output_text"}
_META_PREFIXES = (
    "# AGENTS.md",
    "<environment_context",
    "<user_instructions",
    "<permissions instructions",
    "<recommended_plugins",
    "<skills_instructions",
    "<INSTRUCTIONS>",
)
_PS = re.compile(
    r"\b(?:Get-ChildItem|Select-String|Get-Content|ForEach-Object|powershell)\b"
    r"|\$env:",
    re.IGNORECASE,
)
_JS_CMD = re.compile(
    r"""\bcmd\s*:\s*(?:"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)'|`((?:[^`\\]|\\.)*)`)""",
    re.DOTALL,
)
_JS_TOKEN = re.compile(r'\\[\s\S]|"')
_PATCH_PATH = re.compile(
    r"^\*\*\* (?:Update|Add|Delete) File:[ \t]*([^\r\n]*)",
    re.MULTILINE,
)
# Runner status wordings, most authoritative first; stdout may quote the weaker ones ("Exit code: 1" is also real-log wording).
_EXIT_STATUS = (
    re.compile(r"Process exited with code\s*([0-9]+)\b", re.IGNORECASE),
    re.compile(r'"exit_code"\s*:\s*([0-9]+)\b'),
    re.compile(r"exit code\s*:\s*([0-9]+)\b", re.IGNORECASE),
)
_SCRIPT_FAILED = re.compile(r"^\s*Script failed\b")
_TAG = re.compile(r"<(/?)([A-Za-z_][A-Za-z0-9_-]*)>")


def _open_tags(prefix: str) -> list:
    """Tags opened but not yet closed in `prefix` (empty when its tags balance)."""
    stack = []
    for match in _TAG.finditer(prefix):
        if match.group(1):
            for index in range(len(stack) - 1, -1, -1):
                if stack[index] == match.group(2):
                    del stack[index:]
                    break
        else:
            stack.append(match.group(2))
    return stack


_CURSOR_SPEAKERS = {
    "user": "user",
    "human": "user",
    "assistant": "assistant",
    "ai": "assistant",
}
_CURSOR_TOOL_NAMES = {
    "shell": "Bash",
    "run_terminal_cmd": "Bash",
    "run_terminal_command": "Bash",
    "terminal": "Bash",
    "bash": "Bash",
    "powershell": "Bash",
    "read_file": "Read",
    "readfile": "Read",
    "read": "Read",
    "grep": "Grep",
    "ripgrep": "Grep",
    "rg": "Grep",
    "codebase_search": "Grep",
    "semantic_search": "Grep",
    "search": "Grep",
    "glob": "Glob",
    "glob_file_search": "Glob",
    "list_dir": "Glob",
    "ls": "Glob",
    "file_search": "Glob",
    "strreplace": "Edit",
    "str_replace": "Edit",
    "edit_file": "Edit",
    "search_replace": "Edit",
    "apply_patch": "Edit",
    "write": "Write",
    "create": "Write",
    "create_file": "Write",
    "delete_file": "Edit",
    "multiedit": "Edit",
}
_CURSOR_ARGUMENT_KEYS = ("input", "args", "arguments", "params")
_CURSOR_PATH_KEYS = ("path", "target_file", "file_path")


def _string(value):
    return value if isinstance(value, str) else ""


def _cap(value):
    return _string(value)[:_LIMIT]


def _text_parts(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for block in value:
            if not isinstance(block, dict):
                continue
            if _string(block.get("type")) in _TEXT_TYPES:
                text = block.get("text")
                if isinstance(text, str):
                    yield text


def _text(value):
    return "\n".join(_text_parts(value))


def _arguments(value):
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}
    try:
        parsed = json.loads(value)
    except (ValueError, TypeError, RecursionError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _command(arguments):
    for key in ("cmd", "command"):
        value = arguments.get(key)
        if isinstance(value, str) and value:
            return value
        if isinstance(value, list) and all(
            isinstance(part, str) for part in value
        ):
            command = " ".join(value)
            if command:
                return command
    return ""


def _unescape_js(raw, quote):
    if quote != '"':
        # Preserve escaped backslashes while normalizing the outer delimiter.
        def replace(match):
            token = match.group(0)
            if token == '"':
                return '\\"'
            if token == "\\" + quote:
                return quote
            return token

        encoded = _JS_TOKEN.sub(replace, raw)
    else:
        encoded = raw
    try:
        return json.loads('"' + encoded + '"')
    except (ValueError, TypeError, RecursionError):
        return raw


def _js_command(source):
    match = _JS_CMD.search(source)
    if not match:
        return ""
    for index, quote in enumerate(('"', "'", "`"), 1):
        raw = match.group(index)
        if raw is not None:
            return _unescape_js(raw, quote)
    return ""


def _patch(value):
    arguments = _arguments(value)
    for key in ("patch", "input"):
        candidate = arguments.get(key)
        if isinstance(candidate, str):
            return candidate
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (ValueError, TypeError, RecursionError):
            return value
        return parsed if isinstance(parsed, str) else value
    return ""


def _tool_use(call_id, name, tool_input):
    return [{
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [{
                "type": "tool_use",
                "id": _cap(call_id),
                "name": name,
                "input": tool_input,
            }],
        },
    }]


def _codex_records(record):
    if record.get("type") != "response_item":
        return []
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return []
    kind = _string(payload.get("type"))

    if kind == "message":
        role = _string(payload.get("role"))
        if role not in ("user", "assistant"):
            return []
        content = payload.get("content")
        text = _text(content)
        if not text:
            return []
        if role == "assistant":
            return [{
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": _cap(text)}],
                },
            }]
        result = {
            "type": "user",
            "message": {"role": "user", "content": _cap(text)},
        }
        if (
            record.get("isMeta") is True
            or record.get("isCompactSummary") is True
            or payload.get("isMeta") is True
            or any(
                part.lstrip().startswith(_META_PREFIXES)
                for part in _text_parts(content)
            )
        ):
            result["isMeta"] = True
        return [result]

    if kind in ("function_call", "custom_tool_call"):
        call_id = _string(payload.get("call_id"))
        name = _string(payload.get("name"))
        if not call_id or not name:
            return []
        source = payload.get(
            "input" if kind == "custom_tool_call" else "arguments"
        )
        if name.rsplit(".", 1)[-1] == "apply_patch":
            match = _PATCH_PATH.search(_patch(source))
            path = match.group(1).strip() if match else ""
            return _tool_use(call_id, "Edit", {"file_path": _cap(path)})
        if kind == "custom_tool_call":
            command = _js_command(_string(source))
        else:
            command = _command(_arguments(source))
        if not command:
            return []
        tool_name = "PowerShell" if _PS.search(command) else "Bash"
        return _tool_use(
            call_id, tool_name, {"command": _cap(command)}
        )

    if kind in ("function_call_output", "custom_tool_call_output"):
        call_id = _string(payload.get("call_id"))
        if not call_id:
            return []
        text = _text(payload.get("output"))
        # Avoid int(): malformed logs may contain arbitrarily long numbers.
        status = next((m for m in (pattern.search(text) for pattern in _EXIT_STATUS) if m), None)
        failed = bool(status and status.group(1).lstrip("0")) or bool(_SCRIPT_FAILED.match(text))
        return [{
            "type": "user",
            "message": {
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": _cap(call_id),
                    "content": _cap(text),
                    "is_error": failed,
                }],
            },
        }]
    return []


def _cursor_speaker(record):
    for key in ("role", "type"):
        value = record.get(key)
        if isinstance(value, str):
            speaker = _CURSOR_SPEAKERS.get(value.lower())
            if speaker:
                return speaker
    return ""


def _cursor_content(record):
    message = record.get("message")
    if isinstance(message, dict):
        value = message.get("content")
        if isinstance(value, (str, list)):
            return value
    for key in ("content", "text"):
        value = record.get(key)
        if isinstance(value, (str, list)):
            return value
    return None


def _first_string(mapping, keys):
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _cursor_arguments(block):
    for key in _CURSOR_ARGUMENT_KEYS:
        value = block.get(key)
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            parsed = _arguments(value)
            if parsed:
                return parsed
    return {}


def _cursor_tool(block, index):
    name = _string(block.get("name")).lower()
    mapped_name = _CURSOR_TOOL_NAMES.get(name)
    if mapped_name is None:
        return None

    arguments = _cursor_arguments(block)
    if mapped_name == "Bash":
        command = _cap(_command(arguments))
        mapped_name = "PowerShell" if _PS.search(command) else "Bash"
        tool_input = {"command": command}
    elif mapped_name == "Read":
        tool_input = {
            "file_path": _cap(
                _first_string(arguments, _CURSOR_PATH_KEYS)
            ),
        }
    elif mapped_name == "Grep":
        tool_input = {
            "pattern": _cap(
                _first_string(arguments, ("pattern", "query", "regex"))
            ),
            "path": _cap(
                _first_string(arguments, _CURSOR_PATH_KEYS)
            ),
        }
    elif mapped_name == "Glob":
        tool_input = {
            "pattern": _cap(
                _first_string(
                    arguments,
                    (
                        "pattern", "glob", "query", "path",
                        "target_file", "file_path",
                    ),
                )
            ),
        }
    else:
        path = _first_string(arguments, _CURSOR_PATH_KEYS)
        if not path and name == "apply_patch":
            for key in _CURSOR_ARGUMENT_KEYS:
                match = _PATCH_PATH.search(_patch(block.get(key)))
                if match:
                    path = match.group(1).strip()
                    break
        tool_input = {"file_path": _cap(path)}

    call_id = _first_string(block, ("id", "call_id"))
    if not call_id:
        call_id = "t{}".format(index)
    return {
        "type": "tool_use",
        "id": _cap(call_id),
        "name": mapped_name,
        "input": tool_input,
    }


def _cursor_context(text):
    stripped = text.lstrip()
    if len(stripped) < 2 or stripped[0] != "<":
        return False
    # Recognize an opening tag without scanning arbitrary tag contents.
    initial = stripped[1]
    return (
        "a" <= initial <= "z"
        or "A" <= initial <= "Z"
        or initial == "_"
    )


def _cursor_records(record):
    if "turn_ended" in record:
        return []
    speaker = _cursor_speaker(record)
    if not speaker:
        return []
    content = _cursor_content(record)
    if content is None:
        return []

    if speaker == "user":
        text = _text(content)
        start = text.find("<user_query>")
        leading = start >= 0 and not _open_tags(text[:start])  # a query nested inside a context tag is an example, not a turn
        is_context = not leading and _cursor_context(text)
        if leading:
            start += len("<user_query>")
            end = text.find("</user_query>", start)
            # An incomplete wrapper still has a useful trailing query.
            text = text[start:end] if end >= 0 else text[start:]
            text = text.strip()
        result = {
            "type": "user",
            "message": {"role": "user", "content": _cap(text)},
        }
        message = record.get("message")
        if (
            is_context
            or record.get("isMeta") is True
            or record.get("isCompactSummary") is True
            or (
                isinstance(message, dict)
                and message.get("isMeta") is True
            )
        ):
            result["isMeta"] = True
        return [result]

    blocks = []
    if isinstance(content, str):
        if content:
            blocks.append({"type": "text", "text": _cap(content)})
    else:
        for index, block in enumerate(content):
            if not isinstance(block, dict):
                continue
            kind = _string(block.get("type"))
            if kind in _TEXT_TYPES:
                text = block.get("text")
                if isinstance(text, str) and text:
                    blocks.append({"type": "text", "text": _cap(text)})
            elif kind.lower() in ("tool_use", "tool_call", "toolcall"):
                tool = _cursor_tool(block, index)
                if tool is not None:
                    blocks.append(tool)
            # Cursor supplies no results; never synthesize tool_result blocks.
    if not blocks:
        return []
    return [{
        "type": "assistant",
        "message": {"role": "assistant", "content": blocks},
    }]


def detect_format(record: dict) -> str:
    if not isinstance(record, dict):
        return "claude"
    try:
        kind = record.get("type")
        if kind == "session_meta":
            return "codex"
        if (
            isinstance(kind, str)
            and kind in _CODEX_TYPES
            and isinstance(record.get("payload"), dict)
        ):
            return "codex"
        if isinstance(kind, str) and kind in _CLAUDE_TYPES:
            return "claude"
        if "turn_ended" in record:
            return "cursor"
        if (
            _cursor_speaker(record)
            and _cursor_content(record) is not None
        ):
            return "cursor"
    except Exception:
        # Unknown or malformed shapes retain the conservative default.
        pass
    return "claude"


def to_claude_records(record: dict, fmt: str) -> list:
    if fmt == "claude":
        return [record]
    if not isinstance(record, dict):
        return []
    try:
        if fmt == "codex":
            return _codex_records(record)
        if fmt == "cursor":
            return _cursor_records(record)
        return []
    except Exception:
        # A malformed record must never interrupt the surrounding JSONL scan.
        return []
