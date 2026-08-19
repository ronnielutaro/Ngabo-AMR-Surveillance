"""Unit tests for the proof-carrying claim contracts (Issue #28 / M1B.4)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from ngabo.domain.enums.action_class import ActionClass
from ngabo.domain.enums.claim_type import ClaimType
from ngabo.domain.value_objects.claim_id import ClaimId
from ngabo.domain.value_objects.proof_references import (
    ApprovedEvidenceReference,
    CanonicalRecordReference,
    DeterministicFindingReference,
)
from ngabo.domain.value_objects.reasoning_claim import ReasoningClaim

EXPECTED_CLAIM_TYPES = (
    ClaimType.OBSERVED_FACT,
    ClaimType.DERIVED_FINDING,
    ClaimType.EVIDENCE_STATEMENT,
    ClaimType.HYPOTHESIS,
    ClaimType.ACTION_JUSTIFICATION,
)

FORBIDDEN_AUTHORITY_NAMES = (
    "DIAGNOSIS",
    "PRESCRIPTION",
    "OUTBREAK_CONFIRMATION",
    "MANDATORY_CONTAINMENT_ORDER",
    "OFFICIAL_PUBLIC_HEALTH_DECLARATION",
)


def _record_ref() -> CanonicalRecordReference:
    return CanonicalRecordReference("ISO-031", "ward", "Ward A")


def _finding_ref() -> DeterministicFindingReference:
    return DeterministicFindingReference(
        "profile-comparison-17", "detector-v1", ("ISO-031", "ISO-034"), "similarity=0.93"
    )


def _evidence_ref() -> ApprovedEvidenceReference:
    return ApprovedEvidenceReference("GUIDANCE-004", "chunk-12", "guidance-v2.1", "supports")


def _make_hypothesis(
    uncertainties: tuple[str, ...] = ("Genomic relatedness is unavailable.",),
    requested_action_class: ActionClass | None = ActionClass.SAFE_EXTERNAL_COORDINATION,
    confidence_label: str | None = "BOUNDED_HYPOTHESIS",
) -> ReasoningClaim:
    return ReasoningClaim(
        claim_id=ClaimId("claim-01"),
        claim_type=ClaimType.HYPOTHESIS,
        statement="Possible shared epidemiologic process.",
        supporting_record_refs=(_record_ref(),),
        uncertainties=uncertainties,
        requested_action_class=requested_action_class,
        confidence_label=confidence_label,
    )


class TestClaimType:
    @pytest.mark.parametrize(
        ("claim_type", "expected_value"),
        [
            (ClaimType.OBSERVED_FACT, "OBSERVED_FACT"),
            (ClaimType.DERIVED_FINDING, "DERIVED_FINDING"),
            (ClaimType.EVIDENCE_STATEMENT, "EVIDENCE_STATEMENT"),
            (ClaimType.HYPOTHESIS, "HYPOTHESIS"),
            (ClaimType.ACTION_JUSTIFICATION, "ACTION_JUSTIFICATION"),
        ],
    )
    def test_stable_value(self, claim_type: ClaimType, expected_value: str) -> None:
        assert claim_type.value == expected_value
        assert str(claim_type) == expected_value

    def test_exactly_five_allowed_families(self) -> None:
        assert tuple(ClaimType) == EXPECTED_CLAIM_TYPES

    def test_forbidden_authority_claim_types_absent(self) -> None:
        for name in FORBIDDEN_AUTHORITY_NAMES:
            assert name not in {member.value for member in ClaimType}
            assert not hasattr(ClaimType, name)


class TestClaimId:
    def test_valid_construction(self) -> None:
        claim_id = ClaimId("claim-01")
        assert claim_id.value == "claim-01"
        assert str(claim_id) == "claim-01"

    @pytest.mark.parametrize(
        "invalid",
        ["", "   ", "claim", "claim-", "claim-01x", "CLAIM-01", " claim-01", None, 5],
    )
    def test_rejects_invalid_identifiers(self, invalid: object) -> None:
        with pytest.raises(ValueError):
            ClaimId(invalid)  # type: ignore[arg-type]

    def test_value_semantics(self) -> None:
        assert ClaimId("claim-01") == ClaimId("claim-01")
        assert ClaimId("claim-01") != ClaimId("claim-02")
        assert ClaimId("claim-01") != object()
        assert {ClaimId("claim-01"): "x"}[ClaimId("claim-01")] == "x"

    def test_immutable(self) -> None:
        claim_id = ClaimId("claim-01")
        with pytest.raises(FrozenInstanceError):
            claim_id.value = "claim-02"  # type: ignore[misc]


class TestProofReferences:
    def test_valid_canonical_record_reference(self) -> None:
        ref = _record_ref()
        assert ref.record_id == "ISO-031"
        assert ref.field_path == "ward"
        assert ref.expected_value == "Ward A"

    def test_valid_deterministic_finding_reference(self) -> None:
        ref = _finding_ref()
        assert ref.finding_id == "profile-comparison-17"
        assert ref.policy_version == "detector-v1"
        assert ref.input_refs == ("ISO-031", "ISO-034")
        assert ref.output_value == "similarity=0.93"

    def test_valid_approved_evidence_reference(self) -> None:
        ref = _evidence_ref()
        assert ref.source_id == "GUIDANCE-004"
        assert ref.chunk_id == "chunk-12"
        assert ref.provenance == "guidance-v2.1"
        assert ref.support == "supports"

    def test_evidence_chunk_id_may_be_absent(self) -> None:
        ref = ApprovedEvidenceReference("GUIDANCE-004", None, "guidance-v2.1", "supports")
        assert ref.chunk_id is None

    @pytest.mark.parametrize(
        "invalid",
        ["", "   ", " ISO-031", "ISO-031 ", None, 5],
    )
    def test_record_id_rejected_when_invalid(self, invalid: object) -> None:
        with pytest.raises(ValueError):
            CanonicalRecordReference(invalid, "ward", "Ward A")  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "invalid",
        ["", "   ", " detector-v1", None],
    )
    def test_finding_id_rejected_when_invalid(self, invalid: object) -> None:
        with pytest.raises(ValueError):
            DeterministicFindingReference(
                invalid,  # type: ignore[arg-type]
                "detector-v1",
                ("ISO-031",),
                "similarity=0.93",
            )

    @pytest.mark.parametrize(
        "invalid",
        ["", "   ", " GUIDANCE-004", None],
    )
    def test_source_id_rejected_when_invalid(self, invalid: object) -> None:
        with pytest.raises(ValueError):
            ApprovedEvidenceReference(invalid, None, "guidance-v2.1", "supports")  # type: ignore[arg-type]

    def test_finding_input_refs_rejected_when_any_blank(self) -> None:
        with pytest.raises(ValueError):
            DeterministicFindingReference(
                "profile-comparison-17", "detector-v1", ("ISO-031", "  "), "x"
            )

    def test_evidence_chunk_id_rejected_when_blank(self) -> None:
        with pytest.raises(ValueError):
            ApprovedEvidenceReference("GUIDANCE-004", "   ", "guidance-v2.1", "supports")

    def test_reference_types_are_typed_and_distinct(self) -> None:
        record = _record_ref()
        finding = _finding_ref()
        evidence = _evidence_ref()
        assert type(record) is CanonicalRecordReference
        assert type(finding) is DeterministicFindingReference
        assert type(evidence) is ApprovedEvidenceReference
        # Compare through an object-typed alias: the runtime inequality is
        # the point, and mypy's comparison-overlap rule forbids the direct
        # disjoint-type comparison.
        record_as_object: object = record
        finding_as_object: object = finding
        evidence_as_object: object = evidence
        assert record_as_object != finding
        assert finding_as_object != evidence
        assert evidence_as_object != record
        assert record != object()
        assert finding != object()
        assert evidence != object()

    def test_value_semantics(self) -> None:
        assert _record_ref() == _record_ref()
        assert _finding_ref() == _finding_ref()
        assert _evidence_ref() == _evidence_ref()
        assert _record_ref() != object()
        assert {_record_ref(): "x"}[_record_ref()] == "x"
        assert {_finding_ref(): "x"}[_finding_ref()] == "x"
        assert {_evidence_ref(): "x"}[_evidence_ref()] == "x"

    def test_references_are_frozen(self) -> None:
        with pytest.raises(FrozenInstanceError):
            _record_ref().record_id = "ISO-999"  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            _finding_ref().output_value = "changed"  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            _evidence_ref().source_id = "GUIDANCE-999"  # type: ignore[misc]

    def test_input_refs_tuple_cannot_be_mutated(self) -> None:
        ref = _finding_ref()
        with pytest.raises(AttributeError):
            ref.input_refs.append("ISO-999")  # type: ignore[attr-defined]
        with pytest.raises(FrozenInstanceError):
            ref.input_refs = ("ISO-999",)  # type: ignore[misc]


class TestReasoningClaimFamilies:
    def test_observed_fact_claim(self) -> None:
        claim = ReasoningClaim(
            claim_id=ClaimId("claim-01"),
            claim_type=ClaimType.OBSERVED_FACT,
            statement="Three K. pneumoniae isolates were recorded in Ward A.",
            supporting_record_refs=(_record_ref(),),
        )
        assert claim.claim_type is ClaimType.OBSERVED_FACT
        assert claim.supporting_record_refs == (_record_ref(),)

    def test_derived_finding_claim(self) -> None:
        claim = ReasoningClaim(
            claim_id=ClaimId("claim-02"),
            claim_type=ClaimType.DERIVED_FINDING,
            statement="The isolates' resistance profiles are similar.",
            supporting_finding_refs=(_finding_ref(),),
        )
        assert claim.claim_type is ClaimType.DERIVED_FINDING
        assert claim.supporting_finding_refs == (_finding_ref(),)

    def test_evidence_statement_claim(self) -> None:
        claim = ReasoningClaim(
            claim_id=ClaimId("claim-03"),
            claim_type=ClaimType.EVIDENCE_STATEMENT,
            statement="Guidance recommends carbapenem resistance screening.",
            supporting_evidence_refs=(_evidence_ref(),),
        )
        assert claim.claim_type is ClaimType.EVIDENCE_STATEMENT
        assert claim.supporting_evidence_refs == (_evidence_ref(),)

    def test_hypothesis_claim(self) -> None:
        claim = _make_hypothesis()
        assert claim.claim_type is ClaimType.HYPOTHESIS
        assert claim.uncertainties == ("Genomic relatedness is unavailable.",)

    def test_action_justification_claim(self) -> None:
        claim = ReasoningClaim(
            claim_id=ClaimId("claim-05"),
            claim_type=ClaimType.ACTION_JUSTIFICATION,
            statement="A coordination notification would help share the candidate finding.",
            supporting_claim_ids=(ClaimId("claim-01"), ClaimId("claim-02")),
            requested_action_class=ActionClass.SAFE_EXTERNAL_COORDINATION,
        )
        assert claim.claim_type is ClaimType.ACTION_JUSTIFICATION
        assert claim.supporting_claim_ids == (ClaimId("claim-01"), ClaimId("claim-02"))
        assert claim.requested_action_class is ActionClass.SAFE_EXTERNAL_COORDINATION


class TestReasoningClaimValidation:
    def test_empty_statement_rejected(self) -> None:
        with pytest.raises(ValueError):
            ReasoningClaim(
                claim_id=ClaimId("claim-01"),
                claim_type=ClaimType.OBSERVED_FACT,
                statement="",
            )
        with pytest.raises(ValueError):
            ReasoningClaim(
                claim_id=ClaimId("claim-01"),
                claim_type=ClaimType.OBSERVED_FACT,
                statement="   ",
            )

    def test_empty_claim_id_rejected(self) -> None:
        with pytest.raises(ValueError):
            ReasoningClaim(
                claim_id=ClaimId(""),
                claim_type=ClaimType.OBSERVED_FACT,
                statement="Three isolates in Ward A.",
            )

    def test_raw_string_claim_id_rejected(self) -> None:
        with pytest.raises(ValueError):
            ReasoningClaim(
                claim_id="claim-01",  # type: ignore[arg-type]
                claim_type=ClaimType.OBSERVED_FACT,
                statement="Three isolates in Ward A.",
            )

    def test_raw_string_claim_type_rejected(self) -> None:
        with pytest.raises(ValueError):
            ReasoningClaim(
                claim_id=ClaimId("claim-01"),
                claim_type="HYPOTHESIS",  # type: ignore[arg-type]
                statement="Possible shared process.",
                uncertainties=("Genomic relatedness is unavailable.",),
            )

    def test_blank_uncertainty_entry_rejected(self) -> None:
        with pytest.raises(ValueError):
            _make_hypothesis(uncertainties=("",))

    def test_blank_confidence_label_rejected(self) -> None:
        with pytest.raises(ValueError):
            _make_hypothesis(confidence_label="   ")

    @pytest.mark.parametrize("invalid_class", ["A1", "A2", "A3"])
    def test_raw_string_requested_action_class_rejected(self, invalid_class: str) -> None:
        with pytest.raises(ValueError):
            _make_hypothesis(requested_action_class=invalid_class)  # type: ignore[arg-type]

    def test_supporting_and_contradicting_references_are_typed_claim_ids(self) -> None:
        claim = ReasoningClaim(
            claim_id=ClaimId("claim-06"),
            claim_type=ClaimType.HYPOTHESIS,
            statement="Possible shared process.",
            supporting_claim_ids=(ClaimId("claim-01"),),
            contradicting_claim_ids=(ClaimId("claim-02"),),
            uncertainties=("Alternative ward transfer explanation exists.",),
        )
        assert all(isinstance(c, ClaimId) for c in claim.supporting_claim_ids)
        assert all(isinstance(c, ClaimId) for c in claim.contradicting_claim_ids)
        assert claim.supporting_claim_ids == (ClaimId("claim-01"),)
        assert claim.contradicting_claim_ids == (ClaimId("claim-02"),)


class TestHypothesisUncertaintyRule:
    def test_hypothesis_without_uncertainties_rejected(self) -> None:
        with pytest.raises(ValueError):
            ReasoningClaim(
                claim_id=ClaimId("claim-01"),
                claim_type=ClaimType.HYPOTHESIS,
                statement="Possible shared epidemiologic process.",
                supporting_record_refs=(_record_ref(),),
            )

    def test_hypothesis_with_uncertainty_accepted(self) -> None:
        claim = _make_hypothesis()
        assert claim.uncertainties == ("Genomic relatedness is unavailable.",)

    def test_non_hypothesis_without_uncertainties_accepted(self) -> None:
        claim = ReasoningClaim(
            claim_id=ClaimId("claim-01"),
            claim_type=ClaimType.OBSERVED_FACT,
            statement="Three isolates in Ward A.",
            supporting_record_refs=(_record_ref(),),
        )
        assert claim.uncertainties == ()

    def test_multiple_uncertainties_preserved_in_order(self) -> None:
        uncertainties = ("Genomic relatedness is unavailable.", "Ward census is partial.")
        claim = _make_hypothesis(uncertainties=uncertainties)
        assert claim.uncertainties == uncertainties


class TestRequestedActionClassIsDescriptiveOnly:
    def test_a1_requested_class_does_not_authorize(self) -> None:
        claim = _make_hypothesis()
        assert claim.requested_action_class is ActionClass.SAFE_EXTERNAL_COORDINATION
        for authority_field in (
            "authorized",
            "may_execute",
            "policy_passed",
            "autonomy_decision",
        ):
            assert not hasattr(claim, authority_field)

    @pytest.mark.parametrize(
        "requested_class",
        [
            ActionClass.REAL_OPERATIONAL_ESCALATION,
            ActionClass.CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION,
        ],
    )
    def test_a2_a3_requested_class_creates_no_authority(
        self, requested_class: ActionClass
    ) -> None:
        claim = _make_hypothesis(requested_action_class=requested_class)
        assert claim.requested_action_class is requested_class
        for authority_field in (
            "authorized",
            "may_execute",
            "policy_passed",
            "autonomy_decision",
        ):
            assert not hasattr(claim, authority_field)

    def test_action_justification_has_no_executable_authority(self) -> None:
        claim = ReasoningClaim(
            claim_id=ClaimId("claim-05"),
            claim_type=ClaimType.ACTION_JUSTIFICATION,
            statement="A coordination notification would help share the candidate finding.",
            supporting_claim_ids=(ClaimId("claim-01"),),
            requested_action_class=ActionClass.SAFE_EXTERNAL_COORDINATION,
        )
        for authority_field in (
            "authorized",
            "may_execute",
            "policy_passed",
            "autonomy_decision",
        ):
            assert not hasattr(claim, authority_field)


class TestReasoningClaimImmutability:
    def test_claim_is_frozen(self) -> None:
        claim = _make_hypothesis()
        with pytest.raises(FrozenInstanceError):
            claim.statement = "changed"  # type: ignore[misc]

    def test_collection_fields_cannot_be_mutated(self) -> None:
        claim = _make_hypothesis()
        with pytest.raises(AttributeError):
            claim.uncertainties.append("new")  # type: ignore[attr-defined]
        with pytest.raises(AttributeError):
            claim.supporting_record_refs.append(_record_ref())  # type: ignore[attr-defined]
        with pytest.raises(AttributeError):
            claim.supporting_claim_ids.append(ClaimId("claim-99"))  # type: ignore[attr-defined]
        with pytest.raises(FrozenInstanceError):
            claim.uncertainties = ("changed",)  # type: ignore[misc]

    def test_alias_to_source_tuple_cannot_mutate_claim(self) -> None:
        refs = (_record_ref(),)
        claim = ReasoningClaim(
            claim_id=ClaimId("claim-01"),
            claim_type=ClaimType.OBSERVED_FACT,
            statement="Three isolates in Ward A.",
            supporting_record_refs=refs,
        )
        assert claim.supporting_record_refs == (_record_ref(),)
        assert refs == (_record_ref(),)
        # The shared tuple offers no mutating operations and the elements
        # are themselves frozen.
        with pytest.raises(FrozenInstanceError):
            refs[0].record_id = "ISO-999"  # type: ignore[misc]

    def test_claim_is_hashable_and_value_semantic(self) -> None:
        first = _make_hypothesis()
        second = _make_hypothesis()
        assert first == second
        assert first is not second
        assert first != object()
        assert {first: "x"}[second] == "x"
