"""Unit tests for the claim-verification contracts (Issue #29 / M1B.5).

These tests cover the verification RESULT/ERROR/PORT contracts only. No
verification semantics are exercised: the verifier implementation, and any
test asserting how real claims are judged, belongs to the verifier issue.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import get_type_hints

import pytest

from ngabo.application.ports.verify_reasoning_claims import VerifyReasoningClaims
from ngabo.domain.enums.claim_type import ClaimType
from ngabo.domain.enums.verification_error_code import VerificationErrorCode
from ngabo.domain.value_objects.claim_id import ClaimId
from ngabo.domain.value_objects.claim_verification_error import ClaimVerificationError
from ngabo.domain.value_objects.claim_verification_report import ClaimVerificationReport
from ngabo.domain.value_objects.reasoning_claim import ReasoningClaim

EXPECTED_ERROR_CODES = (
    VerificationErrorCode.UNKNOWN_RECORD_REFERENCE,
    VerificationErrorCode.UNKNOWN_FINDING_REFERENCE,
    VerificationErrorCode.UNKNOWN_EVIDENCE_SOURCE,
    VerificationErrorCode.UNSUPPORTED_FACTUAL_ASSERTION,
    VerificationErrorCode.CLAIM_TYPE_EPISTEMIC_MISMATCH,
    VerificationErrorCode.FORBIDDEN_CLAIM_OR_AUTHORITY,
    VerificationErrorCode.STALE_REFERENCE_OR_VERSION,
    VerificationErrorCode.MISSING_UNCERTAINTY,
)


def _error(
    code: VerificationErrorCode = VerificationErrorCode.UNKNOWN_RECORD_REFERENCE,
    claim_id: ClaimId | None = None,
) -> ClaimVerificationError:
    return ClaimVerificationError(code=code, claim_id=claim_id or ClaimId("claim-17"))


class TestVerificationErrorCode:
    @pytest.mark.parametrize("code", EXPECTED_ERROR_CODES)
    def test_stable_value(self, code: VerificationErrorCode) -> None:
        assert code.value == code.name
        assert str(code) == code.name

    def test_exact_minimal_vocabulary(self) -> None:
        assert tuple(VerificationErrorCode) == EXPECTED_ERROR_CODES
        assert len(VerificationErrorCode) == 8

    def test_preserves_governing_document_names(self) -> None:
        # Both names are established verbatim in PROOF_CARRYING_REASONING §7.
        assert (
            VerificationErrorCode.UNKNOWN_FINDING_REFERENCE.value
            == "UNKNOWN_FINDING_REFERENCE"
        )
        assert (
            VerificationErrorCode.UNSUPPORTED_FACTUAL_ASSERTION.value
            == "UNSUPPORTED_FACTUAL_ASSERTION"
        )


class TestClaimVerificationError:
    def test_full_construction_preserves_fields(self) -> None:
        claim_id = ClaimId("claim-17")
        error = ClaimVerificationError(
            code=VerificationErrorCode.UNKNOWN_FINDING_REFERENCE,
            claim_id=claim_id,
            reference="finding-9",
            field="supporting_finding_refs",
            detail="Finding 9 is not a deterministic result of this incident.",
        )
        assert error.code is VerificationErrorCode.UNKNOWN_FINDING_REFERENCE
        assert error.claim_id is claim_id
        assert error.reference == "finding-9"
        assert error.field == "supporting_finding_refs"
        assert error.detail == "Finding 9 is not a deterministic result of this incident."

    def test_minimal_construction_allows_none_optionals(self) -> None:
        error = _error()
        assert error.reference is None
        assert error.field is None
        assert error.detail is None

    def test_rejects_raw_string_code(self) -> None:
        # StrEnum members compare equal to their string values, so this
        # isinstance guard is load-bearing for the error identity.
        with pytest.raises(ValueError):
            ClaimVerificationError(
                code="UNKNOWN_FINDING_REFERENCE",  # type: ignore[arg-type]
                claim_id=ClaimId("claim-17"),
            )

    def test_rejects_raw_string_claim_id(self) -> None:
        with pytest.raises(ValueError):
            ClaimVerificationError(
                code=VerificationErrorCode.UNKNOWN_RECORD_REFERENCE,
                claim_id="claim-17",  # type: ignore[arg-type]
            )

    def test_rejects_unrelated_enum_as_code(self) -> None:
        with pytest.raises(ValueError):
            ClaimVerificationError(
                code=ClaimType.HYPOTHESIS,  # type: ignore[arg-type]
                claim_id=ClaimId("claim-17"),
            )

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_rejects_blank_optional_strings(self, blank: str) -> None:
        claim_id = ClaimId("claim-17")
        with pytest.raises(ValueError):
            ClaimVerificationError(
                code=VerificationErrorCode.MISSING_UNCERTAINTY,
                claim_id=claim_id,
                reference=blank,
            )
        with pytest.raises(ValueError):
            ClaimVerificationError(
                code=VerificationErrorCode.MISSING_UNCERTAINTY,
                claim_id=claim_id,
                field=blank,
            )
        with pytest.raises(ValueError):
            ClaimVerificationError(
                code=VerificationErrorCode.MISSING_UNCERTAINTY,
                claim_id=claim_id,
                detail=blank,
            )

    def test_frozen_rejects_reassignment(self) -> None:
        error = _error()
        with pytest.raises(FrozenInstanceError):
            error.code = VerificationErrorCode.STALE_REFERENCE_OR_VERSION  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            error.reference = "finding-9"  # type: ignore[misc]

    def test_value_equality(self) -> None:
        first = ClaimVerificationError(
            code=VerificationErrorCode.UNKNOWN_RECORD_REFERENCE,
            claim_id=ClaimId("claim-17"),
            detail="No such record.",
        )
        same = ClaimVerificationError(
            code=VerificationErrorCode.UNKNOWN_RECORD_REFERENCE,
            claim_id=ClaimId("claim-17"),
            detail="No such record.",
        )
        different = ClaimVerificationError(
            code=VerificationErrorCode.UNKNOWN_RECORD_REFERENCE,
            claim_id=ClaimId("claim-17"),
            detail="Different.",
        )
        assert first == same
        assert hash(first) == hash(same)
        assert first != different

    def test_error_carries_no_authorization_fields(self) -> None:
        # Mirror of the #28 descriptive-only guard: a verification error
        # never authorizes or blocks action by itself.
        error = _error()
        assert not hasattr(error, "authorized")
        assert not hasattr(error, "may_execute")
        assert not hasattr(error, "policy_passed")
        assert not hasattr(error, "autonomy_decision")


class TestClaimVerificationReport:
    def test_pass_report_has_no_errors(self) -> None:
        report = ClaimVerificationReport(valid=True)
        assert report.valid is True
        assert report.errors == ()

    def test_fail_report_carries_errors(self) -> None:
        error = _error()
        report = ClaimVerificationReport(valid=False, errors=(error,))
        assert report.valid is False
        assert report.errors == (error,)

    def test_fail_report_preserves_multiple_errors_in_order(self) -> None:
        first = _error(code=VerificationErrorCode.UNKNOWN_RECORD_REFERENCE)
        second = _error(
            code=VerificationErrorCode.UNSUPPORTED_FACTUAL_ASSERTION,
            claim_id=ClaimId("claim-18"),
        )
        report = ClaimVerificationReport(valid=False, errors=(first, second))
        assert report.errors == (first, second)

    def test_valid_report_rejects_errors(self) -> None:
        with pytest.raises(ValueError):
            ClaimVerificationReport(valid=True, errors=(_error(),))

    def test_invalid_report_rejects_empty_errors(self) -> None:
        with pytest.raises(ValueError):
            ClaimVerificationReport(valid=False)

    @pytest.mark.parametrize("non_bool", [1, 0, "yes", None])
    def test_rejects_non_bool_valid(self, non_bool: object) -> None:
        # bool subclasses int, so this isinstance guard is load-bearing:
        # raw truthy/falsy values must never construct a report.
        with pytest.raises(ValueError):
            ClaimVerificationReport(
                valid=non_bool,  # type: ignore[arg-type]
            )

    def test_rejects_list_errors_fail_closed(self) -> None:
        # No normalization: a list is rejected, never silently converted.
        with pytest.raises(ValueError):
            ClaimVerificationReport(
                valid=False, errors=[_error()]  # type: ignore[arg-type]
            )

    def test_mutable_list_alias_never_reaches_report(self) -> None:
        errors = [_error()]
        with pytest.raises(ValueError):
            ClaimVerificationReport(
                valid=False, errors=errors  # type: ignore[arg-type]
            )
        errors.append(
            _error(
                code=VerificationErrorCode.MISSING_UNCERTAINTY,
                claim_id=ClaimId("claim-19"),
            )
        )
        with pytest.raises(ValueError):
            ClaimVerificationReport(
                valid=False, errors=errors  # type: ignore[arg-type]
            )

    @pytest.mark.parametrize(
        "element",
        ["UNKNOWN_FINDING_REFERENCE", ClaimId("claim-17")],
    )
    def test_rejects_wrong_error_element_types(self, element: object) -> None:
        with pytest.raises(ValueError):
            ClaimVerificationReport(
                valid=False,
                errors=(element,),  # type: ignore[arg-type]
            )

    def test_frozen_rejects_reassignment(self) -> None:
        report = ClaimVerificationReport(valid=False, errors=(_error(),))
        with pytest.raises(FrozenInstanceError):
            report.valid = True  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            report.errors = ()  # type: ignore[misc]

    def test_value_equality(self) -> None:
        error = _error()
        first = ClaimVerificationReport(valid=False, errors=(error,))
        same = ClaimVerificationReport(valid=False, errors=(error,))
        assert first == same
        assert hash(first) == hash(same)
        assert first != ClaimVerificationReport(valid=True)


class TestVerifyReasoningClaimsPort:
    def test_port_is_a_runtime_checkable_protocol(self) -> None:
        # Protocol/`_is_runtime_protocol` are the CPython runtime markers of
        # @runtime_checkable Protocols (mypy rejects issubclass() against the
        # Protocol special form, so assert the attributes directly).
        assert getattr(VerifyReasoningClaims, "_is_protocol", False) is True
        assert getattr(VerifyReasoningClaims, "_is_runtime_protocol", False) is True

    def test_port_signature_contract(self) -> None:
        hints = get_type_hints(VerifyReasoningClaims.__call__)
        assert hints["claims"] == tuple[ReasoningClaim, ...]
        assert hints["return"] is ClaimVerificationReport

    def test_conforming_verifier_satisfies_port(self) -> None:
        class _StubVerifier:
            def __call__(
                self, claims: tuple[ReasoningClaim, ...]
            ) -> ClaimVerificationReport:
                return ClaimVerificationReport(valid=True)

        verifier = _StubVerifier()
        assert isinstance(verifier, VerifyReasoningClaims)
        report = verifier(())
        assert isinstance(report, ClaimVerificationReport)
        assert report.valid is True

    def test_non_conforming_verifier_fails_port(self) -> None:
        class _NotAVerifier:
            def something_else(self) -> None:
                return None

        candidate: object = _NotAVerifier()
        assert not isinstance(candidate, VerifyReasoningClaims)
