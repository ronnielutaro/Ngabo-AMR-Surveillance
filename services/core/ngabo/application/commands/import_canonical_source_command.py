"""Immutable command to trigger canonical source import (Issue #44)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImportCanonicalSourceCommand:
    """Command requesting canonical import of a single raw source artifact."""

    source_key: str
    source_location: str

    def __post_init__(self) -> None:
        if not isinstance(self.source_key, str) or not self.source_key.strip():
            raise ValueError("source_key must be a non-empty string")
        if not isinstance(self.source_location, str) or not self.source_location.strip():
            raise ValueError("source_location must be a non-empty string")
