"""Deterministic monorepo change classification for Ngabo PR CI."""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

DOC_PREFIXES = ("docs/",)
DOC_FILES = {
    "README.md", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md",
    "ROADMAP.md", "AGENTS.md", "CLAUDE.md", "LICENSE",
}
CORE_PREFIXES = ("services/core/", "data/")
WEB_PREFIXES = ("apps/web/",)
INFRA_PREFIXES = ("infra/gcp/",)
SHARED_FILES = {
    "package.json", "pnpm-workspace.yaml", ".gitignore", ".dockerignore",
    ".gitattributes",
}
WEB_DEPENDENCY_FILES = {"pnpm-lock.yaml", "apps/web/package.json"}
CORE_DEPENDENCY_FILES = {"services/core/pyproject.toml", "services/core/uv.lock"}
CI_CONTROL_PREFIXES = (".github/workflows/", "scripts/ci/", "infra/github/")


@dataclass(frozen=True)
class Classification:
    core_required: bool
    web_required: bool
    infra_required: bool
    shared_required: bool
    dependency_changed: bool
    ci_control_plane_changed: bool
    docs_only: bool
    conservative_fallback: bool = False

    def github_outputs(self) -> dict[str, str]:
        return {key: str(value).lower() for key, value in asdict(self).items()}


def _normalise(paths: Iterable[str]) -> tuple[str, ...]:
    cleaned = []
    for raw in paths:
        value = raw.strip().replace("\\", "/")
        if value.startswith("./"):
            value = value[2:]
        if value:
            cleaned.append(value)
    return tuple(sorted(set(cleaned)))


def _is_docs_only(path: str) -> bool:
    return path in DOC_FILES or path.startswith(DOC_PREFIXES)


def _is_known_non_doc_path(path: str) -> bool:
    if path in SHARED_FILES or path.startswith(CI_CONTROL_PREFIXES):
        return True
    if path in WEB_DEPENDENCY_FILES or path.startswith(WEB_PREFIXES):
        return True
    if path in CORE_DEPENDENCY_FILES or path.startswith(CORE_PREFIXES):
        return True
    return bool(path.startswith(INFRA_PREFIXES))


def classify(paths: Iterable[str]) -> Classification:
    changed = _normalise(paths)
    if not changed:
        return Classification(
            core_required=True,
            web_required=True,
            infra_required=True,
            shared_required=True,
            dependency_changed=True,
            ci_control_plane_changed=True,
            docs_only=False,
            conservative_fallback=True,
        )

    docs_only = all(_is_docs_only(path) for path in changed)
    if docs_only:
        return Classification(
            core_required=False,
            web_required=False,
            infra_required=False,
            shared_required=False,
            dependency_changed=False,
            ci_control_plane_changed=False,
            docs_only=True,
            conservative_fallback=False,
        )

    has_unclassified_non_doc = any(
        not _is_docs_only(path) and not _is_known_non_doc_path(path)
        for path in changed
    )

    ci_control = any(path.startswith(CI_CONTROL_PREFIXES) for path in changed)
    shared = any(path in SHARED_FILES for path in changed) or ci_control or has_unclassified_non_doc
    core = (
        shared
        or any(path.startswith(CORE_PREFIXES) or path in CORE_DEPENDENCY_FILES for path in changed)
    )
    web = (
        shared
        or any(path.startswith(WEB_PREFIXES) or path in WEB_DEPENDENCY_FILES for path in changed)
    )
    infra = shared or any(path.startswith(INFRA_PREFIXES) for path in changed)
    dependency_changed = any(
        path in WEB_DEPENDENCY_FILES or path in CORE_DEPENDENCY_FILES
        for path in changed
    )

    return Classification(
        core_required=core,
        web_required=web,
        infra_required=infra,
        shared_required=shared,
        dependency_changed=dependency_changed,
        ci_control_plane_changed=ci_control,
        docs_only=False,
        conservative_fallback=has_unclassified_non_doc,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("changed_file_list", type=Path)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    changed = args.changed_file_list.read_text(encoding="utf-8").splitlines()
    result = classify(changed)

    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            for key, value in result.github_outputs().items():
                handle.write(f"{key}={value}\n")

    if args.json:
        print(json.dumps(asdict(result), sort_keys=True))
    else:
        for key, value in result.github_outputs().items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
