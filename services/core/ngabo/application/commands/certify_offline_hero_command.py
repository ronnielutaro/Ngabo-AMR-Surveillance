"""Command object for executing offline hero certification (Issue #48)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ngabo.domain.value_objects.signal_config import SignalConfig

DEFAULT_WINDOW_END = date(2026, 8, 18)
DEFAULT_SOURCE_KEY = "canonical-hero-source"


@dataclass(frozen=True)
class CertifyOfflineHeroCommand:
    """Command parameters for the offline hero certification release gate."""

    source_location: str
    logical_source_id: str | None = None
    source_key: str = DEFAULT_SOURCE_KEY
    window_end: date = DEFAULT_WINDOW_END
    signal_config: SignalConfig | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_location, str) or not self.source_location.strip():
            raise ValueError("source_location must be a non-empty string")
        if self.logical_source_id is not None and (
            not isinstance(self.logical_source_id, str) or not self.logical_source_id.strip()
        ):
            raise ValueError("logical_source_id must be a non-empty string when specified")

    @property
    def resolved_logical_locator(self) -> str:
        """Return the stable logical locator or source_location."""
        return self.logical_source_id or self.source_location
