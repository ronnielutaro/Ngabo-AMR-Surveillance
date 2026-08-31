"""Inward application port for the durable ActionIntent/outbox boundary (#176).

``reserve`` acts as an atomic create-or-get keyed by the deterministic logical
idempotency key, and returns whether THIS caller won the single dispatch
ownership lease. ``record_*`` transitions durable state. The model never
supplies the destination, the idempotency key, or the target.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ngabo.application.enums.intent_state import IntentState
from ngabo.application.value_objects.effect_delivery import EffectDelivery
from ngabo.application.value_objects.hero_action_intent import HeroActionIntent
from ngabo.application.value_objects.intent_reservation import IntentReservation


@runtime_checkable
class ActionIntentStore(Protocol):
    """Durable pre-effect intent/outbox boundary for the deadline hero."""

    def reserve(
        self,
        intent: HeroActionIntent,
        *,
        lease_ttl_seconds: float = 30.0,
        max_retries: int = 2,
    ) -> IntentReservation:
        """Atomically create-or-get the logical intent and acquire dispatch lease.

        For the same logical idempotency key, repeated calls return the same
        record. ``owned`` is True only for the caller that transitions the record
        from PENDING/RETRYABLE/expired-lease to DISPATCHED. A duplicate acquire
        while a valid lease is held does not create a second logical intent and
        must not issue a second external effect. A bounded retry reacquires the
        SAME intent + idempotency key after a transient failure or lease expiry.
        """
        ...

    def record_state(
        self,
        intent: HeroActionIntent,
        state: IntentState,
        delivery: EffectDelivery | None = None,
    ) -> None:
        """Durably transition the intent to ``state`` (recording delivery if given)."""
        ...
