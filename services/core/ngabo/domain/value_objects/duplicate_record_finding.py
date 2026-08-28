"""Framework-free value object for exact duplicate record findings (Issue #40)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DuplicateRecordFinding:
    """Documented occurrence of an exact duplicate canonical record in an import."""

    isolate_id: str
    occurrences: int
    original_index: int
    duplicate_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.isolate_id, str) or not self.isolate_id.strip():
            raise ValueError(f"Invalid isolate_id {self.isolate_id!r}; expected non-empty string")
        if (
            not isinstance(self.occurrences, int)
            or isinstance(self.occurrences, bool)
            or self.occurrences < 2
        ):
            raise ValueError(f"Invalid occurrences {self.occurrences!r}; expected integer >= 2")
        if (
            not isinstance(self.original_index, int)
            or isinstance(self.original_index, bool)
            or self.original_index < 0
        ):
            raise ValueError(
                f"Invalid original_index {self.original_index!r}; expected non-negative integer"
            )
        if not isinstance(self.duplicate_indices, tuple):
            raise TypeError(
                f"Invalid duplicate_indices {self.duplicate_indices!r}; expected tuple of integers"
            )
        if not self.duplicate_indices:
            raise ValueError("duplicate_indices cannot be empty")
        for idx in self.duplicate_indices:
            if not isinstance(idx, int) or isinstance(idx, bool) or idx <= self.original_index:
                raise ValueError(
                    f"Invalid duplicate index {idx!r}; must be integer > original_index "
                    f"({self.original_index})"
                )
        if len(self.duplicate_indices) != self.occurrences - 1:
            raise ValueError(
                f"Count mismatch: occurrences={self.occurrences} but "
                f"{len(self.duplicate_indices)} duplicate indices provided"
            )
