"""Stable terminal outcomes for the event-invoked investigation runtime (#53).

This is the OUTER runtime vocabulary, distinct from the inner deterministic
capability outcomes (:class:`CapabilityOutcome`). It describes what happened to
the event-invoked ADK execution as a whole, not what a single capability
reported.

Authority boundary (the #53 invariant):

- only ``COMPLETED_CURRENT_STAGE`` is a success semantic;
- there is NO member named ``PACKAGE_COMPLETED`` / ``INVESTIGATION_COMPLETE`` /
  ``VERIFIED`` / ``ACTION_READY``;
- a ``FAILED`` / ``BLOCKED`` outcome can never be interpreted as package
  completion or as authorization to act.

``BLOCKED`` is reserved for "cannot legitimately proceed because of incident /
source state" (e.g. missing incident, stale version). ``FAILED`` is reserved
for actual runtime/execution machinery failures (e.g. timeout, wrapper
exception, ADK runtime exception, malformed command). Both are non-success.
"""

from __future__ import annotations

from enum import StrEnum


class InvestigationExecutionOutcome(StrEnum):
    """Terminal outcome of one event-invoked investigation run."""

    COMPLETED_CURRENT_STAGE = "COMPLETED_CURRENT_STAGE"
    """The outer runtime accepted the event and completed the currently
    configured bounded adapter workflow. This is a narrow, truthful success
    semantic: no incident package was synthesized and no action was taken."""

    FAILED = "FAILED"
    """The run did not complete successfully. Reserved for runtime/execution
    machinery failures (malformed command, timeout, budget exceeded, wrapper
    exception, ADK runtime exception)."""

    BLOCKED = "BLOCKED"
    """The run could not legitimately proceed because of incident/source state
    (e.g. missing incident, stale incident version, inward capability
    abstention). It is a non-success, non-authorizing abstention."""

    @property
    def is_success(self) -> bool:
        """True only for the narrow ``COMPLETED_CURRENT_STAGE`` success value."""
        return self is InvestigationExecutionOutcome.COMPLETED_CURRENT_STAGE
