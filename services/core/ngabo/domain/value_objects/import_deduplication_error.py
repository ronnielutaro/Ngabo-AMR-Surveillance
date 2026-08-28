"""Framework-free value object for import deduplication errors (Issue #40)."""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.domain.enums.import_deduplication_error_code import ImportDeduplicationErrorCode


@dataclass(frozen=True)
class ImportDeduplicationError:
    """Structured failure detail when canonical import deduplication fails."""

    code: ImportDeduplicationErrorCode
    isolate_id: str | None
    indices: tuple[int, ...]
    differing_fields: tuple[str, ...] = ()
    detail: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, ImportDeduplicationErrorCode):
            raise TypeError(
                f"Invalid code {self.code!r}; expected ImportDeduplicationErrorCode"
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
        for field in self.differing_fields:
            if not isinstance(field, str) or not field.strip():
                raise ValueError(f"Invalid field name {field!r}; expected non-empty string")
