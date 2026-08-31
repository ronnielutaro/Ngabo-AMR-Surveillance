"""Framework-free support context for hero verification (#176).

This is the exactly-current run's support snapshot the verifier checks the
candidate against: the run binding, the canonical record IDs, the deterministic
finding IDs, and the approved-evidence source/chunk IDs actually supplied to this
run. It is deliberately separate from the raw candidate so a cross-run or stale
candidate cannot pass.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.source_watermark import SourceWatermark

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _require_nonblank(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected non-blank text")
    return value


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
    record_ids: frozenset[str]
    finding_ids: frozenset[str]
    evidence_source_ids: frozenset[str]
    evidence_reference_ids: frozenset[str]
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
        _ids(self.record_ids, "record_ids")
        _ids(self.finding_ids, "finding_ids")
        _ids(self.evidence_source_ids, "evidence_source_ids")
        _ids(self.evidence_reference_ids, "evidence_reference_ids")
        _ids(self.authorized_target_ids, "authorized_target_ids")
