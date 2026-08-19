"""Deterministic fail-closed incident lifecycle transition policy (Issue #26).

Governing rule: a transition is allowed only when explicitly listed here.
Everything else — including same-state requests and unknown inputs — is
rejected. Gemini, ADK, and persistence layers must never decide whether an
incident transition is valid (``docs/CLEAN_ARCHITECTURE.md``,
``docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md``).

Allowed transition graph:

    INVESTIGATING -> COMPLETED
                   | NEEDS_INFORMATION
                   | INSUFFICIENT_APPROVED_EVIDENCE
                   | VALIDATION_FAILED
                   | POLICY_BLOCKED
                   | STALE_RECOMPUTE_REQUIRED
                   | ACTION_FAILED_RETRYABLE
                   | ACTION_FAILED_TERMINAL
    STALE_RECOMPUTE_REQUIRED -> INVESTIGATING
        (freshness recompute path, ADR 0006 / docs/LONG_RUNNING_AGENT.md)
    ACTION_FAILED_RETRYABLE -> COMPLETED
                             | ACTION_FAILED_TERMINAL
        (outbox retry with machine ack, or exhausted retries, ADR 0008)

Terminal states (no outgoing edges): ``COMPLETED``, ``NEEDS_INFORMATION``,
``INSUFFICIENT_APPROVED_EVIDENCE``, ``VALIDATION_FAILED``, ``POLICY_BLOCKED``,
``ACTION_FAILED_TERMINAL``. Terminal states cannot silently reopen.

Same-state requests are rejected: a transition request asks the incident to
change state, and a no-op request is a caller defect or a duplicate event
that the caller must treat idempotently at its own layer (acknowledgement
replay idempotency, ``CLAUDE.md`` §15).
"""

from __future__ import annotations

from typing import Final

from ngabo.domain.enums.incident_state import IncidentState
from ngabo.domain.exceptions import InvalidIncidentTransitionError

ALLOWED_INCIDENT_TRANSITIONS: Final[dict[IncidentState, frozenset[IncidentState]]] = {
    IncidentState.INVESTIGATING: frozenset(
        {
            IncidentState.COMPLETED,
            IncidentState.NEEDS_INFORMATION,
            IncidentState.INSUFFICIENT_APPROVED_EVIDENCE,
            IncidentState.VALIDATION_FAILED,
            IncidentState.POLICY_BLOCKED,
            IncidentState.STALE_RECOMPUTE_REQUIRED,
            IncidentState.ACTION_FAILED_RETRYABLE,
            IncidentState.ACTION_FAILED_TERMINAL,
        }
    ),
    IncidentState.STALE_RECOMPUTE_REQUIRED: frozenset({IncidentState.INVESTIGATING}),
    IncidentState.ACTION_FAILED_RETRYABLE: frozenset(
        {IncidentState.COMPLETED, IncidentState.ACTION_FAILED_TERMINAL}
    ),
}

TERMINAL_INCIDENT_STATES: Final[frozenset[IncidentState]] = frozenset(
    {
        IncidentState.COMPLETED,
        IncidentState.NEEDS_INFORMATION,
        IncidentState.INSUFFICIENT_APPROVED_EVIDENCE,
        IncidentState.VALIDATION_FAILED,
        IncidentState.POLICY_BLOCKED,
        IncidentState.ACTION_FAILED_TERMINAL,
    }
)


def can_transition(current: IncidentState, requested: IncidentState) -> bool:
    """Return True only when ``current -> requested`` is explicitly allowed."""
    if not isinstance(current, IncidentState) or not isinstance(requested, IncidentState):
        return False
    return requested in ALLOWED_INCIDENT_TRANSITIONS.get(current, frozenset())


def validate_transition(current: IncidentState, requested: IncidentState) -> None:
    """Validate ``current -> requested``; raise ``InvalidIncidentTransitionError`` otherwise."""
    if not can_transition(current, requested):
        raise InvalidIncidentTransitionError(current, requested)
