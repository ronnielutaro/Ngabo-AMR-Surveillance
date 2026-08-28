"""Unit and integration tests for the WHONET-style CSV parser (M2.2 / Issue #39)."""

from __future__ import annotations

import io
import json
from datetime import date
from pathlib import Path

import pytest

from ngabo.domain.entities.ast_observation import AstObservation
from ngabo.domain.entities.canonical_import_batch import CanonicalImportBatch
from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.enums.interpretation import Interpretation
from ngabo.interfaces.parsers import (
    WhonetParserError,
    WhonetParserErrorCode,
    WhonetParseResult,
    parse_whonet_csv,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
HERO_CSV_PATH = REPO_ROOT / "data" / "synthetic" / "canonical_hero.csv"
HERO_JSON_PATH = REPO_ROOT / "data" / "synthetic" / "canonical_hero.json"

_VALID_HEADER = (
    "ISOLATE_ID,COLLECTION_DATE,ORGANISM_CODE,ORGANISM_NAME,"
    "FACILITY_ID,LAB_ID,WARD,SPECIMEN_TYPE,PATIENT_TOKEN,SOURCE_IMPORT_ID,AMK,MEM"
)

_VALID_ROW_1 = (
    "ISO-001,2026-08-16,eco,Escherichia coli,"
    "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,S,R"
)

_VALID_ROW_2 = (
    "ISO-002,2026-08-17,kle,Klebsiella pneumoniae,"
    "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-B,blood,SYNTH-CASE-002,SYNTH-IMPORT-001,I,UNKNOWN"
)

SAMPLE_VALID_CSV = "\n".join([_VALID_HEADER, _VALID_ROW_1, _VALID_ROW_2, ""])


class TestValidCsvParsing:
    def test_parse_valid_sample_csv_success(self) -> None:
        result = parse_whonet_csv(SAMPLE_VALID_CSV)
        assert result.success is True
        assert len(result.errors) == 0
        assert len(result.records) == 2
        assert isinstance(result.batch, CanonicalImportBatch)
        assert len(result.batch.records) == 2

        rec1 = result.records[0]
        assert rec1.isolate_id == "ISO-001"
        assert rec1.collection_date == date(2026, 8, 16)
        assert rec1.organism_code == "eco"
        assert rec1.organism_name == "Escherichia coli"
        assert rec1.facility_id == "SYNTH-FACILITY-001"
        assert rec1.lab_id == "SYNTH-LAB-001"
        assert rec1.ward == "SYNTH-WARD-A"
        assert rec1.specimen_type == "urine"
        assert rec1.patient_token == "SYNTH-CASE-001"
        assert rec1.source_import_id == "SYNTH-IMPORT-001"
        assert rec1.ast_results == {
            "AMK": AstObservation(Interpretation.SUSCEPTIBLE),
            "MEM": AstObservation(Interpretation.RESISTANT),
        }

        rec2 = result.records[1]
        assert rec2.isolate_id == "ISO-002"
        assert rec2.collection_date == date(2026, 8, 17)
        assert rec2.organism_code == "kle"
        assert rec2.organism_name == "Klebsiella pneumoniae"
        assert rec2.ast_results == {
            "AMK": AstObservation(Interpretation.INTERMEDIATE),
            "MEM": AstObservation(Interpretation.UNKNOWN),
        }

    def test_parse_hero_csv_fixture_matches_hero_json(self) -> None:
        assert HERO_CSV_PATH.exists(), f"Hero CSV fixture missing at {HERO_CSV_PATH}"
        assert HERO_JSON_PATH.exists(), f"Hero JSON fixture missing at {HERO_JSON_PATH}"

        result = parse_whonet_csv(HERO_CSV_PATH)
        assert result.success is True
        assert len(result.errors) == 0
        assert len(result.records) == 8

        with open(HERO_JSON_PATH, encoding="utf-8") as f:
            json_data = json.load(f)

        expected_records = json_data["records"]
        assert len(expected_records) == 8

        for idx, (parsed, expected) in enumerate(
            zip(result.records, expected_records, strict=True)
        ):
            assert parsed.isolate_id == expected["isolate_id"], f"Record {idx} isolate_id mismatch"
            assert parsed.collection_date.isoformat() == expected["collection_date"]
            assert parsed.organism_code == expected["organism_code"]
            assert parsed.organism_name == expected["organism_name"]
            assert parsed.facility_id == expected["facility_id"]
            assert parsed.lab_id == expected["lab_id"]
            assert parsed.ward == expected["ward"]
            assert parsed.specimen_type == expected["specimen_type"]
            assert parsed.patient_token == expected["patient_token"]
            assert parsed.source_import_id == expected["source_import_id"]

            expected_ast = expected["ast_results"]
            assert set(parsed.ast_results.keys()) == set(expected_ast.keys())
            for abx, obs in expected_ast.items():
                expected_interp = Interpretation(obs["interpretation"])
                assert parsed.ast_results[abx].interpretation == expected_interp

    def test_parse_input_sources_supported(self) -> None:
        # String input
        res1 = parse_whonet_csv(SAMPLE_VALID_CSV)
        assert res1.success is True

        # Path input
        res2 = parse_whonet_csv(HERO_CSV_PATH)
        assert res2.success is True

        # TextIO stream input
        res3 = parse_whonet_csv(io.StringIO(SAMPLE_VALID_CSV))
        assert res3.success is True

    def test_preserves_source_row_order(self) -> None:
        result = parse_whonet_csv(HERO_CSV_PATH)
        expected_ids = [
            "ISO-012",
            "ISO-027",
            "ISO-031",
            "ISO-034",
            "ISO-039",
            "ISO-052",
            "ISO-063",
            "ISO-071",
        ]
        actual_ids = [rec.isolate_id for rec in result.records]
        assert actual_ids == expected_ids

    def test_repeated_parsing_is_deterministic(self) -> None:
        res1 = parse_whonet_csv(SAMPLE_VALID_CSV)
        res2 = parse_whonet_csv(SAMPLE_VALID_CSV)
        assert res1 == res2
        assert res1.records == res2.records
        assert res1.batch == res2.batch
        assert res1.errors == res2.errors

    def test_sparse_ast_observations_supported(self) -> None:
        csv_text = "\n".join([
            (
                "ISOLATE_ID,COLLECTION_DATE,ORGANISM_CODE,ORGANISM_NAME,"
                "FACILITY_ID,LAB_ID,WARD,SPECIMEN_TYPE,PATIENT_TOKEN,SOURCE_IMPORT_ID,AMK,CIP,MEM"
            ),
            (
                "ISO-001,2026-08-16,eco,Escherichia coli,"
                "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,"
                "SYNTH-CASE-001,SYNTH-IMPORT-001,S,,R"
            ),
        ])
        result = parse_whonet_csv(csv_text)
        assert result.success is True
        assert len(result.records) == 1
        # CIP was empty, so only AMK and MEM are populated
        assert set(result.records[0].ast_results.keys()) == {"AMK", "MEM"}
        assert result.records[0].ast_results["AMK"].interpretation == Interpretation.SUSCEPTIBLE
        assert result.records[0].ast_results["MEM"].interpretation == Interpretation.RESISTANT

    def test_whitespace_trimmed_from_cells_and_headers(self) -> None:
        csv_text = "\n".join([
            (
                "  ISOLATE_ID  , COLLECTION_DATE , ORGANISM_CODE , ORGANISM_NAME , "
                "FACILITY_ID , LAB_ID , WARD , SPECIMEN_TYPE , PATIENT_TOKEN , "
                "SOURCE_IMPORT_ID , AMK , MEM  "
            ),
            (
                "  ISO-001  ,  2026-08-16  ,  eco  ,  Escherichia coli  ,  "
                "SYNTH-FACILITY-001  ,  SYNTH-LAB-001  ,  SYNTH-WARD-A  ,  urine  ,  "
                "SYNTH-CASE-001  ,  SYNTH-IMPORT-001  ,  S  ,  R  "
            ),
        ])
        result = parse_whonet_csv(csv_text)
        assert result.success is True
        assert len(result.records) == 1
        rec = result.records[0]
        assert rec.isolate_id == "ISO-001"
        assert rec.collection_date == date(2026, 8, 16)
        assert rec.organism_code == "eco"
        assert rec.organism_name == "Escherichia coli"
        assert rec.ward == "SYNTH-WARD-A"
        assert rec.ast_results["AMK"].interpretation == Interpretation.SUSCEPTIBLE
        assert rec.ast_results["MEM"].interpretation == Interpretation.RESISTANT

    def test_custom_column_mapping(self) -> None:
        custom_csv = "\n".join([
            (
                "IDENTIFICATION,DATE_COLL,ORG,ORG_NAME,"
                "FACILITY,LAB,DEPARTMENT,SPECIMEN,PATIENT_ID,IMPORT_ID,AMK,MEM"
            ),
            (
                "ISO-001,2026-08-16,eco,Escherichia coli,"
                "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,"
                "SYNTH-CASE-001,SYNTH-IMPORT-001,S,R"
            ),
        ])
        custom_mapping = {
            "IDENTIFICATION": "isolate_id",
            "DATE_COLL": "collection_date",
            "ORG": "organism_code",
            "ORG_NAME": "organism_name",
            "FACILITY": "facility_id",
            "LAB": "lab_id",
            "DEPARTMENT": "ward",
            "SPECIMEN": "specimen_type",
            "PATIENT_ID": "patient_token",
            "IMPORT_ID": "source_import_id",
        }
        result = parse_whonet_csv(custom_csv, column_mapping=custom_mapping)
        assert result.success is True
        assert len(result.records) == 1
        assert result.records[0].isolate_id == "ISO-001"
        assert result.records[0].ward == "SYNTH-WARD-A"

    def test_configured_ast_columns(self) -> None:
        csv_text = "\n".join([_VALID_HEADER, _VALID_ROW_1])
        # Allowed AST columns: ("AMK", "MEM")
        res1 = parse_whonet_csv(csv_text, ast_columns=("AMK", "MEM"))
        assert res1.success is True

        # If MEM is not in allowed list, it is rejected
        res2 = parse_whonet_csv(csv_text, ast_columns=("AMK",))
        assert res2.success is False
        assert any(
            err.code == WhonetParserErrorCode.INVALID_AST_COLUMN and err.column == "MEM"
            for err in res2.errors
        )


class TestSyntheticIdentifierEnforcement:
    @pytest.mark.parametrize(
        ("field_col", "invalid_value"),
        [
            ("FACILITY_ID", "REAL-HOSPITAL-1"),
            ("FACILITY_ID", "Mulago Hospital"),
            ("FACILITY_ID", "SYNTH-"),
            ("FACILITY_ID", "synth-facility-001"),
            ("FACILITY_ID", "SYNTH FACILITY"),
            ("LAB_ID", "LAB-001"),
            ("LAB_ID", "Kampala-Lab"),
            ("LAB_ID", "SYNTH-"),
            ("LAB_ID", "synth-lab-001"),
            ("LAB_ID", "SYNTH LAB"),
            ("WARD", "Ward-3A"),
            ("WARD", "ICU"),
            ("WARD", "SYNTH-"),
            ("WARD", "synth-ward-a"),
            ("WARD", "SYNTH WARD"),
            ("PATIENT_TOKEN", "PATIENT-123"),
            ("PATIENT_TOKEN", "John Doe"),
            ("PATIENT_TOKEN", "CASE-031"),
            ("PATIENT_TOKEN", "SYNTH-"),
            ("PATIENT_TOKEN", "synth-case-001"),
            ("PATIENT_TOKEN", "SYNTH PATIENT"),
            ("SOURCE_IMPORT_ID", "IMPORT-REAL-1"),
            ("SOURCE_IMPORT_ID", "IMPORT-2026"),
            ("SOURCE_IMPORT_ID", "SYNTH-"),
            ("SOURCE_IMPORT_ID", "synth-import-001"),
            ("SOURCE_IMPORT_ID", "SYNTH IMPORT"),
        ],
    )
    def test_non_synthetic_identifier_rejected(self, field_col: str, invalid_value: str) -> None:
        row_fields = {
            "ISOLATE_ID": "ISO-001",
            "COLLECTION_DATE": "2026-08-16",
            "ORGANISM_CODE": "eco",
            "ORGANISM_NAME": "Escherichia coli",
            "FACILITY_ID": "SYNTH-FACILITY-001",
            "LAB_ID": "SYNTH-LAB-001",
            "WARD": "SYNTH-WARD-A",
            "SPECIMEN_TYPE": "urine",
            "PATIENT_TOKEN": "SYNTH-CASE-001",
            "SOURCE_IMPORT_ID": "SYNTH-IMPORT-001",
            "AMK": "S",
            "MEM": "R",
        }
        row_fields[field_col] = invalid_value
        row_str = ",".join(row_fields[col] for col in _VALID_HEADER.split(","))
        csv_text = "\n".join([_VALID_HEADER, row_str])

        result = parse_whonet_csv(csv_text)
        assert result.success is False
        assert len(result.errors) == 1
        err = result.errors[0]
        assert err.code == WhonetParserErrorCode.INVALID_SYNTHETIC_ID
        assert err.column == field_col
        assert err.record_id == "ISO-001"
        assert invalid_value in (err.detail or "")

    def test_invalid_facility_id_rejected(self) -> None:
        row = (
            "ISO-001,2026-08-16,eco,Escherichia coli,"
            "Mulago Hospital,SYNTH-LAB-001,SYNTH-WARD-A,urine,"
            "SYNTH-CASE-001,SYNTH-IMPORT-001,S,R"
        )
        result = parse_whonet_csv(f"{_VALID_HEADER}\n{row}")
        assert result.success is False
        assert any(
            err.code == WhonetParserErrorCode.INVALID_SYNTHETIC_ID and err.column == "FACILITY_ID"
            for err in result.errors
        )

    def test_invalid_lab_id_rejected(self) -> None:
        row = (
            "ISO-001,2026-08-16,eco,Escherichia coli,"
            "SYNTH-FACILITY-001,Kampala-Lab,SYNTH-WARD-A,urine,"
            "SYNTH-CASE-001,SYNTH-IMPORT-001,S,R"
        )
        result = parse_whonet_csv(f"{_VALID_HEADER}\n{row}")
        assert result.success is False
        assert any(
            err.code == WhonetParserErrorCode.INVALID_SYNTHETIC_ID and err.column == "LAB_ID"
            for err in result.errors
        )

    def test_invalid_ward_rejected(self) -> None:
        row = (
            "ISO-001,2026-08-16,eco,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,Ward-3A,urine,"
            "SYNTH-CASE-001,SYNTH-IMPORT-001,S,R"
        )
        result = parse_whonet_csv(f"{_VALID_HEADER}\n{row}")
        assert result.success is False
        assert any(
            err.code == WhonetParserErrorCode.INVALID_SYNTHETIC_ID and err.column == "WARD"
            for err in result.errors
        )

    def test_invalid_patient_token_rejected(self) -> None:
        row = (
            "ISO-001,2026-08-16,eco,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,"
            "John Doe,SYNTH-IMPORT-001,S,R"
        )
        result = parse_whonet_csv(f"{_VALID_HEADER}\n{row}")
        assert result.success is False
        assert any(
            err.code == WhonetParserErrorCode.INVALID_SYNTHETIC_ID and err.column == "PATIENT_TOKEN"
            for err in result.errors
        )

    def test_invalid_source_import_id_rejected(self) -> None:
        row = (
            "ISO-001,2026-08-16,eco,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,"
            "SYNTH-CASE-001,IMPORT-REAL-1,S,R"
        )
        result = parse_whonet_csv(f"{_VALID_HEADER}\n{row}")
        assert result.success is False
        assert any(
            err.code == WhonetParserErrorCode.INVALID_SYNTHETIC_ID
            and err.column == "SOURCE_IMPORT_ID"
            for err in result.errors
        )

    def test_valid_synthetic_identifiers_pass(self) -> None:
        valid_row = (
            "ISO-031,2026-08-17,kle,Klebsiella pneumoniae,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,blood,"
            "SYNTH-CASE-031,SYNTH-IMPORT-001,S,R"
        )
        csv_text = "\n".join([_VALID_HEADER, valid_row])
        result = parse_whonet_csv(csv_text)
        assert result.success is True
        assert len(result.records) == 1
        rec = result.records[0]
        assert rec.facility_id == "SYNTH-FACILITY-001"
        assert rec.lab_id == "SYNTH-LAB-001"
        assert rec.ward == "SYNTH-WARD-A"
        assert rec.patient_token == "SYNTH-CASE-031"
        assert rec.source_import_id == "SYNTH-IMPORT-001"


class TestPhysicalLineNumberTracking:
    def test_physical_line_numbers_accurate_after_quoted_multiline_field(self) -> None:
        # Line 1: Header
        # Lines 2-3: Valid record with multiline quoted organism name
        # Line 4: Invalid record with invalid date
        csv_text = (
            f"{_VALID_HEADER}\n"
            "ISO-001,2026-08-16,eco,\"Escherichia\ncoli\","
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,S,R\n"
            "ISO-002,2026-99-99,kle,Klebsiella pneumoniae,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-B,blood,SYNTH-CASE-002,SYNTH-IMPORT-001,S,R\n"
        )
        result = parse_whonet_csv(csv_text)
        assert result.success is False
        assert len(result.errors) == 1
        err = result.errors[0]
        assert err.code == WhonetParserErrorCode.INVALID_COLLECTION_DATE
        assert err.record_id == "ISO-002"
        # Physical line number is line 4
        assert err.row_number == 4
        assert err.record_index == 1


class TestBlankRowPolicy:
    def test_interior_blank_row_fails_closed(self) -> None:
        # Line 1: Header
        # Line 2: Record 0
        # Line 3: Blank line
        # Line 4: Record 1
        csv_text = "\n".join([_VALID_HEADER, _VALID_ROW_1, "", _VALID_ROW_2, ""])
        result = parse_whonet_csv(csv_text)
        assert result.success is False
        assert len(result.errors) == 1
        err = result.errors[0]
        assert err.code == WhonetParserErrorCode.MALFORMED_CSV_ROW
        assert err.row_number == 3
        assert "blank row between CSV data records" in (err.detail or "")

    def test_leading_blank_line_before_header_fails_closed(self) -> None:
        csv_text = "\n".join(["", _VALID_HEADER, _VALID_ROW_1])
        result = parse_whonet_csv(csv_text)
        assert result.success is False
        assert any(
            err.code == WhonetParserErrorCode.MALFORMED_CSV_ROW and err.row_number == 1
            for err in result.errors
        )

    def test_trailing_blank_lines_are_safely_ignored(self) -> None:
        # Standard newline at EOF and trailing blank line
        csv_text = "\n".join([_VALID_HEADER, _VALID_ROW_1, _VALID_ROW_2, "", ""])
        result = parse_whonet_csv(csv_text)
        assert result.success is True
        assert len(result.records) == 2


class TestCsvSyntaxRobustness:
    def test_malformed_unclosed_quote_fails_closed(self) -> None:
        bad_csv = (
            f"{_VALID_HEADER}\n"
            "ISO-001,2026-08-16,eco,\"unclosed quote,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,S,R\n"
        )
        result = parse_whonet_csv(bad_csv)
        assert result.success is False
        assert len(result.errors) == 1
        err = result.errors[0]
        assert err.code == WhonetParserErrorCode.MALFORMED_CSV_ROW
        assert "CSV format error" in (err.detail or "")

    def test_malformed_quote_on_header_fails_closed(self) -> None:
        bad_csv = '"ISOLATE_ID,COLLECTION_DATE,ORGANISM_CODE'
        result = parse_whonet_csv(bad_csv)
        assert result.success is False
        assert any(
            err.code == WhonetParserErrorCode.MALFORMED_CSV_ROW and err.row_number == 1
            for err in result.errors
        )

    def test_bad_quote_in_field_fails_closed_under_strict_mode(self) -> None:
        # Strict mode rejects trailing data after closing quote: "eco"1
        bad_csv = (
            f"{_VALID_HEADER}\n"
            "ISO-001,2026-08-16,\"eco\"1,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,S,R\n"
        )
        result = parse_whonet_csv(bad_csv)
        assert result.success is False
        assert any(
            err.code == WhonetParserErrorCode.MALFORMED_CSV_ROW
            for err in result.errors
        )

    def test_no_raw_csv_error_leaks_to_caller(self) -> None:
        pathological_inputs = [
            '"',
            '"""',
            '"hello\nworld',
            'a,"b\nc,"d',
        ]
        for bad_input in pathological_inputs:
            # Must return WhonetParseResult without raising csv.Error
            result = parse_whonet_csv(bad_input)
            assert result.success is False
            assert len(result.errors) >= 1

    def test_malformed_material_row_never_silently_dropped(self) -> None:
        # Row with wrong column count between valid rows
        bad_csv = (
            f"{_VALID_HEADER}\n"
            f"{_VALID_ROW_1}\n"
            "ISO-BAD,short,row\n"
            f"{_VALID_ROW_2}\n"
        )
        result = parse_whonet_csv(bad_csv)
        assert result.success is False
        assert any(
            err.code == WhonetParserErrorCode.MALFORMED_CSV_ROW
            and err.row_number == 3
            and "row has 3 columns; expected 12" in (err.detail or "")
            for err in result.errors
        )


class TestDuplicateIdPreservationForIssue40:
    def test_duplicate_isolate_ids_preserved_in_order_not_deduplicated(self) -> None:
        dup_row_1 = (
            "ISO-031,2026-08-17,kle,Klebsiella pneumoniae,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,blood,"
            "SYNTH-CASE-031,SYNTH-IMPORT-001,S,R"
        )
        dup_row_2 = (
            "ISO-031,2026-08-17,kle,Klebsiella pneumoniae,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,blood,"
            "SYNTH-CASE-031,SYNTH-IMPORT-001,S,R"
        )
        csv_text = "\n".join([_VALID_HEADER, dup_row_1, dup_row_2])
        result = parse_whonet_csv(csv_text)
        assert result.success is True
        assert len(result.records) == 2
        assert result.records[0].isolate_id == "ISO-031"
        assert result.records[1].isolate_id == "ISO-031"
        # Duplicate records remain in batch for Issue #40
        assert result.batch is not None
        assert len(result.batch.records) == 2


class TestHeaderValidationErrors:
    def test_empty_csv_string_emits_error(self) -> None:
        result = parse_whonet_csv("")
        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].code == WhonetParserErrorCode.EMPTY_CSV
        assert result.records == ()
        assert result.batch is None

    def test_whitespace_only_csv_emits_error(self) -> None:
        result = parse_whonet_csv("   \n\n  \t  \n")
        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].code == WhonetParserErrorCode.EMPTY_CSV

    def test_header_only_csv_emits_error(self) -> None:
        csv_text = _VALID_HEADER + "\n"
        result = parse_whonet_csv(csv_text)
        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].code == WhonetParserErrorCode.EMPTY_CSV

    def test_missing_required_column_emits_error(self) -> None:
        # Missing WARD and SPECIMEN_TYPE
        header = (
            "ISOLATE_ID,COLLECTION_DATE,ORGANISM_CODE,ORGANISM_NAME,"
            "FACILITY_ID,LAB_ID,PATIENT_TOKEN,SOURCE_IMPORT_ID,AMK"
        )
        row = (
            "ISO-001,2026-08-16,eco,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-CASE-001,SYNTH-IMPORT-001,S"
        )
        csv_text = "\n".join([header, row])
        result = parse_whonet_csv(csv_text)
        assert result.success is False
        assert len(result.errors) == 2
        assert result.errors[0].code == WhonetParserErrorCode.MISSING_REQUIRED_COLUMN
        assert result.errors[0].column == "WARD"
        assert result.errors[1].code == WhonetParserErrorCode.MISSING_REQUIRED_COLUMN
        assert result.errors[1].column == "SPECIMEN_TYPE"

    def test_duplicate_header_column_emits_error(self) -> None:
        header = _VALID_HEADER + ",AMK"
        row = _VALID_ROW_1 + ",S"
        csv_text = "\n".join([header, row])
        result = parse_whonet_csv(csv_text)
        assert result.success is False
        assert any(
            err.code == WhonetParserErrorCode.DUPLICATE_COLUMN_HEADER and err.column == "AMK"
            for err in result.errors
        )

    def test_invalid_ast_column_name_emits_error(self) -> None:
        header = _VALID_HEADER + ",INVALID_ANTIBIOTIC_NAME"
        row = _VALID_ROW_1 + ",S"
        csv_text = "\n".join([header, row])
        result = parse_whonet_csv(csv_text)
        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].code == WhonetParserErrorCode.INVALID_AST_COLUMN
        assert result.errors[0].column == "INVALID_ANTIBIOTIC_NAME"


