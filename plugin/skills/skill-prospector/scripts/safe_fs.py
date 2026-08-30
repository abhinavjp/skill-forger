"""Handle-anchored filesystem operations for skill-prospector scans."""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import ntpath
import os
import errno
import stat
from pathlib import Path


class SafePathError(ValueError):
    """A path or leaf object cannot be safely accessed under the root."""


_CAPABILITY_ERROR = "safe filesystem operation unavailable"


def _is_absolute_or_drive(value: str) -> bool:
    normalised = value.replace("\\", "/")
    return (
        os.path.isabs(value)
        or normalised.startswith("/")
        or ntpath.isabs(value)
        or bool(ntpath.splitdrive(value)[0])
    )


def _relative_parts(relative: str) -> tuple[str, ...]:
    if not isinstance(relative, str) or not relative or "\x00" in relative:
        raise SafePathError("path is not a contained relative path")
    if _is_absolute_or_drive(relative):
        raise SafePathError("path is not a contained relative path")
    normalised = relative.replace("\\", "/")
    parts = tuple(normalised.split("/"))
    if (
        not parts
        or parts[-1] == ""
        or any(part in ("", ".", "..") for part in parts)
    ):
        raise SafePathError("path is not a contained relative path")
    return parts


def _normalise_path(value: str) -> str:
    value = value.replace(os.sep, "/")
    return value[2:] if value.startswith("./") else value


def _absolute_to_relative(root: Path, value: str) -> tuple[str, ...]:
    candidate = Path(os.path.abspath(value))
    root_text = os.path.normcase(os.path.abspath(os.fspath(root)))
    candidate_text = os.path.normcase(os.path.abspath(os.fspath(candidate)))
    try:
        common = os.path.commonpath([root_text, candidate_text])
    except ValueError as exc:
        raise SafePathError("path is not contained by target root") from exc
    if common != root_text:
        raise SafePathError("path is not contained by target root")
    return _relative_parts(_normalise_path(os.path.relpath(candidate, root)))


class SafeRoot:
    """Read and write root-contained files without reopening verified leaves."""

    def __init__(self, root: Path | str):
        try:
            resolved = Path(root).resolve()
        except (OSError, RuntimeError) as exc:
            raise SafePathError("target root cannot be resolved") from exc
        if not resolved.is_dir():
            raise SafePathError("target root is not a directory")
        self._path = resolved

    def _parts(self, relative: str, *, allow_absolute: bool = False) -> tuple[str, ...]:
        if allow_absolute and _is_absolute_or_drive(relative):
            if not Path(relative).is_absolute():
                raise SafePathError("path is not contained by target root")
            return _absolute_to_relative(self._path, relative)
        return _relative_parts(relative)

    def read_bytes_with_stat(self, relative: str) -> tuple[bytes, os.stat_result]:
        parts = self._parts(relative)
        if os.name == "nt":
            return _WindowsSafeRoot(self._path).read_bytes(parts)
        return _PosixSafeRoot(self._path).read_bytes(parts)

    def read_text(self, relative: str) -> str:
        raw, _ = self.read_bytes_with_stat(relative)
        text = raw.decode("utf-8", errors="replace")
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def _verify_file(self, relative: str) -> None:
        parts = self._parts(relative)
        if os.name == "nt":
            _WindowsSafeRoot(self._path).verify_file(parts)
        else:
            _PosixSafeRoot(self._path).verify_file(parts)

    def write_text(self, relative: str, text: str) -> None:
        parts = self._parts(relative, allow_absolute=True)
        data = text.encode("utf-8")
        if os.name == "nt":
            _WindowsSafeRoot(self._path).write_bytes(parts, data)
        else:
            _PosixSafeRoot(self._path).write_bytes(parts, data)

    def _verify_directory(self, relative: str) -> None:
        parts = self._parts(relative)
        if os.name == "nt":
            _WindowsSafeRoot(self._path).verify_directory(parts)
        else:
            _PosixSafeRoot(self._path).verify_directory(parts)


