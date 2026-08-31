"""Typed outcomes for the deadline hero completion slice (#176)."""

from __future__ import annotations

from enum import StrEnum


class HeroOutcome(StrEnum):
    """Terminal outcome of one canonical hero run."""

    HERO_COMPLETED = "HERO_COMPLETED"
    """The full canonical hero finished: deterministic verification passed,
    freshness passed, A1 policy authorized the single safe synthetic action,
    a real external delivery occurred, and the machine acknowledgement was
    verified. This is the ONLY success terminal; neither Gemini nor a human
    created it."""

    BLOCKED = "BLOCKED"
    """The hero could not legitimately proceed (unverified package, stale
    binding, unauthorized target, policy abstention, or a verification/cross-
    run failure). Non-success and non-authorizing."""

    FAILED = "FAILED"
    """A runtime/infrastructure failure occurred (delivery transport, malformed
    acknowledgement, invalid signature). Bounded and typed; no fallback."""

    @property
    def is_success(self) -> bool:
        """True only for the narrow ``HERO_COMPLETED`` success."""
        return self is HeroOutcome.HERO_COMPLETED
