"""Semantic YAML workflow pin checker for Ngabo PR CI."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DOCKER_SHA_RE = re.compile(r"^docker://.*@sha256:[0-9a-f]{64}$")


def _fallback_parse_uses(content: str) -> list[str]:
    """Fallback scanner for environments without PyYAML."""
    uses_list: list[str] = []
    lines = content.splitlines()
    i = 0
    in_run_block = False
    run_indent = 0

    while i < len(lines):
        line_raw = lines[i]
        line = line_raw.strip()

        if not line or line.startswith("#"):
            i += 1
            continue

        indent = len(line_raw) - len(line_raw.lstrip())

        if in_run_block:
            if indent > run_indent:
                i += 1
                continue
            else:
                in_run_block = False

        # Ignore 'run:' steps and multiline script blocks ('run: |', 'run: >')
        if re.match(r"""^\s*(?:-\s*)?run\s*:\s*[|>]?""", line_raw, re.IGNORECASE):
            in_run_block = True
            run_indent = indent
            i += 1
            continue

        # Ignore permission/env blocks
        if re.match(r"""^\s*(?:permissions|env)\s*:""", line_raw, re.IGNORECASE):
            i += 1
            continue

        # Single-line mapping key 'uses: action@ref', '"uses": action@ref', or '- "uses": action@ref' at start of line
        m = re.match(r"""^\s*(?:-\s*)?(?:["']?uses["']?)\s*:\s*(['"]?)([^'"\n#]+)\1""", line_raw, re.IGNORECASE)
        if m:
            val = m.group(2).strip()
            if val and val not in ("read", "write", "none"):
                uses_list.append(val)
                i += 1
                continue

        # Multiline mapping key 'uses:\n  action@ref' or '"uses":\n  action@ref' at start of line
        m_multi = re.match(r"""^\s*(?:-\s*)?(?:["']?uses["']?)\s*:\s*$""", line_raw, re.IGNORECASE)
        if m_multi and i + 1 < len(lines):
            next_line_raw = lines[i + 1]
            next_line = next_line_raw.strip()
            if next_line and not next_line.startswith("#"):
                m_val = re.match(r"""^\s*(['"]?)([^'"\n#]+)\1$""", next_line_raw)
                if m_val:
                    val = m_val.group(2).strip()
                    if val and val not in ("read", "write", "none"):
                        uses_list.append(val)
                        i += 2
                        continue

        i += 1
    return uses_list


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


def traverse_yaml_tree(node: Any, path: Path, parent_key: str | None = None) -> list[str]:
    errors: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            k_str = str(k)
            if k_str == "uses":
                # Only validate 'uses' if parent_key is 'steps' or 'jobs' or in a job/step block (not permissions)
                if parent_key not in ("permissions", "env"):
                    errors.extend(validate_uses_value(v, path))
            elif k_str not in ("permissions", "env"):
                errors.extend(traverse_yaml_tree(v, path, parent_key=k_str))
    elif isinstance(node, list):
        for item in node:
            errors.extend(traverse_yaml_tree(item, path, parent_key=parent_key))
    return errors


def scan_file(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8")
    if yaml is None:
        uses_list = _fallback_parse_uses(content)
        errors: list[str] = []
        for val in uses_list:
            errors.extend(validate_uses_value(val, path))
        return errors

    try:
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
