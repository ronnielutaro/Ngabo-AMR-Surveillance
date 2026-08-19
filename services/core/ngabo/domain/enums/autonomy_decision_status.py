"""Framework-free classification-level autonomy decision status (Issue #27).

Small enum used by ``AutonomyDecision`` to express, at the classification
level only, whether autonomous execution is eligible, gated, or blocked.

It is deliberately NOT the later ActionPolicy verdict: the deterministic
policy layer will build richer results on top of this contract when the
allow-list, freshness, ActionIntent and other gates are implemented. It
carries no target, authorization, freshness or package information.
"""

from __future__ import annotations

from enum import StrEnum


class AutonomyDecisionStatus(StrEnum):
    """Classification-level autonomy eligibility of an action.

    ``AUTONOMOUS_ELIGIBLE`` — autonomous execution is eligible at this
    classification level (A0 internal state only; no external-action
    semantics).

    ``GATES_REQUIRED`` — belongs to the potentially autonomous lane, but
    later deterministic gates are still required; classification alone
    authorizes nothing (A1 only).

    ``BLOCKED`` — autonomous execution is not permitted in public v0.1
    (A2/A3).
    """

    AUTONOMOUS_ELIGIBLE = "AUTONOMOUS_ELIGIBLE"
    GATES_REQUIRED = "GATES_REQUIRED"
    BLOCKED = "BLOCKED"
