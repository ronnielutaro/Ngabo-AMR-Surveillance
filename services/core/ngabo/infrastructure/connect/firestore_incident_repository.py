"""Firestore-backed InvestigationContextRepository (#171/#179).

Reads a canonical incident (StoredIncidentContext) from Firestore so the existing
hero's #54 GetInvestigationContext / CompareResistanceProfiles /
GetBaselineSummary / AssessMaterialMissingness can run against production
canonical state. Also persists accepted Connect isolates + batch/event docs.
The Connect cleaning layer is the writer; the hero is the reader.
"""

from __future__ import annotations

from datetime import date
from types import MappingProxyType
from typing import Any

from ngabo.application.value_objects.investigation_context import StoredIncidentContext
from ngabo.domain.entities.ast_observation import AstObservation
from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.enums.interpretation import Interpretation
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.signal_config import SignalConfig
from ngabo.domain.value_objects.source_watermark import SourceWatermark


class FirestoreInvestigationContextRepository:
    """InvestigationContextRepository backed by Firestore documents."""

    def __init__(self, *, project: str, client: Any = None) -> None:
        _import_firestore()
        import google.cloud.firestore as fs

        self._db: Any = client if client is not None else fs.Client(project=project)
        self._incidents = self._db.collection("connect_incidents")

    def get(self, incident_id: IncidentId) -> StoredIncidentContext | None:
        doc = self._incidents.document(incident_id.value).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        isolates = self._read_isolates(incident_id.value)
        return _stored_from_dict(data, isolates)

    def persist_incident(
        self,
        *,
        incident_id: str,
        incident_version: int,
        source_watermark: str,
        window_end: date,
        isolates: list[CanonicalIsolate],
        profile_pair: tuple[str, str] | None = None,
    ) -> None:
        incident_doc = self._incidents.document(incident_id)
        incident_doc.set(
            {
                "incident_id": incident_id,
                "incident_version": incident_version,
                "source_watermark": source_watermark,
                "window_end": window_end.isoformat(),
                "profile_comparison_isolate_ids": list(profile_pair) if profile_pair else None,
            }
        )
        isolates_col = incident_doc.collection("isolates")
        for isolate in isolates:
            isolates_col.document(isolate.isolate_id).set(_isolate_to_dict(isolate))

    def _read_isolates(self, incident_id: str) -> tuple[CanonicalIsolate, ...]:
        batch = self._incidents.document(incident_id).collection("isolates").stream()
        return tuple(
            _isolate_from_dict(doc.to_dict()) for doc in batch if doc.to_dict()
        )


def persist_batch_events(
    *,
    project: str,
    batch_id: str,
    payload: dict[str, object],
) -> None:
    """Persist one ConnectBatch + its workflow events under connect_batches."""
    _import_firestore()
    import google.cloud.firestore as fs

    db = fs.Client(project=project)
    doc = db.collection("connect_batches").document(batch_id)
    doc.set(payload)
    events = payload.get("events")
    if isinstance(events, list):
        events_col = doc.collection("events")
        for index, event in enumerate(events):
            if isinstance(event, dict):
                events_col.document(f"evt-{index}").set(event)


def _import_firestore() -> None:
    try:
        import google.cloud.firestore  # noqa: F401
    except Exception as exc:  # pragma: no cover - deploy dependency
        raise RuntimeError("google-cloud-firestore is required to use Firestore") from exc


def _isolate_to_dict(isolate: CanonicalIsolate) -> dict[str, object]:
    return {
        "isolate_id": isolate.isolate_id,
        "collection_date": isolate.collection_date.isoformat(),
        "organism_code": isolate.organism_code,
        "organism_name": isolate.organism_name,
        "facility_id": isolate.facility_id,
        "lab_id": isolate.lab_id,
        "ward": isolate.ward,
        "specimen_type": isolate.specimen_type,
        "patient_token": isolate.patient_token,
        "source_import_id": isolate.source_import_id,
        "ast_results": {
            code: observation.interpretation.name
            for code, observation in isolate.ast_results.items()
        },
    }


def _isolate_from_dict(data: dict[str, object]) -> CanonicalIsolate:
    ast_raw = data.get("ast_results")
    ast_dict = ast_raw if isinstance(ast_raw, dict) else {}
    code_map = {"SUSCEPTIBLE": "S", "RESISTANT": "R", "INTERMEDIATE": "I", "UNKNOWN": "UNKNOWN"}
    return CanonicalIsolate(
        isolate_id=str(data["isolate_id"]),
        collection_date=date.fromisoformat(str(data["collection_date"])),
        organism_code=str(data["organism_code"]),
        organism_name=str(data["organism_name"]),
        facility_id=str(data["facility_id"]),
        lab_id=str(data["lab_id"]),
        ward=str(data["ward"]),
        specimen_type=str(data["specimen_type"]),
        patient_token=str(data["patient_token"]),
        source_import_id=str(data["source_import_id"]),
        ast_results=MappingProxyType(
            {
                code: AstObservation(Interpretation(code_map.get(str(raw), "UNKNOWN")))
                for code, raw in ast_dict.items()
            }
        ),
    )


def _stored_from_dict(
    data: dict[str, object],
    isolates: tuple[CanonicalIsolate, ...],
) -> StoredIncidentContext:
    pair = data.get("profile_comparison_isolate_ids")
    pair_tuple = tuple(pair) if isinstance(pair, list) and len(pair) == 2 else None
    version_raw = data.get("incident_version")
    version = int(version_raw) if isinstance(version_raw, int) else int(str(version_raw or "0"))
    return StoredIncidentContext(
        incident_id=IncidentId(str(data["incident_id"])),
        incident_version=IncidentVersion(version),
        source_watermark=SourceWatermark(str(data["source_watermark"])),
        isolates=isolates,
        signal_config=SignalConfig(),
        window_end=date.fromisoformat(str(data["window_end"])),
        profile_comparison_isolate_ids=pair_tuple,
    )
