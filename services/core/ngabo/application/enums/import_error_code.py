"""Deterministic application-level import error codes (Issue #44)."""

from __future__ import annotations

from enum import StrEnum


class ImportErrorCode(StrEnum):
    """Error codes emitted when canonical import orchestration fails."""

    SOURCE_READ_ERROR = "SOURCE_READ_ERROR"
    UTF8_DECODE_ERROR = "UTF8_DECODE_ERROR"
    PARSER_FAILURE = "PARSER_FAILURE"
    CANONICAL_VALIDATION_FAILURE = "CANONICAL_VALIDATION_FAILURE"
    CONFLICTING_DUPLICATE_RECORD = "CONFLICTING_DUPLICATE_RECORD"
    REPOSITORY_ERROR = "REPOSITORY_ERROR"
