"""Canonical investigation-context contracts for Issue #50.

``StoredIncidentContext`` is the immutable canonical state an inward
repository port returns for one incident. ``GetInvestigationContextQuery`` is
the caller's request (optionally pinning a version) and
``InvestigationContextResult`` is the typed versioned outcome. Every result
binds to the incident identity, an explicit incident version, and a source
watermark so downstream orchestration can establish which canonical state
produced the investigation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ngabo.application.enums.capability_outcome import CapabilityOutcome
from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.signal_config import SignalConfig
from ngabo.domain.value_objects.source_watermark import SourceWatermark


def _require_isolates(values: object) -> None:
    if not isinstance(values, tuple):
        raise ValueError(f"Invalid isolates {values!r}; expected a tuple")
    for index, item in enumerate(values):
        if not isinstance(item, CanonicalIsolate):
            raise ValueError(
                f"Invalid isolate at position {index}: {item!r}; "
                "expected a CanonicalIsolate"
            )


def _require_pair(value: object) -> tuple[str, str] | None:
    """Validate an optional canonical profile-comparison isolate pair."""
    if value is None:
        return None
    if not isinstance(value, tuple) or len(value) != 2:
        raise ValueError(
            f"Invalid profile_comparison_isolate_ids {value!r}; expected a 2-tuple"
        )
    a, b = value
    for item in (a, b):
        if not isinstance(item, str) or not item.strip() or item != item.strip():
            raise ValueError(f"Invalid profile comparison isolate id {item!r}")
    if a == b:
        raise ValueError("a profile comparison requires two distinct isolates")
    return (a, b)


@dataclass(frozen=True)
class StoredIncidentContext:
    """Immutable canonical incident context returned by the repository port."""

    incident_id: IncidentId
    incident_version: IncidentVersion
    source_watermark: SourceWatermark
    isolates: tuple[CanonicalIsolate, ...]
    signal_config: SignalConfig
    window_end: date
    profile_comparison_isolate_ids: tuple[str, str] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.incident_id, IncidentId):
            raise ValueError("incident_id must be an IncidentId")
        if not isinstance(self.incident_version, IncidentVersion):
            raise ValueError("incident_version must be an IncidentVersion")
        if not isinstance(self.source_watermark, SourceWatermark):
            raise ValueError("source_watermark must be a SourceWatermark")
        _require_isolates(self.isolates)
        # Canonical, deterministic isolate ordering: equivalent contexts must
        # produce the same semantic result regardless of repository return order.
        object.__setattr__(
            self,
            "isolates",
            tuple(sorted(self.isolates, key=lambda iso: iso.isolate_id)),
        )
        if type(self.signal_config) is not SignalConfig:
            raise TypeError("signal_config must be an exact SignalConfig")
        if type(self.window_end) is not date:
            raise TypeError("window_end must be an exact datetime.date")
        object.__setattr__(
            self,
            "profile_comparison_isolate_ids",
            _require_pair(self.profile_comparison_isolate_ids),
        )


@dataclass(frozen=True)
class GetInvestigationContextQuery:
    """Request to retrieve the canonical context for one incident."""

    incident_id: IncidentId
    requested_version: IncidentVersion | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.incident_id, IncidentId):
            raise ValueError("incident_id must be an IncidentId")
        if self.requested_version is not None and not isinstance(
            self.requested_version, IncidentVersion
        ):
            raise ValueError("requested_version must be an IncidentVersion or None")


@dataclass(frozen=True)
class InvestigationContextResult:
    """Typed versioned result of the canonical-context capability."""

    outcome: CapabilityOutcome
    incident_id: IncidentId | None
    incident_version: IncidentVersion | None
    source_watermark: SourceWatermark | None
    isolates: tuple[CanonicalIsolate, ...]
    signal_config: SignalConfig | None
    window_end: date | None
    requested_version: IncidentVersion | None = None
    profile_comparison_isolate_ids: tuple[str, str] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, CapabilityOutcome):
            raise ValueError("outcome must be a CapabilityOutcome")
        if self.incident_id is not None and not isinstance(self.incident_id, IncidentId):
            raise ValueError("incident_id must be an IncidentId or None")
        if self.incident_version is not None and not isinstance(
            self.incident_version, IncidentVersion
        ):
            raise ValueError("incident_version must be an IncidentVersion or None")
        if self.source_watermark is not None and not isinstance(
            self.source_watermark, SourceWatermark
        ):
            raise ValueError("source_watermark must be a SourceWatermark or None")
        _require_isolates(self.isolates)
        object.__setattr__(
            self,
            "isolates",
            tuple(sorted(self.isolates, key=lambda iso: iso.isolate_id)),
        )
        if self.signal_config is not None and type(self.signal_config) is not SignalConfig:
            raise TypeError("signal_config must be an exact SignalConfig or None")
        if self.window_end is not None and type(self.window_end) is not date:
            raise TypeError("window_end must be an exact datetime.date or None")
        object.__setattr__(
            self,
            "profile_comparison_isolate_ids",
            _require_pair(self.profile_comparison_isolate_ids),
        )