class TestRowValidationErrors:
    def test_malformed_row_column_count_mismatch(self) -> None:
        short_row = "ISO-001,2026-08-16,eco,Escherichia coli,SYNTH-FACILITY-001,SYNTH-LAB-001"
        csv_text = "\n".join([_VALID_HEADER, short_row, _VALID_ROW_2])
        result = parse_whonet_csv(csv_text)
        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].code == WhonetParserErrorCode.MALFORMED_CSV_ROW
        assert result.errors[0].row_number == 2
        assert result.errors[0].record_index == 0

    def test_missing_required_cell_value(self) -> None:
        bad_row = (
            "ISO-001,2026-08-16,eco,Escherichia coli,,"
            "SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,S,R"
        )
        csv_text = "\n".join([_VALID_HEADER, bad_row])
        result = parse_whonet_csv(csv_text)
        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].code == WhonetParserErrorCode.MISSING_REQUIRED_VALUE
        assert result.errors[0].column == "FACILITY_ID"
        assert result.errors[0].record_id == "ISO-001"

    def test_invalid_isolate_id_pattern(self) -> None:
        bad_row = (
            "INVALID-1,2026-08-16,eco,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,S,R"
        )
        csv_text = "\n".join([_VALID_HEADER, bad_row])
        result = parse_whonet_csv(csv_text)
        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].code == WhonetParserErrorCode.INVALID_ISOLATE_ID
        assert result.errors[0].record_id is None

    def test_invalid_collection_date_syntax(self) -> None:
        # Compact ISO: 20260816 should be rejected
        bad_row = (
            "ISO-001,20260816,eco,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,S,R"
        )
        csv_text = "\n".join([_VALID_HEADER, bad_row])
        result = parse_whonet_csv(csv_text)
        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].code == WhonetParserErrorCode.INVALID_COLLECTION_DATE
        assert result.errors[0].record_id == "ISO-001"

    def test_invalid_calendar_date(self) -> None:
        # 2026-02-30 does not exist
        bad_row = (
            "ISO-001,2026-02-30,eco,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,S,R"
        )
        csv_text = "\n".join([_VALID_HEADER, bad_row])
        result = parse_whonet_csv(csv_text)
        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].code == WhonetParserErrorCode.INVALID_COLLECTION_DATE

    def test_unsupported_ast_susceptibility_value(self) -> None:
        bad_row = (
            "ISO-001,2026-08-16,eco,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,"
            "Resistant,S"
        )
        csv_text = "\n".join([_VALID_HEADER, bad_row])
        result = parse_whonet_csv(csv_text)
        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].code == WhonetParserErrorCode.INVALID_AST_VALUE
        assert result.errors[0].column == "AMK"
        assert result.errors[0].record_id == "ISO-001"

    def test_empty_ast_results_in_row(self) -> None:
        # All AST columns are blank
        bad_row = (
            "ISO-001,2026-08-16,eco,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,,"
        )
        csv_text = "\n".join([_VALID_HEADER, bad_row])
        result = parse_whonet_csv(csv_text)
        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].code == WhonetParserErrorCode.EMPTY_AST_RESULTS
        assert result.errors[0].record_id == "ISO-001"


