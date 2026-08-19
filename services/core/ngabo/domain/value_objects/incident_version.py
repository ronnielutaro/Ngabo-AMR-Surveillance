"""Framework-free value object for Ngabo incident versions.

An incident version is a strictly positive integer that advances when the
canonical incident state materially changes (ADR 0006). Versions are
compared by value for freshness and stale-action protection; this value
object carries no mutation or persistence behavior.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IncidentVersion:
    """Immutable version of a Ngabo incident."""

    value: int

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, int) or self.value < 1:
            raise ValueError(f"Invalid incident version {self.value!r}; expected int >= 1")

    def __str__(self) -> str:
        return str(self.value)
