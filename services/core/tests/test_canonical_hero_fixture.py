"""Validation tests for the canonical synthetic hero dataset (M1B.6 / Issue #30).

Covers the data contract only: the JSON Schema in ``data/schemas`` and the
single golden fixture in ``data/synthetic``. The fixture is pure synthetic
laboratory observations — these tests prove the schema enforces the contract,
and that the fixture carries no missing material fact and no derived
signal/incident/action fact. No parser, detector or runtime behavior exists
yet, so none is exercised here. All tests run offline.
"""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import (  # type: ignore[import-untyped]
    Draft202012Validator,
    FormatChecker,
    ValidationError,
)

from ngabo.domain.value_objects.proof_references import CanonicalRecordReference

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "data" / "schemas" / "canonical_hero.schema.json"
FIXTURE_PATH = REPO_ROOT / "data" / "synthetic" / "canonical_hero.json"

SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
FIXTURE_DATASET_ID = "canonical-hero-v1"

# All committed record IDs in the golden fixture, ascending (Issue #30).
EXPECTED_RECORD_IDS = (
    "ISO-012",
    "ISO-027",
    "ISO-031",
    "ISO-034",
    "ISO-039",
    "ISO-052",
    "ISO-063",
    "ISO-071",
)

# The three Ward A Klebsiella pneumoniae records prescribed by
# PROOF_CARRYING_REASONING.md §4-5 and AGENT_ARCHITECTURE.md §6.
HERO_RECORD_IDS = ("ISO-031", "ISO-034", "ISO-039")

EXPECTED_FACILITY_IDS = {"SYNTH-FACILITY-001"}
EXPECTED_LAB_IDS = {"SYNTH-LAB-001"}
EXPECTED_WARDS = {"SYNTH-WARD-A", "SYNTH-WARD-B", "SYNTH-WARD-C"}
EXPECTED_SOURCE_IMPORT_IDS = {"SYNTH-IMPORT-001"}
EXPECTED_ANTIBIOTIC_CODES = {"AMK", "CAZ", "CIP", "CRO", "MEM", "SXT"}
EXPECTED_ORGANISMS = {
    "Enterobacter cloacae",
    "Escherichia coli",
    "Klebsiella pneumoniae",
    "Pseudomonas aeruginosa",
}

# Governing interpretation vocabulary (DATA_SAFETY_EVALUATION.md §2). The
# schema reserves UNKNOWN; the golden fixture itself uses only S/I/R.
GOLDEN_INTERPRETATIONS = {"S", "I", "R"}

REQUIRED_SYNTHETIC_DISCLAIMER = (
    "This dataset is synthetic and intended solely for software "
    "demonstration/evaluation. It does not represent real patient records "
    "and is not suitable for clinical inference."
)

