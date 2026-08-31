"""Ngabo Connect deadline-slice contracts (Epic #171).

Framework-free value objects for the narrow zero-touch lab-export ->
surveillance slice. These carry stable identities (lab_id, source_id,
source_profile_version, batch_id, file_sha256) and are persisted to Firestore
as the canonical batch/workflow state. No GCP/FastAPI imports here.

Authority boundary: the raw file is immutable source; cleaning is deterministic;
Gemini decides nothing about microbiology truth. Quarantined rows are structurally
excluded from surveillance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _require_nonblank(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected non-blank text")
    return value


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_PATTERN.fullmatch(value):
        raise ValueError(f"Invalid {label} {value!r}; expected a 64-hex sha256")
    return value


class BatchStatus(StrEnum):
    """Deterministic lifecycle state of a Connect batch."""

    RAW_BATCH_ACCEPTED = "RAW_BATCH_ACCEPTED"
    CLEANING_STARTED = "CLEANING_STARTED"
    VALIDATION_COMPLETED = "VALIDATION_COMPLETED"
    NORMALIZATION_COMPLETED = "NORMALIZATION_COMPLETED"
    QUARANTINE_COMPLETED = "QUARANTINE_COMPLETED"
    CANONICAL_DATA_PERSISTED = "CANONICAL_DATA_PERSISTED"
    SURVEILLANCE_REFRESHED = "SURVEILLANCE_REFRESHED"
    SIGNAL_DETECTED = "SIGNAL_DETECTED"
    INVESTIGATION_STARTED = "INVESTIGATION_STARTED"
    PACKAGE_CANDIDATE_GENERATED = "PACKAGE_CANDIDATE_GENERATED"
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True)
class LaboratorySource:
    """One configured governed laboratory/source for the demo slice."""

    lab_id: str
    source_id: str
    display_name: str
    synthetic: bool = True

    def __post_init__(self) -> None:
        _require_nonblank(self.lab_id, "lab_id")
        _require_nonblank(self.source_id, "source_id")
        _require_nonblank(self.display_name, "display_name")
        if not self.synthetic:
            raise ValueError("the deadline demo source must be synthetic=true")


@dataclass(frozen=True)
class SourceProfile:
    """One governed source-profile: version + deterministic alias mappings."""

    name: str
    version: str
    organism_aliases: dict[str, str]
    organism_name_aliases: dict[str, str]
    interpretation_aliases: dict[str, str]

    def __post_init__(self) -> None:
        _require_nonblank(self.name, "source profile name")
        _require_nonblank(self.version, "source profile version")
        for label, mapping in (
            ("organism_aliases", self.organism_aliases),
            ("organism_name_aliases", self.organism_name_aliases),
            ("interpretation_aliases", self.interpretation_aliases),
        ):
            if not isinstance(mapping, dict):
                raise ValueError(f"{label} must be a dict")
            for key, value in mapping.items():
                _require_nonblank(key, f"{label} key")
                _require_nonblank(value, f"{label} value")


@dataclass(frozen=True)
class RawSourceIdentity:
    """Stable identity of one immutable raw source file."""

    file_sha256: str
    filename: str

    def __post_init__(self) -> None:
        _require_sha256(self.file_sha256, "file_sha256")
        _require_nonblank(self.filename, "filename")


@dataclass(frozen=True)
class AcceptedRecord:
    """One deterministically normalized, canonical bound record."""

    isolate_id: str
    organism_code: str
    organism_name: str
    collection_date: str
    facility_id: str
    lab_id: str
    ward: str
    specimen_type: str
    patient_token: str
    source_import_id: str
    ast_results: dict[str, str]
    row_index: int

    def to_canonical(self) -> dict[str, object]:
        return {
            "isolate_id": self.isolate_id,
            "organism_code": self.organism_code,
            "organism_name": self.organism_name,
            "collection_date": self.collection_date,
            "facility_id": self.facility_id,
            "lab_id": self.lab_id,
            "ward": self.ward,
            "specimen_type": self.specimen_type,
            "patient_token": self.patient_token,
            "source_import_id": self.source_import_id,
            "ast_results": dict(self.ast_results),
        }


@dataclass(frozen=True)
class QuarantinedRecord:
    """One quarantined row; structurally incapable of reaching surveillance."""

    row_index: int
    reason_code: str
    detail: str
    original: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if (
            isinstance(self.row_index, bool)
            or not isinstance(self.row_index, int)
            or self.row_index < 0
        ):
            raise ValueError("row_index must be a non-negative integer")
        _require_nonblank(self.reason_code, "reason_code")
        _require_nonblank(self.detail, "detail")


@dataclass(frozen=True)
class DataQualityReport:
    """Real, deterministic counts produced by one cleaning pass."""

    received_count: int
    accepted_count: int
    quarantined_count: int
    normalization_count: int

    def __post_init__(self) -> None:
        for name, value in (
            ("received_count", self.received_count),
            ("accepted_count", self.accepted_count),
            ("quarantined_count", self.quarantined_count),
            ("normalization_count", self.normalization_count),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")

    def to_primitive(self) -> dict[str, int]:
        return {
            "received_count": self.received_count,
            "accepted_count": self.accepted_count,
            "quarantined_count": self.quarantined_count,
            "normalization_count": self.normalization_count,
        }


@dataclass(frozen=True)
class ConnectBatch:
    """Batch-level identity + provenance for one raw connect batch."""

    batch_id: str
    lab_id: str
    source_id: str
    source_profile_version: str
    file_sha256: str
    gcs_uri: str
    status: BatchStatus
    received_count: int
    accepted_count: int
    quarantined_count: int
    normalization_count: int
    signal_id: str | None = None
    execution_id: str | None = None

    def __post_init__(self) -> None:
        _require_nonblank(self.batch_id, "batch_id")
        _require_nonblank(self.lab_id, "lab_id")
        _require_nonblank(self.source_id, "source_id")
        _require_nonblank(self.source_profile_version, "source_profile_version")
        _require_sha256(self.file_sha256, "file_sha256")
        _require_nonblank(self.gcs_uri, "gcs_uri")
        if not isinstance(self.status, BatchStatus):
            raise ValueError("status must be a BatchStatus")

    def to_primitive(self) -> dict[str, object]:
        return {
            "batch_id": self.batch_id,
            "lab_id": self.lab_id,
            "source_id": self.source_id,
            "source_profile_version": self.source_profile_version,
            "file_sha256": self.file_sha256,
            "gcs_uri": self.gcs_uri,
            "status": self.status.value,
            "received_count": self.received_count,
            "accepted_count": self.accepted_count,
            "quarantined_count": self.quarantined_count,
            "normalization_count": self.normalization_count,
            "signal_id": self.signal_id,
            "execution_id": self.execution_id,
        }


@dataclass(frozen=True)
class WorkflowEvent:
    """One real persisted workflow event (no fake progress)."""

    event_id: str
    event_name: str
    batch_id: str
    payload: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_nonblank(self.event_id, "event_id")
        _require_nonblank(self.event_name, "event_name")
        _require_nonblank(self.batch_id, "batch_id")
