"""Architecture smoke tests for the Ngabo Clean Architecture scaffold.

Statically verify that the inner layers (``domain``, ``application``) do not
import outer frameworks, vendor SDKs, or outer Ngabo layers. Both absolute
and relative imports are resolved before checking. Deliberately lightweight:
they catch obvious forbidden module-level imports rather than enforcing every
rule in ``docs/CLEAN_ARCHITECTURE.md``.
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

# Ngabo layers outside the scanned inner layer, in dependency order.
_DOMAIN_OUTER_LAYERS = (
    "ngabo.application",
    "ngabo.interfaces",
    "ngabo.infrastructure",
    "ngabo.bootstrap",
)
_APPLICATION_OUTER_LAYERS = (
    "ngabo.interfaces",
    "ngabo.infrastructure",
    "ngabo.bootstrap",
)


def _python_files(directory: Path) -> list[Path]:
    return sorted(directory.rglob("*.py"))


def _module_package(path: Path) -> str:
    """Dotted package name of the directory containing ``path``."""
    relative = path.relative_to(PACKAGE_ROOT.parent)
    # Drop the file's own name; ``__init__.py`` files are the package itself.
    parts = relative.with_suffix("").parts[:-1]
    return ".".join(parts)


def _resolve_relative_import(node: ast.ImportFrom, package_name: str) -> set[str]:
    """Resolve a relative ``ImportFrom`` to absolute dotted module names."""
    package_parts = package_name.split(".")
    if node.level - 1 >= len(package_parts):
        return set()  # hops above the top-level package; invalid Python
    base = package_parts[: len(package_parts) - (node.level - 1)]
    if node.module:
        return {".".join([*base, node.module])}
    return {".".join([*base, alias.name]) for alias in node.names}


def _collected_imports(source: str, package_name: str) -> set[str]:
    """Imported module names in ``source`` with relative imports resolved."""
    tree = ast.parse(source)
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                if node.module:
                    modules.add(node.module)
            else:
                modules.update(_resolve_relative_import(node, package_name))
    return modules


def _imported_modules(path: Path) -> set[str]:
    return _collected_imports(path.read_text(encoding="utf-8"), _module_package(path))


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
    forbidden = _forbidden(_imported_modules(path), _DOMAIN_OUTER_LAYERS)
    assert forbidden == set(), f"forbidden imports in {path}: {sorted(forbidden)}"


@pytest.mark.parametrize("path", _python_files(_APPLICATION), ids=lambda p: str(p))
def test_application_has_no_forbidden_imports(path: Path) -> None:
    forbidden = _forbidden(_imported_modules(path), _APPLICATION_OUTER_LAYERS)
    assert forbidden == set(), f"forbidden imports in {path}: {sorted(forbidden)}"


def test_absolute_outer_layer_import_is_forbidden() -> None:
    imported = _collected_imports(
        "from ngabo.infrastructure.foo import Bar", "ngabo.application"
    )
    assert _forbidden(imported, _APPLICATION_OUTER_LAYERS) == {"ngabo.infrastructure.foo"}


def test_relative_outer_layer_import_is_forbidden() -> None:
    imported = _collected_imports(
        "from ..infrastructure.foo import Bar", "ngabo.application"
    )
    assert _forbidden(imported, _APPLICATION_OUTER_LAYERS) == {"ngabo.infrastructure.foo"}


def test_relative_outer_package_import_is_forbidden() -> None:
    imported = _collected_imports(
        "from .. import infrastructure", "ngabo.application"
    )
    assert _forbidden(imported, _APPLICATION_OUTER_LAYERS) == {"ngabo.infrastructure"}


def test_relative_inner_layer_import_is_allowed() -> None:
    imported = _collected_imports(
        "from ..domain.models import Isolate", "ngabo.application"
    )
    assert _forbidden(imported, _APPLICATION_OUTER_LAYERS) == set()


def test_module_package_anchors_at_containing_package() -> None:
    path = PACKAGE_ROOT / "application" / "use_cases" / "foo.py"
    assert _module_package(path) == "ngabo.application.use_cases"


def test_module_package_preserves_init_package() -> None:
    path = PACKAGE_ROOT / "application" / "use_cases" / "__init__.py"
    assert _module_package(path) == "ngabo.application.use_cases"


def test_nested_module_relative_outer_import_is_forbidden() -> None:
    package = _module_package(PACKAGE_ROOT / "application" / "use_cases" / "foo.py")
    imported = _collected_imports("from ...infrastructure.foo import Bar", package)
    assert _forbidden(imported, _APPLICATION_OUTER_LAYERS) == {"ngabo.infrastructure.foo"}


def test_nested_module_relative_inward_import_is_allowed() -> None:
    package = _module_package(PACKAGE_ROOT / "application" / "use_cases" / "foo.py")
    imported = _collected_imports("from ...domain.models import Isolate", package)
    assert _forbidden(imported, _APPLICATION_OUTER_LAYERS) == set()


def test_fastapi_allowed_in_interfaces_layer() -> None:
    """Issue #90: the interfaces HTTP adapter is the sanctioned FastAPI
    boundary. The vendor-SDK prohibition applies to domain and application
    only (VENDOR_FORBIDDEN_LAYERS), so a FastAPI import under interfaces
    must not be reported by the architecture checker."""
    import importlib.util
    import sys as _sys

    checker_path = Path(__file__).resolve().parents[3] / "scripts" / "ci" / "check_architecture.py"
    spec = importlib.util.spec_from_file_location("check_architecture", checker_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    _sys.modules["check_architecture"] = module
    try:
        spec.loader.exec_module(module)
        assert "interfaces" not in module.VENDOR_FORBIDDEN_LAYERS
        assert "domain" in module.VENDOR_FORBIDDEN_LAYERS
        assert "application" in module.VENDOR_FORBIDDEN_LAYERS
    finally:
        _sys.modules.pop("check_architecture", None)


def test_fastapi_forbidden_in_domain() -> None:
    imported = _collected_imports("from fastapi import FastAPI", "ngabo.domain")
    assert _forbidden(imported, _DOMAIN_OUTER_LAYERS) == {"fastapi"}


def test_fastapi_forbidden_in_application() -> None:
    imported = _collected_imports("from fastapi import FastAPI", "ngabo.application")
    assert _forbidden(imported, _APPLICATION_OUTER_LAYERS) == {"fastapi"}
