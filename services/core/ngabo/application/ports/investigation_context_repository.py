"""Inward port for canonical incident investigation context (Issue #50).

This is a framework-free application seam. Infrastructure implementations
resolve the port; the deterministic investigation capabilities depend only on
this contract. It returns an immutable ``StoredIncidentContext`` for a given
incident, or ``None`` when the incident does not exist (the canonical-not-found
signal; the capability translates that to a stable ``INCIDENT_NOT_FOUND``
outcome).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ngabo.application.value_objects.investigation_context import (
    StoredIncidentContext,
)
from ngabo.domain.value_objects.incident_id import IncidentId


@runtime_checkable
class InvestigationContextRepository(Protocol):
    """Fetch the immutable canonical context for one incident."""

    def get(self, incident_id: IncidentId) -> StoredIncidentContext | None:
        """Return the stored canonical context, or ``None`` if not found."""
        ...
