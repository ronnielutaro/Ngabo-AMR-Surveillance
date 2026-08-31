"""Framework-free support context for hero verification (#176).

This is the exactly-current run's support snapshot the verifier checks the
candidate against. It carries the run binding AND the canonical proof VALUES that
a model-generated reference must match (record field/value, deterministic finding
details, approved-evidence source/chunk identity). The ID streams are derived
from the canonical maps so a claim may only reference something that has actual
canonical proof material, never an empty ID set.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from ngabo.application.value_objects.canonical_binding import (
    CanonicalEvidence,
    CanonicalFinding,
)
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.source_watermark import SourceWatermark


def _require_nonblank(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected non-blank text")
    return value


def _records_map(value: object) -> Mapping[str, Mapping[str, str]]:
    if not isinstance(value, Mapping):
        raise ValueError("canonical_records must be a Mapping")
    out: dict[str, Mapping[str, str]] = {}
    for record_id, fields in value.items():
        _require_nonblank(record_id, "record id")
        if not isinstance(fields, Mapping):
            raise ValueError(f"record {record_id!r} fields must be a Mapping")
        out[record_id] = MappingProxyType(
            {
                _require_nonblank(k, "record field path"): _require_nonblank(
                    v, "record expected value"
                )
                for k, v in fields.items()
            }
        )
    return MappingProxyType(out)


def _findings_map(value: object) -> Mapping[str, CanonicalFinding]:
    if not isinstance(value, Mapping):
        raise ValueError("canonical_findings must be a Mapping")
    out: dict[str, CanonicalFinding] = {}
    for finding_id, finding in value.items():
        _require_nonblank(finding_id, "finding id")
        if not isinstance(finding, CanonicalFinding):
            raise ValueError(f"finding {finding_id!r} must be a CanonicalFinding")
        out[finding_id] = finding
    return MappingProxyType(out)


def _evidence_map(value: object) -> Mapping[str, CanonicalEvidence]:
    if not isinstance(value, Mapping):
        raise ValueError("canonical_evidence must be a Mapping")
    out: dict[str, CanonicalEvidence] = {}
    for source_id, evidence in value.items():
        _require_nonblank(source_id, "source id")
        if not isinstance(evidence, CanonicalEvidence):
            raise ValueError(f"evidence {source_id!r} must be a CanonicalEvidence")
        out[source_id] = evidence
    return MappingProxyType(out)


def _ids(values: object, label: str) -> frozenset[str]:
    if not isinstance(values, (frozenset, set, tuple, list)):
        raise ValueError(f"Invalid {label} {values!r}; expected an iterable of IDs")
    result: set[str] = set()
    for value in values:
        result.add(_require_nonblank(value, label))
    return frozenset(result)


@dataclass(frozen=True)
class HeroSupportContext:
    """The exactly-current run's deterministic support and binding state."""

    incident_id: IncidentId
    incident_version: IncidentVersion
    source_watermark: SourceWatermark
    execution_id: str
    policy_config_version: str
    canonical_records: Mapping[str, Mapping[str, str]] = field(
        default_factory=lambda: MappingProxyType({})
    )
    canonical_findings: Mapping[str, CanonicalFinding] = field(
        default_factory=lambda: MappingProxyType({})
    )
    canonical_evidence: Mapping[str, CanonicalEvidence] = field(
        default_factory=lambda: MappingProxyType({})
    )
    authorized_target_ids: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not isinstance(self.incident_id, IncidentId):
            raise ValueError("incident_id must be an IncidentId")
        if not isinstance(self.incident_version, IncidentVersion):
            raise ValueError("incident_version must be an IncidentVersion")
        if not isinstance(self.source_watermark, SourceWatermark):
            raise ValueError("source_watermark must be a SourceWatermark")
        _require_nonblank(self.execution_id, "execution id")
        _require_nonblank(self.policy_config_version, "policy config version")
        object.__setattr__(
            self, "canonical_records", _records_map(self.canonical_records)
        )
        object.__setattr__(
            self, "canonical_findings", _findings_map(self.canonical_findings)
        )
        object.__setattr__(
            self, "canonical_evidence", _evidence_map(self.canonical_evidence)
        )
        _ids(self.authorized_target_ids, "authorized_target_ids")

    @property
    def record_ids(self) -> frozenset[str]:
        """All canonical record IDs with proof material."""
        return frozenset(self.canonical_records)

    @property
    def finding_ids(self) -> frozenset[str]:
        """All canonical deterministic finding IDs."""
        return frozenset(self.canonical_findings)

    @property
    def evidence_source_ids(self) -> frozenset[str]:
        """All canonical approved-evidence source IDs."""
        return frozenset(self.canonical_evidence)

    @property
    def evidence_reference_ids(self) -> frozenset[str]:
        """All canonical approved-evidence chunk IDs."""
        return frozenset(
            chunk_id
            for evidence in self.canonical_evidence.values()
            for chunk_id in evidence.chunk_ids
        )
