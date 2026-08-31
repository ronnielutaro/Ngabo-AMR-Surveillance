"""HMAC-SHA256 authenticated upload scheme for the Connect deadline slice (#171).

Deterministic, model-free authentication for the synthetic intake boundary. The
desktop client signs raw CSV bytes with a per-source shared secret; the intake
service verifies the signature, digest, timestamp freshness and configured source.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import time
from collections.abc import Mapping

_FILENAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]+\.csv$")


def compute_signature(
    secret: bytes,
    lab_id: str,
    source_id: str,
    timestamp: str,
    sha256: str,
    filename: str,
    body: bytes,
) -> str:
    canonical = "|".join((lab_id, source_id, timestamp, sha256, filename)).encode("utf-8")
    signed = canonical + b"|" + body
    return hmac.new(secret, signed, hashlib.sha256).hexdigest()


def verify_upload(
    *,
    headers: Mapping[str, str],
    body: bytes,
    secret: bytes,
    configured_lab_ids: set[str],
    configured_source_ids: set[str],
    max_bytes: int = 5_000_000,
    clock_window_seconds: float = 300.0,
    now: float | None = None,
) -> tuple[bool, str | None]:
    """Verify a signed upload; returns (ok, error)."""
    # HTTP field names are case-insensitive. Starlette exposes them lowercase,
    # while the desktop client and unit fixtures use conventional title case.
    normalized = {key.lower(): value for key, value in headers.items()}
    lab_id = normalized.get("x-ngabo-lab-id", "")
    source_id = normalized.get("x-ngabo-source-id", "")
    timestamp = normalized.get("x-ngabo-timestamp", "")
    sha256 = normalized.get("x-ngabo-content-sha256", "")
    signature = normalized.get("x-ngabo-signature", "")
    filename = normalized.get("x-ngabo-filename", "")
    if lab_id not in configured_lab_ids:
        return False, "unknown lab_id"
    if source_id not in configured_source_ids:
        return False, "unknown source_id"
    if not _FILENAME_PATTERN.fullmatch(filename):
        return False, "invalid filename"
    if not body:
        return False, "empty body"
    if len(body) > max_bytes:
        return False, "body too large"
    if hashlib.sha256(body).hexdigest() != sha256:
        return False, "sha256 mismatch"
    try:
        ts = float(timestamp)
    except ValueError:
        return False, "invalid timestamp"
    current = now if now is not None else time.time()
    if abs(current - ts) > clock_window_seconds:
        return False, "timestamp outside window"
    expected = compute_signature(secret, lab_id, source_id, timestamp, sha256, filename, body)
    if not hmac.compare_digest(expected, signature):
        return False, "signature mismatch"
    return True, None