class _PosixSafeRoot:
    def __init__(self, root: Path):
        self.root = root

    @staticmethod
    def _require_capabilities() -> None:
        required_flags = (getattr(os, "O_DIRECTORY", 0), getattr(os, "O_NOFOLLOW", 0))
        if os.open not in getattr(os, "supports_dir_fd", set()) or not all(required_flags):
            raise SafePathError(_CAPABILITY_ERROR)

    @staticmethod
    def _open_root(path: Path) -> int:
        flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_CLOEXEC", 0)
        return os.open(os.fspath(path), flags)

    @staticmethod
    def _open_child_dir(parent_fd: int, name: str) -> int:
        flags = (
            os.O_RDONLY
            | os.O_DIRECTORY
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0)
        )
        return os.open(name, flags, dir_fd=parent_fd)

    def _open_parent_chain(self, parts: tuple[str, ...]) -> list[int]:
        self._require_capabilities()
        descriptors = [self._open_root(self.root)]
        try:
            for part in parts[:-1]:
                descriptors.append(self._open_child_dir(descriptors[-1], part))
            return descriptors
        except BaseException:
            _close_all(descriptors)
            raise

    def read_bytes(self, parts: tuple[str, ...]) -> tuple[bytes, os.stat_result]:
        descriptors = self._open_parent_chain(parts)
        leaf_fd = None
        try:
            flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
            leaf_fd = os.open(parts[-1], flags, dir_fd=descriptors[-1])
            info = os.fstat(leaf_fd)
            if not stat.S_ISREG(info.st_mode):
                raise SafePathError("path is not a regular file")
            chunks = []
            while True:
                chunk = os.read(leaf_fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks), info
        except OSError as exc:
            raise SafePathError("path is not a regular file") from exc
        finally:
            if leaf_fd is not None:
                os.close(leaf_fd)
            _close_all(descriptors)

    def write_bytes(self, parts: tuple[str, ...], data: bytes) -> None:
        descriptors = self._open_parent_chain(parts)
        leaf_fd = None
        try:
            flags = os.O_WRONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
            try:
                leaf_fd = os.open(parts[-1], flags, dir_fd=descriptors[-1])
            except FileNotFoundError:
                leaf_fd = os.open(
                    parts[-1], flags | os.O_CREAT | os.O_EXCL, 0o666,
                    dir_fd=descriptors[-1],
                )
            info = os.fstat(leaf_fd)
            if not stat.S_ISREG(info.st_mode):
                raise SafePathError("path is not a regular file")
            os.ftruncate(leaf_fd, 0)
            remaining = memoryview(data)
            while remaining:
                written = os.write(leaf_fd, remaining)
                if written <= 0:
                    raise OSError(errno.EIO, "write made no progress")
                remaining = remaining[written:]
        except OSError as exc:
            raise SafePathError("path is not a regular file") from exc
        finally:
            if leaf_fd is not None:
                os.close(leaf_fd)
            _close_all(descriptors)

    def verify_file(self, parts: tuple[str, ...]) -> None:
        descriptors = self._open_parent_chain(parts)
        leaf_fd = None
        try:
            flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
            leaf_fd = os.open(parts[-1], flags, dir_fd=descriptors[-1])
            info = os.fstat(leaf_fd)
            if not stat.S_ISREG(info.st_mode):
                raise SafePathError("path is not a regular file")
        except OSError as exc:
            raise SafePathError("path is not a regular file") from exc
        finally:
            if leaf_fd is not None:
                os.close(leaf_fd)
            _close_all(descriptors)

    def verify_directory(self, parts: tuple[str, ...]) -> None:
        descriptors = self._open_parent_chain(parts + ("__leaf__",))
        try:
            pass
        finally:
            _close_all(descriptors)


def _close_all(descriptors: list[int]) -> None:
    for descriptor in reversed(descriptors):
        try:
            os.close(descriptor)
        except OSError:
            pass


if os.name == "nt":
    wintypes = ctypes.wintypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    CREATE_NEW = 1
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_DIRECTORY = 0x00000010
    FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    FILE_NAME_NORMALIZED = 0x0
    VOLUME_NAME_DOS = 0x0
    FileAttributeTagInfo = 9
    INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

    class FILE_ATTRIBUTE_TAG_INFO(ctypes.Structure):
        _fields_ = [
            ("FileAttributes", wintypes.DWORD),
            ("ReparseTag", wintypes.DWORD),
        ]

    class LARGE_INTEGER(ctypes.Structure):
        _fields_ = [("QuadPart", ctypes.c_longlong)]

    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.GetFileInformationByHandleEx.argtypes = [
        wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD,
    ]
    kernel32.GetFileInformationByHandleEx.restype = wintypes.BOOL
    kernel32.GetFinalPathNameByHandleW.argtypes = [
        wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD,
    ]
    kernel32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    kernel32.GetFileSizeEx.argtypes = [wintypes.HANDLE, ctypes.POINTER(LARGE_INTEGER)]
    kernel32.GetFileSizeEx.restype = wintypes.BOOL
    kernel32.ReadFile.argtypes = [
        wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID,
    ]
    kernel32.ReadFile.restype = wintypes.BOOL
    kernel32.WriteFile.argtypes = [
        wintypes.HANDLE, wintypes.LPCVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID,
    ]
    kernel32.WriteFile.restype = wintypes.BOOL
    kernel32.SetEndOfFile.argtypes = [wintypes.HANDLE]
    kernel32.SetEndOfFile.restype = wintypes.BOOL
    kernel32.SetFilePointerEx.argtypes = [
        wintypes.HANDLE, LARGE_INTEGER, ctypes.POINTER(LARGE_INTEGER), wintypes.DWORD,
    ]
    kernel32.SetFilePointerEx.restype = wintypes.BOOL


