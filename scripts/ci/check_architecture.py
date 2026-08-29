"""Executable Clean Architecture import-boundary checks for ngabo-core."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

INNER_LAYER_FORBIDDEN: dict[str, tuple[str, ...]] = {
    "domain": (
        "ngabo.application", "ngabo.interfaces", "ngabo.infrastructure",
        "ngabo.bootstrap",
    ),
    "application": ("ngabo.interfaces", "ngabo.infrastructure", "ngabo.bootstrap"),
}

VENDOR_PREFIXES = (
    "fastapi", "google", "vertexai", "firebase_admin", "requests", "httpx",
)


@dataclass(frozen=True)
class Violation:
    path: str
    line: int
    imported: str
    reason: str


def _imports(tree: ast.AST) -> Iterable[tuple[int, str]]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.lineno, node.module


def _layer_for(path: Path, root: Path) -> str | None:
    relative = path.relative_to(root)
    return relative.parts[0] if relative.parts else None


def check_tree(root: Path) -> list[Violation]:
    violations: list[Violation] = []
    for path in sorted(root.rglob("*.py")):
        layer = _layer_for(path, root)
        if layer not in INNER_LAYER_FORBIDDEN:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            violations.append(
                Violation(
                    str(path), exc.lineno or 0, "<syntax-error>",
                    f"cannot parse file: {exc.msg}",
                )
            )
            continue

        for line, imported in _imports(tree):
            forbidden_layers = INNER_LAYER_FORBIDDEN[layer]
            if imported.startswith(forbidden_layers):
                violations.append(
                    Violation(
                        str(path), line, imported,
                        f"{layer} must not depend on an outer Ngabo layer",
                    )
                )
            elif imported.startswith(VENDOR_PREFIXES):
                violations.append(
                    Violation(
                        str(path), line, imported,
                        f"{layer} must not directly depend on framework/cloud/network SDKs",
                    )
                )
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default="services/core/ngabo", type=Path)
    args = parser.parse_args()
    violations = check_tree(args.root)
    if not violations:
        print("Architecture check passed: inner-layer imports point inward.")
        return 0
    print("Architecture check failed:")
    for item in violations:
        print(f"- {item.path}:{item.line}: import {item.imported!r}: {item.reason}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