RECORD_FIELDS = frozenset(
    {
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
)

# Facts owned by later deterministic/application stages; the canonical input
# must never carry them (Issue #30 scope).
DERIVED_FACT_FIELDS = frozenset(
    {
        "action_authorized",
        "cluster_score",
        "incident_id",
        "incident_state",
        "notification_status",
        "outbreak_confirmed",
        "policy_result",
        "risk_score",
        "signal_detected",
        "verification_passed",
    }
)


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _validator(schema: dict[str, Any]) -> Draft202012Validator:
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _strings(node: object) -> Iterator[str]:
    """Yield every string value in the fixture tree."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _strings(value)
    elif isinstance(node, list):
        for item in node:
            yield from _strings(item)


def _interpretation_vector(record: dict[str, Any]) -> tuple[str, ...]:
    """Interpretation values ordered by antibiotic code (deterministic)."""
    ast = record["ast_results"]
    return tuple(ast[code]["interpretation"] for code in sorted(ast))


def _expect_invalid(schema: dict[str, Any], mutate: Callable[[dict[str, Any]], None]) -> None:
    """Deep-copy the fixture, apply ``mutate`` and expect schema rejection."""
    mutated = copy.deepcopy(_load_json(FIXTURE_PATH))
    mutate(mutated)
    with pytest.raises(ValidationError):
        _validator(schema).validate(mutated)


@pytest.fixture(scope="module")
def schema() -> dict[str, Any]:
    return _load_json(SCHEMA_PATH)


@pytest.fixture(scope="module")
def hero_fixture(schema: dict[str, Any]) -> dict[str, Any]:
    loaded = _load_json(FIXTURE_PATH)
    _validator(schema).validate(loaded)  # raises if invalid
    return loaded


def _records(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], fixture["records"])


class TestSchemaContract:
    def test_schema_loads(self, schema: dict[str, Any]) -> None:
        assert isinstance(schema, dict)
        assert schema.get("$schema") == SCHEMA_DIALECT

    def test_schema_is_valid_against_metaschema(self, schema: dict[str, Any]) -> None:
        Draft202012Validator.check_schema(schema)

    def test_schema_pins_explicit_synthetic_marker(self, schema: dict[str, Any]) -> None:
        assert schema["properties"]["synthetic"] == {"const": True}

    def test_schema_requires_synthetic_identifier_prefixes(self, schema: dict[str, Any]) -> None:
        synthetic_id = schema["$defs"]["synthetic_id"]
        assert synthetic_id["pattern"] == "^SYNTH-[A-Z0-9-]+$"


class TestFixtureContract:
    def test_fixture_validates_against_schema(
        self, hero_fixture: dict[str, Any], schema: dict[str, Any]
    ) -> None:
        _validator(schema).validate(hero_fixture)  # raises if invalid

    def test_synthetic_marker_is_explicitly_true(self, hero_fixture: dict[str, Any]) -> None:
        assert hero_fixture["synthetic"] is True

    def test_dataset_id_is_committed_literal(self, hero_fixture: dict[str, Any]) -> None:
        assert hero_fixture["dataset_id"] == FIXTURE_DATASET_ID

    def test_provenance_declares_synthetic_origin(self, hero_fixture: dict[str, Any]) -> None:
        origin = hero_fixture["provenance"]["origin"]
        assert "synthetic" in origin.lower()

    def test_provenance_carries_required_disclaimer(self, hero_fixture: dict[str, Any]) -> None:
        assert hero_fixture["provenance"]["disclaimer"] == REQUIRED_SYNTHETIC_DISCLAIMER

    def test_expected_record_count(self, hero_fixture: dict[str, Any]) -> None:
        assert len(_records(hero_fixture)) == len(EXPECTED_RECORD_IDS)

    def test_exact_committed_record_ids(self, hero_fixture: dict[str, Any]) -> None:
        ids = tuple(record["isolate_id"] for record in _records(hero_fixture))
        assert ids == EXPECTED_RECORD_IDS

    def test_prescribed_hero_record_ids_present(self, hero_fixture: dict[str, Any]) -> None:
        ids = {record["isolate_id"] for record in _records(hero_fixture)}
        assert set(HERO_RECORD_IDS) <= ids


class TestMaterialCompleteness:
    def test_no_null_values_anywhere(self, hero_fixture: dict[str, Any]) -> None:
        def walk(node: object) -> bool:
            if node is None:
                return False
            if isinstance(node, dict):
                return all(walk(value) for value in node.values())
            if isinstance(node, list):
                return all(walk(item) for item in node)
            return True

        assert walk(hero_fixture)

    def test_no_blank_strings_anywhere(self, hero_fixture: dict[str, Any]) -> None:
        for value in _strings(hero_fixture):
            assert value.strip()

    def test_no_placeholder_values(self, hero_fixture: dict[str, Any]) -> None:
        # The golden fixture must never carry unknown/placeholder markers.
        for value in _strings(hero_fixture):
            assert value not in {"UNKNOWN", "TBD", "N/A"}

    def test_every_record_carries_all_material_fields(self, hero_fixture: dict[str, Any]) -> None:
        for record in _records(hero_fixture):
            assert set(record) == RECORD_FIELDS
            assert record["ast_results"]

    def test_hero_records_are_complete_and_coherent(self, hero_fixture: dict[str, Any]) -> None:
        # Doc-alignment pin: the prescribed hero isolates are Ward A
        # Klebsiella pneumoniae blood isolates (PCR §4-5, AGENT_ARCH §6).
        records = {record["isolate_id"]: record for record in _records(hero_fixture)}
        for record_id in HERO_RECORD_IDS:
            record = records[record_id]
            assert record["organism_name"] == "Klebsiella pneumoniae"
            assert record["ward"] == "SYNTH-WARD-A"
            assert record["specimen_type"] == "blood"


class TestIdentityAndProofReferenceReadiness:
    def test_record_ids_unique(self, hero_fixture: dict[str, Any]) -> None:
        ids = [record["isolate_id"] for record in _records(hero_fixture)]
        assert len(ids) == len(set(ids))

    def test_record_ids_follow_committed_convention(self, hero_fixture: dict[str, Any]) -> None:
        for record in _records(hero_fixture):
            assert re.fullmatch(r"ISO-\d{3}", record["isolate_id"])

    def test_record_ids_work_as_canonical_record_references(
        self, hero_fixture: dict[str, Any]
    ) -> None:
        # ISO-* IDs must flow directly into #28 CanonicalRecordReference
        # (opaque, non-blank, no edge whitespace) for later proof references.
        for record in _records(hero_fixture):
            reference = CanonicalRecordReference(
                record_id=record["isolate_id"],
                field_path="organism_name",
                expected_value=record["organism_name"],
            )
            assert reference.record_id == record["isolate_id"]
            assert reference.expected_value == record["organism_name"]

    def test_patient_tokens_unique_and_synthetic(self, hero_fixture: dict[str, Any]) -> None:
        tokens = [record["patient_token"] for record in _records(hero_fixture)]
        assert len(tokens) == len(set(tokens))
        assert all(re.fullmatch(r"SYNTH-CASE-\d{3}", token) for token in tokens)


class TestAstObservations:
    def _ast_pairs(self, fixture: dict[str, Any]) -> Iterator[tuple[str, str, dict[str, Any]]]:
        for record in _records(fixture):
            for code, entry in record["ast_results"].items():
                yield record["isolate_id"], code, entry

    def test_every_ast_entry_satisfies_the_schema(
        self, hero_fixture: dict[str, Any], schema: dict[str, Any]
    ) -> None:
        # Re-root the $defs so the subschema's internal $refs resolve.
        entry_schema = {"$defs": schema["$defs"], "$ref": "#/$defs/ast_entry"}
        for _, _, entry in self._ast_pairs(hero_fixture):
            _validator(entry_schema).validate(entry)

    def test_ast_keys_match_antibiotic_codes(self, hero_fixture: dict[str, Any]) -> None:
        for _, code, entry in self._ast_pairs(hero_fixture):
            assert entry["antibiotic_code"] == code

    def test_ast_antibiotic_codes_nonblank(self, hero_fixture: dict[str, Any]) -> None:
        for _, code, _ in self._ast_pairs(hero_fixture):
            assert code.strip() == code

    def test_interpretations_use_explicit_vocabulary(self, hero_fixture: dict[str, Any]) -> None:
        # The golden fixture uses only S/I/R; UNKNOWN is schema-reserved but
        # never used by the complete hero input.
        for _, _, entry in self._ast_pairs(hero_fixture):
            assert entry["interpretation"] in GOLDEN_INTERPRETATIONS

    def test_all_records_share_the_same_antibiotic_panel(
        self, hero_fixture: dict[str, Any]
    ) -> None:
        # A uniform panel keeps resistance vectors aligned for the future
        # deterministic similarity stage.
        for record in _records(hero_fixture):
            assert set(record["ast_results"]) == EXPECTED_ANTIBIOTIC_CODES

    def test_hero_records_share_resistance_phenotype(self, hero_fixture: dict[str, Any]) -> None:
        # A factual property of the observations: the three prescribed Ward A
        # Klebsiella pneumoniae isolates carry identical interpretation
        # vectors. This is input, not a derived cluster claim.
        hero_vectors = {
            record["isolate_id"]: _interpretation_vector(record)
            for record in _records(hero_fixture)
            if record["isolate_id"] in HERO_RECORD_IDS
        }
        assert len(hero_vectors) == len(HERO_RECORD_IDS)
        assert len(set(hero_vectors.values())) == 1

    def test_hero_phenotype_is_not_universal(self, hero_fixture: dict[str, Any]) -> None:
        # The matching phenotype must be distinguishable from the rest of
        # the fixture, or the later surveillance stage would find nothing.
        records = {record["isolate_id"]: record for record in _records(hero_fixture)}
        hero_vector = _interpretation_vector(records[HERO_RECORD_IDS[0]])
        contrasts = [
            _interpretation_vector(record)
            for record in _records(hero_fixture)
            if record["isolate_id"] not in HERO_RECORD_IDS
        ]
        assert hero_vector not in contrasts


class TestSyntheticSafety:
    def test_only_known_synthetic_facility_ids(self, hero_fixture: dict[str, Any]) -> None:
        assert {r["facility_id"] for r in _records(hero_fixture)} == EXPECTED_FACILITY_IDS

    def test_only_known_synthetic_lab_ids(self, hero_fixture: dict[str, Any]) -> None:
        assert {r["lab_id"] for r in _records(hero_fixture)} == EXPECTED_LAB_IDS

    def test_only_known_synthetic_wards(self, hero_fixture: dict[str, Any]) -> None:
        assert {r["ward"] for r in _records(hero_fixture)} == EXPECTED_WARDS

    def test_single_synthetic_import_batch(self, hero_fixture: dict[str, Any]) -> None:
        ids = {r["source_import_id"] for r in _records(hero_fixture)}
        assert ids == EXPECTED_SOURCE_IMPORT_IDS

    def test_organism_names_are_known_synthetic_vocabulary(
        self, hero_fixture: dict[str, Any]
    ) -> None:
        names = {r["organism_name"] for r in _records(hero_fixture)}
        assert names == EXPECTED_ORGANISMS

    def test_every_identity_field_carries_synthetic_prefix(
        self, hero_fixture: dict[str, Any]
    ) -> None:
        for record in _records(hero_fixture):
            for field in ("facility_id", "lab_id", "ward", "patient_token"):
                assert re.fullmatch(r"SYNTH-[A-Z0-9-]+", record[field])
            assert re.fullmatch(r"SYNTH-[A-Z0-9-]+", record["source_import_id"])


class TestNoDerivedFactLeakage:
    def test_fixture_contains_observations_only(self, hero_fixture: dict[str, Any]) -> None:
        assert set(hero_fixture) == {
            "schema_version",
            "dataset_id",
            "synthetic",
            "provenance",
            "records",
        }

    def test_no_future_result_fields_anywhere(self, hero_fixture: dict[str, Any]) -> None:
        def keys(node: object) -> Iterator[str]:
            if isinstance(node, dict):
                for key, value in node.items():
                    yield key
                    yield from keys(value)

        for key in keys(hero_fixture):
            assert key not in DERIVED_FACT_FIELDS


class TestDeterminism:
    def test_fixture_is_reproducible_from_disk(self, hero_fixture: dict[str, Any]) -> None:
        # The fixture is a committed static artifact: re-reading it yields
        # identical content (no runtime generation anywhere).
        assert _load_json(FIXTURE_PATH) == hero_fixture


class TestSchemaEnforcesContract:
    def test_rejects_missing_isolate_id(self, schema: dict[str, Any]) -> None:
        def mutate(f: dict[str, Any]) -> None:
            del f["records"][0]["isolate_id"]

        _expect_invalid(schema, mutate)

    def test_rejects_missing_organism_name(self, schema: dict[str, Any]) -> None:
        def mutate(f: dict[str, Any]) -> None:
            del f["records"][0]["organism_name"]

        _expect_invalid(schema, mutate)

    def test_rejects_missing_ast_results(self, schema: dict[str, Any]) -> None:
        def mutate(f: dict[str, Any]) -> None:
            del f["records"][0]["ast_results"]

        _expect_invalid(schema, mutate)

    def test_rejects_empty_ast_results(self, schema: dict[str, Any]) -> None:
        def mutate(f: dict[str, Any]) -> None:
            f["records"][0]["ast_results"] = {}

        _expect_invalid(schema, mutate)

    def test_rejects_missing_ward(self, schema: dict[str, Any]) -> None:
        def mutate(f: dict[str, Any]) -> None:
            del f["records"][0]["ward"]

        _expect_invalid(schema, mutate)

    def test_rejects_missing_collection_date(self, schema: dict[str, Any]) -> None:
        def mutate(f: dict[str, Any]) -> None:
            del f["records"][0]["collection_date"]

        _expect_invalid(schema, mutate)

    def test_rejects_invalid_collection_date(self, schema: dict[str, Any]) -> None:
        def mutate(f: dict[str, Any]) -> None:
            f["records"][0]["collection_date"] = "not-a-date"

        _expect_invalid(schema, mutate)

    def test_rejects_synthetic_marker_false(self, schema: dict[str, Any]) -> None:
        def mutate(f: dict[str, Any]) -> None:
            f["synthetic"] = False

        _expect_invalid(schema, mutate)

    def test_rejects_unknown_interpretation(self, schema: dict[str, Any]) -> None:
        def mutate(f: dict[str, Any]) -> None:
            f["records"][0]["ast_results"]["MEM"]["interpretation"] = "X"

        _expect_invalid(schema, mutate)

    def test_rejects_unknown_extra_field(self, schema: dict[str, Any]) -> None:
        def mutate(f: dict[str, Any]) -> None:
            f["records"][0]["cluster_score"] = 0.9

        _expect_invalid(schema, mutate)

    def test_rejects_non_synthetic_facility_id(self, schema: dict[str, Any]) -> None:
        def mutate(f: dict[str, Any]) -> None:
            f["records"][0]["facility_id"] = "REAL-FACILITY-9"

        _expect_invalid(schema, mutate)

    def test_rejects_non_synthetic_ward_name(self, schema: dict[str, Any]) -> None:
        def mutate(f: dict[str, Any]) -> None:
            f["records"][0]["ward"] = "Ward A"

        _expect_invalid(schema, mutate)

    def test_rejects_whitespace_organism_name(self, schema: dict[str, Any]) -> None:
        def mutate(f: dict[str, Any]) -> None:
            f["records"][0]["organism_name"] = "   "

        _expect_invalid(schema, mutate)

    def test_rejects_malformed_isolate_id(self, schema: dict[str, Any]) -> None:
        def mutate(f: dict[str, Any]) -> None:
            f["records"][0]["isolate_id"] = "ISOLATE-999"

        _expect_invalid(schema, mutate)

    def test_rejects_empty_records_collection(self, schema: dict[str, Any]) -> None:
        def mutate(f: dict[str, Any]) -> None:
            f["records"] = []

        _expect_invalid(schema, mutate)
