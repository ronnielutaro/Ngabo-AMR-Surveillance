"""Stable execution error codes for the event-invoked investigation runtime (#53).

These describe WHY an outer execution did not reach
``InvestigationExecutionOutcome.COMPLETED_CURRENT_STAGE``. They are not the
inner capability outcomes; they are the deterministic outer-runtime routing
vocabulary a future orchestrator/PubSub adapter can branch on without parsing
prose or exceptions.
"""

from __future__ import annotations

from enum import StrEnum


class InvestigationExecutionErrorCode(StrEnum):
    """Stable, machine-checkable reason a run failed or was blocked."""

    MALFORMED_COMMAND = "MALFORMED_COMMAND"
    """The event-shaped command was missing/invalid before any run started."""

    INCIDENT_NOT_FOUND = "INCIDENT_NOT_FOUND"
    """The referenced incident does not exist in canonical state."""

    STALE_INCIDENT_VERSION = "STALE_INCIDENT_VERSION"
    """The command's requested incident version is not current."""

    SOURCE_WATERMARK_MISMATCH = "SOURCE_WATERMARK_MISMATCH"
    """The event's source watermark does not match the canonical source watermark."""

    REQUIRED_INPUT_UNAVAILABLE = "REQUIRED_INPUT_UNAVAILABLE"
    """The deterministic fan-out input could not be derived unambiguously
    (e.g. an incident that does not contain exactly the required comparison
    pair, or a non-homogeneous cohort)."""

    REQUIRED_BRANCH_FAILED = "REQUIRED_BRANCH_FAILED"
    """A required deterministic branch did not complete with SUCCESS."""

    BRANCH_BINDING_MISMATCH = "BRANCH_BINDING_MISMATCH"
    """A branch reported SUCCESS but returned a different incident id, incident
    version, or source watermark than the canonical fan-out input."""

    GRAPH_RETRY_EXHAUSTED = "GRAPH_RETRY_EXHAUSTED"
    """A retryable graph attempt failed repeatedly and the hard attempt budget
    was exhausted."""

    GRAPH_CANCELLED = "GRAPH_CANCELLED"
    """The deterministic graph invocation was cancelled before completion."""

    MISSING_INPUT = "MISSING_INPUT"
    """The inward capability reported a required input was unavailable."""

    INWARD_CAPABILITY_FAILED = "INWARD_CAPABILITY_FAILED"
    """An inward capability reported an unexpected non-success outcome."""

    WRAPPER_EXCEPTION = "WRAPPER_EXCEPTION"
    """A thin ADK wrapper raised an unexpected exception (fail closed)."""

    ADK_RUNTIME_EXCEPTION = "ADK_RUNTIME_EXCEPTION"
    """The ADK Runner/session/workflow machinery raised an unexpected error."""

    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"
    """The enforced runtime deadline was exceeded (fail closed)."""

    EXECUTION_BUDGET_EXCEEDED = "EXECUTION_BUDGET_EXCEEDED"
    """A configured execution budget (tool/function call count) was exceeded."""
