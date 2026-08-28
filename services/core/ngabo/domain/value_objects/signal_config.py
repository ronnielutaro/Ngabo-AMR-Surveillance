"""Governed configuration for investigation-priority signal detection (Issue #47)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta

GOVERNED_SIGNAL_POLICY_VERSION = "ngabo-signal-v1"
GOVERNED_SIGNAL_CONFIG_VERSION = "signal-win7d-org-facility-ward-v1"
GOVERNED_SIGNAL_ALGORITHM_VERSION = "composite-priority-v1"
GOVERNED_SIGNAL_WINDOW_DAYS = 7
GOVERNED_SIGNAL_PRECISION = 4
GOVERNED_MIN_CANDIDATE_COUNT = 3
GOVERNED_TRIGGER_THRESHOLD = 0.7500
GOVERNED_SYNTHETIC_BASELINE_COUNT = 1.0
GOVERNED_W_PHENOTYPE = 0.35
GOVERNED_W_LOCATION = 0.25
GOVERNED_W_TEMPORAL = 0.20
GOVERNED_W_BASELINE = 0.20
GOVERNED_BASELINE_SATURATION_MULTIPLIER = 3.0


@dataclass(frozen=True)
class SignalConfig:
    """Immutable, version-governed configuration for investigation-priority signal scoring.

    Enforces the closed v0.1 policy established by ADR 0012. Runtime configuration
    spoofing or mutation of weights, thresholds, window size, or baseline parameters
    is strictly rejected.
    """

    policy_version: str = GOVERNED_SIGNAL_POLICY_VERSION
    config_version: str = GOVERNED_SIGNAL_CONFIG_VERSION
    algorithm_version: str = GOVERNED_SIGNAL_ALGORITHM_VERSION
    window_days: int = GOVERNED_SIGNAL_WINDOW_DAYS
    precision: int = GOVERNED_SIGNAL_PRECISION
    min_candidate_count: int = GOVERNED_MIN_CANDIDATE_COUNT
    trigger_threshold: float = GOVERNED_TRIGGER_THRESHOLD
    configured_synthetic_baseline_count: float = GOVERNED_SYNTHETIC_BASELINE_COUNT
    w_phenotype: float = GOVERNED_W_PHENOTYPE
    w_location: float = GOVERNED_W_LOCATION
    w_temporal: float = GOVERNED_W_TEMPORAL
    w_baseline: float = GOVERNED_W_BASELINE
    baseline_saturation_multiplier: float = GOVERNED_BASELINE_SATURATION_MULTIPLIER

    def __post_init__(self) -> None:
        for name, val in (
            ("trigger_threshold", self.trigger_threshold),
            ("configured_synthetic_baseline_count", self.configured_synthetic_baseline_count),
            ("w_phenotype", self.w_phenotype),
            ("w_location", self.w_location),
            ("w_temporal", self.w_temporal),
            ("w_baseline", self.w_baseline),
            ("baseline_saturation_multiplier", self.baseline_saturation_multiplier),
        ):
            if not isinstance(val, float) or isinstance(val, bool) or not math.isfinite(val):
                raise ValueError(f"{name} must be a finite float; got {val!r}")

        if not (0.0 <= self.trigger_threshold <= 1.0):
            raise ValueError(
                f"trigger_threshold must be within [0.0, 1.0]; got {self.trigger_threshold}"
            )

        if self.policy_version != GOVERNED_SIGNAL_POLICY_VERSION:
            raise ValueError(
                f"Unsupported policy_version {self.policy_version!r}; "
                f"closed v0.1 policy requires {GOVERNED_SIGNAL_POLICY_VERSION!r}"
            )
        if self.config_version != GOVERNED_SIGNAL_CONFIG_VERSION:
            raise ValueError(
                f"Unsupported config_version {self.config_version!r}; "
                f"closed v0.1 policy requires {GOVERNED_SIGNAL_CONFIG_VERSION!r}"
            )
        if self.algorithm_version != GOVERNED_SIGNAL_ALGORITHM_VERSION:
            raise ValueError(
                f"Unsupported algorithm_version {self.algorithm_version!r}; "
                f"closed v0.1 policy requires {GOVERNED_SIGNAL_ALGORITHM_VERSION!r}"
            )
        if (
            not isinstance(self.window_days, int)
            or isinstance(self.window_days, bool)
            or self.window_days != GOVERNED_SIGNAL_WINDOW_DAYS
        ):
            raise ValueError(
                f"Unsupported window_days {self.window_days!r}; "
                f"closed v0.1 policy requires exactly {GOVERNED_SIGNAL_WINDOW_DAYS}"
            )
        if (
            not isinstance(self.precision, int)
            or isinstance(self.precision, bool)
            or self.precision != GOVERNED_SIGNAL_PRECISION
        ):
            raise ValueError(
                f"Unsupported precision {self.precision!r}; "
                f"closed v0.1 policy requires exactly {GOVERNED_SIGNAL_PRECISION}"
            )
        if (
            not isinstance(self.min_candidate_count, int)
            or isinstance(self.min_candidate_count, bool)
            or self.min_candidate_count != GOVERNED_MIN_CANDIDATE_COUNT
        ):
            raise ValueError(
                f"Unsupported min_candidate_count {self.min_candidate_count!r}; "
                f"closed v0.1 policy requires exactly {GOVERNED_MIN_CANDIDATE_COUNT}"
            )
        if (
            not isinstance(self.trigger_threshold, float)
            or isinstance(self.trigger_threshold, bool)
            or self.trigger_threshold != GOVERNED_TRIGGER_THRESHOLD
        ):
            raise ValueError(
                f"Unsupported trigger_threshold {self.trigger_threshold!r}; "
                f"closed v0.1 policy requires exactly {GOVERNED_TRIGGER_THRESHOLD}"
            )
        if (
            not isinstance(self.configured_synthetic_baseline_count, float)
            or isinstance(self.configured_synthetic_baseline_count, bool)
            or self.configured_synthetic_baseline_count <= 0.0
            or self.configured_synthetic_baseline_count != GOVERNED_SYNTHETIC_BASELINE_COUNT
        ):
            raise ValueError(
                f"Unsupported configured_synthetic_baseline_count "
                f"{self.configured_synthetic_baseline_count!r}; "
                f"closed v0.1 policy requires a positive float exactly "
                f"{GOVERNED_SYNTHETIC_BASELINE_COUNT}"
            )
        if (
            not isinstance(self.w_phenotype, float)
            or isinstance(self.w_phenotype, bool)
            or self.w_phenotype != GOVERNED_W_PHENOTYPE
        ):
            raise ValueError(f"Unsupported w_phenotype; must be {GOVERNED_W_PHENOTYPE}")
        if (
            not isinstance(self.w_location, float)
            or isinstance(self.w_location, bool)
            or self.w_location != GOVERNED_W_LOCATION
        ):
            raise ValueError(f"Unsupported w_location; must be {GOVERNED_W_LOCATION}")
        if (
            not isinstance(self.w_temporal, float)
            or isinstance(self.w_temporal, bool)
            or self.w_temporal != GOVERNED_W_TEMPORAL
        ):
            raise ValueError(f"Unsupported w_temporal; must be {GOVERNED_W_TEMPORAL}")
        if (
            not isinstance(self.w_baseline, float)
            or isinstance(self.w_baseline, bool)
            or self.w_baseline != GOVERNED_W_BASELINE
        ):
            raise ValueError(f"Unsupported w_baseline; must be {GOVERNED_W_BASELINE}")
        if (
            not isinstance(self.baseline_saturation_multiplier, float)
            or isinstance(self.baseline_saturation_multiplier, bool)
            or self.baseline_saturation_multiplier != GOVERNED_BASELINE_SATURATION_MULTIPLIER
        ):
            raise ValueError(
                f"Unsupported baseline_saturation_multiplier; "
                f"must be {GOVERNED_BASELINE_SATURATION_MULTIPLIER}"
            )

        weight_sum = round(
            self.w_phenotype + self.w_location + self.w_temporal + self.w_baseline, 4
        )
        if weight_sum != 1.0:
            raise ValueError(f"Component weights must sum exactly to 1.0000; got {weight_sum}")

    def calculate_window_start(self, window_end: date) -> date:
        """Calculate inclusive window_start from explicit date-only window_end."""
        if type(window_end) is not date:
            raise TypeError(
                f"window_end must be an exact datetime.date; got {type(window_end).__name__}"
            )
        return window_end - timedelta(days=self.window_days - 1)
