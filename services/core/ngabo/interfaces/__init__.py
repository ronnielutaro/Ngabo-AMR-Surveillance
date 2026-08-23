"""Interfaces layer: transport, API, and format adapters (M2.2 / Issue #39)."""

from __future__ import annotations

from ngabo.interfaces.parsers import (
    ACCEPTED_INTERPRETATIONS,
    DEFAULT_WHONET_COLUMN_MAPPING,
    WhonetParserError,
    WhonetParserErrorCode,
    WhonetParseResult,
    parse_whonet_csv,
)

__all__ = [
    "ACCEPTED_INTERPRETATIONS",
    "DEFAULT_WHONET_COLUMN_MAPPING",
    "WhonetParseResult",
    "WhonetParserError",
    "WhonetParserErrorCode",
    "parse_whonet_csv",
]
