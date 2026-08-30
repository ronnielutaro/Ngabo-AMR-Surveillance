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
from typing import Any

import pytest

from ngabo.application.commands.certify_offline_hero_command import (
    CertifyOfflineHeroCommand,
)
from ngabo.application.enums.import_outcome_disposition import ImportOutcomeDisposition
from ngabo.application.value_objects.offline_hero_certification_result import (
    GOVERNED_HERO_COMPONENTS,
    GOVERNED_HERO_EVENT_ID,
    GOVERNED_HERO_IMPORTED_RECORD_IDS,
    GOVERNED_HERO_RAW_DIGEST,
    GOVERNED_HERO_SCORE,
    GOVERNED_HERO_SIGNAL_ID,
    GOVERNED_HERO_WATERMARK,
    OfflineHeroCertificationResult,
)
from ngabo.bootstrap.certify_hero import certify_hero, create_offline_hero_use_case, main
from ngabo.domain.enums.signal_status import SignalReason, SignalStatus
from ngabo.domain.events.investigation_priority_signal_event import (
    InvestigationPrioritySignalEvent,
    compute_signal_event_id,
)
from ngabo.domain.value_objects.deterministic_finding_evidence import (
    DeterministicFindingEvidence,
)
from ngabo.domain.value_objects.proof_references import DeterministicFindingReference
from ngabo.infrastructure.repositories.in_memory_source_replay_repository import (
    InMemorySourceReplayRepository,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
HERO_CSV_PATH = REPO_ROOT / "data" / "synthetic" / "canonical_hero.csv"
HERO_CERTIFICATION_JSON_PATH = (
    REPO_ROOT / "data" / "synthetic" / "canonical_hero_certification.json"
)
CERTIFICATION_FIXTURES_DIR = REPO_ROOT / "data" / "synthetic" / "certification"


@pytest.fixture(autouse=True)
def deny_network_access(monkeypatch: pytest.MonkeyPatch) -> None:
    """Guard ensuring zero network calls can be made during offline certification."""
    import socket

    def fail_connect(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Network access attempted during offline certification test!")

    monkeypatch.setattr(socket.socket, "connect", fail_connect)


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
        cmd = CertifyOfflineHeroCommand(
            source_location=str(HERO_CSV_PATH),
            logical_source_id="data/synthetic/canonical_hero.csv",
        )
        result = use_case.execute(cmd)

        # 1. Primary certification flags
        assert result.execution_succeeded is True
        assert result.certified is True
        assert result.verify_hero_expectations() is True
        assert result.errors == ()
        assert result.input_location == "data/synthetic/canonical_hero.csv"

        # 2. Source identity invariants
        assert result.raw_source_digest == GOVERNED_HERO_RAW_DIGEST
        assert result.source_watermark == GOVERNED_HERO_WATERMARK
        assert result.import_disposition == ImportOutcomeDisposition.FIRST_IMPORT
        assert result.imported_record_count == 8
        assert result.imported_record_ids == GOVERNED_HERO_IMPORTED_RECORD_IDS
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

        # 4. Deterministic signal event envelope
        assert result.event is not None
        assert isinstance(result.event, InvestigationPrioritySignalEvent)
        assert result.event_id == "evt-a44635c546dfc667"
        assert result.event.event_id == "evt-a44635c546dfc667"
        assert result.event.event_type == "INVESTIGATION_PRIORITY_SIGNAL"
        assert result.event.contract_version == "ngabo-signal-event-v1"
        assert result.event.signal_id == GOVERNED_HERO_SIGNAL_ID
        assert result.event.source_watermark == GOVERNED_HERO_WATERMARK
        assert result.event.facility_id == "SYNTH-FACILITY-001"
        assert result.event.ward == "SYNTH-WARD-A"
        assert result.event.organism_code == "kle"
        assert result.event.signal_score == 0.9375
        assert result.event.supporting_finding_refs == sig.supporting_finding_refs
        assert result.event.supporting_isolate_refs == sig.supporting_isolate_refs

        # 5. Deterministic finding evidence manifest
        assert len(result.finding_evidence) == 5
        finding_ids = tuple(f.finding_id for f in result.finding_evidence)
        assert finding_ids == sig.supporting_finding_refs

        lconc = [f for f in result.finding_evidence if f.finding_id == "lconc-1d3ff528db1484f0"][0]
        assert isinstance(lconc, DeterministicFindingEvidence)
        assert lconc.finding_type == "LOCATION_CONCENTRATION"
        assert lconc.policy_version == "ngabo-concentration-v1"
        assert lconc.algorithm_version == "ward-share-v1"
        assert lconc.config_version == "win7d-org-facility-ward-v1"
        assert lconc.input_refs == ("ISO-027", "ISO-031", "ISO-034", "ISO-039")

        tconc = [f for f in result.finding_evidence if f.finding_id == "tconc-ed312ddb0844c9ca"][0]
        assert tconc.finding_type == "TEMPORAL_CONCENTRATION"
        assert tconc.policy_version == "ngabo-concentration-v1"
        assert tconc.algorithm_version == "retrospective-count-v1"
        assert tconc.config_version == "win7d-org-facility-ward-v1"
        assert tconc.input_refs == ("ISO-027", "ISO-031", "ISO-034", "ISO-039")

        psims = [f for f in result.finding_evidence if f.finding_type == "PROFILE_SIMILARITY"]
        assert len(psims) == 3
        for p in psims:
            assert p.policy_version == "ngabo-profile-sim-v1"
            assert p.algorithm_version == "exact-ratio-v1"
            assert p.config_version == "min3-strict-org-v1"

        # 6. Zero human and zero agentic/model metrics
        assert result.model_required is False
        assert result.network_required is False
        assert result.cloud_required is False
        assert result.human_intervention_required is False
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
        cmd = CertifyOfflineHeroCommand(
            source_location=str(HERO_CSV_PATH),
            logical_source_id="data/synthetic/canonical_hero.csv",
        )
        result = use_case.execute(cmd)

        assert HERO_CERTIFICATION_JSON_PATH.is_file()
        committed_json = json.loads(HERO_CERTIFICATION_JSON_PATH.read_text(encoding="utf-8"))
        actual_dict = result.to_dict()

        assert actual_dict == committed_json

    def test_portable_logical_locator_is_independent_of_filesystem_path(
        self, tmp_path: Path
    ) -> None:
        """Proves evidence is byte-for-byte portable across alternate directories."""
        alternate_csv = tmp_path / "somewhere_else" / "canonical_hero.csv"
        alternate_csv.parent.mkdir(parents=True, exist_ok=True)
        alternate_csv.write_bytes(HERO_CSV_PATH.read_bytes())

        # certify_hero recognizes canonical_hero.csv and assigns portable locator
        result = certify_hero(alternate_csv)

        assert result.certified is True
        assert result.input_location == "data/synthetic/canonical_hero.csv"
        expected_json = json.loads(HERO_CERTIFICATION_JSON_PATH.read_text(encoding="utf-8"))
        assert result.to_dict() == expected_json


# ============================================================================
# 2. Repeatability & Ordering Invariance Proofs
# ============================================================================


class TestDeterminismAndInvariance:
    """Tests proving repeatability and ordering invariance using committed fixtures."""

    def test_repeated_runs_produce_identical_output(self) -> None:
        use_case = create_offline_hero_use_case()
        cmd = CertifyOfflineHeroCommand(
            source_location=str(HERO_CSV_PATH),
            logical_source_id="data/synthetic/canonical_hero.csv",
        )

        run1 = use_case.execute(cmd)
        run2 = use_case.execute(cmd)

        assert run1.raw_source_digest == run2.raw_source_digest
        assert run1.source_watermark == run2.source_watermark
        assert run1.signal_count == run2.signal_count
        assert run1.hero_signal_id == run2.hero_signal_id
        assert run1.hero_signal_score == run2.hero_signal_score
        assert run1.hero_components == run2.hero_components
        assert run1.event_id == run2.event_id
        assert run1.signals == run2.signals

    def test_row_ordering_invariance_from_committed_fixture(self) -> None:
        reordered_csv_path = CERTIFICATION_FIXTURES_DIR / "canonical_hero_reordered.csv"
        assert reordered_csv_path.is_file()

        use_case = create_offline_hero_use_case()
        res = use_case.execute(
            CertifyOfflineHeroCommand(
                source_location=str(reordered_csv_path),
                logical_source_id="data/synthetic/certification/canonical_hero_reordered.csv",
            )
        )

        assert res.execution_succeeded is True
        # Canonical hero expectations: watermark is invariant to row order
        assert res.source_watermark == GOVERNED_HERO_WATERMARK
        assert res.signal_count == 1
        assert res.hero_signal_id == GOVERNED_HERO_SIGNAL_ID
        assert res.hero_signal_score == GOVERNED_HERO_SCORE
        assert res.hero_components == GOVERNED_HERO_COMPONENTS
        assert res.event_id == "evt-a44635c546dfc667"
        assert res.imported_record_ids == GOVERNED_HERO_IMPORTED_RECORD_IDS


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
            source_location=str(HERO_CSV_PATH),
            source_key="test-hero-stream",
            logical_source_id="data/synthetic/canonical_hero.csv",
        )

        # First run -> FIRST_IMPORT
        res1 = use_case.execute(cmd)
        assert res1.execution_succeeded is True
        assert res1.certified is True
        assert res1.import_disposition == ImportOutcomeDisposition.FIRST_IMPORT
        assert res1.signal_count == 1

        # Second run -> EXACT_REPLAY
        res2 = use_case.execute(cmd)
        assert res2.execution_succeeded is True
        assert res2.certified is True
        assert res2.import_disposition == ImportOutcomeDisposition.EXACT_REPLAY
        assert res2.source_watermark == res1.source_watermark
        assert res2.signal_count == 1
        assert res2.hero_signal_id == res1.hero_signal_id
        assert res2.event_id == res1.event_id
        assert len(repo.accept_calls) == 2


# ============================================================================
# 4. Proof-Reference Continuity
# ============================================================================


class TestProofReferenceContinuity:
    """Tests proving proof-carrying linkage to underlying deterministic findings."""

    def test_signal_carries_exact_deterministic_finding_references(self) -> None:
        use_case = create_offline_hero_use_case()
        result = use_case.execute(
            CertifyOfflineHeroCommand(
                source_location=str(HERO_CSV_PATH),
                logical_source_id="data/synthetic/canonical_hero.csv",
            )
        )

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
# 5. Normal Baseline Acceptance (Negative Control with Certified Semantics)
# ============================================================================


class TestNormalBaselineAcceptance:
    """Tests proving normal baseline surveillance input yields zero signals."""

    def test_sporadic_normal_baseline_emits_zero_signals_and_uncertified(self) -> None:
        normal_csv_path = CERTIFICATION_FIXTURES_DIR / "normal_baseline.csv"
        assert normal_csv_path.is_file()

        use_case = create_offline_hero_use_case()
        res = use_case.execute(
            CertifyOfflineHeroCommand(
                source_location=str(normal_csv_path),
                logical_source_id="data/synthetic/certification/normal_baseline.csv",
                source_key="normal-stream",
                window_end=date(2026, 8, 18),
            )
        )

        # Pipeline execution succeeded on valid CSV
        assert res.execution_succeeded is True
        # But CANNOT be certified because hero criteria were not met
        assert res.certified is False
        assert res.verify_hero_expectations() is False
        assert res.imported_record_count == 8
        assert res.signal_count == 0
        assert res.signals == ()
        assert res.hero_signal is None
        assert res.hero_signal_id is None
        assert res.hero_signal_score is None
        assert res.event is None
        assert res.event_id is None
        assert res.finding_evidence == ()
        assert res.to_dict()["hero_certification"]["certified"] is False
        assert res.to_dict()["hero_certification"]["execution_succeeded"] is True


# ============================================================================
# 6. Malformed and Missing Evidence Fail-Closed Proofs
# ============================================================================


class TestFailClosedBoundaries:
    """Tests proving fail-closed handling of malformed input and missing evidence."""

    def test_missing_source_file_fails_closed(self) -> None:
        use_case = create_offline_hero_use_case()
        cmd = CertifyOfflineHeroCommand(source_location="nonexistent_hero.csv")
        result = use_case.execute(cmd)

        assert result.execution_succeeded is False
        assert result.certified is False
        assert result.signal_count == 0
        assert len(result.errors) > 0
        assert any("SOURCE_READ_ERROR" in e for e in result.errors)

    def test_malformed_csv_header_fails_closed_from_committed_fixture(self) -> None:
        bad_csv_path = CERTIFICATION_FIXTURES_DIR / "malformed_header.csv"
        assert bad_csv_path.is_file()

        use_case = create_offline_hero_use_case()
        result = use_case.execute(
            CertifyOfflineHeroCommand(
                source_location=str(bad_csv_path),
                logical_source_id="data/synthetic/certification/malformed_header.csv",
            )
        )

        assert result.execution_succeeded is False
        assert result.certified is False
        assert result.signal_count == 0
        assert len(result.errors) > 0
        assert any("PARSER_FAILURE" in e for e in result.errors)

    def test_conflicting_duplicate_record_fails_closed_from_committed_fixture(self) -> None:
        conflict_csv_path = CERTIFICATION_FIXTURES_DIR / "conflicting_duplicate.csv"
        assert conflict_csv_path.is_file()

        use_case = create_offline_hero_use_case()
        result = use_case.execute(
            CertifyOfflineHeroCommand(
                source_location=str(conflict_csv_path),
                logical_source_id="data/synthetic/certification/conflicting_duplicate.csv",
            )
        )

        assert result.execution_succeeded is False
        assert result.certified is False
        assert result.signal_count == 0
        assert any("CONFLICTING_DUPLICATE_RECORD" in e for e in result.errors)

    def test_missing_material_phenotype_evidence_from_committed_fixture(self) -> None:
        missing_csv_path = CERTIFICATION_FIXTURES_DIR / "missing_phenotype_evidence.csv"
        assert missing_csv_path.is_file()

        use_case = create_offline_hero_use_case()
        result = use_case.execute(
            CertifyOfflineHeroCommand(
                source_location=str(missing_csv_path),
                logical_source_id="data/synthetic/certification/missing_phenotype_evidence.csv",
            )
        )

        # Batch imports successfully, but detector yields 0 signals due to INSUFFICIENT_DATA
        assert result.execution_succeeded is True
        assert result.certified is False
        assert result.imported_record_count == 3
        assert result.signal_count == 0
        assert result.signals == ()
        assert result.event is None


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
        assert data["hero_certification"]["execution_succeeded"] is True
        assert data["hero_certification"]["signal_id"] == GOVERNED_HERO_SIGNAL_ID
        assert data["hero_certification"]["event_id"] == "evt-a44635c546dfc667"

    def test_cli_runner_nonexistent_file_exits_one(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(["--csv", "does_not_exist.csv"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "ERROR: Pipeline execution failed" in captured.err

    def test_cli_runner_normal_baseline_exits_one_with_uncertified_status(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        normal_csv_path = CERTIFICATION_FIXTURES_DIR / "normal_baseline.csv"
        exit_code = main(["--csv", str(normal_csv_path)])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert (
            "ERROR: Execution succeeded but canonical hero release criteria were not met"
            in captured.err
        )
        data = json.loads(captured.out)
        assert data["hero_certification"]["certified"] is False
        assert data["hero_certification"]["execution_succeeded"] is True


# ============================================================================
# 8. Adversarial, Material Change, and Integrity Scenarios
# ============================================================================


class TestAdversarialAndEdgeScenarios:
    """Tests proving prompt injection immunity, material change, and tampering detection."""

    def test_prompt_injection_in_data_has_zero_influence_from_committed_fixture(
        self,
    ) -> None:
        inject_csv_path = CERTIFICATION_FIXTURES_DIR / "prompt_injection.csv"
        assert inject_csv_path.is_file()

        use_case = create_offline_hero_use_case()
        res = use_case.execute(
            CertifyOfflineHeroCommand(
                source_location=str(inject_csv_path),
                logical_source_id="data/synthetic/certification/prompt_injection.csv",
            )
        )

        assert res.execution_succeeded is True
        assert res.certified is False
        assert res.signal_count == 0
        assert res.hero_signal is None
        assert res.model_calls == 0
        assert res.human_prompts == 0

    def test_material_change_from_committed_fixture_advances_watermark(self) -> None:
        material_change_csv_path = CERTIFICATION_FIXTURES_DIR / "material_change.csv"
        assert material_change_csv_path.is_file()

        repo = InMemorySourceReplayRepository()
        use_case = create_offline_hero_use_case(replay_repo=repo)

        cmd1 = CertifyOfflineHeroCommand(
            source_location=str(HERO_CSV_PATH),
            source_key="stream-1",
            logical_source_id="data/synthetic/canonical_hero.csv",
        )
        res1 = use_case.execute(cmd1)
        assert res1.import_disposition == ImportOutcomeDisposition.FIRST_IMPORT
        assert res1.imported_record_count == 8

        cmd2 = CertifyOfflineHeroCommand(
            source_location=str(material_change_csv_path),
            source_key="stream-1",
            logical_source_id="data/synthetic/certification/material_change.csv",
        )
        res2 = use_case.execute(cmd2)
        assert res2.execution_succeeded is True
        assert res2.certified is False
        assert res2.import_disposition == ImportOutcomeDisposition.MATERIAL_CHANGE
        assert res2.imported_record_count == 7
        assert res2.source_watermark != res1.source_watermark

    def test_result_invariant_validation_fails_closed(self) -> None:
        """Tests proving OfflineHeroCertificationResult fails closed on invalid states."""
        use_case = create_offline_hero_use_case()
        valid_res = use_case.execute(
            CertifyOfflineHeroCommand(
                source_location=str(HERO_CSV_PATH),
                logical_source_id="data/synthetic/canonical_hero.csv",
            )
        )
        assert valid_res.certified is True

        # 1. certified=True but execution_succeeded=False is rejected
        with pytest.raises(
            ValueError, match="certified cannot be True when execution_succeeded is False"
        ):
            OfflineHeroCertificationResult(
                execution_succeeded=False,
                certified=True,
                input_location=valid_res.input_location,
                raw_source_digest=valid_res.raw_source_digest,
                source_watermark=valid_res.source_watermark,
                import_disposition=valid_res.import_disposition,
                imported_record_count=valid_res.imported_record_count,
                imported_record_ids=valid_res.imported_record_ids,
                exact_duplicate_count=valid_res.exact_duplicate_count,
                signal_count=valid_res.signal_count,
                signals=valid_res.signals,
                policy_version=valid_res.policy_version,
                config_version=valid_res.config_version,
                algorithm_version=valid_res.algorithm_version,
                event=valid_res.event,
                event_id=valid_res.event_id,
            )

        # 2. imported_record_count mismatch
        with pytest.raises(ValueError, match="imported_record_count"):
            OfflineHeroCertificationResult(
                execution_succeeded=True,
                certified=False,
                input_location=valid_res.input_location,
                raw_source_digest=valid_res.raw_source_digest,
                source_watermark=valid_res.source_watermark,
                import_disposition=valid_res.import_disposition,
                imported_record_count=99,
                imported_record_ids=valid_res.imported_record_ids,
                exact_duplicate_count=valid_res.exact_duplicate_count,
                signal_count=valid_res.signal_count,
                signals=valid_res.signals,
                policy_version=valid_res.policy_version,
                config_version=valid_res.config_version,
                algorithm_version=valid_res.algorithm_version,
            )

        # 3. signal_count mismatch
        with pytest.raises(ValueError, match="signal_count"):
            OfflineHeroCertificationResult(
                execution_succeeded=True,
                certified=False,
                input_location=valid_res.input_location,
                raw_source_digest=valid_res.raw_source_digest,
                source_watermark=valid_res.source_watermark,
                import_disposition=valid_res.import_disposition,
                imported_record_count=valid_res.imported_record_count,
                imported_record_ids=valid_res.imported_record_ids,
                exact_duplicate_count=valid_res.exact_duplicate_count,
                signal_count=99,
                signals=valid_res.signals,
                policy_version=valid_res.policy_version,
                config_version=valid_res.config_version,
                algorithm_version=valid_res.algorithm_version,
            )

        # 4. event_id mismatch
        with pytest.raises(ValueError, match="event_id"):
            OfflineHeroCertificationResult(
                execution_succeeded=True,
                certified=False,
                input_location=valid_res.input_location,
                raw_source_digest=valid_res.raw_source_digest,
                source_watermark=valid_res.source_watermark,
                import_disposition=valid_res.import_disposition,
                imported_record_count=valid_res.imported_record_count,
                imported_record_ids=valid_res.imported_record_ids,
                exact_duplicate_count=valid_res.exact_duplicate_count,
                signal_count=valid_res.signal_count,
                signals=valid_res.signals,
                policy_version=valid_res.policy_version,
                config_version=valid_res.config_version,
                algorithm_version=valid_res.algorithm_version,
                event=valid_res.event,
                event_id="evt-mismatch",
            )

    def test_event_id_tampering_fails_closed(self) -> None:
        """InvestigationPrioritySignalEvent rejects tampered or arbitrary event IDs."""
        use_case = create_offline_hero_use_case()
        res = use_case.execute(
            CertifyOfflineHeroCommand(
                source_location=str(HERO_CSV_PATH),
                logical_source_id="data/synthetic/canonical_hero.csv",
            )
        )
        assert res.event is not None
        valid_event = res.event

        with pytest.raises(
            ValueError, match="does not match expected deterministic event ID"
        ):
            InvestigationPrioritySignalEvent(
                event_id="evt-0000000000000000",
                event_type=valid_event.event_type,
                contract_version=valid_event.contract_version,
                signal_id=valid_event.signal_id,
                source_watermark=valid_event.source_watermark,
                facility_id=valid_event.facility_id,
                ward=valid_event.ward,
                organism_code=valid_event.organism_code,
                window_start=valid_event.window_start,
                window_end=valid_event.window_end,
                signal_score=valid_event.signal_score,
                policy_version=valid_event.policy_version,
                config_version=valid_event.config_version,
                algorithm_version=valid_event.algorithm_version,
                supporting_finding_refs=valid_event.supporting_finding_refs,
                supporting_isolate_refs=valid_event.supporting_isolate_refs,
            )

    @pytest.mark.parametrize(
        "field_name,tampered_value",
        [
            (
                "source_watermark",
                "ngabo-source-v1:sha256:0000000000000000000000000000000000000000000000000000000000000000",
            ),
            ("signal_score", 0.5),
            ("facility_id", "TAMPERED-FACILITY"),
            ("ward", "TAMPERED-WARD"),
            ("organism_code", "eco"),
            ("policy_version", "tampered-policy-v2"),
            ("config_version", "tampered-config-v2"),
            ("algorithm_version", "tampered-alg-v2"),
            (
                "supporting_finding_refs",
                ("lconc-1d3ff528db1484f0", "tconc-ed312ddb0844c9ca"),
            ),
            ("supporting_isolate_refs", ("ISO-031", "ISO-034")),
        ],
    )
    def test_event_payload_tampering_fails_closed(
        self, field_name: str, tampered_value: Any
    ) -> None:
        """Event ID validation fails closed when semantic payload is tampered with."""
        use_case = create_offline_hero_use_case()
        res = use_case.execute(
            CertifyOfflineHeroCommand(
                source_location=str(HERO_CSV_PATH),
                logical_source_id="data/synthetic/canonical_hero.csv",
            )
        )
        assert res.event is not None
        event_kwargs: dict[str, Any] = {
            "event_id": GOVERNED_HERO_EVENT_ID,
            "event_type": res.event.event_type,
            "contract_version": res.event.contract_version,
            "signal_id": res.event.signal_id,
            "source_watermark": res.event.source_watermark,
            "facility_id": res.event.facility_id,
            "ward": res.event.ward,
            "organism_code": res.event.organism_code,
            "window_start": res.event.window_start,
            "window_end": res.event.window_end,
            "signal_score": res.event.signal_score,
            "policy_version": res.event.policy_version,
            "config_version": res.event.config_version,
            "algorithm_version": res.event.algorithm_version,
            "supporting_finding_refs": res.event.supporting_finding_refs,
            "supporting_isolate_refs": res.event.supporting_isolate_refs,
        }
        event_kwargs[field_name] = tampered_value

        with pytest.raises(
            ValueError, match="does not match expected deterministic event ID"
        ):
            InvestigationPrioritySignalEvent(**event_kwargs)

    def test_event_type_and_contract_tampering_fails_closed(self) -> None:
        """InvestigationPrioritySignalEvent rejects non-governed event types and contracts."""
        use_case = create_offline_hero_use_case()
        res = use_case.execute(
            CertifyOfflineHeroCommand(
                source_location=str(HERO_CSV_PATH),
                logical_source_id="data/synthetic/canonical_hero.csv",
            )
        )
        assert res.event is not None
        valid_event = res.event

        # 1. Tampered event_type
        with pytest.raises(
            ValueError, match="event_type must be 'INVESTIGATION_PRIORITY_SIGNAL'"
        ):
            InvestigationPrioritySignalEvent(
                event_id="evt-any",
                event_type="OUTBREAK_CONFIRMED",
                contract_version=valid_event.contract_version,
                signal_id=valid_event.signal_id,
                source_watermark=valid_event.source_watermark,
                facility_id=valid_event.facility_id,
                ward=valid_event.ward,
                organism_code=valid_event.organism_code,
                window_start=valid_event.window_start,
                window_end=valid_event.window_end,
                signal_score=valid_event.signal_score,
                policy_version=valid_event.policy_version,
                config_version=valid_event.config_version,
                algorithm_version=valid_event.algorithm_version,
                supporting_finding_refs=valid_event.supporting_finding_refs,
                supporting_isolate_refs=valid_event.supporting_isolate_refs,
            )

        # 2. Tampered contract_version
        with pytest.raises(
            ValueError, match="contract_version must be 'ngabo-signal-event-v1'"
        ):
            InvestigationPrioritySignalEvent(
                event_id="evt-any",
                event_type=valid_event.event_type,
                contract_version="ngabo-signal-event-v2",
                signal_id=valid_event.signal_id,
                source_watermark=valid_event.source_watermark,
                facility_id=valid_event.facility_id,
                ward=valid_event.ward,
                organism_code=valid_event.organism_code,
                window_start=valid_event.window_start,
                window_end=valid_event.window_end,
                signal_score=valid_event.signal_score,
                policy_version=valid_event.policy_version,
                config_version=valid_event.config_version,
                algorithm_version=valid_event.algorithm_version,
                supporting_finding_refs=valid_event.supporting_finding_refs,
                supporting_isolate_refs=valid_event.supporting_isolate_refs,
            )

    def test_event_unsorted_refs_fails_closed(self) -> None:
        """InvestigationPrioritySignalEvent requires canonical sorted order for refs."""
        use_case = create_offline_hero_use_case()
        res = use_case.execute(
            CertifyOfflineHeroCommand(
                source_location=str(HERO_CSV_PATH),
                logical_source_id="data/synthetic/canonical_hero.csv",
            )
        )
        assert res.event is not None
        valid_event = res.event

        unsorted_findings = tuple(reversed(valid_event.supporting_finding_refs))
        with pytest.raises(
            ValueError, match="supporting_finding_refs must be in canonical sorted order"
        ):
            InvestigationPrioritySignalEvent(
                event_id=valid_event.event_id,
                event_type=valid_event.event_type,
                contract_version=valid_event.contract_version,
                signal_id=valid_event.signal_id,
                source_watermark=valid_event.source_watermark,
                facility_id=valid_event.facility_id,
                ward=valid_event.ward,
                organism_code=valid_event.organism_code,
                window_start=valid_event.window_start,
                window_end=valid_event.window_end,
                signal_score=valid_event.signal_score,
                policy_version=valid_event.policy_version,
                config_version=valid_event.config_version,
                algorithm_version=valid_event.algorithm_version,
                supporting_finding_refs=unsorted_findings,
                supporting_isolate_refs=valid_event.supporting_isolate_refs,
            )

    def test_certification_event_substitution_fails_closed(self) -> None:
        """OfflineHeroCertificationResult rejects hero signal with inconsistent event."""
        use_case = create_offline_hero_use_case()
        valid_res = use_case.execute(
            CertifyOfflineHeroCommand(
                source_location=str(HERO_CSV_PATH),
                logical_source_id="data/synthetic/canonical_hero.csv",
            )
        )
        assert valid_res.event is not None
        sig = valid_res.signals[0]

        # Compute a valid substitute event for a different facility
        substitute_event_id = compute_signal_event_id(
            contract_version=valid_res.event.contract_version,
            event_type=valid_res.event.event_type,
            signal_id=sig.signal_id,
            source_watermark=valid_res.event.source_watermark,
            facility_id="SYNTH-FACILITY-002",
            ward=sig.ward,
            organism_code=sig.organism_code,
            window_start=sig.window_start,
            window_end=sig.window_end,
            signal_score=sig.signal_score,
            precision=4,
            policy_version=sig.policy_version,
            config_version=sig.config_version,
            algorithm_version=sig.algorithm_version,
            supporting_finding_refs=sig.supporting_finding_refs,
            supporting_isolate_refs=sig.supporting_isolate_refs,
        )
        substitute_event = InvestigationPrioritySignalEvent(
            event_id=substitute_event_id,
            event_type=valid_res.event.event_type,
            contract_version=valid_res.event.contract_version,
            signal_id=sig.signal_id,
            source_watermark=valid_res.event.source_watermark,
            facility_id="SYNTH-FACILITY-002",
            ward=sig.ward,
            organism_code=sig.organism_code,
            window_start=sig.window_start,
            window_end=sig.window_end,
            signal_score=sig.signal_score,
            policy_version=sig.policy_version,
            config_version=sig.config_version,
            algorithm_version=sig.algorithm_version,
            supporting_finding_refs=sig.supporting_finding_refs,
            supporting_isolate_refs=sig.supporting_isolate_refs,
        )

        with pytest.raises(
            ValueError, match="event.facility_id must match hero_signal.facility_id"
        ):
            OfflineHeroCertificationResult(
                execution_succeeded=True,
                certified=True,
                input_location=valid_res.input_location,
                raw_source_digest=valid_res.raw_source_digest,
                source_watermark=valid_res.source_watermark,
                import_disposition=valid_res.import_disposition,
                imported_record_count=valid_res.imported_record_count,
                imported_record_ids=valid_res.imported_record_ids,
                exact_duplicate_count=valid_res.exact_duplicate_count,
                signal_count=valid_res.signal_count,
                signals=valid_res.signals,
                policy_version=valid_res.policy_version,
                config_version=valid_res.config_version,
                algorithm_version=valid_res.algorithm_version,
                event=substitute_event,
                event_id=substitute_event.event_id,
                finding_evidence=valid_res.finding_evidence,
            )

    def test_missing_finding_evidence_fails_closed(self) -> None:
        """OfflineHeroCertificationResult rejects certified=True when evidence is missing."""
        use_case = create_offline_hero_use_case()
        valid_res = use_case.execute(
            CertifyOfflineHeroCommand(
                source_location=str(HERO_CSV_PATH),
                logical_source_id="data/synthetic/canonical_hero.csv",
            )
        )
        assert valid_res.certified is True

        with pytest.raises(
            ValueError,
            match="finding_evidence must exactly match hero_signal.to_finding_evidence()",
        ):
            OfflineHeroCertificationResult(
                execution_succeeded=True,
                certified=True,
                input_location=valid_res.input_location,
                raw_source_digest=valid_res.raw_source_digest,
                source_watermark=valid_res.source_watermark,
                import_disposition=valid_res.import_disposition,
                imported_record_count=valid_res.imported_record_count,
                imported_record_ids=valid_res.imported_record_ids,
                exact_duplicate_count=valid_res.exact_duplicate_count,
                signal_count=valid_res.signal_count,
                signals=valid_res.signals,
                policy_version=valid_res.policy_version,
                config_version=valid_res.config_version,
                algorithm_version=valid_res.algorithm_version,
                event=valid_res.event,
                event_id=valid_res.event_id,
                finding_evidence=(),
            )

    @pytest.mark.parametrize(
        "mutation_type",
        ["finding_id", "finding_type", "policy_version", "input_refs"],
    )
    def test_altered_finding_evidence_fails_closed(self, mutation_type: str) -> None:
        """OfflineHeroCertificationResult rejects certified=True when evidence is altered."""
        use_case = create_offline_hero_use_case()
        valid_res = use_case.execute(
            CertifyOfflineHeroCommand(
                source_location=str(HERO_CSV_PATH),
                logical_source_id="data/synthetic/canonical_hero.csv",
            )
        )
        assert valid_res.certified is True
        original_evidence = valid_res.finding_evidence
        first = original_evidence[0]

        if mutation_type == "finding_id":
            altered_first = DeterministicFindingEvidence(
                finding_id="lconc-altered",
                finding_type=first.finding_type,
                policy_version=first.policy_version,
                algorithm_version=first.algorithm_version,
                config_version=first.config_version,
                input_refs=first.input_refs,
            )
        elif mutation_type == "finding_type":
            altered_first = DeterministicFindingEvidence(
                finding_id=first.finding_id,
                finding_type="PROFILE_SIMILARITY",
                policy_version=first.policy_version,
                algorithm_version=first.algorithm_version,
                config_version=first.config_version,
                input_refs=first.input_refs,
            )
        elif mutation_type == "policy_version":
            altered_first = DeterministicFindingEvidence(
                finding_id=first.finding_id,
                finding_type=first.finding_type,
                policy_version="altered-policy-v2",
                algorithm_version=first.algorithm_version,
                config_version=first.config_version,
                input_refs=first.input_refs,
            )
        else:
            altered_first = DeterministicFindingEvidence(
                finding_id=first.finding_id,
                finding_type=first.finding_type,
                policy_version=first.policy_version,
                algorithm_version=first.algorithm_version,
                config_version=first.config_version,
                input_refs=("ISO-099",),
            )

        altered_evidence = (altered_first,) + original_evidence[1:]

        with pytest.raises(
            ValueError,
            match="finding_evidence must exactly match hero_signal.to_finding_evidence()",
        ):
            OfflineHeroCertificationResult(
                execution_succeeded=True,
                certified=True,
                input_location=valid_res.input_location,
                raw_source_digest=valid_res.raw_source_digest,
                source_watermark=valid_res.source_watermark,
                import_disposition=valid_res.import_disposition,
                imported_record_count=valid_res.imported_record_count,
                imported_record_ids=valid_res.imported_record_ids,
                exact_duplicate_count=valid_res.exact_duplicate_count,
                signal_count=valid_res.signal_count,
                signals=valid_res.signals,
                policy_version=valid_res.policy_version,
                config_version=valid_res.config_version,
                algorithm_version=valid_res.algorithm_version,
                event=valid_res.event,
                event_id=valid_res.event_id,
                finding_evidence=altered_evidence,
            )


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

        # Verify none of these are imported by the framework-free ngabo
        # layers that the certification pipeline executes (domain,
        # application, bootstrap). The interfaces HTTP adapter legitimately
        # hosts FastAPI (Issue #90, docs/SYSTEM_DESIGN.md) and is therefore
        # excluded from this check; only the inner layers must stay
        # framework-free.
        inner_layers = ("ngabo.domain", "ngabo.application", "ngabo.bootstrap")
        for mod in sys.modules:
            if not any(mod == layer or mod.startswith(f"{layer}.") for layer in inner_layers):
                continue
            for forbidden in forbidden_modules:
                assert not (
                    mod == forbidden or mod.startswith(f"{forbidden}.")
                ), f"Forbidden module {forbidden!r} imported by inner layer {mod!r}"
