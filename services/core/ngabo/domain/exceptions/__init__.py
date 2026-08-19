"""Domain exceptions — framework-free error types for domain policy violations.

Must never import frameworks, cloud SDKs, AI SDKs, or outer Ngabo layers
(see ``docs/CLEAN_ARCHITECTURE.md``). Populated issue by issue; see Issue #26
for the invalid incident-transition error added in M1B.2.
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
