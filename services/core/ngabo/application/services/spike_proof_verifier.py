"""Deterministic proof verifier for the ADK/Gemini capability spike (#49).

This is the executable proof that model output is NOT self-authenticating. It
is ordinary framework-free application code: it receives a proposed
``SpikeProofClaim`` plus the deterministic branch results and decides, from a
known-reference context, whether the claim may continue. The Gemini model
never answers "is your evidence valid?" — a deterministic set check does.

Checks performed (in order, fail-closed):
1. Every required deterministic parallel branch produced valid output; any
   missing/failed required branch yields ``REQUIRED_BRANCH_FAILED`` before
   synthesis can be trusted.
2. The proposed claim exists and is structurally usable; otherwise
   ``MALFORMED_PROOF``.
3. Every referenced record/finding/source ID exists in the verification
   context; any unknown reference yields its ``UNKNOWN_*_REFERENCE`` family.

The verifier does NOT judge the *truth* of the statement; it judges only
referential integrity and required-input completeness, which is the
deterministic accept/reject boundary that must exist before any downstream
routing.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ngabo.application.enums.spike_verification_code import SpikeVerificationCode
from ngabo.application.value_objects.spike_verification_result import (
    SpikeVerificationError,
    SpikeVerificationResult,
)
from ngabo.domain.value_objects.spike_proof_claim import SpikeProofClaim

REQUIRED_BRANCHES: Final[tuple[str, str]] = ("branch_a", "branch_b")


@dataclass(frozen=True)
class BranchResult:
    """Deterministic output of one parallel branch in the spike graph."""

    branch_name: str
    ok: bool
    finding_id: str | None = None
    output_value: str | None = None
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.branch_name, str) or not self.branch_name.strip():
            raise ValueError("branch_name must be a non-blank string")
        if not isinstance(self.ok, bool):
            raise ValueError("ok must be a bool")
        if self.finding_id is not None and (
            not isinstance(self.finding_id, str) or not self.finding_id.strip()
        ):
            raise ValueError("finding_id must be non-blank text or None")
        if self.output_value is not None and (
            not isinstance(self.output_value, str) or not self.output_value.strip()
        ):
            raise ValueError("output_value must be non-blank text or None")


@dataclass(frozen=True)
class VerificationContext:
    """Known-reference IDs against which proposed claims are checked."""

    known_record_ids: frozenset[str]
    known_finding_ids: frozenset[str]
    known_source_ids: frozenset[str]

    def __post_init__(self) -> None:
        for label, values in (
            ("known_record_ids", self.known_record_ids),
            ("known_finding_ids", self.known_finding_ids),
            ("known_source_ids", self.known_source_ids),
        ):
            if not isinstance(values, frozenset):
                raise ValueError(f"{label} must be a frozenset")


def _error(
    code: SpikeVerificationCode,
    *,
    reference: str | None = None,
    field: str | None = None,
    detail: str | None = None,
) -> SpikeVerificationError:
    return SpikeVerificationError(
        code=code,
        reference=reference,
        field=field,
        detail=detail,
    )


class SpikeProofVerifier:
    """Deterministic, fail-closed verification of a proposed spike claim."""

    def __init__(self, context: VerificationContext) -> None:
        if not isinstance(context, VerificationContext):
            raise TypeError("context must be a VerificationContext")
        self._context = context

    def verify(
        self,
        claim: SpikeProofClaim | None,
        branches: Sequence[BranchResult] | None,
    ) -> SpikeVerificationResult:
        """Return the aggregate pass/fail decision for one proposed claim."""
        branch_map = {branch.branch_name: branch for branch in (branches or ())}
        missing_branch = next(
            (
                name
                for name in REQUIRED_BRANCHES
                if branch_map.get(name) is None or not branch_map[name].ok
            ),
            None,
        )
        if missing_branch is not None:
            branch = branch_map.get(missing_branch)
            return SpikeVerificationResult(
                valid=False,
                errors=(
                    _error(
                        SpikeVerificationCode.REQUIRED_BRANCH_FAILED,
                        field=missing_branch,
                        detail=branch.failure_reason
                        if branch is not None and branch.failure_reason
                        else f"Required branch {missing_branch} did not produce valid output",
                    ),
                ),
            )

        if claim is None:
            return SpikeVerificationResult(
                valid=False,
                errors=(
                    _error(
                        SpikeVerificationCode.MALFORMED_PROOF,
                        field="claim",
                        detail="No structured proof claim was produced",
                    ),
                ),
            )

        errors: list[SpikeVerificationError] = []
        for record_id in claim.supporting_record_ids:
            if record_id not in self._context.known_record_ids:
                errors.append(
                    _error(
                        SpikeVerificationCode.UNKNOWN_RECORD_REFERENCE,
                        reference=record_id,
                        field="supporting_record_ids",
                    )
                )
        for finding_id in claim.supporting_finding_ids:
            if finding_id not in self._context.known_finding_ids:
                errors.append(
                    _error(
                        SpikeVerificationCode.UNKNOWN_FINDING_REFERENCE,
                        reference=finding_id,
                        field="supporting_finding_ids",
                    )
                )
        for source_id in claim.supporting_source_ids:
            if source_id not in self._context.known_source_ids:
                errors.append(
                    _error(
                        SpikeVerificationCode.UNKNOWN_SOURCE_REFERENCE,
                        reference=source_id,
                        field="supporting_source_ids",
                    )
                )

        if errors:
            return SpikeVerificationResult(valid=False, errors=tuple(errors))
        return SpikeVerificationResult(valid=True)
