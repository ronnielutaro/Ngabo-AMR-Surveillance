"""Baseline-summary investigation capability contracts (Issue #50).

``GetBaselineSummaryQuery`` requests the existing deterministic baseline/signal
evaluation for one cohort (organism/facility/ward) within an incident.
``BaselineSummaryResult`` carries the typed ``SignalEvaluationResult`` produced
by the existing deterministic signal-detection owner (which includes the
synthetic baseline-excess component), and is bound to the incident identity,
version, and source watermark. It is never an LLM-generated summary — "summary"
here means a typed deterministic application result.
"""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.application.enums.capability_outcome import CapabilityOutcome
from ngabo.domain.services.signal_detection import SignalEvaluationResult
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.source_watermark import SourceWatermark


def _require_opaque_id(value: object, label: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected a non-blank opaque ID")


@dataclass(frozen=True)
class GetBaselineSummaryQuery:
    """Request the deterministic baseline evaluation for one cohort."""

    incident_id: IncidentId
    organism_code: str
    facility_id: str
    ward: str
    requested_version: IncidentVersion | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.incident_id, IncidentId):
            raise ValueError("incident_id must be an IncidentId")
        _require_opaque_id(self.organism_code, "organism_code")
        _require_opaque_id(self.facility_id, "facility_id")
        _require_opaque_id(self.ward, "ward")
        if self.requested_version is not None and not isinstance(
            self.requested_version, IncidentVersion
        ):
            raise ValueError("requested_version must be an IncidentVersion or None")


@dataclass(frozen=True)
class BaselineSummaryResult:
    """Typed versioned result of the baseline-summary capability."""

    outcome: CapabilityOutcome
    incident_id: IncidentId | None
    incident_version: IncidentVersion | None
    source_watermark: SourceWatermark | None
    signal_evaluation: SignalEvaluationResult | None
    organism_code: str | None = None
    facility_id: str | None = None
    ward: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, CapabilityOutcome):
            raise ValueError("outcome must be a CapabilityOutcome")
        if self.incident_id is not None and not isinstance(self.incident_id, IncidentId):
            raise ValueError("incident_id must be an IncidentId or None")
        if self.incident_version is not None and not isinstance(
            self.incident_version, IncidentVersion
        ):
            raise ValueError("incident_version must be an IncidentVersion or None")
        if self.source_watermark is not None and not isinstance(
            self.source_watermark, SourceWatermark
        ):
            raise ValueError("source_watermark must be a SourceWatermark or None")
        if self.signal_evaluation is not None and not isinstance(
            self.signal_evaluation, SignalEvaluationResult
        ):
            raise ValueError("signal_evaluation must be a SignalEvaluationResult or None")
