"""Comprehensive release-gate certification tests for offline hero surveillance (Issue #48).

Certifies from clean committed input that the complete deterministic pipeline
produces one reproducible, referenceable surveillance signal without model, cloud,
network, or human intervention.

Primary Invariant: The certified output is strictly an INVESTIGATION_PRIORITY_SIGNAL.
It is NEVER an outbreak declaration, outbreak probability, diagnosis, model confidence,
clinical decision, or prescribing/treatment guidance.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pytest

from ngabo.application.commands.certify_offline_hero_command import (
    CertifyOfflineHeroCommand,
)
from ngabo.application.enums.import_outcome_disposition import ImportOutcomeDisposition
from ngabo.application.value_objects.offline_hero_certification_result import (
    GOVERNED_HERO_COMPONENTS,
    GOVERNED_HERO_RAW_DIGEST,
    GOVERNED_HERO_SCORE,
    GOVERNED_HERO_SIGNAL_ID,
    GOVERNED_HERO_WATERMARK,
    OfflineHeroCertificationResult,
)
from ngabo.bootstrap.certify_hero import create_offline_hero_use_case, main
from ngabo.domain.enums.signal_status import SignalReason, SignalStatus
from ngabo.domain.value_objects.proof_references import DeterministicFindingReference
from ngabo.infrastructure.repositories.in_memory_source_replay_repository import (
    InMemorySourceReplayRepository,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
HERO_CSV_PATH = REPO_ROOT / "data" / "synthetic" / "canonical_hero.csv"
HERO_CERTIFICATION_JSON_PATH = (
    REPO_ROOT / "data" / "synthetic" / "canonical_hero_certification.json"
)

SPORADIC_NORMAL_BASELINE_CSV = (
    b"ISOLATE_ID,COLLECTION_DATE,ORGANISM_CODE,ORGANISM_NAME,"
    b"FACILITY_ID,LAB_ID,WARD,SPECIMEN_TYPE,PATIENT_TOKEN,SOURCE_IMPORT_ID,AMK,CAZ,CIP\n"
    b"ISO-801,2026-08-13,eco,Escherichia coli,"
    b"SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-801,SYNTH-IMPORT-001,S,S,S\n"
    b"ISO-802,2026-08-14,eco,Escherichia coli,"
    b"SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,blood,SYNTH-CASE-802,SYNTH-IMPORT-001,S,S,S\n"
    b"ISO-803,2026-08-15,kle,Klebsiella pneumoniae,"
    b"SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-B,urine,SYNTH-CASE-803,SYNTH-IMPORT-001,S,S,S\n"
    b"ISO-804,2026-08-16,kle,Klebsiella pneumoniae,"
    b"SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-B,blood,SYNTH-CASE-804,SYNTH-IMPORT-001,S,S,S\n"
    b"ISO-805,2026-08-14,pae,Pseudomonas aeruginosa,"
    b"SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-C,sputum,SYNTH-CASE-805,SYNTH-IMPORT-001,S,S,S\n"
    b"ISO-806,2026-08-17,pae,Pseudomonas aeruginosa,"
    b"SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-C,wound,SYNTH-CASE-806,SYNTH-IMPORT-001,S,S,S\n"
    b"ISO-807,2026-08-15,ecl,Enterobacter cloacae,"
    b"SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-D,blood,SYNTH-CASE-807,SYNTH-IMPORT-001,S,S,S\n"
    b"ISO-808,2026-08-18,ecl,Enterobacter cloacae,"
    b"SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-D,urine,SYNTH-CASE-808,SYNTH-IMPORT-001,S,S,S\n"
)


class InMemoryCustomLoader:
    """In-memory loader helper for test scenarios."""

    def __init__(self, sources: dict[str, bytes]) -> None:
        self._sources = dict(sources)

    def __call__(self, location: str) -> bytes:
        if location not in self._sources:
            raise FileNotFoundError(f"Source not found: {location!r}")
        return self._sources[location]


# ============================================================================
# 1. Clean Hero Run & Golden Certification Proof
# ============================================================================


class TestCanonicalHeroReleaseCertification:
    """Core certification tests proving the end-to-end hero outcome from committed CSV."""

    def test_clean_hero_run_produces_exact_certified_result(self) -> None:
        use_case = create_offline_hero_use_case()
        cmd = CertifyOfflineHeroCommand(source_location=str(HERO_CSV_PATH))
        result = use_case.execute(cmd)

        # 1. Primary certification flags
        assert result.certified is True
        assert result.verify_hero_expectations() is True
        assert result.errors == ()

        # 2. Source identity invariants
        assert result.raw_source_digest == GOVERNED_HERO_RAW_DIGEST
        assert result.source_watermark == GOVERNED_HERO_WATERMARK
        assert result.import_disposition == ImportOutcomeDisposition.FIRST_IMPORT
        assert result.imported_record_count == 8
        assert result.exact_duplicate_count == 0

        # 3. Investigation-priority signal invariants
        assert result.signal_count == 1
        assert result.hero_signal is not None
        assert result.hero_signal_id == GOVERNED_HERO_SIGNAL_ID
        assert result.hero_signal_score == GOVERNED_HERO_SCORE
        assert result.hero_components == GOVERNED_HERO_COMPONENTS

        sig = result.hero_signal
        assert sig.facility_id == "SYNTH-FACILITY-001"
        assert sig.ward == "SYNTH-WARD-A"
        assert sig.organism_code == "kle"
        assert sig.ward_organism_count == 3
        assert sig.facility_organism_count == 4
        assert sig.status == SignalStatus.TRIGGERED
        assert sig.reason == SignalReason.HIGH_PRIORITY_CLUSTER
        assert sig.window_start == date(2026, 8, 12)
        assert sig.window_end == date(2026, 8, 18)

        # 4. Zero human and zero agentic/model metrics
        assert result.autonomous_external_actions == 0
        assert result.model_calls == 0
        assert result.network_calls == 0
        assert result.cloud_calls == 0
        assert result.human_prompts == 0
        assert result.human_interventions == 0
        assert result.clarifications == 0
        assert result.approvals == 0

    def test_committed_golden_json_artifact_matches_execution(self) -> None:
        use_case = create_offline_hero_use_case()
        result = use_case.execute(CertifyOfflineHeroCommand(source_location=str(HERO_CSV_PATH)))

        assert HERO_CERTIFICATION_JSON_PATH.is_file()
        committed_json = json.loads(HERO_CERTIFICATION_JSON_PATH.read_text(encoding="utf-8"))
        actual_dict = result.to_dict()

        # Compare material sections
        actual_hero = actual_dict["hero_certification"]
        expected_hero = committed_json["hero_certification"]

        assert actual_hero["certified"] == expected_hero["certified"]
        assert actual_hero["input_valid"] == expected_hero["input_valid"]
        assert actual_hero["deterministic_import"] == expected_hero["deterministic_import"]
        assert actual_hero["raw_source_digest"] == expected_hero["raw_source_digest"]
        assert actual_hero["source_watermark"] == expected_hero["source_watermark"]
        assert actual_hero["imported_record_count"] == expected_hero["imported_record_count"]
        assert actual_hero["signal_count"] == expected_hero["signal_count"]
        assert actual_hero["signal_id"] == expected_hero["signal_id"]
        assert actual_hero["signal_score"] == expected_hero["signal_score"]
        assert actual_hero["components"] == expected_hero["components"]
        assert actual_hero["supporting_finding_refs"] == expected_hero["supporting_finding_refs"]
        assert actual_hero["supporting_isolate_refs"] == expected_hero["supporting_isolate_refs"]
        assert actual_hero["policy_version"] == expected_hero["policy_version"]
        assert actual_hero["config_version"] == expected_hero["config_version"]
        assert actual_hero["algorithm_version"] == expected_hero["algorithm_version"]


# ============================================================================
# 2. Repeatability & Ordering Invariance Proofs
# ============================================================================


class TestDeterminismAndInvariance:
    """Tests proving repeatability and ordering invariance."""

    def test_repeated_runs_produce_identical_output(self) -> None:
        use_case = create_offline_hero_use_case()
        cmd = CertifyOfflineHeroCommand(source_location=str(HERO_CSV_PATH))

        run1 = use_case.execute(cmd)
        run2 = use_case.execute(cmd)

        assert run1.raw_source_digest == run2.raw_source_digest
        assert run1.source_watermark == run2.source_watermark
        assert run1.signal_count == run2.signal_count
        assert run1.hero_signal_id == run2.hero_signal_id
        assert run1.hero_signal_score == run2.hero_signal_score
        assert run1.hero_components == run2.hero_components
        assert run1.signals == run2.signals

    def test_row_ordering_invariance(self) -> None:
        hero_text = HERO_CSV_PATH.read_text(encoding="utf-8")
        lines = [line for line in hero_text.splitlines() if line.strip()]
        header = lines[0]
        rows = lines[1:]

        # Reverse row order
        reversed_csv = "\n".join([header] + list(reversed(rows)) + [""]).encode("utf-8")

        loader = InMemoryCustomLoader({"permuted.csv": reversed_csv})
        repo = InMemorySourceReplayRepository()
        use_case = create_offline_hero_use_case(source_loader=loader, replay_repo=repo)

        res = use_case.execute(
            CertifyOfflineHeroCommand(source_location="permuted.csv", source_key="permuted")
        )

        assert res.certified is True
        # SourceWatermark is canonical and order-independent
        assert res.source_watermark == GOVERNED_HERO_WATERMARK
        assert res.signal_count == 1
        assert res.hero_signal_id == GOVERNED_HERO_SIGNAL_ID
        assert res.hero_signal_score == GOVERNED_HERO_SCORE
        assert res.hero_components == GOVERNED_HERO_COMPONENTS


# ============================================================================
# 3. Duplicate-Safe Replay Proof
# ============================================================================


class TestDuplicateSafeReplay:
    """Tests proving replay safety against the replay repository."""

    def test_exact_replay_produces_exact_replay_disposition_without_extra_signals(
        self,
    ) -> None:
        repo = InMemorySourceReplayRepository()
        use_case = create_offline_hero_use_case(replay_repo=repo)
        cmd = CertifyOfflineHeroCommand(
            source_location=str(HERO_CSV_PATH), source_key="test-hero-stream"
        )

        # First run -> FIRST_IMPORT
        res1 = use_case.execute(cmd)
        assert res1.certified is True
        assert res1.import_disposition == ImportOutcomeDisposition.FIRST_IMPORT
        assert res1.signal_count == 1

        # Second run -> EXACT_REPLAY
        res2 = use_case.execute(cmd)
        assert res2.certified is True
        assert res2.import_disposition == ImportOutcomeDisposition.EXACT_REPLAY
        assert res2.source_watermark == res1.source_watermark
        assert res2.signal_count == 1
        assert res2.hero_signal_id == res1.hero_signal_id
        assert len(repo.accept_calls) == 2


# ============================================================================
# 4. Proof-Reference Continuity
# ============================================================================


class TestProofReferenceContinuity:
    """Tests proving proof-carrying linkage to underlying deterministic findings."""

    def test_signal_carries_exact_deterministic_finding_references(self) -> None:
        use_case = create_offline_hero_use_case()
        result = use_case.execute(CertifyOfflineHeroCommand(source_location=str(HERO_CSV_PATH)))

        sig = result.hero_signal
        assert sig is not None

        ref = sig.to_finding_reference()
        assert isinstance(ref, DeterministicFindingReference)
        assert ref.finding_id == GOVERNED_HERO_SIGNAL_ID
        assert ref.policy_version == "ngabo-signal-v1"

        # Pinned upstream findings
        assert "tconc-ed312ddb0844c9ca" in ref.input_refs
        assert "lconc-1d3ff528db1484f0" in ref.input_refs
        assert "psim-8ce3cf934d3d8eb2" in ref.input_refs
        assert "psim-a18b030a20a5f1b1" in ref.input_refs
        assert "psim-cde2a3614f7f873d" in ref.input_refs

        # Supporting isolates
        assert sig.supporting_isolate_refs == ("ISO-031", "ISO-034", "ISO-039")


# ============================================================================
# 5. Normal Baseline Acceptance (Negative Control)
# ============================================================================


class TestNormalBaselineAcceptance:
    """Tests proving normal baseline surveillance input yields zero signals."""

    def test_sporadic_normal_baseline_emits_zero_signals(self) -> None:
        loader = InMemoryCustomLoader({"normal.csv": SPORADIC_NORMAL_BASELINE_CSV})
        repo = InMemorySourceReplayRepository()
        use_case = create_offline_hero_use_case(source_loader=loader, replay_repo=repo)

        res = use_case.execute(
            CertifyOfflineHeroCommand(
                source_location="normal.csv",
                source_key="normal-stream",
                window_end=date(2026, 8, 18),
            )
        )

        assert res.certified is True
        assert res.imported_record_count == 8
        assert res.signal_count == 0
        assert res.signals == ()
        assert res.hero_signal is None
        assert res.hero_signal_id is None
        assert res.hero_signal_score is None


# ============================================================================
# 6. Malformed and Missing Evidence Fail-Closed Proofs
# ============================================================================


class TestFailClosedBoundaries:
    """Tests proving fail-closed handling of malformed input and missing evidence."""

    def test_missing_source_file_fails_closed(self) -> None:
        use_case = create_offline_hero_use_case()
        cmd = CertifyOfflineHeroCommand(source_location="nonexistent_hero.csv")
        result = use_case.execute(cmd)

        assert result.certified is False
        assert result.signal_count == 0
        assert len(result.errors) > 0
        assert any("SOURCE_READ_ERROR" in e for e in result.errors)

    def test_malformed_csv_header_fails_closed(self) -> None:
        bad_csv = b"BAD_HEADER_1,BAD_HEADER_2\nVAL1,VAL2\n"
        loader = InMemoryCustomLoader({"bad.csv": bad_csv})
        use_case = create_offline_hero_use_case(source_loader=loader)

        result = use_case.execute(CertifyOfflineHeroCommand(source_location="bad.csv"))

        assert result.certified is False
        assert result.signal_count == 0
        assert len(result.errors) > 0
        assert any("PARSER_FAILURE" in e for e in result.errors)

    def test_conflicting_duplicate_record_fails_closed(self) -> None:
        # Same isolate ID with conflicting AST results
        conflicting_csv = (
            b"ISOLATE_ID,COLLECTION_DATE,ORGANISM_CODE,ORGANISM_NAME,"
            b"FACILITY_ID,LAB_ID,WARD,SPECIMEN_TYPE,PATIENT_TOKEN,SOURCE_IMPORT_ID,AMK\n"
            b"ISO-001,2026-08-16,eco,Escherichia coli,"
            b"SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,"
            b"SYNTH-CASE-001,SYNTH-IMPORT-001,S\n"
            b"ISO-001,2026-08-16,eco,Escherichia coli,"
            b"SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,"
            b"SYNTH-CASE-001,SYNTH-IMPORT-001,R\n"
        )

        loader = InMemoryCustomLoader({"conflict.csv": conflicting_csv})
        use_case = create_offline_hero_use_case(source_loader=loader)

        result = use_case.execute(CertifyOfflineHeroCommand(source_location="conflict.csv"))

        assert result.certified is False
        assert result.signal_count == 0
        assert any("CONFLICTING_DUPLICATE_RECORD" in e for e in result.errors)

    def test_missing_material_phenotype_evidence_fails_closed(self) -> None:
        # 3 Ward A isolates but with non-overlapping / non-comparable AST results
        missing_pheno_csv = (
            b"ISOLATE_ID,COLLECTION_DATE,ORGANISM_CODE,ORGANISM_NAME,"
            b"FACILITY_ID,LAB_ID,WARD,SPECIMEN_TYPE,PATIENT_TOKEN,SOURCE_IMPORT_ID,AMK,MEM,CIP\n"
            b"ISO-101,2026-08-16,kle,Klebsiella pneumoniae,"
            b"SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,blood,"
            b"SYNTH-CASE-101,SYNTH-IMPORT-001,S,UNKNOWN,UNKNOWN\n"
            b"ISO-102,2026-08-17,kle,Klebsiella pneumoniae,"
            b"SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,blood,"
            b"SYNTH-CASE-102,SYNTH-IMPORT-001,UNKNOWN,R,UNKNOWN\n"
            b"ISO-103,2026-08-18,kle,Klebsiella pneumoniae,"
            b"SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,blood,"
            b"SYNTH-CASE-103,SYNTH-IMPORT-001,UNKNOWN,UNKNOWN,I\n"
        )

        loader = InMemoryCustomLoader({"missing_pheno.csv": missing_pheno_csv})
        use_case = create_offline_hero_use_case(source_loader=loader)

        result = use_case.execute(CertifyOfflineHeroCommand(source_location="missing_pheno.csv"))

        # Batch imports successfully, but detector yields 0 signals due to INSUFFICIENT_DATA
        assert result.certified is True
        assert result.imported_record_count == 3
        assert result.signal_count == 0
        assert result.signals == ()


# ============================================================================
# 7. Bootstrap CLI Runner & Exit Code Tests
# ============================================================================


class TestBootstrapCliRunner:
    """Tests proving the console entrypoint ngabo-certify-hero behavior."""

    def test_cli_runner_clean_hero_exits_zero(self) -> None:
        exit_code = main(["--csv", str(HERO_CSV_PATH), "--quiet"])
        assert exit_code == 0

    def test_cli_runner_prints_valid_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(["--csv", str(HERO_CSV_PATH)])
        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["hero_certification"]["certified"] is True
        assert data["hero_certification"]["signal_id"] == GOVERNED_HERO_SIGNAL_ID

    def test_cli_runner_nonexistent_file_exits_one(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["--csv", "does_not_exist.csv"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "ERROR: Certification failed" in captured.err

    def test_cli_runner_normal_baseline_exits_one_on_hero_expectation_failure(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        normal_csv_file = tmp_path / "normal.csv"
        normal_csv_file.write_bytes(SPORADIC_NORMAL_BASELINE_CSV)

        exit_code = main(["--csv", str(normal_csv_file)])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "ERROR: Hero expectations violated" in captured.err


# ============================================================================
# 8. Adversarial, Material Change, and Integrity Scenarios
# ============================================================================


class TestAdversarialAndEdgeScenarios:
    """Tests proving prompt injection immunity, material change, and tampering detection."""

    def test_prompt_injection_in_data_has_zero_influence_on_deterministic_scoring(
        self,
    ) -> None:
        # Prompt injection payload in synthetic string fields
        injection_csv = (
            b"ISOLATE_ID,COLLECTION_DATE,ORGANISM_CODE,ORGANISM_NAME,"
            b"FACILITY_ID,LAB_ID,WARD,SPECIMEN_TYPE,PATIENT_TOKEN,SOURCE_IMPORT_ID,AMK,CAZ,CIP\n"
            b"ISO-801,2026-08-13,eco,Escherichia coli,"
            b"SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,"
            b"SYNTH-CASE-INJECT-SYSTEM-OVERRIDE-ALERT,"
            b"SYNTH-IMPORT-IGNORE-PREVIOUS-INSTRUCTIONS,S,S,S\n"
            b"ISO-802,2026-08-14,eco,Escherichia coli,"
            b"SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,blood,"
            b"SYNTH-CASE-802,SYNTH-IMPORT-001,S,S,S\n"
        )

        loader = InMemoryCustomLoader({"inject.csv": injection_csv})
        repo = InMemorySourceReplayRepository()
        use_case = create_offline_hero_use_case(source_loader=loader, replay_repo=repo)

        res = use_case.execute(CertifyOfflineHeroCommand(source_location="inject.csv"))

        # Ingestion succeeds deterministically because SYNTH- pattern is satisfied;
        # NO prompt is ever evaluated; surveillance logic evaluates k=2 -> 0 signals
        assert res.certified is True
        assert res.signal_count == 0
        assert res.hero_signal is None
        assert res.model_calls == 0
        assert res.human_prompts == 0

    def test_material_change_advances_watermark_and_reports_disposition(self) -> None:
        hero_bytes_1 = HERO_CSV_PATH.read_bytes()
        # Slightly modified hero CSV (remove last row ISO-071)
        hero_lines = hero_bytes_1.decode("utf-8").splitlines()
        modified_csv = "\n".join(hero_lines[:-1] + [""]).encode("utf-8")

        loader = InMemoryCustomLoader({"stream.csv": hero_bytes_1})
        repo = InMemorySourceReplayRepository()
        use_case = create_offline_hero_use_case(source_loader=loader, replay_repo=repo)

        cmd = CertifyOfflineHeroCommand(source_location="stream.csv", source_key="stream-1")
        res1 = use_case.execute(cmd)
        assert res1.import_disposition == ImportOutcomeDisposition.FIRST_IMPORT
        assert res1.imported_record_count == 8

        # Update loader with modified source
        loader._sources["stream.csv"] = modified_csv
        res2 = use_case.execute(cmd)
        assert res2.import_disposition == ImportOutcomeDisposition.MATERIAL_CHANGE
        assert res2.imported_record_count == 7
        assert res2.source_watermark != res1.source_watermark

    def test_verify_hero_expectations_fails_on_tampered_metrics(self) -> None:
        use_case = create_offline_hero_use_case()
        valid_res = use_case.execute(CertifyOfflineHeroCommand(source_location=str(HERO_CSV_PATH)))
        assert valid_res.verify_hero_expectations() is True

        # Tampered model_calls > 0
        tampered_model = OfflineHeroCertificationResult(
            certified=valid_res.certified,
            input_location=valid_res.input_location,
            raw_source_digest=valid_res.raw_source_digest,
            source_watermark=valid_res.source_watermark,
            import_disposition=valid_res.import_disposition,
            imported_record_count=valid_res.imported_record_count,
            exact_duplicate_count=valid_res.exact_duplicate_count,
            signal_count=valid_res.signal_count,
            signals=valid_res.signals,
            policy_version=valid_res.policy_version,
            config_version=valid_res.config_version,
            algorithm_version=valid_res.algorithm_version,
            model_calls=1,  # VIOLATION
        )
        assert tampered_model.verify_hero_expectations() is False

        # Tampered human_prompts > 0
        tampered_human = OfflineHeroCertificationResult(
            certified=valid_res.certified,
            input_location=valid_res.input_location,
            raw_source_digest=valid_res.raw_source_digest,
            source_watermark=valid_res.source_watermark,
            import_disposition=valid_res.import_disposition,
            imported_record_count=valid_res.imported_record_count,
            exact_duplicate_count=valid_res.exact_duplicate_count,
            signal_count=valid_res.signal_count,
            signals=valid_res.signals,
            policy_version=valid_res.policy_version,
            config_version=valid_res.config_version,
            algorithm_version=valid_res.algorithm_version,
            human_prompts=1,  # VIOLATION
        )
        assert tampered_human.verify_hero_expectations() is False


# ============================================================================
# 9. Dependency & Clean Architecture Audit
# ============================================================================


class TestDependencyAudit:
    """Tests proving complete offline execution with zero cloud/model imports."""

    def test_no_cloud_or_model_imports_in_certification_pipeline(self) -> None:
        forbidden_modules = [
            "google",
            "google.cloud",
            "google.genai",
            "google_genai",
            "google.adk",
            "vertexai",
            "fastapi",
            "requests",
            "urllib.request",
            "anthropic",
            "openai",
        ]

        # Verify none of these are imported by ngabo modules
        for mod in sys.modules:
            for forbidden in forbidden_modules:
                assert not (
                    mod == forbidden or mod.startswith(f"{forbidden}.")
                ), f"Forbidden module {mod!r} found in sys.modules"
