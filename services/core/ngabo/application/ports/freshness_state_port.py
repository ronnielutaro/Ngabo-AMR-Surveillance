"""Inward application port for authoritative current-state reload (#176)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ngabo.application.value_objects.canonical_binding import HeroStateBinding
from ngabo.domain.value_objects.incident_id import IncidentId


@runtime_checkable
class FreshnessStatePort(Protocol):
    """Reload authoritative current binding immediately before authorization."""

    def current_binding(self, incident_id: IncidentId) -> HeroStateBinding:
        """Return the CURRENT canonical binding for ``incident_id``.

        This must be freshly loaded from authoritative application state, not
        reused from an earlier in-memory snapshot. The model never supplies it.
        """
        ...
