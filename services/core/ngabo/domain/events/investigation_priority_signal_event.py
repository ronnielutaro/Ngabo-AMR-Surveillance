"""Deterministic investigation-priority signal event contract (Issue #48 / Epic #18).

Primary Invariant: This event represents the deterministic handoff of an
INVESTIGATION_PRIORITY_SIGNAL candidate. It is NEVER an outbreak declaration,
diagnosis, model-confidence score, or clinical decision.
Contains NO timestamps, random UUIDs, network/cloud metadata, or delivery semantics.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from typing import Any

from ngabo.domain.value_objects.investigation_priority_signal import (
    InvestigationPrioritySignal,
)
from ngabo.domain.value_objects.proof_references import _require_opaque_id

DEFAULT_SIGNAL_EVENT_TYPE = "INVESTIGATION_PRIORITY_SIGNAL"
DEFAULT_SIGNAL_EVENT_CONTRACT_VERSION = "ngabo-signal-event-v1"


def compute_signal_event_id(
    *,
    contract_version: str,
    event_type: str,
    signal_id: str,
    source_watermark: str,
    facility_id: str,
    ward: str,
    organism_code: str,
    window_start: date,
    window_end: date,
    signal_score: float,
    precision: int,
    policy_version: str,
    config_version: str,
    algorithm_version: str,
    supporting_finding_refs: tuple[str, ...],
    supporting_isolate_refs: tuple[str, ...],
) -> str:
    """Compute a deterministic, opaque SHA-256 event ID for a signal event.

    Binds the meaningful semantic payload using sorted, separator-stripped JSON.
    Prefix: ``evt-`` + 16 hex characters.
    """
    payload = {
        "algorithm_version": algorithm_version,
        "config_version": config_version,
        "contract_version": contract_version,
        "event_type": event_type,
        "facility_id": facility_id,
        "organism_code": organism_code,
        "policy_version": policy_version,
        "signal_id": signal_id,
        "signal_score": f"{signal_score:.{precision}f}",
        "source_watermark": source_watermark,
        "supporting_finding_refs": list(supporting_finding_refs),
        "supporting_isolate_refs": list(supporting_isolate_refs),
        "ward": ward,
        "window_end": window_end.isoformat(),
        "window_start": window_start.isoformat(),
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(serialized).hexdigest()
    return f"evt-{digest[:16]}"


@dataclass(frozen=True)
class InvestigationPrioritySignalEvent:
    """Deterministic event envelope emitted when an investigation-priority signal triggers.

    Framework-free domain value object representing the deterministic handoff
    from surveillance signal detection to downstream workflow orchestration.
    """

    event_id: str
    event_type: str
    contract_version: str
    signal_id: str
    source_watermark: str
    facility_id: str
    ward: str
    organism_code: str
    window_start: date
    window_end: date
    signal_score: float
    policy_version: str
    config_version: str
    algorithm_version: str
    supporting_finding_refs: tuple[str, ...]
    supporting_isolate_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_opaque_id(self.event_id, "event_id")
        if not self.event_id.startswith("evt-"):
            raise ValueError(f"event_id must start with 'evt-'; got {self.event_id!r}")

        _require_opaque_id(self.event_type, "event_type")
        _require_opaque_id(self.contract_version, "contract_version")
        _require_opaque_id(self.signal_id, "signal_id")
        _require_opaque_id(self.source_watermark, "source_watermark")
        _require_opaque_id(self.facility_id, "facility_id")
        _require_opaque_id(self.ward, "ward")
        _require_opaque_id(self.organism_code, "organism_code")
        _require_opaque_id(self.policy_version, "policy_version")
        _require_opaque_id(self.config_version, "config_version")
        _require_opaque_id(self.algorithm_version, "algorithm_version")

        if type(self.window_start) is not date:
            raise TypeError("window_start must be an exact datetime.date")
        if type(self.window_end) is not date:
            raise TypeError("window_end must be an exact datetime.date")
        if self.window_start > self.window_end:
            raise ValueError("window_start must be <= window_end")

        if not isinstance(self.signal_score, float) or isinstance(self.signal_score, bool):
            raise TypeError("signal_score must be a float")
        if not (0.0 <= self.signal_score <= 1.0):
            raise ValueError("signal_score must be in range [0.0, 1.0]")

        if not isinstance(self.supporting_finding_refs, tuple):
            raise TypeError("supporting_finding_refs must be a tuple")
        if not self.supporting_finding_refs:
            raise ValueError("supporting_finding_refs cannot be empty")
        for ref in self.supporting_finding_refs:
            _require_opaque_id(ref, "supporting_finding_ref")

        if not isinstance(self.supporting_isolate_refs, tuple):
            raise TypeError("supporting_isolate_refs must be a tuple")
        if not self.supporting_isolate_refs:
            raise ValueError("supporting_isolate_refs cannot be empty")
        for ref in self.supporting_isolate_refs:
            _require_opaque_id(ref, "supporting_isolate_ref")

    def to_dict(self) -> dict[str, Any]:
        """Serialize event to a canonical dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "contract_version": self.contract_version,
            "signal_id": self.signal_id,
            "source_watermark": self.source_watermark,
            "facility_id": self.facility_id,
            "ward": self.ward,
            "organism_code": self.organism_code,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "signal_score": self.signal_score,
            "policy_version": self.policy_version,
            "config_version": self.config_version,
            "algorithm_version": self.algorithm_version,
            "supporting_finding_refs": list(self.supporting_finding_refs),
            "supporting_isolate_refs": list(self.supporting_isolate_refs),
        }

    def to_json(self) -> str:
        """Serialize event to canonical JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)


def create_investigation_priority_signal_event(
    signal: InvestigationPrioritySignal,
    source_watermark: str,
    contract_version: str = DEFAULT_SIGNAL_EVENT_CONTRACT_VERSION,
    event_type: str = DEFAULT_SIGNAL_EVENT_TYPE,
) -> InvestigationPrioritySignalEvent:
    """Create a deterministic event envelope from a triggered investigation-priority signal."""
    if type(signal) is not InvestigationPrioritySignal:
        raise TypeError("signal must be an exact InvestigationPrioritySignal instance")
    if not isinstance(source_watermark, str) or not source_watermark.strip():
        raise ValueError("source_watermark must be a non-empty string")

    event_id = compute_signal_event_id(
        contract_version=contract_version,
        event_type=event_type,
        signal_id=signal.signal_id,
        source_watermark=source_watermark,
        facility_id=signal.facility_id,
        ward=signal.ward,
        organism_code=signal.organism_code,
        window_start=signal.window_start,
        window_end=signal.window_end,
        signal_score=signal.signal_score,
        precision=signal.policy_config.precision,
        policy_version=signal.policy_version,
        config_version=signal.config_version,
        algorithm_version=signal.algorithm_version,
        supporting_finding_refs=signal.supporting_finding_refs,
        supporting_isolate_refs=signal.supporting_isolate_refs,
    )

    return InvestigationPrioritySignalEvent(
        event_id=event_id,
        event_type=event_type,
        contract_version=contract_version,
        signal_id=signal.signal_id,
        source_watermark=source_watermark,
        facility_id=signal.facility_id,
        ward=signal.ward,
        organism_code=signal.organism_code,
        window_start=signal.window_start,
        window_end=signal.window_end,
        signal_score=signal.signal_score,
        policy_version=signal.policy_version,
        config_version=signal.config_version,
        algorithm_version=signal.algorithm_version,
        supporting_finding_refs=signal.supporting_finding_refs,
        supporting_isolate_refs=signal.supporting_isolate_refs,
    )
