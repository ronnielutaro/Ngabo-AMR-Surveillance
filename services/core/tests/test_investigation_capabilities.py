"""Focused application tests for Issue #50 investigation capabilities.

These exercise the framework-free deterministic capabilities with an in-memory
repository fake — zero model/cloud dependencies. They cover success, missing
incident, stale version, required-branch failure, immutability, order
independence, stable references, and no-recomputation delegation to the existing
deterministic owners.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import FrozenInstanceError
from datetime import date
from types import MappingProxyType

import pytest

from ngabo.application.enums.capability_outcome import CapabilityOutcome
from ngabo.application.enums.missingness_code import MissingnessCode
from ngabo.application.use_cases.assess_material_missingness import (
    AssessMaterialMissingness,
)
from ngabo.application.use_cases.compare_resistance_profiles import (
    CompareResistanceProfiles,
)
from ngabo.application.use_cases.get_baseline_summary import GetBaselineSummary
from ngabo.application.use_cases.get_investigation_context import (
    GetInvestigationContext,
)
from ngabo.application.value_objects.baseline_summary import (
    GetBaselineSummaryQuery,
)
from ngabo.application.value_objects.investigation_context import (
    GetInvestigationContextQuery,
    InvestigationContextResult,
    StoredIncidentContext,
)
from ngabo.application.value_objects.missingness import (
    AssessMissingnessQuery,
)
from ngabo.application.value_objects.profile_comparison import (
    CompareProfilesQuery,
)
from ngabo.domain.entities.ast_observation import AstObservation
from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.enums.interpretation import Interpretation
from ngabo.domain.services.resistance_profile_similarity import (
    compare_canonical_isolates,
)
from ngabo.domain.services.signal_detection import (
    SignalEvaluationResult,
    evaluate_cohort_signal,
)
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.profile_similarity_finding import (
    ProfileSimilarityFinding,
)
from ngabo.domain.value_objects.signal_config import SignalConfig
from ngabo.domain.value_objects.source_watermark import SourceWatermark

INCIDENT_1 = IncidentId("INC-001")
INCIDENT_2 = IncidentId("INC-002")
VERSION_1 = IncidentVersion(1)
VERSION_2 = IncidentVersion(2)
WATERMARK = SourceWatermark("ngabo-source-v1:sha256:abc123")
WINDOW_END = date(2026, 8, 17)
COHORT_ORG = "kle"
COHORT_FACILITY = "SYNTH-FACILITY-001"
COHORT_WARD = "SYNTH-WARD-A"


def _make_isolate(
    isolate_id: str,
    *,
    collection_date: date = WINDOW_END,
) -> CanonicalIsolate:
    ast = {
        "AMK": Interpretation.SUSCEPTIBLE,
        "CAZ": Interpretation.RESISTANT,
        "CIP": Interpretation.RESISTANT,
        "CRO": Interpretation.RESISTANT,
        "MEM": Interpretation.RESISTANT,
        "SXT": Interpretation.RESISTANT,
    }
    ast_obs = MappingProxyType(
        {code: AstObservation(interp) for code, interp in ast.items()}
    )
    return CanonicalIsolate(
        isolate_id=isolate_id,
        collection_date=collection_date,
        organism_code=COHORT_ORG,
        organism_name="Klebsiella pneumoniae",
        facility_id=COHORT_FACILITY,
        lab_id="SYNTH-LAB-001",
        ward=COHORT_WARD,
        specimen_type="blood",
        patient_token=f"SYNTH-CASE-{isolate_id.replace('ISO-', '')}",
        source_import_id="SYNTH-IMPORT-001",
        ast_results=ast_obs,
    )


def _make_context(
    incident_id: IncidentId,
    *,
    version: IncidentVersion,
    isolate_ids: tuple[str, ...],
) -> StoredIncidentContext:
    isolates = tuple(_make_isolate(i) for i in isolate_ids)
    return StoredIncidentContext(
        incident_id=incident_id,
        incident_version=version,
        source_watermark=WATERMARK,
        isolates=isolates,
        signal_config=SignalConfig(),
        window_end=WINDOW_END,
    )


class FakeContextRepository:
    """In-memory InvestigationContextRepository fake."""

    def __init__(self, contexts: dict[str, StoredIncidentContext]) -> None:
        self._contexts = dict(contexts)

    def get(self, incident_id: IncidentId) -> StoredIncidentContext | None:
        return self._contexts.get(incident_id.value)


def _repo() -> FakeContextRepository:
    return FakeContextRepository(
        {
            INCIDENT_1.value: _make_context(
                INCIDENT_1,
                version=VERSION_1,
                isolate_ids=("ISO-001", "ISO-002", "ISO-003", "ISO-004"),
            ),
            INCIDENT_2.value: _make_context(
                INCIDENT_2,
                version=VERSION_2,
                isolate_ids=("ISO-010", "ISO-011", "ISO-012"),
            ),
        }
    )


def test_context_capability_success() -> None:
    capability = GetInvestigationContext(_repo())
    result = capability.execute(
        GetInvestigationContextQuery(incident_id=INCIDENT_1, requested_version=VERSION_1)
    )
    assert result.outcome is CapabilityOutcome.SUCCESS
    assert result.incident_id == INCIDENT_1
    assert result.incident_version == VERSION_1
    assert result.source_watermark == WATERMARK
    assert len(result.isolates) == 4
    assert result.signal_config is not None


def test_context_capability_missing_incident() -> None:
    capability = GetInvestigationContext(_repo())
    result = capability.execute(GetInvestigationContextQuery(incident_id=IncidentId("INC-999")))
    assert result.outcome is CapabilityOutcome.INCIDENT_NOT_FOUND
    assert result.incident_id is None
    assert result.isolates == ()


def test_context_capability_stale_version() -> None:
    capability = GetInvestigationContext(_repo())
    result = capability.execute(
        GetInvestigationContextQuery(incident_id=INCIDENT_1, requested_version=IncidentVersion(5))
    )
    assert result.outcome is CapabilityOutcome.STALE_INCIDENT_VERSION
    assert result.requested_version == IncidentVersion(5)
    assert result.incident_version == VERSION_1
    # Fail closed: no stale-context data is exposed for consumption.
    assert result.isolates == ()
    assert result.signal_config is None
    assert result.window_end is None
    assert result.source_watermark == WATERMARK


def test_profile_comparison_success_and_stable_reference() -> None:
    capability = CompareResistanceProfiles(_repo())
    result = capability.execute(
        CompareProfilesQuery(
            incident_id=INCIDENT_1,
            isolate_id_a="ISO-001",
            isolate_id_b="ISO-002",
            requested_version=VERSION_1,
        )
    )
    assert result.outcome is CapabilityOutcome.SUCCESS
    assert result.finding is not None
    assert result.finding_reference is not None
    assert result.finding_reference.finding_id == result.finding.finding_id
    assert result.finding_reference.policy_version == result.finding.policy_version


def test_profile_comparison_order_independent() -> None:
    repo = _repo()
    capability = CompareResistanceProfiles(repo)
    ab = capability.execute(
        CompareProfilesQuery(incident_id=INCIDENT_1, isolate_id_a="ISO-001", isolate_id_b="ISO-002")
    )
    ba = capability.execute(
        CompareProfilesQuery(incident_id=INCIDENT_1, isolate_id_a="ISO-002", isolate_id_b="ISO-001")
    )
    assert ab.outcome is CapabilityOutcome.SUCCESS
    assert ba.outcome is CapabilityOutcome.SUCCESS
    assert ab.finding == ba.finding
    assert ab.finding_reference == ba.finding_reference


def test_profile_comparison_missing_input() -> None:
    capability = CompareResistanceProfiles(_repo())
    result = capability.execute(
        CompareProfilesQuery(incident_id=INCIDENT_1, isolate_id_a="ISO-001", isolate_id_b="ISO-999")
    )
    assert result.outcome is CapabilityOutcome.MISSING_INPUT
    assert result.finding is None


def test_profile_comparison_same_isolate_is_not_a_comparison() -> None:
    capability = CompareResistanceProfiles(_repo())
    result = capability.execute(
        CompareProfilesQuery(incident_id=INCIDENT_1, isolate_id_a="ISO-001", isolate_id_b="ISO-001")
    )
    assert result.outcome is CapabilityOutcome.MISSING_INPUT
    assert result.finding is None


def test_profile_comparison_stale_version() -> None:
    capability = CompareResistanceProfiles(_repo())
    result = capability.execute(
        CompareProfilesQuery(
            incident_id=INCIDENT_1,
            isolate_id_a="ISO-001",
            isolate_id_b="ISO-002",
            requested_version=IncidentVersion(7),
        )
    )
    assert result.outcome is CapabilityOutcome.STALE_INCIDENT_VERSION
    assert result.finding is None


def test_profile_comparison_delegates_to_domain_owner() -> None:
    calls: list[tuple[CanonicalIsolate, CanonicalIsolate]] = []

    def spy(a: CanonicalIsolate, b: CanonicalIsolate) -> ProfileSimilarityFinding:
        calls.append((a, b))
        return compare_canonical_isolates(a, b)

    capability = CompareResistanceProfiles(_repo(), compare=spy)
    result = capability.execute(
        CompareProfilesQuery(incident_id=INCIDENT_1, isolate_id_a="ISO-001", isolate_id_b="ISO-002")
    )
    assert result.outcome is CapabilityOutcome.SUCCESS
    assert len(calls) == 1
    # Handler delegates to the scientific owner, not recompute:
    assert calls[0][0].isolate_id != calls[0][1].isolate_id


def test_baseline_summary_success_and_delegation() -> None:
    calls: list[dict[str, object]] = []

    def spy(
        *,
        organism_code: str,
        facility_id: str,
        ward: str,
        isolates: Sequence[CanonicalIsolate],
        window_end: date,
        config: SignalConfig | None,
    ) -> SignalEvaluationResult:
        calls.append(
            {
                "organism_code": organism_code,
                "facility_id": facility_id,
                "ward": ward,
                "window_end": window_end,
            }
        )
        return evaluate_cohort_signal(
            organism_code=organism_code,
            facility_id=facility_id,
            ward=ward,
            isolates=isolates,
            window_end=window_end,
            config=config,
        )

    capability = GetBaselineSummary(_repo(), evaluate_cohort=spy)
    result = capability.execute(
        GetBaselineSummaryQuery(
            incident_id=INCIDENT_1,
            organism_code=COHORT_ORG,
            facility_id=COHORT_FACILITY,
            ward=COHORT_WARD,
            requested_version=VERSION_1,
        )
    )
    assert result.outcome is CapabilityOutcome.SUCCESS
    assert result.signal_evaluation is not None
    assert result.signal_evaluation.organism_code == COHORT_ORG
    assert result.signal_evaluation.ward == COHORT_WARD
    assert len(calls) == 1
    assert calls[0]["window_end"] == WINDOW_END


def test_baseline_summary_missing_incident() -> None:
    capability = GetBaselineSummary(_repo())
    result = capability.execute(
        GetBaselineSummaryQuery(
            incident_id=IncidentId("INC-999"),
            organism_code=COHORT_ORG,
            facility_id=COHORT_FACILITY,
            ward=COHORT_WARD,
        )
    )
    assert result.outcome is CapabilityOutcome.INCIDENT_NOT_FOUND
    assert result.signal_evaluation is None


def test_missingness_success_with_no_material_absence() -> None:
    capability = AssessMaterialMissingness(_repo())
    result = capability.execute(AssessMissingnessQuery(incident_id=INCIDENT_1))
    assert result.outcome is CapabilityOutcome.SUCCESS
    assert result.has_material_missingness is False
    assert result.missing_items == ()


def test_missingness_missing_comparison_input() -> None:
    capability = AssessMaterialMissingness(_repo())
    result = capability.execute(
        AssessMissingnessQuery(
            incident_id=INCIDENT_1,
            required_isolate_ids=("ISO-001", "ISO-777"),
        )
    )
    assert result.outcome is CapabilityOutcome.SUCCESS
    assert result.has_material_missingness is True
    assert any(i.code is MissingnessCode.MISSING_COMPARISON_INPUT for i in result.missing_items)
    assert any(
        i.code is MissingnessCode.UNAVAILABLE_REQUIRED_BRANCH_RESULT
        for i in result.missing_items
    )


def test_missingness_order_independent() -> None:
    capability = AssessMaterialMissingness(_repo())
    ab = capability.execute(
        AssessMissingnessQuery(
            incident_id=INCIDENT_1,
            required_isolate_ids=("ISO-001", "ISO-777"),
        )
    )
    ba = capability.execute(
        AssessMissingnessQuery(
            incident_id=INCIDENT_1,
            required_isolate_ids=("ISO-777", "ISO-001"),
        )
    )
    assert ab.missing_items == ba.missing_items
    assert ab.has_material_missingness == ba.has_material_missingness


def test_missingness_missing_incident_is_material() -> None:
    capability = AssessMaterialMissingness(_repo())
    result = capability.execute(AssessMissingnessQuery(incident_id=IncidentId("INC-999")))
    assert result.outcome is CapabilityOutcome.INCIDENT_NOT_FOUND
    assert result.has_material_missingness is True
    assert result.missing_items


def test_missingness_stale_version_is_material() -> None:
    capability = AssessMaterialMissingness(_repo())
    result = capability.execute(
        AssessMissingnessQuery(incident_id=INCIDENT_1, requested_version=IncidentVersion(3))
    )
    assert result.outcome is CapabilityOutcome.STALE_INCIDENT_VERSION
    assert result.has_material_missingness is True


def test_immutability_of_context_and_results() -> None:
    context = _make_context(INCIDENT_1, version=VERSION_1, isolate_ids=("ISO-001", "ISO-002"))
    with pytest.raises(FrozenInstanceError):
        context.isolates = ()  # type: ignore[misc]
    isolate = context.isolates[0]
    with pytest.raises(FrozenInstanceError):
        isolate.isolate_id = "ISO-999"  # type: ignore[misc]
    result = InvestigationContextResult(
        outcome=CapabilityOutcome.SUCCESS,
        incident_id=context.incident_id,
        incident_version=context.incident_version,
        source_watermark=context.source_watermark,
        isolates=context.isolates,
        signal_config=context.signal_config,
        window_end=context.window_end,
    )
    with pytest.raises(FrozenInstanceError):
        result.isolates = ()  # type: ignore[misc]


def test_two_capabilities_share_context_without_mutation() -> None:
    repo = _repo()
    profile = CompareResistanceProfiles(repo)
    baseline = GetBaselineSummary(repo)
    profile_result = profile.execute(
        CompareProfilesQuery(incident_id=INCIDENT_1, isolate_id_a="ISO-001", isolate_id_b="ISO-002")
    )
    baseline_result = baseline.execute(
        GetBaselineSummaryQuery(
            incident_id=INCIDENT_1,
            organism_code=COHORT_ORG,
            facility_id=COHORT_FACILITY,
            ward=COHORT_WARD,
        )
    )
    assert profile_result.outcome is CapabilityOutcome.SUCCESS
    assert baseline_result.outcome is CapabilityOutcome.SUCCESS
