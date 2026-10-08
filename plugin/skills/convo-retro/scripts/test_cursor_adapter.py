"""Cursor adapter tests using invented transcripts and paths only."""

import json
import os
import sys
import time
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

import log_adapters
import session_signals


FIXTURE = os.path.join(SCRIPTS_DIR, "fixtures", "cursor-sample.jsonl")


def assistant_record(blocks):
    return {"role": "assistant", "message": {"content": blocks}}


def converted_blocks(record):
    records = log_adapters.to_claude_records(record, "cursor")
    if not records:
        return []
    return records[0]["message"]["content"]


class CursorAdapterTests(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(
            log_adapters.FORMATS, ("claude", "codex", "cursor")
        )

    def test_detection_preserves_claude_and_codex(self):
        claude_records = [
            {"type": "user", "message": {"content": "Hello"}},
            {"type": "assistant", "message": {"content": []}},
            {"type": "system"},
            {"type": "summary"},
            {"type": "progress"},
            {"type": "file-history-snapshot"},
            {"type": "queue-operation"},
            {"type": "response_item", "payload": None},
            {},
            None,
            [],
        ]
        for record in claude_records:
            with self.subTest(record=record):
                self.assertEqual(
                    log_adapters.detect_format(record), "claude"
                )

        codex_records = [
            {"type": "session_meta"},
            {"type": "response_item", "payload": {}},
            {"type": "event_msg", "payload": {}},
            {"type": "turn_context", "payload": {}},
            {
                "type": "response_item",
                "role": "user",
                "message": {"content": "Hello"},
                "payload": {},
            },
        ]
        for record in codex_records:
            with self.subTest(record=record):
                self.assertEqual(
                    log_adapters.detect_format(record), "codex"
                )

    def test_cursor_detection_and_claude_ambiguity(self):
        cursor_records = [
            {"role": "user", "message": {"content": "Hello"}},
            {"role": "assistant", "content": []},
            {"role": "human", "text": "Hello"},
            {"role": "ai", "content": "Hello"},
            {"type": "human", "content": "Hello"},
            {"type": "ai", "message": {"content": []}},
            {"turn_ended": True},
        ]
        for record in cursor_records:
            with self.subTest(record=record):
                self.assertEqual(
                    log_adapters.detect_format(record), "cursor"
                )

        for speaker in ("user", "assistant"):
            ambiguous = {
                "type": speaker,
                "role": speaker,
                "message": {"content": "Hello"},
            }
            self.assertEqual(
                log_adapters.detect_format(ambiguous), "claude"
            )
            self.assertEqual(
                log_adapters.to_claude_records(ambiguous, "claude"),
                [ambiguous],
            )

    def test_existing_codex_conversion(self):
        record = {
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "call_id": "sample-call",
                "name": "exec_command",
                "arguments": json.dumps(
                    {"cmd": "rg total /srv/shop"}
                ),
            },
        }
        self.assertEqual(
            log_adapters.to_claude_records(record, "codex"),
            [{
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [{
                        "type": "tool_use",
                        "id": "sample-call",
                        "name": "Bash",
                        "input": {"command": "rg total /srv/shop"},
                    }],
                },
            }],
        )

    def test_user_query_stripping_and_content_locations(self):
        wrapped = (
            "<attached_files>/srv/shop</attached_files>\n"
            "<user_query>\nUpdate the total helper.\n</user_query>\n"
            "<system_reminder>Invented context.</system_reminder>"
        )
        records = [
            {"role": "user", "message": {"content": wrapped}},
            {"role": "human", "content": wrapped},
            {"type": "human", "text": wrapped},
            {
                "role": "user",
                "message": {
                    "content": [{"type": "text", "text": wrapped}],
                },
            },
        ]
        expected = [{
            "type": "user",
            "message": {
                "role": "user",
                "content": "Update the total helper.",
            },
        }]
        for record in records:
            with self.subTest(record=record):
                self.assertEqual(
                    log_adapters.to_claude_records(record, "cursor"),
                    expected,
                )

    def test_incomplete_user_query_is_tolerated(self):
        record = {
            "role": "user",
            "text": "<user_query>\nUpdate the total helper.",
        }
        result = log_adapters.to_claude_records(record, "cursor")[0]
        self.assertEqual(
            result["message"]["content"], "Update the total helper."
        )
        self.assertNotIn("isMeta", result)

    def test_injected_context_is_meta(self):
        for tag in (
            "attached_files",
            "open_and_recently_viewed_files",
            "user_info",
            "system_reminder",
        ):
            text = "  <{0}>Invented context.</{0}>".format(tag)
            record = {"role": "user", "content": text}
            result = log_adapters.to_claude_records(
                record, "cursor"
            )[0]
            self.assertIs(result["isMeta"], True)
            self.assertEqual(result["message"]["content"], text)

        for text in ("Update /srv/shop.", "<3 items need updates."):
            result = log_adapters.to_claude_records(
                {"role": "user", "text": text}, "cursor"
            )[0]
            self.assertNotIn("isMeta", result)

        explicit = {
            "role": "user",
            "isMeta": True,
            "content": "Invented context.",
        }
        self.assertIs(
            log_adapters.to_claude_records(
                explicit, "cursor"
            )[0]["isMeta"],
            True,
        )

    def test_assistant_text_tools_ids_and_unknown_tools(self):
        record = assistant_record([
            {"type": "text", "text": "I will inspect the helper."},
            {
                "type": "tool_use",
                "name": "Read",
                "input": {"path": "/srv/shop/src/checkout.py"},
            },
            {
                "type": "tool_call",
                "id": "sample-edit",
                "name": "edit_file",
                "arguments": json.dumps({
                    "target_file": "/srv/shop/src/checkout.py",
                }),
            },
            {
                "type": "toolCall",
                "name": "InventedUnknownTool",
                "params": {"path": "/srv/shop"},
            },
            {
                "type": "tool_result",
                "tool_use_id": "sample-edit",
                "content": "Invented result.",
                "is_error": True,
            },
            {"type": "text", "text": "The helper is located."},
        ])
        expected = [
            {"type": "text", "text": "I will inspect the helper."},
            {
                "type": "tool_use",
                "id": "t1",
                "name": "Read",
                "input": {"file_path": "/srv/shop/src/checkout.py"},
            },
            {
                "type": "tool_use",
                "id": "sample-edit",
                "name": "Edit",
                "input": {"file_path": "/srv/shop/src/checkout.py"},
            },
            {"type": "text", "text": "The helper is located."},
        ]
        self.assertEqual(converted_blocks(record), expected)
        self.assertEqual(converted_blocks(record), expected)

        # An unrelated conversion cannot affect fallback IDs.
        converted_blocks(assistant_record([
            {"type": "tool_use", "name": "Read", "input": {}},
        ]))
        self.assertEqual(converted_blocks(record), expected)

        self.assertEqual(
            converted_blocks({"type": "ai", "text": "Located."}),
            [{"type": "text", "text": "Located."}],
        )
        self.assertEqual(
            converted_blocks(assistant_record([
                {"type": "tool_use", "name": "Unknown", "input": {}},
            ])),
            [],
        )

    def test_every_tool_name_mapping(self):
        cases = [
            (
                (
                    "shell", "run_terminal_cmd", "run_terminal_command",
                    "terminal", "bash", "powershell",
                ),
                {"command": "rg total /srv/shop"},
                "Bash",
                {"command": "rg total /srv/shop"},
            ),
            (
                ("read_file", "readfile", "read"),
                {"path": "/srv/shop/src/checkout.py"},
                "Read",
                {"file_path": "/srv/shop/src/checkout.py"},
            ),
            (
                (
                    "grep", "ripgrep", "rg", "codebase_search",
                    "semantic_search", "search",
                ),
                {"query": "total", "path": "/srv/shop"},
                "Grep",
                {"pattern": "total", "path": "/srv/shop"},
            ),
            (
                (
                    "glob", "glob_file_search", "list_dir",
                    "ls", "file_search",
                ),
                {"pattern": "/srv/shop/**/*.py"},
                "Glob",
                {"pattern": "/srv/shop/**/*.py"},
            ),
            (
                (
                    "strreplace", "str_replace", "edit_file",
                    "search_replace", "apply_patch",
                    "delete_file", "multiedit",
                ),
                {"target_file": "/srv/shop/src/checkout.py"},
                "Edit",
                {"file_path": "/srv/shop/src/checkout.py"},
            ),
            (
                ("write", "create", "create_file"),
                {"file_path": "/srv/shop/src/checkout.py"},
                "Write",
                {"file_path": "/srv/shop/src/checkout.py"},
            ),
        ]
        for aliases, arguments, mapped_name, expected_input in cases:
            for alias in aliases:
                with self.subTest(tool=alias):
                    blocks = converted_blocks(assistant_record([{
                        "type": "tool_use",
                        "name": alias.upper(),
                        "input": arguments,
                    }]))
                    self.assertEqual(blocks, [{
                        "type": "tool_use",
                        "id": "t0",
                        "name": mapped_name,
                        "input": expected_input,
                    }])

    def test_argument_fields_dicts_and_json_strings(self):
        arguments = {
            "command": "Get-Content /srv/shop/src/checkout.py",
        }
        for field in ("input", "args", "arguments", "params"):
            for value in (arguments, json.dumps(arguments)):
                with self.subTest(field=field, value=value):
                    block = {
                        "type": "toolCall",
                        "name": "Shell",
                        field: value,
                    }
                    self.assertEqual(
                        converted_blocks(assistant_record([block])),
                        [{
                            "type": "tool_use",
                            "id": "t0",
                            "name": "PowerShell",
                            "input": arguments,
                        }],
                    )

    def test_path_pattern_and_command_aliases(self):
        for key in ("path", "target_file", "file_path"):
            block = {
                "type": "tool_use",
                "name": "Read",
                "input": {key: "/srv/shop/src/checkout.py"},
            }
            self.assertEqual(
                converted_blocks(assistant_record([block]))[0]["input"],
                {"file_path": "/srv/shop/src/checkout.py"},
            )

        for key in ("pattern", "query", "regex"):
            block = {
                "type": "tool_use",
                "name": "Grep",
                "input": {key: "total", "path": "/srv/shop"},
            }
            self.assertEqual(
                converted_blocks(assistant_record([block]))[0]["input"],
                {"pattern": "total", "path": "/srv/shop"},
            )

        for key in ("cmd", "command"):
            block = {
                "type": "tool_use",
                "name": "Shell",
                "input": {key: ["rg", "total", "/srv/shop"]},
            }
            self.assertEqual(
                converted_blocks(assistant_record([block]))[0]["input"],
                {"command": "rg total /srv/shop"},
            )

        blocks = converted_blocks(assistant_record([{
            "type": "tool_use",
            "name": "list_dir",
            "input": {"path": "/srv/shop"},
        }]))
        self.assertEqual(
            blocks[0]["input"], {"pattern": "/srv/shop"}
        )

    def test_apply_patch_path_fallback(self):
        block = {
            "type": "tool_use",
            "name": "apply_patch",
            "input": (
                "*** Begin Patch\n"
                "*** Update File: /srv/shop/src/checkout.py\n"
                "@@\n-old\n+new\n"
                "*** End Patch"
            ),
        }
        self.assertEqual(
            converted_blocks(assistant_record([block]))[0]["input"],
            {"file_path": "/srv/shop/src/checkout.py"},
        )

    def test_turn_ended_and_missing_speaker_are_ignored(self):
        for record in (
            {"turn_ended": True},
            {"turn_ended": False, "role": "user", "text": "Hello"},
            {"turn_ended": None, "role": "assistant", "text": "Hello"},
            {"content": "Hello"},
            {"message": {"role": "assistant", "content": "Hello"}},
        ):
            with self.subTest(record=record):
                self.assertEqual(
                    log_adapters.to_claude_records(record, "cursor"), []
                )

    def test_malformed_inputs_never_raise(self):
        malformed = [
            None,
            False,
            42,
            "Invented plain text.",
            [],
            {},
            {"type": []},
            {"role": {}},
            {"role": "user", "message": []},
            {"role": "user", "content": {"text": "Hello"}},
            {"role": "assistant", "content": [None, 42, [], {}]},
            {"role": "assistant", "content": [{"type": []}]},
            assistant_record([{
                "type": "tool_use", "name": [], "input": {},
            }]),
            assistant_record([{
                "type": "tool_use", "name": "Shell", "input": "{",
            }]),
            assistant_record([{
                "type": "tool_use", "name": "Shell",
                "arguments": "[1, 2]",
            }]),
            assistant_record([{
                "type": "tool_use", "name": "Shell",
                "params": "[" * 2000 + "]" * 2000,
            }]),
            assistant_record([{
                "type": "tool_use", "name": "Read",
                "id": [], "input": {"path": {}},
            }]),
            assistant_record([{
                "type": "tool_use", "name": "Grep",
                "input": {"pattern": [], "path": None},
            }]),
        ]
        for index, record in enumerate(malformed):
            with self.subTest(index=index):
                self.assertIn(
                    log_adapters.detect_format(record),
                    log_adapters.FORMATS,
                )
                self.assertIsInstance(
                    log_adapters.to_claude_records(record, "cursor"),
                    list,
                )

    def test_copied_strings_are_capped(self):
        long_text = "x" * 20001
        record = assistant_record([
            {"type": "text", "text": long_text},
            {
                "type": "tool_use",
                "id": long_text,
                "name": "Shell",
                "input": {"command": long_text},
            },
            {
                "type": "tool_use",
                "name": "Read",
                "input": {"path": long_text},
            },
            {
                "type": "tool_use",
                "name": "Grep",
                "input": {"pattern": long_text, "path": long_text},
            },
            {
                "type": "tool_use",
                "name": "Glob",
                "input": {"pattern": long_text},
            },
            {
                "type": "tool_use",
                "name": "Edit_file",
                "input": {"file_path": long_text},
            },
        ])
        blocks = converted_blocks(record)
        self.assertEqual(len(blocks[0]["text"]), 20000)
        self.assertEqual(len(blocks[1]["id"]), 20000)
        for block in blocks[1:]:
            for value in block["input"].values():
                self.assertEqual(len(value), 20000)

        user = log_adapters.to_claude_records(
            {"role": "user", "text": long_text}, "cursor"
        )[0]
        self.assertEqual(len(user["message"]["content"]), 20000)

    def test_two_megabyte_strings_are_fast(self):
        long_text = "x" * (2 * 1024 * 1024)
        wrapped = "<user_query>\n" + long_text + "\n</user_query>"
        command_json = json.dumps({"command": long_text})

        started = time.perf_counter()
        user = log_adapters.to_claude_records(
            {"role": "user", "text": wrapped}, "cursor"
        )[0]
        assistant = converted_blocks(assistant_record([
            {"type": "text", "text": long_text},
            {
                "type": "tool_use",
                "name": "Shell",
                "arguments": command_json,
            },
        ]))
        # An unterminated tag-like string must not trigger a regex scan.
        meta = log_adapters.to_claude_records(
            {"role": "user", "text": "<attached_files " + long_text},
            "cursor",
        )[0]
        elapsed = time.perf_counter() - started

        self.assertEqual(len(user["message"]["content"]), 20000)
        self.assertEqual(len(assistant[0]["text"]), 20000)
        self.assertEqual(
            len(assistant[1]["input"]["command"]), 20000
        )
        self.assertIs(meta["isMeta"], True)
        self.assertLess(elapsed, 2.0)

    def test_fixture_conversion(self):
        with open(FIXTURE, encoding="utf-8") as handle:
            source = [json.loads(line) for line in handle if line.strip()]
        self.assertEqual(len(source), 14)
        self.assertTrue(all(
            log_adapters.detect_format(record) == "cursor"
            for record in source
        ))

        converted = []
        for record in source:
            converted.extend(
                log_adapters.to_claude_records(record, "cursor")
            )
        self.assertEqual(len(converted), 13)
        self.assertIs(converted[1]["isMeta"], True)
        self.assertEqual(
            converted[0]["message"]["content"],
            (
                "Find the checkout total calculation in /srv/shop "
                "and update only the total helper."
            ),
        )

        tools = [
            block
            for record in converted
            if record["type"] == "assistant"
            for block in record["message"]["content"]
            if block["type"] == "tool_use"
        ]
        self.assertEqual(
            [block["name"] for block in tools],
            ["Bash", "Grep", "Glob", "Bash", "Edit"],
        )
        self.assertFalse(any(
            isinstance(record["message"]["content"], list)
            and any(
                block.get("type") == "tool_result"
                for block in record["message"]["content"]
            )
            for record in converted
        ))

    def test_fixture_through_session_signals_analyze(self):
        # Assumed existing API: analyze(path) returns a signals mapping/list.
        report = session_signals.analyze(FIXTURE)
        self.assertIsInstance(report, dict)
        self.assertIn("signals", report)
        signals = report["signals"]

        if isinstance(signals, dict):
            names = [
                name for name, evidence in signals.items() if evidence
            ]
        else:
            self.assertIsInstance(signals, list)
            names = []
            for signal in signals:
                if isinstance(signal, str):
                    names.append(signal)
                    continue
                self.assertIsInstance(signal, dict)
                name = None
                for key in ("signal", "name", "kind", "type", "id", "code"):
                    value = signal.get(key)
                    if isinstance(value, str):
                        name = value
                        break
                self.assertIsNotNone(
                    name, "Each signal must identify its signal category."
                )
                names.append(name)

        self.assertEqual(
            sorted(names), ["search_thrash", "user_correction"]
        )
        self.assertNotIn("retry_loop", names)


if __name__ == "__main__":
    unittest.main()
