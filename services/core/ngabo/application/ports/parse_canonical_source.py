"""Inward application port for parsing raw source text into canonical import batches (Issue #44)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ngabo.domain.entities.canonical_import_batch import CanonicalImportBatch


@runtime_checkable
class ParsedSourceError(Protocol):
    """Protocol for structured parser errors consumed by the application layer."""

    @property
    def detail(self) -> str | None: ...

    @property
    def column(self) -> str | None: ...

    @property
    def row_number(self) -> int | None: ...

    @property
    def record_index(self) -> int | None: ...

    @property
    def record_id(self) -> str | None: ...

    @property
    def code(self) -> object: ...


@runtime_checkable
class ParsedSourceResult(Protocol):
    """Protocol for parser output consumed by the application layer."""

    @property
    def success(self) -> bool: ...

    @property
    def batch(self) -> CanonicalImportBatch | None: ...

    @property
    def errors(self) -> Sequence[ParsedSourceError]: ...


@runtime_checkable
class ParseCanonicalSource(Protocol):
    """Inward application port for parsing raw CSV text into a canonical import batch."""

    def __call__(self, source: str, /) -> ParsedSourceResult:
        """Parse source CSV text into a canonical import batch or structured errors.

        Args:
            source: Validated UTF-8 source CSV text string.

        Returns:
            A ``ParsedSourceResult`` exposing batch or errors.
        """
        ...
