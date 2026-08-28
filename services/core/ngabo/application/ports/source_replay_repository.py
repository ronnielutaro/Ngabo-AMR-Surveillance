"""Inward application port for atomic source watermark replay acceptance (Issue #44)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ngabo.domain.value_objects.source_watermark import SourceWatermark


@runtime_checkable
class SourceReplayRepository(Protocol):
    """Inward application port for atomically querying and advancing source watermark state.

    Concurrent / Redelivery Invariant:
    All implementations must guarantee atomic all-or-nothing execution:
    under concurrent or redelivered events for the same source_key, the
    repository atomically reads the previously accepted watermark, records
    the newly accepted watermark, and returns the previous watermark.
    A caller receiving None was the FIRST_IMPORT; a caller receiving the same
    watermark is an EXACT_REPLAY without duplicate work.
    """

    def accept_watermark(
        self,
        source_key: str,
        current: SourceWatermark,
    ) -> SourceWatermark | None:
        """Atomically record current watermark and return previously accepted watermark.

        Args:
            source_key: The stable logical identifier for the ingestion source.
            current: The deterministically computed SourceWatermark to record as accepted.

        Returns:
            The previously accepted SourceWatermark for source_key, or None if this
            is the first accepted import for the source.

        Raises:
            Exception: If the underlying atomic read-and-record operation fails.
        """
        ...
