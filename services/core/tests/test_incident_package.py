"""Focused tests for Issue #52 versioned proof-carrying incident package contract."""

from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from ngabo.application.enums.incident_package_error_code import (
    IncidentPackageErrorCode,
)
from ngabo.application.services.incident_package_codec import (
    deserialize_incident_package,
    incident_package_to_canonical_json,
    incident_package_to_primitive,
    parse_incident_package,
)
from ngabo.application.value_objects.incident_package import (
    DraftCoordinationMessage,
    IncidentPackageCandidate,
    IncidentPackageEvidenceBinding,
    IncidentPackageId,
    IncidentPackageMetadata,
    PackageContractVersion,
    PackageLimitation,
)
from ngabo.domain.enums.action_class import ActionClass
from ngabo.domain.enums.claim_type import ClaimType
from ngabo.domain.value_objects.claim_id import ClaimId
from ngabo.domain.value_objects.evidence_reference import EvidenceReferenceId
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.proof_references import (
    ApprovedEvidenceReference,
    CanonicalRecordReference,
    DeterministicFindingReference,
)
from ngabo.domain.value_objects.reasoning_claim import ReasoningClaim
from ngabo.domain.value_objects.source_watermark import SourceWatermark

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "ngabo"
REPO_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_SCHEMA_PATH = REPO_ROOT / "data" / "schemas" / "incident_package.schema.json"

# Representative synthetic hero values (carbapenem-resistant K. pneumoniae
# cluster). Synthetic-only; not clinical truth.
INCIDENT = IncidentId("INC-001")
INCIDENT_VERSION = IncidentVersion(1)
WATERMARK = SourceWatermark("ngabo-source-v1:sha256:abc123")
CORPUS_DIGEST = "575a8552d35eb1ab6b2bb8ffa60f020bf643f4358fa28c50865fbe79e9085aeb"


def _record_ref(record_id: str, field_path: str, expected_value: str) -> CanonicalRecordReference:
    return CanonicalRecordReference(
        record_id=record_id, field_path=field_path, expected_value=expected_value
    )


def _finding_ref() -> DeterministicFindingReference:
    return DeterministicFindingReference(
        finding_id="profile-comparison-17",
        policy_version="resistance-profile-similarity-v1",
        input_refs=("ISO-031", "ISO-034"),
        output_value="HIGH_SIMILARITY",
    )


def _evidence_ref() -> ApprovedEvidenceReference:
    return ApprovedEvidenceReference(
        source_id="WHO-AMR-001",
        chunk_id="WHO-AMR-001::ipc-principle-01",
        provenance="WHO-AMR-001 v1; 2017-11-01",
        support="supports-contact-precautions",
    )


def _hero_claims() -> tuple[ReasoningClaim, ...]:
    return (
        ReasoningClaim(
            claim_id=ClaimId("claim-01"),
            claim_type=ClaimType.OBSERVED_FACT,
            statement=(
                "Three Klebsiella pneumoniae isolates were recorded in ward A "
                "during the surveillance window."
            ),
            supporting_record_refs=(
                _record_ref("ISO-031", "ward", "WARD-A"),
            ),
        ),
        ReasoningClaim(
            claim_id=ClaimId("claim-02"),
            claim_type=ClaimType.DERIVED_FINDING,
            statement="The cluster shows a closely matching resistance phenotype.",
            supporting_finding_refs=(_finding_ref(),),
        ),
        ReasoningClaim(
            claim_id=ClaimId("claim-03"),
            claim_type=ClaimType.EVIDENCE_STATEMENT,
            statement=(
                "Approved WHO guidance supports contact precautions for "
                "carbapenem-resistant Enterobacteriaceae."
            ),
            supporting_evidence_refs=(_evidence_ref(),),
        ),
        ReasoningClaim(
            claim_id=ClaimId("claim-04"),
            claim_type=ClaimType.HYPOTHESIS,
            statement="A shared epidemiologic process may be driving this cluster.",
            supporting_finding_refs=(_finding_ref(),),
            uncertainties=("Genomic relatedness is unavailable.",),
        ),
        ReasoningClaim(
            claim_id=ClaimId("claim-05"),
            claim_type=ClaimType.ACTION_JUSTIFICATION,
            statement=(
                "A safe external coordination message may help verify whether "
                "a shared process is occurring."
            ),
            supporting_evidence_refs=(_evidence_ref(),),
            requested_action_class=ActionClass.SAFE_EXTERNAL_COORDINATION,
        ),
    )


