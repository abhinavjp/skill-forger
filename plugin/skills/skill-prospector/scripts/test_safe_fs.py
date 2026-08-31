#!/usr/bin/env python3
"""Unit tests for handle-anchored filesystem helpers."""
from __future__ import annotations

import contextlib
import errno
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import safe_fs
from safe_fs import SafeRoot

SafePathError = getattr(safe_fs, "SafePathError", ValueError)


class SafeRootTests(unittest.TestCase):
    def make_file_symlink(self, link: Path, target: Path):
        try:
            link.symlink_to(target)
        except (NotImplementedError, OSError) as exc:
            unsupported = getattr(exc, "winerror", None) in {1314, 1920}
            unsupported = unsupported or getattr(exc, "errno", None) in {
                errno.EPERM, errno.ENOSYS, errno.EOPNOTSUPP,
            }
            if unsupported:
                self.skipTest(f"file symlinks unavailable: {exc}")
            raise

    def make_dir_link(self, link: Path, target: Path):
        if os.name == "nt":
            command = ["cmd.exe", "/d", "/c", "mklink", "/J", os.fspath(link), os.fspath(target)]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                self.skipTest(f"junctions unavailable: {result.stderr or result.stdout}")
            return
        try:
            link.symlink_to(target, target_is_directory=True)
        except (NotImplementedError, OSError) as exc:
            unsupported = getattr(exc, "errno", None) in {
                errno.EPERM, errno.ENOSYS, errno.EOPNOTSUPP,
            }
            if unsupported:
                self.skipTest(f"directory symlinks unavailable: {exc}")
            raise

    def remove_dir_link(self, link: Path):
        if link.exists() or link.is_symlink():
            if os.name == "nt":
                os.rmdir(link)
            else:
                link.unlink()

    def test_rejects_lexical_escapes_and_empty_leafs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = SafeRoot(directory)
            bad_paths = [
                "", ".", "..", "../secret.md", "docs/../secret.md",
                "docs/./guide.md", "docs//guide.md", "docs/",
                os.path.abspath(os.path.join(directory, "guide.md")),
                "C:relative-drive.md", "\\\\server\\share\\secret.md",
                "bad\x00name.md",
            ]
            for bad_path in bad_paths:
                with self.subTest(path=bad_path):
                    with self.assertRaises(SafePathError):
                        root.read_text(bad_path)

    def test_public_api_is_limited_to_planned_operations(self):
        self.assertTrue(hasattr(safe_fs, "SafePathError"))
        public_methods = {
            name for name, value in vars(SafeRoot).items()
            if callable(value) and not name.startswith("_")
        }
        self.assertEqual(
            {"read_text", "read_bytes_with_stat", "write_text"},
            public_methods,
        )

    def test_normal_read_stat_and_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root_path = Path(directory)
            nested = root_path / "docs"
            nested.mkdir()
            (nested / "guide.md").write_bytes(b"hello")
            root = SafeRoot(root_path)

            raw, info = root.read_bytes_with_stat("docs/guide.md")
            self.assertEqual(b"hello", raw)
            self.assertEqual(5, info.st_size)

            root.write_text("docs/out.txt", "first\n")
            self.assertEqual("first\n", (nested / "out.txt").read_text(encoding="utf-8"))
            root.write_text("docs/out.txt", "second\n")
            self.assertEqual("second\n", (nested / "out.txt").read_text(encoding="utf-8"))

    def test_final_link_or_reparse_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root_path = Path(directory)
            external = Path(outside) / "secret.md"
            external.write_text("OUTSIDE SECRET\n", encoding="utf-8")
            root = SafeRoot(root_path)
            if os.name == "nt":
                link = root_path / "junction"
                self.make_dir_link(link, Path(outside))
                try:
                    with self.assertRaises(SafePathError):
                        root.read_bytes_with_stat("junction")
                finally:
                    self.remove_dir_link(link)
            else:
                self.make_file_symlink(root_path / "link.md", external)
                with self.assertRaises(SafePathError):
                    root.read_bytes_with_stat("link.md")

    def test_intermediate_link_or_reparse_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root_path = Path(directory)
            external = Path(outside)
            (external / "secret.md").write_text("OUTSIDE SECRET\n", encoding="utf-8")
            link = root_path / "link"
            self.make_dir_link(link, external)
            try:
                stdout = io.StringIO()
                stderr = io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    with self.assertRaises(SafePathError):
                        SafeRoot(root_path).read_bytes_with_stat("link/secret.md")
                self.assertNotIn("OUTSIDE SECRET", stdout.getvalue())
                self.assertNotIn("OUTSIDE SECRET", stderr.getvalue())
            finally:
                self.remove_dir_link(link)

    def test_same_handle_read_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root_path = Path(directory)
            target = root_path / "guide.md"
            replacement = root_path / "replacement.md"
            target.write_bytes(b"ORIGINAL")
            replacement.write_bytes(b"REPLACED")
            root = SafeRoot(root_path)

            if os.name == "nt":
                original_read_all = safe_fs._WindowsSafeRoot._read_all
                attempted = {"done": False}

                def swapping_read(handle, size):
                    if not attempted["done"]:
                        attempted["done"] = True
                        with contextlib.suppress(OSError):
                            os.replace(replacement, target)
                    return original_read_all(handle, size)

                with mock.patch.object(safe_fs._WindowsSafeRoot, "_read_all", side_effect=swapping_read):
                    raw, _ = root.read_bytes_with_stat("guide.md")
            else:
                original_fstat = safe_fs.os.fstat
                attempted = {"done": False}

                def swapping_fstat(fd):
                    info = original_fstat(fd)
                    if not attempted["done"] and stat_is_regular(info.st_mode):
                        attempted["done"] = True
                        os.replace(replacement, target)
                    return info

                with mock.patch.object(safe_fs.os, "fstat", side_effect=swapping_fstat):
                    raw, _ = root.read_bytes_with_stat("guide.md")

            self.assertEqual(b"ORIGINAL", raw)

    def test_handles_are_closed_after_failure(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root_path = Path(directory)
            link = root_path / "link"
            self.make_dir_link(link, Path(outside))
            try:
                if os.name == "nt":
                    opened = []
                    closed = []
                    original_open = safe_fs._WindowsSafeRoot._open
                    original_close = safe_fs._WindowsSafeRoot._close

                    def recording_open(path, access, creation, flags):
                        handle = original_open(path, access, creation, flags)
                        opened.append(handle)
                        return handle

                    def recording_close(handle):
                        closed.append(handle)
                        original_close(handle)

                    with mock.patch.object(safe_fs._WindowsSafeRoot, "_open", side_effect=recording_open):
                        with mock.patch.object(safe_fs._WindowsSafeRoot, "_close", side_effect=recording_close):
                            with self.assertRaises(SafePathError):
                                SafeRoot(root_path).read_bytes_with_stat("link/secret.md")
                    self.assertCountEqual(opened, closed)
                else:
                    opened = []
                    closed = []
                    original_open = safe_fs.os.open
                    original_close = safe_fs.os.close

                    def recording_open(*args, **kwargs):
                        descriptor = original_open(*args, **kwargs)
                        opened.append(descriptor)
                        return descriptor

                    def recording_close(descriptor):
                        closed.append(descriptor)
                        original_close(descriptor)

                    with mock.patch.object(safe_fs.os, "open", side_effect=recording_open):
                        with mock.patch.object(safe_fs.os, "close", side_effect=recording_close):
                            with self.assertRaises(SafePathError):
                                SafeRoot(root_path).read_bytes_with_stat("link/secret.md")
                    self.assertCountEqual(opened, closed)
            finally:
                self.remove_dir_link(link)

    @unittest.skipIf(os.name == "nt", "POSIX descriptor race probe")
    def test_posix_symlink_swap_before_leaf_open_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root_path = Path(directory)
            docs = root_path / "docs"
            docs.mkdir()
            target = docs / "guide.md"
            target.write_text("INTERNAL\n", encoding="utf-8")
            external = Path(outside) / "secret.md"
            external.write_text("OUTSIDE SECRET\n", encoding="utf-8")
            original_chain = safe_fs._PosixSafeRoot._open_parent_chain
            swapped = {"done": False}

            def swap_before_leaf(helper, parts):
                descriptors = original_chain(helper, parts)
                if not swapped["done"]:
                    swapped["done"] = True
                    target.unlink()
                    target.symlink_to(external)
                return descriptors

            with mock.patch.object(safe_fs._PosixSafeRoot, "_open_parent_chain", swap_before_leaf):
                with self.assertRaises(SafePathError):
                    SafeRoot(root_path).read_bytes_with_stat("docs/guide.md")
            self.assertEqual("OUTSIDE SECRET\n", external.read_text(encoding="utf-8"))

    @unittest.skipIf(os.name != "nt", "Windows junction race probe")
    def test_windows_junction_swap_before_leaf_open_is_blocked_or_rejected(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root_path = Path(directory)
            docs = root_path / "docs"
            docs.mkdir()
            target = docs / "guide.md"
            target.write_text("INTERNAL\n", encoding="utf-8")
            external = Path(outside)
            (external / "guide.md").write_text("OUTSIDE SECRET\n", encoding="utf-8")
            original_open = safe_fs._WindowsSafeRoot._open
            attempted = {"done": False}
            swapped = {"done": False}

            def swap_before_leaf(path, access, creation, flags):
                if Path(path) == docs and not attempted["done"]:
                    attempted["done"] = True
                    target.unlink()
                    docs.rmdir()
                    self.make_dir_link(docs, external)
                    swapped["done"] = True
                return original_open(path, access, creation, flags)

            try:
                with mock.patch.object(safe_fs._WindowsSafeRoot, "_open", side_effect=swap_before_leaf):
                    raw, _ = SafeRoot(root_path).read_bytes_with_stat("docs/guide.md")
            except SafePathError:
                pass
            else:
                self.assertNotIn(b"OUTSIDE SECRET", raw)
            finally:
                if docs.exists() or docs.is_symlink():
                    self.remove_dir_link(docs)
            self.assertTrue(attempted["done"])
            self.assertTrue(swapped["done"])

    def test_write_rejects_external_link_without_overwriting_sentinel(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root_path = Path(directory)
            external = Path(outside) / "sentinel.txt"
            external.write_text("OUTSIDE SECRET\n", encoding="utf-8")
            if os.name == "nt":
                link = root_path / "link"
                self.make_dir_link(link, Path(outside))
                relative = "link/sentinel.txt"
            else:
                link = root_path / "out.txt"
                self.make_file_symlink(link, external)
                relative = "out.txt"

            try:
                stdout = io.StringIO()
                stderr = io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    with self.assertRaises(SafePathError):
                        SafeRoot(root_path).write_text(relative, "changed\n")
                self.assertEqual("OUTSIDE SECRET\n", external.read_text(encoding="utf-8"))
                self.assertNotIn("OUTSIDE SECRET", stdout.getvalue())
                self.assertNotIn("OUTSIDE SECRET", stderr.getvalue())
            finally:
                if os.name == "nt":
                    self.remove_dir_link(link)

    @unittest.skipIf(os.name == "nt", "POSIX capability guard")
    def test_posix_missing_descriptor_capability_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root_path = Path(directory)
            (root_path / "guide.md").write_bytes(b"internal")
            helper = safe_fs._PosixSafeRoot(root_path)
            missing_capabilities = (
                ("O_DIRECTORY", 0),
                ("O_NOFOLLOW", 0),
                ("supports_dir_fd", set()),
            )
            for name, replacement in missing_capabilities:
                with self.subTest(capability=name):
                    with mock.patch.object(safe_fs.os, name, replacement):
                        with mock.patch.object(safe_fs.os, "open", wraps=os.open) as opened:
                            with self.assertRaisesRegex(SafePathError, "safe filesystem operation unavailable"):
                                helper.read_bytes(("guide.md",))
                    opened.assert_not_called()

    @unittest.skipIf(os.name == "nt", "POSIX exclusive-create race guard")
    def test_posix_write_refuses_racer_created_leaf(self):
        with tempfile.TemporaryDirectory() as directory:
            root_path = Path(directory)
            target = root_path / "out.txt"
            helper = safe_fs._PosixSafeRoot(root_path)
            original_open = safe_fs.os.open
            first_leaf_open = {"done": False}

            def racer(path, flags, mode=0o777, *, dir_fd=None):
                if path == "out.txt" and not first_leaf_open["done"]:
                    first_leaf_open["done"] = True
                    self.assertFalse(flags & os.O_CREAT)
                    target.write_bytes(b"RACER")
                    raise FileNotFoundError(errno.ENOENT, "raced")
                return original_open(path, flags, mode, dir_fd=dir_fd)

            with mock.patch.object(safe_fs.os, "open", side_effect=racer):
                with self.assertRaises(SafePathError):
                    helper.write_bytes(("out.txt",), b"OURS")
            self.assertEqual(b"RACER", target.read_bytes())

    @unittest.skipIf(os.name == "nt", "POSIX short-write guard")
    def test_posix_write_retries_short_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root_path = Path(directory)
            target = root_path / "out.txt"
            helper = safe_fs._PosixSafeRoot(root_path)
            original_write = safe_fs.os.write

            def short_write(descriptor, data):
                return original_write(descriptor, data[:2])

            with mock.patch.object(safe_fs.os, "write", side_effect=short_write):
                helper.write_bytes(("out.txt",), b"complete payload")
            self.assertEqual(b"complete payload", target.read_bytes())


def stat_is_regular(mode: int) -> bool:
    import stat
    return stat.S_ISREG(mode)


if __name__ == "__main__":
    unittest.main()
