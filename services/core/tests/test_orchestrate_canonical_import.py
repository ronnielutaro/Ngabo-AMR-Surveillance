"""Comprehensive application tests for canonical import orchestration (Issue #44)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from ngabo.application.commands.import_canonical_source_command import (
    ImportCanonicalSourceCommand,
)
from ngabo.application.enums.import_error_code import ImportErrorCode
from ngabo.application.enums.import_outcome_disposition import ImportOutcomeDisposition
from ngabo.application.ports.parse_canonical_source import ParsedSourceResult
from ngabo.application.use_cases.orchestrate_canonical_import import (
    OrchestrateCanonicalImport,
)
from ngabo.application.value_objects.canonical_import_result import (
    CanonicalImportResult,
)
from ngabo.application.value_objects.import_error_detail import ImportErrorDetail
from ngabo.domain.entities.ast_observation import AstObservation
from ngabo.domain.entities.canonical_import_batch import CanonicalImportBatch
from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.enums.interpretation import Interpretation
from ngabo.domain.value_objects.source_digest import SourceDigest
from ngabo.domain.value_objects.source_watermark import SourceWatermark
from ngabo.interfaces.parsers.whonet_csv_parser import parse_whonet_csv

REPO_ROOT = Path(__file__).resolve().parents[3]
HERO_CSV_PATH = REPO_ROOT / "data" / "synthetic" / "canonical_hero.csv"
HERO_JSON_PATH = REPO_ROOT / "data" / "synthetic" / "canonical_hero.json"

PINNED_HERO_RAW_DIGEST = (
    "sha256:6b6bbc9a8d1f0e44419aee4ed4bdd073d965bab7507961307dcd051b4dae926b"
)
PINNED_HERO_SOURCE_WATERMARK = (
    "ngabo-source-v1:sha256:b1b00a5938f2515c77cf144ec4bf5731bcaa9406265996941818f914567cd94c"
)

SAMPLE_VALID_CSV = (
    "ISOLATE_ID,COLLECTION_DATE,ORGANISM_CODE,ORGANISM_NAME,"
    "FACILITY_ID,LAB_ID,WARD,SPECIMEN_TYPE,PATIENT_TOKEN,SOURCE_IMPORT_ID,AMK\n"
    "ISO-001,2026-08-16,eco,Escherichia coli,"
    "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,S\n"
)


# ============================================================================
# In-Memory Fakes (Framework-Free Application Seams)
# ============================================================================


class InMemorySourceLoader:
    """In-memory source loader fake for controlled test environments."""

    def __init__(self, initial_sources: dict[str, bytes] | None = None) -> None:
        self._sources: dict[str, bytes] = dict(initial_sources or {})

    def add_source(self, location: str, data: bytes) -> None:
        self._sources[location] = data

    def __call__(self, location: str) -> bytes:
        if location not in self._sources:
            raise KeyError(f"Source not found at location: {location!r}")
        return self._sources[location]


class InMemorySourceReplayRepository:
    """In-memory replay repository fake with atomic accept_watermark semantics."""

    def __init__(
        self, initial_watermarks: dict[str, SourceWatermark] | None = None
    ) -> None:
        self._watermarks: dict[str, SourceWatermark] = dict(initial_watermarks or {})
        self.accept_calls: list[tuple[str, SourceWatermark]] = []

    def accept_watermark(
        self, source_key: str, current: SourceWatermark
    ) -> SourceWatermark | None:
        """Atomically read previous watermark, record current, and return previous."""
        self.accept_calls.append((source_key, current))
        previous = self._watermarks.get(source_key)
        self._watermarks[source_key] = current
        return previous

    def get_stored_watermark(self, source_key: str) -> SourceWatermark | None:
        """Helper to inspect repository state during tests."""
        return self._watermarks.get(source_key)


def _make_dummy_batch() -> CanonicalImportBatch:
    return CanonicalImportBatch(
        (
            CanonicalIsolate(
                isolate_id="ISO-001",
                collection_date=date(2026, 8, 16),
                organism_code="eco",
                organism_name="Escherichia coli",
                facility_id="SYNTH-FACILITY-001",
                lab_id="SYNTH-LAB-001",
                ward="SYNTH-WARD-A",
                specimen_type="blood",
                patient_token="SYNTH-CASE-001",
                source_import_id="SYNTH-IMPORT-001",
                ast_results=MappingProxyType(
                    {"AMK": AstObservation(Interpretation.SUSCEPTIBLE)}
                ),
            ),
        )
    )


# ============================================================================
# 1. Hero CSV Through Application Use Case Tests
# ============================================================================


class TestHeroCanonicalImport:
    def test_canonical_hero_csv_produces_exact_hero_batch_and_disposition(
        self,
    ) -> None:
        hero_bytes = HERO_CSV_PATH.read_bytes()
        loader = InMemorySourceLoader({"hero_loc": hero_bytes})
        repo = InMemorySourceReplayRepository()

        use_case = OrchestrateCanonicalImport(
            source_loader=loader,
            replay_repo=repo,
            parser=parse_whonet_csv,
        )
        command = ImportCanonicalSourceCommand(
            source_key="hero_source",
            source_location="hero_loc",
        )
        result = use_case.execute(command)

        assert result.success is True
        assert result.disposition == ImportOutcomeDisposition.FIRST_IMPORT
        assert result.source_key == "hero_source"
        assert result.raw_digest is not None
        assert str(result.raw_digest) == PINNED_HERO_RAW_DIGEST
        assert result.watermark is not None
        assert result.watermark.value == PINNED_HERO_SOURCE_WATERMARK
        assert result.batch is not None
        assert len(result.batch.records) == 8
        assert result.exact_duplicates == ()
        assert result.errors == ()

        # Value-for-value verification against committed canonical hero JSON
        json_data = json.loads(HERO_JSON_PATH.read_text(encoding="utf-8"))
        expected_records = json_data["records"]
        assert len(result.batch.records) == len(expected_records)

        for actual, expected in zip(result.batch.records, expected_records, strict=True):
            assert actual.isolate_id == expected["isolate_id"]
            assert actual.collection_date.isoformat() == expected["collection_date"]
            assert actual.organism_code == expected["organism_code"]
            assert actual.organism_name == expected["organism_name"]
            assert actual.facility_id == expected["facility_id"]
            assert actual.lab_id == expected["lab_id"]
            assert actual.ward == expected["ward"]
            assert actual.specimen_type == expected["specimen_type"]
            assert actual.patient_token == expected["patient_token"]
            assert actual.source_import_id == expected["source_import_id"]

            actual_ast = {
                code: obs.interpretation.value
                for code, obs in actual.ast_results.items()
            }
            expected_ast = {
                code: data["interpretation"]
                for code, data in expected["ast_results"].items()
            }
            assert actual_ast == expected_ast

        # Verified repository stored the accepted watermark
        assert repo.get_stored_watermark("hero_source") == result.watermark

        # Second invocation of unchanged hero automatically produces EXACT_REPLAY
        second_result = use_case.execute(command)
        assert second_result.success is True
        assert second_result.disposition == ImportOutcomeDisposition.EXACT_REPLAY
        assert second_result.watermark == result.watermark
        assert second_result.raw_digest == result.raw_digest


# ============================================================================
# 2. First Import, Exact Replay, and Material Change Tests
# ============================================================================


class TestReplayOutcomes:
    def test_first_import_when_no_prior_watermark_exists(self) -> None:
        loader = InMemorySourceLoader({"data_a": SAMPLE_VALID_CSV.encode("utf-8")})
        repo = InMemorySourceReplayRepository()
        use_case = OrchestrateCanonicalImport(loader, repo, parse_whonet_csv)

        cmd = ImportCanonicalSourceCommand("source_1", "data_a")
        res = use_case(cmd)

        assert res.success is True
        assert res.disposition == ImportOutcomeDisposition.FIRST_IMPORT
        assert res.batch is not None
        assert len(res.batch.records) == 1
        assert res.watermark is not None
        assert repo.get_stored_watermark("source_1") == res.watermark

    def test_exact_replay_automatic_without_manual_seeding(self) -> None:
        csv_bytes = SAMPLE_VALID_CSV.encode("utf-8")
        loader = InMemorySourceLoader({"data_a": csv_bytes})
        repo = InMemorySourceReplayRepository()
        use_case = OrchestrateCanonicalImport(loader, repo, parse_whonet_csv)

        cmd = ImportCanonicalSourceCommand("source_1", "data_a")
        first_res = use_case(cmd)
        assert first_res.success is True
        assert first_res.disposition == ImportOutcomeDisposition.FIRST_IMPORT
        assert first_res.watermark is not None

        # Second invocation of unchanged source automatically produces EXACT_REPLAY
        replay_res = use_case(cmd)
        assert replay_res.success is True
        assert replay_res.disposition == ImportOutcomeDisposition.EXACT_REPLAY
        assert replay_res.watermark == first_res.watermark
        assert replay_res.batch == first_res.batch
        assert replay_res.raw_digest == first_res.raw_digest
        assert replay_res.errors == ()
        assert len(repo.accept_calls) == 2

    def test_material_change_advances_baseline_and_leads_to_exact_replay(self) -> None:
        csv_bytes_1 = SAMPLE_VALID_CSV.encode("utf-8")
        csv_bytes_2 = (
            b"ISOLATE_ID,COLLECTION_DATE,ORGANISM_CODE,ORGANISM_NAME,"
            b"FACILITY_ID,LAB_ID,WARD,SPECIMEN_TYPE,PATIENT_TOKEN,SOURCE_IMPORT_ID,AMK\n"
            b"ISO-002,2026-08-16,eco,Escherichia coli,"
            b"SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,blood,SYNTH-CASE-002,SYNTH-IMPORT-001,R\n"
        )
        loader = InMemorySourceLoader({"data_a": csv_bytes_1})
        repo = InMemorySourceReplayRepository()
        use_case = OrchestrateCanonicalImport(loader, repo, parse_whonet_csv)

        cmd = ImportCanonicalSourceCommand("source_1", "data_a")

        # Call 1: W1 -> FIRST_IMPORT
        res1 = use_case(cmd)
        assert res1.success is True
        assert res1.disposition == ImportOutcomeDisposition.FIRST_IMPORT
        assert res1.watermark is not None
        assert repo.get_stored_watermark("source_1") == res1.watermark

        # Call 2: Source content changes to W2 -> MATERIAL_CHANGE
        loader.add_source("data_a", csv_bytes_2)
        res2 = use_case(cmd)
        assert res2.success is True
        assert res2.disposition == ImportOutcomeDisposition.MATERIAL_CHANGE
        assert res2.watermark is not None
        assert res2.watermark != res1.watermark
        assert repo.get_stored_watermark("source_1") == res2.watermark

        # Call 3: Source unchanged W2 -> EXACT_REPLAY
        res3 = use_case(cmd)
        assert res3.success is True
        assert res3.disposition == ImportOutcomeDisposition.EXACT_REPLAY
        assert res3.watermark == res2.watermark
        assert repo.get_stored_watermark("source_1") == res2.watermark
        assert len(repo.accept_calls) == 3


# ============================================================================
# 3. Duplicate Records Handling Tests
# ============================================================================


class TestDuplicateRecordHandling:
    def test_exact_duplicate_records_collapse_before_replay_comparison(self) -> None:
        csv_with_exact_dup = (
            "ISOLATE_ID,COLLECTION_DATE,ORGANISM_CODE,ORGANISM_NAME,"
            "FACILITY_ID,LAB_ID,WARD,SPECIMEN_TYPE,PATIENT_TOKEN,SOURCE_IMPORT_ID,AMK\n"
            "ISO-001,2026-08-16,eco,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,S\n"
            "ISO-001,2026-08-16,eco,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,S\n"
        )
        loader = InMemorySourceLoader({"dup_loc": csv_with_exact_dup.encode("utf-8")})
        repo = InMemorySourceReplayRepository()
        use_case = OrchestrateCanonicalImport(loader, repo, parse_whonet_csv)

        cmd = ImportCanonicalSourceCommand("source_dup", "dup_loc")
        res = use_case(cmd)

        assert res.success is True
        assert res.disposition == ImportOutcomeDisposition.FIRST_IMPORT
        assert res.batch is not None
        assert len(res.batch.records) == 1
        assert len(res.exact_duplicates) == 1
        assert res.exact_duplicates[0].isolate_id == "ISO-001"
        assert res.exact_duplicates[0].occurrences == 2
        assert res.exact_duplicates[0].original_index == 0
        assert res.exact_duplicates[0].duplicate_indices == (1,)

    def test_conflicting_duplicate_records_fail_closed_without_modifying_repo(
        self,
    ) -> None:
        csv_with_conflict = (
            "ISOLATE_ID,COLLECTION_DATE,ORGANISM_CODE,ORGANISM_NAME,"
            "FACILITY_ID,LAB_ID,WARD,SPECIMEN_TYPE,PATIENT_TOKEN,SOURCE_IMPORT_ID,AMK\n"
            "ISO-001,2026-08-16,eco,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,S\n"
            "ISO-001,2026-08-16,eco,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,R\n"
        )
        loader = InMemorySourceLoader({"conflict_loc": csv_with_conflict.encode("utf-8")})
        repo = InMemorySourceReplayRepository()
        use_case = OrchestrateCanonicalImport(loader, repo, parse_whonet_csv)

        cmd = ImportCanonicalSourceCommand("source_conflict", "conflict_loc")
        res = use_case(cmd)

        assert res.success is False
        assert res.disposition == ImportOutcomeDisposition.FAILED
        assert res.batch is None
        assert res.watermark is None
        assert res.raw_digest is not None
        assert len(res.errors) == 1
        assert res.errors[0].code == ImportErrorCode.CONFLICTING_DUPLICATE_RECORD
        assert res.errors[0].isolate_id == "ISO-001"
        assert "ast_results" in res.errors[0].differing_fields

        # Conflicting duplicates fail before repo acceptance
        assert len(repo.accept_calls) == 0
        assert repo.get_stored_watermark("source_conflict") is None


# ============================================================================
# 4. Raw Source & UTF-8 Decode Failures Tests
# ============================================================================


class TestRawSourceAndDecode:
    def test_raw_bytes_hashed_before_decoding(self) -> None:
        raw_bytes = SAMPLE_VALID_CSV.encode("utf-8")
        loader = InMemorySourceLoader({"raw_loc": raw_bytes})
        repo = InMemorySourceReplayRepository()
        use_case = OrchestrateCanonicalImport(loader, repo, parse_whonet_csv)

        cmd = ImportCanonicalSourceCommand("src_raw", "raw_loc")
        res = use_case(cmd)
        assert res.raw_digest is not None
        assert str(res.raw_digest).startswith("sha256:")

    def test_invalid_utf8_fails_closed_preserving_raw_digest_without_repo_call(
        self,
    ) -> None:
        bad_utf8 = b"\xff\xfe\x00\x00malformed_bytes"
        loader = InMemorySourceLoader({"bad_utf8": bad_utf8})
        repo = InMemorySourceReplayRepository()
        use_case = OrchestrateCanonicalImport(loader, repo, parse_whonet_csv)

        cmd = ImportCanonicalSourceCommand("bad_src", "bad_utf8")
        res = use_case(cmd)

        assert res.success is False
        assert res.disposition == ImportOutcomeDisposition.FAILED
        assert res.batch is None
        assert res.watermark is None
        assert res.raw_digest is not None
        assert len(res.errors) == 1
        assert res.errors[0].code == ImportErrorCode.UTF8_DECODE_ERROR
        assert "not valid UTF-8" in res.errors[0].message
        assert len(repo.accept_calls) == 0


# ============================================================================
# 5. Parser & Canonical Validation Failure Tests
# ============================================================================


class TestParserFailures:
    def test_malformed_csv_missing_columns_fails_closed_preserving_raw_digest(
        self,
    ) -> None:
        bad_csv = b"ISOLATE_ID,COLLECTION_DATE\nISO-001,2026-08-16\n"
        loader = InMemorySourceLoader({"bad_csv": bad_csv})
        repo = InMemorySourceReplayRepository()
        use_case = OrchestrateCanonicalImport(loader, repo, parse_whonet_csv)

        cmd = ImportCanonicalSourceCommand("bad_csv_src", "bad_csv")
        res = use_case(cmd)

        assert res.success is False
        assert res.disposition == ImportOutcomeDisposition.FAILED
        assert res.batch is None
        assert res.watermark is None
        assert res.raw_digest is not None
        assert len(res.errors) > 0
        assert any(e.code == ImportErrorCode.PARSER_FAILURE for e in res.errors)
        assert len(repo.accept_calls) == 0

    def test_invalid_synthetic_id_preserves_error_code_and_record_index(
        self,
    ) -> None:
        bad_synth_id_csv = (
            b"ISOLATE_ID,COLLECTION_DATE,ORGANISM_CODE,ORGANISM_NAME,"
            b"FACILITY_ID,LAB_ID,WARD,SPECIMEN_TYPE,PATIENT_TOKEN,SOURCE_IMPORT_ID,AMK\n"
            b"ISO-001,2026-08-16,eco,Escherichia coli,"
            b"REAL-HOSPITAL-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,S\n"
        )
        loader = InMemorySourceLoader({"bad_synth": bad_synth_id_csv})
        repo = InMemorySourceReplayRepository()
        use_case = OrchestrateCanonicalImport(loader, repo, parse_whonet_csv)

        cmd = ImportCanonicalSourceCommand("bad_synth_src", "bad_synth")
        res = use_case(cmd)

        assert res.success is False
        assert res.disposition == ImportOutcomeDisposition.FAILED
        assert res.batch is None
        assert res.watermark is None
        assert res.raw_digest is not None
        assert len(res.errors) == 1
        err = res.errors[0]
        assert err.code == ImportErrorCode.PARSER_FAILURE
        assert err.source_code == "INVALID_SYNTHETIC_ID"
        assert err.record_index == 0
        assert err.line_number == 2
        assert err.field == "FACILITY_ID"
        assert "SYNTH-" in err.message
        assert len(repo.accept_calls) == 0

    def test_canonical_validation_error_maps_to_canonical_validation_failure(
        self,
    ) -> None:
        class FakeParserError:
            def __init__(self) -> None:
                self.code = "CANONICAL_VALIDATION_ERROR"
                self.detail = "Invalid date format"
                self.column = "collection_date"
                self.row_number = 2
                self.record_index = 0
                self.record_id = "ISO-001"

        class FakeParserResult:
            def __init__(self) -> None:
                self.success = False
                self.batch = None
                self.errors = (FakeParserError(),)

        def mock_parser(source: str) -> ParsedSourceResult:
            return FakeParserResult()

        loader = InMemorySourceLoader({"data": SAMPLE_VALID_CSV.encode("utf-8")})
        repo = InMemorySourceReplayRepository()
        use_case = OrchestrateCanonicalImport(loader, repo, mock_parser)

        cmd = ImportCanonicalSourceCommand("src_cve", "data")
        res = use_case(cmd)

        assert res.success is False
        assert res.disposition == ImportOutcomeDisposition.FAILED
        assert len(res.errors) == 1
        err = res.errors[0]
        assert err.code == ImportErrorCode.CANONICAL_VALIDATION_FAILURE
        assert err.source_code == "CANONICAL_VALIDATION_ERROR"
        assert err.field == "collection_date"
        assert err.line_number == 2
        assert err.record_index == 0
        assert err.isolate_id == "ISO-001"

    def test_parser_exception_fails_closed_preserving_raw_digest(self) -> None:
        def throwing_parser(source: str) -> ParsedSourceResult:
            raise RuntimeError("Parser engine crashed unexpectedly")

        loader = InMemorySourceLoader({"data": SAMPLE_VALID_CSV.encode("utf-8")})
        repo = InMemorySourceReplayRepository()
        use_case = OrchestrateCanonicalImport(loader, repo, throwing_parser)

        cmd = ImportCanonicalSourceCommand("src_crash", "data")
        res = use_case(cmd)

        assert res.success is False
        assert res.disposition == ImportOutcomeDisposition.FAILED
        assert res.raw_digest is not None
        assert res.batch is None
        assert res.watermark is None
        assert len(res.errors) == 1
        assert res.errors[0].code == ImportErrorCode.PARSER_FAILURE
        assert "Parser engine crashed unexpectedly" in res.errors[0].message
        assert len(repo.accept_calls) == 0

    def test_injected_parser_returning_invalid_result_object_fails_closed(
        self,
    ) -> None:
        def invalid_parser(source: str) -> Any:
            return "not-a-result-object"

        loader = InMemorySourceLoader({"data": SAMPLE_VALID_CSV.encode("utf-8")})
        repo = InMemorySourceReplayRepository()
        use_case = OrchestrateCanonicalImport(loader, repo, invalid_parser)

        cmd = ImportCanonicalSourceCommand("src_bad_parser", "data")
        res = use_case(cmd)

        assert res.success is False
        assert res.disposition == ImportOutcomeDisposition.FAILED
        assert res.raw_digest is not None
        assert res.errors[0].code == ImportErrorCode.PARSER_FAILURE
        assert "invalid result object" in res.errors[0].message

    def test_no_parser_row_silently_disappears(self) -> None:
        hdr = (
            "ISOLATE_ID,COLLECTION_DATE,ORGANISM_CODE,ORGANISM_NAME,"
            "FACILITY_ID,LAB_ID,WARD,SPECIMEN_TYPE,PATIENT_TOKEN,SOURCE_IMPORT_ID,AMK\n"
        )
        r1 = (
            "ISO-001,2026-08-16,eco,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,S\n"
        )
        r2 = (
            "ISO-002,2026-08-16,eco,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,blood,SYNTH-CASE-002,SYNTH-IMPORT-001,R\n"
        )
        r3 = (
            "ISO-003,2026-08-16,kle,Klebsiella pneumoniae,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-B,sputum,SYNTH-CASE-003,SYNTH-IMPORT-001,I\n"
        )
        csv_multi = (hdr + r1 + r2 + r3).encode("utf-8")
        loader = InMemorySourceLoader({"multi": csv_multi})
        repo = InMemorySourceReplayRepository()
        use_case = OrchestrateCanonicalImport(loader, repo, parse_whonet_csv)

        cmd = ImportCanonicalSourceCommand("multi_src", "multi")
        res = use_case(cmd)

        assert res.success is True
        assert res.batch is not None
        assert len(res.batch.records) == 3
        assert [r.isolate_id for r in res.batch.records] == ["ISO-001", "ISO-002", "ISO-003"]


# ============================================================================
# 6. Port Failures Tests
# ============================================================================


class TestPortFailures:
    def test_source_loader_failure_returns_source_read_error_without_raw_digest(
        self,
    ) -> None:
        loader = InMemorySourceLoader({})  # missing location
        repo = InMemorySourceReplayRepository()
        use_case = OrchestrateCanonicalImport(loader, repo, parse_whonet_csv)

        cmd = ImportCanonicalSourceCommand("src_missing", "non_existent_loc")
        res = use_case(cmd)

        assert res.success is False
        assert res.disposition == ImportOutcomeDisposition.FAILED
        assert res.raw_digest is None
        assert res.batch is None
        assert res.watermark is None
        assert len(res.errors) == 1
        assert res.errors[0].code == ImportErrorCode.SOURCE_READ_ERROR

    def test_source_loader_returning_non_bytes_fails_closed(self) -> None:
        def bad_loader(location: str) -> bytes:
            return "not-bytes"  # type: ignore[return-value]

        repo = InMemorySourceReplayRepository()
        use_case = OrchestrateCanonicalImport(bad_loader, repo, parse_whonet_csv)

        cmd = ImportCanonicalSourceCommand("src_bad_ret", "any_loc")
        res = use_case(cmd)

        assert res.success is False
        assert res.disposition == ImportOutcomeDisposition.FAILED
        assert res.raw_digest is None
        assert res.errors[0].code == ImportErrorCode.SOURCE_READ_ERROR

    def test_repository_acceptance_failure_returns_repository_error_preserving_raw_digest(
        self,
    ) -> None:
        class FailingReplayRepo:
            def accept_watermark(
                self, source_key: str, current: SourceWatermark
            ) -> SourceWatermark | None:
                raise RuntimeError("Database connection timed out")

        loader = InMemorySourceLoader({"data": SAMPLE_VALID_CSV.encode("utf-8")})
        use_case = OrchestrateCanonicalImport(loader, FailingReplayRepo(), parse_whonet_csv)

        cmd = ImportCanonicalSourceCommand("src_repo_err", "data")
        res = use_case(cmd)

        assert res.success is False
        assert res.disposition == ImportOutcomeDisposition.FAILED
        assert res.raw_digest is not None
        assert res.batch is None
        assert res.watermark is None
        assert len(res.errors) == 1
        assert res.errors[0].code == ImportErrorCode.REPOSITORY_ERROR
        assert "Database connection timed out" in res.errors[0].message

    def test_invalid_repository_return_type_fails_closed(self) -> None:
        class CorruptReplayRepo:
            def accept_watermark(
                self, source_key: str, current: SourceWatermark
            ) -> Any:
                return "corrupt-watermark-string"

        loader = InMemorySourceLoader({"data": SAMPLE_VALID_CSV.encode("utf-8")})
        use_case = OrchestrateCanonicalImport(loader, CorruptReplayRepo(), parse_whonet_csv)

        cmd = ImportCanonicalSourceCommand("src_corrupt_repo", "data")
        res = use_case(cmd)

        assert res.success is False
        assert res.disposition == ImportOutcomeDisposition.FAILED
        assert res.raw_digest is not None
        assert res.batch is None
        assert res.watermark is None
        assert len(res.errors) == 1
        assert res.errors[0].code == ImportErrorCode.REPOSITORY_ERROR
        assert "Invalid repository return type" in res.errors[0].message


# ============================================================================
# 7. Invariants, Immutability, and Determinism Tests
# ============================================================================


class TestInvariantsAndDeterminism:
    def test_command_validation_invariants(self) -> None:
        with pytest.raises(ValueError, match="source_key must be a non-empty string"):
            ImportCanonicalSourceCommand("", "loc")

        with pytest.raises(ValueError, match="source_location must be a non-empty string"):
            ImportCanonicalSourceCommand("key", "")

    def test_use_case_constructor_validation(self) -> None:
        repo = InMemorySourceReplayRepository()
        loader = InMemorySourceLoader()

        with pytest.raises(TypeError, match="expected callable"):
            OrchestrateCanonicalImport("not-a-loader", repo, parse_whonet_csv)  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="expected SourceReplayRepository"):
            OrchestrateCanonicalImport(loader, "not-a-repo", parse_whonet_csv)  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="expected callable ParseCanonicalSource"):
            OrchestrateCanonicalImport(loader, repo, "not-a-parser")  # type: ignore[arg-type]

    def test_result_immutability_and_contradictory_rejection(self) -> None:
        # Cannot assign attributes to frozen dataclass
        res = CanonicalImportResult(
            success=False,
            disposition=ImportOutcomeDisposition.FAILED,
            source_key="k",
            errors=(
                ImportErrorDetail(code=ImportErrorCode.SOURCE_READ_ERROR, message="err"),
            ),
        )
        with pytest.raises(AttributeError):
            res.success = True  # type: ignore[misc]

        dummy_batch = _make_dummy_batch()

        # Success with FAILED disposition rejected
        with pytest.raises(ValueError, match="cannot have disposition"):
            CanonicalImportResult(
                success=True,
                disposition=ImportOutcomeDisposition.FAILED,
                source_key="k",
                raw_digest=SourceDigest("sha256", "a" * 64),
                watermark=SourceWatermark("ngabo-source-v1:sha256:" + "a" * 64),
                batch=dummy_batch,
            )

        # Success missing batch rejected
        with pytest.raises(ValueError, match="requires a valid batch"):
            CanonicalImportResult(
                success=True,
                disposition=ImportOutcomeDisposition.FIRST_IMPORT,
                source_key="k",
                raw_digest=SourceDigest("sha256", "a" * 64),
                watermark=SourceWatermark("ngabo-source-v1:sha256:" + "a" * 64),
                batch=None,
            )

        # Failure with batch rejected
        with pytest.raises(ValueError, match="must not have an accepted batch"):
            CanonicalImportResult(
                success=False,
                disposition=ImportOutcomeDisposition.FAILED,
                source_key="k",
                batch=dummy_batch,
                errors=(
                    ImportErrorDetail(code=ImportErrorCode.SOURCE_READ_ERROR, message="err"),
                ),
            )

        # Failure with watermark rejected
        with pytest.raises(ValueError, match="must not have a watermark"):
            CanonicalImportResult(
                success=False,
                disposition=ImportOutcomeDisposition.FAILED,
                source_key="k",
                watermark=SourceWatermark("ngabo-source-v1:sha256:" + "a" * 64),
                errors=(
                    ImportErrorDetail(code=ImportErrorCode.SOURCE_READ_ERROR, message="err"),
                ),
            )

        # Failure without errors rejected
        with pytest.raises(ValueError, match="must contain at least one error"):
            CanonicalImportResult(
                success=False,
                disposition=ImportOutcomeDisposition.FAILED,
                source_key="k",
                errors=(),
            )

    def test_import_error_detail_invariants(self) -> None:
        with pytest.raises(TypeError, match="expected ImportErrorCode"):
            ImportErrorDetail(code="NOT_A_CODE", message="err")  # type: ignore[arg-type]

        with pytest.raises(ValueError, match="message must be a non-empty string"):
            ImportErrorDetail(code=ImportErrorCode.SOURCE_READ_ERROR, message="")

        with pytest.raises(TypeError, match="expected tuple of integers"):
            ImportErrorDetail(
                code=ImportErrorCode.SOURCE_READ_ERROR,
                message="err",
                indices=[0],  # type: ignore[arg-type]
            )

        with pytest.raises(ValueError, match="expected non-negative integer"):
            ImportErrorDetail(
                code=ImportErrorCode.SOURCE_READ_ERROR,
                message="err",
                indices=(-1,),
            )

        with pytest.raises(ValueError, match="expected non-negative integer"):
            ImportErrorDetail(
                code=ImportErrorCode.SOURCE_READ_ERROR,
                message="err",
                record_index=-1,
            )

        with pytest.raises(ValueError, match="expected positive integer"):
            ImportErrorDetail(
                code=ImportErrorCode.SOURCE_READ_ERROR,
                message="err",
                line_number=0,
            )

        with pytest.raises(TypeError, match="expected tuple of strings"):
            ImportErrorDetail(
                code=ImportErrorCode.SOURCE_READ_ERROR,
                message="err",
                differing_fields=["field"],  # type: ignore[arg-type]
            )

        with pytest.raises(ValueError, match="differing_fields must contain non-empty strings"):
            ImportErrorDetail(
                code=ImportErrorCode.SOURCE_READ_ERROR,
                message="err",
                differing_fields=("",),
            )

        with pytest.raises(ValueError, match="source_code must be a non-empty string"):
            ImportErrorDetail(
                code=ImportErrorCode.SOURCE_READ_ERROR,
                message="err",
                source_code="",
            )

    def test_repeated_same_command_and_same_fake_state_produces_equal_result(
        self,
    ) -> None:
        csv_bytes = SAMPLE_VALID_CSV.encode("utf-8")
        loader = InMemorySourceLoader({"loc_1": csv_bytes})
        repo = InMemorySourceReplayRepository()
        use_case = OrchestrateCanonicalImport(loader, repo, parse_whonet_csv)

        cmd = ImportCanonicalSourceCommand("source_key_det", "loc_1")
        # Call 1 -> FIRST_IMPORT
        res_1 = use_case.execute(cmd)
        assert res_1.disposition == ImportOutcomeDisposition.FIRST_IMPORT

        # Call 2 -> EXACT_REPLAY
        res_2 = use_case.execute(cmd)
        assert res_2.disposition == ImportOutcomeDisposition.EXACT_REPLAY

        # Call 3 -> EXACT_REPLAY (idempotent result)
        res_3 = use_case.execute(cmd)
        assert res_2 == res_3
        assert res_2.disposition == res_3.disposition
        assert res_2.watermark == res_3.watermark
        assert res_2.raw_digest == res_3.raw_digest
        assert res_2.batch == res_3.batch

    def test_atomic_replay_port_contract_simulation(self) -> None:
        """Simulate two concurrent first deliveries using the atomic accept_watermark method.

        In a transactional store, accept_watermark executes atomically under concurrency:
        - Exactly one call observes previous is None -> FIRST_IMPORT
        - The other call observes previous is W1 -> EXACT_REPLAY
        Both callers observe valid deterministic outcomes without duplicate ingestion work.
        """
        wm = SourceWatermark("ngabo-source-v1:sha256:" + "e" * 64)
        repo = InMemorySourceReplayRepository()

        # Delivery A
        prev_a = repo.accept_watermark("source_concurrent", wm)
        # Delivery B
        prev_b = repo.accept_watermark("source_concurrent", wm)

        assert prev_a is None  # Winner of race
        assert prev_b == wm  # Follower observed already-accepted state
