"""Domain exceptions — framework-free error types for domain policy violations.

Must never import frameworks, cloud SDKs, AI SDKs, or outer Ngabo layers
(see ``docs/CLEAN_ARCHITECTURE.md``). Populated issue by issue; see Issue #26
for the invalid incident-transition error (M1B.2) and Issue #27 for the
invalid autonomy-decision error (M1B.3).
"""

from __future__ import annotations

from ngabo.domain.enums.incident_state import IncidentState


class InvalidIncidentTransitionError(Exception):
    """Raised when a requested incident transition is not explicitly allowed.

    Carries the current and requested states so callers and logs can identify
    exactly which deterministic rejection occurred.
    """

    def __init__(self, current: IncidentState, requested: IncidentState) -> None:
        self.current = current
        self.requested = requested
        super().__init__(
            f"Invalid incident state transition {current} -> {requested}; "
            "transitions must be explicitly allowed by the deterministic "
            "incident lifecycle policy"
        )


class InvalidAutonomyDecisionError(Exception):
    """Raised when an autonomy decision requests an impossible combination.

    Carries the offending action class and status values so callers and logs
    can identify exactly which deterministic rejection occurred: either the
    class is unknown, or the (class, status, reason) combination is not one
    the deterministic autonomy classification contract permits.
    """

    def __init__(self, action_class: object, status: object) -> None:
        self.action_class = action_class
        self.status = status
        super().__init__(
            f"Invalid autonomy decision for action class {action_class!r} with "
            f"status {status!r}; only combinations explicitly permitted by the "
            "deterministic autonomy classification contract are allowed"
        )
