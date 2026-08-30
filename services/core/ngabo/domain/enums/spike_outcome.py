"""Spike-level workflow outcomes for the ADK/Gemini capability spike (Issue #49).

These are *workflow* outcomes, distinct from the certified
``VerificationErrorCode`` per-claim vocabulary (#29). The spike verifier
never changes the canonical nine-code vocabulary; it represents the
aggregate decision it routes the graph toward, which the certified codes
deliberately do not express.

Values:

- ``ACCEPTED`` — the structured claim passed deterministic verification and
  the downstream path may continue.
- ``REQUIRED_BRANCH_FAILED`` — a required deterministic parallel branch did
  not produce valid output, so the workflow degrades/blocks rather than
  synthesizing a false success.
- ``MALFORMED_PROOF`` — the model produced output that could not satisfy the
  structured proof schema or the framework-free DTO construction.
- ``BLOCKED`` — verification failed after bounded repair (or a non-repairable
  structural failure); continuation is deterministically blocked/abstained.
"""

from __future__ import annotations

from enum import StrEnum


class SpikeOutcome(StrEnum):
    """Aggregate route decision produced by the deterministic spike verifier."""

    ACCEPTED = "ACCEPTED"
    REQUIRED_BRANCH_FAILED = "REQUIRED_BRANCH_FAILED"
    MALFORMED_PROOF = "MALFORMED_PROOF"
    BLOCKED = "BLOCKED"
