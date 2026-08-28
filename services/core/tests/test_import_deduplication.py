"""Focused tests for canonical import deduplication and duplicate detection (Issue #40)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from ngabo.domain.entities.ast_observation import AstObservation
from ngabo.domain.entities.canonical_import_batch import CanonicalImportBatch
from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.enums.import_deduplication_error_code import ImportDeduplicationErrorCode
from ngabo.domain.enums.interpretation import Interpretation
from ngabo.domain.services.import_deduplication import deduplicate_canonical_batch
from ngabo.domain.value_objects.duplicate_record_finding import DuplicateRecordFinding
from ngabo.domain.value_objects.import_deduplication_error import ImportDeduplicationError
from ngabo.domain.value_objects.import_deduplication_report import ImportDeduplicationReport
from ngabo.domain.value_objects.source_watermark import SourceWatermark
from ngabo.interfaces.parsers.whonet_csv_parser import parse_whonet_csv

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
HERO_CSV_PATH = DATA_DIR / "synthetic" / "canonical_hero.csv"
PINNED_HERO_SOURCE_WATERMARK = (
    "ngabo-source-v1:sha256:b1b00a5938f2515c77cf144ec4bf5731bcaa9406265996941818f914567cd94c"
)


def _make_isolate(
    isolate_id: str = "ISO-001",
    collection_date: date = date(2026, 8, 16),
    organism_code: str = "eco",
    organism_name: str = "Escherichia coli",
    facility_id: str = "SYNTH-FACILITY-001",
    lab_id: str = "SYNTH-LAB-001",
    ward: str = "SYNTH-WARD-A",
    specimen_type: str = "blood",
    patient_token: str = "SYNTH-CASE-001",
    source_import_id: str = "SYNTH-IMPORT-001",
    ast_results: dict[str, Interpretation] | None = None,
) -> CanonicalIsolate:
    if ast_results is None:
        ast_results = {
            "AMK": Interpretation.SUSCEPTIBLE,
            "CIP": Interpretation.RESISTANT,
        }
    typed_ast = {k: AstObservation(v) for k, v in ast_results.items()}
    return CanonicalIsolate(
        isolate_id=isolate_id,
        collection_date=collection_date,
        organism_code=organism_code,
        organism_name=organism_name,
        facility_id=facility_id,
        lab_id=lab_id,
        ward=ward,
        specimen_type=specimen_type,
        patient_token=patient_token,
        source_import_id=source_import_id,
        ast_results=typed_ast,
    )


# ============================================================================
# Unique Records Tests
# ============================================================================


class TestUniqueRecordsDeduplication:
    def test_single_unique_record_succeeds_unchanged(self) -> None:
        iso = _make_isolate("ISO-001")
        batch = CanonicalImportBatch(records=(iso,))
        report = deduplicate_canonical_batch(batch)

        assert report.success is True
        assert report.batch is not None
        assert len(report.batch.records) == 1
        assert report.batch.records[0] == iso
        assert report.watermark is not None
        assert report.exact_duplicates == ()
        assert report.errors == ()

    def test_multiple_unique_records_preserve_exact_source_order(self) -> None:
        iso_b = _make_isolate("ISO-030")
        iso_a = _make_isolate("ISO-010")
        iso_c = _make_isolate("ISO-020")

        batch = CanonicalImportBatch(records=(iso_b, iso_a, iso_c))
        report = deduplicate_canonical_batch(batch)

        assert report.success is True
        assert report.batch is not None
        # Must preserve original source order: ISO-030, ISO-010, ISO-020
        assert [r.isolate_id for r in report.batch.records] == ["ISO-030", "ISO-010", "ISO-020"]
        assert report.exact_duplicates == ()
        assert report.errors == ()


# ============================================================================
# Exact Duplicate Records Tests
# ============================================================================


class TestExactDuplicateRecords:
    def test_exact_duplicate_collapses_to_one_canonical_record(self) -> None:
        iso_1 = _make_isolate("ISO-001")
        iso_2 = _make_isolate("ISO-002")
        iso_1_dup = _make_isolate("ISO-001")  # identical to iso_1

        batch = CanonicalImportBatch(records=(iso_1, iso_2, iso_1_dup))
        report = deduplicate_canonical_batch(batch)

        assert report.success is True
        assert report.batch is not None
        assert len(report.batch.records) == 2
        assert [r.isolate_id for r in report.batch.records] == ["ISO-001", "ISO-002"]
        assert len(report.exact_duplicates) == 1

        finding = report.exact_duplicates[0]
        assert finding.isolate_id == "ISO-001"
        assert finding.occurrences == 2
        assert finding.original_index == 0
        assert finding.duplicate_indices == (2,)

    def test_multiple_duplicates_of_same_record(self) -> None:
        iso = _make_isolate("ISO-001")
        batch = CanonicalImportBatch(records=(iso, iso, iso))
        report = deduplicate_canonical_batch(batch)

        assert report.success is True
        assert report.batch is not None
        assert len(report.batch.records) == 1
        assert len(report.exact_duplicates) == 1

        finding = report.exact_duplicates[0]
        assert finding.isolate_id == "ISO-001"
        assert finding.occurrences == 3
        assert finding.original_index == 0
        assert finding.duplicate_indices == (1, 2)

    def test_multiple_distinct_duplicate_groups(self) -> None:
        iso_1 = _make_isolate("ISO-001")
        iso_2 = _make_isolate("ISO-002")
        batch = CanonicalImportBatch(records=(iso_1, iso_2, iso_1, iso_2))
        report = deduplicate_canonical_batch(batch)

        assert report.success is True
        assert report.batch is not None
        assert [r.isolate_id for r in report.batch.records] == ["ISO-001", "ISO-002"]
        assert len(report.exact_duplicates) == 2

        f1 = report.exact_duplicates[0]
        assert f1.isolate_id == "ISO-001"
        assert f1.original_index == 0
        assert f1.duplicate_indices == (2,)

        f2 = report.exact_duplicates[1]
        assert f2.isolate_id == "ISO-002"
        assert f2.original_index == 1
        assert f2.duplicate_indices == (3,)


# ============================================================================
# Conflicting Duplicate Records (Fail Closed) Tests
# ============================================================================


class TestConflictingDuplicateRecordsFailClosed:
    def test_different_ast_results_fails_closed(self) -> None:
        iso_original = _make_isolate(
            "ISO-001",
            ast_results={"AMK": Interpretation.SUSCEPTIBLE},
        )
        iso_conflict = _make_isolate(
            "ISO-001",
            ast_results={"AMK": Interpretation.RESISTANT},
        )
        batch = CanonicalImportBatch(records=(iso_original, iso_conflict))
        report = deduplicate_canonical_batch(batch)

        assert report.success is False
        assert report.batch is None
        assert report.watermark is None
        assert len(report.errors) == 1

        err = report.errors[0]
        assert err.code == ImportDeduplicationErrorCode.CONFLICTING_DUPLICATE_RECORD
        assert err.isolate_id == "ISO-001"
        assert err.indices == (0, 1)
        assert "ast_results" in err.differing_fields
        assert "differing fields: ast_results" in (err.detail or "")

    def test_different_collection_date_fails_closed(self) -> None:
        iso_original = _make_isolate("ISO-001", collection_date=date(2026, 8, 16))
        iso_conflict = _make_isolate("ISO-001", collection_date=date(2026, 8, 17))
        batch = CanonicalImportBatch(records=(iso_original, iso_conflict))
        report = deduplicate_canonical_batch(batch)

        assert report.success is False
        assert report.batch is None
        assert len(report.errors) == 1

        err = report.errors[0]
        assert err.code == ImportDeduplicationErrorCode.CONFLICTING_DUPLICATE_RECORD
        assert err.isolate_id == "ISO-001"
        assert "collection_date" in err.differing_fields

    @pytest.mark.parametrize(
        ("field", "orig_val", "conflict_val"),
        [
            ("organism_code", "eco", "kle"),
            ("organism_name", "Escherichia coli", "Klebsiella pneumoniae"),
            ("facility_id", "SYNTH-FACILITY-001", "SYNTH-FACILITY-002"),
            ("lab_id", "SYNTH-LAB-001", "SYNTH-LAB-002"),
            ("ward", "SYNTH-WARD-A", "SYNTH-WARD-B"),
            ("specimen_type", "blood", "urine"),
            ("patient_token", "SYNTH-CASE-001", "SYNTH-CASE-002"),
            ("source_import_id", "SYNTH-IMPORT-001", "SYNTH-IMPORT-002"),
        ],
    )
    def test_material_metadata_conflict_fails_closed(
        self,
        field: str,
        orig_val: str,
        conflict_val: str,
    ) -> None:
        kwargs_orig: dict[str, object] = {field: orig_val}
        kwargs_conflict: dict[str, object] = {field: conflict_val}
        iso_1 = _make_isolate("ISO-001", **kwargs_orig)  # type: ignore[arg-type]
        iso_2 = _make_isolate("ISO-001", **kwargs_conflict)  # type: ignore[arg-type]

        batch = CanonicalImportBatch(records=(iso_1, iso_2))
        report = deduplicate_canonical_batch(batch)

        assert report.success is False
        assert report.batch is None
        assert report.watermark is None
        assert len(report.errors) == 1
        assert field in report.errors[0].differing_fields

    def test_no_first_wins_or_last_wins_behavior(self) -> None:
        # A conflicting record must never be accepted by preferring first or last
        iso_first = _make_isolate("ISO-001", organism_code="eco")
        iso_second = _make_isolate("ISO-001", organism_code="kle")
        iso_other = _make_isolate("ISO-002")

        batch = CanonicalImportBatch(records=(iso_first, iso_second, iso_other))
        report = deduplicate_canonical_batch(batch)

        assert report.success is False
        assert report.batch is None
        assert report.watermark is None
        assert len(report.errors) >= 1

    def test_mixed_exact_duplicate_and_conflicting_duplicate(self) -> None:
        iso_1 = _make_isolate("ISO-001")
        iso_1_exact = _make_isolate("ISO-001")
        iso_1_conflict = _make_isolate("ISO-001", organism_code="kle")

        batch = CanonicalImportBatch(records=(iso_1, iso_1_exact, iso_1_conflict))
        report = deduplicate_canonical_batch(batch)

        # Must fail closed due to the conflict
        assert report.success is False
        assert report.batch is None
        assert report.watermark is None
        # The exact duplicate is documented in exact_duplicates
        assert len(report.exact_duplicates) == 1
        assert report.exact_duplicates[0].duplicate_indices == (1,)
        # The conflict is recorded in errors
        assert len(report.errors) == 1
        assert report.errors[0].indices == (0, 2)


# ============================================================================
# Value Object Invariant Tests
# ============================================================================


class TestDeduplicationValueObjectInvariants:
    def test_import_deduplication_report_success_invariants(self) -> None:
        iso = _make_isolate("ISO-001")
        batch = CanonicalImportBatch(records=(iso,))
        wm = SourceWatermark("ngabo-source-v1:sha256:" + "0" * 64)

        # Success requires batch and watermark
        with pytest.raises(ValueError, match="must provide a CanonicalImportBatch"):
            ImportDeduplicationReport(
                success=True,
                batch=None,
                watermark=wm,
            )

        with pytest.raises(ValueError, match="must provide a SourceWatermark"):
            ImportDeduplicationReport(
                success=True,
                batch=batch,
                watermark=None,
            )

        # Success cannot carry errors
        err = ImportDeduplicationError(
            code=ImportDeduplicationErrorCode.CONFLICTING_DUPLICATE_RECORD,
            isolate_id="ISO-001",
            indices=(0, 1),
        )
        with pytest.raises(ValueError, match="cannot carry errors"):
            ImportDeduplicationReport(
                success=True,
                batch=batch,
                watermark=wm,
                errors=(err,),
            )

    def test_import_deduplication_report_failure_invariants(self) -> None:
        iso = _make_isolate("ISO-001")
        batch = CanonicalImportBatch(records=(iso,))
        wm = SourceWatermark("ngabo-source-v1:sha256:" + "0" * 64)
        err = ImportDeduplicationError(
            code=ImportDeduplicationErrorCode.CONFLICTING_DUPLICATE_RECORD,
            isolate_id="ISO-001",
            indices=(0, 1),
        )

        # Failure cannot provide batch or watermark
        with pytest.raises(ValueError, match="must not provide a CanonicalImportBatch"):
            ImportDeduplicationReport(
                success=False,
                batch=batch,
                watermark=None,
                errors=(err,),
            )

        with pytest.raises(ValueError, match="must not provide a SourceWatermark"):
            ImportDeduplicationReport(
                success=False,
                batch=None,
                watermark=wm,
                errors=(err,),
            )

        # Failure must carry errors
        with pytest.raises(ValueError, match="must carry at least one error"):
            ImportDeduplicationReport(
                success=False,
                batch=None,
                watermark=None,
                errors=(),
            )

    def test_duplicate_record_finding_invariants(self) -> None:
        with pytest.raises(ValueError, match="expected integer >= 2"):
            DuplicateRecordFinding(
                isolate_id="ISO-001",
                occurrences=1,
                original_index=0,
                duplicate_indices=(1,),
            )

        with pytest.raises(ValueError, match="Count mismatch"):
            DuplicateRecordFinding(
                isolate_id="ISO-001",
                occurrences=3,
                original_index=0,
                duplicate_indices=(1,),  # expected 2 indices
            )

        with pytest.raises(ValueError, match="must be integer > original_index"):
            DuplicateRecordFinding(
                isolate_id="ISO-001",
                occurrences=2,
                original_index=2,
                duplicate_indices=(1,),  # 1 <= 2 is invalid
            )

    def test_invalid_input_to_deduplicate_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="expected CanonicalImportBatch"):
            deduplicate_canonical_batch("not-a-batch")  # type: ignore[arg-type]


# ============================================================================
# Determinism & Full Hero Integration Tests
# ============================================================================


class TestDeterminismAndHeroIntegration:
    def test_repeated_deduplication_is_value_identical(self) -> None:
        iso_1 = _make_isolate("ISO-001")
        iso_2 = _make_isolate("ISO-002")
        batch = CanonicalImportBatch(records=(iso_1, iso_2, iso_1))

        report_1 = deduplicate_canonical_batch(batch)
        report_2 = deduplicate_canonical_batch(batch)

        assert report_1.success == report_2.success
        assert report_1.batch == report_2.batch
        assert report_1.watermark == report_2.watermark
        assert report_1.exact_duplicates == report_2.exact_duplicates
        assert report_1.errors == report_2.errors

    def test_canonical_hero_csv_through_parser_and_deduplication(self) -> None:
        csv_text = HERO_CSV_PATH.read_text(encoding="utf-8")
        parsed = parse_whonet_csv(csv_text)
        assert parsed.success is True
        assert parsed.batch is not None

        report = deduplicate_canonical_batch(parsed.batch)
        assert report.success is True
        assert report.batch is not None
        assert len(report.batch.records) == 8
        assert report.exact_duplicates == ()
        assert report.errors == ()
        assert report.watermark is not None
        assert report.watermark.value == PINNED_HERO_SOURCE_WATERMARK
