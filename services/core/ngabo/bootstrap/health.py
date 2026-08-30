"""Minimal bootstrap health check for the M1A scaffold.

Proves the ``ngabo`` package imports and a tiny entry point runs. No Ngabo
domain behavior exists yet (see Issue #12 scope).

The payload contract lives in the interfaces layer (``ngabo.interfaces.health``)
so the HTTP adapter (Issue #90) never depends on bootstrap; this module
re-exports it for the one-shot ``ngabo-health`` console entry point.
"""

from __future__ import annotations

import json

from ngabo.interfaces.health import health  # noqa: F401  (re-exported contract)


def main() -> None:
    """Print the health payload as JSON (console entry point ``ngabo-health``)."""
    print(json.dumps(health()))


if __name__ == "__main__":
    main()
