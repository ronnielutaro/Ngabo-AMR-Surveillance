"""Framework-free autonomous-action classification vocabulary (Issue #27 / M1B.3).

The four canonical action classes, exactly as defined by ``CLAUDE.md`` §4,
``docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`` §4, ADR 0007 and the other
governing documents:

- ``A0 INTERNAL_STATE`` — internal incident/package/audit state work; may be
  autonomous.
- ``A1 SAFE_EXTERNAL_COORDINATION`` — allow-listed test/sandbox/internal
  coordination action; may be autonomous only after all later deterministic
  policy gates pass.
- ``A2 REAL_OPERATIONAL_ESCALATION`` — real stakeholder/facility escalation
  with meaningful operational consequence; outside the default autonomous
  public-v0.1 lane.
- ``A3 CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION`` — prescribing,
  treatment, diagnosis, official outbreak confirmation/declaration, or
  equivalent consequential authority; never autonomous in v0.1.

Classification is NOT authorization. A class says what kind of action
something is; whether it may execute autonomously is decided by the later
deterministic ActionPolicy (not implemented in this issue) and reflected at
the classification level by ``AutonomyDecision``. Gemini/ADK never own the
final executable action class (ADR 0007: "Gemini does not own this
classification").

The serialized values ``"A0"``..``"A3"`` are the canonical short labels used
throughout the governing documents (e.g. the ``"requested_action_class":
"A1"`` hero-package data contract in ``docs/AGENT_ARCHITECTURE.md``);
member names carry the canonical semantic names.
"""

from __future__ import annotations

from enum import StrEnum


class ActionClass(StrEnum):
    """The four canonical action classes of the Ngabo autonomy model."""

    INTERNAL_STATE = "A0"
    SAFE_EXTERNAL_COORDINATION = "A1"
    REAL_OPERATIONAL_ESCALATION = "A2"
    CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION = "A3"
