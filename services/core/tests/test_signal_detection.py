"""Comprehensive deterministic unit tests for investigation-priority signal detection (Issue #47).

Validates:
- Maintainer-approved Ngabo v0.1 Prototype Investigation-Priority Signal Policy (ADR 0012);
- Exact score 0.9375 on canonical hero;
- Exactly one emitted signal candidate on canonical hero;
- Structural gate (k >= 3) and inclusive threshold (>= 0.7500);
- Fail-closed behavior on missing material data or invalid baseline config;
- Cryptographic signal ID stability with material calculation parameter binding;
- Independent recomputability of scores and decisions from persisted signal objects;
- Explicit normal-baseline acceptance proof yielding zero signals;
- Value object input validation hardening (finite floats within bounds);
- Exact proof-reference generation.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from types import MappingProxyType

import pytest

from ngabo.domain.entities.ast_observation import AstObservation
from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.enums.interpretation import Interpretation
from ngabo.domain.enums.signal_status import SignalReason, SignalStatus
from ngabo.domain.services.signal_detection import (
    _compute_signal_id,
    _resolve_governed_config,
    evaluate_cohort_signal,
    evaluate_surveillance_signals,
    recompute_signal_score,
)
from ngabo.domain.value_objects.investigation_priority_signal import (
    InvestigationPrioritySignal,
    SignalComponents,
)
from ngabo.domain.value_objects.proof_references import DeterministicFindingReference
from ngabo.domain.value_objects.signal_config import SignalConfig

REPO_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_HERO_PATH = REPO_ROOT / "data" / "synthetic" / "canonical_hero.json"


def _load_hero_isolates() -> list[CanonicalIsolate]:
    with open(CANONICAL_HERO_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return [
        CanonicalIsolate(
            isolate_id=r["isolate_id"],
            collection_date=date.fromisoformat(r["collection_date"]),
            organism_code=r["organism_code"],
            organism_name=r["organism_name"],
            facility_id=r["facility_id"],
            lab_id=r["lab_id"],
            ward=r["ward"],
            specimen_type=r["specimen_type"],
            patient_token=r["patient_token"],
            source_import_id=r["source_import_id"],
            ast_results=MappingProxyType(
                {
                    ab: AstObservation(Interpretation(ast["interpretation"]))
                    for ab, ast in r["ast_results"].items()
                }
            ),
        )
        for r in data["records"]
    ]


def _make_isolate(
    isolate_id: str,
    collection_date: date,
    organism_code: str = "kle",
    facility_id: str = "SYNTH-FACILITY-001",
    ward: str = "SYNTH-WARD-A",
    ast_results: dict[str, str] | None = None,
) -> CanonicalIsolate:
    if ast_results is None:
        raw_ast = {
            "AMK": "S",
            "CAZ": "R",
            "CIP": "R",
            "CRO": "R",
            "MEM": "R",
            "SXT": "R",
        }
    else:
        raw_ast = ast_results
    return CanonicalIsolate(
        isolate_id=isolate_id,
        collection_date=collection_date,
        organism_code=organism_code,
        organism_name="Klebsiella pneumoniae" if organism_code == "kle" else "Other",
        facility_id=facility_id,
        lab_id="SYNTH-LAB-001",
        ward=ward,
        specimen_type="blood",
        patient_token=f"PAT-{isolate_id}",
        source_import_id="SYNTH-IMPORT-001",
        ast_results=MappingProxyType(
            {code: AstObservation(Interpretation(interp)) for code, interp in raw_ast.items()}
        ),
    )


def _make_normal_baseline_isolates() -> list[CanonicalIsolate]:
    """Generate a realistic normal surveillance baseline with routine sporadic isolates.

    Includes 11 isolates across 4 wards and 4 organisms over the 7-day window:
    - 8 sporadic isolates across Wards A, B, C (all k=1 < 3);
    - 3 E. coli isolates in Ward D with divergent AST phenotypes yielding low score.
    None of the cohorts qualify as high-priority clusters.
    """
    sporadic = [
        _make_isolate("ISO-801", date(2026, 8, 13), organism_code="eco", ward="SYNTH-WARD-A"),
        _make_isolate("ISO-802", date(2026, 8, 14), organism_code="sau", ward="SYNTH-WARD-A"),
        _make_isolate("ISO-803", date(2026, 8, 15), organism_code="pae", ward="SYNTH-WARD-B"),
        _make_isolate("ISO-804", date(2026, 8, 15), organism_code="kle", ward="SYNTH-WARD-B"),
        _make_isolate("ISO-805", date(2026, 8, 16), organism_code="eco", ward="SYNTH-WARD-C"),
        _make_isolate("ISO-806", date(2026, 8, 16), organism_code="sau", ward="SYNTH-WARD-C"),
        _make_isolate("ISO-807", date(2026, 8, 17), organism_code="pae", ward="SYNTH-WARD-A"),
        _make_isolate("ISO-808", date(2026, 8, 18), organism_code="eco", ward="SYNTH-WARD-B"),
    ]
    # 3 E. coli in Ward D with divergent resistance profiles (low phenotype similarity)
    divergent_ward_d = [
        _make_isolate(
            "ISO-809",
            date(2026, 8, 14),
            organism_code="eco",
            ward="SYNTH-WARD-D",
            ast_results={"AMK": "R", "CAZ": "R", "CIP": "R"},
        ),
        _make_isolate(
            "ISO-810",
            date(2026, 8, 15),
            organism_code="eco",
            ward="SYNTH-WARD-D",
            ast_results={"AMK": "S", "CAZ": "S", "CIP": "S"},
        ),
        _make_isolate(
            "ISO-811",
            date(2026, 8, 16),
            organism_code="eco",
            ward="SYNTH-WARD-D",
            ast_results={"AMK": "I", "CAZ": "I", "CIP": "I"},
        ),
    ]
    return sporadic + divergent_ward_d


class TestCanonicalHeroSignal:
    """Core tests against committed canonical synthetic hero dataset."""

    def test_canonical_hero_emits_exactly_one_signal(self) -> None:
        isolates = _load_hero_isolates()
        window_end = date(2026, 8, 18)

        signals = evaluate_surveillance_signals(isolates, window_end)

        assert len(signals) == 1
        signal = signals[0]
        assert signal.organism_code == "kle"
        assert signal.facility_id == "SYNTH-FACILITY-001"
        assert signal.ward == "SYNTH-WARD-A"
        assert signal.status == SignalStatus.TRIGGERED
        assert signal.reason == SignalReason.HIGH_PRIORITY_CLUSTER

    def test_canonical_hero_score_is_exactly_governed_value(self) -> None:
        isolates = _load_hero_isolates()
        window_end = date(2026, 8, 18)

        signals = evaluate_surveillance_signals(isolates, window_end)
        assert len(signals) == 1
        signal = signals[0]

        # Components:
        # c_phenotype = 1.0000
        # c_location = 0.7500
        # c_temporal = 1.0000
        # c_baseline = 1.0000
        assert signal.components.c_phenotype == 1.0000
        assert signal.components.c_location == 0.7500
        assert signal.components.c_temporal == 1.0000
        assert signal.components.c_baseline == 1.0000

        # Score: 0.35(1.0) + 0.25(0.75) + 0.20(1.0) + 0.20(1.0) = 0.9375
        assert signal.signal_score == 0.9375
        assert signal.trigger_threshold == 0.7500
        assert signal.ward_organism_count == 3
        assert signal.facility_organism_count == 4

    def test_canonical_hero_signal_identity_is_stable(self) -> None:
        isolates = _load_hero_isolates()
        window_end = date(2026, 8, 18)

        signals = evaluate_surveillance_signals(isolates, window_end)
        assert len(signals) == 1
        signal = signals[0]

        # Cryptographic identity bound to all material data and calculation parameters
        assert signal.signal_id == "sig-c4180061263e7207"
        # Run again and ensure exact identity match
        signals_repeat = evaluate_surveillance_signals(isolates, window_end)
        assert signals_repeat[0].signal_id == signal.signal_id

    def test_persisted_policy_config_on_emitted_signal(self) -> None:
        isolates = _load_hero_isolates()
        window_end = date(2026, 8, 18)

        signal = evaluate_surveillance_signals(isolates, window_end)[0]
        assert isinstance(signal.policy_config, SignalConfig)

        # Directly accessible material parameters
        assert signal.w_phenotype == 0.35
        assert signal.w_location == 0.25
        assert signal.w_temporal == 0.20
        assert signal.w_baseline == 0.20
        assert signal.min_candidate_count == 3
        assert signal.configured_synthetic_baseline_count == 1.0
        assert signal.baseline_saturation_multiplier == 3.0
        assert signal.trigger_threshold == 0.7500
        assert signal.precision == 4

    def test_repeated_evaluation_produces_identical_output(self) -> None:
        isolates = _load_hero_isolates()
        window_end = date(2026, 8, 18)

        run1 = evaluate_surveillance_signals(isolates, window_end)
        run2 = evaluate_surveillance_signals(isolates, window_end)
        assert run1 == run2

    def test_version_identifiers_carried_as_required(self) -> None:
        isolates = _load_hero_isolates()
        signal = evaluate_surveillance_signals(isolates, date(2026, 8, 18))[0]
        assert signal.policy_version == "ngabo-signal-v1"
        assert signal.config_version == "signal-win7d-org-facility-ward-v1"
        assert signal.algorithm_version == "composite-priority-v1"

    def test_canonical_hero_proof_reference(self) -> None:
        isolates = _load_hero_isolates()
        window_end = date(2026, 8, 18)

        signals = evaluate_surveillance_signals(isolates, window_end)
        signal = signals[0]

        ref = signal.to_finding_reference()
        assert isinstance(ref, DeterministicFindingReference)
        assert ref.finding_id == signal.signal_id
        assert ref.policy_version == "ngabo-signal-v1"
        assert ref.input_refs == signal.supporting_finding_refs
        assert ref.output_value == signal.output_value

        # Must reference #46 temporal finding (tconc-...) and location finding (lconc-...)
        # and #45 similarity findings (psim-...)
        assert any(r.startswith("tconc-") for r in ref.input_refs)
        assert any(r.startswith("lconc-") for r in ref.input_refs)
        assert any(r.startswith("psim-") for r in ref.input_refs)
        assert signal.supporting_isolate_refs == ("ISO-031", "ISO-034", "ISO-039")


class TestIndependentRecomputation:
    """Tests proving results are independently recomputable from persisted values."""

    def test_recompute_score_from_persisted_signal_matches_exactly(self) -> None:
        isolates = _load_hero_isolates()
        window_end = date(2026, 8, 18)

        signal = evaluate_surveillance_signals(isolates, window_end)[0]

        # 1. Instance method recomputation
        recomputed_score = signal.recompute_score()
        assert recomputed_score == signal.signal_score
        assert recomputed_score == 0.9375

        # 2. Pure function recomputation from components and persisted config
        fn_score = recompute_signal_score(signal.components, signal.policy_config)
        assert fn_score == signal.signal_score
        assert fn_score == 0.9375

        # 3. Trigger decision verification
        assert signal.verify_trigger_decision() is True

    def test_non_triggering_result_explains_decision_with_persisted_config(self) -> None:
        isolates = _load_hero_isolates()
        window_end = date(2026, 8, 18)

        # Single isolate in Ward B -> below candidate count
        res = evaluate_cohort_signal(
            "kle", "SYNTH-FACILITY-001", "SYNTH-WARD-B", isolates, window_end
        )
        assert res.status == SignalStatus.NO_SIGNAL
        assert res.reason == SignalReason.INSUFFICIENT_CLUSTER_SIZE
        assert res.ward_organism_count < res.policy_config.min_candidate_count
        assert res.policy_config.min_candidate_count == 3
        assert res.signal is None

        # Divergent resistance profiles -> below priority threshold
        iso1 = _make_isolate(
            "ISO-001", date(2026, 8, 15), ast_results={"AMK": "R", "CAZ": "R", "CIP": "R"}
        )
        iso2 = _make_isolate(
            "ISO-002", date(2026, 8, 16), ast_results={"AMK": "S", "CAZ": "S", "CIP": "S"}
        )
        iso3 = _make_isolate(
            "ISO-003", date(2026, 8, 17), ast_results={"AMK": "I", "CAZ": "I", "CIP": "I"}
        )
        divergent_res = evaluate_cohort_signal(
            "kle", "SYNTH-FACILITY-001", "SYNTH-WARD-A", [iso1, iso2, iso3], window_end
        )
        assert divergent_res.status == SignalStatus.NO_SIGNAL
        assert divergent_res.reason == SignalReason.BELOW_PRIORITY_THRESHOLD
        assert divergent_res.signal_score is not None
        assert divergent_res.signal_score < divergent_res.policy_config.trigger_threshold
        assert divergent_res.policy_config.trigger_threshold == 0.7500


class TestNormalBaselineAcceptance:
    """Acceptance tests demonstrating normal baseline scenario yields zero signals."""

    def test_normal_baseline_produces_zero_signals(self) -> None:
        normal_baseline = _make_normal_baseline_isolates()
        window_end = date(2026, 8, 18)

        signals = evaluate_surveillance_signals(normal_baseline, window_end)
        assert signals == ()

    def test_normal_baseline_cohorts_evaluate_to_no_signal_with_explicit_reasons(self) -> None:
        normal_baseline = _make_normal_baseline_isolates()
        window_end = date(2026, 8, 18)

        # Inspect distinct cohorts in the normal baseline
        for ward in ("SYNTH-WARD-A", "SYNTH-WARD-B", "SYNTH-WARD-C"):
            res = evaluate_cohort_signal(
                "eco", "SYNTH-FACILITY-001", ward, normal_baseline, window_end
            )
            assert res.status == SignalStatus.NO_SIGNAL
            assert res.reason == SignalReason.INSUFFICIENT_CLUSTER_SIZE
            assert res.signal is None

        # Inspect the 3-isolate Ward D cohort
        res_ward_d = evaluate_cohort_signal(
            "eco", "SYNTH-FACILITY-001", "SYNTH-WARD-D", normal_baseline, window_end
        )
        assert res_ward_d.status == SignalStatus.NO_SIGNAL
        assert res_ward_d.reason == SignalReason.BELOW_PRIORITY_THRESHOLD
        assert res_ward_d.signal is None

    def test_normal_baseline_vs_canonical_hero_acceptance(self) -> None:
        normal_baseline = _make_normal_baseline_isolates()
        hero_isolates = _load_hero_isolates()
        window_end = date(2026, 8, 18)

        normal_signals = evaluate_surveillance_signals(normal_baseline, window_end)
        hero_signals = evaluate_surveillance_signals(hero_isolates, window_end)

        # Normal baseline: 0 signals
        assert len(normal_signals) == 0

        # Canonical hero: exactly 1 signal at 0.9375
        assert len(hero_signals) == 1
        assert hero_signals[0].signal_score == 0.9375
        assert hero_signals[0].signal_id == "sig-c4180061263e7207"


class TestContrastAndStructuralGate:
    """Tests verifying that non-qualifying cohorts do not trigger."""

    def test_single_isolate_groups_do_not_trigger(self) -> None:
        iso = _make_isolate("ISO-001", date(2026, 8, 15))
        signals = evaluate_surveillance_signals([iso], date(2026, 8, 18))
        assert signals == ()

        result = evaluate_cohort_signal(
            "kle", "SYNTH-FACILITY-001", "SYNTH-WARD-A", [iso], date(2026, 8, 18)
        )
        assert result.status == SignalStatus.NO_SIGNAL
        assert result.reason == SignalReason.INSUFFICIENT_CLUSTER_SIZE
        assert result.signal is None

    def test_two_isolate_groups_do_not_trigger(self) -> None:
        iso1 = _make_isolate("ISO-001", date(2026, 8, 15))
        iso2 = _make_isolate("ISO-002", date(2026, 8, 16))
        signals = evaluate_surveillance_signals([iso1, iso2], date(2026, 8, 18))
        assert signals == ()

        result = evaluate_cohort_signal(
            "kle", "SYNTH-FACILITY-001", "SYNTH-WARD-A", [iso1, iso2], date(2026, 8, 18)
        )
        assert result.status == SignalStatus.NO_SIGNAL
        assert result.reason == SignalReason.INSUFFICIENT_CLUSTER_SIZE
        assert result.signal is None

    def test_hero_contrast_groups_produce_zero_candidates(self) -> None:
        isolates = _load_hero_isolates()
        window_end = date(2026, 8, 18)

        # Ward B Klebsiella (ISO-027 only)
        ward_b_kle = evaluate_cohort_signal(
            "kle", "SYNTH-FACILITY-001", "SYNTH-WARD-B", isolates, window_end
        )
        assert ward_b_kle.status == SignalStatus.NO_SIGNAL
        assert ward_b_kle.reason == SignalReason.INSUFFICIENT_CLUSTER_SIZE
        assert ward_b_kle.signal is None

        # Ward A Pseudomonas (ISO-052 only)
        ward_a_pae = evaluate_cohort_signal(
            "pae", "SYNTH-FACILITY-001", "SYNTH-WARD-A", isolates, window_end
        )
        assert ward_a_pae.status == SignalStatus.NO_SIGNAL
        assert ward_a_pae.reason == SignalReason.INSUFFICIENT_CLUSTER_SIZE

        # Ward A E. coli (ISO-071 only)
        ward_a_eco = evaluate_cohort_signal(
            "eco", "SYNTH-FACILITY-001", "SYNTH-WARD-A", isolates, window_end
        )
        assert ward_a_eco.status == SignalStatus.NO_SIGNAL
        assert ward_a_eco.reason == SignalReason.INSUFFICIENT_CLUSTER_SIZE


class TestThresholdAndScoringEdgeCases:
    """Tests boundary thresholds, missing data, and math constraints."""

    def test_production_decision_triggers_on_exact_threshold_equality(self) -> None:
        """Executable regression coverage proving signal_score >= trigger_threshold triggers."""
        # 14 antimicrobials: 9 identical (R), 5 differing across 3 isolates
        # Yields pairwise similarities 9/14 = 0.6429, c_pheno = 0.6429
        # 3 in Ward A, 3 in Ward B -> facility total 6
        # c_loc = 3/6 = 0.5000, c_temp = 1.0000, c_base = 1.0000
        # raw = 0.35 * 0.6429 + 0.25 * 0.5000 + 0.20 * 1.0000 + 0.20 * 1.0000 = 0.750015 -> 0.7500
        shared_9 = {
            "AMK": "R",
            "CAZ": "R",
            "CIP": "R",
            "CRO": "R",
            "MEM": "R",
            "FEP": "R",
            "TZP": "R",
            "SXT": "R",
            "CST": "R",
        }
        iso1_ast = {**shared_9, "LVX": "R", "TOB": "R", "TGC": "R", "CHL": "R", "ATM": "R"}
        iso2_ast = {**shared_9, "LVX": "S", "TOB": "S", "TGC": "S", "CHL": "S", "ATM": "S"}
        iso3_ast = {**shared_9, "LVX": "I", "TOB": "I", "TGC": "I", "CHL": "I", "ATM": "I"}

        ward_a_isolates = [
            _make_isolate("ISO-701", date(2026, 8, 15), ward="SYNTH-WARD-A", ast_results=iso1_ast),
            _make_isolate("ISO-702", date(2026, 8, 16), ward="SYNTH-WARD-A", ast_results=iso2_ast),
            _make_isolate("ISO-703", date(2026, 8, 17), ward="SYNTH-WARD-A", ast_results=iso3_ast),
        ]
        # 3 isolates in Wards B, C, D to make facility total 6 while keeping other wards at k=1
        other_ward_isolates = [
            _make_isolate("ISO-704", date(2026, 8, 15), ward="SYNTH-WARD-B"),
            _make_isolate("ISO-705", date(2026, 8, 15), ward="SYNTH-WARD-C"),
            _make_isolate("ISO-706", date(2026, 8, 15), ward="SYNTH-WARD-D"),
        ]
        all_isolates = ward_a_isolates + other_ward_isolates

        # Test cohort evaluation directly
        res = evaluate_cohort_signal(
            "kle", "SYNTH-FACILITY-001", "SYNTH-WARD-A", all_isolates, date(2026, 8, 18)
        )
        assert res.status == SignalStatus.TRIGGERED
        assert res.signal_score == 0.7500
        assert res.signal is not None
        assert res.signal.signal_score == 0.7500
        assert res.signal.trigger_threshold == 0.7500
        assert res.signal.ward_organism_count == 3

        # Test full surveillance pipeline emits the candidate
        signals = evaluate_surveillance_signals(all_isolates, date(2026, 8, 18))
        assert len(signals) == 1
        assert signals[0].signal_score == 0.7500
        assert signals[0].status == SignalStatus.TRIGGERED

    def test_production_decision_does_not_trigger_just_below_threshold(self) -> None:
        """8/14 matching antimicrobials yields score 0.7250 < 0.7500 and fails to trigger."""
        shared_8 = {
            "AMK": "R",
            "CAZ": "R",
            "CIP": "R",
            "CRO": "R",
            "MEM": "R",
            "FEP": "R",
            "TZP": "R",
            "SXT": "R",
        }
        # 6 differing antimicrobials -> sim = 8/14 = 0.5714 -> score = 0.7250
        iso1_ast = {
            **shared_8,
            "CST": "R",
            "LVX": "R",
            "TOB": "R",
            "TGC": "R",
            "CHL": "R",
            "ATM": "R",
        }
        iso2_ast = {
            **shared_8,
            "CST": "S",
            "LVX": "S",
            "TOB": "S",
            "TGC": "S",
            "CHL": "S",
            "ATM": "S",
        }
        iso3_ast = {
            **shared_8,
            "CST": "I",
            "LVX": "I",
            "TOB": "I",
            "TGC": "I",
            "CHL": "I",
            "ATM": "I",
        }

        ward_a_isolates = [
            _make_isolate("ISO-711", date(2026, 8, 15), ward="SYNTH-WARD-A", ast_results=iso1_ast),
            _make_isolate("ISO-712", date(2026, 8, 16), ward="SYNTH-WARD-A", ast_results=iso2_ast),
            _make_isolate("ISO-713", date(2026, 8, 17), ward="SYNTH-WARD-A", ast_results=iso3_ast),
        ]
        other_ward_isolates = [
            _make_isolate("ISO-714", date(2026, 8, 15), ward="SYNTH-WARD-B"),
            _make_isolate("ISO-715", date(2026, 8, 15), ward="SYNTH-WARD-C"),
            _make_isolate("ISO-716", date(2026, 8, 15), ward="SYNTH-WARD-D"),
        ]
        all_isolates = ward_a_isolates + other_ward_isolates

        res = evaluate_cohort_signal(
            "kle", "SYNTH-FACILITY-001", "SYNTH-WARD-A", all_isolates, date(2026, 8, 18)
        )
        assert res.status == SignalStatus.NO_SIGNAL
        assert res.reason == SignalReason.BELOW_PRIORITY_THRESHOLD
        assert res.signal_score == 0.7250
        assert res.signal is None

        signals = evaluate_surveillance_signals(all_isolates, date(2026, 8, 18))
        assert signals == ()

    def test_score_exactly_equal_to_threshold_triggers_inclusively(self) -> None:
        comp = SignalComponents(
            c_phenotype=0.6429,
            c_location=0.5000,
            c_temporal=1.0000,
            c_baseline=1.0000,
        )
        score = round(0.35 * 0.6429 + 0.25 * 0.5000 + 0.20 * 1.0000 + 0.20 * 1.0000, 4)
        assert score == 0.7500

        sig = InvestigationPrioritySignal(
            signal_id="sig-0123456789abcdef",
            policy_version="ngabo-signal-v1",
            algorithm_version="composite-priority-v1",
            config_version="signal-win7d-org-facility-ward-v1",
            organism_code="kle",
            facility_id="SYNTH-FACILITY-001",
            ward="SYNTH-WARD-A",
            window_start=date(2026, 8, 12),
            window_end=date(2026, 8, 18),
            ward_organism_count=3,
            facility_organism_count=6,
            components=comp,
            signal_score=score,
            trigger_threshold=0.7500,
            status=SignalStatus.TRIGGERED,
            reason=SignalReason.HIGH_PRIORITY_CLUSTER,
            supporting_finding_refs=("tconc-1", "lconc-1", "psim-1"),
            supporting_isolate_refs=("ISO-001", "ISO-002", "ISO-003"),
            output_value="signal_score=0.7500",
            policy_config=SignalConfig(),
        )
        assert sig.signal_score >= sig.trigger_threshold
        assert sig.status == SignalStatus.TRIGGERED

    def test_insufficient_phenotype_evidence_fails_closed(self) -> None:
        iso1 = _make_isolate("ISO-001", date(2026, 8, 15), ast_results={"AMK": "R"})
        iso2 = _make_isolate("ISO-002", date(2026, 8, 16), ast_results={"CAZ": "R"})
        iso3 = _make_isolate("ISO-003", date(2026, 8, 17), ast_results={"CIP": "R"})

        signals = evaluate_surveillance_signals([iso1, iso2, iso3], date(2026, 8, 18))
        assert signals == ()

        result = evaluate_cohort_signal(
            "kle", "SYNTH-FACILITY-001", "SYNTH-WARD-A", [iso1, iso2, iso3], date(2026, 8, 18)
        )
        assert result.status == SignalStatus.INSUFFICIENT_DATA
        assert result.reason == SignalReason.INSUFFICIENT_PHENOTYPE_EVIDENCE
        assert result.signal is None

    def test_missing_required_material_input_does_not_renormalize_weights(self) -> None:
        iso1 = _make_isolate("ISO-001", date(2026, 8, 15), ast_results={"AMK": "R"})
        iso2 = _make_isolate("ISO-002", date(2026, 8, 16), ast_results={"CAZ": "R"})
        iso3 = _make_isolate("ISO-003", date(2026, 8, 17), ast_results={"CIP": "R"})

        result = evaluate_cohort_signal(
            "kle", "SYNTH-FACILITY-001", "SYNTH-WARD-A", [iso1, iso2, iso3], date(2026, 8, 18)
        )
        assert result.status == SignalStatus.INSUFFICIENT_DATA
        assert result.signal_score is None
        assert result.components is None

    def test_materially_different_semantics_produce_different_signal_id(self) -> None:
        kwargs = {
            "policy_version": "ngabo-signal-v1",
            "config_version": "signal-win7d-org-facility-ward-v1",
            "algorithm_version": "composite-priority-v1",
            "precision": 4,
            "facility_id": "SYNTH-FACILITY-001",
            "ward": "SYNTH-WARD-A",
            "organism_code": "kle",
            "window_start": date(2026, 8, 12),
            "window_end": date(2026, 8, 18),
            "ward_organism_count": 3,
            "facility_organism_count": 4,
            "c_phenotype": 1.0,
            "c_location": 0.75,
            "c_temporal": 1.0,
            "c_baseline": 1.0,
            "signal_score": 0.9375,
            "trigger_threshold": 0.7500,
            "w_phenotype": 0.35,
            "w_location": 0.25,
            "w_temporal": 0.20,
            "w_baseline": 0.20,
            "min_candidate_count": 3,
            "configured_synthetic_baseline_count": 1.0,
            "baseline_saturation_multiplier": 3.0,
            "status": SignalStatus.TRIGGERED,
            "supporting_finding_refs": ["tconc-1", "lconc-1"],
            "supporting_isolate_refs": ["ISO-031", "ISO-034", "ISO-039"],
            "output_value": "out1",
        }
        id1 = _compute_signal_id(**kwargs)  # type: ignore[arg-type]

        # Mutate score
        kwargs2 = dict(kwargs, signal_score=0.9025)
        id2 = _compute_signal_id(**kwargs2)  # type: ignore[arg-type]
        assert id1 != id2

        # Mutate weight
        kwargs3 = dict(kwargs, w_phenotype=0.40)
        id3 = _compute_signal_id(**kwargs3)  # type: ignore[arg-type]
        assert id1 != id3

        # Mutate baseline count
        kwargs4 = dict(kwargs, configured_synthetic_baseline_count=2.0)
        id4 = _compute_signal_id(**kwargs4)  # type: ignore[arg-type]
        assert id1 != id4


class TestValueObjectHardening:
    """Tests verifying finite values and strict boundary validation."""

    def test_components_reject_non_finite_and_out_of_bounds(self) -> None:
        for bad_val in (float("nan"), float("inf"), float("-inf"), -0.1, 1.01):
            with pytest.raises(ValueError, match="within"):
                SignalComponents(
                    c_phenotype=bad_val, c_location=0.5, c_temporal=0.5, c_baseline=0.5
                )

    def test_investigation_priority_signal_rejects_non_finite_score(self) -> None:
        comp = SignalComponents(c_phenotype=1.0, c_location=1.0, c_temporal=1.0, c_baseline=1.0)
        for bad_score in (float("nan"), float("inf"), float("-inf"), -0.01, 1.01):
            with pytest.raises(ValueError, match="signal_score must be finite and within"):
                InvestigationPrioritySignal(
                    signal_id="sig-0123456789abcdef",
                    policy_version="ngabo-signal-v1",
                    algorithm_version="composite-priority-v1",
                    config_version="signal-win7d-org-facility-ward-v1",
                    organism_code="kle",
                    facility_id="SYNTH-FACILITY-001",
                    ward="SYNTH-WARD-A",
                    window_start=date(2026, 8, 12),
                    window_end=date(2026, 8, 18),
                    ward_organism_count=3,
                    facility_organism_count=4,
                    components=comp,
                    signal_score=bad_score,
                    trigger_threshold=0.7500,
                    status=SignalStatus.TRIGGERED,
                    reason=SignalReason.HIGH_PRIORITY_CLUSTER,
                    supporting_finding_refs=("tconc-1",),
                    supporting_isolate_refs=("ISO-001", "ISO-002", "ISO-003"),
                    output_value="out",
                    policy_config=SignalConfig(),
                )

    def test_investigation_priority_signal_rejects_non_finite_trigger_threshold(self) -> None:
        comp = SignalComponents(c_phenotype=1.0, c_location=1.0, c_temporal=1.0, c_baseline=1.0)
        for bad_thresh in (float("nan"), float("inf"), float("-inf"), -0.1, 1.1):
            with pytest.raises(ValueError, match="trigger_threshold must be finite and within"):
                InvestigationPrioritySignal(
                    signal_id="sig-0123456789abcdef",
                    policy_version="ngabo-signal-v1",
                    algorithm_version="composite-priority-v1",
                    config_version="signal-win7d-org-facility-ward-v1",
                    organism_code="kle",
                    facility_id="SYNTH-FACILITY-001",
                    ward="SYNTH-WARD-A",
                    window_start=date(2026, 8, 12),
                    window_end=date(2026, 8, 18),
                    ward_organism_count=3,
                    facility_organism_count=4,
                    components=comp,
                    signal_score=0.9375,
                    trigger_threshold=bad_thresh,
                    status=SignalStatus.TRIGGERED,
                    reason=SignalReason.HIGH_PRIORITY_CLUSTER,
                    supporting_finding_refs=("tconc-1",),
                    supporting_isolate_refs=("ISO-001", "ISO-002", "ISO-003"),
                    output_value="out",
                    policy_config=SignalConfig(),
                )

    def test_policy_config_mismatch_fails_closed(self) -> None:
        comp = SignalComponents(c_phenotype=1.0, c_location=1.0, c_temporal=1.0, c_baseline=1.0)
        with pytest.raises(ValueError, match="policy_version does not match"):
            InvestigationPrioritySignal(
                signal_id="sig-0123456789abcdef",
                policy_version="different-policy-version",
                algorithm_version="composite-priority-v1",
                config_version="signal-win7d-org-facility-ward-v1",
                organism_code="kle",
                facility_id="SYNTH-FACILITY-001",
                ward="SYNTH-WARD-A",
                window_start=date(2026, 8, 12),
                window_end=date(2026, 8, 18),
                ward_organism_count=3,
                facility_organism_count=4,
                components=comp,
                signal_score=0.9375,
                trigger_threshold=0.7500,
                status=SignalStatus.TRIGGERED,
                reason=SignalReason.HIGH_PRIORITY_CLUSTER,
                supporting_finding_refs=("tconc-1",),
                supporting_isolate_refs=("ISO-001", "ISO-002", "ISO-003"),
                output_value="out",
                policy_config=SignalConfig(),
            )


class TestConfigAndGovernanceInvariants:
    """Tests governing configuration, bypass prevention, and versioning."""

    def test_default_config_matches_governed_constants(self) -> None:
        cfg = SignalConfig()
        assert cfg.policy_version == "ngabo-signal-v1"
        assert cfg.config_version == "signal-win7d-org-facility-ward-v1"
        assert cfg.algorithm_version == "composite-priority-v1"
        assert cfg.window_days == 7
        assert cfg.precision == 4
        assert cfg.min_candidate_count == 3
        assert cfg.trigger_threshold == 0.7500
        assert cfg.configured_synthetic_baseline_count == 1.0
        assert cfg.w_phenotype == 0.35
        assert cfg.w_location == 0.25
        assert cfg.w_temporal == 0.20
        assert cfg.w_baseline == 0.20
        assert cfg.baseline_saturation_multiplier == 3.0

    def test_config_rejects_spoofed_versions_or_parameters(self) -> None:
        with pytest.raises(ValueError, match="Unsupported policy_version"):
            SignalConfig(policy_version="custom-policy")

        with pytest.raises(ValueError, match="Unsupported trigger_threshold"):
            SignalConfig(trigger_threshold=0.5000)

        with pytest.raises(ValueError, match="Unsupported configured_synthetic_baseline_count"):
            SignalConfig(configured_synthetic_baseline_count=-1.0)

        with pytest.raises(ValueError, match="Unsupported configured_synthetic_baseline_count"):
            SignalConfig(configured_synthetic_baseline_count=0.0)

    def test_config_rejects_non_finite_values(self) -> None:
        for bad_val in (float("nan"), float("inf"), float("-inf")):
            with pytest.raises(ValueError, match="must be a finite float"):
                SignalConfig(trigger_threshold=bad_val)

    def test_resolver_rejects_subclasses_duck_types_and_mappings(self) -> None:
        class SubConfig(SignalConfig):
            pass

        sub = SubConfig()
        with pytest.raises(TypeError, match="exact validated SignalConfig"):
            _resolve_governed_config(sub)

        class DuckConfig:
            policy_version = "ngabo-signal-v1"

        with pytest.raises(TypeError, match="exact validated SignalConfig"):
            _resolve_governed_config(DuckConfig())  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="exact validated SignalConfig"):
            _resolve_governed_config({"policy_version": "ngabo-signal-v1"})  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="exact validated SignalConfig"):
            _resolve_governed_config("invalid")  # type: ignore[arg-type]

    def test_entry_points_guard_against_config_bypass(self) -> None:
        class SubConfig(SignalConfig):
            pass

        isolates = _load_hero_isolates()
        with pytest.raises(TypeError, match="exact validated SignalConfig"):
            evaluate_surveillance_signals(isolates, date(2026, 8, 18), config=SubConfig())

        with pytest.raises(TypeError, match="exact validated SignalConfig"):
            evaluate_cohort_signal(
                "kle",
                "SYNTH-FACILITY-001",
                "SYNTH-WARD-A",
                isolates,
                date(2026, 8, 18),
                config=SubConfig(),
            )


class TestInputHandlingAndDeterminism:
    """Tests duplicate handling, ordering invariance, and non-clinical nomenclature."""

    def test_reordered_inputs_produce_identical_signal_id(self) -> None:
        isolates = _load_hero_isolates()
        window_end = date(2026, 8, 18)

        sig1 = evaluate_surveillance_signals(isolates, window_end)[0]
        sig2 = evaluate_surveillance_signals(list(reversed(isolates)), window_end)[0]

        assert sig1.signal_id == sig2.signal_id
        assert sig1.signal_score == sig2.signal_score
        assert sig1.supporting_finding_refs == sig2.supporting_finding_refs
        assert sig1.supporting_isolate_refs == sig2.supporting_isolate_refs

    def test_duplicate_identical_records_collapse_idempotently(self) -> None:
        isolates = _load_hero_isolates()
        window_end = date(2026, 8, 18)

        # Duplicate every isolate
        doubled = isolates + isolates
        signals = evaluate_surveillance_signals(doubled, window_end)
        assert len(signals) == 1
        expected_id = evaluate_surveillance_signals(isolates, window_end)[0].signal_id
        assert signals[0].signal_id == expected_id

    def test_conflicting_duplicate_isolate_fails_closed(self) -> None:
        isolates = _load_hero_isolates()
        window_end = date(2026, 8, 18)

        # Mutate one isolate with same ID but different ward
        conflicting = _make_isolate("ISO-031", date(2026, 8, 17), ward="SYNTH-WARD-CONFLICT")

        with pytest.raises(ValueError, match="Conflicting duplicate isolate_id"):
            evaluate_surveillance_signals(isolates + [conflicting], window_end)

    def test_non_date_window_end_raises_type_error(self) -> None:
        isolates = _load_hero_isolates()
        with pytest.raises(TypeError, match="window_end must be an exact datetime.date"):
            evaluate_surveillance_signals(isolates, "2026-08-18")  # type: ignore[arg-type]

    def test_non_clinical_nomenclature_invariant(self) -> None:
        """Verify no output or method claims outbreak probability or clinical diagnosis."""
        isolates = _load_hero_isolates()
        signal = evaluate_surveillance_signals(isolates, date(2026, 8, 18))[0]

        forbidden = [
            "outbreak",
            "diagnosis",
            "probability",
            "confidence",
            "treatment",
            "prescribing",
        ]
        output_str = signal.output_value.lower()
        for word in forbidden:
            assert word not in output_str

        ref = signal.to_finding_reference()
        for word in forbidden:
            assert word not in ref.output_value.lower()
