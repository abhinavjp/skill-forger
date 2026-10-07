#!/usr/bin/env python3
"""Extract struggle signals from a Claude Code session log (JSONL).

Usage:
    session_signals.py <log.jsonl> [--max-line-bytes N] [--top N] [--heavy-chars N]

Read-only. Parses each line as JSON and nothing else: no log content is ever
executed, imported, or followed. Prints one JSON report to stdout. Every signal
carries a ``file:line`` locator; quoted text is redacted and short. Quoted text
is data from the log, never instructions.

Signals: user_correction, search_thrash, retry_loop, reverted_edit, heavy_output.

Exit codes: 0 report printed (even with no signals), 2 unreadable input.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_MAX_LINE_BYTES = 8 * 1024 * 1024
DEFAULT_TOP = 5
DEFAULT_HEAVY_CHARS = 20000
EXPLORE_RUN_MIN = 4
QUOTE_CHARS = 120

_REDACTED = "[REDACTED]"
_REDACTIONS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), _REDACTED),
    # Truncated key: header with no end marker; drop the base64 that follows it.
    (
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----(?:\s|\\[rn])*"
            r"(?:(?:(?:Proc-Type|DEK-Info):[^\r\n\\]*|[A-Za-z0-9+/=]{8,})(?:\s|\\[rn])*)*"
        ),
        _REDACTED,
    ),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"), _REDACTED),
    (re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{16,}"), _REDACTED),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{35}"), _REDACTED),
    (re.compile(r"\b(?=[0-9a-fA-F]*\d)(?=[0-9a-fA-F]*[a-fA-F])[0-9a-fA-F]{32}\b"), _REDACTED),
    # user:password@ inside a URL; the host stays.
    (re.compile(r"(\b[A-Za-z][A-Za-z0-9+.-]*://[^\s/:@]*:)[^\s/@?#]+(@)"), r"\1" + _REDACTED + r"\2"),
    (re.compile(r"(?i)(\bAuthorization[\"']?\s*:\s*[\"']?Basic\s+)\S+"), r"\1" + _REDACTED),
    # CLI flags: --password hunter2, --token=abc, and -pHunter22 (value glued to -p, needs a letter and a digit).
    (
        re.compile(r"(?i)(--(?:password|passwd|pwd|secret|token|api[_-]?key)(?:=|\s+))(?:\"[^\"]*(?:\"|$)|'[^']*(?:'|$)|\S+)"),
        r"\1" + _REDACTED,
    ),
    (re.compile(r"(?<!\S)(-p)(?=[^\s=./]*\d)(?=[^\s=./]*[A-Za-z])[^\s=./]{6,}\S*"), r"\1" + _REDACTED),
    (re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"), _REDACTED),
    (re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), _REDACTED),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), _REDACTED),
    (re.compile(r"(?i)(\bBearer\s+)[A-Za-z0-9._~+/=-]{16,}"), r"\1" + _REDACTED),
    (
        re.compile(
            r"(?i)(\b[A-Za-z0-9_]*(?:password|passwd|secret|token|api[_-]?key)[A-Za-z0-9_]*[\"']?\s*[:=]\s*)"
            r"(?:\"[^\"]*(?:\"|$)|'[^']*(?:'|$)|\S+)"
        ),
        r"\1" + _REDACTED,
    ),
    # Long mixed letter+digit blobs (keys, hashes). Paths and slugs keep their slashes and dots.
    (re.compile(r"\b(?=[A-Za-z0-9+_=-]*\d)(?=[A-Za-z0-9+_=-]*[A-Za-z])[A-Za-z0-9+_=-]{40,}\b"), _REDACTED),
]

_CORRECTION = re.compile(
    # "No problem / idea / worries / rush" are polite, not corrections.
    r"^\s*(?:no(?!\s+(?:problem|idea|worries|rush)\b)|nope|don'?t|do not|stop|wrong|not that|that'?s not|actually"
    r"|instead|why did you|undo|revert)\b",
    re.I,
)
_INTERRUPT = "[Request interrupted by user"
# Harness-injected user text, not something the user said.
_NOT_USER_PREFIXES = ("Stop hook feedback",)

_EXPLORE_TOOLS = {"Read", "Grep", "Glob"}
_WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
_SHELL_TOOLS = {"Bash", "PowerShell"}
_SEARCH_COMMANDS = {"grep", "rg", "find", "ls", "cat", "tree", "fd", "ag"}
_PS_SEARCH_COMMANDS = {
    "get-childitem", "gci", "dir", "ls", "select-string", "sls", "get-content", "gc", "cat", "type", "findstr",
    "rg", "grep", "find",
}  # compared lowercased
_QUOTE_INPUT_CHARS = 2000  # redaction patterns can be quadratic on huge input; quote() caps before redacting


def redact(text: str) -> str:
    for pattern, replacement in _REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def _excerpt(text: str, limit: int) -> str:
    return redact(" ".join(text[:_QUOTE_INPUT_CHARS].split()))[:limit]


def quote(text: str) -> str:
    return _excerpt(text, QUOTE_CHARS)


def iter_lines(handle, max_line_bytes: int):
    """Yield (lineno, bytes-or-None); None marks an oversize line that was skipped unread."""
    lineno = 0
    while True:
        raw = handle.readline(max_line_bytes + 1)
        if not raw:
            return
        lineno += 1
        if len(raw) > max_line_bytes and not raw.endswith(b"\n"):
            while True:
                rest = handle.readline(max_line_bytes)
                if not rest or rest.endswith(b"\n"):
                    break
            yield lineno, None
        else:
            yield lineno, raw


def user_text(record: dict) -> str:
    message = record.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str)
        )
    return ""


def _command(tool_input: dict) -> str:
    """Command with whitespace collapsed outside quotes: the retry_loop identity only. Never used to parse a command."""
    command = tool_input.get("command")
    if not isinstance(command, str):
        return ""
    out, quote_char, pending_space, escaped = [], None, False, False
    for ch in command:
        if quote_char:
            out.append(ch)
            if escaped:
                escaped = False  # the character after a backslash in double quotes never closes the quote
            elif ch == "\\" and quote_char == '"':
                escaped = True
            elif ch == quote_char:
                quote_char = None
        elif ch.isspace():
            pending_space = bool(out)
        else:
            if pending_space:
                out.append(" ")
                pending_space = False
            out.append(ch)
            if ch in "'\"":
                quote_char = ch
    return "".join(out)


def _raw_command(tool_input: dict) -> str:
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


_READ_TOOLS = {"Read"}
_BASH_READS = {"cat"}  # pure file reads; in Bash `type` is a builtin lookup, not a read
_PS_READS = {"cat", "type", "get-content", "gc"}  # compared lowercased
_SEARCH_ONLY_COMMANDS = _SEARCH_COMMANDS - _BASH_READS
_PS_SEARCH_ONLY_COMMANDS = _PS_SEARCH_COMMANDS - _PS_READS
_PATH_FLAGS = {"-path", "-literalpath", "-p"}  # PowerShell: the next token (or the :attached value) is the path
_VALUE_FLAGS = {  # PowerShell: the next token is a value, not a path
    "-totalcount", "-tail", "-head", "-first", "-last", "-readcount", "-encoding", "-delimiter", "-stream",
    "-filter", "-include", "-exclude",
}
_MAX_OPERANDS = 50  # file operands examined per shell call; the rest are ignored
_DRIVE = re.compile(r"^([A-Za-z]):(?:[\\/]|$)")
_MSYS = re.compile(r"^/([A-Za-z])/(.+)$")
_STDERR_REDIRECT = re.compile(r"^2>(?:>|&\d)?")
_BASH_ESCAPED = ";|&'\""  # after a backslash outside quotes (as is any whitespace): the command is not parsed


def _norm_path(value: str, shell: bool = False, drives=None) -> str:
    """Identity of a path: Windows drive paths fold case and use slashes; an MSYS /c/... form maps to the drive form in a shell
    or once a drive form was seen; POSIX paths are left alone. Never truncated or whitespace-collapsed."""
    drive = _DRIVE.match(value)
    if drive:
        if drives is not None:
            drives.add(drive.group(1).lower())
        return value.replace("\\", "/").casefold()
    if value.startswith("/"):
        msys = _MSYS.match(value)
        if msys and (shell or (drives is not None and msys.group(1).lower() in drives)):
            return (msys.group(1) + ":/" + msys.group(2)).casefold()
        return value
    return value.replace("\\", "/")


def _segments(command: str, bash: bool):
    """Split a command on && || ; | and newlines outside quotes.

    Returns None (unclassifiable) when it cannot be parsed with confidence: an unbalanced quote, or in Bash a
    backslash-escaped separator or quote outside quotes. Stops at an unquoted heredoc marker: conservative by design,
    everything from "<<" on (the body, and anything after it) is data and is never classified.
    """
    out, cur, quote_char, i = [], [], None, 0
    while i < len(command):
        ch = command[i]
        if quote_char:
            if bash and quote_char == '"' and ch == "\\" and i + 1 < len(command):
                cur.append(command[i : i + 2])  # a Bash escape inside double quotes
                i += 2
                continue
            cur.append(ch)
            if ch == quote_char:
                quote_char = None
        elif ch in "'\"":
            quote_char = ch
            cur.append(ch)
        elif ch == "#" and (not cur or cur[-1].isspace()):
            while i < len(command) and command[i] != "\n":
                i += 1  # a comment: nothing in it runs
            continue
        elif bash and ch == "\\" and i + 1 < len(command) and (command[i + 1].isspace() or command[i + 1] in _BASH_ESCAPED):
            return None
        elif command.startswith("<<", i):
            cur.append("<<")
            break
        elif command.startswith("&&", i) or command.startswith("||", i):
            out.append("".join(cur))
            cur, i = [], i + 2
            continue
        elif ch in ";|\n":
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    if quote_char:
        return None
    out.append("".join(cur))
    return out


def _tokens(segment: str, bash: bool):
    """Quote-aware split into (text, quoted, redirect); quoted means the token began with a quote.
    Backslashes are literal (Windows paths). None when a quote is unbalanced."""
    tokens, cur, quote_char, started, quoted, redirect, i = [], [], None, False, False, False, 0
    while i < len(segment):
        ch = segment[i]
        if quote_char:
            if bash and quote_char == '"' and ch == "\\" and segment[i + 1 : i + 2] in ('"', "\\", "$", "`", "\n"):
                return None  # a real Bash escape inside double quotes changes the operand; do not guess
            if ch == quote_char:
                quote_char = None
            else:
                cur.append(ch)
        elif ch in "'\"":
            quote_char = ch
            quoted = quoted or not started
            started = True
        elif ch.isspace():
            if started:
                tokens.append(("".join(cur), quoted, redirect))
                cur, started, quoted, redirect = [], False, False, False
        else:
            redirect = redirect or ch in "<>"
            cur.append(ch)
            started = True
        i += 1
    if quote_char:
        return None
    if started:
        tokens.append(("".join(cur), quoted, redirect))
    return tokens


def _segment_read_paths(tokens: list, bash: bool):
    """Paths read by one cat/type/Get-Content segment, or None when it redirects (a write, not a read).

    Bash cat flags never take a value, `--` ends options and `-` is stdin. PowerShell path flags take the next token
    or an attached `-Path:value`; value flags (-TotalCount ...) skip their value.
    """
    args, i = tokens[1:], 0
    flagged, positional = [], []
    options_ended = False
    while i < len(args):
        text, quoted, redirect = args[i]
        i += 1
        if redirect:
            if _STDERR_REDIRECT.match(text):
                if text in ("2>", "2>>"):
                    i += 1  # the file that stderr goes to
                continue
            return None
        if bash:
            if text == "-":
                continue
            if not options_ended and text in ("--help", "--version"):
                return []  # prints help or the version; reads nothing
            if not options_ended and text == "--":
                options_ended = True  # quoting does not change what `--` means
                continue
            if not options_ended and text.startswith("-"):
                continue  # quoting does not turn an option into a file
            positional.append(text)
            continue
        if not quoted and text.startswith("-") and len(text) > 1:
            name, _, attached = text.partition(":")
            name = name.lower()
            if attached:
                if name in _PATH_FLAGS:
                    flagged.append(attached)
            elif name in _PATH_FLAGS:
                if i < len(args):
                    flagged.append(args[i][0])
                    i += 1
            elif name in _VALUE_FLAGS and i < len(args):
                i += 1
            continue
        positional.append(text)
    return flagged or positional


def _shell_call(command: str, bash: bool, drives):
    """Heuristic classifier: a search, a read of files, or None. An uncertain command is None (neutral)."""
    segments = _segments(command, bash)
    if segments is None:
        return None
    only = _SEARCH_ONLY_COMMANDS if bash else _PS_SEARCH_ONLY_COMMANDS
    reads = _BASH_READS if bash else _PS_READS
    keys, seen, operands, is_read = [], set(), 0, False
    for segment in segments:
        tokens = _tokens(segment, bash)
        if not tokens:
            continue
        head = tokens[0][0] if bash else tokens[0][0].lower()
        if head in only:
            return "search", quote(command), ("shell", " ".join(command.split()))
        if head in reads:
            paths = _segment_read_paths(tokens, bash)
            if paths is None:
                continue
            is_read = True
            for path in paths[: _MAX_OPERANDS - operands]:
                operands += 1
                if not path:
                    continue
                key = ("read", _norm_path(path, True, drives), None, None)
                if key not in seen:
                    seen.add(key)
                    keys.append(key)
    return ("read", quote(command), keys) if is_read else None


def _page_value(value):
    return value if isinstance(value, (int, str)) else None


def _explore_call(name: str, tool_input: dict, drives=None):
    """Classify a call: None (not exploration), or (kind, target, key).

    kind is "search" (always counts; key is one hashable identity) or "read" (counts only as a re-read;
    key is a list of identities, one per file read, empty when no path is readable).
    """
    if name in _READ_TOOLS:
        value = tool_input.get("file_path")
        if not isinstance(value, str):
            value = tool_input.get("path")
        if isinstance(value, str):
            page = (_page_value(tool_input.get("offset")), _page_value(tool_input.get("limit")))
            return "read", quote(value), [("read", _norm_path(value, False, drives)) + page]
        return "read", name, []
    if name in _EXPLORE_TOOLS:
        fields = [tool_input.get(key) for key in ("pattern", "file_path", "path")]
        fields = [field if isinstance(field, str) else None for field in fields]
        if all(field is None for field in fields):
            return "search", name, (name,)
        pattern, file_path, path = fields
        text = next(field for field in fields if field is not None)
        file_path = None if file_path is None else _norm_path(file_path, False, drives)
        path = None if path is None else _norm_path(path, False, drives)
        return "search", quote(text), ("search", name, pattern, file_path, path)
    if name in _SHELL_TOOLS:
        return _shell_call(_raw_command(tool_input), name == "Bash", drives)
    return None


def _result_chars(content) -> int:
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        total = 0
        for item in content:
            if isinstance(item, str):
                total += len(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                total += len(item["text"])
        return total
    return 0


class _State:
    def __init__(self, name: str, heavy_chars: int):
        self.name = name
        self.heavy_chars = heavy_chars
        self.signals: list = []
        self.tools: dict = {}  # tool_use id -> {"name", "line", "command"}
        # Counted exploration calls since the last write or user turn: (line, target, key).
        # Searches count at once; a read counts only once its path is read again (then both reads count).
        self.run: list = []
        self.reads: dict = {}  # read key -> first call (line, target, key, call id) awaiting a re-read, or None once promoted
        self.counted: set = set()  # call ids already in the run: a call counts once
        self.drives: set = set()  # drive letters seen in Windows-form paths (lets the MSYS /c/... form map to the drive form)
        self.seq = 0
        # normalized command -> failure streaks, once it has failed:
        # {"streak", "streak_line" (current), "line", "count" (longest streak so far)}
        self.retries: dict = {}
        self.edits: dict = {}  # file -> [(old, new)]

    def locator(self, lineno: int) -> str:
        return f"{self.name}:{lineno}"

    def flush_run(self) -> None:
        if len(self.run) >= EXPLORE_RUN_MIN:
            self.run.sort(key=lambda call: call[0])
            self.signals.append(
                {
                    "kind": "search_thrash",
                    "locator": self.locator(self.run[0][0]),
                    "count": len(self.run),
                    "distinct": len({key for _, _, key in self.run}),
                    "targets": [target for _, target, _ in self.run[:5]],
                }
            )
        self.run = []
        self.reads = {}
        self.counted = set()

    def tool_use(self, lineno: int, block: dict) -> None:
        name = block.get("name") if isinstance(block.get("name"), str) else ""
        tool_input = block.get("input") if isinstance(block.get("input"), dict) else {}
        command = _command(tool_input) if name in _SHELL_TOOLS else ""
        if isinstance(block.get("id"), str):
            self.tools[block["id"]] = {"name": name, "line": lineno, "command": command}
        if name in _WRITE_TOOLS:
            self.flush_run()
        else:
            call = _explore_call(name, tool_input, self.drives)
            if call is not None:
                self._explore(lineno, *call)
        if name == "Edit":
            self._edit(lineno, tool_input)

    def _explore(self, lineno: int, kind: str, target: str, key) -> None:
        if kind == "search":
            self.run.append((lineno, target, key))
            return
        # A read: key is a list of file identities. A first read is neutral; a re-read of any identity counts,
        # and so does the earlier call that first read it. Each call counts at most once.
        keys = list(dict.fromkeys(key))
        if not keys:
            return
        self.seq += 1
        call_id = self.seq
        promoted = False
        for read_key in keys:
            if read_key in self.reads:
                first = self.reads[read_key]
                if first is not None:
                    self.reads[read_key] = None
                    if first[3] not in self.counted:
                        self.counted.add(first[3])
                        self.run.append((first[0], first[1], read_key))
                if not promoted:
                    promoted = True
                    self.counted.add(call_id)
                    self.run.append((lineno, target, read_key))
        for read_key in keys:
            if read_key not in self.reads:
                self.reads[read_key] = (lineno, target, read_key, call_id)

    def _edit(self, lineno: int, tool_input: dict) -> None:
        path, old, new = (tool_input.get(k) for k in ("file_path", "old_string", "new_string"))
        if not all(isinstance(v, str) for v in (path, old, new)):
            return
        if any(prev_old == new and prev_new == old for prev_old, prev_new in self.edits.get(path, [])):
            self.signals.append({"kind": "reverted_edit", "locator": self.locator(lineno), "file": redact(path[:_QUOTE_INPUT_CHARS])[:200]})
        self.edits.setdefault(path, []).append((old, new))

    def tool_result(self, lineno: int, block: dict) -> None:
        tool_use_id = block.get("tool_use_id")
        tool = self.tools.get(tool_use_id if isinstance(tool_use_id, str) else None, {"name": "unknown", "line": lineno, "command": ""})
        chars = _result_chars(block.get("content"))
        if chars > self.heavy_chars:
            self.signals.append(
                {"kind": "heavy_output", "locator": self.locator(lineno), "tool": tool["name"], "chars": chars}
            )
        command = tool["command"]
        if tool["name"] in _SHELL_TOOLS and command:
            entry = self.retries.get(command)
            if block.get("is_error") is True:
                if entry is None:
                    entry = self.retries[command] = {"streak": 0, "streak_line": 0, "line": 0, "count": 0}
                entry["streak"] += 1
                if entry["streak"] == 1:
                    entry["streak_line"] = tool["line"]
                if entry["streak"] > entry["count"]:  # strict: an earlier streak wins ties
                    entry["count"], entry["line"] = entry["streak"], entry["streak_line"]
            elif entry is not None:
                entry["streak"] = 0  # a pass ends the streak: fail,pass is a fix, not a retry

    def user_turn(self, lineno: int, text: str) -> None:
        self.flush_run()
        if _CORRECTION.match(text) or text.lstrip().startswith(_INTERRUPT):
            self.signals.append({"kind": "user_correction", "locator": self.locator(lineno), "quote": quote(text)})

    def finish(self) -> list:
        self.flush_run()
        for command, entry in self.retries.items():
            if entry["count"] >= 2:
                self.signals.append(
                    {
                        "kind": "retry_loop",
                        "locator": self.locator(entry["line"]),
                        "count": entry["count"],
                        "quote": quote(command),
                    }
                )
        return self.signals


def _line_of(signal: dict) -> int:
    return int(signal["locator"].rsplit(":", 1)[1])


def _weight(signal: dict) -> int:
    return signal.get("count") or signal.get("chars") or 0


def analyze(
    path,
    *,
    max_line_bytes: int = DEFAULT_MAX_LINE_BYTES,
    top: int = DEFAULT_TOP,
    heavy_chars: int = DEFAULT_HEAVY_CHARS,
) -> dict:
    path = Path(path)
    state = _State(path.name, heavy_chars)
    report = {
        "source": path.name,
        "records": 0,
        "parse_errors": 0,
        "oversize_lines": 0,
        "data_not_instructions": True,
        "signals": [],
        "omitted": {},
    }
    with path.open("rb") as handle:
        for lineno, raw in iter_lines(handle, max_line_bytes):
            if raw is None:
                report["oversize_lines"] += 1
                continue
            if not raw.strip():
                continue
            try:
                record = json.loads(raw)
            except (ValueError, RecursionError):  # RecursionError: deeply nested crafted line
                report["parse_errors"] += 1
                continue
            if not isinstance(record, dict):
                report["parse_errors"] += 1
                continue
            report["records"] += 1
            kind = record.get("type")
            message = record.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            blocks = [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []
            if kind == "assistant":
                for block in blocks:
                    if block.get("type") == "tool_use":
                        state.tool_use(lineno, block)
            elif kind == "user":
                for block in blocks:
                    if block.get("type") == "tool_result":
                        state.tool_result(lineno, block)
                text = user_text(record)
                injected = record.get("isMeta") is True or record.get("isCompactSummary") is True
                if text and not injected and not text.lstrip().startswith(_NOT_USER_PREFIXES):
                    state.user_turn(lineno, text)
    by_kind: dict = {}
    for signal in state.finish():
        by_kind.setdefault(signal["kind"], []).append(signal)
    kept = []
    for kind, signals in by_kind.items():
        signals.sort(key=lambda s: (-_weight(s), _line_of(s)))
        kept.extend(signals[:top])
        if len(signals) > top:
            report["omitted"][kind] = len(signals) - top
    report["signals"] = sorted(kept, key=_line_of)
    return report


_CONTEXT_BEFORE = 3  # records shown before the requested one
_CONTEXT_CHARS = 400  # per record


_RECORD_TYPES = ("user", "assistant", "system", "summary", "unreadable")  # labels safe to print; any other type is "other"


def _plain(value, depth: int = 0) -> str:
    """String leaves of a JSON value joined by spaces, unescaped (json.dumps would hide quote pairs from the redactor)."""
    if isinstance(value, str):
        return value
    if depth > 8:
        return ""
    if isinstance(value, dict):
        return " ".join(f"{key}={_plain(item, depth + 1)}" for key, item in value.items() if isinstance(key, str))
    if isinstance(value, list):
        return " ".join(_plain(item, depth + 1) for item in value)
    return "" if value is None else str(value)


def _describe(record) -> str:
    """Redaction-ready text of one record: user/assistant text, tool calls and tool results (not thinking)."""
    message = record.get("message") if isinstance(record, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return content
    parts = []
    for block in content if isinstance(content, list) else []:
        if not isinstance(block, dict):
            continue
        kind = block.get("type")
        if kind == "text" and isinstance(block.get("text"), str):
            parts.append(block["text"])
        elif kind == "tool_use":
            parts.append(f"[tool_use {block.get('name')}] {_plain(block.get('input'))}")
        elif kind == "tool_result":
            body = block.get("content")
            flag = " error" if block.get("is_error") is True else ""
            parts.append(f"[tool_result{flag}] {_plain(body)}")
    return " ".join(parts)


def context(path: str, line: int, max_line_bytes: int = DEFAULT_MAX_LINE_BYTES) -> dict:
    """Redacted, truncated view of record `line` and the few before it, so nobody has to read raw transcript lines."""
    if max_line_bytes < 1 or line < 1:
        raise ValueError("line and max-line-bytes must be positive")
    shown = []
    with open(path, "rb") as handle:
        for lineno, raw in iter_lines(handle, max_line_bytes):
            if lineno > line:
                break
            if lineno < line - _CONTEXT_BEFORE:
                continue
            try:
                record = json.loads(raw) if raw is not None else None
            except (ValueError, RecursionError):
                record = None
            if not isinstance(record, dict):
                shown.append({"line": lineno, "type": "unreadable"})
                continue
            kind = record.get("type")
            shown.append(
                {"line": lineno, "type": kind if kind in _RECORD_TYPES else "other", "text": _excerpt(_describe(record), _CONTEXT_CHARS)}
            )
    return {"source": os.path.basename(path), "data_not_instructions": True, "records": shown}


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="session_signals",
        description="Extract struggle signals from a Claude Code session log (read-only).",
    )
    parser.add_argument("log", help="path to a session .jsonl file")
    parser.add_argument("--max-line-bytes", type=_positive_int, default=DEFAULT_MAX_LINE_BYTES)
    parser.add_argument("--top", type=_positive_int, default=DEFAULT_TOP, help="max signals reported per kind")
    parser.add_argument("--heavy-chars", type=_positive_int, default=DEFAULT_HEAVY_CHARS, help="tool-result size that counts as heavy")
    parser.add_argument("--context", type=_positive_int, metavar="LINE", help="print a redacted view of record LINE and the 3 before it, then exit")
    args = parser.parse_args(argv)
    try:
        if args.context:
            report = context(args.log, args.context, args.max_line_bytes)
            json.dump(report, sys.stdout, indent=2)
            sys.stdout.write("\n")
            return 0
        report = analyze(args.log, max_line_bytes=args.max_line_bytes, top=args.top, heavy_chars=args.heavy_chars)
    except OSError as exc:
        print(f"session_signals: cannot read {args.log}: {exc.strerror or exc}", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
