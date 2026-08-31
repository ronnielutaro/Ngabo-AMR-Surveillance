"""Concrete Connect ingestion adapter (HMAC auth + Firestore persistence).

This lives in the infrastructure layer so the ``interfaces`` HTTP adapter never
imports a GCP/cloud SDK or a concrete repository directly (Clean Architecture:
interfaces -> application ports, never infrastructure). The bootstrap composes
a ``ConnectIngestionService`` and injects it via ``configure_connect_ingestion``
before the service serves requests.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Any

from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.infrastructure.connect.firestore_incident_repository import (
    FirestoreInvestigationContextRepository,
    load_latest_batch,
    persist_batch_events,
)
from ngabo.infrastructure.connect.hmac_auth import verify_upload


class ConnectIngestionService:
    """Real connect ingest wiring: authenticated upload + Firestore persistence."""

    def __init__(
        self,
        *,
        project: str,
        secret: str,
        client: Any = None,
        database: str = "ngabo",
    ) -> None:
        self._project = project
        self._secret = secret.encode("utf-8")
        self._client = client
        self._database = database
        self._repo: FirestoreInvestigationContextRepository | None = None

    def _get_repo(self) -> FirestoreInvestigationContextRepository:
        if self._repo is None:
            self._repo = FirestoreInvestigationContextRepository(
                project=self._project,
                client=self._client,
                database=self._database,
            )
        return self._repo

    def verify_upload(
        self,
        *,
        headers: Mapping[str, str],
        body: bytes,
        configured_lab_ids: set[str],
        configured_source_ids: set[str],
    ) -> tuple[bool, str | None]:
        return verify_upload(
            headers=headers,
            body=body,
            secret=self._secret,
            configured_lab_ids=configured_lab_ids,
            configured_source_ids=configured_source_ids,
        )

    def persist_isolates(
        self,
        *,
        incident_id: str,
        isolates: list[CanonicalIsolate],
        lab_id: str,
        source_id: str,
        window_end: date,
        profile_pair: tuple[str, str] | None = None,
    ) -> None:
        if not self._project:
            return
        self._get_repo().persist_incident(
            incident_id=incident_id,
            incident_version=1,
            source_watermark=f"connect/{lab_id}/{source_id}/v1",
            window_end=window_end,
            isolates=isolates,
            profile_pair=profile_pair,
        )

    def persist_batch_events(self, *, batch_id: str, payload: dict[str, object]) -> None:
        if not self._project:
            return
        persist_batch_events(
            project=self._project,
            batch_id=batch_id,
            payload=payload,
            client=self._client,
            database=self._database,
        )

    def load_latest_batch(self) -> dict[str, object] | None:
        """Read the canonical latest status for cross-instance web polling."""
        if not self._project:
            return None
        return load_latest_batch(
            project=self._project,
            client=self._client,
            database=self._database,
        )
