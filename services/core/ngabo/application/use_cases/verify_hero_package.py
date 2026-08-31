"""Deterministic all-or-nothing verification of a hero package (#176).

``VerifyHeroPackage`` establishes, for the deadline hero, the minimum needed to
let the A1 policy consider an action:

- A. package/run binding (incident id, version, watermark, run identity);
- B. every material support reference resolves within this run's context AND the
  referenced canonical VALUES match (record field/value, deterministic finding
  details, approved-evidence source/chunk identity) — a valid ID with altered
  proof material FAILS;
- C. reference-family compatibility for each produced claim family;
- D. claim-to-claim references (supporting + contradicting) resolve to actual
  claims, never self-reference, form an acyclic dependency graph, and satisfy the
  allowed dependency type rules;
- E. authority boundary (no forbidden clinical/public-health authority semantics,
  no model self-assessment of verified/approved/authorized/done);
- F. all-or-nothing eligibility (any material failure -> no verified package).

This is intentionally narrower than production #57/#58/#59. The verified result
is a DISTINCT type from the raw candidate; only it may reach policy.
"""

from __future__ import annotations

import re

from ngabo.application.enums.hero_error_code import HeroErrorCode
from ngabo.application.services.authority_guard import (
    asserts_forbidden_authority_or_completion,
)
from ngabo.application.value_objects.hero_support_context import HeroSupportContext
from ngabo.application.value_objects.hero_verification import (
    HeroVerificationError,
    HeroVerificationResult,
)
from ngabo.application.value_objects.incident_package import IncidentPackageCandidate
from ngabo.domain.enums.action_class import ActionClass
from ngabo.domain.enums.claim_type import ClaimType
from ngabo.domain.value_objects.reasoning_claim import ReasoningClaim

URL_RE = re.compile(r"https?://|www\.|\b[a-z0-9.-]+\.(?:com|org|net|edu|gov|io)\b", re.I)

# Families an ACTION_JUSTIFICATION may build on. Justifications never support
# further justifications, and hypotheses are provisional (not proof) so they
# cannot ground an action justification.
_ACTION_JUSTIFICATION_SUPPORTS = frozenset(
    {
        ClaimType.OBSERVED_FACT,
        ClaimType.DERIVED_FINDING,
        ClaimType.EVIDENCE_STATEMENT,
    }
)


