"""Stable outcomes for deterministic investigation capabilities (Issue #50).

Expected workflow states are typed, not arbitrary exceptions. A capability
reports one of these values so future orchestration can distinguish an
optional absence (e.g. insufficient data) from a mandatory branch that failed.
Unexpected programmer/infrastructure failures may still raise per existing
policy; this vocabulary is for the deterministic, expected states.
"""

from __future__ import annotations

from enum import StrEnum


class CapabilityOutcome(StrEnum):
    """Stable outcome of a deterministic investigation capability."""

    SUCCESS = "SUCCESS"
    INCIDENT_NOT_FOUND = "INCIDENT_NOT_FOUND"
    STALE_INCIDENT_VERSION = "STALE_INCIDENT_VERSION"
    MISSING_INPUT = "MISSING_INPUT"
    REQUIRED_CAPABILITY_FAILED = "REQUIRED_CAPABILITY_FAILED"
