"""Collect PR file paths including previous_filename for renames.

Used by the CI Control Plane workflow to ensure renamed files are not
exempt from protected-path evaluation.  This script is metadata-only:
it queries the GitHub API and never checks out or executes PR code.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Sequence
from typing import Any


def fetch_pr_files_raw(
    repo: str,
    pr_number: int,
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None = None,
) -> list[dict[str, Any]]:
    """Fetch the PR files list from GitHub API."""
    cmd = [
        "gh", "api", "--paginate",
        f"repos/{repo}/pulls/{pr_number}/files?per_page=100",
    ]
    if runner is None:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    else:
        proc = runner(cmd)

    if proc.returncode != 0:
        raise RuntimeError(
            f"Failed to fetch PR files: {proc.stderr.strip() or proc.stdout.strip()}"
        )
    return json.loads(proc.stdout)


def extract_all_paths(files: list[dict[str, Any]]) -> set[str]:
    """Extract both filename and previous_filename from each file object.

    For renamed/moved files, the PR files API includes:
      - ``filename``: the new/destination path
      - ``previous_filename``: the old/source path (only present on renames)

    Both must be evaluated for protected-path analysis.
    """
    paths: set[str] = set()
    for f in files:
        filename = f.get("filename")
        if filename:
            paths.add(filename)
        prev = f.get("previous_filename")
        if prev:
            paths.add(prev)
    return paths


PROTECTED_PREFIXES = (
    ".github/workflows/",
    "scripts/ci/",
    "infra/github/",
)

PROTECTED_EXACT = {
    "package.json",
    "pnpm-workspace.yaml",
    "services/core/pyproject.toml",
    "apps/web/package.json",
}

PROTECTED_GLOBS_WEB = (
    "apps/web/tsconfig",
    "apps/web/eslint.config.",
    "apps/web/vitest.config.",
    "apps/web/next.config.",
    "apps/web/postcss.config.",
)


def is_protected_path(path: str) -> bool:
    """Check whether a path is a CI-control-plane protected file."""
    if path.startswith(PROTECTED_PREFIXES):
        return True
    if path in PROTECTED_EXACT:
        return True
    return any(path.startswith(g) for g in PROTECTED_GLOBS_WEB)


def classify_pr_files(
    files: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    """Classify PR files into protected and unprotected sets.

    Returns ``(protected_paths, all_paths)`` — both deduplicated and
    sorted for deterministic output.
    """
    all_paths = extract_all_paths(files)
    protected = sorted(p for p in all_paths if is_protected_path(p))
    return protected, sorted(all_paths)
