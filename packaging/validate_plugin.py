#!/usr/bin/env python3
"""Deterministically validate the canonical multi-Skill plugin payload.

Checks the Agent Plugins and Claude manifests, enumerates every immediate
``plugin/skills/*/SKILL.md`` package, runs the canonical inspector on each,
enforces path containment and unique names, and rejects tracked host mirrors.

Usage:
    python packaging/validate_plugin.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = Path(__file__).resolve().parent / "plugin.schema.1.0.0.json"
PLUGIN_DIR = REPO_ROOT / "plugin"
PLUGIN_SKILLS = PLUGIN_DIR / "skills"
CLAUDE_PLUGIN_JSON = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"
EXPECTED_SKILL_IDS = {
    "merge-sentinel",
    "skill-engineer",
    "skill-prospector",
    "forge-clarify",
    "forge-discover",
    "forge-spec",
    "forge-plan",
    "forge-implement",
}
REPOSITORY_URL = "https://github.com/abhinavjp/skill-forger"
PERSONAL_PATH_RE = re.compile(
    r"(?i)(?:[a-z]:[\\/]+users[\\/]+[^\\/]+|/(?:home|users)/[^/]+)"
)
CREDENTIAL_PATTERNS = {
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    "GitLab token": re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b"),
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
}
_ok = True


def fail(msg: str) -> None:
    global _ok
    _ok = False
    print(f"FAIL: {msg}")


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def frontmatter_name(skill_md: Path) -> str | None:
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("name:"):
            return line.removeprefix("name:").strip().strip("'\"") or None
    return None


def check_schema(plugin_json: Path) -> dict | None:
    try:
        data = read_json(plugin_json)
        schema = read_json(SCHEMA_PATH)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"plugin/plugin.json schema inputs: {exc}")
        return None
    try:
        import jsonschema

        jsonschema.validate(data, schema)
        ok("plugin/plugin.json validates against Agent Plugins v1.0.0 schema (jsonschema)")
    except ImportError:
        errors = []
        if data.get("$schema") != schema["properties"]["$schema"]["const"]:
            errors.append("$schema mismatch")
        name = data.get("name")
        if not name or not re.match(schema["properties"]["name"]["pattern"], name):
            errors.append("name missing or fails pattern")
        if not (1 <= len(name or "") <= 64):
            errors.append("name length out of bounds")
        extra = set(data) - set(schema["properties"])
        if extra:
            errors.append(f"additional properties not allowed: {sorted(extra)}")
        missing = set(schema["required"]) - set(data)
        if missing:
            errors.append(f"missing required: {sorted(missing)}")
        if errors:
            fail("plugin/plugin.json schema (manual fallback): " + "; ".join(errors))
        else:
            ok("plugin/plugin.json validates against Agent Plugins v1.0.0 schema (manual fallback)")
    except Exception as exc:
        fail(f"plugin/plugin.json schema: {exc}")
    return data


def discover_skills(skills_dir: Path = PLUGIN_SKILLS) -> list[Path]:
    if skills_dir == PLUGIN_SKILLS and not (PLUGIN_DIR / "plugin.json").is_file():
        fail("plugin/plugin.json missing at plugin root")
    elif skills_dir == PLUGIN_SKILLS:
        ok("plugin/plugin.json present at plugin root")
    if not skills_dir.is_dir():
        fail("plugin/skills/ directory missing")
        return []

    children = sorted(path for path in skills_dir.iterdir() if path.is_dir())
    missing_skill_md = [path.name for path in children if not (path / "SKILL.md").is_file()]
    if missing_skill_md:
        fail(f"immediate plugin/skills directories missing SKILL.md: {missing_skill_md}")
    skill_dirs = [path for path in children if (path / "SKILL.md").is_file()]
    found = {path.name for path in skill_dirs}
    if not EXPECTED_SKILL_IDS <= found:
        missing = sorted(EXPECTED_SKILL_IDS - found)
        fail(f"required Skill IDs missing: {missing}; found {sorted(found)}")
    else:
        ok(f"required Skill IDs are present; found {sorted(found)}")
    return skill_dirs


def check_skill_names(skill_dirs: list[Path]) -> None:
    names: list[str] = []
    for skill_dir in skill_dirs:
        name = frontmatter_name(skill_dir / "SKILL.md")
        if name is None:
            fail(f"{skill_dir.relative_to(REPO_ROOT)}/SKILL.md has no frontmatter name")
            continue
        names.append(name)
        if name != skill_dir.name:
            fail(f"folder {skill_dir.name!r} does not match frontmatter name {name!r}")
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        fail(f"duplicate Skill frontmatter names: {duplicates}")
    elif len(names) == len(skill_dirs):
        ok("all Skill folder names match unique frontmatter names")


def check_containment() -> None:
    root = PLUGIN_DIR.resolve()
    escapes: list[str] = []
    for path in PLUGIN_DIR.rglob("*"):
        try:
            resolved = path.resolve()
        except OSError:
            escapes.append(str(path.relative_to(REPO_ROOT)))
            continue
        if resolved != root and not resolved.is_relative_to(root):
            escapes.append(str(path.relative_to(REPO_ROOT)))
    if escapes:
        fail(f"paths resolve outside plugin root: {escapes}")
    else:
        ok("all packaged filesystem paths resolve within plugin/")


GENERATED_RESULTS_RE = re.compile(r"^plugin/skills/[^/]+/evals/results/")


def tracked_generated_results(paths: list[str]) -> list[str]:
    """Return tracked per-Skill ``evals/results/`` paths in the canonical payload.

    Generated result artifacts are ignored working-tree state, not source. A local,
    git-ignored run directory is expected during behavioral comparison, so only a
    *committed* result artifact is a packaging defect.
    """
    normalized = (path.replace("\\", "/") for path in paths)
    return sorted(path for path in normalized if GENERATED_RESULTS_RE.match(path))


def check_no_generated_results() -> None:
    proc = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True
    )
    if proc.returncode != 0:
        fail(f"cannot enumerate tracked files: {proc.stderr.strip()}")
        return
    tracked = tracked_generated_results(proc.stdout.splitlines())
    if tracked:
        fail(f"generated eval result artifacts tracked in canonical payload: {tracked}")
    else:
        ok("canonical Skill payloads track no generated eval result artifacts")


def reference_escapes_plugin(skill_dir: Path, reference: dict) -> bool:
    target = reference["target"]
    if re.match(r"^(?:https?:|mailto:|#)", target) or os.path.isabs(target):
        return False
    source_dir = Path(reference["from"]).parent
    candidates = [(skill_dir / source_dir / target).resolve()]
    if reference["context"] != "link":
        candidates.append((skill_dir / target).resolve())
    existing = [candidate for candidate in candidates if candidate.exists()]
    plugin_root = PLUGIN_DIR.resolve()
    return any(not candidate.is_relative_to(plugin_root) for candidate in existing)


def check_inspector(skill_dirs: list[Path]) -> None:
    inspector = PLUGIN_SKILLS / "skill-engineer" / "scripts" / "inspect_skill.py"
    if not inspector.is_file():
        fail("canonical inspect_skill.py missing from skill-engineer")
        return
    for skill_dir in skill_dirs:
        proc = subprocess.run(
            [sys.executable, str(inspector), str(skill_dir)],
            capture_output=True,
            text=True,
        )
        label = str(skill_dir.relative_to(REPO_ROOT))
        if proc.returncode != 0:
            fail(f"inspect_skill.py failed on {label}: {proc.stderr.strip()}")
            continue
        try:
            report = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            fail(f"inspect_skill.py emitted invalid JSON for {label}: {exc}")
            continue

        metadata_errors = [
            error
            for error in report["metadata"]["errors"]
            if not error.startswith("PyYAML unavailable:")
        ]
        personal_paths = [
            finding
            for finding in report["hardcoded_paths"]
            if PERSONAL_PATH_RE.search(finding["match"])
        ]
        escaping_refs = [
            reference
            for reference in report["references"]
            if reference["resolved"] and reference_escapes_plugin(skill_dir, reference)
        ]
        problems = []
        if metadata_errors:
            problems.append(f"metadata errors={metadata_errors}")
        if report["broken_references"]:
            problems.append(f"broken references={report['broken_references']}")
        if personal_paths:
            problems.append(f"personal paths={personal_paths}")
        if report["platform_extensions"]:
            problems.append(f"platform frontmatter={report['platform_extensions']}")
        if escaping_refs:
            problems.append(f"references escaping plugin/={escaping_refs}")
        if problems:
            fail(f"inspect_skill.py findings in {label}: " + "; ".join(problems))
        else:
            ok(f"inspect_skill.py passes portable-core checks ({label})")


def check_sensitive_content(skill_dirs: list[Path]) -> None:
    findings: list[str] = []
    for skill_dir in skill_dirs:
        generated_results = skill_dir / "evals" / "results"
        for path in skill_dir.rglob("*"):
            if not path.is_file():
                continue
            if path.is_relative_to(generated_results):
                # Ignored local run output, excluded from every distribution copy.
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if PERSONAL_PATH_RE.search(text):
                findings.append(f"{path.relative_to(REPO_ROOT)} (personal path)")
            for label, pattern in CREDENTIAL_PATTERNS.items():
                if pattern.search(text):
                    findings.append(f"{path.relative_to(REPO_ROOT)} ({label})")
    if findings:
        fail(f"personal path or credential-like material in portable payload: {findings}")
    else:
        ok("no personal paths or credential-like material found in packaged text")


def illegal_tracked_skill_sources(paths: list[str]) -> list[str]:
    """Return tracked SKILL.md paths outside the canonical plugin Skill tree."""
    skill_sources = []
    for path in paths:
        normalized = path.replace("\\", "/")
        if PurePosixPath(normalized).name == "SKILL.md":
            skill_sources.append(normalized)
    return sorted(path for path in skill_sources if not path.startswith("plugin/skills/"))


def check_no_tracked_mirrors() -> None:
    proc = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True
    )
    if proc.returncode != 0:
        fail(f"cannot enumerate tracked files: {proc.stderr.strip()}")
        return
    mirrors = illegal_tracked_skill_sources(proc.stdout.splitlines())
    legacy_dirs = [
        REPO_ROOT / "skill-engineer",
        REPO_ROOT / ".agents" / "skills" / "skill-engineer",
        REPO_ROOT / ".agents" / "skills" / "merge-sentinel",
    ]
    existing = [str(path.relative_to(REPO_ROOT)) for path in legacy_dirs if path.exists()]
    if mirrors or existing:
        fail(f"Skill mirrors outside plugin/skills/: tracked={mirrors}, existing={existing}")
    else:
        ok("plugin/skills/ is the only tracked and authored Skill tree")


INSTALL_DOCS_DIR = REPO_ROOT / "docs" / "install"
BANNED_MIRROR_FRAGMENTS = (
    ".agents/skills/",
    ".claude/skills/",
    ".cursor/skills/",
    "skill-engineer/",
    "merge-sentinel/",
)
GIT_MUTATING_COMMAND = re.compile(r"\bgit\s+(?:add|commit|mv)\b")


def _install_doc_files() -> list[Path]:
    docs = [REPO_ROOT / "README.md"]
    if INSTALL_DOCS_DIR.is_dir():
        docs.extend(sorted(INSTALL_DOCS_DIR.glob("*.md")))
    return [doc for doc in docs if doc.is_file()]


def check_install_docs_do_not_instruct_committing_mirrors() -> None:
    """Fail only when a doc's own shell examples commit a banned mirror path.

    This intentionally ignores plain prose mentions (including "Do not ..." warnings and
    ``plugin/skills/...`` paths) and only inspects git-mutating commands inside fenced code
    blocks, so documenting a mirror as a forbidden or host-owned destination is not itself
    a failure.
    """
    problems: list[str] = []
    for doc in _install_doc_files():
        in_code_block = False
        for line in doc.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if not in_code_block or not GIT_MUTATING_COMMAND.search(line):
                continue
            for fragment in BANNED_MIRROR_FRAGMENTS:
                if fragment in line and f"plugin/skills/{fragment}" not in line:
                    problems.append(f"{doc.relative_to(REPO_ROOT)}: {line.strip()!r}")
    if problems:
        fail(f"install docs instruct committing a banned mirror path: {problems}")
    else:
        ok("install docs never instruct committing a tracked Skill mirror")


def check_manifests(agent_manifest: dict | None) -> None:
    try:
        claude = read_json(CLAUDE_PLUGIN_JSON)
        market = read_json(MARKETPLACE_JSON)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Claude manifest inputs: {exc}")
        return
    if agent_manifest is None:
        return

    identity = agent_manifest.get("name")
    version = agent_manifest.get("version")
    if claude.get("name") != identity or claude.get("version") != version:
        fail("plugin manifests do not share one name and version")
    else:
        ok(f"Agent and Claude manifests share identity {identity!r} at version {version}")

    entries = [entry for entry in market.get("plugins", []) if entry.get("name") == identity]
    if len(entries) != 1 or entries[0].get("source") != "./plugin":
        fail("marketplace must contain exactly one matching './plugin' entry")
    else:
        ok("marketplace has one correctly sourced entry for the existing plugin identity")

    if market.get("version") != version or (
        len(entries) == 1 and entries[0].get("version") != version
    ):
        fail("marketplace and plugin entry versions must match the plugin manifests")
    else:
        ok(f"marketplace and plugin entry versions match release {version}")

    repositories = {
        agent_manifest.get("repository"),
        claude.get("repository"),
        claude.get("homepage"),
    }
    if repositories != {REPOSITORY_URL}:
        fail(f"manifest repository URLs are inconsistent: {sorted(str(x) for x in repositories)}")
    else:
        ok(f"manifest repository URL is {REPOSITORY_URL}")

    descriptions = [
        agent_manifest.get("description", ""),
        claude.get("description", ""),
        entries[0].get("description", "") if len(entries) == 1 else "",
    ]
    if any("skill" not in value.lower() or "merge" not in value.lower() for value in descriptions):
        fail("manifest descriptions must cover Skill engineering and merge-request review")
    else:
        ok("manifest descriptions cover all included Skills")


def main() -> int:
    global _ok
    _ok = True
    agent_manifest = check_schema(PLUGIN_DIR / "plugin.json")
    skill_dirs = discover_skills()
    check_skill_names(skill_dirs)
    check_containment()
    check_no_generated_results()
    check_inspector(skill_dirs)
    check_sensitive_content(skill_dirs)
    check_no_tracked_mirrors()
    check_manifests(agent_manifest)
    check_install_docs_do_not_instruct_committing_mirrors()
    print()
    print("RESULT:", "PASS" if _ok else "FAIL")
    return 0 if _ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
