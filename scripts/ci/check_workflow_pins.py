"""Semantic YAML workflow pin checker for Ngabo PR CI."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DOCKER_SHA_RE = re.compile(r"^docker://.*@sha256:[0-9a-f]{64}$")


def validate_uses_value(uses_val: Any, path: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(uses_val, str):
        return [f"{path}: 'uses' key value is not a string: {uses_val!r}"]

    val = uses_val.strip()
    if not val:
        return [f"{path}: 'uses' key value is empty"]

    # Local reference: starts with ./ or .github/
    if val.startswith("./") or val.startswith(".github/"):
        return []

    # Docker action reference
    if val.startswith("docker://"):
        if not DOCKER_SHA_RE.fullmatch(val):
            errors.append(
                f"{path}: docker action '{val}' must be pinned to an immutable @sha256:<64-hex> digest"
            )
        return errors

    # External GitHub Action or Reusable Workflow (owner/repo@ref or owner/repo/path@ref)
    if "@" not in val:
        errors.append(
            f"{path}: external action/workflow '{val}' missing '@<commit-sha>' version ref"
        )
        return errors

    action, ref = val.rsplit("@", 1)
    if not SHA_RE.fullmatch(ref):
        errors.append(
            f"{path}: external action/workflow '{val}' must be pinned to a full 40-hex commit SHA (got '{ref}')"
        )

    return errors


def traverse_yaml_tree(node: Any, path: Path) -> list[str]:
    errors: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            if str(k) == "uses":
                errors.extend(validate_uses_value(v, path))
            else:
                errors.extend(traverse_yaml_tree(v, path))
    elif isinstance(node, list):
        for item in node:
            errors.extend(traverse_yaml_tree(item, path))
    return errors


def scan_file(path: Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
    except Exception as exc:
        return [f"{path}: failed to parse YAML: {exc}"]

    if data is None:
        return []
    return traverse_yaml_tree(data, path)


def scan(root: Path) -> list[str]:
    errors: list[str] = []
    for ext in ("*.yml", "*.yaml"):
        for path in sorted(root.glob(ext)):
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
