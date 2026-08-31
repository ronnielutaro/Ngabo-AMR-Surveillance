"""Firestore-backed FreshnessStatePort (#176 read against canonical state)."""

from __future__ import annotations

from ngabo.application.value_objects.canonical_binding import HeroStateBinding
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.signal_config import SignalConfig
from ngabo.infrastructure.connect.firestore_incident_repository import (
    FirestoreInvestigationContextRepository,
)


class FirestoreFreshnessStatePort:
    """Reload authoritative current binding immediately before authorization."""

    def __init__(self, repository: FirestoreInvestigationContextRepository) -> None:
        self._repo = repository

    def current_binding(self, incident_id: IncidentId) -> HeroStateBinding:
        context = self._repo.get(incident_id)
        if context is None:
            raise RuntimeError(f"no canonical incident for {incident_id.value}")
        return HeroStateBinding(
            incident_id=context.incident_id,
            incident_version=context.incident_version,
            source_watermark=context.source_watermark,
            policy_config_version=SignalConfig().policy_version,
        )
