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
        re.compile(r"(?i)(--(?:password|passwd|pwd|secret|token|api[_-]?key)(?:=|\s+))(?:\"[^\"]*\"|'[^']*'|\S+)"),
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
            r"(?:\"[^\"]*\"|'[^']*'|\S+)"
        ),
        r"\1" + _REDACTED,
    ),
    # Long mixed letter+digit blobs (keys, hashes). Paths and slugs keep their slashes and dots.
    (re.compile(r"\b(?=[A-Za-z0-9+_=-]*\d)(?=[A-Za-z0-9+_=-]*[A-Za-z])[A-Za-z0-9+_=-]{40,}\b"), _REDACTED),
]

_CORRECTION = re.compile(
    r"^\s*(?:no|nope|don'?t|do not|stop|wrong|not that|that'?s not|actually|instead|why did you|undo|revert)\b",
    re.I,
)

_EXPLORE_TOOLS = {"Read", "Grep", "Glob"}
_WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
_SEARCH_COMMANDS = {"grep", "rg", "find", "ls", "cat", "tree", "fd", "ag"}


def redact(text: str) -> str:
    for pattern, replacement in _REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def quote(text: str) -> str:
    return redact(" ".join(text.split()))[:QUOTE_CHARS]


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
    command = tool_input.get("command")
    return " ".join(command.split()) if isinstance(command, str) else ""


def _explore_target(name: str, tool_input: dict):
    """Return a short target string if this call is exploration, else None."""
    if name in _EXPLORE_TOOLS:
        for key in ("pattern", "file_path", "path"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return quote(value)
        return name
    if name == "Bash":
        command = _command(tool_input)
        if command.split(" ", 1)[0] in _SEARCH_COMMANDS:
            return quote(command)
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
        self.run: list = []  # exploration calls since the last write or user turn: (line, target)
        self.retries: dict = {}  # normalized command -> {"line", "count"}, once it has failed
        self.edits: dict = {}  # file -> [(old, new)]

    def locator(self, lineno: int) -> str:
        return f"{self.name}:{lineno}"

    def flush_run(self) -> None:
        if len(self.run) >= EXPLORE_RUN_MIN:
            self.signals.append(
                {
                    "kind": "search_thrash",
                    "locator": self.locator(self.run[0][0]),
                    "count": len(self.run),
                    "targets": [target for _, target in self.run[:5]],
                }
            )
        self.run = []

    def tool_use(self, lineno: int, block: dict) -> None:
        name = block.get("name") if isinstance(block.get("name"), str) else ""
        tool_input = block.get("input") if isinstance(block.get("input"), dict) else {}
        command = _command(tool_input) if name == "Bash" else ""
        if isinstance(block.get("id"), str):
            self.tools[block["id"]] = {"name": name, "line": lineno, "command": command}
        if name in _WRITE_TOOLS:
            self.flush_run()
        else:
            target = _explore_target(name, tool_input)
            if target is not None:
                self.run.append((lineno, target))
        if name == "Edit":
            self._edit(lineno, tool_input)

    def _edit(self, lineno: int, tool_input: dict) -> None:
        path, old, new = (tool_input.get(k) for k in ("file_path", "old_string", "new_string"))
        if not all(isinstance(v, str) for v in (path, old, new)):
            return
        if any(prev_old == new and prev_new == old for prev_old, prev_new in self.edits.get(path, [])):
            self.signals.append({"kind": "reverted_edit", "locator": self.locator(lineno), "file": redact(path)[:200]})
        self.edits.setdefault(path, []).append((old, new))

    def tool_result(self, lineno: int, block: dict) -> None:
        tool = self.tools.get(block.get("tool_use_id"), {"name": "unknown", "line": lineno, "command": ""})
        chars = _result_chars(block.get("content"))
        if chars > self.heavy_chars:
            self.signals.append(
                {"kind": "heavy_output", "locator": self.locator(lineno), "tool": tool["name"], "chars": chars}
            )
        command = tool["command"]
        if tool["name"] == "Bash" and command:
            entry = self.retries.get(command)
            if entry is not None:
                entry["count"] += 1
            elif block.get("is_error") is True:
                self.retries[command] = {"line": tool["line"], "count": 1}

    def user_turn(self, lineno: int, text: str) -> None:
        self.flush_run()
        if _CORRECTION.match(text):
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
                if text:
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="session_signals",
        description="Extract struggle signals from a Claude Code session log (read-only).",
    )
    parser.add_argument("log", help="path to a session .jsonl file")
    parser.add_argument("--max-line-bytes", type=int, default=DEFAULT_MAX_LINE_BYTES)
    parser.add_argument("--top", type=int, default=DEFAULT_TOP, help="max signals reported per kind")
    parser.add_argument("--heavy-chars", type=int, default=DEFAULT_HEAVY_CHARS, help="tool-result size that counts as heavy")
    args = parser.parse_args(argv)
    try:
        report = analyze(args.log, max_line_bytes=args.max_line_bytes, top=args.top, heavy_chars=args.heavy_chars)
    except OSError as exc:
        print(f"session_signals: cannot read {args.log}: {exc.strerror or exc}", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