class TestMultiErrorAccumulation:
    def test_accumulates_errors_across_multiple_rows_deterministically(self) -> None:
        bad_row_1 = (
            "ISO-001,2026-08-16,eco,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-A,urine,SYNTH-CASE-001,SYNTH-IMPORT-001,"
            "INVALID_VAL,S"
        )
        bad_row_2 = (
            "ISO-002,2026-99-99,kle,Klebsiella pneumoniae,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,SYNTH-WARD-B,blood,SYNTH-CASE-002,SYNTH-IMPORT-001,S,R"
        )
        bad_row_3 = (
            "ISO-003,2026-08-18,pae,Pseudomonas aeruginosa,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,,respiratory,SYNTH-CASE-003,SYNTH-IMPORT-001,R,R"
        )
        csv_text = "\n".join([_VALID_HEADER, bad_row_1, bad_row_2, bad_row_3])
        result = parse_whonet_csv(csv_text)
        assert result.success is False
        assert len(result.errors) == 3
        # Row 2 (ISO-001) has invalid AST value
        assert result.errors[0].code == WhonetParserErrorCode.INVALID_AST_VALUE
        assert result.errors[0].row_number == 2
        assert result.errors[0].record_id == "ISO-001"
        # Row 3 (ISO-002) has invalid date
        assert result.errors[1].code == WhonetParserErrorCode.INVALID_COLLECTION_DATE
        assert result.errors[1].row_number == 3
        assert result.errors[1].record_id == "ISO-002"
        # Row 4 (ISO-003) has missing ward
        assert result.errors[2].code == WhonetParserErrorCode.MISSING_REQUIRED_VALUE
        assert result.errors[2].row_number == 4
        assert result.errors[2].record_id == "ISO-003"
        assert result.errors[2].column == "WARD"

    def test_accumulates_multiple_field_errors_within_single_row(self) -> None:
        bad_row = (
            "ISO-001,2026-08-16,,Escherichia coli,"
            "SYNTH-FACILITY-001,SYNTH-LAB-001,,urine,"
            "SYNTH-CASE-001,SYNTH-IMPORT-001,BAD_VAL,BAD_VAL2"
        )
        csv_text = "\n".join([_VALID_HEADER, bad_row])
        result = parse_whonet_csv(csv_text)
        assert result.success is False
        # Expected errors in fixed field order: organism_code -> ward -> AMK -> MEM
        assert len(result.errors) == 4
        assert result.errors[0].column == "ORGANISM_CODE"
        assert result.errors[1].column == "WARD"
        assert result.errors[2].column == "AMK"
        assert result.errors[3].column == "MEM"


