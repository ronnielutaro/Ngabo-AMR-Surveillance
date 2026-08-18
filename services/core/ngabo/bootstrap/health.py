"""Minimal bootstrap health check for the M1A scaffold.

Proves the ``ngabo`` package imports and a tiny entry point runs. No Ngabo
domain behavior exists yet (see Issue #12 scope).
"""

from __future__ import annotations

import json
from typing import Final

SERVICE_NAME: Final[str] = "ngabo-core"
STATUS_OK: Final[str] = "ok"


def health() -> dict[str, str]:
    """Return a minimal, framework-free health payload."""
    return {"status": STATUS_OK, "service": SERVICE_NAME}


def main() -> None:
    """Print the health payload as JSON (console entry point ``ngabo-health``)."""
    print(json.dumps(health()))


if __name__ == "__main__":
    main()
