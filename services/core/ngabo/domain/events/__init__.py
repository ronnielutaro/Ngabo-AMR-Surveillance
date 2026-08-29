"""Domain events for Ngabo surveillance (Issue #48 / Epic #18)."""

from __future__ import annotations

from ngabo.domain.events.investigation_priority_signal_event import (
    DEFAULT_SIGNAL_EVENT_CONTRACT_VERSION,
    DEFAULT_SIGNAL_EVENT_TYPE,
    InvestigationPrioritySignalEvent,
    compute_signal_event_id,
    create_investigation_priority_signal_event,
)

__all__ = [
    "DEFAULT_SIGNAL_EVENT_CONTRACT_VERSION",
    "DEFAULT_SIGNAL_EVENT_TYPE",
    "InvestigationPrioritySignalEvent",
    "compute_signal_event_id",
    "create_investigation_priority_signal_event",
]
