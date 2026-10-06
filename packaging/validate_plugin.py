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
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Dict, List, Optional, Set

from plugin_policy import CANONICAL_EVAL_VALIDATORS, EXPECTED_SKILL_IDS


REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = Path(__file__).resolve().parent / "plugin.schema.1.0.0.json"
PLUGIN_DIR = REPO_ROOT / "plugin"
PLUGIN_SKILLS = PLUGIN_DIR / "skills"
CLAUDE_PLUGIN_JSON = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"
# Competitors a trigger corpus may name that this plugin does not ship: they are
# provided by the host, so they cannot be validated against the packaged set.
EXTERNAL_COMPETITORS = {"skill-creator"}
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


def frontmatter_name(skill_md: Path) -> Optional[str]:
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("name:"):
            return line[len("name:"):].strip().strip("'\"") or None
    return None


def check_schema(plugin_json: Path) -> Optional[dict]:
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


def discover_skills(skills_dir: Path = PLUGIN_SKILLS) -> List[Path]:
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


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def check_skill_names(skill_dirs: List[Path]) -> None:
    names: List[str] = []
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
    escapes: List[str] = []
    for path in PLUGIN_DIR.rglob("*"):
        try:
            resolved = path.resolve()
        except OSError:
            escapes.append(str(path.relative_to(REPO_ROOT)))
            continue
        if resolved != root and not _is_relative_to(resolved, root):
            escapes.append(str(path.relative_to(REPO_ROOT)))
    if escapes:
        fail(f"paths resolve outside plugin root: {escapes}")
    else:
        ok("all packaged filesystem paths resolve within plugin/")


GENERATED_RESULTS_RE = re.compile(r"^plugin/skills/[^/]+/evals/results/")


def tracked_generated_results(paths: List[str]) -> List[str]:
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
    return any(not _is_relative_to(candidate, plugin_root) for candidate in existing)


def check_inspector(skill_dirs: List[Path]) -> None:
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
        # disable-model-invocation is the one accepted host-only-field
        # exception (R22 in rules-portability.md): a user-invoked Skill pairs
        # it with an agents/openai.yaml policy, checked by invocation_policy.
        unexpected_extensions = [
            extension for extension in report["platform_extensions"]
            if extension.get("key") != "disable-model-invocation"
        ]
        if unexpected_extensions:
            problems.append(f"platform frontmatter={unexpected_extensions}")
        invocation_mismatch = report.get("invocation_policy", {}).get("mismatch")
        if invocation_mismatch:
            problems.append(f"invocation policy mismatch={invocation_mismatch}")
        if escaping_refs:
            problems.append(f"references escaping plugin/={escaping_refs}")
        if problems:
            fail(f"inspect_skill.py findings in {label}: " + "; ".join(problems))
        else:
            ok(f"inspect_skill.py passes portable-core checks ({label})")


def check_sensitive_content(skill_dirs: List[Path]) -> None:
    findings: List[str] = []
    for skill_dir in skill_dirs:
        generated_results = skill_dir / "evals" / "results"
        for path in skill_dir.rglob("*"):
            if not path.is_file():
                continue
            if _is_relative_to(path, generated_results):
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


def illegal_tracked_skill_sources(paths: List[str]) -> List[str]:
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


def _install_doc_files() -> List[Path]:
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
    problems: List[str] = []
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


def check_install_docs_name_every_skill(skill_dirs: List[Path]) -> None:
    """Every install guide must name every discovered Skill.

    The guides list Skill names by hand, so a newly added Skill silently leaves
    each route's Verify step unable to detect its own absence.
    """
    names = sorted(path.name for path in skill_dirs)
    docs = sorted((REPO_ROOT / "docs" / "install").glob("*.md"))
    if not docs:
        fail("no install guides found under docs/install/")
        return

    problems = []
    for doc in docs:
        try:
            text = doc.read_text(encoding="utf-8")
        except OSError as exc:
            fail(f"unreadable install guide {doc.name}: {exc}")
            return
        missing = [name for name in names if name not in text]
        if missing:
            problems.append(f"{doc.relative_to(REPO_ROOT).as_posix()}: {missing}")
    if problems:
        fail("install guides do not name every discovered Skill: " + "; ".join(problems))
    else:
        ok(f"every install guide names all {len(names)} discovered Skills")


