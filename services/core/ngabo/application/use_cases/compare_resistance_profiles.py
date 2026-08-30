"""Resistance-profile comparison investigation capability (Issue #50).

Coordinates the existing deterministic resistance-profile-similarity domain
service and returns a typed, versioned result with a stable
``DeterministicFindingReference``. It does NOT recompute the scientific
similarity; the ``compare`` seam is defaulted to the existing domain owner so
handlers never duplicate scientific logic. The isolate pair is canonicalized
by identity before comparison so semantically unordered inputs
``(A, B)`` and ``(B, A)`` yield the identical finding.
"""

from __future__ import annotations

from collections.abc import Callable

from ngabo.application.enums.capability_outcome import CapabilityOutcome
from ngabo.application.ports.investigation_context_repository import (
    InvestigationContextRepository,
)
from ngabo.application.value_objects.profile_comparison import (
    CompareProfilesQuery,
    ProfileComparisonResult,
)
from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.services.resistance_profile_similarity import (
    compare_canonical_isolates,
)
from ngabo.domain.value_objects.profile_similarity_finding import (
    ProfileSimilarityFinding,
)


class CompareResistanceProfiles:
    """Framework-free profile-comparison application capability."""

    def __init__(
        self,
        repository: InvestigationContextRepository,
        *,
        compare: Callable[
            [CanonicalIsolate, CanonicalIsolate], ProfileSimilarityFinding
        ] = compare_canonical_isolates,
    ) -> None:
        if not hasattr(repository, "get"):
            raise TypeError("repository must satisfy InvestigationContextRepository")
        if not callable(compare):
            raise TypeError("compare must be callable")
        self._repository = repository
        self._compare = compare

    def execute(self, query: CompareProfilesQuery) -> ProfileComparisonResult:
        """Return the typed versioned profile-comparison result."""
        if not isinstance(query, CompareProfilesQuery):
            raise TypeError(
                f"query must be a CompareProfilesQuery; got {type(query).__name__}"
            )

        stored = self._repository.get(query.incident_id)
        if stored is None:
            return ProfileComparisonResult(
                outcome=CapabilityOutcome.INCIDENT_NOT_FOUND,
                incident_id=None,
                incident_version=None,
                source_watermark=None,
                finding=None,
                finding_reference=None,
                isolate_id_a=query.isolate_id_a,
                isolate_id_b=query.isolate_id_b,
            )

        if (
            query.requested_version is not None
            and query.requested_version != stored.incident_version
        ):
            return ProfileComparisonResult(
                outcome=CapabilityOutcome.STALE_INCIDENT_VERSION,
                incident_id=stored.incident_id,
                incident_version=stored.incident_version,
                source_watermark=stored.source_watermark,
                finding=None,
                finding_reference=None,
                isolate_id_a=query.isolate_id_a,
                isolate_id_b=query.isolate_id_b,
            )

        by_id = {iso.isolate_id: iso for iso in stored.isolates}
        isolate_a = by_id.get(query.isolate_id_a)
        isolate_b = by_id.get(query.isolate_id_b)
        if isolate_a is None or isolate_b is None:
            return ProfileComparisonResult(
                outcome=CapabilityOutcome.MISSING_INPUT,
                incident_id=stored.incident_id,
                incident_version=stored.incident_version,
                source_watermark=stored.source_watermark,
                finding=None,
                finding_reference=None,
                isolate_id_a=query.isolate_id_a,
                isolate_id_b=query.isolate_id_b,
            )

        # Canonicalize the symmetric pair so (A, B) and (B, A) are identical.
        first, second = sorted((isolate_a, isolate_b), key=lambda iso: iso.isolate_id)
        finding = self._compare(first, second)
        if not isinstance(finding, ProfileSimilarityFinding):
            raise TypeError("compare must return a ProfileSimilarityFinding")

        return ProfileComparisonResult(
            outcome=CapabilityOutcome.SUCCESS,
            incident_id=stored.incident_id,
            incident_version=stored.incident_version,
            source_watermark=stored.source_watermark,
            finding=finding,
            finding_reference=finding.to_finding_reference(),
            isolate_id_a=finding.isolate_id_a,
            isolate_id_b=finding.isolate_id_b,
        )

    def __call__(self, query: CompareProfilesQuery) -> ProfileComparisonResult:
        """Callable protocol support."""
        return self.execute(query)
