#!/usr/bin/env python3
"""Tests for the deterministic Merge Sentinel corpus validator."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VALIDATOR = ROOT / "validate_corpus.py"


class ValidateCorpusTests(unittest.TestCase):
    def run_validator(self, eval_root: Path, *extra: str):
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(eval_root), *extra],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

    def copy_corpus(self, directory: str) -> Path:
        target = Path(directory) / "evals"
        shutil.copytree(
            ROOT,
            target,
            ignore=shutil.ignore_patterns("__pycache__", "test_*.py"),
        )
        return target

    def read_json(self, root: Path, name: str):
        return json.loads((root / name).read_text(encoding="utf-8"))

    def write_json(self, root: Path, name: str, value) -> None:
        (root / name).write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )

    def assert_mutation_error(self, mutate, expected: str) -> None:
        with tempfile.TemporaryDirectory(prefix="merge-sentinel-corpus-") as directory:
            root = self.copy_corpus(directory)
            mutate(root)
            result = self.run_validator(root, "--json")
            self.assertNotEqual(0, result.returncode, result.stdout)
            report = json.loads(result.stdout)
            self.assertTrue(
                any(expected in error.get("error", "") for error in report["errors"]),
                report["errors"],
            )

    def test_real_corpus_is_schema_complete(self):
        result = self.run_validator(ROOT, "--json")
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertIsInstance(report, dict)
        self.assertEqual(5, len(report["files"]))
        self.assertEqual(5, len(set(report["files"])))
        self.assertGreater(report["case_count"], 0)
        self.assertEqual([], report["errors"])

    def test_id_only_case_record_is_rejected(self):
        def mutate(root: Path) -> None:
            cases = self.read_json(root, "cases.json")
            cases[0] = {"id": cases[0]["id"]}
            self.write_json(root, "cases.json", cases)

        self.assert_mutation_error(mutate, "cases.json[clean-mr]")

    def test_missing_fixture_required_key_is_rejected(self):
        def mutate(root: Path) -> None:
            path = root / "fixtures" / "clean-mr" / "input.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            del value["head_files"]
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

        self.assert_mutation_error(mutate, "clean-mr/input.json")

    def test_broken_fixture_reference_is_rejected(self):
        def mutate(root: Path) -> None:
            cases = self.read_json(root, "cases.json")
            cases[0]["input"] = "fixtures/clean-mr/missing.json"
            self.write_json(root, "cases.json", cases)

        self.assert_mutation_error(mutate, "cases.json[clean-mr].input")

    def test_duplicate_json_object_key_is_rejected(self):
        def mutate(root: Path) -> None:
            (root / "quality-inputs.json").write_text(
                '{"cases": [], "cases": []}\n', encoding="utf-8"
            )

        self.assert_mutation_error(mutate, "quality-inputs.json: duplicate JSON key")

    def test_quality_contract_divergence_is_rejected(self):
        def mutate(root: Path) -> None:
            contracts = self.read_json(root, "quality-contracts.json")
            contracts["cases"][0]["expected_findings"] = ["drifted"]
            self.write_json(root, "quality-contracts.json", contracts)

        self.assert_mutation_error(mutate, "quality-cases.json[clean-preserved-contract]")

    def test_trigger_boolean_type_is_rejected(self):
        def mutate(root: Path) -> None:
            queries = self.read_json(root, "trigger_queries.json")
            queries[0]["expected"] = "true"
            self.write_json(root, "trigger_queries.json", queries)

        self.assert_mutation_error(mutate, "trigger_queries.json[01].expected")

    def test_invalid_root_returns_two(self):
        result = self.run_validator(Path("does-not-exist"), "--json")
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("evaluation root", result.stderr)


if __name__ == "__main__":
    unittest.main()