def check_competition_candidates(skill_dirs: List[Path]) -> None:
    """Validate trigger-corpus candidates and case-id stability.

    A competition candidate naming a Skill that does not exist can never be
    satisfied, so the case records `unmeasured` forever instead of competing.
    A reused case id silently retargets a recorded result at different content.
    """
    shipped = {path.name for path in skill_dirs}
    unknown: List[str] = []
    duplicate_ids: List[str] = []
    corpora = sorted(PLUGIN_SKILLS.glob("*/evals/trigger.json"))
    if not corpora:
        fail("no trigger corpora found under plugin/skills/*/evals/")
        return

    for corpus in corpora:
        try:
            cases = read_json(corpus)
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"unreadable trigger corpus {corpus.name}: {exc}")
            return
        if not isinstance(cases, list):
            cases = [cases]
        for case in cases:
            if not isinstance(case, dict):
                continue
            competition = case.get("competition")
            if not isinstance(competition, dict):
                continue
            for candidate in competition.get("required_candidates", []) or []:
                if candidate not in shipped and candidate not in EXTERNAL_COMPETITORS:
                    where = corpus.relative_to(REPO_ROOT).as_posix()
                    unknown.append(f"{where}:{case.get('id')} -> {candidate!r}")

        seen: Dict[str, int] = {}
        for case in cases:
            if isinstance(case, dict) and isinstance(case.get("id"), str):
                seen[case["id"]] = seen.get(case["id"], 0) + 1
        repeated = sorted(case_id for case_id, count in seen.items() if count > 1)
        if repeated:
            duplicate_ids.append(f"{corpus.relative_to(REPO_ROOT).as_posix()}: {repeated}")
    if unknown:
        fail(
            "competing-skill candidates name Skills that are neither shipped nor "
            f"declared host Skills {sorted(EXTERNAL_COMPETITORS)}: " + "; ".join(sorted(unknown))
        )
    else:
        ok("every competing-skill candidate is a shipped or declared host Skill")

    if duplicate_ids:
        fail(
            "trigger corpora reuse a case id, so a result cannot be traced to one case: "
            + "; ".join(duplicate_ids)
        )
    else:
        ok("every trigger case id is unique within its corpus")


def check_manifests(agent_manifest: Optional[dict], skill_dirs: List[Path]) -> None:
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

    descriptions = {
        "plugin/plugin.json": agent_manifest.get("description", ""),
        "plugin/.claude-plugin/plugin.json": claude.get("description", ""),
        ".claude-plugin/marketplace.json plugin entry": (
            entries[0].get("description", "") if len(entries) == 1 else ""
        ),
    }
    descriptions[".claude-plugin/marketplace.json"] = market.get("description", "")

    problems = []
    for where, value in sorted(descriptions.items()):
        lowered = value.lower()
        for topic in ("skill", "merge"):
            if topic not in lowered:
                problems.append(f"{where}: missing {topic!r}")
    if problems:
        fail("manifest descriptions must cover Skill engineering and merge-request review: " + "; ".join(problems))
    else:
        ok("manifest descriptions cover Skill engineering and merge-request review")

    check_skill_count_claims(len(skill_dirs), descriptions)


# Written-out counts a manifest or install doc may use for the shipped Skill set.
_COUNT_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}
# A count only claims the whole shipped set when an all-set qualifier follows it,
# so "the five forge-* Skills" (a subset) and "v1.0.0" (a version) are not claims.
_COUNT_CLAIM_RE = re.compile(
    r"(?i)\b(?:all\s+)?(%s|\d+)\s+(?:(?:portable|canonical|user-facing|shipped|included|agent)\s+){0,2}skills?\b" % "|".join(_COUNT_WORDS)
)


def _claimed_counts(text: str) -> Set[int]:
    counts: Set[int] = set()
    for match in _COUNT_CLAIM_RE.finditer(text):
        token = match.group(1).lower()
        counts.add(_COUNT_WORDS.get(token) or int(token))
    return counts


def count_claim_documents() -> List[Path]:
    """Every tracked document allowed to state how many Skills ship."""
    return [REPO_ROOT / "README.md", *sorted((REPO_ROOT / "docs" / "install").glob("*.md"))]


def check_skill_count_claims(discovered: int, descriptions: Dict[str, str]) -> None:
    """Reject any manifest, README, or install-doc claim about how many Skills ship.

    ``discover_skills`` deliberately allows Skills beyond the required baseline,
    so a hardcoded count is only correct until the next Skill lands.  Derive the
    truth from the discovered packages and fail on every stale claim.
    """
    sources = dict(descriptions)
    for doc in count_claim_documents():
        try:
            sources[str(doc.relative_to(REPO_ROOT)).replace(os.sep, "/")] = doc.read_text(
                encoding="utf-8"
            )
        except OSError as exc:
            fail(f"unreadable documentation file {doc.name}: {exc}")
            return

    stale = []
    for where, text in sorted(sources.items()):
        for claimed in sorted(_claimed_counts(text)):
            if claimed != discovered:
                stale.append(f"{where}: claims {claimed}")
    if stale:
        fail(
            f"Skill-count claims disagree with the {discovered} discovered Skill packages: "
            + "; ".join(stale)
        )
    else:
        ok(f"every Skill-count claim matches the {discovered} discovered Skill packages")


