"""Typed result of the bounded package-candidate synthesis stage (#56)."""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.application.enums.package_candidate_error_code import (
    PackageCandidateErrorCode,
)
from ngabo.application.enums.package_candidate_outcome import (
    PackageCandidateOutcome,
)
from ngabo.application.value_objects.incident_package import IncidentPackageCandidate
from ngabo.application.value_objects.synthesis_support_manifest import (
    SynthesisSupportManifest,
)


@dataclass(frozen=True)
class PackageCandidateResult:
    """Outcome of one bounded #56 synthesis run.

    ``package`` is non-None exactly when ``outcome`` is
    ``PACKAGE_CANDIDATE_GENERATED``. A generated package is an UNVERIFIED
    proposal; this contract carries no ``verified``/``approved``/``authorized``
    state and never represents action readiness.
    """

    outcome: PackageCandidateOutcome
    package: IncidentPackageCandidate | None
    model_calls: int
    duration_ms: int
    model_version: str | None
    error_code: PackageCandidateErrorCode | None
    support_manifest: SynthesisSupportManifest | None = None
    execution_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, PackageCandidateOutcome):
            raise ValueError("outcome must be a PackageCandidateOutcome")
        if self.package is not None and not isinstance(
            self.package, IncidentPackageCandidate
        ):
            raise ValueError("package must be an IncidentPackageCandidate or None")
        if (
            isinstance(self.model_calls, bool)
            or not isinstance(self.model_calls, int)
            or self.model_calls < 0
        ):
            raise ValueError("model_calls must be a non-negative integer")
        if (
            isinstance(self.duration_ms, bool)
            or not isinstance(self.duration_ms, int)
            or self.duration_ms < 0
        ):
            raise ValueError("duration_ms must be a non-negative integer")
        if self.model_version is not None and (
            not isinstance(self.model_version, str) or not self.model_version.strip()
        ):
            raise ValueError("model_version must be non-blank text or None")
        if self.error_code is not None and not isinstance(
            self.error_code, PackageCandidateErrorCode
        ):
            raise ValueError("error_code must be a PackageCandidateErrorCode or None")
        if self.support_manifest is not None and not isinstance(
            self.support_manifest, SynthesisSupportManifest
        ):
            raise ValueError("support_manifest must be a SynthesisSupportManifest or None")
        if self.execution_id is not None and (
            not isinstance(self.execution_id, str) or not self.execution_id.strip()
        ):
            raise ValueError("execution_id must be non-blank text or None")
        if self.outcome.is_success and self.error_code is not None:
            raise ValueError("a successful synthesis outcome cannot carry an error_code")
        if self.outcome.is_success and self.package is None:
            raise ValueError("PACKAGE_CANDIDATE_GENERATED requires a package")

    def is_success(self) -> bool:
        """True only when an unverified package candidate was generated."""
        return self.outcome.is_success
