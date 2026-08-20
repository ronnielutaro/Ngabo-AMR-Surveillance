"""Aggregate claim-verification result contract (M1B.5 / Issue #29).

``ClaimVerificationReport`` is the immutable result the deterministic claim
verifier returns through the inward ``VerifyReasoningClaims`` application
port. Shape per Issue #29 and ``docs/PROOF_CARRYING_REASONING.md`` §7:
``valid`` plus zero-or-more per-claim errors, with the hard invariants that
a valid report carries no errors and an invalid report carries at least one.

Authority boundary: this report says only whether claim verification
passed. It does NOT mean ActionPolicy passed, freshness passed, an
ActionIntent exists, A1 is authorized, or external execution may begin —
and it deliberately contains no AutonomyDecision, authorization, repair,
package or persistence fields.

Deeply immutable: ``errors`` must be an actual tuple of
``ClaimVerificationError`` — non-tuple collections and wrong element types
are rejected at construction, so no mutable alias can reach the report.
"""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.domain.value_objects.claim_verification_error import ClaimVerificationError


@dataclass(frozen=True)
class ClaimVerificationReport:
    """Immutable pass/fail result of deterministic claim verification."""

    valid: bool
    errors: tuple[ClaimVerificationError, ...] = ()

    def __post_init__(self) -> None:
        # bool subclasses int, so the type must be guarded with isinstance
        # rather than a truthiness check: raw 1/0 must never construct.
        if not isinstance(self.valid, bool):
            raise ValueError(f"Invalid verification result {self.valid!r}; expected a bool")
        if not isinstance(self.errors, tuple):
            raise ValueError(f"Invalid verification errors {self.errors!r}; expected a tuple")
        for index, error in enumerate(self.errors):
            if not isinstance(error, ClaimVerificationError):
                raise ValueError(
                    f"Invalid verification error at position {index}: {error!r}; "
                    "expected a ClaimVerificationError"
                )
        if self.valid and self.errors:
            raise ValueError("A valid verification report cannot carry verification errors")
        if not self.valid and not self.errors:
            raise ValueError(
                "An invalid verification report must carry at least one verification error"
            )
