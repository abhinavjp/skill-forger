#!/usr/bin/env python3
"""Deterministic inspector for an Agent Skill package. Facts only, no judgement.

Usage:
    inspect_skill.py <skill-dir>

Emits a JSON object of structured facts about the package: frontmatter, file inventory,
reference resolution, scripts/assets, size metrics, duplicate blocks,
platform-specific frontmatter keys, hardcoded paths, and eval-schema results.

Reference records carry a `context` of `link`, `fence` or `prose`: a path inside a
fenced code block is often illustrative, so an unresolved one is weaker evidence
than an unresolved markdown link.

Exit codes:
    0  inspection completed (findings may still be present in the output)
    2  target is not a readable Skill package

Semantic conclusions (scope, context design, completion quality) are out of
scope by design; they belong to the AI-review and runtime-eval layers.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import PurePosixPath, PureWindowsPath

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_evals  # noqa: E402

# Keys defined by the open Agent Skills format.
STANDARD_KEYS = {"name", "description", "license", "compatibility", "metadata",
                 "version"}
# Frontmatter keys known to be host-specific. Anything else unrecognised is
# reported as an unknown extension rather than attributed to a platform.
PLATFORM_KEYS = {
    "allowed-tools": "claude-code",
    "disable-model-invocation": "claude-code",
    "argument-hint": "claude-code",
    "model": "claude-code",
    "user-invocable": "claude-code",
    "alwaysApply": "cursor",
    "globs": "cursor",
    "alias": "cursor",
    "agents": "codex",
    "sandbox": "codex",
    "permissions": "antigravity",
}

TEXT_EXTS = (".md", ".markdown", ".txt")
REF_EXTS = r"md|markdown|txt|py|sh|ps1|js|ts|json|ya?ml|csv|html|toml|ini"
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
PATHY_RE = re.compile(r"(?<![\w/.-])((?:\.{0,2}/)?[\w.-]+(?:/[\w.-]+)+"
                      r"\.(?:" + REF_EXTS + r"))(?![\w])")
HARDCODED_RE = re.compile(
    r"(?<![\w])(?:[A-Za-z]:[\\/][\w\\/. -]+"
    r"|~/[\w./-]+"
    r"|/(?:Users|home|opt|etc|var|mnt|usr)/[\w./-]+)")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")

# Limits defined by the Agent Skills format. Hosts truncate or reject metadata
# beyond these, so exceeding them is a load-time defect, not a style question.
NAME_MAX = 64
DESCRIPTION_MAX = 1024

# Intentionally defective eval fixtures, and generated eval-run evidence
# (transcripts/results), are data about the Skill's evaluation process, not
# Skill content: scanning them would report their planted defects, or their
# quotes of those defects, as defects of the host package. They are still
# inventoried, and inspecting a fixture or a results directory directly (as
# its own root) scans it normally.
EXCLUDED_SCAN_PREFIXES = ("evals/fixtures/", "evals/results/")

# Narrative documents living directly in evals/ (validation plans, cross-host
# handoffs, run notes) describe the validation *process* around the canonical
# case corpus (evals/*.json) and its fixtures/results; they are not part of
# the inspected product surface either. Matching only direct children of
# evals/ keeps genuine product documentation under references/ (or nested
# inside a fixture's own root) unaffected.
EXCLUDED_SCAN_TOPLEVEL_DOC_RE = re.compile(r"^evals/[^/]+\.(?:md|markdown|txt)$")


def _scannable(rel_path):
    if rel_path.startswith(EXCLUDED_SCAN_PREFIXES):
        return False
    return not EXCLUDED_SCAN_TOPLEVEL_DOC_RE.match(rel_path)


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def parse_frontmatter(text):
    """Return (frontmatter_dict, body, errors). Tolerates missing PyYAML."""
    errors = []
    if not text.startswith("---"):
        return {}, text, ["SKILL.md has no YAML frontmatter block"]
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text, ["frontmatter block is not terminated by '---'"]
    raw = text[text.find("\n", 3) + 1:end]
    body = text[end + 4:].lstrip("\n")
    try:
        import yaml
        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            return {}, body, ["frontmatter is not a mapping"]
        return data, body, errors
    except ImportError:
        data = {}
        for line in raw.splitlines():
            if re.match(r"^\w[\w-]*\s*:", line):
                key, _, value = line.partition(":")
                data[key.strip()] = value.strip().strip("'\"")
        return data, body, errors


def inventory(root):
    files = []
    for base, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
        for name in sorted(names):
            full = os.path.join(base, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            size = os.path.getsize(full)
            files.append({
                "path": rel,
                "bytes": size,
                "token_estimate": size // 4,
                "executable": os.access(full, os.X_OK),
            })
    return files


def _is_absolute_reference(target):
    """Absolute-path check independent of the OS running the inspector.

    os.path.isabs() judges by the host OS's own path rules, so a POSIX
    path can come out "relative" when the inspector runs on Windows, or
    vice versa. Checking both PurePosixPath and PureWindowsPath recognises
    POSIX absolute paths, Windows drive-absolute paths, and Windows UNC
    paths regardless of which OS is doing the inspecting.
    """
    return (PurePosixPath(target).is_absolute()
            or PureWindowsPath(target).is_absolute())


def scan_references(root, files):
    refs, broken = [], []
    for entry in files:
        if not entry["path"].endswith(TEXT_EXTS) or not _scannable(entry["path"]):
            continue
        full = os.path.join(root, entry["path"])
        source_dir = os.path.dirname(entry["path"])
        in_fence = False
        for lineno, line in enumerate(_read(full).splitlines(), 1):
            if FENCE_RE.match(line):
                in_fence = not in_fence
                continue
            links = set(LINK_RE.findall(line))
            targets = links | set(PATHY_RE.findall(line))
            for target in targets:
                if re.match(r"^(https?:|mailto:|#)", target):
                    continue
                # Absolute paths are host coupling, not package references;
                # find_hardcoded_paths owns them. Resolving them here reported
                # every absolute path as a broken reference.
                if _is_absolute_reference(target):
                    continue
                context = ("link" if target in links
                           else "fence" if in_fence else "prose")
                # A Markdown link resolves relative to its own document, full
                # stop. Falling back to the package root made `[x](references/
                # x.md)` inside references/ resolve against the root copy and
                # report a genuinely broken link as fine. Prose and fenced
                # paths are usually written from the package root, so they keep
                # both candidates.
                candidates = [
                    os.path.normpath(os.path.join(root, source_dir, target))]
                if context != "link":
                    candidates.append(os.path.normpath(
                        os.path.join(root, target)))
                exists = any(os.path.exists(c) for c in candidates)
                record = {"from": entry["path"], "line": lineno,
                          "target": target, "resolved": exists,
                          "context": context}
                refs.append(record)
                if not exists:
                    broken.append(record)
    return refs, broken


def find_duplicate_blocks(root, files, window=3):
    seen = {}
    for entry in files:
        if not entry["path"].endswith(TEXT_EXTS) or not _scannable(entry["path"]):
            continue
        lines = [l.strip() for l in
                 _read(os.path.join(root, entry["path"])).splitlines()]
        for i in range(len(lines) - window + 1):
            block = lines[i:i + window]
            if sum(1 for l in block if l) < window or len("".join(block)) < 60:
                continue
            key = "\n".join(block)
            seen.setdefault(key, []).append(
                {"path": entry["path"], "line": i + 1})
    return [{"block": key, "occurrences": locs}
            for key, locs in seen.items() if len(locs) > 1]


def find_hardcoded_paths(root, files):
    hits = []
    for entry in files:
        if (not entry["path"].endswith(TEXT_EXTS + (".py", ".sh", ".ps1"))
                or not _scannable(entry["path"])):
            continue
        for lineno, line in enumerate(
                _read(os.path.join(root, entry["path"])).splitlines(), 1):
            if lineno == 1 and line.startswith("#!"):
                continue  # shebangs are interpreter resolution, not coupling
            for match in HARDCODED_RE.findall(line):
                hits.append({"path": entry["path"], "line": lineno,
                             "match": match})
    return hits


def inspect(root):
    skill_md = os.path.join(root, "SKILL.md")
    if not os.path.isfile(skill_md):
        raise RuntimeError(f"no SKILL.md in {root}")

    text = _read(skill_md)
    frontmatter, body, fm_errors = parse_frontmatter(text)

    metadata_errors = list(fm_errors)
    name = frontmatter.get("name")
    description = frontmatter.get("description")
    if not name:
        metadata_errors.append("missing required frontmatter field: name")
    elif not NAME_RE.match(str(name)):
        metadata_errors.append(
            "name is not lowercase-hyphen format: %r" % name)
    elif len(str(name)) > NAME_MAX:
        metadata_errors.append(
            "name exceeds %d characters: %d" % (NAME_MAX, len(str(name))))
    if not description:
        metadata_errors.append(
            "missing required frontmatter field: description")
    elif len(str(description)) > DESCRIPTION_MAX:
        metadata_errors.append(
            "description exceeds %d characters: %d"
            % (DESCRIPTION_MAX, len(str(description))))

    platform_extensions = []
    for key in frontmatter:
        if key in STANDARD_KEYS:
            continue
        platform_extensions.append({
            "key": key,
            "platform": PLATFORM_KEYS.get(key, "unknown"),
        })

    files = inventory(root)
    references, broken = scan_references(root, files)
    hardcoded = find_hardcoded_paths(root, files)
    skill_bytes = os.path.getsize(skill_md)

    eval_paths = [os.path.join(root, d) for d in ("evals",)
                  if os.path.isdir(os.path.join(root, d))]
    evals = (validate_evals.validate_paths(eval_paths) if eval_paths
             else {"files": [], "case_count": 0, "cases": [], "errors": []})
    evals["files"] = [os.path.relpath(f, root).replace(os.sep, "/")
                      for f in evals["files"]]
    for case in evals["cases"]:
        case["file"] = os.path.relpath(case["file"], root).replace(os.sep, "/")

    return {
        "skill_path": os.path.abspath(root),
        "metadata": {
            "frontmatter": frontmatter,
            "name": name,
            "description": description,
            "description_chars": len(description or ""),
            "errors": metadata_errors,
        },
        "files": files,
        "references": references,
        "broken_references": broken,
        "scripts": [f for f in files if f["path"].startswith("scripts/")],
        "assets": [f for f in files if f["path"].startswith("assets/")],
        "reference_docs": [f for f in files
                           if f["path"].startswith("references/")],
        "platform_extensions": platform_extensions,
        "hardcoded_paths": hardcoded,
        "exact_duplicates": find_duplicate_blocks(root, files),
        "metrics": {
            "skill_lines": text.count("\n") + 1,
            "skill_bytes": skill_bytes,
            "skill_token_estimate": skill_bytes // 4,
            "package_files": len(files),
            "package_bytes": sum(f["bytes"] for f in files),
            "body_lines": body.count("\n") + 1,
            # Counts so a grader can assert on one unambiguous string; the
            # bare `"errors": []` shape appears in several sections and made
            # metadata assertions untestable.
            "metadata_error_count": len(metadata_errors),
            "broken_reference_count": len(broken),
            "hardcoded_path_count": len(hardcoded),
        },
        "evals": evals,
    }


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        facts = inspect(args[0])
    except (RuntimeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(facts, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
