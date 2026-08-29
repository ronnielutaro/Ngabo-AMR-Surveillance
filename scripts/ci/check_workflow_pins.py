"""Reject mutable external GitHub Action references."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^@\s]+)@([^\s#]+)")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def scan_file(path: Path) -> list[str]:
    errors: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = USES_RE.match(line)
        if not match:
            continue
        action, ref = match.groups()
        if action.startswith("./"):
            continue
        if not SHA_RE.fullmatch(ref):
            errors.append(
                f"{path}:{number}: external action {action}@{ref} "
                "must be pinned to a full 40-hex commit SHA"
            )
    return errors


def scan(root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(root.glob("*.y*ml")):
        errors.extend(scan_file(path))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "workflow_dir", nargs="?", type=Path, default=Path(".github/workflows")
    )
    args = parser.parse_args()
    errors = scan(args.workflow_dir)
    if errors:
        print("\n".join(errors))
        return 1
    print("Workflow pin check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
