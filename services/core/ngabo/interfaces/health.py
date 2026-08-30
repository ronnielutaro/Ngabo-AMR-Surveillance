"""Typed health payload contract (Issue #90).

The payload is environment-derived metadata (service identity, source
revision) exposed by both the one-shot ``ngabo-health`` console entry
point (bootstrap) and the minimal HTTP adapter (interfaces). Living here
keeps the dependency direction clean: interfaces never import bootstrap;
bootstrap re-exports this contract for the CLI.

The container contract (Issue #89) enriches the payload with version and
source-revision metadata supplied by the environment (``NGABO_SERVICE_VERSION``,
``NGABO_SOURCE_REVISION``); absent those variables the payload stays minimal.
"""

from __future__ import annotations

import os
from typing import Final

SERVICE_NAME: Final[str] = "ngabo-core"
STATUS_OK: Final[str] = "ok"


def health() -> dict[str, str]:
    """Return the minimal, framework-free health payload."""
    payload: dict[str, str] = {"status": STATUS_OK, "service": SERVICE_NAME}
    version = os.environ.get("NGABO_SERVICE_VERSION")
    if version:
        payload["version"] = version
    revision = os.environ.get("NGABO_SOURCE_REVISION")
    if revision:
        payload["revision"] = revision
    return payload
