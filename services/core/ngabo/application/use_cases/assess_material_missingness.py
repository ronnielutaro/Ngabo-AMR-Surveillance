"""Material-missingness investigation capability (Issue #50).

Deterministically assesses which required inputs for the investigation are
materially absent, in stable typed form. It distinguishes material absence from
ordinary empty values and never delegates materiality to a model. A missing
incident or a stale version is reported through the stable ``CapabilityOutcome``
and a corresponding material ``MissingnessItem``.
"""

from __future__ import annotations

from ngabo.application.enums.capability_outcome import CapabilityOutcome
from ngabo.application.enums.missingness_code import MissingnessCode
from ngabo.application.ports.investigation_context_repository import (
    InvestigationContextRepository,
)
from ngabo.application.value_objects.missingness import (
    AssessMissingnessQuery,
    MissingnessItem,
    MissingnessResult,
)


def _item(
    code: MissingnessCode,
    field: str,
    *,
    detail: str | None = None,
) -> MissingnessItem:
    return MissingnessItem(code=code, field=field, material=True, detail=detail)


class AssessMaterialMissingness:
    """Framework-free material-missingness application capability."""

    def __init__(self, repository: InvestigationContextRepository) -> None:
        if not hasattr(repository, "get"):
            raise TypeError("repository must satisfy InvestigationContextRepository")
        self._repository = repository

    def execute(self, query: AssessMissingnessQuery) -> MissingnessResult:
        """Return the typed material-missingness assessment for ``query``."""
        if not isinstance(query, AssessMissingnessQuery):
            raise TypeError(f"query must be an AssessMissingnessQuery; got {type(query).__name__}")

        stored = self._repository.get(query.incident_id)
        if stored is None:
            return MissingnessResult(
                outcome=CapabilityOutcome.INCIDENT_NOT_FOUND,
                incident_id=query.incident_id,
                incident_version=None,
                source_watermark=None,
                missing_items=(
                    _item(
                        MissingnessCode.REQUIRED_FIELD_ABSENT,
                        "incident",
                        detail="incident not found",
                    ),
                ),
                has_material_missingness=True,
            )

        if (
            query.requested_version is not None
            and query.requested_version != stored.incident_version
        ):
            return MissingnessResult(
                outcome=CapabilityOutcome.STALE_INCIDENT_VERSION,
                incident_id=stored.incident_id,
                incident_version=stored.incident_version,
                source_watermark=stored.source_watermark,
                missing_items=(
                    _item(
                        MissingnessCode.REQUIRED_FIELD_ABSENT,
                        "incident_version",
                        detail=(
                            f"requested version {query.requested_version} != "
                            f"stored version {stored.incident_version}"
                        ),
                    ),
                ),
                has_material_missingness=True,
            )

        items: list[MissingnessItem] = []
        # Canonical context completeness (material, but never a model decision).
        if stored.window_end is None:
            items.append(_item(MissingnessCode.INCOMPLETE_SOURCE_WINDOW, "window_end"))
        if not stored.isolates:
            items.append(_item(MissingnessCode.REQUIRED_FIELD_ABSENT, "isolates"))

        # Required comparison inputs requested by the caller.
        present = {iso.isolate_id for iso in stored.isolates}
        for isolate_id in query.required_isolate_ids:
            if isolate_id not in present:
                items.append(
                    _item(
                        MissingnessCode.MISSING_COMPARISON_INPUT,
                        "isolate_id",
                        detail=f"required isolate {isolate_id!r} is absent",
                    )
                )

        has_material = bool(items)
        return MissingnessResult(
            outcome=CapabilityOutcome.SUCCESS,
            incident_id=stored.incident_id,
            incident_version=stored.incident_version,
            source_watermark=stored.source_watermark,
            missing_items=tuple(items),
            has_material_missingness=has_material,
        )

    def __call__(self, query: AssessMissingnessQuery) -> MissingnessResult:
        """Callable protocol support."""
        return self.execute(query)
