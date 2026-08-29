"""Rename-aware changed-path collector for Ngabo PR CI.

Parses ``git diff --name-status -z --find-renames`` output to capture
*both* source and destination for renames (R) and copies (C).  Ordinary
modifications (M), additions (A) and deletions (D) emit only the single
path.

The NUL-separated format is used so filenames containing spaces or other
special characters are handled safely.
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence


def collect_from_git(
    base_sha: str,
    head_sha: str,
) -> set[str]:
    """Run ``git diff`` and return the complete logical changed-path set."""
    cmd = [
        "git", "diff", "--name-status", "-z", "--find-renames",
        "--find-copies", "--diff-filter=ACDMRT",
        base_sha, head_sha,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return parse_name_status_z(proc.stdout)


def parse_name_status_z(raw: str) -> set[str]:
    """Parse NUL-separated ``--name-status -z`` output.

    Format per entry (NUL-delimited):

    - ``M\\0path\\0``
    - ``A\\0path\\0``
    - ``D\\0path\\0``
    - ``R###\\0old\\0new\\0``  (### is the similarity index, e.g. R100)
    - ``C###\\0old\\0new\\0``

    Returns the full set of logical changed paths.
    """
    paths: set[str] = set()
    if not raw:
        return paths

    # Split on NUL; the output always ends with a trailing NUL so the
    # last element after split is an empty string.
    parts = raw.split("\0")
    i = 0
    while i < len(parts):
        token = parts[i]
        if not token:
            i += 1
            continue

        status_char = token[0]
        if status_char in ("R", "C"):
            # Rename / Copy: next two fields are old_path, new_path
            if i + 2 >= len(parts):
                break
            old_path = parts[i + 1]
            new_path = parts[i + 2]
            if old_path:
                paths.add(old_path)
            if new_path:
                paths.add(new_path)
            i += 3
        elif status_char in ("M", "A", "D", "T"):
            # Modification / Addition / Deletion / Type-change: one path
            if i + 1 >= len(parts):
                break
            path = parts[i + 1]
            if path:
                paths.add(path)
            i += 2
        else:
            # Unknown status letter — skip defensively
            i += 1

    return paths


def write_changed_files(paths: set[str], output_path: str) -> None:
    """Write paths to a file, one per line, sorted for determinism."""
    with open(output_path, "w", encoding="utf-8") as f:
        for p in sorted(paths):
            f.write(p + "\n")


def main() -> int:
    """CLI entry point for use in CI workflows."""
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Collect rename-aware changed paths from a Git diff"
    )
    parser.add_argument("--base-sha", default=os.environ.get("BASE_SHA"))
    parser.add_argument("--head-sha", default=os.environ.get("HEAD_SHA"))
    parser.add_argument("--output", default="changed-files.txt")
    args = parser.parse_args()

    if not args.base_sha or not args.head_sha:
        print("ERROR: --base-sha and --head-sha are required", flush=True)
        return 1

    paths = collect_from_git(args.base_sha, args.head_sha)
    write_changed_files(paths, args.output)
    print(f"Collected {len(paths)} changed paths:")
    for p in sorted(paths):
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
