"""Deterministic in-memory ``ActionIntentStore`` for the deadline hero tests (#176).

Test-only seam. It is NOT durable production storage; it exists to prove the
orchestration boundary (no intent -> no effect, duplicate logical action does not
acquire dispatch ownership) without touching a real persistence backend.
"""

from __future__ import annotations

from ngabo.application.enums.intent_state import IntentState
from ngabo.application.value_objects.effect_delivery import EffectDelivery
from ngabo.application.value_objects.hero_action_intent import HeroActionIntent
from ngabo.application.value_objects.intent_reservation import IntentReservation


class FakeActionIntentStore:
    """In-memory, keyed by the deterministic logical idempotency key."""

    def __init__(self) -> None:
        self._records: dict[str, tuple[IntentState, EffectDelivery | None]] = {}
        self.reservations: list[IntentReservation] = []
        self.state_transitions: list[IntentState] = []

    def reserve(self, intent: HeroActionIntent) -> IntentReservation:
        key = intent.idempotency_key
        if key not in self._records:
            # First reservation of a logical action: durable record created and the
            # caller acquires the single dispatch lease.
            self._records[key] = (IntentState.DISPATCHED, None)
            reservation = IntentReservation(
                intent=intent, state=IntentState.DISPATCHED, owned=True
            )
        else:
            reservation = IntentReservation(
                intent=intent,
                state=self._records[key][0],
                owned=False,
            )
        self.reservations.append(reservation)
        return reservation

    def record_state(
        self,
        intent: HeroActionIntent,
        state: IntentState,
        delivery: EffectDelivery | None = None,
    ) -> None:
        self._records[intent.idempotency_key] = (state, delivery)
        self.state_transitions.append(state)

    def state(self, intent: HeroActionIntent) -> IntentState:
        return self._records[intent.idempotency_key][0]

    def delivery(self, intent: HeroActionIntent) -> EffectDelivery | None:
        return self._records[intent.idempotency_key][1]
