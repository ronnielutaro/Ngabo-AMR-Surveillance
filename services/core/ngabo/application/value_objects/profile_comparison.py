"""Profile-comparison investigation capability contracts (Issue #50).

``CompareProfilesQuery`` requests the existing deterministic resistance
profile similarity between two canonical isolates within an incident.
``ProfileComparisonResult`` returns the typed deterministic ``ProfileSimilarity
Finding`` plus its stable ``DeterministicFindingReference``, bound to the
incident identity/version and the source watermark that produced it. The
handler never recomputes the scientific similarity; it delegates to the
existing deterministic domain owner.
"""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.application.enums.capability_outcome import CapabilityOutcome
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.profile_similarity_finding import (
    ProfileSimilarityFinding,
)
from ngabo.domain.value_objects.proof_references import (
    DeterministicFindingReference,
    _require_opaque_id,
)
from ngabo.domain.value_objects.source_watermark import SourceWatermark


@dataclass(frozen=True)
class CompareProfilesQuery:
    """Request the deterministic similarity of two isolates in one incident."""

    incident_id: IncidentId
    isolate_id_a: str
    isolate_id_b: str
    requested_version: IncidentVersion | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.incident_id, IncidentId):
            raise ValueError("incident_id must be an IncidentId")
        _require_opaque_id(self.isolate_id_a, "isolate_id_a")
        _require_opaque_id(self.isolate_id_b, "isolate_id_b")
        if self.requested_version is not None and not isinstance(
            self.requested_version, IncidentVersion
        ):
            raise ValueError("requested_version must be an IncidentVersion or None")


@dataclass(frozen=True)
class ProfileComparisonResult:
    """Typed versioned result of the profile-comparison capability."""

    outcome: CapabilityOutcome
    incident_id: IncidentId | None
    incident_version: IncidentVersion | None
    source_watermark: SourceWatermark | None
    finding: ProfileSimilarityFinding | None
    finding_reference: DeterministicFindingReference | None
    isolate_id_a: str | None = None
    isolate_id_b: str | None = None

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
        if self.finding is not None and not isinstance(self.finding, ProfileSimilarityFinding):
            raise ValueError("finding must be a ProfileSimilarityFinding or None")
        if self.finding_reference is not None and not isinstance(
            self.finding_reference, DeterministicFindingReference
        ):
            raise ValueError("finding_reference must be a DeterministicFindingReference or None")
        if self.isolate_id_a is not None:
            _require_opaque_id(self.isolate_id_a, "isolate_id_a")
        if self.isolate_id_b is not None:
            _require_opaque_id(self.isolate_id_b, "isolate_id_b")
