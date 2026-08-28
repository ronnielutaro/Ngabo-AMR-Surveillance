"""Unit tests for deterministic resistance profile similarity findings (Issue #45)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from types import MappingProxyType

import pytest

from ngabo.domain.entities.ast_observation import AstObservation
from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.enums.interpretation import Interpretation
from ngabo.domain.enums.profile_similarity_status import ProfileSimilarityStatus
from ngabo.domain.services.resistance_profile_similarity import (
    compare_canonical_isolates,
    compare_isolate_collection,
)
from ngabo.domain.value_objects.profile_similarity_config import (
    ProfileSimilarityConfig,
)
from ngabo.domain.value_objects.profile_similarity_finding import (
    ProfileSimilarityFinding,
)
from ngabo.domain.value_objects.proof_references import (
    DeterministicFindingReference,
)
from ngabo.domain.value_objects.resistance_profile import ResistanceProfile

REPO_ROOT = Path(__file__).resolve().parents[3]
HERO_JSON_PATH = REPO_ROOT / "data" / "synthetic" / "canonical_hero.json"


def _make_isolate(
    isolate_id: str,
    organism_code: str = "kle",
    organism_name: str = "Klebsiella pneumoniae",
    ast_dict: dict[str, Interpretation] | None = None,
) -> CanonicalIsolate:
    default_ast = {
        "AMK": Interpretation.SUSCEPTIBLE,
        "CAZ": Interpretation.RESISTANT,
        "CIP": Interpretation.RESISTANT,
        "CRO": Interpretation.RESISTANT,
        "MEM": Interpretation.RESISTANT,
        "SXT": Interpretation.RESISTANT,
    }
    actual_ast = ast_dict if ast_dict is not None else default_ast
    ast_obs = MappingProxyType(
        {code: AstObservation(interp) for code, interp in actual_ast.items()}
    )
    return CanonicalIsolate(
        isolate_id=isolate_id,
        collection_date=date(2026, 8, 17),
        organism_code=organism_code,
        organism_name=organism_name,
        facility_id="SYNTH-FACILITY-001",
        lab_id="SYNTH-LAB-001",
        ward="SYNTH-WARD-A",
        specimen_type="blood",
        patient_token=f"SYNTH-CASE-{isolate_id.replace('ISO-', '')}",
        source_import_id="SYNTH-IMPORT-001",
        ast_results=ast_obs,
    )


# ============================================================================
# 1. Core Similarity Calculations & Interpretation Policies
# ============================================================================


class TestSimilarityCalculations:
    def test_identical_known_sir_profiles(self) -> None:
        iso_a = _make_isolate("ISO-001")
        iso_b = _make_isolate("ISO-002")

        finding = compare_canonical_isolates(iso_a, iso_b)

        assert finding.status == ProfileSimilarityStatus.SUCCESS
        assert finding.similarity_score == 1.0
        assert len(finding.comparable_antibiotics) == 6
        assert len(finding.matching_antibiotics) == 6
        assert len(finding.differing_antibiotics) == 0
        assert finding.output_value == "similarity=1.0000;matching=6;shared=6"

    def test_fully_different_known_sir_profiles(self) -> None:
        ast_a = {
            "AMK": Interpretation.RESISTANT,
            "CAZ": Interpretation.RESISTANT,
            "CIP": Interpretation.RESISTANT,
        }
        ast_b = {
            "AMK": Interpretation.SUSCEPTIBLE,
            "CAZ": Interpretation.INTERMEDIATE,
            "CIP": Interpretation.SUSCEPTIBLE,
        }
        iso_a = _make_isolate("ISO-001", ast_dict=ast_a)
        iso_b = _make_isolate("ISO-002", ast_dict=ast_b)

        finding = compare_canonical_isolates(iso_a, iso_b)

        assert finding.status == ProfileSimilarityStatus.SUCCESS
        assert finding.similarity_score == 0.0
        assert len(finding.comparable_antibiotics) == 3
        assert len(finding.matching_antibiotics) == 0
        assert len(finding.differing_antibiotics) == 3
        assert finding.output_value == "similarity=0.0000;matching=0;shared=3"

    def test_partially_overlapping_panels(self) -> None:
        # A has AMK, CAZ, CIP, CRO (4)
        # B has CIP, CRO, MEM, SXT (4)
        # Intersection has CIP, CRO (2 shared) -> default min=3 yields INSUFFICIENT_DATA
        ast_a = {
            "AMK": Interpretation.SUSCEPTIBLE,
            "CAZ": Interpretation.RESISTANT,
            "CIP": Interpretation.RESISTANT,
            "CRO": Interpretation.RESISTANT,
        }
        ast_b = {
            "CIP": Interpretation.RESISTANT,
            "CRO": Interpretation.RESISTANT,
            "MEM": Interpretation.RESISTANT,
            "SXT": Interpretation.RESISTANT,
        }
        iso_a = _make_isolate("ISO-001", ast_dict=ast_a)
        iso_b = _make_isolate("ISO-002", ast_dict=ast_b)

        finding = compare_canonical_isolates(iso_a, iso_b)
        assert finding.status == ProfileSimilarityStatus.INSUFFICIENT_DATA
        assert finding.similarity_score is None
        assert finding.comparable_antibiotics == ("CIP", "CRO")
        assert "min_required=3" in finding.output_value

        # With min_comparable=2, comparison succeeds on the 2 shared antibiotics
        cfg = ProfileSimilarityConfig(min_comparable_antibiotics=2)
        finding_2 = compare_canonical_isolates(iso_a, iso_b, cfg)
        assert finding_2.status == ProfileSimilarityStatus.SUCCESS
        assert finding_2.similarity_score == 1.0
        assert finding_2.comparable_antibiotics == ("CIP", "CRO")

    def test_disjoint_panels_yield_insufficient_data(self) -> None:
        ast_a = {
            "AMK": Interpretation.SUSCEPTIBLE,
            "CAZ": Interpretation.RESISTANT,
            "CIP": Interpretation.RESISTANT,
        }
        ast_b = {
            "CRO": Interpretation.RESISTANT,
            "MEM": Interpretation.RESISTANT,
            "SXT": Interpretation.RESISTANT,
        }
        iso_a = _make_isolate("ISO-001", ast_dict=ast_a)
        iso_b = _make_isolate("ISO-002", ast_dict=ast_b)

        finding = compare_canonical_isolates(iso_a, iso_b)
        assert finding.status == ProfileSimilarityStatus.INSUFFICIENT_DATA
        assert finding.similarity_score is None
        assert finding.comparable_antibiotics == ()
        assert finding.untested_or_unknown_antibiotics == (
            "AMK", "CAZ", "CIP", "CRO", "MEM", "SXT"
        )

    def test_unknown_observations_are_strictly_excluded_from_denominator(self) -> None:
        # 4 antibiotics tested: AMK, CAZ, CIP, CRO
        # In iso_a: CRO is UNKNOWN
        # In iso_b: CAZ is UNKNOWN
        # Shared known antibiotics: AMK and CIP (only 2)
        ast_a = {
            "AMK": Interpretation.SUSCEPTIBLE,
            "CAZ": Interpretation.RESISTANT,
            "CIP": Interpretation.RESISTANT,
            "CRO": Interpretation.UNKNOWN,
        }
        ast_b = {
            "AMK": Interpretation.SUSCEPTIBLE,
            "CAZ": Interpretation.UNKNOWN,
            "CIP": Interpretation.RESISTANT,
            "CRO": Interpretation.RESISTANT,
        }
        iso_a = _make_isolate("ISO-001", ast_dict=ast_a)
        iso_b = _make_isolate("ISO-002", ast_dict=ast_b)

        finding = compare_canonical_isolates(iso_a, iso_b)
        # Because 2 < min (3), fails closed as INSUFFICIENT_DATA
        assert finding.status == ProfileSimilarityStatus.INSUFFICIENT_DATA
        assert finding.similarity_score is None
        assert finding.comparable_antibiotics == ("AMK", "CIP")
        assert "CAZ" in finding.untested_or_unknown_antibiotics
        assert "CRO" in finding.untested_or_unknown_antibiotics

        # If a 5th antibiotic MEM is added (known in both), comparable count becomes 3
        ast_a["MEM"] = Interpretation.RESISTANT
        ast_b["MEM"] = Interpretation.RESISTANT
        iso_a5 = _make_isolate("ISO-001", ast_dict=ast_a)
        iso_b5 = _make_isolate("ISO-002", ast_dict=ast_b)

        finding_5 = compare_canonical_isolates(iso_a5, iso_b5)
        assert finding_5.status == ProfileSimilarityStatus.SUCCESS
        assert finding_5.comparable_antibiotics == ("AMK", "CIP", "MEM")
        assert finding_5.similarity_score == 1.0  # AMK, CIP, MEM all match
        assert finding_5.output_value == "similarity=1.0000;matching=3;shared=3"

    def test_untested_antibiotics_excluded_without_inventing_susceptibility(self) -> None:
        ast_a = {
            "AMK": Interpretation.SUSCEPTIBLE,
            "CAZ": Interpretation.RESISTANT,
            "CIP": Interpretation.RESISTANT,
            "CRO": Interpretation.RESISTANT,
        }
        ast_b = {
            "AMK": Interpretation.SUSCEPTIBLE,
            "CAZ": Interpretation.RESISTANT,
            "CIP": Interpretation.RESISTANT,
        }
        iso_a = _make_isolate("ISO-001", ast_dict=ast_a)
        iso_b = _make_isolate("ISO-002", ast_dict=ast_b)

        finding = compare_canonical_isolates(iso_a, iso_b)
        assert finding.status == ProfileSimilarityStatus.SUCCESS
        assert finding.comparable_antibiotics == ("AMK", "CAZ", "CIP")
        assert finding.similarity_score == 1.0
        assert finding.untested_or_unknown_antibiotics == ("CRO",)


# ============================================================================
# 2. Biological Compatibility, Symmetry, and Duplicate Inputs
# ============================================================================


class TestBiologicalAndSymmetricInvariants:
    def test_cross_organism_comparison_fails_closed_as_incompatible(self) -> None:
        iso_kle = _make_isolate(
            "ISO-001", organism_code="kle", organism_name="Klebsiella pneumoniae"
        )
        iso_eco = _make_isolate(
            "ISO-002", organism_code="eco", organism_name="Escherichia coli"
        )

        finding = compare_canonical_isolates(iso_kle, iso_eco)
        assert finding.status == ProfileSimilarityStatus.INCOMPATIBLE_ORGANISM
        assert finding.similarity_score is None
        assert finding.organism_code is None
        assert "status=INCOMPATIBLE_ORGANISM;org_a=kle;org_b=eco" in finding.output_value

    def test_self_comparison_yields_identical_inputs_status(self) -> None:
        iso_a = _make_isolate("ISO-001")

        finding = compare_canonical_isolates(iso_a, iso_a)
        assert finding.status == ProfileSimilarityStatus.IDENTICAL_INPUTS
        assert finding.similarity_score is None
        assert finding.output_value == "status=IDENTICAL_INPUTS;isolate_id=ISO-001"

    def test_symmetric_pair_ordering_invariance(self) -> None:
        iso_a = _make_isolate("ISO-001")
        iso_b = _make_isolate("ISO-002")

        finding_ab = compare_canonical_isolates(iso_a, iso_b)
        finding_ba = compare_canonical_isolates(iso_b, iso_a)

        assert finding_ab == finding_ba
        assert finding_ab.finding_id == finding_ba.finding_id
        assert finding_ab.input_refs == ("ISO-001", "ISO-002")
        assert finding_ba.input_refs == ("ISO-001", "ISO-002")

    def test_collection_pairwise_order_independence(self) -> None:
        iso_1 = _make_isolate("ISO-001")
        iso_2 = _make_isolate("ISO-002")
        iso_3 = _make_isolate("ISO-003")

        # Collection in forward order
        findings_123 = compare_isolate_collection([iso_1, iso_2, iso_3])
        # Collection in reverse order
        findings_321 = compare_isolate_collection([iso_3, iso_2, iso_1])
        # Collection with duplicates
        findings_dups = compare_isolate_collection([iso_2, iso_1, iso_2, iso_3, iso_1])

        assert len(findings_123) == 3
        assert findings_123 == findings_321
        assert findings_123 == findings_dups
        assert tuple(f.input_refs for f in findings_123) == (
            ("ISO-001", "ISO-002"),
            ("ISO-001", "ISO-003"),
            ("ISO-002", "ISO-003"),
        )


# ============================================================================
# 3. Determinism, Versioning, and ID Stability
# ============================================================================


class TestDeterminismAndVersioning:
    def test_repeated_runs_produce_identical_findings_and_ids(self) -> None:
        iso_a = _make_isolate("ISO-031")
        iso_b = _make_isolate("ISO-034")

        run1 = compare_canonical_isolates(iso_a, iso_b)
        run2 = compare_canonical_isolates(iso_a, iso_b)

        assert run1 == run2
        assert run1.finding_id == run2.finding_id
        assert run1.output_value == run2.output_value

    def test_material_ast_change_changes_finding_id_and_score(self) -> None:
        iso_a = _make_isolate("ISO-031")
        iso_b = _make_isolate("ISO-034")

        baseline_finding = compare_canonical_isolates(iso_a, iso_b)
        assert baseline_finding.similarity_score == 1.0

        # Change one antibiotic in iso_b
        mutated_ast = dict(iso_b.ast_results)
        mutated_ast["CAZ"] = AstObservation(Interpretation.SUSCEPTIBLE)
        iso_b_mutated = CanonicalIsolate(
            isolate_id=iso_b.isolate_id,
            collection_date=iso_b.collection_date,
            organism_code=iso_b.organism_code,
            organism_name=iso_b.organism_name,
            facility_id=iso_b.facility_id,
            lab_id=iso_b.lab_id,
            ward=iso_b.ward,
            specimen_type=iso_b.specimen_type,
            patient_token=iso_b.patient_token,
            source_import_id=iso_b.source_import_id,
            ast_results=MappingProxyType(mutated_ast),
        )

        mutated_finding = compare_canonical_isolates(iso_a, iso_b_mutated)
        assert mutated_finding.similarity_score == round(5 / 6, 4)
        assert mutated_finding.finding_id != baseline_finding.finding_id
        assert mutated_finding.output_value != baseline_finding.output_value

    def test_version_or_config_change_produces_distinguishable_finding_id(self) -> None:
        iso_a = _make_isolate("ISO-031")
        iso_b = _make_isolate("ISO-034")

        cfg1 = ProfileSimilarityConfig(config_version="min3-strict-org-v1")
        cfg2 = ProfileSimilarityConfig(
            config_version="min4-strict-org-v2", min_comparable_antibiotics=4
        )

        finding_v1 = compare_canonical_isolates(iso_a, iso_b, cfg1)
        finding_v2 = compare_canonical_isolates(iso_a, iso_b, cfg2)

        assert finding_v1.finding_id != finding_v2.finding_id
        assert finding_v1.config_version == "min3-strict-org-v1"
        assert finding_v2.config_version == "min4-strict-org-v2"

    def test_pinned_literal_golden_finding_id(self) -> None:
        iso_a = _make_isolate("ISO-031")
        iso_b = _make_isolate("ISO-034")

        finding = compare_canonical_isolates(iso_a, iso_b)

        # Pin the exact literal finding ID to detect any unintended serialization drift
        assert finding.finding_id == "psim-ce8df2b52d2ed9ae"
        assert finding.policy_version == "ngabo-profile-sim-v1"
        assert finding.algorithm_version == "exact-ratio-v1"
        assert finding.config_version == "min3-strict-org-v1"
        assert finding.output_value == "similarity=1.0000;matching=6;shared=6"


# ============================================================================
# 4. Hero Cluster Golden Test (ISO-031, ISO-034, ISO-039)
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

    def test_hero_triad_produces_identical_phenotype_findings(
        self, hero_records: dict[str, CanonicalIsolate]
    ) -> None:
        iso_31 = hero_records["ISO-031"]
        iso_34 = hero_records["ISO-034"]
        iso_39 = hero_records["ISO-039"]

        f_31_34 = compare_canonical_isolates(iso_31, iso_34)
        f_31_39 = compare_canonical_isolates(iso_31, iso_39)
        f_34_39 = compare_canonical_isolates(iso_34, iso_39)

        for f in (f_31_34, f_31_39, f_34_39):
            assert f.status == ProfileSimilarityStatus.SUCCESS
            assert f.similarity_score == 1.0
            assert f.comparable_antibiotics == ("AMK", "CAZ", "CIP", "CRO", "MEM", "SXT")
            assert f.matching_antibiotics == ("AMK", "CAZ", "CIP", "CRO", "MEM", "SXT")
            assert f.differing_antibiotics == ()
            assert f.output_value == "similarity=1.0000;matching=6;shared=6"

    def test_hero_cluster_distinguishable_from_contrast_klebsiella(
        self, hero_records: dict[str, CanonicalIsolate]
    ) -> None:
        iso_31 = hero_records["ISO-031"]
        iso_27 = hero_records["ISO-027"]  # Klebsiella pneumoniae contrast in Ward B

        finding = compare_canonical_isolates(iso_31, iso_27)
        assert finding.status == ProfileSimilarityStatus.SUCCESS
        assert finding.similarity_score == round(2 / 6, 4)  # AMK=S and CIP=R match
        assert finding.matching_antibiotics == ("AMK", "CIP")
        assert finding.differing_antibiotics == ("CAZ", "CRO", "MEM", "SXT")
        assert finding.output_value == "similarity=0.3333;matching=2;shared=6"

    def test_hero_cluster_distinguishable_from_other_organisms(
        self, hero_records: dict[str, CanonicalIsolate]
    ) -> None:
        iso_31 = hero_records["ISO-031"]  # kle
        iso_12 = hero_records["ISO-012"]  # eco
        iso_52 = hero_records["ISO-052"]  # pae

        f_eco = compare_canonical_isolates(iso_31, iso_12)
        assert f_eco.status == ProfileSimilarityStatus.INCOMPATIBLE_ORGANISM
        assert f_eco.similarity_score is None

        f_pae = compare_canonical_isolates(iso_31, iso_52)
        assert f_pae.status == ProfileSimilarityStatus.INCOMPATIBLE_ORGANISM
        assert f_pae.similarity_score is None


# ============================================================================
# 5. Proof-Carrying Reference Compatibility
# ============================================================================


class TestProofCarryingReferenceCompatibility:
    def test_finding_converts_directly_to_deterministic_finding_reference(
        self,
    ) -> None:
        iso_a = _make_isolate("ISO-031")
        iso_b = _make_isolate("ISO-034")

        finding = compare_canonical_isolates(iso_a, iso_b)
        ref = finding.to_finding_reference()

        assert isinstance(ref, DeterministicFindingReference)
        assert ref.finding_id == finding.finding_id
        assert ref.policy_version == finding.policy_version
        assert ref.input_refs == ("ISO-031", "ISO-034")
        assert ref.output_value == finding.output_value
        assert not any(ws in ref.finding_id for ws in (" ", "\t", "\n"))
        assert not any(ws in ref.output_value for ws in ("\t", "\n"))


# ============================================================================
# 6. Value Object Invariants and Immutability
# ============================================================================


class TestValueObjectInvariants:
    def test_config_invariants(self) -> None:
        with pytest.raises(ValueError, match="algorithm_version"):
            ProfileSimilarityConfig(algorithm_version="")

        with pytest.raises(ValueError, match="config_version"):
            ProfileSimilarityConfig(config_version=" ")

        with pytest.raises(ValueError, match="min_comparable_antibiotics"):
            ProfileSimilarityConfig(min_comparable_antibiotics=0)

        with pytest.raises(TypeError, match="strict_organism_match"):
            ProfileSimilarityConfig(strict_organism_match="yes")  # type: ignore[arg-type]

    def test_resistance_profile_immutability(self) -> None:
        iso = _make_isolate("ISO-001")
        prof = ResistanceProfile.from_canonical_isolate(iso)

        with pytest.raises(AttributeError):
            prof.isolate_id = "ISO-002"  # type: ignore[misc]

        with pytest.raises(TypeError):
            prof.observations["AMK"] = Interpretation.RESISTANT  # type: ignore[index]

    def test_finding_immutability_and_validation(self) -> None:
        iso_a = _make_isolate("ISO-001")
        iso_b = _make_isolate("ISO-002")
        finding = compare_canonical_isolates(iso_a, iso_b)

        with pytest.raises(AttributeError):
            finding.similarity_score = 0.5  # type: ignore[misc]

        # Success with None score rejected
        with pytest.raises(ValueError, match="similarity_score must be a float"):
            ProfileSimilarityFinding(
                finding_id="f-1",
                policy_version="pol-1",
                algorithm_version="alg-1",
                config_version="cfg-1",
                isolate_id_a="ISO-001",
                isolate_id_b="ISO-002",
                input_refs=("ISO-001", "ISO-002"),
                organism_code="kle",
                status=ProfileSimilarityStatus.SUCCESS,
                comparable_antibiotics=("AMK",),
                matching_antibiotics=("AMK",),
                differing_antibiotics=(),
                untested_or_unknown_antibiotics=(),
                similarity_score=None,
                output_value="sim=1.0",
            )