class TestWhonetParseResultContracts:
    def test_success_result_invariants(self) -> None:
        res = parse_whonet_csv(SAMPLE_VALID_CSV)
        assert res.success is True
        assert res.batch is not None
        assert len(res.records) == 2
        assert res.errors == ()
        # Verify raw_candidates is not present on WhonetParseResult
        assert not hasattr(res, "raw_candidates")

    def test_failure_result_invariants_raise_on_invalid_construction(self) -> None:
        sample_isolate = parse_whonet_csv(SAMPLE_VALID_CSV).records[0]
        batch = CanonicalImportBatch(records=(sample_isolate,))

        # Cannot construct success=True with errors
        with pytest.raises(ValueError, match="must not contain errors"):
            WhonetParseResult(
                success=True,
                records=(sample_isolate,),
                batch=batch,
                errors=(
                    WhonetParserError(
                        code=WhonetParserErrorCode.EMPTY_CSV,
                    ),
                ),
            )

        # Cannot construct success=False with records
        with pytest.raises(ValueError, match="must not expose parsed records"):
            WhonetParseResult(
                success=False,
                records=(sample_isolate,),
                batch=None,
                errors=(
                    WhonetParserError(
                        code=WhonetParserErrorCode.EMPTY_CSV,
                    ),
                ),
            )

        # Type guards: non-tuple records or errors raise TypeError
        with pytest.raises(TypeError, match="expected a tuple"):
            WhonetParseResult(
                success=False,
                records=[sample_isolate],  # type: ignore[arg-type]
                batch=None,
                errors=(
                    WhonetParserError(
                        code=WhonetParserErrorCode.EMPTY_CSV,
                    ),
                ),
            )

        with pytest.raises(TypeError, match="expected a tuple"):
            WhonetParseResult(
                success=False,
                records=(),
                batch=None,
                errors=[  # type: ignore[arg-type]
                    WhonetParserError(
                        code=WhonetParserErrorCode.EMPTY_CSV,
                    ),
                ],
            )

        # Success must be a bool
        with pytest.raises(TypeError, match="Invalid success"):
            WhonetParseResult(
                success="true",  # type: ignore[arg-type]
                records=(),
                batch=None,
                errors=(
                    WhonetParserError(
                        code=WhonetParserErrorCode.EMPTY_CSV,
                    ),
                ),
            )

        # Record element must be CanonicalIsolate
        with pytest.raises(TypeError, match="expected CanonicalIsolate"):
            WhonetParseResult(
                success=True,
                records=("not-an-isolate",),  # type: ignore[arg-type]
                batch=batch,
                errors=(),
            )

        # Error element must be WhonetParserError
        with pytest.raises(TypeError, match="expected WhonetParserError"):
            WhonetParseResult(
                success=False,
                records=(),
                batch=None,
                errors=("not-an-error",),  # type: ignore[arg-type]
            )

        # Success requires batch to be CanonicalImportBatch
        with pytest.raises(ValueError, match="must provide a CanonicalImportBatch"):
            WhonetParseResult(
                success=True,
                records=(sample_isolate,),
                batch=None,
                errors=(),
            )

        # Success requires batch.records == records
        other_isolate = CanonicalIsolate(
            isolate_id="ISO-999",
            collection_date=sample_isolate.collection_date,
            organism_code=sample_isolate.organism_code,
            organism_name=sample_isolate.organism_name,
            facility_id=sample_isolate.facility_id,
            lab_id=sample_isolate.lab_id,
            ward=sample_isolate.ward,
            specimen_type=sample_isolate.specimen_type,
            patient_token=sample_isolate.patient_token,
            source_import_id=sample_isolate.source_import_id,
            ast_results=sample_isolate.ast_results,
        )
        with pytest.raises(ValueError, match="batch records must match"):
            WhonetParseResult(
                success=True,
                records=(sample_isolate,),
                batch=CanonicalImportBatch(records=(other_isolate,)),
                errors=(),
            )

        # Failure must not expose a batch
        with pytest.raises(ValueError, match="must not expose an import batch"):
            WhonetParseResult(
                success=False,
                records=(),
                batch=batch,
                errors=(
                    WhonetParserError(
                        code=WhonetParserErrorCode.EMPTY_CSV,
                    ),
                ),
            )


