"""Spike verifier result/error contracts (Issue #49).

``SpikeVerificationError`` is one immutable structured verification failure,
carrying the stable ``SpikeVerificationCode`` family in addition to optional
offending ``reference``/``field``/``detail``. ``SpikeVerificationResult`` is
the aggregate: ``valid`` plus zero-or-more errors, with the hard invariants
that a valid result carries no errors and an invalid result carries at least
one.

This is an issue-scoped result type. It does NOT replace the canonical
``ClaimVerificationReport`` (#29) — the infrastructure adapter proves the
boundary by also mapping a verified spike claim onto a ``ReasoningClaim`` /
``ClaimVerificationReport`` where the production contract is exercised.
"""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.application.enums.spike_verification_code import SpikeVerificationCode


@dataclass(frozen=True)
class SpikeVerificationError:
    """Immutable structured verification failure for one spike claim/context."""

    code: SpikeVerificationCode
    reference: str | None = None
    field: str | None = None
    detail: str | None = None

    def __post_init__(self) -> None:
        # StrEnum members compare equal to their string values, so the type
        # must be guarded with isinstance rather than a mapping lookup.
        if not isinstance(self.code, SpikeVerificationCode):
            raise ValueError(
                f"Invalid spike verification code {self.code!r}; "
                "expected a SpikeVerificationCode member"
            )
        for name, value in (
            ("reference", self.reference),
            ("field", self.field),
            ("detail", self.detail),
        ):
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"Invalid {name} {value!r}; expected non-blank text or None")


@dataclass(frozen=True)
class SpikeVerificationResult:
    """Immutable pass/fail result of the spike deterministic verifier."""

    valid: bool
    errors: tuple[SpikeVerificationError, ...] = ()

    def __post_init__(self) -> None:
        # bool subclasses int, so the type must be guarded with isinstance.
        if not isinstance(self.valid, bool):
            raise ValueError(f"Invalid verification result {self.valid!r}; expected a bool")
        if not isinstance(self.errors, tuple):
            raise ValueError(
                f"Invalid verification errors {self.errors!r}; expected a tuple"
            )
        for index, error in enumerate(self.errors):
            if not isinstance(error, SpikeVerificationError):
                raise ValueError(
                    f"Invalid verification error at position {index}: {error!r}; "
                    "expected a SpikeVerificationError"
                )
        if self.valid and self.errors:
            raise ValueError("A valid verification result cannot carry verification errors")
        if not self.valid and not self.errors:
            raise ValueError(
                "An invalid verification result must carry at least one verification error"
            )
