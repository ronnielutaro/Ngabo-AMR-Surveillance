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

        # Ignore permission/env/with/inputs blocks in fallback scanner
        if re.match(r"""^\s*(?:permissions|env|with|inputs)\s*:""", line_raw, re.IGNORECASE):
            i += 1
            continue

        # Single-line mapping key 'uses: action@ref', '"uses": action@ref', or inline '{ uses: action@ref }'
        m = re.search(r"""(?:^\s*(?:-\s*)?|\{\s*)(?:["']?uses["']?)\s*:\s*(['"]?)([^'"\}\n#]+)\1""", line_raw, re.IGNORECASE)
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


def _find_repo_root(path: Path) -> Path:
    """Find repository root by walking up from path."""
    curr = path.resolve() if path.is_dir() else path.resolve().parent
    for p in (curr, *curr.parents):
        if (p / ".git").exists() or (p / ".github").is_dir() or (p / "package.json").is_file():
            return p
    return curr


def _resolve_local_action(
    val: str, calling_file: Path, repo_root: Path | None = None
) -> Path | None:
    """Resolve a local action path to its action.yml or action.yaml manifest."""
    root = repo_root or _find_repo_root(calling_file)
    cleaned = val.lstrip(".").lstrip("/").replace("\\", "/")

    # GitHub Actions always resolves ./relative paths in workflows from repo root
    candidates: list[Path] = [
        root / cleaned,
        calling_file.parent / val,
        calling_file.parent / cleaned,
        Path(val).resolve(),
    ]

    for cand in candidates:
        if cand.is_file() and cand.suffix in (".yml", ".yaml"):
            return cand.resolve()
        if cand.is_dir():
            for name in ("action.yml", "action.yaml"):
                manifest = cand / name
                if manifest.is_file():
                    return manifest.resolve()
    return None


def validate_uses_value(
    uses_val: Any,
    path: Path,
    allow_fallback: bool = False,
    repo_root: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(uses_val, str):
        return [f"{path}: 'uses' key value is not a string: {uses_val!r}"]

    val = uses_val.strip()
    if not val:
        return [f"{path}: 'uses' key value is empty"]

    # Local reference: starts with ./ or .github/
    if val.startswith("./") or val.startswith(".github/"):
        manifest = _resolve_local_action(val, path, repo_root=repo_root)
        if manifest is None:
            errors.append(f"{path}: referenced local action '{val}' could not be resolved")
            return errors
        if manifest != path.resolve():
            errors.extend(
                scan_file(manifest, allow_fallback=allow_fallback, repo_root=repo_root)
            )
        return errors

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


def _check_step(
    step: Any,
    path: Path,
    allow_fallback: bool = False,
    repo_root: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    if isinstance(step, dict) and "uses" in step:
        errors.extend(
            validate_uses_value(
                step["uses"], path, allow_fallback=allow_fallback, repo_root=repo_root
            )
        )
    return errors


def check_workflow_tree(
    data: Any,
    path: Path,
    allow_fallback: bool = False,
    repo_root: Path | None = None,
) -> list[str]:
    """Check action and reusable workflow pin compliance in parsed YAML data.

    Inspects ONLY actual action execution positions:
    - Reusable workflow calls at job level: `jobs.<job_id>.uses`
    - Action references at step level: `jobs.<job_id>.steps[i].uses`
    - Composite action step references: `runs.steps[i].uses`
    - Direct step list references: `steps[i].uses`

    Non-action data positions (such as `with.uses`, `inputs.uses`, `env.uses`)
    are not treated as action references.
    """
    errors: list[str] = []
    if not isinstance(data, dict):
        return errors

    # 1. Top-level steps list (workflow step snippets or action manifests)
    top_steps = data.get("steps")
    if isinstance(top_steps, list):
        for step in top_steps:
            errors.extend(
                _check_step(
                    step, path, allow_fallback=allow_fallback, repo_root=repo_root
                )
            )

    # 2. Workflow jobs: jobs.<job_id>
    jobs = data.get("jobs")
    if isinstance(jobs, dict):
        for _job_id, job in jobs.items():
            if not isinstance(job, dict):
                continue
            # Reusable workflow call at job level
            if "uses" in job:
                errors.extend(
                    validate_uses_value(
                        job["uses"],
                        path,
                        allow_fallback=allow_fallback,
                        repo_root=repo_root,
                    )
                )
            # Steps within job
            steps = job.get("steps")
            if isinstance(steps, list):
                for step in steps:
                    errors.extend(
                        _check_step(
                            step,
                            path,
                            allow_fallback=allow_fallback,
                            repo_root=repo_root,
                        )
                    )

    # 3. Composite action definition: runs.steps
    runs = data.get("runs")
    if isinstance(runs, dict):
        steps = runs.get("steps")
        if isinstance(steps, list):
            for step in steps:
                errors.extend(
                    _check_step(
                        step, path, allow_fallback=allow_fallback, repo_root=repo_root
                    )
                )

    return errors


def scan_file(
    path: Path,
    allow_fallback: bool = False,
    repo_root: Path | None = None,
) -> list[str]:
    content = path.read_text(encoding="utf-8")
    if yaml is None:
        if not allow_fallback:
            return [
                f"{path}: PyYAML is required for authoritative workflow pin checking but is not installed. "
                f"Refusing to evaluate pins via fallback."
            ]
        uses_list = _fallback_parse_uses(content)
        errors: list[str] = []
        for val in uses_list:
            errors.extend(
                validate_uses_value(
                    val, path, allow_fallback=allow_fallback, repo_root=repo_root
                )
            )
        return errors

    try:
        data = yaml.safe_load(content)
    except Exception as exc:
        return [f"{path}: failed to parse YAML: {exc}"]

    if data is None:
        return []
    return check_workflow_tree(
        data, path, allow_fallback=allow_fallback, repo_root=repo_root
    )


def scan(
    root: Path,
    allow_fallback: bool = False,
    repo_root: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    paths: set[Path] = set()
    root_resolved = root.resolve()
    effective_repo_root = repo_root or _find_repo_root(root_resolved)

    if root_resolved.is_file():
        paths.add(root_resolved)
    elif root_resolved.is_dir():
        for ext in ("*.yml", "*.yaml"):
            paths.update(p.resolve() for p in root_resolved.rglob(ext))
        # If scanning a workflows directory, also look for sibling actions directory
        if root_resolved.name == "workflows" and (root_resolved.parent / "actions").is_dir():
            for ext in ("*.yml", "*.yaml"):
                paths.update(p.resolve() for p in (root_resolved.parent / "actions").rglob(ext))
    for path in sorted(paths):
        errors.extend(
            scan_file(
                path,
                allow_fallback=allow_fallback,
                repo_root=effective_repo_root,
            )
        )
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Authoritative semantic YAML workflow pin checker."
    )
    parser.add_argument(
        "workflow_dir", nargs="?", type=Path, default=Path(".github/workflows")
    )
    parser.add_argument(
        "--allow-fallback",
        action="store_true",
        help="Allow fallback scanner for optional local diagnostics without PyYAML (never authoritative in CI)",
    )
    args = parser.parse_args()
    errors = scan(args.workflow_dir, allow_fallback=args.allow_fallback)
    if errors:
        print("\n".join(errors))
        return 1
    print("Workflow pin check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
