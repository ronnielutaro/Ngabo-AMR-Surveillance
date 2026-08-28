"""Structured failure detail for application import orchestration (Issue #44)."""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.application.enums.import_error_code import ImportErrorCode


@dataclass(frozen=True)
class ImportErrorDetail:
    """Structured, machine-readable failure detail for an import error."""

    code: ImportErrorCode
    message: str
    field: str | None = None
    line_number: int | None = None
    record_index: int | None = None
    isolate_id: str | None = None
    indices: tuple[int, ...] = ()
    differing_fields: tuple[str, ...] = ()
    source_code: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, ImportErrorCode):
            raise TypeError(f"Invalid code {self.code!r}; expected ImportErrorCode")
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("message must be a non-empty string")
        if self.record_index is not None and (
            not isinstance(self.record_index, int)
            or isinstance(self.record_index, bool)
            or self.record_index < 0
        ):
            raise ValueError(
                f"Invalid record_index {self.record_index!r}; expected non-negative integer"
            )
        if self.line_number is not None and (
            not isinstance(self.line_number, int)
            or isinstance(self.line_number, bool)
            or self.line_number < 1
        ):
            raise ValueError(
                f"Invalid line_number {self.line_number!r}; expected positive integer"
            )
        if not isinstance(self.indices, tuple):
            raise TypeError(f"Invalid indices {self.indices!r}; expected tuple of integers")
        for idx in self.indices:
            if not isinstance(idx, int) or isinstance(idx, bool) or idx < 0:
                raise ValueError(f"Invalid index {idx!r}; expected non-negative integer")
        if not isinstance(self.differing_fields, tuple):
            raise TypeError(
                f"Invalid differing_fields {self.differing_fields!r}; expected tuple of strings"
            )
        for f in self.differing_fields:
            if not isinstance(f, str) or not f.strip():
                raise ValueError("differing_fields must contain non-empty strings")
        if self.source_code is not None and (
            not isinstance(self.source_code, str) or not self.source_code.strip()
        ):
            raise ValueError("source_code must be a non-empty string when provided")
