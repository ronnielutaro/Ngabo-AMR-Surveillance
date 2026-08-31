"""Framework-free deterministic hero package verification result (#176).

``HeroVerificationError`` is one typed failed check. ``HeroVerificationResult``
is the all-or-nothing aggregate: ``verified=True`` only when every material
claim/reference/binding check passed. This is structurally DISTINCT from the raw
``IncidentPackageCandidate`` and is the ONLY input the A1 policy may accept.
"""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.application.enums.hero_error_code import HeroErrorCode
from ngabo.application.value_objects.incident_package import IncidentPackageCandidate


@dataclass(frozen=True)
class HeroVerificationError:
    """One deterministic verification failure."""

    code: HeroErrorCode
    detail: str
    claim_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, HeroErrorCode):
            raise ValueError("code must be a HeroErrorCode")
        if not isinstance(self.detail, str) or not self.detail:
            raise ValueError("detail must be non-blank text")
        if self.claim_id is not None and (
            not isinstance(self.claim_id, str) or not self.claim_id
        ):
            raise ValueError("claim_id must be non-blank text or None")


@dataclass(frozen=True)
class HeroVerificationResult:
    """All-or-nothing deterministic verification of a hero package."""

    verified: bool
    package: IncidentPackageCandidate | None
    errors: tuple[HeroVerificationError, ...] = ()
    claim_count: int = 0
    verified_claim_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.verified, bool):
            raise ValueError("verified must be a bool")
        if self.package is not None and not isinstance(
            self.package, IncidentPackageCandidate
        ):
            raise ValueError("package must be an IncidentPackageCandidate or None")
        if not isinstance(self.errors, tuple):
            raise ValueError("errors must be a tuple")
        for index, error in enumerate(self.errors):
            if not isinstance(error, HeroVerificationError):
                raise ValueError(
                    f"errors[{index}] must be a HeroVerificationError"
                )
        if isinstance(self.claim_count, bool) or not isinstance(
            self.claim_count, int
        ) or self.claim_count < 0:
            raise ValueError("claim_count must be a non-negative integer")
        if not isinstance(self.verified_claim_ids, tuple):
            raise ValueError("verified_claim_ids must be a tuple")
        if self.verified and self.package is None:
            raise ValueError("a verified result must carry the package")
        if self.verified and self.errors:
            raise ValueError("a verified result cannot carry errors")
        if not self.verified and self.package is not None:
            # Keep the package for diagnostics/telemetry; it is NOT the verified
            # type and must never reach policy.
            pass

    @property
    def verified_package_id(self) -> str | None:
        return self.package.package_id.value if self.package is not None else None
