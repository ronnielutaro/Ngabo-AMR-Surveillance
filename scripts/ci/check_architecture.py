"""Executable Clean Architecture import-boundary checks for ngabo-core."""

from __future__ import annotations

import argparse
import ast
import importlib.util
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

INNER_LAYER_FORBIDDEN: dict[str, tuple[str, ...]] = {
    "domain": (
        "ngabo.application", "ngabo.interfaces", "ngabo.infrastructure",
        "ngabo.bootstrap",
    ),
    "application": ("ngabo.interfaces", "ngabo.infrastructure", "ngabo.bootstrap"),
    "interfaces": ("ngabo.infrastructure", "ngabo.bootstrap"),
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


def _imports(tree: ast.AST, package: str) -> Iterable[tuple[int, str]]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
        elif isinstance(node, ast.ImportFrom):
            level = node.level
            module = node.module
            if level == 0:
                if module:
                    yield node.lineno, module
                    for alias in node.names:
                        yield node.lineno, f"{module}.{alias.name}"
            else:
                rel_name = f"{'.' * level}{module}" if module else ("." * level)
                try:
                    resolved_base = importlib.util.resolve_name(rel_name, package)
                except ValueError:
                    yield node.lineno, f"<invalid-relative-import:{rel_name}>"
                    continue
                yield node.lineno, resolved_base
                for alias in node.names:
                    yield node.lineno, f"{resolved_base}.{alias.name}"


def _layer_for(path: Path, root: Path) -> str | None:
    relative = path.relative_to(root)
    if relative.parts and relative.parts[0] == "ngabo":
        relative = Path(*relative.parts[1:])
    return relative.parts[0] if relative.parts else None


def _package_for(path: Path, root: Path) -> str:
    relative = path.relative_to(root)
    parts = list(relative.parts)
    if parts and parts[0] == "ngabo":
        parts = parts[1:]
    if not parts:
        return "ngabo"
    dir_parts = parts[:-1]
    if dir_parts:
        return f"ngabo.{'.'.join(dir_parts)}"
    return "ngabo"


def check_tree(root: Path) -> list[Violation]:
    violations: list[Violation] = []
    seen_violations: set[tuple[str, int, str]] = set()

    for path in sorted(root.rglob("*.py")):
        layer = _layer_for(path, root)
        if layer not in INNER_LAYER_FORBIDDEN:
            continue
        package = _package_for(path, root)
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

        forbidden_layers = INNER_LAYER_FORBIDDEN[layer]
        for line, imported in _imports(tree, package):
            if imported.startswith(forbidden_layers):
                key = (str(path), line, "outer_layer")
                if key not in seen_violations:
                    seen_violations.add(key)
                    violations.append(
                        Violation(
                            str(path), line, imported,
                            f"{layer} must not depend on an outer Ngabo layer",
                        )
                    )
            elif imported.startswith(VENDOR_PREFIXES):
                key = (str(path), line, "vendor")
                if key not in seen_violations:
                    seen_violations.add(key)
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
