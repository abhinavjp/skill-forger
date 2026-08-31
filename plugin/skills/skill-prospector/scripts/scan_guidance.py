#!/usr/bin/env python3
"""Scan repository guidance into compact, provenance-preserving metadata.

Usage:
    scan_guidance.py scan <root> [--json] [--out PATH] [--max-bytes N]
    scan_guidance.py slice <root> <relative-path> --scan-id TOKEN \
        (--section <heading> | --document) [--max-bytes N]

The scanner reads target files and writes only the explicitly requested JSON
inventory. It never executes target content. ``slice`` is a deliberately
narrow, heading-scoped second read for classification ambiguity.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import sys
from pathlib import Path

from safe_fs import SafePathError, SafeRoot

HERE = Path(__file__).resolve().parent
DEFAULT_EXCLUDED_DIRS = {
    ".git", "node_modules", "vendor", "dist", "build", "target", ".venv"
}
KNOWN_GUIDANCE_BASENAMES = {
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", "SKILL.md",
    "CONTRIBUTING.md", "CONVENTIONS.md",
}
TEXT_EXTENSIONS = {".md", ".markdown", ".mdc", ".txt", ".rst"}
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(.+?)\s*$")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)")
SCANNER_VERSION = 1


class _ContainmentError(ValueError):
    """A requested path cannot be safely bound to the target root."""


class _SliceOutputError(ValueError):
    """A bounded slice cannot retain both provenance and its truncation marker."""


def _canonical_root(root: Path) -> Path:
    try:
        resolved = root.resolve()
    except (OSError, RuntimeError) as exc:
        raise _ContainmentError("target root cannot be resolved") from exc
    if not resolved.is_dir():
        raise _ContainmentError("target root is not a directory")
    return resolved


def _load_patterns():
    data = json.loads(SafeRoot(HERE).read_text("patterns.json"))
    if data.get("version") != 1:
        raise ValueError("patterns.json version must be 1")
    return data


def _normalise_path(value: str) -> str:
    value = value.replace("\\", "/").replace(os.sep, "/")
    return value[2:] if value.startswith("./") else value


def _glob_match(path: str, pattern: str) -> bool:
    """Match repository-relative paths with useful gitignore-like semantics."""
    path = _normalise_path(path)
    pattern = pattern.replace("\\", "/")
    directory_pattern = pattern.endswith("/")
    pattern = pattern.rstrip("/")
    anchored = pattern.startswith("/")
    pattern = pattern.lstrip("/")
    candidates = [path]
    if not anchored:
        candidates.extend(path.split("/"))
    if fnmatch.fnmatchcase(path, pattern):
        return True
    if not anchored and "/" in pattern and fnmatch.fnmatchcase(path, f"*/{pattern}"):
        return True
    if pattern.startswith("**/") and fnmatch.fnmatchcase(path, pattern[3:]):
        return True
    if "/" not in pattern and any(
        fnmatch.fnmatchcase(candidate, pattern) for candidate in candidates
    ):
        return True
    if directory_pattern and (path == pattern or path.startswith(pattern + "/")):
        return True
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        if path == prefix or path.startswith(prefix + "/"):
            return True
    return False


def _read_gitignore(safe_root: SafeRoot):
    try:
        if not os.path.lexists(os.fspath(safe_root._path / ".gitignore")):
            return []
        lines = safe_root.read_text(".gitignore").splitlines()
    except (SafePathError, OSError) as exc:
        raise SafePathError("gitignore cannot be read") from exc
    rules = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        negated = line.startswith("!")
        if negated:
            line = line[1:]
        if line:
            rules.append((line, negated))
    return rules


def _gitignored(path: str, is_dir: bool, rules) -> bool:
    ignored = False
    for pattern, negated in rules:
        candidate = path + "/" if is_dir else path
        if _glob_match(candidate, pattern):
            ignored = not negated
    return ignored


def _excluded(path: str, is_dir: bool, exclusions) -> str | None:
    parts = path.split("/")
    if is_dir and parts[-1] in DEFAULT_EXCLUDED_DIRS:
        return "default-directory"
    for pattern in exclusions:
        if _glob_match(path, pattern):
            return pattern
        if is_dir and _glob_match(path + "/", pattern):
            return pattern
    return None


def _catalogue_entries(rel_path: str, catalogue):
    return [
        entry for entry in catalogue
        if any(_glob_match(rel_path, glob) for glob in entry.get("globs", []))
    ]


def _resolve_directory_within(root: Path, relative: str) -> Path:
    canonical_root = _canonical_root(root)
    safe_root = SafeRoot(canonical_root)
    try:
        parts = safe_root._parts(relative)
        safe_root._verify_directory(relative)
    except SafePathError as exc:
        raise _ContainmentError("directory cannot be resolved") from exc
    return canonical_root.joinpath(*parts)


def _could_contain_guidance(root: Path, relative: str, catalogue) -> bool:
    """Permit ignored directories only for known roots or direct guidance names."""
    if _catalogue_entries(relative, catalogue):
        return True
    try:
        directory = _resolve_directory_within(root, relative)
        with os.scandir(directory) as entries:
            return any(entry.name in KNOWN_GUIDANCE_BASENAMES for entry in entries)
    except (OSError, _ContainmentError):
        return False


def _directive_regexes(patterns):
    return [re.compile(marker, re.IGNORECASE) for marker in patterns]


def _is_directive(line: str, marker_regexes) -> bool:
    return any(marker.search(line) for marker in marker_regexes)


def _headings(lines):
    found = []
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if not match:
            continue
        title = re.sub(r"\s+#+\s*$", "", match.group(2)).strip()
        found.append({"level": len(match.group(1)), "title": title,
                      "line": index + 1, "index": index})
    return found


def _markdown_metrics(text: str, marker_regexes):
    lines = text.splitlines(keepends=True)
    headings = _headings(lines)
    directive_count = sum(
        1 for line in lines if line.strip() and _is_directive(line, marker_regexes)
    )
    code_fence_count = 0
    inside_fence = False
    for line in lines:
        if not line.lstrip().startswith(("```", "~~~")):
            continue
        if not inside_fence:
            code_fence_count += 1
        inside_fence = not inside_fence
    cross_references = []
    for target in LINK_RE.findall(text):
        if target.startswith(("http:", "https:", "mailto:", "#")):
            continue
        if target not in cross_references:
            cross_references.append(target)

    outline = []
    for position, heading in enumerate(headings):
        boundary = len(lines)
        for next_heading in headings[position + 1:]:
            if next_heading["level"] <= heading["level"]:
                boundary = next_heading["index"]
                break
        section_directives = sum(
            1 for line in lines[heading["index"] + 1:boundary]
            if line.strip() and _is_directive(line, marker_regexes)
        )
        outline.append({
            "level": heading["level"],
            "title": heading["title"],
            "line": heading["line"],
            "directives": section_directives,
        })
    return outline, directive_count, code_fence_count, cross_references


def _sha256(raw: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(raw)
    return digest.hexdigest()


def _canonical_json_digest(value) -> str:
    rendered = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return _sha256(rendered.encode("utf-8"))


def _make_scan_id(root: Path, max_bytes: int, patterns, pairs) -> str:
    payload = {
        "root": str(root.resolve()),
        "scanner_version": SCANNER_VERSION,
        "pattern_catalogue_sha256": _canonical_json_digest(patterns),
        "max_bytes": max_bytes,
        "files": sorted([[path, digest] for path, digest in pairs]),
    }
    return f"v2:{max_bytes}:{_canonical_json_digest(payload)}"


def _parse_scan_id(value: str) -> tuple[int, str]:
    version, separator, remainder = value.partition(":")
    max_text, second_separator, digest = remainder.partition(":")
    if version != "v2" or separator != ":" or second_separator != ":":
        raise _ContainmentError("scan id must be a v2 inventory token")
    try:
        max_bytes = int(max_text)
    except ValueError as exc:
        raise _ContainmentError("scan id has invalid max bytes") from exc
    if max_bytes <= 0 or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise _ContainmentError("scan id is invalid")
    return max_bytes, digest


def _relative_error_path(root: Path, value) -> str:
    if not value:
        return ""
    try:
        path = Path(value)
        if path.is_absolute():
            return _normalise_path(os.path.relpath(str(path), str(root)))
    except (OSError, ValueError):
        pass
    text = _normalise_path(os.fspath(value))
    if text.startswith("../") or text == "..":
        return Path(text).name
    return text


def _build_inventory(root: Path, max_bytes: int | None):
    patterns = _load_patterns()
    heuristic = patterns["heuristic"]
    if max_bytes is None:
        max_bytes = heuristic["max_bytes"]
    marker_regexes = _directive_regexes(heuristic["directive_markers"])
    safe_root = SafeRoot(root)
    matched_units = []
    skipped = []
    errors = []
    scanned_files = 0
    truncated = False
    ignored_guidance_count = 0

    try:
        gitignore = _read_gitignore(safe_root)
    except (SafePathError, OSError, UnicodeError):
        gitignore = []
        errors.append({"path": ".gitignore", "error": "gitignore read failed"})

    def onerror(error):
        errors.append({
            "path": _relative_error_path(root, getattr(error, "filename", "")),
            "error": "walk failed",
        })

    walk = os.walk(str(root), topdown=True, onerror=onerror) if not errors else ()
    for base, dirs, names in walk:
        base_path = Path(base)
        kept_dirs = []
        for dirname in sorted(dirs):
            full_dir = base_path / dirname
            rel_dir = _normalise_path(os.path.relpath(str(full_dir), str(root)))
            reason = _excluded(rel_dir, True, patterns.get("exclusions", []))
            if reason is not None:
                skipped.append({"path": rel_dir, "reason": f"excluded:{reason}"})
            else:
                kept_dirs.append(dirname)
        dirs[:] = kept_dirs

        for filename in sorted(names):
            full_path = base_path / filename
            rel_path = _normalise_path(os.path.relpath(str(full_path), str(root)))
            exclusion = _excluded(rel_path, False, patterns.get("exclusions", []))
            if exclusion is not None:
                skipped.append({"path": rel_path, "reason": f"excluded:{exclusion}"})
                continue
            entries = _catalogue_entries(rel_path, patterns["catalogue"])
            ignored_by_git = _gitignored(rel_path, False, gitignore)
            if ignored_by_git and not entries:
                skipped.append({"path": rel_path, "reason": "excluded:.gitignore"})
                continue
            try:
                safe_root._verify_file(rel_path)
            except SafePathError:
                errors.append({
                    "path": rel_path,
                    "error": "candidate rejected by containment",
                })
                continue
            scanned_files += 1
            is_heuristic_candidate = (
                full_path.suffix.lower() in set(heuristic["extensions"])
            )
            if not entries and not is_heuristic_candidate:
                continue

            reasons = [f"catalogue:{entry['id']}" for entry in entries]
            host_affinity = [host for entry in entries
                             for host in entry.get("host_affinity", [])]
            if entries:
                current_mechanism = entries[0].get("current_mechanism", "unknown")
            else:
                current_mechanism = "prose-doc"
            try:
                raw, info = safe_root.read_bytes_with_stat(rel_path)
                size = info.st_size
                record = _read_file_metadata(
                    raw, rel_path, size, reasons, host_affinity,
                    current_mechanism, max_bytes, marker_regexes
                )
            except SafePathError:
                errors.append({
                    "path": rel_path,
                    "error": "candidate rejected by containment",
                })
                continue
            except (OSError, UnicodeError):
                errors.append({"path": rel_path, "error": "candidate read failed"})
                continue

            record["source_scope"] = "catalogue" if entries else "heuristic"
            record["ignored_by_git"] = ignored_by_git

            matched = False
            if record.get("status") == "oversize":
                record["match_reason"].append("heuristic:oversize")
                truncated = True
                matched = True
            elif entries or record["directive_count"] >= heuristic["min_directives"]:
                if not entries:
                    record["match_reason"].append("heuristic:imperative-density")
                matched = True
            if matched:
                matched_units.append(record)
                if ignored_by_git and entries:
                    ignored_guidance_count += 1

    scan_pairs = [(unit["path"], unit["sha256"]) for unit in matched_units]
    result = {
        "version": 1,
        "root": str(root.resolve()),
        "scanned_files": scanned_files,
        "matched_units": matched_units,
        "skipped": skipped,
        "scan_id": _make_scan_id(root, max_bytes, patterns, scan_pairs),
        "ignored_guidance_count": ignored_guidance_count,
        "truncated": truncated,
        "errors": errors,
    }
    return result, {path: digest for path, digest in scan_pairs}


def _read_file_metadata(raw: bytes, rel_path: str, size: int, match_reason,
                         host_affinity, current_mechanism: str, max_bytes: int,
                         marker_regexes):
    """Read one candidate once and return metadata without retaining its body."""
    record = {
        "path": rel_path,
        "bytes": size,
        "token_estimate": size // 4,
        "sha256": _sha256(raw),
        "match_reason": list(match_reason),
        "host_affinity": list(dict.fromkeys(host_affinity or ["none"])),
        "current_mechanism": current_mechanism,
        "outline": [],
        "directive_count": 0,
        "code_fence_count": 0,
        "cross_references": [],
    }
    if size > max_bytes:
        record["status"] = "oversize"
        return record
    rel_as_path = Path(rel_path)
    if rel_as_path.suffix.lower() in TEXT_EXTENSIONS or rel_as_path.name in {
        "AGENTS.md", "CLAUDE.md", "GEMINI.md", "SKILL.md",
        "CONTRIBUTING.md", "CONVENTIONS.md", ".cursorrules",
        ".windsurfrules"
    }:
        text = raw.decode("utf-8", errors="replace")
        (record["outline"], record["directive_count"],
         record["code_fence_count"], record["cross_references"]
         ) = _markdown_metrics(text, marker_regexes)
    return record


def _scan(args):
    try:
        root = _canonical_root(Path(args.root))
    except _ContainmentError:
        print("error: scan root is not a directory or is not readable",
              file=sys.stderr)
        return 2
    safe_root = SafeRoot(root)
    try:
        result, _ = _build_inventory(root, args.max_bytes)
    except (SafePathError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: cannot load pattern catalogue: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(result, indent=2) + "\n"
    if args.out:
        try:
            safe_root.write_text(args.out, rendered)
        except SafePathError:
            print("error: inventory output must stay inside scan root", file=sys.stderr)
            return 2
        except OSError as exc:
            print(f"error: cannot write inventory: {exc}", file=sys.stderr)
            return 2
    sys.stdout.write(rendered)
    return 2 if result["errors"] else 0


def _slice_output(path: str, start: int, lines: list[str], max_bytes: int):
    """Render the longest complete-line slice that fits its byte budget."""
    source_lines = list(lines)
    full_end = start + len(source_lines) - 1
    full_header = f"{path}:{start}-{full_end}\n"
    full_body = "".join(source_lines)
    full = full_header + full_body
    if len(full.encode("utf-8")) <= max_bytes:
        return full

    marker = "[truncated]"
    for count in range(len(source_lines), -1, -1):
        actual_end = start + count - 1
        header = f"{path}:{start}-{actual_end}\n"
        body = "".join(source_lines[:count])
        separator = "" if not body or body.endswith(("\n", "\r")) else "\n"
        rendered = header + body + separator + marker
        if len(rendered.encode("utf-8")) <= max_bytes:
            return rendered

    raise _SliceOutputError("slice limit is too small for provenance and truncation marker")


def _slice(args):
    try:
        root = _canonical_root(Path(args.root))
        safe_root = SafeRoot(root)
        relative_path = "/".join(safe_root._parts(args.relative_path))
    except (SafePathError, _ContainmentError):
        print("error: slice path must stay inside target root", file=sys.stderr)
        return 2
    if not args.scan_id:
        print("error: scan id is required for slice", file=sys.stderr)
        return 2
    try:
        inventory_max_bytes, _ = _parse_scan_id(args.scan_id)
    except _ContainmentError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    try:
        result, matched_pairs = _build_inventory(root, inventory_max_bytes)
    except (SafePathError, OSError, ValueError, json.JSONDecodeError):
        print("error: scan membership cannot be verified", file=sys.stderr)
        return 2
    if result["errors"]:
        print("error: scan membership cannot be verified", file=sys.stderr)
        return 2
    if result["scan_id"] != args.scan_id:
        print("error: scan id does not match current inventory", file=sys.stderr)
        return 2
    matched_digest = matched_pairs.get(relative_path)
    if matched_digest is None:
        print("error: slice path is absent from scan inventory", file=sys.stderr)
        return 2
    try:
        raw, _ = safe_root.read_bytes_with_stat(relative_path)
    except (SafePathError, OSError):
        print("error: cannot read slice path", file=sys.stderr)
        return 2
    if matched_digest is not None and _sha256(raw) != matched_digest:
        print("error: slice path digest does not match inventory", file=sys.stderr)
        return 2
    text = raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.splitlines(keepends=True)
    if args.document:
        start_line = 1
        selected_lines = lines
    else:
        headings = _headings(lines)
        exact = [heading for heading in headings if heading["title"] == args.section]
        matches = exact or [
            heading for heading in headings
            if heading["title"].casefold() == args.section.casefold()
        ]
        if not matches:
            print(f"error: section not found: {args.section}", file=sys.stderr)
            return 4
        if len(matches) > 1:
            print(f"error: section is ambiguous: {args.section}", file=sys.stderr)
            for heading in matches:
                print(f"  {heading['line']}: {heading['title']}", file=sys.stderr)
            return 3
        selected = matches[0]
        end_index = len(lines)
        for heading in headings:
            if heading["index"] <= selected["index"]:
                continue
            if heading["level"] <= selected["level"]:
                end_index = heading["index"]
                break
        start_line = selected["line"]
        selected_lines = lines[selected["index"]:end_index]
    display_path = _normalise_path(relative_path)
    try:
        rendered = _slice_output(display_path, start_line, selected_lines,
                                 args.max_bytes)
    except _SliceOutputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(rendered)
    return 0


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser("scan", help="scan a target repository")
    scan.add_argument("root")
    scan.add_argument("--json", action="store_true", help="emit JSON (default)")
    scan.add_argument("--out")
    scan.add_argument("--max-bytes", type=_positive_int)
    slice_parser = subparsers.add_parser("slice", help="read one heading span")
    slice_parser.add_argument("root")
    slice_parser.add_argument("relative_path")
    selector = slice_parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--section")
    selector.add_argument("--document", action="store_true")
    slice_parser.add_argument("--max-bytes", type=_positive_int, default=8192)
    slice_parser.add_argument("--scan-id", required=True)
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    if args.command == "scan":
        return _scan(args)
    return _slice(args)


if __name__ == "__main__":
    raise SystemExit(main())
