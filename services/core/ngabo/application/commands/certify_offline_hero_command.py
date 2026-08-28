"""Command object for executing offline hero certification (Issue #48)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ngabo.domain.value_objects.signal_config import SignalConfig

DEFAULT_WINDOW_END = date(2026, 8, 18)
DEFAULT_SOURCE_KEY = "canonical-hero-source"


def _default_hero_csv_path() -> str:
    """Resolve default canonical hero CSV path relative to this source file."""
    # .../services/core/ngabo/application/commands/certify_offline_hero_command.py
    # parents[4] is repo root
    repo_root = Path(__file__).resolve().parents[5]
    hero_csv = repo_root / "data" / "synthetic" / "canonical_hero.csv"
    return str(hero_csv)


@dataclass(frozen=True)
class CertifyOfflineHeroCommand:
    """Command parameters for the offline hero certification release gate."""

    source_location: str | None = None
    source_key: str = DEFAULT_SOURCE_KEY
    window_end: date = DEFAULT_WINDOW_END
    signal_config: SignalConfig | None = None

    def resolved_location(self) -> str:
        """Return the explicit or default source location string."""
        if self.source_location is not None and self.source_location.strip():
            return self.source_location
        return _default_hero_csv_path()
