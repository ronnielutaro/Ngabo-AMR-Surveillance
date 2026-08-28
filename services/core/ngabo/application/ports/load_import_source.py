"""Inward application port for loading raw source artifact bytes (Issue #44)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LoadImportSource(Protocol):
    """Inward application port for retrieving raw artifact bytes from a source location."""

    def __call__(self, location: str) -> bytes:
        """Load raw artifact bytes from the given location or reference string.

        Args:
            location: A non-empty string specifying the source location or URI.

        Returns:
            The exact, immutable raw bytes of the source artifact.

        Raises:
            Exception: If the source cannot be accessed or read.
        """
        ...
