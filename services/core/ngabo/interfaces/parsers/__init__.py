"""Parser interface adapters for external laboratory formats (M2.2 / Issue #39)."""

from __future__ import annotations

from ngabo.interfaces.parsers.whonet_csv_parser import (
    ACCEPTED_INTERPRETATIONS,
    DEFAULT_WHONET_COLUMN_MAPPING,
    parse_whonet_csv,
)
from ngabo.interfaces.parsers.whonet_parse_result import WhonetParseResult
from ngabo.interfaces.parsers.whonet_parser_error import WhonetParserError
from ngabo.interfaces.parsers.whonet_parser_error_code import WhonetParserErrorCode

__all__ = [
    "ACCEPTED_INTERPRETATIONS",
    "DEFAULT_WHONET_COLUMN_MAPPING",
    "WhonetParseResult",
    "WhonetParserError",
    "WhonetParserErrorCode",
    "parse_whonet_csv",
]
