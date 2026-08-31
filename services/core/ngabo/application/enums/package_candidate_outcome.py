"""Typed outcomes for the bounded Gemini package-candidate synthesis stage (Issue #56).

These describe the outer #56 synthesis stage as a whole. The package is an
UNVERIFIED model proposal. ``PACKAGE_CANDIDATE_GENERATED`` is the single
success semantic and is equivalent to ``AWAITING_DETERMINISTIC_VERIFICATION``:
no claim was verified, no policy/action/authority was granted, and the package
is not sent or acted on.

Authority boundary:

- the only success is ``PACKAGE_CANDIDATE_GENERATED``;
- there is NO member named ``VERIFIED``, ``APPROVED``, ``ACTION_READY``,
  ``PACKAGE_COMPLETED``, ``SENT``, ``ACKNOWLEDGED`` or ``OUTBREAK_CONFIRMED``;
- ``BLOCKED`` / ``FAILED`` / ``NO_EVIDENCE`` are non-success and never
  authorize synthesis, verification, policy or action.
"""

from __future__ import annotations

from enum import StrEnum


class PackageCandidateOutcome(StrEnum):
    """Terminal outcome of one bounded #56 package-candidate synthesis run."""

    PACKAGE_CANDIDATE_GENERATED = "PACKAGE_CANDIDATE_GENERATED"
    """A valid framework-free ``IncidentPackageCandidate`` was produced from
    the deterministic #54 findings and the #55 approved evidence. It is
    unverified and awaiting deterministic verification. This is a narrow,
    truthful success semantic: no verification, policy, action, or delivery
    happened."""

    NO_EVIDENCE = "NO_EVIDENCE"
    """The #55 stage did not produce approved evidence, so synthesis cannot
    ground claims and must not begin."""

    BLOCKED = "BLOCKED"
    """The stage could not legitimately proceed: the #54 entry gate was not
    downstream-ready, the #55 outcome was not evidence-prepared, the model
    produced a forbidden/invalid proposal, or a deterministic gate rejected the
    support references. Never authorizes verification or action."""

    FAILED = "FAILED"
    """The model/provider/runtime failed (malformed output, schema violation,
    timeout, rate limit, provider failure, parse failure). Bounded and typed;
    no free-form prose fallback."""

    @property
    def is_success(self) -> bool:
        """True only for the narrow ``PACKAGE_CANDIDATE_GENERATED`` completion."""
        return self is PackageCandidateOutcome.PACKAGE_CANDIDATE_GENERATED

    @property
    def awaiting_deterministic_verification(self) -> bool:
        """Alias documenting that a generated candidate waits for verification."""
        return self.is_success
