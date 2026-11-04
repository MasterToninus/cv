# +---------------------------------------------------------------------------
# | Project           : CV generator
# |
# | Program name      : cvgen/helpers/paths.py
# |
# | Author            : Antonio Michele Miti
# |
# | Date created      : 2026-11-04
# |
# | Purpose           : Resolve repository-relative paths for the CLI entry points.
# |
# | Revision History  :
# | Date      Author       Revision
# | 20261104  Miti/Codex   Centralize path resolution with an explicit root.
# | Tools             : OpenAI ChatGPT/Codex
# +---------------------------------------------------------------------------
"""Resolve command-line paths independently of the caller's working directory."""

from pathlib import Path


def resolve_project_path(value: str | Path, *, root: Path) -> Path:
    """Resolve relative inputs against the root supplied by the current caller.

    Do not capture a repository root in a default argument: entry points can
    select a different root, including isolated checkouts used by callers/tests.
    """
    path = Path(value)
    return path if path.is_absolute() else root / path
