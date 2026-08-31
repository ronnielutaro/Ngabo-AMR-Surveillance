"""Deterministic test-only ``FreshnessStatePort`` (#176).

Returns a configured binding so tests can advance canonical state between
verification and the pre-action freshness reload (V1 -> V2 -> BLOCKED).
"""

from __future__ import annotations

from ngabo.application.value_objects.canonical_binding import HeroStateBinding
from ngabo.domain.value_objects.incident_id import IncidentId


class FakeFreshnessStatePort:
    """Test freshness port that returns a controllable authoritative binding."""

    def __init__(self, binding: HeroStateBinding) -> None:
        self._binding = binding
        self.calls: list[IncidentId] = []

    def current_binding(self, incident_id: IncidentId) -> HeroStateBinding:
        self.calls.append(incident_id)
        return self._binding
