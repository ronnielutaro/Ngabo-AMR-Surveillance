"""Material-missingness investigation capability contracts (Issue #50).

The deterministic missingness capability reports which required inputs for the
investigation are materially absent, in stable typed form. It distinguishes
material absence from ordinary empty values so future Gemini reasoning knows
where evidence/data is missing rather than hallucinating completeness. The
model never decides materiality; deterministic code does.
"""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.application.enums.capability_outcome import CapabilityOutcome
from ngabo.application.enums.missingness_code import MissingnessCode
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.source_watermark import SourceWatermark


def _require_opaque_id(value: object, label: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected a non-blank opaque ID")


@dataclass(frozen=True)
class MissingnessItem:
    """One typed material-absence condition."""

    code: MissingnessCode
    field: str
    material: bool = True
    detail: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, MissingnessCode):
            raise ValueError("code must be a MissingnessCode")
        _require_opaque_id(self.field, "field")
        if not isinstance(self.material, bool):
            raise ValueError("material must be a bool")
        if self.detail is not None and (
            not isinstance(self.detail, str) or not self.detail.strip()
        ):
            raise ValueError("detail must be non-blank text or None")


@dataclass(frozen=True)
class AssessMissingnessQuery:
    """Request a deterministic material-missingness assessment."""

    incident_id: IncidentId
    required_isolate_ids: tuple[str, ...] = ()
    requested_version: IncidentVersion | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.incident_id, IncidentId):
            raise ValueError("incident_id must be an IncidentId")
        if not isinstance(self.required_isolate_ids, tuple):
            raise ValueError("required_isolate_ids must be a tuple")
        for index, isolate_id in enumerate(self.required_isolate_ids):
            _require_opaque_id(isolate_id, f"required_isolate_ids element at {index}")
        if self.requested_version is not None and not isinstance(
            self.requested_version, IncidentVersion
        ):
            raise ValueError("requested_version must be an IncidentVersion or None")


@dataclass(frozen=True)
class MissingnessResult:
    """Typed material-missingness assessment bound to an incident version."""

    outcome: CapabilityOutcome
    incident_id: IncidentId
    incident_version: IncidentVersion | None
    source_watermark: SourceWatermark | None
    missing_items: tuple[MissingnessItem, ...]
    has_material_missingness: bool

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, CapabilityOutcome):
            raise ValueError("outcome must be a CapabilityOutcome")
        if not isinstance(self.incident_id, IncidentId):
            raise ValueError("incident_id must be an IncidentId")
        if self.incident_version is not None and not isinstance(
            self.incident_version, IncidentVersion
        ):
            raise ValueError("incident_version must be an IncidentVersion or None")
        if self.source_watermark is not None and not isinstance(
            self.source_watermark, SourceWatermark
        ):
            raise ValueError("source_watermark must be a SourceWatermark or None")
        if not isinstance(self.missing_items, tuple):
            raise ValueError("missing_items must be a tuple")
        for index, item in enumerate(self.missing_items):
            if not isinstance(item, MissingnessItem):
                raise ValueError(
                    f"Invalid missingness item at position {index}: {item!r}; "
                    "expected a MissingnessItem"
                )
        if not isinstance(self.has_material_missingness, bool):
            raise ValueError("has_material_missingness must be a bool")
