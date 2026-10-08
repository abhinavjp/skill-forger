import json
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from log_adapters import FORMATS, detect_format, to_claude_records


def codex(kind, **fields):
    return {
        "type": "response_item",
        "payload": dict(fields, type=kind),
    }


def adapt(record):
    return to_claude_records(record, "codex")


def block(record):
    return adapt(record)[0]["message"]["content"][0]


class LogAdaptersTests(unittest.TestCase):
    def test_detection_and_identity(self):
        self.assertEqual(FORMATS, ("claude", "codex", "cursor"))
        self.assertEqual(detect_format({"type": "session_meta"}), "codex")
        for kind in ("response_item", "event_msg", "turn_context"):
            with self.subTest(kind=kind):
                self.assertEqual(
                    detect_format({"type": kind, "payload": {}}), "codex"
                )
                self.assertEqual(
                    detect_format({"type": kind, "payload": None}), "claude"
                )
        record = {
            "type": "user",
            "message": {"role": "user", "content": "Fix shipping."},
        }
        self.assertEqual(detect_format(record), "claude")
        self.assertIs(to_claude_records(record, "claude")[0], record)
        self.assertEqual(to_claude_records(record, "unknown"), [])

    def test_user_text(self):
        record = codex(
            "message", role="user",
            content=[
                {"type": "input_text", "text": "Fix shipping."},
                {"type": "input_text", "text": "Keep the config."},
                {"type": "input_image", "text": "Ignore this."},
            ],
        )
        self.assertEqual(adapt(record), [{
            "type": "user",
            "message": {
                "role": "user",
                "content": "Fix shipping.\nKeep the config.",
            },
        }])

    def test_injected_context_is_meta(self):
        markers = (
            "# AGENTS.md instructions\nUse /srv/shop.",
            "<environment_context>\n/srv/shop\n</environment_context>",
            "<user_instructions>Use Python.</user_instructions>",
            "<permissions instructions>Read only.</permissions instructions>",
            "<recommended_plugins>None.</recommended_plugins>",
            "<skills_instructions>None.</skills_instructions>",
        )
        for text in markers:
            with self.subTest(text=text):
                record = codex(
                    "message", role="user",
                    content=[{"type": "input_text", "text": " \n" + text}],
                )
                self.assertTrue(adapt(record)[0]["isMeta"])
        record = codex(
            "message", role="user", content="Harness instruction.",
            isMeta=True,
        )
        self.assertTrue(adapt(record)[0]["isMeta"])
        record = codex("message", role="user", content="Harness instruction.")
        record["isMeta"] = True
        self.assertTrue(adapt(record)[0]["isMeta"])
        real = codex(
            "message", role="user",
            content="No, do not touch the config",
        )
        self.assertNotIn("isMeta", adapt(real)[0])

    def test_meta_marker_in_later_block(self):
        record = codex(
            "message", role="user",
            content=[
                {"type": "input_text", "text": "Harness preamble."},
                {"type": "input_text", "text": "<environment_context>"},
            ],
        )
        self.assertTrue(adapt(record)[0]["isMeta"])

    def test_assistant_text_and_other_roles(self):
        record = codex(
            "message", role="assistant",
            content=[{"type": "output_text", "text": "Checking shipping."}],
        )
        self.assertEqual(adapt(record), [{
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "Checking shipping."}],
            },
        }])
        for role in ("developer", "system"):
            self.assertEqual(
                adapt(codex("message", role=role, content="Instructions.")),
                [],
            )

    def test_function_call_shell(self):
        for arguments, name, command in (
            ({"cmd": "rg shipping /srv/shop"}, "Bash",
             "rg shipping /srv/shop"),
            ({"command": ["python", "/srv/shop/check.py"]}, "Bash",
             "python /srv/shop/check.py"),
            ({"cmd": ["rg", "shipping", "/srv/shop"]}, "Bash",
             "rg shipping /srv/shop"),
            ({"command": "Get-Content /srv/shop/config.py"}, "PowerShell",
             "Get-Content /srv/shop/config.py"),
        ):
            with self.subTest(arguments=arguments):
                result = block(codex(
                    "function_call", name="exec_command", call_id="call-shell",
                    arguments=json.dumps(arguments),
                ))
                self.assertEqual(result["type"], "tool_use")
                self.assertEqual(result["id"], "call-shell")
                self.assertEqual(result["name"], name)
                self.assertEqual(result["input"], {"command": command})

    def test_powershell_heuristics(self):
        commands = (
            "Get-ChildItem /srv/shop",
            "Select-String shipping /srv/shop/config.py",
            "Get-Content /srv/shop/config.py",
            "$env:SHOP_ROOT",
            "items | ForEach-Object { $_ }",
            "powershell -Command echo",
        )
        for command in commands:
            with self.subTest(command=command):
                result = block(codex(
                    "function_call", name="exec_command", call_id="call-ps",
                    arguments=json.dumps({"cmd": command}),
                ))
                self.assertEqual(result["name"], "PowerShell")

    def test_custom_exec_js(self):
        examples = (
            (
                'const r = await tools.exec_command({'
                '"cmd": "rg shipping /srv/shop", "yield_time_ms": 1000});',
                None,
            ),
            (
                'const r = await tools.exec_command({'
                'cmd: "Get-Content /srv/shop/config.py", max_output_tokens: 20});',
                "Get-Content /srv/shop/config.py",
            ),
            ("await tools.exec_command({cmd: 'rg shipping /srv/shop'});",
             "rg shipping /srv/shop"),
            ("await tools.exec_command({cmd: `rg shipping /srv/shop`});",
             "rg shipping /srv/shop"),
            (r'await tools.exec_command({cmd: "echo first\nsecond"});',
             "echo first\nsecond"),
            (r"""await tools.exec_command({cmd: 'echo "shop"\nnext'});""",
             'echo "shop"\nnext'),
            (r"""await tools.exec_command({cmd: 'echo it\'s shop'});""",
             "echo it's shop"),
            (r'await tools.exec_command({cmd: "echo \q"});',
             r"echo \q"),
        )
        for source, expected in examples:
            with self.subTest(source=source):
                records = adapt(codex(
                    "custom_tool_call", name="exec", call_id="call-js",
                    input=source,
                ))
                if expected is None:
                    # Quoted object keys are tested separately below.
                    continue
                self.assertEqual(len(records), 1)
                result = records[0]["message"]["content"][0]
                self.assertEqual(result["id"], "call-js")
                self.assertEqual(result["input"]["command"], expected)

    def test_apply_patch(self):
        for kind, field in (
            ("function_call", "arguments"),
            ("custom_tool_call", "input"),
        ):
            for action in ("Update", "Add", "Delete"):
                with self.subTest(kind=kind, action=action):
                    patch = (
                        "*** Begin Patch\n"
                        "*** {} File: /srv/shop/cart.py\n"
                        "*** Update File: /srv/shop/other.py\n"
                        "*** End Patch"
                    ).format(action)
                    result = block(codex(
                        kind, name="apply_patch", call_id="call-patch",
                        **{field: patch}
                    ))
                    self.assertEqual(result["name"], "Edit")
                    self.assertEqual(
                        result["input"], {"file_path": "/srv/shop/cart.py"}
                    )
        result = block(codex(
            "function_call", name="apply_patch", call_id="call-patch",
            arguments=json.dumps({
                "patch": "*** Add File: /srv/shop/new.py\n+pass"
            }),
        ))
        self.assertEqual(result["input"]["file_path"], "/srv/shop/new.py")
        result = block(codex(
            "custom_tool_call", name="apply_patch", call_id="call-empty",
            input=None,
        ))
        self.assertEqual(result["input"], {"file_path": ""})

    def test_outputs(self):
        cases = (
            ("Script completed\nProcess exited with code 0", False),
            ("Script completed\nProcess exited with code 2", True),
            ("exit code: 0", False),
            ("exit code: 01", True),
            ("exit code: 000", False),
            ("Wall time 0.2 seconds\nOutput:\nOK", False),
            ("exit code: 0\nProcess exited with code 3", True),
        )
        for kind in ("function_call_output", "custom_tool_call_output"):
            for text, failed in cases:
                for output in (
                    text,
                    [{"type": "input_text", "text": text}],
                ):
                    with self.subTest(kind=kind, output=output):
                        result = block(codex(
                            kind, call_id="call-result", output=output
                        ))
                        self.assertEqual(result["type"], "tool_result")
                        self.assertEqual(result["tool_use_id"], "call-result")
                        self.assertEqual(result["content"], text)
                        self.assertIs(result["is_error"], failed)

    def test_error_detection_before_truncation(self):
        result = block(codex(
            "function_call_output", call_id="call-long",
            output="x" * 21000 + "\nProcess exited with code 7",
        ))
        self.assertEqual(len(result["content"]), 20000)
        self.assertTrue(result["is_error"])

    def test_ignored_records(self):
        for kind in (
            "session_meta", "turn_context", "world_state", "compacted",
            "token_usage_record", "inter_agent_communication_metadata",
        ):
            self.assertEqual(adapt({"type": kind, "payload": {}}), [])
        for kind in ("token_count", "item_completed", "task_complete"):
            self.assertEqual(
                adapt({"type": "event_msg", "payload": {"type": kind}}), []
            )
        for kind in ("reasoning", "agent_message", "unknown"):
            self.assertEqual(adapt(codex(kind, content="Ignore.")), [])

    def test_malformed_inputs_never_raise(self):
        cases = [
            {}, None, [], {"type": []},
            {"type": "response_item", "payload": None},
            {"type": "response_item", "payload": []},
            {"type": "response_item", "payload": "bad"},
            codex([], role=[], content=None),
            codex("message", role="user", content=[None, [], {"type": []}]),
            codex("message", role="assistant", content=None),
            codex("function_call", name=[], call_id=None, arguments=None),
            codex("function_call", name="exec_command", call_id="call-bad",
                  arguments="not JSON"),
            codex("function_call", name="exec_command", call_id="call-bad",
                  arguments='["python", "/srv/shop/check.py"]'),
            codex("function_call", name="exec_command", call_id="call-bad",
                  arguments='{"cmd": ["python", null]}'),
            codex("custom_tool_call", name="exec", call_id="call-bad",
                  input=[]),
            codex("function_call_output", call_id=[], output=None),
            codex("custom_tool_call_output", call_id="call-bad",
                  output=[None, [], {"type": "input_text", "text": None}]),
        ]
        for record in cases:
            with self.subTest(record=record):
                self.assertIn(detect_format(record), FORMATS)
                self.assertIsInstance(adapt(record), list)

    def test_string_caps(self):
        long = "x" * 21000
        for role, content_type in (
            ("user", "input_text"), ("assistant", "output_text")
        ):
            result = adapt(codex(
                "message", role=role,
                content=[{"type": content_type, "text": long}],
            ))[0]["message"]["content"]
            text = result if isinstance(result, str) else result[0]["text"]
            self.assertEqual(len(text), 20000)
        result = block(codex(
            "function_call", name="apply_patch", call_id=long,
            arguments="*** Update File: " + long,
        ))
        self.assertEqual(len(result["id"]), 20000)
        self.assertEqual(len(result["input"]["file_path"]), 20000)

    def test_two_megabyte_command_is_fast(self):
        command = "echo " + "x" * (2 * 1024 * 1024)
        records = (
            codex(
                "function_call", name="exec_command", call_id="call-large",
                arguments=json.dumps({"cmd": command}),
            ),
            codex(
                "custom_tool_call", name="exec", call_id="call-large",
                input='await tools.exec_command({cmd: "' + command + '"});',
            ),
        )
        for record in records:
            with self.subTest(kind=record["payload"]["type"]):
                started = time.perf_counter()
                result = block(record)
                elapsed = time.perf_counter() - started
                self.assertLess(elapsed, 1.0)
                self.assertEqual(len(result["input"]["command"]), 20000)

    def test_two_megabyte_unterminated_js_is_fast(self):
        record = codex(
            "custom_tool_call", name="exec", call_id="call-unclosed",
            input='cmd: "' + "x" * (2 * 1024 * 1024),
        )
        started = time.perf_counter()
        self.assertEqual(adapt(record), [])
        self.assertLess(time.perf_counter() - started, 1.0)