class _WindowsSafeRoot:
    def __init__(self, root: Path):
        self.root = root

    @staticmethod
    def _long_path(path: Path | str) -> str:
        text = os.path.abspath(os.fspath(path))
        if text.startswith("\\\\?\\"):
            return text
        if text.startswith("\\\\"):
            return "\\\\?\\UNC\\" + text[2:]
        return "\\\\?\\" + text

    @staticmethod
    def _open(path: Path | str, access: int, creation: int, flags: int):
        handle = kernel32.CreateFileW(
            _WindowsSafeRoot._long_path(path),
            access,
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            None,
            creation,
            flags,
            None,
        )
        if handle == INVALID_HANDLE_VALUE:
            raise SafePathError("path is not a regular file")
        return handle

    @staticmethod
    def _close(handle) -> None:
        if handle and handle != INVALID_HANDLE_VALUE:
            kernel32.CloseHandle(handle)

    @staticmethod
    def _attrs(handle) -> int:
        info = FILE_ATTRIBUTE_TAG_INFO()
        ok = kernel32.GetFileInformationByHandleEx(
            handle, FileAttributeTagInfo, ctypes.byref(info), ctypes.sizeof(info)
        )
        if not ok:
            raise SafePathError("path attributes cannot be verified")
        return int(info.FileAttributes)

    @staticmethod
    def _final_path(handle) -> str:
        size = 512
        while True:
            buffer = ctypes.create_unicode_buffer(size)
            needed = kernel32.GetFinalPathNameByHandleW(
                handle, buffer, size, FILE_NAME_NORMALIZED | VOLUME_NAME_DOS
            )
            if needed == 0:
                raise SafePathError("path cannot be verified")
            if needed < size:
                return buffer.value
            size = needed + 1

    @staticmethod
    def _normal_final(value: str) -> str:
        value = value.replace("/", "\\")
        if value.startswith("\\\\?\\UNC\\"):
            value = "\\\\" + value[8:]
        elif value.startswith("\\\\?\\"):
            value = value[4:]
        return os.path.normcase(os.path.normpath(value))

    def _expected_final(self, root_final: str, parts: tuple[str, ...]) -> str:
        suffix = "\\".join(parts)
        return self._normal_final(root_final + ("\\" + suffix if suffix else ""))

    def _open_chain(self, parts: tuple[str, ...], leaf_access: int, leaf_creation: int):
        handles = []
        root_handle = self._open(
            self.root, GENERIC_READ, OPEN_EXISTING,
            FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
        )
        handles.append(root_handle)
        try:
            root_attrs = self._attrs(root_handle)
            if root_attrs & FILE_ATTRIBUTE_REPARSE_POINT:
                raise SafePathError("target root cannot be verified")
            if not root_attrs & FILE_ATTRIBUTE_DIRECTORY:
                raise SafePathError("target root is not a directory")
            root_final = self._final_path(root_handle)
            current = self.root
            for index, part in enumerate(parts):
                current = current / part
                is_leaf = index == len(parts) - 1
                flags = FILE_FLAG_OPEN_REPARSE_POINT
                access = leaf_access if is_leaf else GENERIC_READ
                creation = leaf_creation if is_leaf else OPEN_EXISTING
                if not is_leaf:
                    flags |= FILE_FLAG_BACKUP_SEMANTICS
                handle = self._open(current, access, creation, flags)
                handles.append(handle)
                attrs = self._attrs(handle)
                if attrs & FILE_ATTRIBUTE_REPARSE_POINT:
                    raise SafePathError("path traverses a link or reparse point")
                if is_leaf:
                    if attrs & FILE_ATTRIBUTE_DIRECTORY:
                        raise SafePathError("path is not a regular file")
                elif not attrs & FILE_ATTRIBUTE_DIRECTORY:
                    raise SafePathError("path is not a directory")
                if self._normal_final(self._final_path(handle)) != self._expected_final(root_final, parts[:index + 1]):
                    raise SafePathError("path is not contained by target root")
            return handles
        except BaseException:
            self._close_all(handles)
            raise

    def read_bytes(self, parts: tuple[str, ...]) -> tuple[bytes, os.stat_result]:
        handles = self._open_chain(parts, GENERIC_READ, OPEN_EXISTING)
        try:
            leaf = handles[-1]
            size = LARGE_INTEGER()
            if not kernel32.GetFileSizeEx(leaf, ctypes.byref(size)):
                raise SafePathError("path size cannot be verified")
            raw = self._read_all(leaf, size.QuadPart)
            return raw, os.stat_result((0, 0, 0, 0, 0, 0, size.QuadPart, 0, 0, 0))
        finally:
            self._close_all(handles)

    def write_bytes(self, parts: tuple[str, ...], data: bytes) -> None:
        try:
            handles = self._open_chain(parts, GENERIC_WRITE, OPEN_EXISTING)
        except SafePathError:
            handles = self._open_chain(parts, GENERIC_WRITE, CREATE_NEW)
        try:
            leaf = handles[-1]
            zero = LARGE_INTEGER(0)
            if not kernel32.SetFilePointerEx(leaf, zero, None, 0):
                raise SafePathError("path cannot be written")
            if not kernel32.SetEndOfFile(leaf):
                raise SafePathError("path cannot be written")
            self._write_all(leaf, data)
        finally:
            self._close_all(handles)

    def verify_file(self, parts: tuple[str, ...]) -> None:
        handles = self._open_chain(parts, GENERIC_READ, OPEN_EXISTING)
        self._close_all(handles)

    def verify_directory(self, parts: tuple[str, ...]) -> None:
        handles = []
        root_handle = self._open(
            self.root, GENERIC_READ, OPEN_EXISTING,
            FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
        )
        handles.append(root_handle)
        try:
            root_attrs = self._attrs(root_handle)
            if root_attrs & FILE_ATTRIBUTE_REPARSE_POINT:
                raise SafePathError("target root cannot be verified")
            if not root_attrs & FILE_ATTRIBUTE_DIRECTORY:
                raise SafePathError("target root is not a directory")
            root_final = self._final_path(root_handle)
            current = self.root
            for index, part in enumerate(parts):
                current = current / part
                handle = self._open(
                    current, GENERIC_READ, OPEN_EXISTING,
                    FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
                )
                handles.append(handle)
                attrs = self._attrs(handle)
                if attrs & FILE_ATTRIBUTE_REPARSE_POINT:
                    raise SafePathError("path traverses a link or reparse point")
                if not attrs & FILE_ATTRIBUTE_DIRECTORY:
                    raise SafePathError("path is not a directory")
                if self._normal_final(self._final_path(handle)) != self._expected_final(root_final, parts[:index + 1]):
                    raise SafePathError("path is not contained by target root")
        finally:
            self._close_all(handles)

    @staticmethod
    def _read_all(handle, size: int) -> bytes:
        chunks = []
        remaining = size
        while remaining:
            count = min(remaining, 1024 * 1024)
            buffer = ctypes.create_string_buffer(count)
            read = wintypes.DWORD(0)
            ok = kernel32.ReadFile(handle, buffer, count, ctypes.byref(read), None)
            if not ok:
                raise SafePathError("path cannot be read")
            if read.value == 0:
                break
            chunks.append(buffer.raw[:read.value])
            remaining -= read.value
        return b"".join(chunks)

    @staticmethod
    def _write_all(handle, data: bytes) -> None:
        offset = 0
        while offset < len(data):
            chunk = data[offset:offset + 1024 * 1024]
            written = wintypes.DWORD(0)
            buffer = ctypes.create_string_buffer(chunk)
            ok = kernel32.WriteFile(
                handle, buffer, len(chunk), ctypes.byref(written), None
            )
            if not ok:
                raise SafePathError("path cannot be written")
            offset += written.value

    @classmethod
    def _close_all(cls, handles) -> None:
        for handle in reversed(handles):
            cls._close(handle)
