"""Signal detection status and reason taxonomy (Issue #47 / ADR 0012)."""

from __future__ import annotations

from enum import StrEnum


class SignalStatus(StrEnum):
    """Execution status for investigation-priority signal candidate evaluation."""

    TRIGGERED = "TRIGGERED"
    NO_SIGNAL = "NO_SIGNAL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class SignalReason(StrEnum):
    """Deterministic reason taxonomy explaining signal evaluation outcomes."""

    HIGH_PRIORITY_CLUSTER = "HIGH_PRIORITY_CLUSTER"
    BELOW_PRIORITY_THRESHOLD = "BELOW_PRIORITY_THRESHOLD"
    INSUFFICIENT_CLUSTER_SIZE = "INSUFFICIENT_CLUSTER_SIZE"
    INSUFFICIENT_PHENOTYPE_EVIDENCE = "INSUFFICIENT_PHENOTYPE_EVIDENCE"
    INVALID_BASELINE_CONFIGURATION = "INVALID_BASELINE_CONFIGURATION"
