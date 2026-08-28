"""Deterministic import deduplication error code enum (Issue #40)."""

from __future__ import annotations

from enum import StrEnum


class ImportDeduplicationErrorCode(StrEnum):
    """Error codes emitted when canonical import deduplication fails."""

    CONFLICTING_DUPLICATE_RECORD = "CONFLICTING_DUPLICATE_RECORD"
