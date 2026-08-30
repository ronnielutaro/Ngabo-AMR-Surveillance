"""Typed runtime identity contracts (Issue #90).

The payloads are environment-derived metadata exposed by the HTTP adapter
(interfaces) and the one-shot ``ngabo-health`` console entry point
(bootstrap). Living here keeps the dependency direction clean: interfaces
never import bootstrap; bootstrap re-exports this contract for the CLI.

Identity fields come ONLY from deployment-supplied environment:

- ``NGABO_SERVICE_VERSION``  — application version (default 0.1.0).
- ``NGABO_SOURCE_REVISION``  — source commit SHA (container build injects it).
- ``NGABO_IMAGE_DIGEST``     — immutable Artifact Registry digest
  (``sha256:<64 hex>``) injected by the trusted deployment from the exact
  digest it deploys. Never invented or derived from a mutable tag here.
- ``NGABO_ENVIRONMENT``      — deployment environment (default development).

A malformed/absent ``NGABO_IMAGE_DIGEST`` is NOT reported as a digest: the
field is omitted and the consumer must treat the identity as incomplete
(web renders SCHEMA_MISMATCH rather than LIVE with an invented value).
"""

from __future__ import annotations

import os
import re
from typing import Final

SERVICE_NAME: Final[str] = "ngabo-core"
STATUS_OK: Final[str] = "ok"
DEFAULT_VERSION: Final[str] = "0.1.0"
DEFAULT_ENVIRONMENT: Final[str] = "development"

DIGEST_RE: Final[re.Pattern[str]] = re.compile(r"^sha256:[0-9a-f]{64}$")


def health() -> dict[str, str]:
    """Return the minimal, framework-free liveness payload."""
    payload: dict[str, str] = {"status": STATUS_OK, "service": SERVICE_NAME}
    version = os.environ.get("NGABO_SERVICE_VERSION")
    if version:
        payload["version"] = version
    revision = os.environ.get("NGABO_SOURCE_REVISION")
    if revision:
        payload["revision"] = revision
    return payload


def readiness() -> dict[str, str | bool]:
    """Return the readiness payload (liveness plus ready: true)."""
    payload: dict[str, str | bool] = dict(health())
    payload["ready"] = True
    return payload


def runtime_identity() -> dict[str, str]:
    """Return the runtime/artifact identity payload for /version.

    Includes the immutable image digest ONLY when a valid ``sha256:<64 hex>``
    value is supplied via ``NGABO_IMAGE_DIGEST``; absent or malformed values
    are omitted so consumers can distinguish complete identity from missing.
    """
    payload: dict[str, str] = {
        "service": SERVICE_NAME,
        "version": os.environ.get("NGABO_SERVICE_VERSION", DEFAULT_VERSION),
        "revision": os.environ.get("NGABO_SOURCE_REVISION", "unknown"),
        "environment": os.environ.get("NGABO_ENVIRONMENT", DEFAULT_ENVIRONMENT),
    }
    image_digest = os.environ.get("NGABO_IMAGE_DIGEST", "")
    if DIGEST_RE.fullmatch(image_digest):
        payload["image_digest"] = image_digest
    return payload
