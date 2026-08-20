"""Structured per-claim verification error (M1B.5 / Issue #29).

One small immutable error value object, carried by
``ClaimVerificationReport``. Follows the minimal shape required by
Issue #29 and the governing report example in
``docs/PROOF_CARRYING_REASONING.md`` §7:

- ``code`` — the stable ``VerificationErrorCode`` family; the primary
  machine-readable identity used for routing, repair, telemetry and
  evaluation (never prose alone);
- ``claim_id`` — the typed ``ClaimId`` of the affected claim;
- ``reference`` — optional offending reference (record/finding/source/claim
  ID the verifier could not resolve or validate);
- ``field`` — optional affected claim field;
- ``detail`` — optional safe supplemental human-readable detail.

``detail`` is supplemental only: it never carries the error's identity and
must never contain model-generated chain-of-thought. Optional strings are
rejected when blank. Construction validates intrinsic invariants only —
whether a reference actually exists is checked by the later deterministic
verifier, which builds these errors from its actual checks.
"""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.domain.enums.verification_error_code import VerificationErrorCode
from ngabo.domain.value_objects.claim_id import ClaimId


@dataclass(frozen=True)
class ClaimVerificationError:
    """Immutable structured verification failure for one claim."""

    code: VerificationErrorCode
    claim_id: ClaimId
    reference: str | None = None
    field: str | None = None
    detail: str | None = None

    def __post_init__(self) -> None:
        # StrEnum members compare equal to their string values, so the type
        # must be guarded with isinstance rather than a mapping lookup.
        if not isinstance(self.code, VerificationErrorCode):
            raise ValueError(
                f"Invalid verification error code {self.code!r}; "
                "expected a VerificationErrorCode member"
            )
        if not isinstance(self.claim_id, ClaimId):
            raise ValueError(
                f"Invalid affected claim ID {self.claim_id!r}; expected a ClaimId value object"
            )
        for name, value in (
            ("reference", self.reference),
            ("field", self.field),
            ("detail", self.detail),
        ):
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"Invalid {name} {value!r}; expected non-blank text or None")
