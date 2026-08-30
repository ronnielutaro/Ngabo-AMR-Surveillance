"""Canonical investigation-context capability (Issue #50).

Retrieves the immutable canonical context for an incident from the inward
repository port and returns a typed, versioned result. It fails closed on a
missing incident (``INCIDENT_NOT_FOUND``) and on a requested version that does
not match the stored version (``STALE_INCIDENT_VERSION``). It never invents
incident truth, never synthesizes narrative interpretation, and never calls a
model.
"""

from __future__ import annotations

from ngabo.application.enums.capability_outcome import CapabilityOutcome
from ngabo.application.ports.investigation_context_repository import (
    InvestigationContextRepository,
)
from ngabo.application.value_objects.investigation_context import (
    GetInvestigationContextQuery,
    InvestigationContextResult,
)


class GetInvestigationContext:
    """Framework-free canonical-context application capability."""

    def __init__(self, repository: InvestigationContextRepository) -> None:
        if not hasattr(repository, "get"):
            raise TypeError("repository must satisfy InvestigationContextRepository")
        self._repository = repository

    def execute(self, query: GetInvestigationContextQuery) -> InvestigationContextResult:
        """Return the typed versioned canonical context for ``query``."""
        if not isinstance(query, GetInvestigationContextQuery):
            raise TypeError(
                f"query must be a GetInvestigationContextQuery; got {type(query).__name__}"
            )

        stored = self._repository.get(query.incident_id)
        if stored is None:
            return InvestigationContextResult(
                outcome=CapabilityOutcome.INCIDENT_NOT_FOUND,
                incident_id=None,
                incident_version=None,
                source_watermark=None,
                isolates=(),
                signal_config=None,
                window_end=None,
                requested_version=query.requested_version,
            )

        if (
            query.requested_version is not None
            and query.requested_version != stored.incident_version
        ):
            return InvestigationContextResult(
                outcome=CapabilityOutcome.STALE_INCIDENT_VERSION,
                incident_id=stored.incident_id,
                incident_version=stored.incident_version,
                source_watermark=stored.source_watermark,
                # Fail closed: never expose stale-context data for consumption.
                isolates=(),
                signal_config=None,
                window_end=None,
                requested_version=query.requested_version,
            )

        return InvestigationContextResult(
            outcome=CapabilityOutcome.SUCCESS,
            incident_id=stored.incident_id,
            incident_version=stored.incident_version,
            source_watermark=stored.source_watermark,
            isolates=stored.isolates,
            signal_config=stored.signal_config,
            window_end=stored.window_end,
            requested_version=query.requested_version,
        )

    def __call__(self, query: GetInvestigationContextQuery) -> InvestigationContextResult:
        """Callable protocol support."""
        return self.execute(query)
