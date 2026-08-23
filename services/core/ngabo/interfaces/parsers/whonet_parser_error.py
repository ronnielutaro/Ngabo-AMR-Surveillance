"""Structured WHONET parser error value object (M2.2 / Issue #39)."""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.interfaces.parsers.whonet_parser_error_code import WhonetParserErrorCode


@dataclass(frozen=True)
class WhonetParserError:
    """Immutable machine-readable error emitted during WHONET CSV parsing/normalization."""

    code: WhonetParserErrorCode
    row_number: int | None = None
    record_index: int | None = None
    column: str | None = None
    record_id: str | None = None
    detail: str | None = None
