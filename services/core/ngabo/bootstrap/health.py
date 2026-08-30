"""Minimal bootstrap health check for the M1A scaffold.

Proves the ``ngabo`` package imports and a tiny entry point runs. No Ngabo
domain behavior exists yet (see Issue #12 scope).

The container contract (Issue #89) may enrich the payload with version and
source-revision metadata supplied by the environment (``NGABO_SERVICE_VERSION``,
``NGABO_SOURCE_REVISION``); absent those variables the payload stays minimal.
"""

from __future__ import annotations

import json
import os
from typing import Final

SERVICE_NAME: Final[str] = "ngabo-core"
STATUS_OK: Final[str] = "ok"


def health() -> dict[str, str]:
    """Return a minimal, framework-free health payload."""
    payload: dict[str, str] = {"status": STATUS_OK, "service": SERVICE_NAME}
    version = os.environ.get("NGABO_SERVICE_VERSION")
    if version:
        payload["version"] = version
    revision = os.environ.get("NGABO_SOURCE_REVISION")
    if revision:
        payload["revision"] = revision
    return payload


def main() -> None:
    """Print the health payload as JSON (console entry point ``ngabo-health``)."""
    print(json.dumps(health()))


if __name__ == "__main__":
    main()
