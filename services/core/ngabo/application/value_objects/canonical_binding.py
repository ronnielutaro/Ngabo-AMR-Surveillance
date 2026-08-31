"""Framework-free canonical-binding value objects for the deadline hero (#176)."""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.source_watermark import SourceWatermark


def _require_nonblank(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected non-blank text")
    return value


@dataclass(frozen=True)
class CanonicalFinding:
    """Deterministic canonical finding proof material for one finding ID."""

    finding_id: str
    policy_version: str
    input_refs: tuple[str, ...]
    output_value: str

    def __post_init__(self) -> None:
        _require_nonblank(self.finding_id, "finding id")
        _require_nonblank(self.policy_version, "policy version")
        if not isinstance(self.input_refs, tuple):
            raise ValueError("input_refs must be a tuple")
        for ref in self.input_refs:
            _require_nonblank(ref, "finding input ref")
        _require_nonblank(self.output_value, "output value")


@dataclass(frozen=True)
class CanonicalEvidence:
    """Approved-evidence canonical proof material for one source ID."""

    source_id: str
    provenance: str
    chunk_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_nonblank(self.source_id, "source id")
        _require_nonblank(self.provenance, "provenance")
        if not isinstance(self.chunk_ids, tuple):
            raise ValueError("chunk_ids must be a tuple")
        for chunk in self.chunk_ids:
            _require_nonblank(chunk, "evidence chunk id")


@dataclass(frozen=True)
class HeroStateBinding:
    """Authoritative current binding reloaded immediately before authorization."""

    incident_id: IncidentId
    incident_version: IncidentVersion
    source_watermark: SourceWatermark
    policy_config_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.incident_id, IncidentId):
            raise ValueError("incident_id must be an IncidentId")
        if not isinstance(self.incident_version, IncidentVersion):
            raise ValueError("incident_version must be an IncidentVersion")
        if not isinstance(self.source_watermark, SourceWatermark):
            raise ValueError("source_watermark must be a SourceWatermark")
        _require_nonblank(self.policy_config_version, "policy config version")
