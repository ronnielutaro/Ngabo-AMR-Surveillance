"""Deterministic all-or-nothing verification of a hero package (#176).

``VerifyHeroPackage`` establishes, for the deadline hero, the minimum needed to
let the A1 policy consider an action:

- A. package/run binding (incident id, version, watermark, run identity);
- B. every material support reference resolves within this run's context;
- C. reference-family compatibility for each produced claim family;
- D. authority boundary (no forbidden clinical/public-health semantics, no model
  self-assessment of verified/approved/authorized/done);
- E. all-or-nothing eligibility (any material failure -> no verified package).

This is intentionally narrower than production #57/#58/#59. The verified result
is a DISTINCT type from the raw candidate; only it may reach policy.
"""

from __future__ import annotations

import re

from ngabo.application.enums.hero_error_code import HeroErrorCode
from ngabo.application.value_objects.hero_support_context import HeroSupportContext
from ngabo.application.value_objects.hero_verification import (
    HeroVerificationError,
    HeroVerificationResult,
)
from ngabo.application.value_objects.incident_package import IncidentPackageCandidate
from ngabo.domain.enums.claim_type import ClaimType
from ngabo.domain.value_objects.reasoning_claim import ReasoningClaim

URL_RE = re.compile(r"https?://|www\.|\b[a-z0-9.-]+\.(?:com|org|net|edu|gov|io)\b", re.I)

FORBIDDEN_AUTHORITY_TOKENS = (
    "VERIFIED",
    "APPROVED",
    "APPROVE",
    "AUTHORIZED",
    "AUTHORIZE",
    "ACTION_READY",
    "AUTO_EXECUTE_A1",
    "OUTBREAK_CONFIRMED",
    "DIAGNOSIS",
    "PRESCRIPTION",
    "MANDATORY_CONTAINMENT",
    "OFFICIAL_PUBLIC_HEALTH_DECLARATION",
    "PACKAGE_COMPLETED",
    "INVESTIGATION_COMPLETE",
    "DELIVERED",
    "ACKNOWLEDGED",
    "NO_ACTION_NEEDED",
    "ESCALATE",
)
_FORBIDDEN_AUTHORITY_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(tok) for tok in FORBIDDEN_AUTHORITY_TOKENS) + r")\b",
    re.I,
)


