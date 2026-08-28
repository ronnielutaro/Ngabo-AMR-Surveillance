"""In-memory implementation of the SourceReplayRepository port (Issue #44, Issue #48).

Provides an in-memory, thread-safe repository suitable for offline execution,
local CLI commands, testing, and certification without external database dependencies.
"""

from __future__ import annotations

import threading
from collections.abc import Mapping

from ngabo.application.ports.source_replay_repository import SourceReplayRepository
from ngabo.domain.value_objects.source_watermark import SourceWatermark


class InMemorySourceReplayRepository(SourceReplayRepository):
    """Thread-safe in-memory repository implementing SourceReplayRepository."""

    def __init__(
        self, initial_watermarks: Mapping[str, SourceWatermark] | None = None
    ) -> None:
        self._watermarks: dict[str, SourceWatermark] = dict(initial_watermarks or {})
        self._lock = threading.Lock()
        self._accept_calls: list[tuple[str, SourceWatermark]] = []

    def accept_watermark(
        self, source_key: str, current: SourceWatermark
    ) -> SourceWatermark | None:
        """Atomically read previous watermark, record current, and return previous."""
        if not isinstance(source_key, str) or not source_key.strip():
            raise ValueError("source_key must be a non-empty string")
        if not isinstance(current, SourceWatermark):
            raise TypeError(
                f"current must be a SourceWatermark instance; got {type(current).__name__}"
            )

        with self._lock:
            self._accept_calls.append((source_key, current))
            previous = self._watermarks.get(source_key)
            self._watermarks[source_key] = current
            return previous

    def get_stored_watermark(self, source_key: str) -> SourceWatermark | None:
        """Retrieve the currently stored watermark for source_key without mutating."""
        with self._lock:
            return self._watermarks.get(source_key)

    @property
    def accept_calls(self) -> tuple[tuple[str, SourceWatermark], ...]:
        """Inspection property returning recorded accept calls."""
        with self._lock:
            return tuple(self._accept_calls)

    def clear(self) -> None:
        """Reset stored watermarks and call history."""
        with self._lock:
            self._watermarks.clear()
            self._accept_calls.clear()
