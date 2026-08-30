#!/usr/bin/env python3
"""Scan repository guidance into compact, provenance-preserving metadata.

Usage:
    scan_guidance.py scan <root> [--json] [--out PATH] [--max-bytes N]
    scan_guidance.py slice <path> --section <heading> [--max-bytes N]

The scanner reads target files and writes only the explicitly requested JSON
inventory. It never executes target content. ``slice`` is a deliberately
narrow, heading-scoped second read for classification ambiguity.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import ntpath
import os
import re
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
PATTERNS_PATH = HERE / "patterns.json"
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
REPARSE_POINT = 0x400


class _ContainmentError(ValueError):
    """A requested path cannot be safely bound to the target root."""


def _canonical_root(root: Path) -> Path:
    try:
        resolved = root.resolve()
    except (OSError, RuntimeError) as exc:
        raise _ContainmentError("target root cannot be resolved") from exc
    if not resolved.is_dir():
        raise _ContainmentError("target root is not a directory")
    return resolved


def _is_absolute_or_drive(value: str) -> bool:
    normalised = value.replace("\\", "/")
    return (
        os.path.isabs(value)
        or normalised.startswith("/")
        or ntpath.isabs(value)
        or bool(ntpath.splitdrive(value)[0])
    )


def _relative_parts(relative: str):
    if not isinstance(relative, str) or not relative or "\x00" in relative:
        raise _ContainmentError("path is not a contained relative path")
    normalised = relative.replace("\\", "/")
    if _is_absolute_or_drive(relative):
        raise _ContainmentError("path is not a contained relative path")
    parts = [part for part in normalised.split("/") if part not in ("", ".")]
    if not parts or any(part == ".." for part in parts):
        raise _ContainmentError("path is not a contained relative path")
    return parts


def _assert_contained(root: Path, candidate: Path):
    root_text = os.path.normcase(os.path.abspath(os.fspath(root)))
    candidate_text = os.path.normcase(os.path.abspath(os.fspath(candidate)))
    try:
        common = os.path.commonpath([root_text, candidate_text])
    except ValueError as exc:
        raise _ContainmentError("path is not contained by target root") from exc
    if common != root_text:
        raise _ContainmentError("path is not contained by target root")


def _is_link_or_reparse(path: Path) -> bool:
    try:
        if path.is_symlink() or os.path.islink(os.fspath(path)):
            return True
        if os.name == "nt":
            attributes = os.stat(
                os.fspath(path), follow_symlinks=False
            ).st_file_attributes
            return bool(attributes & REPARSE_POINT)
    except FileNotFoundError:
        return False
    except OSError:
        return False
    return False


def _reject_link_components(root: Path, candidate: Path):
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise _ContainmentError("path is not contained by target root") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if _is_link_or_reparse(current):
            raise _ContainmentError("path traverses a link or reparse point")


def _resolve_candidate(root: Path, candidate: Path, *, require_file: bool) -> Path:
    _assert_contained(root, candidate)
    _reject_link_components(root, candidate)
    try:
        resolved = candidate.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise _ContainmentError("path cannot be resolved") from exc
    _assert_contained(root, resolved)
    if resolved.exists() and not resolved.is_file():
        raise _ContainmentError("path is not a regular file")
    if require_file and not resolved.is_file():
        raise _ContainmentError("path is not a regular file")
    return resolved


def _resolve_within(root: Path, relative: str, *, require_file: bool) -> Path:
    """Resolve a repository-relative path without crossing links or root."""
    canonical_root = _canonical_root(root)
    parts = _relative_parts(relative)
    candidate = canonical_root.joinpath(*parts)
    return _resolve_candidate(canonical_root, candidate, require_file=require_file)


def _resolve_output(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise _ContainmentError("inventory output must stay inside target root")
    if not _is_absolute_or_drive(value):
        return _resolve_within(root, value, require_file=False)
    if not Path(value).is_absolute():
        raise _ContainmentError("inventory output must stay inside target root")
    canonical_root = _canonical_root(root)
    candidate = Path(os.path.abspath(value))
    return _resolve_candidate(canonical_root, candidate, require_file=False)


def _load_patterns():
    with PATTERNS_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("version") != 1:
        raise ValueError("patterns.json version must be 1")
    return data


def _normalise_path(value: str) -> str:
    value = value.replace(os.sep, "/")
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


def _read_gitignore(root: Path):
    try:
        path = _resolve_within(root, ".gitignore", require_file=True)
    except (_ContainmentError, OSError):
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
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
    parts = _relative_parts(relative)
    candidate = canonical_root.joinpath(*parts)
    _assert_contained(canonical_root, candidate)
    _reject_link_components(canonical_root, candidate)
    try:
        resolved = candidate.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise _ContainmentError("directory cannot be resolved") from exc
    _assert_contained(canonical_root, resolved)
    if not resolved.is_dir():
        raise _ContainmentError("path is not a directory")
    return resolved


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


def _make_scan_id(root: Path, pairs) -> str:
    payload = {
        "root": str(root.resolve()),
        "files": sorted([[path, digest] for path, digest in pairs]),
    }
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"))
    return _sha256(rendered.encode("utf-8"))


def _candidate_hash_pairs(root: Path):
    """Recompute candidate hash membership for optional slice freshness checks."""
    try:
        patterns = _load_patterns()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise _ContainmentError("scan membership cannot be recomputed") from exc
    heuristic = patterns["heuristic"]
    gitignore = _read_gitignore(root)
    pairs = []
    walk_errors = []

    def onerror(error):
        walk_errors.append(error)

    for base, dirs, names in os.walk(str(root), topdown=True, onerror=onerror):
        base_path = Path(base)
        kept_dirs = []
        for dirname in sorted(dirs):
            full_dir = base_path / dirname
            rel_dir = _normalise_path(os.path.relpath(str(full_dir), str(root)))
            reason = _excluded(rel_dir, True, patterns.get("exclusions", []))
            if (
                reason is None
                and _gitignored(rel_dir, True, gitignore)
                and not _could_contain_guidance(root, rel_dir, patterns["catalogue"])
            ):
                reason = ".gitignore"
            if reason is None:
                kept_dirs.append(dirname)
        dirs[:] = kept_dirs

        for filename in sorted(names):
            full_path = base_path / filename
            rel_path = _normalise_path(os.path.relpath(str(full_path), str(root)))
            if _excluded(rel_path, False, patterns.get("exclusions", [])) is not None:
                continue
            safe_path = _resolve_within(root, rel_path, require_file=True)
            entries = _catalogue_entries(rel_path, patterns["catalogue"])
            if _gitignored(rel_path, False, gitignore) and not entries:
                continue
            if not entries and safe_path.suffix.lower() not in set(heuristic["extensions"]):
                continue
            try:
                with safe_path.open("rb") as handle:
                    raw = handle.read()
            except OSError as exc:
                raise _ContainmentError("scan membership cannot be recomputed") from exc
            pairs.append((rel_path, _sha256(raw)))
    if walk_errors:
        raise _ContainmentError("scan membership cannot be recomputed")
    return pairs


def _read_file_metadata(path: Path, rel_path: str, size: int, match_reason,
                         host_affinity, current_mechanism: str, max_bytes: int,
                         marker_regexes, root=None):
    """Read one candidate once and return metadata without retaining its body."""
    if root is not None:
        path = _resolve_within(root, rel_path, require_file=True)
    with path.open("rb") as handle:
        raw = handle.read()
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
    if path.suffix.lower() in TEXT_EXTENSIONS or path.name in {
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
    try:
        patterns = _load_patterns()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: cannot load pattern catalogue: {exc}", file=sys.stderr)
        return 2

    heuristic = patterns["heuristic"]
    max_bytes = args.max_bytes if args.max_bytes is not None else heuristic["max_bytes"]
    marker_regexes = _directive_regexes(heuristic["directive_markers"])
    gitignore = _read_gitignore(root)
    matched_units = []
    skipped = []
    errors = []
    scanned_files = 0
    truncated = False
    containment_failed = False
    ignored_guidance_count = 0
    scan_pairs = []

    def onerror(error):
        errors.append({"path": _normalise_path(str(getattr(error, "filename", ""))),
                       "error": str(error)})

    for base, dirs, names in os.walk(str(root), topdown=True, onerror=onerror):
        base_path = Path(base)
        kept_dirs = []
        for dirname in sorted(dirs):
            full_dir = base_path / dirname
            rel_dir = _normalise_path(os.path.relpath(str(full_dir), str(root)))
            reason = _excluded(rel_dir, True, patterns.get("exclusions", []))
            if (
                reason is None
                and _gitignored(rel_dir, True, gitignore)
                and not _could_contain_guidance(root, rel_dir, patterns["catalogue"])
            ):
                reason = ".gitignore"
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
            try:
                safe_path = _resolve_within(root, rel_path, require_file=True)
            except _ContainmentError:
                errors.append({"path": rel_path,
                               "error": "candidate rejected by target-root containment"})
                containment_failed = True
                continue
            entries = _catalogue_entries(rel_path, patterns["catalogue"])
            ignored_by_git = _gitignored(rel_path, False, gitignore)
            if ignored_by_git and not entries:
                skipped.append({"path": rel_path, "reason": "excluded:.gitignore"})
                continue
            scanned_files += 1
            try:
                size = safe_path.stat().st_size
            except OSError as exc:
                errors.append({"path": rel_path, "error": str(exc)})
                continue
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
                record = _read_file_metadata(
                    safe_path, rel_path, size, reasons, host_affinity,
                    current_mechanism, max_bytes, marker_regexes, root=root
                )
            except _ContainmentError:
                errors.append({"path": rel_path,
                               "error": "candidate rejected by target-root containment"})
                containment_failed = True
                continue
            except (OSError, UnicodeError) as exc:
                errors.append({"path": rel_path, "error": str(exc)})
                continue

            record["source_scope"] = "catalogue" if entries else "heuristic"
            record["ignored_by_git"] = ignored_by_git
            scan_pairs.append((rel_path, record["sha256"]))
            if ignored_by_git and entries:
                ignored_guidance_count += 1

            if record.get("status") == "oversize":
                record["match_reason"].append("heuristic:oversize")
                matched_units.append(record)
                truncated = True
            elif entries or record["directive_count"] >= heuristic["min_directives"]:
                if not entries:
                    record["match_reason"].append("heuristic:imperative-density")
                matched_units.append(record)

    result = {
        "version": 1,
        "root": str(root.resolve()),
        "scanned_files": scanned_files,
        "matched_units": matched_units,
        "skipped": skipped,
        "scan_id": _make_scan_id(root, scan_pairs),
        "ignored_guidance_count": ignored_guidance_count,
        "truncated": truncated,
        "errors": errors,
    }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.out:
        try:
            output_path = _resolve_output(root, args.out)
            with output_path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(rendered)
        except _ContainmentError:
            print("error: inventory output must stay inside scan root", file=sys.stderr)
            return 2
        except OSError as exc:
            print(f"error: cannot write inventory: {exc}", file=sys.stderr)
            return 2
    sys.stdout.write(rendered)
    return 2 if containment_failed else 0


def _slice_output(path: str, start: int, end: int, body: str, max_bytes: int):
    prefix = f"{path}:{start}-{end}\n"
    full = prefix + body
    if len(full.encode("utf-8")) <= max_bytes:
        return full
    marker = "\n[truncated]"
    prefix_bytes = len(prefix.encode("utf-8"))
    marker_bytes = len(marker.encode("utf-8"))
    if prefix_bytes + marker_bytes <= max_bytes:
        available = max_bytes - prefix_bytes - marker_bytes
        encoded_body = body.encode("utf-8")[:available]
        safe_body = encoded_body.decode("utf-8", errors="ignore")
        return prefix + safe_body + marker
    marker_only = "[truncated]"
    if len(marker_only.encode("utf-8")) <= max_bytes:
        return marker_only
    return marker_only.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")


def _slice(args):
    try:
        path = _resolve_within(Path(args.root), args.relative_path,
                                require_file=True)
    except _ContainmentError:
        print("error: slice path must stay inside target root", file=sys.stderr)
        return 2
    if args.scan_id:
        try:
            current_scan_id = _make_scan_id(
                _canonical_root(Path(args.root)),
                _candidate_hash_pairs(Path(args.root)),
            )
        except _ContainmentError:
            print("error: scan membership cannot be verified", file=sys.stderr)
            return 2
        if current_scan_id != args.scan_id:
            print("error: scan id does not match current inventory", file=sys.stderr)
            return 2
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    except OSError as exc:
        print(f"error: cannot read slice path: {exc}", file=sys.stderr)
        return 2
    if args.document:
        start_line = 1
        end_line = len(lines)
        body = "".join(lines)
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
        end_line = end_index
        body = "".join(lines[selected["index"]:end_index])
    display_path = _normalise_path(args.relative_path)
    sys.stdout.write(_slice_output(display_path, start_line, end_line, body,
                                   args.max_bytes))
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
    slice_parser.add_argument("--scan-id")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    if args.command == "scan":
        return _scan(args)
    return _slice(args)


if __name__ == "__main__":
    raise SystemExit(main())