def _hero_package() -> IncidentPackageCandidate:
    return IncidentPackageCandidate(
        package_id=IncidentPackageId("PKG-001"),
        contract_version=PackageContractVersion("1.0"),
        incident_id=INCIDENT,
        incident_version=INCIDENT_VERSION,
        source_watermark=WATERMARK,
        metadata=IncidentPackageMetadata(
            policy_config_version="signal-policy-v1",
            model_identifier="gemini-3.6-flash",
            model_version="1.0",
            evidence_binding=IncidentPackageEvidenceBinding(
                corpus_id="ngabo-approved-evidence-v1",
                manifest_version="1.0",
                corpus_digest=CORPUS_DIGEST,
                evidence_references=(
                    EvidenceReferenceId("WHO-AMR-001::ipc-principle-01"),
                    EvidenceReferenceId("CDC-CRE-001::facility-response-01"),
                ),
            ),
            generation_run_id="run-001",
        ),
        claims=_hero_claims(),
        uncertainties=("Genomic relatedness is unavailable.",),
        limitations=(
            PackageLimitation("Genomic relatedness unavailable."),
            PackageLimitation("Source window is incomplete."),
            PackageLimitation("Clinical confirmation is outside Ngabo's authority."),
        ),
        draft_coordination_message=DraftCoordinationMessage(
            subject="Potential carbapenem-resistant Enterobacterales cluster",
            body="Synthetic candidate: requesting facility infection-control verification.",
            intended_purpose="request-facility-infection-control-verification",
            candidate_recipient_role="facility-infection-control-coordinator",
        ),
    )


def test_valid_construction() -> None:
    package = _hero_package()
    assert package.package_id.value == "PKG-001"
    assert package.contract_version.value == "1.0"
    assert package.incident_id == INCIDENT
    assert package.incident_version == INCIDENT_VERSION
    assert package.source_watermark == WATERMARK
    assert len(package.claims) == 5
    # Claims are canonicalized by claim_id.
    assert [claim.claim_id.value for claim in package.claims] == [
        "claim-01",
        "claim-02",
        "claim-03",
        "claim-04",
        "claim-05",
    ]


def test_hero_round_trip_preserves_typed_references_and_versions() -> None:
    package = _hero_package()
    serialized = incident_package_to_canonical_json(package)
    round_trip = deserialize_incident_package(serialized)
    assert round_trip.ok
    assert round_trip.package == package
    # Typed reference families survive as the correct semantic types.
    parsed = round_trip.package
    assert parsed is not None
    assert isinstance(parsed.claims[0].supporting_record_refs[0], CanonicalRecordReference)
    assert isinstance(parsed.claims[1].supporting_finding_refs[0], DeterministicFindingReference)
    assert isinstance(parsed.claims[2].supporting_evidence_refs[0], ApprovedEvidenceReference)


def test_canonical_serialization_is_stable_regardless_of_claim_order() -> None:
    package = _hero_package()
    canonical_a = incident_package_to_canonical_json(package)
    # Build an equivalent package with claims supplied in the reverse order.
    reversed_claims = tuple(reversed(_hero_claims()))
    equivalent = IncidentPackageCandidate(
        package_id=package.package_id,
        contract_version=package.contract_version,
        incident_id=package.incident_id,
        incident_version=package.incident_version,
        source_watermark=package.source_watermark,
        metadata=package.metadata,
        claims=reversed_claims,
        uncertainties=package.uncertainties,
        limitations=package.limitations,
        draft_coordination_message=package.draft_coordination_message,
    )
    assert incident_package_to_canonical_json(equivalent) == canonical_a


def test_order_independent_collections_serialize_identically() -> None:
    package = _hero_package()
    canonical = incident_package_to_canonical_json(package)
    # Build an equivalent package with semantically unordered collections in the
    # reverse order; the deterministic canonicalization must yield the same JSON.
    reversed_metadata = IncidentPackageMetadata(
        policy_config_version=package.metadata.policy_config_version,
        model_identifier=package.metadata.model_identifier,
        model_version=package.metadata.model_version,
        evidence_binding=IncidentPackageEvidenceBinding(
            corpus_id=package.metadata.evidence_binding.corpus_id,
            manifest_version=package.metadata.evidence_binding.manifest_version,
            corpus_digest=package.metadata.evidence_binding.corpus_digest,
            evidence_references=tuple(
                reversed(package.metadata.evidence_binding.evidence_references)
            ),
        ),
        generation_run_id=package.metadata.generation_run_id,
    )
    equivalent = IncidentPackageCandidate(
        package_id=package.package_id,
        contract_version=package.contract_version,
        incident_id=package.incident_id,
        incident_version=package.incident_version,
        source_watermark=package.source_watermark,
        metadata=reversed_metadata,
        claims=tuple(reversed(_hero_claims())),
        uncertainties=tuple(reversed(package.uncertainties)),
        limitations=tuple(reversed(package.limitations)),
        draft_coordination_message=package.draft_coordination_message,
    )
    assert incident_package_to_canonical_json(equivalent) == canonical


