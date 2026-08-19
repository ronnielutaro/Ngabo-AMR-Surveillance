"""Framework-free incident lifecycle state enum (Issue #26 / M1B.2).

State names are taken from the governing documents:

- ``INVESTIGATING`` — the active investigation state shown by the frontend
  data contract (``docs/UI_UX_SPEC.md`` §25).
- ``COMPLETED`` — terminal success reached when the machine acknowledgement
  closes the hero (``docs/PRD.md`` §13, ``docs/SYSTEM_DESIGN.md`` §16).
- ``NEEDS_INFORMATION`` / ``INSUFFICIENT_APPROVED_EVIDENCE`` /
  ``VALIDATION_FAILED`` / ``POLICY_BLOCKED`` / ``STALE_RECOMPUTE_REQUIRED`` /
  ``ACTION_FAILED_RETRYABLE`` / ``ACTION_FAILED_TERMINAL`` — the valid
  terminal/degraded states listed in
  ``docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`` §13 and
  ``docs/AGENT_ARCHITECTURE.md`` §12; these are the outcomes the incident
  lifecycle must keep visible instead of faking completion.

Deliberately NOT incident lifecycle states:

- ``CLAIM_VERIFICATION_FAILED`` — a transient verification-phase outcome that
  feeds bounded repair inside the active workflow; only repair exhaustion
  transitions the incident to ``VALIDATION_FAILED`` (``CLAUDE.md`` §12).
- the ``ActionIntent`` status lifecycle (``PREPARED``/``SENDING``/``SENT``/
  ``ACKNOWLEDGED``/...) — a separate outbox lifecycle per ADR 0008 /
  ``docs/AUTONOMOUS_EFFECT_OUTBOX.md``.
- workflow event names such as ``WORKFLOW_COMPLETED``/``WORKFLOW_ABSTAINED``.

The enum carries no persistence, framework, or transition behavior; see
``ngabo.domain.services.incident_transitions`` for the deterministic
fail-closed transition policy.
"""

from __future__ import annotations

from enum import StrEnum


class IncidentState(StrEnum):
    """Lifecycle states of a Ngabo incident."""

    INVESTIGATING = "INVESTIGATING"
    COMPLETED = "COMPLETED"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"
    INSUFFICIENT_APPROVED_EVIDENCE = "INSUFFICIENT_APPROVED_EVIDENCE"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    STALE_RECOMPUTE_REQUIRED = "STALE_RECOMPUTE_REQUIRED"
    ACTION_FAILED_RETRYABLE = "ACTION_FAILED_RETRYABLE"
    ACTION_FAILED_TERMINAL = "ACTION_FAILED_TERMINAL"
