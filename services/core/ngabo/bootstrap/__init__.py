"""Ngabo bootstrap layer — composition root.

Wires concrete infrastructure into application ports via explicit dependency
injection. Holds the scaffold health entry point and offline certification runners.
"""

from ngabo.bootstrap.certify_hero import certify_hero
from ngabo.bootstrap.health import health

__all__ = ["certify_hero", "health"]