SPEC_REFERENCE_RE = re.compile(r"(?m)^\*\*Spec:\*\*\s+`?([^`\r\n]+?)`?\s*$")
UNRESOLVED_AUTHORITY_HEADING_RE = re.compile(
    r"(?im)^\s*#{1,6}\s+(?:open questions?|unresolved decisions?)\b"
)
UNRESOLVED_AUTHORITY_STATUS_RE = re.compile(
    r"(?im)^\s*(?:status|state):\s*(?:draft|unresolved)\b"
)
REVISION_RE = re.compile(r"(?im)^\s*-?\s*revision:\s*\d+\b")


def _tracked_paths() -> Set[str]:
    proc = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True
    )
    if proc.returncode != 0:
        return set()
    return {
        PurePosixPath(path.replace("\\", "/")).as_posix()
        for path in proc.stdout.splitlines()
        if path.strip()
    }


def validate_implementation_plan_specs(
    plan_paths: Optional[List[Path]] = None,
    tracked_paths: Optional[Set[str]] = None,
    repo_root: Path = REPO_ROOT,
) -> List[str]:
    """Validate explicit Specification bindings on implementation plans.

    A plan without a ``**Spec:**`` binding is outside this repository gate's
    explicit-authority protocol.  When a binding is present, its target must be
    tracked, inside the repository, revisioned, and free of Draft/open-decision
    authority markers.
    """
    root = Path(repo_root).resolve()
    paths = plan_paths
    if paths is None:
        paths = sorted((root / "docs" / "superpowers" / "plans").glob("*.md"))
    tracked = tracked_paths if tracked_paths is not None else _tracked_paths()
    errors: List[str] = []
    if tracked_paths is None and not tracked:
        errors.append("cannot enumerate tracked files for Specification authority")
        return errors

    for plan_path in paths:
        plan_path = Path(plan_path)
        try:
            plan_text = plan_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append("{}: unreadable plan: {}".format(plan_path, exc))
            continue
        matches = SPEC_REFERENCE_RE.findall(plan_text)
        if not matches:
            continue
        if len(matches) != 1:
            errors.append("{}: requires exactly one **Spec:** reference".format(plan_path))
            continue
        reference = matches[0].strip()
        posix = PurePosixPath(reference.replace("\\", "/"))
        windows = PureWindowsPath(reference)
        if posix.is_absolute() or windows.is_absolute() or bool(windows.drive):
            errors.append("{}: Specification path must be repository-relative".format(plan_path))
            continue
        candidate = (root / reference.replace("/", os.sep).replace("\\", os.sep)).resolve()
        try:
            relative = candidate.relative_to(root).as_posix()
        except ValueError:
            errors.append("{}: Specification path escapes repository".format(plan_path))
            continue
        if relative not in tracked:
            errors.append("{}: Specification is not tracked: {}".format(plan_path, reference))
            continue
        if not candidate.is_file():
            errors.append("{}: Specification does not resolve: {}".format(plan_path, reference))
            continue
        try:
            authority = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append("{}: unreadable Specification: {}".format(plan_path, exc))
            continue
        lowered = authority.casefold()
        if "draft for grilling" in lowered or UNRESOLVED_AUTHORITY_HEADING_RE.search(authority):
            errors.append("{}: Specification is Draft or has unresolved decisions".format(plan_path))
        if UNRESOLVED_AUTHORITY_STATUS_RE.search(authority):
            errors.append("{}: Specification status is unresolved".format(plan_path))
        if not REVISION_RE.search(authority):
            errors.append("{}: Specification has no numeric current revision".format(plan_path))
    return errors


def check_implementation_plan_specs() -> None:
    errors = validate_implementation_plan_specs()
    if errors:
        fail("implementation-plan Specification authority: " + "; ".join(errors))
    else:
        ok("implementation-plan Specification references are tracked and resolved")


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
    check_manifests(agent_manifest, skill_dirs)
    check_implementation_plan_specs()
    check_install_docs_do_not_instruct_committing_mirrors()
    check_install_docs_name_every_skill(skill_dirs)
    check_competition_candidates(skill_dirs)
    print()
    print("RESULT:", "PASS" if _ok else "FAIL")
    return 0 if _ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
