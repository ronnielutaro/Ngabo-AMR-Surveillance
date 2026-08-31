"""Durable ActionIntent lifecycle state for the deadline hero (#176).

This is the minimum deadline-safe dispatch state machine. Production
transactional outbox recovery and dispatcher hardening remain #67/#69.
"""

from __future__ import annotations

from enum import StrEnum


class IntentState(StrEnum):
    """Durable lifecycle state of one logical ActionIntent."""

    PENDING = "PENDING"
    """The intent durably exists and is awaiting dispatch. No external effect has
    occurred yet."""

    DISPATCHED = "DISPATCHED"
    """A single dispatch owner acquired the lease and the effect was attempted."""

    ACKNOWLEDGED = "ACKNOWLEDGED"
    """A machine-verifiable acknowledgement for the exact persisted action was
    received and verified. Only this may lead to HERO_COMPLETED."""

    FAILED = "FAILED"
    """The effect or acknowledgement failed; never becomes a success."""