def test_immutability_after_construction() -> None:
    package = _hero_package()
    with pytest.raises(FrozenInstanceError):
        package.claims = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        package.metadata = package.metadata  # type: ignore[misc]
    assert isinstance(package.claims, tuple)
    assert isinstance(package.limitations, tuple)


def test_duplicate_claim_id_rejected_by_constructor() -> None:
    claims = (
        _hero_claims()[0],
        ReasoningClaim(
            claim_id=ClaimId("claim-01"),
            claim_type=ClaimType.EVIDENCE_STATEMENT,
            statement="Duplicate claim id must be rejected.",
            supporting_evidence_refs=(_evidence_ref(),),
        ),
    )
    with pytest.raises(ValueError, match="Duplicate claim ID"):
        IncidentPackageCandidate(
            package_id=IncidentPackageId("PKG-001"),
            contract_version=PackageContractVersion("1.0"),
            incident_id=INCIDENT,
            incident_version=INCIDENT_VERSION,
            source_watermark=WATERMARK,
            metadata=_hero_package().metadata,
            claims=claims,
        )


def test_duplicate_claim_id_parse_failure() -> None:
    primitive = incident_package_to_primitive(_hero_package())
    claims = primitive["claims"]
    assert isinstance(claims, list)
    claims.append(dict(claims[0]))
    result = parse_incident_package(primitive)
    assert not result.ok
    assert any(
        error.code == IncidentPackageErrorCode.DUPLICATE_CLAIM_ID
        for error in result.errors
    )


def test_missing_required_field_fails_closed() -> None:
    primitive = incident_package_to_primitive(_hero_package())
    del primitive["package_id"]
    result = parse_incident_package(primitive)
    assert not result.ok
    assert any(
        error.code == IncidentPackageErrorCode.MISSING_REQUIRED_FIELD
        for error in result.errors
    )


def test_unsupported_package_version_fails_closed() -> None:
    primitive = incident_package_to_primitive(_hero_package())
    primitive["package_contract_version"] = "2.0"
    result = parse_incident_package(primitive)
    assert not result.ok
    assert any(
        error.code == IncidentPackageErrorCode.UNSUPPORTED_PACKAGE_VERSION
        for error in result.errors
    )


def test_package_contract_version_only_supported_constructible() -> None:
    assert PackageContractVersion("1.0").value == "1.0"
    with pytest.raises(ValueError, match="Unsupported package contract version"):
        PackageContractVersion("2.0")


def test_constructible_package_round_trips_under_supported_version() -> None:
    package = _hero_package()
    assert package.contract_version.value == "1.0"
    result = deserialize_incident_package(incident_package_to_canonical_json(package))
    assert result.ok
    assert result.package is not None
    assert result.package.contract_version.value == "1.0"


@pytest.mark.parametrize("limitation", ["  leading", "trailing  ", "   "])
def test_whitespace_padded_limitation_returns_structured_failure(
    limitation: str,
) -> None:
    primitive = incident_package_to_primitive(_hero_package())
    primitive["limitations"] = [limitation]
    # Must NOT raise out of the parser.
    result = parse_incident_package(primitive)
    assert not result.ok
    assert result.package is None
    assert any(
        error.code == IncidentPackageErrorCode.MALFORMED_PACKAGE
        and error.path == ("limitations", "0")
        for error in result.errors
    )


def test_valid_limitation_parses_normally() -> None:
    primitive = incident_package_to_primitive(_hero_package())
    primitive["limitations"] = ["Genomic relatedness unavailable."]
    result = parse_incident_package(primitive)
    assert result.ok
    assert result.package is not None
    assert result.package.limitations == (
        PackageLimitation("Genomic relatedness unavailable."),
    )


@pytest.mark.parametrize(
    "authority_field",
    [
        {"verified": True},
        {"verification": {"valid": True}},
        {"action_authorized": True},
        {"ready_to_send": True},
        {"approved": True},
        {"authorized_action_class": "A1"},
    ],
)
def test_forbidden_authority_fields_fail_closed(authority_field: dict[str, object]) -> None:
    primitive = incident_package_to_primitive(_hero_package())
    primitive.update(authority_field)
    result = parse_incident_package(primitive)
    assert not result.ok
    assert any(
        error.code == IncidentPackageErrorCode.FORBIDDEN_FIELD
        for error in result.errors
    )


