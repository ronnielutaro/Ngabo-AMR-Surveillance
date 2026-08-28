"""Status taxonomy for temporal and location concentration evaluations (Issue #46)."""

from __future__ import annotations

from enum import StrEnum


class ConcentrationStatus(StrEnum):
    """Outcome status for temporal or location concentration evaluations.

    Differentiates valid descriptive measurements from deterministic abstentions
    (e.g., empty facility denominator preventing ratio calculation).
    """

    SUCCESS = "SUCCESS"
    """Measurement successfully calculated over valid observations."""

    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    """Data was insufficient to perform the measurement."""


class ConcentrationReason(StrEnum):
    """Specific typed reason for an INSUFFICIENT_DATA concentration status.

    Note on canonical boundaries: Because CanonicalIsolate guarantees non-blank text
    for ward, facility_id, and organism_code, and a date-only collection_date,
    missing-field states are structurally impossible for canonical records. The primary
    material reason in Issue #46 is EMPTY_DENOMINATOR.
    """

    EMPTY_DENOMINATOR = "EMPTY_DENOMINATOR"
    """Zero isolates in facility window for the specified organism; ratio is undefined."""