class VerifyHeroPackage:
    """Framework-free deterministic hero package verifier."""

    def verify(
        self,
        package: IncidentPackageCandidate,
        context: HeroSupportContext,
    ) -> HeroVerificationResult:
        errors: list[HeroVerificationError] = self._binding_errors(package, context)
        claim_ids: list[str] = []
        verified_claim_ids: list[str] = []
        for claim in package.claims:
            claim_ids.append(claim.claim_id.value)
            claim_errors = self._claim_errors(claim, context)
            if claim_errors:
                errors.extend(claim_errors)
            else:
                verified_claim_ids.append(claim.claim_id.value)
        if errors:
            return HeroVerificationResult(
                verified=False,
                package=None,
                errors=tuple(errors),
                claim_count=len(claim_ids),
            )
        return HeroVerificationResult(
            verified=True,
            package=package,
            claim_count=len(claim_ids),
            verified_claim_ids=tuple(verified_claim_ids),
        )

    def _binding_errors(
        self,
        package: IncidentPackageCandidate,
        context: HeroSupportContext,
    ) -> list[HeroVerificationError]:
        errors: list[HeroVerificationError] = []
        if package.incident_id.value != context.incident_id.value:
            errors.append(
                HeroVerificationError(
                    HeroErrorCode.STALE_VERSION_BINDING,
                    "package incident_id does not match the current incident",
                )
            )
        if package.incident_version.value != context.incident_version.value:
            errors.append(
                HeroVerificationError(
                    HeroErrorCode.STALE_VERSION_BINDING,
                    "package incident_version is not the current version",
                )
            )
        if package.source_watermark.value != context.source_watermark.value:
            errors.append(
                HeroVerificationError(
                    HeroErrorCode.RUN_BINDING_MISMATCH,
                    "package source watermark does not match the current run",
                )
            )
        generation_run_id = package.metadata.generation_run_id
        if generation_run_id is not None and generation_run_id != context.execution_id:
            errors.append(
                HeroVerificationError(
                    HeroErrorCode.RUN_BINDING_MISMATCH,
                    "package generation_run_id does not match the current run",
                )
            )
        return errors

    def _claim_errors(
        self,
        claim: ReasoningClaim,
        context: HeroSupportContext,
    ) -> list[HeroVerificationError]:
        errors: list[HeroVerificationError] = []
        claim_id = claim.claim_id.value
        # Authority boundary: reject forbidden semantics in narrative text ahead
        # of verifying references. The claim type allow-list already excludes
        # diagnosis/prescription/outbreak-confirmation families.
        if _FORBIDDEN_AUTHORITY_RE.search(claim.statement):
            errors.append(
                HeroVerificationError(
                    HeroErrorCode.VERIFICATION_FAILED,
                    "claim asserts forbidden clinical/public-health authority",
                    claim_id,
                )
            )

        # Reference-family compatibility.
        family = claim.claim_type
        record_ok = all(
            r.record_id in context.record_ids for r in claim.supporting_record_refs
        )
        finding_ok = all(
            f.finding_id in context.finding_ids for f in claim.supporting_finding_refs
        )
        evidence_ok = all(
            e.source_id in context.evidence_source_ids
            and (e.chunk_id is None or e.chunk_id in context.evidence_reference_ids)
            for e in claim.supporting_evidence_refs
        )
        if not record_ok:
            errors.append(
                HeroVerificationError(
                    HeroErrorCode.VERIFICATION_FAILED,
                    "a canonical record reference does not resolve in this run",
                    claim_id,
                )
            )
        if not finding_ok:
            errors.append(
                HeroVerificationError(
                    HeroErrorCode.VERIFICATION_FAILED,
                    "a deterministic finding reference does not resolve in this run",
                    claim_id,
                )
            )
        if not evidence_ok:
            errors.append(
                HeroVerificationError(
                    HeroErrorCode.VERIFICATION_FAILED,
                    "an approved-evidence reference does not resolve in this run",
                    claim_id,
                )
            )
        for ref in (
            *claim.supporting_record_refs,
            *claim.supporting_finding_refs,
            *claim.supporting_evidence_refs,
        ):
            text = _ref_text(ref)
            if URL_RE.search(text):
                errors.append(
                    HeroVerificationError(
                        HeroErrorCode.VERIFICATION_FAILED,
                        "a support reference uses a URL/domain instead of an opaque ID",
                        claim_id,
                    )
                )

        # Family-typed support requirement.
        if family is ClaimType.OBSERVED_FACT and not claim.supporting_record_refs:
            errors.append(
                HeroVerificationError(
                    HeroErrorCode.VERIFICATION_FAILED,
                    "an OBSERVED_FACT requires canonical record support",
                    claim_id,
                )
            )
        if family is ClaimType.DERIVED_FINDING and not claim.supporting_finding_refs:
            errors.append(
                HeroVerificationError(
                    HeroErrorCode.VERIFICATION_FAILED,
                    "a DERIVED_FINDING requires deterministic finding support",
                    claim_id,
                )
            )
        if family is ClaimType.EVIDENCE_STATEMENT and not claim.supporting_evidence_refs:
            errors.append(
                HeroVerificationError(
                    HeroErrorCode.VERIFICATION_FAILED,
                    "an EVIDENCE_STATEMENT requires approved-evidence support",
                    claim_id,
                )
            )
        if family is ClaimType.HYPOTHESIS:
            if not claim.uncertainties:
                errors.append(
                    HeroVerificationError(
                        HeroErrorCode.VERIFICATION_FAILED,
                        "a HYPOTHESIS requires explicit uncertainty",
                        claim_id,
                    )
                )
            if not (
                claim.supporting_record_refs
                or claim.supporting_finding_refs
                or claim.supporting_evidence_refs
            ):
                errors.append(
                    HeroVerificationError(
                        HeroErrorCode.VERIFICATION_FAILED,
                        "a HYPOTHESIS requires supporting material",
                        claim_id,
                    )
                )
        if family is ClaimType.ACTION_JUSTIFICATION and not claim.supporting_claim_ids:
            errors.append(
                HeroVerificationError(
                    HeroErrorCode.VERIFICATION_FAILED,
                    "an ACTION_JUSTIFICATION must reference verified upstream claims",
                    claim_id,
                )
            )
        return errors


def _ref_text(ref: object) -> str:
    """Serialize a support reference to text for the URL guard."""
    parts = [str(getattr(ref, "record_id", "")), str(getattr(ref, "finding_id", ""))]
    if hasattr(ref, "field_path"):
        parts.append(str(ref.field_path))
    if hasattr(ref, "policy_version"):
        parts.append(str(ref.policy_version))
    if hasattr(ref, "source_id"):
        parts.append(str(ref.source_id))
    if hasattr(ref, "chunk_id") and ref.chunk_id is not None:
        parts.append(str(ref.chunk_id))
    if hasattr(ref, "expected_value"):
        parts.append(str(ref.expected_value))
    if hasattr(ref, "output_value"):
        parts.append(str(ref.output_value))
    return " ".join(parts)