def test_package_structurally_cannot_self_verify_or_authorize() -> None:
    package = _hero_package()
    for attribute in (
        "verified",
        "approved",
        "authorized",
        "ready_to_send",
        "authorization",
        "verification",
    ):
        assert not hasattr(package, attribute)


def test_forbidden_claim_type_fails_closed() -> None:
    primitive = incident_package_to_primitive(_hero_package())
    claims = primitive["claims"]
    assert isinstance(claims, list)
    claims[0]["claim_type"] = "DIAGNOSIS"
    result = parse_incident_package(primitive)
    assert not result.ok
    assert any(
        error.code == IncidentPackageErrorCode.MALFORMED_PACKAGE
        and "claim_type" in error.path
        for error in result.errors
    )


def test_hypothesis_uncertainty_survives_round_trip() -> None:
    package = _hero_package()
    round_trip = deserialize_incident_package(incident_package_to_canonical_json(package))
    assert round_trip.ok
    parsed = round_trip.package
    assert parsed is not None
    hypothesis = next(c for c in parsed.claims if c.claim_type is ClaimType.HYPOTHESIS)
    assert hypothesis.uncertainties == ("Genomic relatedness is unavailable.",)


def test_missing_hypothesis_uncertainty_rejected() -> None:
    primitive = incident_package_to_primitive(_hero_package())
    claims = primitive["claims"]
    assert isinstance(claims, list)
    claims[3]["uncertainties"] = []
    result = parse_incident_package(primitive)
    assert not result.ok
    assert any(
        error.code == IncidentPackageErrorCode.MISSING_REQUIRED_FIELD
        for error in result.errors
    )


def test_unknown_field_fails_closed() -> None:
    primitive = incident_package_to_primitive(_hero_package())
    primitive["unexpected_model_field"] = "x"
    result = parse_incident_package(primitive)
    assert not result.ok
    assert any(
        error.code == IncidentPackageErrorCode.FORBIDDEN_FIELD
        for error in result.errors
    )


def test_draft_message_round_trips_as_draft_only() -> None:
    package = _hero_package()
    assert package.draft_coordination_message is not None
    assert package.draft_coordination_message.intended_purpose == (
        "request-facility-infection-control-verification"
    )
    for attribute in ("send", "sent", "delivery_id", "transport_id", "authorized"):
        assert not hasattr(package.draft_coordination_message, attribute)
    round_trip = deserialize_incident_package(incident_package_to_canonical_json(package))
    assert round_trip.ok
    assert round_trip.package is not None
    assert round_trip.package.draft_coordination_message is not None
    assert (
        round_trip.package.draft_coordination_message.subject
        == package.draft_coordination_message.subject
    )


def test_architecture_no_adk_gemini_pydantic_cloud_leakage() -> None:
    forbidden = ("google", "vertexai", "fastapi", "pydantic", "firebase_admin")
    sources = [
        *PACKAGE_ROOT.joinpath("application").rglob("incident_package*.py"),
        PACKAGE_ROOT / "application" / "services" / "incident_package_codec.py",
        PACKAGE_ROOT / "application" / "enums" / "incident_package_error_code.py",
    ]
    for path in sources:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules.add(node.module)
        for module in modules:
            prefix = module.split(".", 1)[0]
            assert prefix not in forbidden, f"{path} imports forbidden {module}"


def test_malformed_json_fails_closed() -> None:
    result = deserialize_incident_package("{ not json")
    assert not result.ok
    assert result.errors[0].code == IncidentPackageErrorCode.MALFORMED_PACKAGE


def test_package_primitive_matches_schema() -> None:
    raw = incident_package_to_primitive(_hero_package())
    schema = json.loads(PACKAGE_SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(raw),
        key=lambda error: list(error.path),
    )
    assert errors == [], [error.message for error in errors]


def test_package_schema_exposes_no_authority_states() -> None:
    schema = json.loads(PACKAGE_SCHEMA_PATH.read_text(encoding="utf-8"))

    def _property_names(node: object, collected: set[str]) -> None:
        if isinstance(node, dict):
            props = node.get("properties")
            if isinstance(props, dict):
                collected.update(str(key) for key in props)
            for value in node.values():
                _property_names(value, collected)
        elif isinstance(node, list):
            for value in node:
                _property_names(value, collected)

    names: set[str] = set()
    _property_names(schema, names)
    for token in ("verified", "authorized", "executed", "ready_to_send"):
        assert token not in names, f"package schema must not expose property {token!r}"