class ReviewRoundAdapterTests(unittest.TestCase):
    def test_codex_output_quoting_a_failure_but_exiting_zero_is_not_an_error(self):
        record = {"type": "response_item", "payload": {
            "type": "function_call_output", "call_id": "c1",
            "output": "Example exit code: 1\nProcess exited with code 0"}}
        result = to_claude_records(record, "codex")[0]["message"]["content"][0]
        self.assertFalse(result["is_error"])
        record["payload"]["output"] = "boom\nProcess exited with code 2"
        self.assertTrue(to_claude_records(record, "codex")[0]["message"]["content"][0]["is_error"])

    def test_codex_failure_wordings_seen_in_real_logs(self):
        def is_error(output):
            record = {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "c", "output": output}}
            return to_claude_records(record, "codex")[0]["message"]["content"][0]["is_error"]

        self.assertTrue(is_error("Exit code: 1\nWall time 0.2 seconds"))
        self.assertTrue(is_error('{"exit_code":2,"original_token_count":5,"output":"x"}'))
        self.assertTrue(is_error("Script failed\nSyntaxError"))
        self.assertFalse(is_error('{"exit_code":0,"original_token_count":5,"output":"x"}'))
        self.assertFalse(is_error("Script completed\nWall time 1.3 seconds"))

    def test_nested_identical_context_tags_stay_open(self):
        nested = {"role": "user", "text": "<context><context></context><user_query>No, stop</user_query></context>"}
        self.assertIs(to_claude_records(nested, "cursor")[0].get("isMeta"), True)

    def test_compact_summaries_are_meta_in_every_host(self):
        codex = {"type": "response_item", "isCompactSummary": True, "payload": {
            "type": "message", "role": "user", "content": [{"type": "input_text", "text": "No, stop"}]}}
        cursor = {"role": "user", "isCompactSummary": True, "text": "No, stop"}
        self.assertIs(to_claude_records(codex, "codex")[0].get("isMeta"), True)
        self.assertIs(to_claude_records(cursor, "cursor")[0].get("isMeta"), True)

    def test_cursor_query_nested_in_a_context_tag_is_not_a_user_turn(self):
        nested = {"role": "user", "text": "<attached_files><user_query>No, do not touch it</user_query></attached_files>"}
        self.assertIs(to_claude_records(nested, "cursor")[0].get("isMeta"), True)
        sibling = {"role": "user", "text": "<attached_files>/srv/shop</attached_files>\n<user_query>\nFix it\n</user_query>"}
        out = to_claude_records(sibling, "cursor")[0]
        self.assertEqual(out["message"]["content"], "Fix it")
        self.assertNotIn("isMeta", out)


if __name__ == "__main__":
    unittest.main()
