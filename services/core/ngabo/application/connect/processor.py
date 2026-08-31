"""Connect batch processor: clean -> canonical isolates -> signal -> hero (#171).

The application bridge between the Connect slice and the existing trusted
surveillance/hero boundary. It runs the deterministic ``WHONET_DEMO_V1`` cleaning,
builds canonical isolates, runs the EXISTING deterministic signal detection, and
hands off to an injected hero executor (the existing HeroRuntime). It does not
re-implement surveillance science or hero logic.
"""

from __future__ import annotations

import csv
import hashlib
import io
from collections.abc import Callable
from datetime import date
from typing import Any

from ngabo.application.connect.contracts import AcceptedRecord
from ngabo.application.connect.source_profile import WHONET_DEMO_V1, clean_rows
from ngabo.domain.entities.ast_observation import AstObservation
from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.enums.interpretation import Interpretation
from ngabo.domain.services.signal_detection import evaluate_surveillance_signals
from ngabo.domain.value_objects.signal_config import SignalConfig

AST_CODES = ("AMK", "CAZ", "CIP", "CRO", "MEM", "SXT")
_INTERP = {
    "S": Interpretation.SUSCEPTIBLE,
    "R": Interpretation.RESISTANT,
    "I": Interpretation.INTERMEDIATE,
    "UNKNOWN": Interpretation.UNKNOWN,
}


def process_connect_csv(
    raw: bytes,
    *,
    lab_id: str,
    source_id: str,
    window_end_iso: str,
    execute_hero: Callable[[dict[str, object]], dict[str, object]],
    persist_isolates: Callable[[str, list[CanonicalIsolate]], None] | None = None,
    publish_progress: Callable[[dict[str, object]], None] | None = None,
) -> dict[str, Any]:
    """Run cleaning + signal detection + hero handoff for one raw CSV batch.

    Returns a JSON-safe dict with real counts, the deterministic signal if any, the
    hero result, and the workflow timeline. The ``execute_hero`` callback is the
    existing HeroRuntime seam (injected by the infrastructure composition root).
    """
    batch_id = f"batch-{hashlib.sha256(raw).hexdigest()[:16]}"
    events: list[dict[str, object]] = []
    received_count = 0
    accepted_count = 0
    quarantined_count = 0
    normalization_count = 0
    signal_id: str | None = None
    signal_count = 0
    hero_result: dict[str, object] | None = None

    def snapshot(
        *, active_stage: str | None, workflow_state: str = "RUNNING"
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "batch_id": batch_id,
            "lab_id": lab_id,
            "source_id": source_id,
            "source_profile_version": WHONET_DEMO_V1.version,
            "accepted_count": accepted_count,
            "quarantined_count": quarantined_count,
            "received_count": received_count,
            "normalization_count": normalization_count,
            "signal_id": signal_id,
            "signal_count": signal_count,
            "hero_result": hero_result,
            "active_stage": active_stage,
            "workflow_state": workflow_state,
            "events": [dict(event) for event in events],
        }
        if publish_progress is not None:
            publish_progress(payload)
        return payload

    snapshot(active_stage="LAB_BATCH_SYNCED")
    parser = csv.DictReader(io.StringIO(raw.decode("utf-8")))
    rows: list[dict[str, object]] = []
    for index, raw_row in enumerate(parser):
        row: dict[str, object] = {
            "row_index": index,
            "isolate_id": raw_row.get("ISOLATE_ID", ""),
            "collection_date": raw_row.get("COLLECTION_DATE", ""),
            "organism_code": raw_row.get("ORGANISM_CODE", ""),
            "organism_name": raw_row.get("ORGANISM_NAME", ""),
            "facility_id": raw_row.get("FACILITY_ID", ""),
            "lab_id": raw_row.get("LAB_ID", ""),
            "ward": raw_row.get("WARD", ""),
            "specimen_type": raw_row.get("SPECIMEN_TYPE", ""),
            "patient_token": raw_row.get("PATIENT_TOKEN", ""),
            "source_import_id": raw_row.get("SOURCE_IMPORT_ID", ""),
            "ast_results": {code: raw_row.get(code, "") for code in AST_CODES},
        }
        rows.append(row)
    received_count = len(rows)
    events.append({"event": "LAB_BATCH_SYNCED"})
    snapshot(active_stage="CLEANING_STARTED")
    accepted, quarantined, report = clean_rows(rows, WHONET_DEMO_V1)
    received_count = report.received_count
    accepted_count = report.accepted_count
    quarantined_count = report.quarantined_count
    normalization_count = report.normalization_count
    events.extend(
        (
            {"event": "CLEANING_STARTED"},
            {"event": "VALIDATION_COMPLETED"},
            {"event": "NORMALIZATION_COMPLETED"},
            {"event": "QUARANTINE_COMPLETED"},
        )
    )
    snapshot(active_stage="SURVEILLANCE_REFRESHED")
    isolates = [_to_isolate(record) for record in accepted]
    window_end = date.fromisoformat(window_end_iso)
    signals = evaluate_surveillance_signals(isolates, window_end, SignalConfig())
    events.append({"event": "SURVEILLANCE_REFRESHED"})
    signal_id = signals[0].signal_id if signals else None
    signal_count = len(signals)
    if signals:
        snapshot(active_stage="SIGNAL_DETECTED")
        events.append({"event": "SIGNAL_DETECTED", "signal_id": signal_id})
        incident_numeric = int(hashlib.sha256(raw).hexdigest()[:12], 16) % 10**8
        command: dict[str, object] = {
            "contract_version": "ngabo-event-investigation-v1",
            "incident_id": f"INC-{incident_numeric}",
            "incident_version": 1,
            "source_watermark": f"connect/{lab_id}/{source_id}/v1",
            "event_id": f"evt-{hashlib.sha256(raw).hexdigest()[:16]}",
            "correlation_id": f"corr-{signal_id or 'none'}",
        }
        snapshot(active_stage="INVESTIGATION_STARTED")
        if persist_isolates is not None:
            persist_isolates(str(command["incident_id"]), isolates)
        events.append({"event": "INVESTIGATION_STARTED"})
        snapshot(active_stage="WORKFLOW_HERO_COMPLETED")
        hero_result = execute_hero(command)
        outcome = hero_result.get("outcome") if hero_result else None
        if outcome:
            events.append({"event": f"WORKFLOW_{outcome}"})
    terminal = (
        "COMPLETED"
        if hero_result and hero_result.get("outcome") == "HERO_COMPLETED"
        else "BLOCKED"
    )
    return snapshot(active_stage=None, workflow_state=terminal)


def _to_isolate(record: AcceptedRecord) -> CanonicalIsolate:
    return CanonicalIsolate(
        isolate_id=record.isolate_id,
        collection_date=date.fromisoformat(record.collection_date),
        organism_code=record.organism_code,
        organism_name=record.organism_name,
        facility_id=record.facility_id,
        lab_id=record.lab_id,
        ward=record.ward,
        specimen_type=record.specimen_type,
        patient_token=record.patient_token,
        source_import_id=record.source_import_id,
        ast_results={
            code: AstObservation(_INTERP[interp]) for code, interp in record.ast_results.items()
        },
    )