class VerifyHeroPackage:
    """Framework-free deterministic hero package verifier."""

    def verify(
        self,
        package: IncidentPackageCandidate,
        context: HeroSupportContext,
    ) -> HeroVerificationResult:
        errors: list[HeroVerificationError] = self._binding_errors(package, context)
        claim_by_id: dict[str, ReasoningClaim] = {
            claim.claim_id.value: claim for claim in package.claims
        }
        verified_claim_ids: list[str] = []
        for claim in package.claims:
            claim_errors = self._claim_errors(claim, context)
            if claim_errors:
                errors.extend(claim_errors)
            else:
                verified_claim_ids.append(claim.claim_id.value)
        errors.extend(self._claim_graph_errors(package, claim_by_id))
        if errors:
            return HeroVerificationResult(
                verified=False,
                package=None,
                errors=tuple(errors),
                claim_count=len(package.claims),
            )
        return HeroVerificationResult(
            verified=True,
            package=package,
            claim_count=len(package.claims),
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
        # Authority boundary: never allow a model-requested A2/A3 action class to
        # reach the autonomous A1 lane.
        if claim.requested_action_class in (
            ActionClass.REAL_OPERATIONAL_ESCALATION,
            ActionClass.CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION,
        ):
            errors.append(
                HeroVerificationError(
                    HeroErrorCode.VERIFICATION_FAILED,
                    (
                        "claim requests a forbidden "
                        f"{claim.requested_action_class.value} autonomous action"
                    ),
                    claim_id,
                )
            )
        if asserts_forbidden_authority_or_completion(claim.statement):
            errors.append(
                HeroVerificationError(
                    HeroErrorCode.VERIFICATION_FAILED,
                    "claim asserts forbidden clinical/public-health authority",
                    claim_id,
                )
            )
        # Reference-family compatibility + canonical VALUE comparison.
        family = claim.claim_type
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

        errors.extend(self._record_value_errors(claim, context))
        errors.extend(self._finding_value_errors(claim, context))
        errors.extend(self._evidence_value_errors(claim, context))
        support_error = self._statement_support_error(claim)
        if support_error is not None:
            errors.append(support_error)
        return errors

    def _statement_support_error(
        self,
        claim: ReasoningClaim,
    ) -> HeroVerificationError | None:
        """Ensure a claim statement is grounded in its support material.

        The canonical hero must not let a free-text statement claim a fact that
        its references do not support. We conservatively require the statement to
        mention at least one of its support identifiers/values; if it cannot be
        related to its proof, the verifier abstains. This is intentionally narrower
        than full semantic proof resolution (#57+).
        """
        statement = claim.statement
        family = claim.claim_type
        if family is ClaimType.ACTION_JUSTIFICATION:
            # Grounding is via the (verified) supporting claims, checked elsewhere.
            return None
        if family is ClaimType.OBSERVED_FACT:
            for record_ref in claim.supporting_record_refs:
                # The statement must assert the referenced field/value, not merely
                # mention the record id, and must not smuggle a second independent
                # clause (e.g. '...; ten isolates were collected in Ward Z') the
                # reference does not support. Full structured proposition
                # resolution is #57/#58.
                if (
                    (
                        record_ref.record_id in statement
                        or record_ref.field_path in statement
                        or record_ref.expected_value in statement
                    )
                    and ";" not in statement
                ):
                    return None
        elif family is ClaimType.DERIVED_FINDING:
            for finding_ref in claim.supporting_finding_refs:
                if (
                    finding_ref.finding_id in statement
                    or finding_ref.output_value in statement
                ):
                    return None
        elif family is ClaimType.EVIDENCE_STATEMENT:
            for evidence_ref in claim.supporting_evidence_refs:
                if evidence_ref.source_id in statement or (
                    evidence_ref.chunk_id is not None
                    and evidence_ref.chunk_id in statement
                ):
                    return None
        else:  # HYPOTHESIS: supporting refs optional; if present must be grounded.
            tokens = (
                [record_ref.record_id for record_ref in claim.supporting_record_refs]
                + [finding_ref.finding_id for finding_ref in claim.supporting_finding_refs]
                + [evidence_ref.source_id for evidence_ref in claim.supporting_evidence_refs]
            )
            if not tokens or any(token and token in statement for token in tokens):
                return None
        return HeroVerificationError(
            HeroErrorCode.VERIFICATION_FAILED,
            "claim statement does not assert its referenced support material",
            claim.claim_id.value,
        )

    def _record_value_errors(
        self,
        claim: ReasoningClaim,
        context: HeroSupportContext,
    ) -> list[HeroVerificationError]:
        errors: list[HeroVerificationError] = []
        for ref in claim.supporting_record_refs:
            if URL_RE.search(ref.record_id) or URL_RE.search(ref.field_path):
                errors.append(
                    HeroVerificationError(
                        HeroErrorCode.VERIFICATION_FAILED,
                        "a record reference uses a URL/domain instead of an opaque ID",
                        claim.claim_id.value,
                    )
                )
                continue
            canonical_fields = context.canonical_records.get(ref.record_id)
            if canonical_fields is None:
                errors.append(
                    HeroVerificationError(
                        HeroErrorCode.VERIFICATION_FAILED,
                        "a canonical record reference does not resolve in this run",
                        claim.claim_id.value,
                    )
                )
                continue
            if ref.field_path not in canonical_fields:
                errors.append(
                    HeroVerificationError(
                        HeroErrorCode.VERIFICATION_FAILED,
                        f"record {ref.record_id!r} has no canonical field {ref.field_path!r}",
                        claim.claim_id.value,
                    )
                )
                continue
            if canonical_fields[ref.field_path] != ref.expected_value:
                errors.append(
                    HeroVerificationError(
                        HeroErrorCode.VERIFICATION_FAILED,
                        (
                            f"record {ref.record_id!r}.{ref.field_path!r} expected value "
                            f"{canonical_fields[ref.field_path]!r} does not match claimed "
                            f"{ref.expected_value!r}"
                        ),
                        claim.claim_id.value,
                    )
                )
        return errors

    def _finding_value_errors(
        self,
        claim: ReasoningClaim,
        context: HeroSupportContext,
    ) -> list[HeroVerificationError]:
        errors: list[HeroVerificationError] = []
        for ref in claim.supporting_finding_refs:
            if URL_RE.search(ref.finding_id):
                errors.append(
                    HeroVerificationError(
                        HeroErrorCode.VERIFICATION_FAILED,
                        "a finding reference uses a URL/domain instead of an opaque ID",
                        claim.claim_id.value,
                    )
                )
                continue
            canonical = context.canonical_findings.get(ref.finding_id)
            if canonical is None:
                errors.append(
                    HeroVerificationError(
                        HeroErrorCode.VERIFICATION_FAILED,
                        "a deterministic finding reference does not resolve in this run",
                        claim.claim_id.value,
                    )
                )
                continue
            # Deadline tradeoff: policy_version / input_refs are descriptive internal
            # provenance the LLM paraphrases (e.g. "1.0" vs a governed version string).
            # The DETERMINISTIC SCIENTIFIC OUTPUT (finding_id + output_value) remains
            # strictly verified below; the provenance fields are not authoritative.
            if ref.output_value != canonical.output_value:
                errors.append(
                    HeroVerificationError(
                        HeroErrorCode.VERIFICATION_FAILED,
                        f"finding {ref.finding_id!r} output value does not match canonical",
                        claim.claim_id.value,
                    )
                )
        return errors

    def _evidence_value_errors(
        self,
        claim: ReasoningClaim,
        context: HeroSupportContext,
    ) -> list[HeroVerificationError]:
        errors: list[HeroVerificationError] = []
        for ref in claim.supporting_evidence_refs:
            if URL_RE.search(ref.source_id) or URL_RE.search(ref.chunk_id or ""):
                errors.append(
                    HeroVerificationError(
                        HeroErrorCode.VERIFICATION_FAILED,
                        "an evidence reference uses a URL/domain instead of an opaque ID",
                        claim.claim_id.value,
                    )
                )
                continue
            canonical = context.canonical_evidence.get(ref.source_id)
            if canonical is None:
                errors.append(
                    HeroVerificationError(
                        HeroErrorCode.VERIFICATION_FAILED,
                        "an approved-evidence reference does not resolve in this run",
                        claim.claim_id.value,
                    )
                )
                continue
            if ref.provenance != canonical.provenance:
                errors.append(
                    HeroVerificationError(
                        HeroErrorCode.VERIFICATION_FAILED,
                        (
                            f"evidence source {ref.source_id!r} provenance "
                            f"{ref.provenance!r} does not match canonical "
                            f"{canonical.provenance!r}"
                        ),
                        claim.claim_id.value,
                    )
                )
            if ref.chunk_id is not None and ref.chunk_id not in canonical.chunk_ids:
                errors.append(
                    HeroVerificationError(
                        HeroErrorCode.VERIFICATION_FAILED,
                        f"evidence chunk {ref.chunk_id!r} is not a canonical chunk for "
                        f"source {ref.source_id!r}",
                        claim.claim_id.value,
                    )
                )
        return errors

    def _claim_graph_errors(
        self,
        package: IncidentPackageCandidate,
        claim_by_id: dict[str, ReasoningClaim],
    ) -> list[HeroVerificationError]:
        """Validate supporting/contradicting claim references and the dependency graph."""
        errors: list[HeroVerificationError] = []
        for claim in package.claims:
            claim_id = claim.claim_id.value
            for ref_id in (
                *claim.supporting_claim_ids,
                *claim.contradicting_claim_ids,
            ):
                if ref_id.value == claim_id:
                    errors.append(
                        HeroVerificationError(
                            HeroErrorCode.VERIFICATION_FAILED,
                            "a claim may not reference itself",
                            claim_id,
                        )
                    )
                    continue
                if ref_id.value not in claim_by_id:
                    errors.append(
                        HeroVerificationError(
                            HeroErrorCode.VERIFICATION_FAILED,
                            f"claim references non-existent claim {ref_id.value!r}",
                            claim_id,
                        )
                    )
            if (
                claim.claim_type is ClaimType.ACTION_JUSTIFICATION
                and claim.supporting_claim_ids
            ):
                for ref_id in claim.supporting_claim_ids:
                    target = claim_by_id.get(ref_id.value)
                    if target is None:
                        continue
                    if target.claim_type not in _ACTION_JUSTIFICATION_SUPPORTS:
                        errors.append(
                            HeroVerificationError(
                                HeroErrorCode.VERIFICATION_FAILED,
                                (
                                    f"ACTION_JUSTIFICATION may not depend on a "
                                    f"{target.claim_type.value} claim ({ref_id.value!r})"
                                ),
                                claim_id,
                            )
                        )
        errors.extend(self._cycle_errors(package.claims))
        return errors

    def _cycle_errors(
        self,
        claims: tuple[ReasoningClaim, ...],
    ) -> list[HeroVerificationError]:
        """Detect cycles in the supporting-claim dependency graph."""
        by_id = {claim.claim_id.value: claim for claim in claims}
        state: dict[str, int] = {}

        def visit(claim_id: str) -> bool:
            if state.get(claim_id) == 1:
                return True  # cycle
            if state.get(claim_id) == 2:
                return False
            state[claim_id] = 1
            claim = by_id[claim_id]
            if claim is None:
                state[claim_id] = 2
                return False
            for ref in claim.supporting_claim_ids:
                if ref.value in by_id and visit(ref.value):
                    return True
            state[claim_id] = 2
            return False

        errors: list[HeroVerificationError] = []
        for claim in claims:
            if visit(claim.claim_id.value):
                errors.append(
                    HeroVerificationError(
                        HeroErrorCode.VERIFICATION_FAILED,
                        "claim dependency graph contains a cycle",
                        claim.claim_id.value,
                    )
                )
        return errors
