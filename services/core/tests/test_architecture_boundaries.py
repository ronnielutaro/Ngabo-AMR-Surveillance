"""Architecture smoke tests for the Ngabo Clean Architecture scaffold.

Statically verify that the inner layers (``domain``, ``application``) do not
import outer frameworks, vendor SDKs, or outer Ngabo layers. Deliberately
lightweight: they catch obvious forbidden module-level imports rather than
enforcing every rule in ``docs/CLEAN_ARCHITECTURE.md``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "ngabo"

# Framework / vendor SDKs that must never appear inside inner layers.
_FORBIDDEN_FRAMEWORKS = (
    "fastapi",
    "starlette",
    "google",
    "firebase",
    "vertexai",
)

_DOMAIN = PACKAGE_ROOT / "domain"
_APPLICATION = PACKAGE_ROOT / "application"


def _python_files(directory: Path) -> list[Path]:
    return sorted(directory.rglob("*.py"))


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module)
    return modules


def _is_framework(module: str) -> bool:
    return any(
        module == prefix or module.startswith(f"{prefix}.") for prefix in _FORBIDDEN_FRAMEWORKS
    )


def _is_outer_layer(module: str, outer_layers: tuple[str, ...]) -> bool:
    return any(module == layer or module.startswith(f"{layer}.") for layer in outer_layers)


def _forbidden(imported: set[str], outer_layers: tuple[str, ...]) -> set[str]:
    return {
        module
        for module in imported
        if _is_framework(module) or _is_outer_layer(module, outer_layers)
    }


@pytest.mark.parametrize("path", _python_files(_DOMAIN), ids=lambda p: str(p))
def test_domain_has_no_forbidden_imports(path: Path) -> None:
    forbidden = _forbidden(
        _imported_modules(path),
        ("ngabo.application", "ngabo.interfaces", "ngabo.infrastructure", "ngabo.bootstrap"),
    )
    assert forbidden == set(), f"forbidden imports in {path}: {sorted(forbidden)}"


@pytest.mark.parametrize("path", _python_files(_APPLICATION), ids=lambda p: str(p))
def test_application_has_no_forbidden_imports(path: Path) -> None:
    forbidden = _forbidden(
        _imported_modules(path),
        ("ngabo.interfaces", "ngabo.infrastructure", "ngabo.bootstrap"),
    )
    assert forbidden == set(), f"forbidden imports in {path}: {sorted(forbidden)}"