class TestWhonetParserErrorContracts:
    def test_valid_construction(self) -> None:
        err = WhonetParserError(
            code=WhonetParserErrorCode.INVALID_ISOLATE_ID,
            row_number=2,
            record_index=0,
            column="ISOLATE_ID",
            record_id="BAD",
            detail="detail message",
        )
        assert err.code == WhonetParserErrorCode.INVALID_ISOLATE_ID
        assert err.row_number == 2
        assert err.record_index == 0
        assert err.column == "ISOLATE_ID"
        assert err.record_id == "BAD"
        assert err.detail == "detail message"

    def test_invalid_code_type_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="Invalid code"):
            WhonetParserError(code="INVALID_ISOLATE_ID")  # type: ignore[arg-type]

    @pytest.mark.parametrize("bad_row", [0, -1, True, False])
    def test_invalid_row_number_raises_value_error(self, bad_row: object) -> None:
        with pytest.raises(ValueError, match="Invalid row_number"):
            WhonetParserError(
                code=WhonetParserErrorCode.EMPTY_CSV,
                row_number=bad_row,  # type: ignore[arg-type]
            )

    @pytest.mark.parametrize("bad_index", [-1, -5, True, False])
    def test_invalid_record_index_raises_value_error(self, bad_index: object) -> None:
        with pytest.raises(ValueError, match="Invalid record_index"):
            WhonetParserError(
                code=WhonetParserErrorCode.EMPTY_CSV,
                record_index=bad_index,  # type: ignore[arg-type]
            )
