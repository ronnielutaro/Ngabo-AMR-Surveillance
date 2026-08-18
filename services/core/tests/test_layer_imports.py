"""Layer import smoke tests: prove every scaffolded Ngabo layer imports."""

from __future__ import annotations

import importlib

import pytest

LAYERS = ("domain", "application", "interfaces", "infrastructure", "bootstrap")


@pytest.mark.parametrize("layer", LAYERS)
def test_layer_package_imports(layer: str) -> None:
    module = importlib.import_module(f"ngabo.{layer}")
    assert module is not None
