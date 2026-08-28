"""Governed configuration for temporal and location concentration evaluation (Issue #46)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

GOVERNED_POLICY_VERSION = "ngabo-concentration-v1"
GOVERNED_CONFIG_VERSION = "win7d-org-facility-ward-v1"
GOVERNED_TEMPORAL_ALGORITHM_VERSION = "retrospective-count-v1"
GOVERNED_LOCATION_ALGORITHM_VERSION = "ward-share-v1"
GOVERNED_WINDOW_DAYS = 7
GOVERNED_PRECISION = 4


@dataclass(frozen=True)
class ConcentrationConfig:
    """Immutable, version-governed configuration for temporal and location concentration.

    Enforces the closed v0.1 policy established by ADR 0011. Runtime configuration
    spoofing or mutation of window size, algorithms, or precision is strictly rejected.
    """

    policy_version: str = GOVERNED_POLICY_VERSION
    config_version: str = GOVERNED_CONFIG_VERSION
    temporal_algorithm_version: str = GOVERNED_TEMPORAL_ALGORITHM_VERSION
    location_algorithm_version: str = GOVERNED_LOCATION_ALGORITHM_VERSION
    window_days: int = GOVERNED_WINDOW_DAYS
    precision: int = GOVERNED_PRECISION

    def __post_init__(self) -> None:
        if self.policy_version != GOVERNED_POLICY_VERSION:
            raise ValueError(
                f"Unsupported policy_version {self.policy_version!r}; "
                f"closed v0.1 policy requires {GOVERNED_POLICY_VERSION!r}"
            )
        if self.config_version != GOVERNED_CONFIG_VERSION:
            raise ValueError(
                f"Unsupported config_version {self.config_version!r}; "
                f"closed v0.1 policy requires {GOVERNED_CONFIG_VERSION!r}"
            )
        if self.temporal_algorithm_version != GOVERNED_TEMPORAL_ALGORITHM_VERSION:
            raise ValueError(
                f"Unsupported temporal_algorithm_version {self.temporal_algorithm_version!r}; "
                f"closed v0.1 policy requires {GOVERNED_TEMPORAL_ALGORITHM_VERSION!r}"
            )
        if self.location_algorithm_version != GOVERNED_LOCATION_ALGORITHM_VERSION:
            raise ValueError(
                f"Unsupported location_algorithm_version {self.location_algorithm_version!r}; "
                f"closed v0.1 policy requires {GOVERNED_LOCATION_ALGORITHM_VERSION!r}"
            )
        if (
            not isinstance(self.window_days, int)
            or isinstance(self.window_days, bool)
            or self.window_days != GOVERNED_WINDOW_DAYS
        ):
            raise ValueError(
                f"Unsupported window_days {self.window_days!r}; "
                f"closed v0.1 policy requires exactly {GOVERNED_WINDOW_DAYS}"
            )
        if (
            not isinstance(self.precision, int)
            or isinstance(self.precision, bool)
            or self.precision != GOVERNED_PRECISION
        ):
            raise ValueError(
                f"Unsupported precision {self.precision!r}; "
                f"closed v0.1 policy requires exactly {GOVERNED_PRECISION}"
            )

    def calculate_window_start(self, window_end: date) -> date:
        """Calculate inclusive window_start from explicit date-only window_end."""
        if type(window_end) is not date:
            raise TypeError(
                f"window_end must be an exact datetime.date; got {type(window_end).__name__}"
            )
        return window_end - timedelta(days=self.window_days - 1)

    def is_in_window(self, collection_date: date, window_end: date) -> bool:
        """Evaluate if date-only collection_date falls within [window_start, window_end]."""
        if type(collection_date) is not date:
            raise TypeError(
                f"collection_date must be an exact datetime.date; "
                f"got {type(collection_date).__name__}"
            )
        start = self.calculate_window_start(window_end)
        return start <= collection_date <= window_end
