"""Unit tests for deterministic temporal and location concentration findings (Issue #46)."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from types import MappingProxyType

import pytest

from ngabo.domain.entities.ast_observation import AstObservation
from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.enums.concentration_status import (
    ConcentrationReason,
    ConcentrationStatus,
)
from ngabo.domain.enums.interpretation import Interpretation
from ngabo.domain.services.concentration_analysis import (
    compute_location_concentration_findings,
    compute_temporal_concentration_findings,
    evaluate_location_cohort,
)
from ngabo.domain.value_objects.concentration_config import (
    GOVERNED_CONFIG_VERSION,
    GOVERNED_LOCATION_ALGORITHM_VERSION,
    GOVERNED_POLICY_VERSION,
    GOVERNED_PRECISION,
    GOVERNED_TEMPORAL_ALGORITHM_VERSION,
    GOVERNED_WINDOW_DAYS,
    ConcentrationConfig,
)
from ngabo.domain.value_objects.location_concentration_finding import (
    LocationConcentrationFinding,
)
from ngabo.domain.value_objects.proof_references import (
    DeterministicFindingReference,
)
from ngabo.domain.value_objects.temporal_concentration_finding import (
    TemporalConcentrationFinding,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
HERO_JSON_PATH = REPO_ROOT / "data" / "synthetic" / "canonical_hero.json"


def _make_isolate(
    isolate_id: str,
    collection_date: date = date(2026, 8, 17),
    organism_code: str = "kle",
    organism_name: str = "Klebsiella pneumoniae",
    facility_id: str = "SYNTH-FACILITY-001",
    ward: str = "SYNTH-WARD-A",
) -> CanonicalIsolate:
    ast_dict = {
        "AMK": Interpretation.SUSCEPTIBLE,
        "CAZ": Interpretation.RESISTANT,
        "CIP": Interpretation.RESISTANT,
        "CRO": Interpretation.RESISTANT,
        "MEM": Interpretation.RESISTANT,
        "SXT": Interpretation.RESISTANT,
    }
    ast_obs = MappingProxyType(
        {code: AstObservation(interp) for code, interp in ast_dict.items()}
    )
    return CanonicalIsolate(
        isolate_id=isolate_id,
        collection_date=collection_date,
        organism_code=organism_code,
        organism_name=organism_name,
        facility_id=facility_id,
        lab_id="SYNTH-LAB-001",
        ward=ward,
        specimen_type="blood",
        patient_token=f"SYNTH-CASE-{isolate_id.replace('ISO-', '')}",
        source_import_id="SYNTH-IMPORT-001",
        ast_results=ast_obs,
    )


# ============================================================================
# 1. Window Boundary Semantics & Date Invariants
# ============================================================================


class TestWindowBoundarySemantics:
    def test_exact_window_start_included(self) -> None:
        # window_end: 2026-08-18 -> window_start: 2026-08-12
        window_end = date(2026, 8, 18)
        iso_start = _make_isolate("ISO-001", collection_date=date(2026, 8, 12))

        findings = compute_temporal_concentration_findings([iso_start], window_end)
        assert len(findings) == 1
        assert findings[0].facility_organism_count == 1
        assert findings[0].input_refs == ("ISO-001",)

    def test_one_day_before_window_start_excluded(self) -> None:
        window_end = date(2026, 8, 18)
        iso_before = _make_isolate("ISO-000", collection_date=date(2026, 8, 11))
        iso_in = _make_isolate("ISO-001", collection_date=date(2026, 8, 12))

        findings = compute_temporal_concentration_findings([iso_before, iso_in], window_end)
        assert len(findings) == 1
        assert findings[0].facility_organism_count == 1
        assert findings[0].input_refs == ("ISO-001",)

    def test_exact_window_end_included(self) -> None:
        window_end = date(2026, 8, 18)
        iso_end = _make_isolate("ISO-002", collection_date=date(2026, 8, 18))

        findings = compute_temporal_concentration_findings([iso_end], window_end)
        assert len(findings) == 1
        assert findings[0].facility_organism_count == 1
        assert findings[0].input_refs == ("ISO-002",)

    def test_one_day_after_window_end_excluded(self) -> None:
        window_end = date(2026, 8, 18)
        iso_after = _make_isolate("ISO-003", collection_date=date(2026, 8, 19))
        iso_in = _make_isolate("ISO-002", collection_date=date(2026, 8, 18))

        findings = compute_temporal_concentration_findings([iso_after, iso_in], window_end)
        assert len(findings) == 1
        assert findings[0].facility_organism_count == 1
        assert findings[0].input_refs == ("ISO-002",)

    def test_all_records_on_same_day(self) -> None:
        window_end = date(2026, 8, 18)
        iso_1 = _make_isolate("ISO-001", collection_date=date(2026, 8, 15))
        iso_2 = _make_isolate("ISO-002", collection_date=date(2026, 8, 15))

        findings = compute_temporal_concentration_findings([iso_1, iso_2], window_end)
        assert len(findings) == 1
        assert findings[0].facility_organism_count == 2
        assert findings[0].observed_min_date == date(2026, 8, 15)
        assert findings[0].observed_max_date == date(2026, 8, 15)
        assert findings[0].observed_span_days == 1

    def test_month_boundary_crossing(self) -> None:
        # window_end: 2026-08-03 -> window_start: 2026-07-28
        window_end = date(2026, 8, 3)
        iso_jul = _make_isolate("ISO-101", collection_date=date(2026, 7, 29))
        iso_aug = _make_isolate("ISO-102", collection_date=date(2026, 8, 2))

        findings = compute_temporal_concentration_findings([iso_jul, iso_aug], window_end)
        assert len(findings) == 1
        assert findings[0].facility_organism_count == 2
        assert findings[0].window_start == date(2026, 7, 28)
        assert findings[0].window_end == date(2026, 8, 3)
        assert findings[0].observed_span_days == 5

    def test_year_boundary_crossing(self) -> None:
        # window_end: 2027-01-03 -> window_start: 2026-12-28
        window_end = date(2027, 1, 3)
        iso_prev = _make_isolate("ISO-201", collection_date=date(2026, 12, 30))
        iso_next = _make_isolate("ISO-202", collection_date=date(2027, 1, 2))

        findings = compute_temporal_concentration_findings([iso_prev, iso_next], window_end)
        assert len(findings) == 1
        assert findings[0].facility_organism_count == 2
        assert findings[0].window_start == date(2026, 12, 28)
        assert findings[0].window_end == date(2027, 1, 3)
        assert findings[0].observed_span_days == 4

    def test_leap_year_crossing(self) -> None:
        # 2024 is a leap year; Feb has 29 days.
        # window_end: 2024-03-02 -> window_start: 2024-02-25
        window_end = date(2024, 3, 2)
        iso_leap = _make_isolate("ISO-301", collection_date=date(2024, 2, 29))
        iso_mar = _make_isolate("ISO-302", collection_date=date(2024, 3, 1))

        findings = compute_temporal_concentration_findings([iso_leap, iso_mar], window_end)
        assert len(findings) == 1
        assert findings[0].facility_organism_count == 2
        assert findings[0].observed_span_days == 2

    def test_window_end_rejects_datetime_with_timestamp(self) -> None:
        dt_end = datetime(2026, 8, 18, 12, 0, 0)
        with pytest.raises(TypeError, match="window_end must be an exact datetime.date"):
            compute_temporal_concentration_findings([], dt_end)

        with pytest.raises(TypeError, match="window_end must be an exact datetime.date"):
            compute_location_concentration_findings([], dt_end)


# ============================================================================
# 2. Temporal Concentration Policies & Descriptive Low-Count Measurement
# ============================================================================


class TestTemporalConcentration:
    def test_single_isolate_is_valid_success_measurement(self) -> None:
        # Crucial #46 rule: Issue #46 produces measurements; it does NOT enforce k=3.
        # A single isolate is a valid SUCCESS measurement.
        window_end = date(2026, 8, 18)
        iso = _make_isolate("ISO-001", collection_date=date(2026, 8, 17))

        findings = compute_temporal_concentration_findings([iso], window_end)
        assert len(findings) == 1
        f = findings[0]
        assert f.status == ConcentrationStatus.SUCCESS
        assert f.facility_organism_count == 1
        assert f.observed_min_date == date(2026, 8, 17)
        assert f.observed_max_date == date(2026, 8, 17)
        assert f.observed_span_days == 1
        assert f.input_refs == ("ISO-001",)
        assert f.output_value == "temporal_count=1;span_days=1;window_days=7"

    def test_two_isolates_is_valid_success_measurement(self) -> None:
        window_end = date(2026, 8, 18)
        iso_1 = _make_isolate("ISO-001", collection_date=date(2026, 8, 14))
        iso_2 = _make_isolate("ISO-002", collection_date=date(2026, 8, 17))

        findings = compute_temporal_concentration_findings([iso_1, iso_2], window_end)
        assert len(findings) == 1
        f = findings[0]
        assert f.status == ConcentrationStatus.SUCCESS
        assert f.facility_organism_count == 2
        assert f.observed_span_days == 4
        assert f.input_refs == ("ISO-001", "ISO-002")

    def test_grouping_by_organism_and_facility(self) -> None:
        window_end = date(2026, 8, 18)
        iso_kle_fac1 = _make_isolate("ISO-001", organism_code="kle", facility_id="FAC-1")
        iso_eco_fac1 = _make_isolate("ISO-002", organism_code="eco", facility_id="FAC-1")
        iso_kle_fac2 = _make_isolate("ISO-003", organism_code="kle", facility_id="FAC-2")

        findings = compute_temporal_concentration_findings(
            [iso_kle_fac1, iso_eco_fac1, iso_kle_fac2], window_end
        )
        assert len(findings) == 3
        # Sorted by (organism_code, facility_id)
        assert (findings[0].organism_code, findings[0].facility_id) == ("eco", "FAC-1")
        assert (findings[1].organism_code, findings[1].facility_id) == ("kle", "FAC-1")
        assert (findings[2].organism_code, findings[2].facility_id) == ("kle", "FAC-2")


# ============================================================================
# 3. Location Concentration Policies (Ward Share)
# ============================================================================


class TestLocationConcentration:
    def test_single_ward_yields_100_percent_ratio(self) -> None:
        window_end = date(2026, 8, 18)
        iso_1 = _make_isolate("ISO-001", ward="SYNTH-WARD-A")
        iso_2 = _make_isolate("ISO-002", ward="SYNTH-WARD-A")

        findings = compute_location_concentration_findings([iso_1, iso_2], window_end)
        assert len(findings) == 1
        f = findings[0]
        assert f.ward == "SYNTH-WARD-A"
        assert f.ward_organism_count == 2
        assert f.facility_organism_count == 2
        assert f.location_concentration_ratio == 1.0
        assert f.output_value == (
            "ward_share=1.0000;ward_count=2;facility_count=2;ward=SYNTH-WARD-A"
        )

    def test_two_wards_split_75_and_25(self) -> None:
        window_end = date(2026, 8, 18)
        # 3 in Ward A, 1 in Ward B
        isolates = [
            _make_isolate("ISO-001", ward="SYNTH-WARD-A"),
            _make_isolate("ISO-002", ward="SYNTH-WARD-A"),
            _make_isolate("ISO-003", ward="SYNTH-WARD-A"),
            _make_isolate("ISO-004", ward="SYNTH-WARD-B"),
        ]

        findings = compute_location_concentration_findings(isolates, window_end)
        assert len(findings) == 2

        f_a = findings[0]
        assert f_a.ward == "SYNTH-WARD-A"
        assert f_a.ward_organism_count == 3
        assert f_a.facility_organism_count == 4
        assert f_a.location_concentration_ratio == 0.7500
        assert f_a.ward_input_refs == ("ISO-001", "ISO-002", "ISO-003")
        assert f_a.facility_window_input_refs == ("ISO-001", "ISO-002", "ISO-003", "ISO-004")

        f_b = findings[1]
        assert f_b.ward == "SYNTH-WARD-B"
        assert f_b.ward_organism_count == 1
        assert f_b.facility_organism_count == 4
        assert f_b.location_concentration_ratio == 0.2500
        assert f_b.ward_input_refs == ("ISO-004",)
        assert f_b.facility_window_input_refs == ("ISO-001", "ISO-002", "ISO-003", "ISO-004")

    def test_equal_split_yields_exact_half(self) -> None:
        window_end = date(2026, 8, 18)
        isolates = [
            _make_isolate("ISO-001", ward="SYNTH-WARD-A"),
            _make_isolate("ISO-002", ward="SYNTH-WARD-B"),
        ]
        findings = compute_location_concentration_findings(isolates, window_end)
        assert len(findings) == 2
        assert findings[0].location_concentration_ratio == 0.5000
        assert findings[1].location_concentration_ratio == 0.5000

    def test_denominator_change_changes_finding_id(self) -> None:
        window_end = date(2026, 8, 18)
        # Baseline: 3 in Ward A only -> Ward A is 3/3 = 1.0000
        iso_a1 = _make_isolate("ISO-001", ward="SYNTH-WARD-A")
        iso_a2 = _make_isolate("ISO-002", ward="SYNTH-WARD-A")
        iso_a3 = _make_isolate("ISO-003", ward="SYNTH-WARD-A")
        findings_base = compute_location_concentration_findings(
            [iso_a1, iso_a2, iso_a3], window_end
        )

        # Contrast: adding ISO-004 in Ward B changes Ward A ratio to 3/4 = 0.7500
        iso_b1 = _make_isolate("ISO-004", ward="SYNTH-WARD-B")
        findings_expanded = compute_location_concentration_findings(
            [iso_a1, iso_a2, iso_a3, iso_b1], window_end
        )

        f_base_ward_a = findings_base[0]
        f_exp_ward_a = findings_expanded[0]

        assert f_base_ward_a.ward == f_exp_ward_a.ward == "SYNTH-WARD-A"
        assert f_base_ward_a.ward_organism_count == f_exp_ward_a.ward_organism_count == 3
        assert f_base_ward_a.facility_organism_count == 3
        assert f_exp_ward_a.facility_organism_count == 4
        assert (
            f_base_ward_a.location_concentration_ratio
            != f_exp_ward_a.location_concentration_ratio
        )
        assert f_base_ward_a.finding_id != f_exp_ward_a.finding_id

    def test_organism_grouping_prevents_denominator_contamination(self) -> None:
        window_end = date(2026, 8, 18)
        iso_kle = _make_isolate("ISO-001", organism_code="kle", ward="SYNTH-WARD-A")
        iso_eco = _make_isolate("ISO-002", organism_code="eco", ward="SYNTH-WARD-A")

        findings = compute_location_concentration_findings([iso_kle, iso_eco], window_end)
        assert len(findings) == 2
        # E. coli should have denominator=1, not 2
        assert findings[0].organism_code == "eco"
        assert findings[0].facility_organism_count == 1
        assert findings[0].location_concentration_ratio == 1.0000

        # Klebsiella should have denominator=1, not 2
        assert findings[1].organism_code == "kle"
        assert findings[1].facility_organism_count == 1
        assert findings[1].location_concentration_ratio == 1.0000

    def test_facility_grouping_prevents_cross_facility_contamination(self) -> None:
        window_end = date(2026, 8, 18)
        iso_fac1 = _make_isolate("ISO-001", facility_id="FAC-1", ward="SYNTH-WARD-A")
        iso_fac2 = _make_isolate("ISO-002", facility_id="FAC-2", ward="SYNTH-WARD-A")

        findings = compute_location_concentration_findings([iso_fac1, iso_fac2], window_end)
        assert len(findings) == 2
        assert findings[0].facility_id == "FAC-1"
        assert findings[0].facility_organism_count == 1
        assert findings[1].facility_id == "FAC-2"
        assert findings[1].facility_organism_count == 1

    def test_location_cohort_empty_denominator_yields_insufficient_data(self) -> None:
        window_end = date(2026, 8, 18)
        finding = evaluate_location_cohort(
            "kle", "FAC-999", "SYNTH-WARD-A", [], window_end
        )
        assert finding.status == ConcentrationStatus.INSUFFICIENT_DATA
        assert finding.reason == ConcentrationReason.EMPTY_DENOMINATOR
        assert finding.facility_organism_count == 0
        assert finding.location_concentration_ratio is None
        assert finding.input_refs == ()


# ============================================================================
# 4. Authoritative Input Authority & Proof-Carrying Reference Compatibility
# ============================================================================


class TestAuthoritativeInputAuthorityAndProofReference:
    def test_temporal_finding_reference_conversion(self) -> None:
        window_end = date(2026, 8, 18)
        iso_1 = _make_isolate("ISO-001")
        iso_2 = _make_isolate("ISO-002")

        findings = compute_temporal_concentration_findings([iso_1, iso_2], window_end)
        finding = findings[0]

        ref = finding.to_finding_reference()
        assert isinstance(ref, DeterministicFindingReference)
        assert ref.finding_id == finding.finding_id
        assert ref.policy_version == finding.policy_version
        assert ref.input_refs == ("ISO-001", "ISO-002")
        assert ref.output_value == finding.output_value

    def test_location_finding_reference_includes_all_denominator_records(self) -> None:
        # Non-negotiable Section 6 requirement:
        # Authoritative input_refs MUST include the union of all records materially used.
        # Even though Ward A has only ISO-001 and ISO-002, ISO-003 is in Ward B and materially
        # affected the ratio (from 2/2 to 2/3). It must be present in ref.input_refs.
        window_end = date(2026, 8, 18)
        iso_1 = _make_isolate("ISO-001", ward="SYNTH-WARD-A")
        iso_2 = _make_isolate("ISO-002", ward="SYNTH-WARD-A")
        iso_3 = _make_isolate("ISO-003", ward="SYNTH-WARD-B")

        findings = compute_location_concentration_findings(
            [iso_1, iso_2, iso_3], window_end
        )
        f_ward_a = findings[0]
        assert f_ward_a.ward == "SYNTH-WARD-A"
        assert f_ward_a.ward_input_refs == ("ISO-001", "ISO-002")
        assert f_ward_a.facility_window_input_refs == ("ISO-001", "ISO-002", "ISO-003")
        assert f_ward_a.input_refs == ("ISO-001", "ISO-002", "ISO-003")

        ref = f_ward_a.to_finding_reference()
        assert ref.input_refs == ("ISO-001", "ISO-002", "ISO-003")


# ============================================================================
# 5. Duplicate Safety & Conflict Handling
# ============================================================================


class TestDuplicateSafetyAndConflictHandling:
    def test_exact_value_identical_duplicate_collapses_idempotently(self) -> None:
        window_end = date(2026, 8, 18)
        iso_1 = _make_isolate("ISO-001")
        iso_1_dup = _make_isolate("ISO-001")

        findings = compute_temporal_concentration_findings([iso_1, iso_1_dup], window_end)
        assert len(findings) == 1
        assert findings[0].facility_organism_count == 1
        assert findings[0].input_refs == ("ISO-001",)

    def test_conflicting_same_id_fails_closed_in_temporal(self) -> None:
        window_end = date(2026, 8, 18)
        iso_1 = _make_isolate("ISO-001", ward="SYNTH-WARD-A")
        iso_1_conflict = _make_isolate("ISO-001", ward="SYNTH-WARD-B")

        with pytest.raises(
            ValueError, match="Conflicting CanonicalIsolate records for 'ISO-001'"
        ):
            compute_temporal_concentration_findings([iso_1, iso_1_conflict], window_end)

    def test_conflicting_same_id_fails_closed_in_location(self) -> None:
        window_end = date(2026, 8, 18)
        iso_1 = _make_isolate("ISO-001", collection_date=date(2026, 8, 15))
        iso_1_conflict = _make_isolate("ISO-001", collection_date=date(2026, 8, 16))

        with pytest.raises(
            ValueError, match="Conflicting CanonicalIsolate records for 'ISO-001'"
        ):
            compute_location_concentration_findings([iso_1, iso_1_conflict], window_end)

    def test_collection_order_independence(self) -> None:
        window_end = date(2026, 8, 18)
        iso_1 = _make_isolate("ISO-001", ward="SYNTH-WARD-A")
        iso_2 = _make_isolate("ISO-002", ward="SYNTH-WARD-B")
        iso_3 = _make_isolate("ISO-003", ward="SYNTH-WARD-A")

        forward_order = [iso_1, iso_2, iso_3]
        reverse_order = [iso_3, iso_2, iso_1]
        permuted_order = [iso_2, iso_3, iso_1]

        t_fwd = compute_temporal_concentration_findings(forward_order, window_end)
        t_rev = compute_temporal_concentration_findings(reverse_order, window_end)
        t_per = compute_temporal_concentration_findings(permuted_order, window_end)

        assert t_fwd == t_rev == t_per

        l_fwd = compute_location_concentration_findings(forward_order, window_end)
        l_rev = compute_location_concentration_findings(reverse_order, window_end)
        l_per = compute_location_concentration_findings(permuted_order, window_end)

        assert l_fwd == l_rev == l_per


# ============================================================================
# 6. Closed Policy Configuration & Runtime Invariants
# ============================================================================


class TestClosedPolicyConfiguration:
    def test_default_config_matches_governed_constants(self) -> None:
        cfg = ConcentrationConfig()
        assert cfg.policy_version == GOVERNED_POLICY_VERSION
        assert cfg.config_version == GOVERNED_CONFIG_VERSION
        assert cfg.temporal_algorithm_version == GOVERNED_TEMPORAL_ALGORITHM_VERSION
        assert cfg.location_algorithm_version == GOVERNED_LOCATION_ALGORITHM_VERSION
        assert cfg.window_days == GOVERNED_WINDOW_DAYS
        assert cfg.precision == GOVERNED_PRECISION

    def test_config_rejects_window_days_modification(self) -> None:
        with pytest.raises(ValueError, match="Unsupported window_days"):
            ConcentrationConfig(window_days=14)

    def test_config_rejects_precision_modification(self) -> None:
        with pytest.raises(ValueError, match="Unsupported precision"):
            ConcentrationConfig(precision=2)

    def test_config_rejects_policy_version_spoofing(self) -> None:
        with pytest.raises(ValueError, match="Unsupported policy_version"):
            ConcentrationConfig(policy_version="spoofed-v1")

    def test_config_rejects_config_version_spoofing(self) -> None:
        with pytest.raises(ValueError, match="Unsupported config_version"):
            ConcentrationConfig(config_version="spoofed-v1")

    def test_config_rejects_temporal_algorithm_spoofing(self) -> None:
        with pytest.raises(ValueError, match="Unsupported temporal_algorithm_version"):
            ConcentrationConfig(temporal_algorithm_version="spoofed-v1")

    def test_config_rejects_location_algorithm_spoofing(self) -> None:
        with pytest.raises(ValueError, match="Unsupported location_algorithm_version"):
            ConcentrationConfig(location_algorithm_version="spoofed-v1")

    def test_finding_immutability_and_validation(self) -> None:
        window_end = date(2026, 8, 18)
        iso = _make_isolate("ISO-001")
        findings = compute_temporal_concentration_findings([iso], window_end)
        f = findings[0]

        with pytest.raises(AttributeError):
            f.facility_organism_count = 99  # type: ignore[misc]

        # Invariant: input_refs must match facility_organism_count
        with pytest.raises(ValueError, match="must match len"):
            TemporalConcentrationFinding(
                finding_id=f.finding_id,
                policy_version=f.policy_version,
                algorithm_version=f.algorithm_version,
                config_version=f.config_version,
                organism_code=f.organism_code,
                facility_id=f.facility_id,
                window_start=f.window_start,
                window_end=f.window_end,
                facility_organism_count=99,
                input_refs=f.input_refs,
                observed_min_date=f.observed_min_date,
                observed_max_date=f.observed_max_date,
                observed_span_days=f.observed_span_days,
                status=f.status,
                output_value=f.output_value,
            )

        # Invariant: Location authoritative input_refs must equal facility_window_input_refs
        loc_findings = compute_location_concentration_findings([iso], window_end)
        lf = loc_findings[0]
        with pytest.raises(ValueError, match="must equal facility_window_input_refs"):
            LocationConcentrationFinding(
                finding_id=lf.finding_id,
                policy_version=lf.policy_version,
                algorithm_version=lf.algorithm_version,
                config_version=lf.config_version,
                organism_code=lf.organism_code,
                facility_id=lf.facility_id,
                ward=lf.ward,
                window_start=lf.window_start,
                window_end=lf.window_end,
                ward_organism_count=lf.ward_organism_count,
                facility_organism_count=lf.facility_organism_count,
                location_concentration_ratio=lf.location_concentration_ratio,
                ward_input_refs=lf.ward_input_refs,
                facility_window_input_refs=lf.facility_window_input_refs,
                input_refs=("ISO-OTHER",),
                status=lf.status,
                output_value=lf.output_value,
            )


# ============================================================================
# 7. Closed Policy Config Resolver Bypass Regressions (Section 3)
# ============================================================================


class _SubclassOverridingWindow(ConcentrationConfig):
    """Subclass attempting to alter window duration while inheriting valid metadata."""

    def calculate_window_start(self, window_end: date) -> date:
        from datetime import timedelta

        return window_end - timedelta(days=13)  # 14-day window


class _DuckConfigWindowDays14:
    """Duck-typed config object presenting valid versions but 14-day window."""

    def __init__(self) -> None:
        self.policy_version = GOVERNED_POLICY_VERSION
        self.config_version = GOVERNED_CONFIG_VERSION
        self.temporal_algorithm_version = GOVERNED_TEMPORAL_ALGORITHM_VERSION
        self.location_algorithm_version = GOVERNED_LOCATION_ALGORITHM_VERSION
        self.window_days = 14
        self.precision = GOVERNED_PRECISION

    def calculate_window_start(self, window_end: date) -> date:
        from datetime import timedelta

        return window_end - timedelta(days=13)


class _DuckConfigPrecision2:
    """Duck-typed config object presenting valid versions but precision=2."""

    def __init__(self) -> None:
        self.policy_version = GOVERNED_POLICY_VERSION
        self.config_version = GOVERNED_CONFIG_VERSION
        self.temporal_algorithm_version = GOVERNED_TEMPORAL_ALGORITHM_VERSION
        self.location_algorithm_version = GOVERNED_LOCATION_ALGORITHM_VERSION
        self.window_days = GOVERNED_WINDOW_DAYS
        self.precision = 2

    def calculate_window_start(self, window_end: date) -> date:
        from datetime import timedelta

        return window_end - timedelta(days=6)


_EXPECTED_CONFIG_ERROR = "config must be an exact validated ConcentrationConfig"


class TestClosedPolicyConfigResolverBypassRegressions:
    def test_none_config_succeeds_with_governed_default(self) -> None:
        window_end = date(2026, 8, 18)
        iso = _make_isolate("ISO-001")
        t_findings = compute_temporal_concentration_findings([iso], window_end, config=None)
        l_findings = compute_location_concentration_findings([iso], window_end, config=None)
        c_finding = evaluate_location_cohort(
            "kle", "SYNTH-FACILITY-001", "SYNTH-WARD-A", [iso], window_end, config=None
        )
        assert len(t_findings) == 1
        assert len(l_findings) == 1
        assert c_finding.status == ConcentrationStatus.SUCCESS

    def test_exact_config_instance_succeeds(self) -> None:
        window_end = date(2026, 8, 18)
        iso = _make_isolate("ISO-001")
        exact_cfg = ConcentrationConfig()
        t_findings = compute_temporal_concentration_findings([iso], window_end, config=exact_cfg)
        l_findings = compute_location_concentration_findings([iso], window_end, config=exact_cfg)
        c_finding = evaluate_location_cohort(
            "kle", "SYNTH-FACILITY-001", "SYNTH-WARD-A", [iso], window_end, config=exact_cfg
        )
        assert len(t_findings) == 1
        assert len(l_findings) == 1
        assert c_finding.status == ConcentrationStatus.SUCCESS

    def test_subclass_overriding_window_start_raises_type_error(self) -> None:
        window_end = date(2026, 8, 18)
        subclass_cfg = _SubclassOverridingWindow()
        with pytest.raises(TypeError, match=_EXPECTED_CONFIG_ERROR):
            compute_temporal_concentration_findings([], window_end, config=subclass_cfg)

        with pytest.raises(TypeError, match=_EXPECTED_CONFIG_ERROR):
            compute_location_concentration_findings([], window_end, config=subclass_cfg)

        with pytest.raises(TypeError, match=_EXPECTED_CONFIG_ERROR):
            evaluate_location_cohort("kle", "FAC-1", "WARD-A", [], window_end, config=subclass_cfg)

    def test_duck_config_window_days_14_raises_type_error(self) -> None:
        window_end = date(2026, 8, 18)
        duck_cfg = _DuckConfigWindowDays14()
        with pytest.raises(TypeError, match=_EXPECTED_CONFIG_ERROR):
            compute_temporal_concentration_findings(
                [], window_end, config=duck_cfg  # type: ignore[arg-type]
            )

    def test_duck_config_precision_2_raises_type_error(self) -> None:
        window_end = date(2026, 8, 18)
        duck_cfg = _DuckConfigPrecision2()
        with pytest.raises(TypeError, match=_EXPECTED_CONFIG_ERROR):
            compute_location_concentration_findings(
                [], window_end, config=duck_cfg  # type: ignore[arg-type]
            )

    def test_dict_config_raises_type_error(self) -> None:
        window_end = date(2026, 8, 18)
        dict_cfg = {
            "policy_version": GOVERNED_POLICY_VERSION,
            "config_version": GOVERNED_CONFIG_VERSION,
            "window_days": GOVERNED_WINDOW_DAYS,
            "precision": GOVERNED_PRECISION,
        }
        with pytest.raises(TypeError, match=_EXPECTED_CONFIG_ERROR):
            compute_temporal_concentration_findings(
                [], window_end, config=dict_cfg  # type: ignore[arg-type]
            )

    def test_arbitrary_object_raises_type_error(self) -> None:
        window_end = date(2026, 8, 18)
        with pytest.raises(TypeError, match=_EXPECTED_CONFIG_ERROR):
            compute_temporal_concentration_findings(
                [], window_end, config=object()  # type: ignore[arg-type]
            )

    def test_empty_compute_temporal_collection_with_spoof_config_raises_type_error(self) -> None:
        window_end = date(2026, 8, 18)
        spoof = _SubclassOverridingWindow()
        # Even with empty isolate list, spoofed config must be rejected before checking collection
        with pytest.raises(TypeError, match=_EXPECTED_CONFIG_ERROR):
            compute_temporal_concentration_findings([], window_end, config=spoof)

    def test_empty_compute_location_collection_with_spoof_config_raises_type_error(self) -> None:
        window_end = date(2026, 8, 18)
        spoof = _SubclassOverridingWindow()
        with pytest.raises(TypeError, match=_EXPECTED_CONFIG_ERROR):
            compute_location_concentration_findings([], window_end, config=spoof)

    def test_evaluate_location_cohort_with_spoof_config_raises_type_error(self) -> None:
        window_end = date(2026, 8, 18)
        spoof = _SubclassOverridingWindow()
        with pytest.raises(TypeError, match=_EXPECTED_CONFIG_ERROR):
            evaluate_location_cohort("kle", "FAC-1", "WARD-A", [], window_end, config=spoof)


# ============================================================================
# 8. Insufficient-Data Reason Invariants (Section 5)
# ============================================================================


class TestInsufficientDataReasonInvariants:
    def test_location_finding_insufficient_data_requires_empty_denominator_reason(self) -> None:
        # INSUFFICIENT_DATA without reason must fail closed
        with pytest.raises(
            ValueError,
            match="INSUFFICIENT_DATA status requires reason=ConcentrationReason.EMPTY_DENOMINATOR",
        ):
            LocationConcentrationFinding(
                finding_id="lconc-test",
                policy_version=GOVERNED_POLICY_VERSION,
                algorithm_version=GOVERNED_LOCATION_ALGORITHM_VERSION,
                config_version=GOVERNED_CONFIG_VERSION,
                organism_code="kle",
                facility_id="FAC-1",
                ward="WARD-A",
                window_start=date(2026, 8, 12),
                window_end=date(2026, 8, 18),
                ward_organism_count=0,
                facility_organism_count=0,
                location_concentration_ratio=None,
                ward_input_refs=(),
                facility_window_input_refs=(),
                input_refs=(),
                status=ConcentrationStatus.INSUFFICIENT_DATA,
                reason=None,
                output_value="status=INSUFFICIENT_DATA",
            )

    def test_location_finding_success_rejects_reason(self) -> None:
        with pytest.raises(ValueError, match="reason must be None on SUCCESS status"):
            LocationConcentrationFinding(
                finding_id="lconc-test",
                policy_version=GOVERNED_POLICY_VERSION,
                algorithm_version=GOVERNED_LOCATION_ALGORITHM_VERSION,
                config_version=GOVERNED_CONFIG_VERSION,
                organism_code="kle",
                facility_id="FAC-1",
                ward="WARD-A",
                window_start=date(2026, 8, 12),
                window_end=date(2026, 8, 18),
                ward_organism_count=1,
                facility_organism_count=1,
                location_concentration_ratio=1.0,
                ward_input_refs=("ISO-001",),
                facility_window_input_refs=("ISO-001",),
                input_refs=("ISO-001",),
                status=ConcentrationStatus.SUCCESS,
                reason=ConcentrationReason.EMPTY_DENOMINATOR,
                output_value="ward_share=1.0000;ward_count=1;facility_count=1;ward=WARD-A",
            )

    def test_temporal_finding_rejects_insufficient_data_status(self) -> None:
        # Section 4: Temporal concentration has no denominator; INSUFFICIENT_DATA is invalid
        with pytest.raises(
            ValueError,
            match="TemporalConcentrationFinding only supports ConcentrationStatus.SUCCESS in v0.1",
        ):
            TemporalConcentrationFinding(
                finding_id="tconc-test",
                policy_version=GOVERNED_POLICY_VERSION,
                algorithm_version=GOVERNED_TEMPORAL_ALGORITHM_VERSION,
                config_version=GOVERNED_CONFIG_VERSION,
                organism_code="kle",
                facility_id="FAC-1",
                window_start=date(2026, 8, 12),
                window_end=date(2026, 8, 18),
                facility_organism_count=0,
                input_refs=(),
                observed_min_date=None,
                observed_max_date=None,
                observed_span_days=None,
                status=ConcentrationStatus.INSUFFICIENT_DATA,
                reason=None,
                output_value="status=INSUFFICIENT_DATA",
            )

    def test_temporal_finding_rejects_reason(self) -> None:
        with pytest.raises(
            ValueError,
            match="reason must be None on TemporalConcentrationFinding",
        ):
            TemporalConcentrationFinding(
                finding_id="tconc-test",
                policy_version=GOVERNED_POLICY_VERSION,
                algorithm_version=GOVERNED_TEMPORAL_ALGORITHM_VERSION,
                config_version=GOVERNED_CONFIG_VERSION,
                organism_code="kle",
                facility_id="FAC-1",
                window_start=date(2026, 8, 12),
                window_end=date(2026, 8, 18),
                facility_organism_count=1,
                input_refs=("ISO-001",),
                observed_min_date=date(2026, 8, 15),
                observed_max_date=date(2026, 8, 15),
                observed_span_days=1,
                status=ConcentrationStatus.SUCCESS,
                reason=ConcentrationReason.EMPTY_DENOMINATOR,
                output_value="temporal_count=1;span_days=1;window_days=7",
            )


# ============================================================================
# 9. Hero Cluster Golden Tests
# ============================================================================


class TestHeroClusterGoldenFindings:
    @pytest.fixture
    def hero_records(self) -> dict[str, CanonicalIsolate]:
        json_data = json.loads(HERO_JSON_PATH.read_text(encoding="utf-8"))
        records: dict[str, CanonicalIsolate] = {}
        for r in json_data["records"]:
            d_parts = [int(p) for p in r["collection_date"].split("-")]
            cdate = date(d_parts[0], d_parts[1], d_parts[2])
            ast_dict = {
                code: AstObservation(Interpretation(entry["interpretation"]))
                for code, entry in r["ast_results"].items()
            }
            isolate = CanonicalIsolate(
                isolate_id=r["isolate_id"],
                collection_date=cdate,
                organism_code=r["organism_code"],
                organism_name=r["organism_name"],
                facility_id=r["facility_id"],
                lab_id=r["lab_id"],
                ward=r["ward"],
                specimen_type=r["specimen_type"],
                patient_token=r["patient_token"],
                source_import_id=r["source_import_id"],
                ast_results=MappingProxyType(ast_dict),
            )
            records[isolate.isolate_id] = isolate
        return records

    def test_hero_temporal_exact_result(
        self, hero_records: dict[str, CanonicalIsolate]
    ) -> None:
        window_end = date(2026, 8, 18)
        findings = compute_temporal_concentration_findings(
            list(hero_records.values()), window_end
        )

        # Filter to the hero Klebsiella finding
        kle_findings = [
            f
            for f in findings
            if f.organism_code == "kle" and f.facility_id == "SYNTH-FACILITY-001"
        ]
        assert len(kle_findings) == 1
        f = kle_findings[0]

        assert f.status == ConcentrationStatus.SUCCESS
        assert f.facility_organism_count == 4
        assert f.observed_min_date == date(2026, 8, 16)
        assert f.observed_max_date == date(2026, 8, 18)
        assert f.observed_span_days == 3
        assert f.input_refs == ("ISO-027", "ISO-031", "ISO-034", "ISO-039")
        assert f.output_value == "temporal_count=4;span_days=3;window_days=7"

    def test_hero_ward_a_exact_result(
        self, hero_records: dict[str, CanonicalIsolate]
    ) -> None:
        window_end = date(2026, 8, 18)
        findings = compute_location_concentration_findings(
            list(hero_records.values()), window_end
        )

        ward_a_findings = [
            f
            for f in findings
            if f.organism_code == "kle"
            and f.facility_id == "SYNTH-FACILITY-001"
            and f.ward == "SYNTH-WARD-A"
        ]
        assert len(ward_a_findings) == 1
        f = ward_a_findings[0]

        assert f.status == ConcentrationStatus.SUCCESS
        assert f.ward_organism_count == 3
        assert f.facility_organism_count == 4
        assert f.location_concentration_ratio == 0.7500
        assert f.ward_input_refs == ("ISO-031", "ISO-034", "ISO-039")
        assert f.facility_window_input_refs == (
            "ISO-027",
            "ISO-031",
            "ISO-034",
            "ISO-039",
        )
        assert f.input_refs == ("ISO-027", "ISO-031", "ISO-034", "ISO-039")
        assert f.output_value == (
            "ward_share=0.7500;ward_count=3;facility_count=4;ward=SYNTH-WARD-A"
        )

    def test_hero_ward_b_exact_result(
        self, hero_records: dict[str, CanonicalIsolate]
    ) -> None:
        window_end = date(2026, 8, 18)
        findings = compute_location_concentration_findings(
            list(hero_records.values()), window_end
        )

        ward_b_findings = [
            f
            for f in findings
            if f.organism_code == "kle"
            and f.facility_id == "SYNTH-FACILITY-001"
            and f.ward == "SYNTH-WARD-B"
        ]
        assert len(ward_b_findings) == 1
        f = ward_b_findings[0]

        assert f.status == ConcentrationStatus.SUCCESS
        assert f.ward_organism_count == 1
        assert f.facility_organism_count == 4
        assert f.location_concentration_ratio == 0.2500
        assert f.ward_input_refs == ("ISO-027",)
        assert f.facility_window_input_refs == (
            "ISO-027",
            "ISO-031",
            "ISO-034",
            "ISO-039",
        )
        assert f.input_refs == ("ISO-027", "ISO-031", "ISO-034", "ISO-039")
        assert f.output_value == (
            "ward_share=0.2500;ward_count=1;facility_count=4;ward=SYNTH-WARD-B"
        )

    def test_hero_pinned_literal_finding_ids(
        self, hero_records: dict[str, CanonicalIsolate]
    ) -> None:
        window_end = date(2026, 8, 18)
        t_findings = compute_temporal_concentration_findings(
            list(hero_records.values()), window_end
        )
        l_findings = compute_location_concentration_findings(
            list(hero_records.values()), window_end
        )

        kle_t = next(
            f
            for f in t_findings
            if f.organism_code == "kle" and f.facility_id == "SYNTH-FACILITY-001"
        )
        kle_ward_a = next(
            f
            for f in l_findings
            if f.organism_code == "kle"
            and f.facility_id == "SYNTH-FACILITY-001"
            and f.ward == "SYNTH-WARD-A"
        )
        kle_ward_b = next(
            f
            for f in l_findings
            if f.organism_code == "kle"
            and f.facility_id == "SYNTH-FACILITY-001"
            and f.ward == "SYNTH-WARD-B"
        )

        # Check prefixes
        assert kle_t.finding_id.startswith("tconc-")
        assert kle_ward_a.finding_id.startswith("lconc-")
        assert kle_ward_b.finding_id.startswith("lconc-")

        # Pinned literal golden IDs under canonical JSON serialization
        assert kle_t.finding_id == "tconc-ed312ddb0844c9ca"
        assert kle_ward_a.finding_id == "lconc-1d3ff528db1484f0"
        assert kle_ward_b.finding_id == "lconc-a50bd0596c86ed8e"
