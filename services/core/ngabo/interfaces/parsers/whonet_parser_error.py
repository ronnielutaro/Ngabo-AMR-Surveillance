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

    def __post_init__(self) -> None:
        if not isinstance(self.code, WhonetParserErrorCode):
            raise TypeError(f"Invalid code {self.code!r}; expected WhonetParserErrorCode")
        if self.row_number is not None and (
            not isinstance(self.row_number, int)
            or isinstance(self.row_number, bool)
            or self.row_number < 1
        ):
            raise ValueError(f"Invalid row_number {self.row_number!r}; expected positive integer")
        if self.record_index is not None and (
            not isinstance(self.record_index, int)
            or isinstance(self.record_index, bool)
            or self.record_index < 0
        ):
            raise ValueError(
                f"Invalid record_index {self.record_index!r}; expected non-negative integer"
            )
