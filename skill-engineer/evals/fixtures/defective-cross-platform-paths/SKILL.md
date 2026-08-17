---
name: cross-platform-paths
description: Fixture for absolute-path classification. Use only as an inspector test input, never as a real Skill.
license: Apache-2.0
---

# Cross-platform paths

This package exists to exercise absolute-path classification in
`inspect_skill.py`, independent of the OS running the inspector.

## Workflow

1. On POSIX hosts the release log lives at /var/releases/log.txt.
2. On Windows hosts the equivalent lives at C:/temp/release-log.txt.
3. Read [the present reference](references/present.md) before starting.
4. Read [the missing reference](references/missing.md) for background.

## Done when

The inspector has reported exactly one broken reference (the missing one)
and has classified both absolute paths above as hardcoded paths, not as
broken package-relative references.
