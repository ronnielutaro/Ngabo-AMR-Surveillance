"""Focused tests for source identity, raw digest, watermark, and replay (Issue #40)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from types import MappingProxyType

import pytest

from ngabo.domain.entities.ast_observation import AstObservation
from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.enums.interpretation import Interpretation
from ngabo.domain.enums.source_replay_disposition import SourceReplayDisposition
from ngabo.domain.services.source_identity import (
    CANONICAL_HASH_ALGORITHM,
    CANONICAL_SOURCE_VERSION,
    compare_source_replay,
    compute_isolate_fingerprint,
    compute_raw_source_digest,
    compute_source_watermark,
    serialize_canonical_isolate_to_dict,
)
from ngabo.domain.value_objects.source_digest import SourceDigest
from ngabo.domain.value_objects.source_watermark import SourceWatermark
from ngabo.interfaces.parsers.whonet_csv_parser import parse_whonet_csv

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
HERO_CSV_PATH = DATA_DIR / "synthetic" / "canonical_hero.csv"
HERO_JSON_PATH = DATA_DIR / "synthetic" / "canonical_hero.json"

PINNED_HERO_RAW_DIGEST = "sha256:6b6bbc9a8d1f0e44419aee4ed4bdd073d965bab7507961307dcd051b4dae926b"
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
# Raw Source Digest Tests
# ============================================================================


class TestRawSourceDigest:
    def test_same_bytes_produce_same_sha256(self) -> None:
        content = b"ISOLATE_ID,COLLECTION_DATE\nISO-001,2026-08-16\n"
        digest_1 = compute_raw_source_digest(content)
        digest_2 = compute_raw_source_digest(content)
        assert digest_1 == digest_2
        assert digest_1.algorithm == "sha256"
        assert len(digest_1.hex_digest) == 64
        assert str(digest_1) == f"sha256:{digest_1.hex_digest}"

    def test_string_source_is_utf8_encoded(self) -> None:
        text = "ISOLATE_ID,COLLECTION_DATE\nISO-001,2026-08-16\n"
        digest_text = compute_raw_source_digest(text)
        digest_bytes = compute_raw_source_digest(text.encode("utf-8"))
        assert digest_text == digest_bytes

    def test_byte_change_produces_different_digest(self) -> None:
        base = b"ISO-001,2026-08-16"
        modified = b"ISO-001,2026-08-17"
        assert compute_raw_source_digest(base) != compute_raw_source_digest(modified)

    def test_line_ending_difference_produces_different_digest(self) -> None:
        lf_content = "header\nrow1\n"
        crlf_content = "header\r\nrow1\r\n"
        assert compute_raw_source_digest(lf_content) != compute_raw_source_digest(crlf_content)

    def test_whitespace_difference_produces_different_digest(self) -> None:
        content_a = "ISO-001, 2026-08-16"
        content_b = "ISO-001,2026-08-16"
        assert compute_raw_source_digest(content_a) != compute_raw_source_digest(content_b)

    def test_row_reordering_produces_different_raw_digest(self) -> None:
        order_1 = "header\nrowA\nrowB\n"
        order_2 = "header\nrowB\nrowA\n"
        assert compute_raw_source_digest(order_1) != compute_raw_source_digest(order_2)

    def test_pinned_hero_csv_raw_digest(self) -> None:
        csv_text = HERO_CSV_PATH.read_text(encoding="utf-8")
        digest = compute_raw_source_digest(csv_text)
        assert str(digest) == PINNED_HERO_RAW_DIGEST

    def test_invalid_source_type_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="Unsupported source type"):
            compute_raw_source_digest(12345)  # type: ignore[arg-type]


class TestSourceDigestContracts:
    def test_valid_construction(self) -> None:
        digest = SourceDigest(
            algorithm="sha256",
            hex_digest="a" * 64,
        )
        assert digest.algorithm == "sha256"
        assert digest.hex_digest == "a" * 64
        assert str(digest) == f"sha256:{'a' * 64}"

    def test_invalid_algorithm_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid algorithm"):
            SourceDigest(algorithm="md5", hex_digest="a" * 64)

    @pytest.mark.parametrize(
        "bad_hex",
        [
            "short",
            "a" * 63,
            "a" * 65,
            "A" * 64,  # Uppercase not allowed
            "z" * 64,  # Non-hex character
            "",
        ],
    )
    def test_invalid_hex_digest_raises_value_error(self, bad_hex: str) -> None:
        with pytest.raises(ValueError, match="Invalid hex_digest"):
            SourceDigest(algorithm="sha256", hex_digest=bad_hex)


# ============================================================================
# Canonical Serialization & Fingerprint Tests
# ============================================================================


class TestCanonicalIsolateSerialization:
    def test_serialization_contains_all_11_canonical_fields(self) -> None:
        iso = _make_isolate()
        serialized = serialize_canonical_isolate_to_dict(iso)
        expected_keys = {
            "isolate_id",
            "collection_date",
            "organism_code",
            "organism_name",
            "facility_id",
            "lab_id",
            "ward",
            "specimen_type",
            "patient_token",
            "source_import_id",
            "ast_results",
        }
        assert set(serialized.keys()) == expected_keys
        assert serialized["collection_date"] == "2026-08-16"

    def test_ast_results_sorted_by_antimicrobial_code(self) -> None:
        # Create isolate with out-of-order AST keys: SXT, AMK, MEM, CIP
        ast_dict = {
            "SXT": Interpretation.RESISTANT,
            "AMK": Interpretation.SUSCEPTIBLE,
            "MEM": Interpretation.SUSCEPTIBLE,
            "CIP": Interpretation.INTERMEDIATE,
        }
        iso = _make_isolate(ast_results=ast_dict)
        serialized = serialize_canonical_isolate_to_dict(iso)
        ast_res = serialized["ast_results"]
        assert isinstance(ast_res, dict)
        ast_keys = list(ast_res.keys())
        assert ast_keys == ["AMK", "CIP", "MEM", "SXT"]

    def test_non_isolate_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="Invalid record"):
            serialize_canonical_isolate_to_dict("not-an-isolate")  # type: ignore[arg-type]


class TestIsolateFingerprint:
    def test_fingerprint_is_64_char_lowercase_hex(self) -> None:
        iso = _make_isolate()
        fp = compute_isolate_fingerprint(iso)
        assert len(fp) == 64
        assert fp == fp.lower()
        assert all(c in "0123456789abcdef" for c in fp)

    def test_identical_records_produce_identical_fingerprint(self) -> None:
        iso_1 = _make_isolate()
        iso_2 = _make_isolate()
        assert compute_isolate_fingerprint(iso_1) == compute_isolate_fingerprint(iso_2)

    def test_ast_insertion_order_does_not_affect_fingerprint(self) -> None:
        ast_a = {
            "AMK": Interpretation.SUSCEPTIBLE,
            "MEM": Interpretation.RESISTANT,
        }
        ast_b = {
            "MEM": Interpretation.RESISTANT,
            "AMK": Interpretation.SUSCEPTIBLE,
        }
        iso_a = _make_isolate(ast_results=ast_a)
        iso_b = _make_isolate(ast_results=ast_b)
        assert compute_isolate_fingerprint(iso_a) == compute_isolate_fingerprint(iso_b)

    @pytest.mark.parametrize(
        ("field", "new_val"),
        [
            ("collection_date", date(2026, 8, 17)),
            ("organism_code", "kle"),
            ("organism_name", "Klebsiella pneumoniae"),
            ("facility_id", "SYNTH-FACILITY-002"),
            ("lab_id", "SYNTH-LAB-002"),
            ("ward", "SYNTH-WARD-B"),
            ("specimen_type", "urine"),
            ("patient_token", "SYNTH-CASE-002"),
            ("source_import_id", "SYNTH-IMPORT-002"),
        ],
    )
    def test_material_field_change_produces_different_fingerprint(
        self,
        field: str,
        new_val: object,
    ) -> None:
        base_args: dict[str, object] = {
            "isolate_id": "ISO-001",
            "collection_date": date(2026, 8, 16),
            "organism_code": "eco",
            "organism_name": "Escherichia coli",
            "facility_id": "SYNTH-FACILITY-001",
            "lab_id": "SYNTH-LAB-001",
            "ward": "SYNTH-WARD-A",
            "specimen_type": "blood",
            "patient_token": "SYNTH-CASE-001",
            "source_import_id": "SYNTH-IMPORT-001",
        }
        base_iso = _make_isolate(**base_args)  # type: ignore[arg-type]
        modified_args = dict(base_args)
        modified_args[field] = new_val
        mod_iso = _make_isolate(**modified_args)  # type: ignore[arg-type]
        assert compute_isolate_fingerprint(base_iso) != compute_isolate_fingerprint(mod_iso)

    def test_ast_interpretation_change_produces_different_fingerprint(self) -> None:
        iso_s = _make_isolate(ast_results={"AMK": Interpretation.SUSCEPTIBLE})
        iso_r = _make_isolate(ast_results={"AMK": Interpretation.RESISTANT})
        assert compute_isolate_fingerprint(iso_s) != compute_isolate_fingerprint(iso_r)


# ============================================================================
# Canonical Source Watermark Tests
# ============================================================================


class TestSourceWatermark:
    def test_watermark_format_and_version(self) -> None:
        iso = _make_isolate()
        wm = compute_source_watermark([iso])
        assert isinstance(wm, SourceWatermark)
        assert wm.value.startswith(f"{CANONICAL_SOURCE_VERSION}:{CANONICAL_HASH_ALGORITHM}:")
        parts = wm.value.split(":")
        assert len(parts) == 3
        assert parts[0] == "ngabo-source-v1"
        assert parts[1] == "sha256"
        assert len(parts[2]) == 64

    def test_same_records_repeated_runs_produce_same_watermark(self) -> None:
        records = [_make_isolate("ISO-001"), _make_isolate("ISO-002")]
        wm_1 = compute_source_watermark(records)
        wm_2 = compute_source_watermark(records)
        assert wm_1 == wm_2

    def test_pinned_hero_watermark_matches_expected_constant(self) -> None:
        csv_text = HERO_CSV_PATH.read_text(encoding="utf-8")
        parsed = parse_whonet_csv(csv_text)
        assert parsed.success is True
        wm = compute_source_watermark(parsed.records)
        assert wm.value == PINNED_HERO_SOURCE_WATERMARK

    def test_hero_csv_and_hero_json_produce_identical_watermark(self) -> None:
        csv_text = HERO_CSV_PATH.read_text(encoding="utf-8")
        csv_parsed = parse_whonet_csv(csv_text)

        json_data = json.loads(HERO_JSON_PATH.read_text(encoding="utf-8"))
        json_records = [
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
                        k: AstObservation(Interpretation(v["interpretation"]))
                        for k, v in r["ast_results"].items()
                    }
                ),
            )
            for r in json_data["records"]
        ]

        csv_wm = compute_source_watermark(csv_parsed.records)
        json_wm = compute_source_watermark(json_records)
        assert csv_wm == json_wm
        assert csv_wm.value == PINNED_HERO_SOURCE_WATERMARK

    def test_unique_record_reordering_produces_identical_watermark(self) -> None:
        iso_1 = _make_isolate("ISO-001")
        iso_2 = _make_isolate("ISO-002")
        iso_3 = _make_isolate("ISO-003")

        order_forward = [iso_1, iso_2, iso_3]
        order_reverse = [iso_3, iso_2, iso_1]
        order_mixed = [iso_2, iso_3, iso_1]

        wm_forward = compute_source_watermark(order_forward)
        wm_reverse = compute_source_watermark(order_reverse)
        wm_mixed = compute_source_watermark(order_mixed)

        assert wm_forward == wm_reverse
        assert wm_forward == wm_mixed

    def test_ast_insertion_order_difference_produces_identical_watermark(self) -> None:
        iso_a = _make_isolate(
            "ISO-001",
            ast_results={"AMK": Interpretation.SUSCEPTIBLE, "CIP": Interpretation.RESISTANT},
        )
        iso_b = _make_isolate(
            "ISO-001",
            ast_results={"CIP": Interpretation.RESISTANT, "AMK": Interpretation.SUSCEPTIBLE},
        )
        assert compute_source_watermark([iso_a]) == compute_source_watermark([iso_b])

    def test_material_ast_change_produces_different_watermark(self) -> None:
        iso_base = _make_isolate(
            "ISO-001",
            ast_results={"AMK": Interpretation.SUSCEPTIBLE},
        )
        iso_changed = _make_isolate(
            "ISO-001",
            ast_results={"AMK": Interpretation.RESISTANT},
        )
        wm_base = compute_source_watermark([iso_base])
        wm_changed = compute_source_watermark([iso_changed])
        assert wm_base != wm_changed

    def test_material_metadata_change_produces_different_watermark(self) -> None:
        iso_base = _make_isolate("ISO-001", specimen_type="blood")
        iso_changed = _make_isolate("ISO-001", specimen_type="urine")
        assert compute_source_watermark([iso_base]) != compute_source_watermark([iso_changed])

    def test_invalid_records_type_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="expected a tuple or list"):
            compute_source_watermark("not-a-sequence")  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="expected CanonicalIsolate"):
            compute_source_watermark(["not-an-isolate"])  # type: ignore[list-item]


# ============================================================================
# Replay Comparison Tests
# ============================================================================


class TestSourceReplayComparison:
    def test_identical_watermarks_produce_exact_replay(self) -> None:
        wm_1 = SourceWatermark(PINNED_HERO_SOURCE_WATERMARK)
        wm_2 = SourceWatermark(PINNED_HERO_SOURCE_WATERMARK)
        disposition = compare_source_replay(wm_1, wm_2)
        assert disposition == SourceReplayDisposition.EXACT_REPLAY

    def test_differing_watermarks_produce_material_change(self) -> None:
        wm_1 = SourceWatermark(PINNED_HERO_SOURCE_WATERMARK)
        wm_2 = SourceWatermark("ngabo-source-v1:sha256:" + "0" * 64)
        disposition = compare_source_replay(wm_1, wm_2)
        assert disposition == SourceReplayDisposition.MATERIAL_CHANGE

    def test_invalid_watermark_types_raise_type_error(self) -> None:
        wm = SourceWatermark(PINNED_HERO_SOURCE_WATERMARK)
        with pytest.raises(TypeError, match="expected SourceWatermark"):
            compare_source_replay("string", wm)  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="expected SourceWatermark"):
            compare_source_replay(wm, "string")  # type: ignore[arg-type]
