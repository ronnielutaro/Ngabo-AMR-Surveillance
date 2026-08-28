"""Inward application port for querying and recording canonical source watermarks (Issue #44)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ngabo.domain.value_objects.source_watermark import SourceWatermark


@runtime_checkable
class SourceReplayRepository(Protocol):
    """Inward application port for querying and recording canonical source watermarks."""

    def get_previous_watermark(self, source_key: str) -> SourceWatermark | None:
        """Retrieve the previous accepted SourceWatermark for a logical source.

        Args:
            source_key: The stable logical identifier for the source.

        Returns:
            The previous accepted ``SourceWatermark``, or ``None`` if this is a first import.
        """
        ...

    def record_accepted_watermark(
        self,
        source_key: str,
        watermark: SourceWatermark,
    ) -> None:
        """Record the accepted SourceWatermark for a logical source.

        Args:
            source_key: The stable logical identifier for the source.
            watermark: The accepted ``SourceWatermark``.
        """
        ...
