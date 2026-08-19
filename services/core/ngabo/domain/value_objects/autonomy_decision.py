"""Classification-level autonomy decision contract (Issue #27 / M1B.3).

``AutonomyDecision`` is the smallest immutable framework-free value object
that captures, at the classification-contract level, whether an action of a
given ``ActionClass`` may be autonomous: the class itself, a deterministic
status, and a stable reason suitable for later application/DTO boundaries.

It is deliberately NOT the ActionPolicy result object: it carries no target,
allow-list evaluation, authorization configuration, incident/package
versions, freshness result, ActionIntent data, payload, or external adapter
information. The later deterministic policy layer will evaluate those gates
and owns final classification/authorization (``CLAUDE.md`` §4,
``docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`` §4–5, ADR 0007).

Structural invariants (enforced at construction time, fail-closed):

    A0 INTERNAL_STATE                                -> AUTONOMOUS_ELIGIBLE
    A1 SAFE_EXTERNAL_COORDINATION                    -> GATES_REQUIRED
    A2 REAL_OPERATIONAL_ESCALATION                   -> BLOCKED
    A3 CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION   -> BLOCKED

Every other (class, status) combination — and every reason other than the
canonical one — is rejected deterministically. Because the mapping is
enforced at construction, no caller (including a model) can supply a
different status or reason value and obtain an A2/A3 decision that claims
autonomous eligibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from ngabo.domain.enums.action_class import ActionClass
from ngabo.domain.enums.autonomy_decision_status import AutonomyDecisionStatus
from ngabo.domain.exceptions import InvalidAutonomyDecisionError

REASON_A0: Final[str] = (
    "A0 INTERNAL_STATE: autonomous internal incident/package/audit state work "
    "is eligible at this classification level; carries no external-action "
    "semantics and authorizes no external effect."
)
REASON_A1: Final[str] = (
    "A1 SAFE_EXTERNAL_COORDINATION: belongs to the potentially autonomous "
    "safe-coordination lane; classification alone authorizes nothing — later "
    "deterministic gates (verified package, allow-listed target, "
    "authorization, freshness, ActionIntent/idempotency) remain required."
)
REASON_A2: Final[str] = (
    "A2 REAL_OPERATIONAL_ESCALATION: outside the default autonomous "
    "public-v0.1 envelope; autonomous execution is blocked — any escalation "
    "requires separate explicit authorization outside the autonomous flow."
)
REASON_A3: Final[str] = (
    "A3 CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION: prescribing, treatment, "
    "diagnosis, official outbreak confirmation/declaration, or equivalent "
    "consequential authority; never autonomously executable in v0.1."
)

AUTONOMY_CLASSIFICATION_CONTRACT: Final[
    dict[ActionClass, tuple[AutonomyDecisionStatus, str]]
] = {
    ActionClass.INTERNAL_STATE: (
        AutonomyDecisionStatus.AUTONOMOUS_ELIGIBLE,
        REASON_A0,
    ),
    ActionClass.SAFE_EXTERNAL_COORDINATION: (
        AutonomyDecisionStatus.GATES_REQUIRED,
        REASON_A1,
    ),
    ActionClass.REAL_OPERATIONAL_ESCALATION: (
        AutonomyDecisionStatus.BLOCKED,
        REASON_A2,
    ),
    ActionClass.CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION: (
        AutonomyDecisionStatus.BLOCKED,
        REASON_A3,
    ),
}


@dataclass(frozen=True)
class AutonomyDecision:
    """Immutable classification-level autonomy decision for one action class.

    Only the exact combinations permitted by
    ``AUTONOMY_CLASSIFICATION_CONTRACT`` may be constructed; anything else —
    unknown classes, forbidden statuses, non-canonical reasons — raises
    ``InvalidAutonomyDecisionError``.
    """

    action_class: ActionClass
    status: AutonomyDecisionStatus
    reason: str

    def __post_init__(self) -> None:
        validate_autonomy_decision(self.action_class, self.status, self.reason)

    @classmethod
    def for_class(cls, action_class: ActionClass) -> AutonomyDecision:
        """Build the canonical decision for ``action_class``; fail closed on unknown input."""
        if not isinstance(action_class, ActionClass):
            raise InvalidAutonomyDecisionError(action_class, None)
        status, reason = AUTONOMY_CLASSIFICATION_CONTRACT[action_class]
        return cls(action_class=action_class, status=status, reason=reason)


def validate_autonomy_decision(
    action_class: object,
    status: object,
    reason: str,
) -> None:
    """Reject any decision the classification contract does not permit.

    ``StrEnum`` members compare equal to their string values, so unknown
    inputs must be rejected with ``isinstance`` guards rather than mapping
    lookups; otherwise a raw ``"A1"`` string would silently pass as
    ``ActionClass.SAFE_EXTERNAL_COORDINATION``.
    """
    if not isinstance(action_class, ActionClass) or not isinstance(
        status, AutonomyDecisionStatus
    ):
        raise InvalidAutonomyDecisionError(action_class, status)
    expected_status, expected_reason = AUTONOMY_CLASSIFICATION_CONTRACT[action_class]
    if status != expected_status or reason != expected_reason:
        raise InvalidAutonomyDecisionError(action_class, status)
