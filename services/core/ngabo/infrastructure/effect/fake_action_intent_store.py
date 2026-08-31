"""Deterministic in-memory ``ActionIntentStore`` for the deadline hero tests (#176).

Test-only seam. It is NOT durable production storage; it exists to prove the
orchestration boundary (no intent -> no effect, duplicate logical action does not
acquire dispatch ownership) without touching a real persistence backend.
"""

from __future__ import annotations

import time
import uuid

from ngabo.application.enums.intent_state import IntentState
from ngabo.application.value_objects.effect_delivery import EffectDelivery
from ngabo.application.value_objects.hero_action_intent import HeroActionIntent
from ngabo.application.value_objects.intent_reservation import IntentReservation


class FakeActionIntentStore:
    """In-memory, keyed by the deterministic logical idempotency key."""

    def __init__(self) -> None:
        self._records: dict[
            str,
            tuple[IntentState, EffectDelivery | None, float, int, str | None],
        ] = {}
        self.reservations: list[IntentReservation] = []
        self.state_transitions: list[IntentState] = []

    def reserve(
        self,
        intent: HeroActionIntent,
        *,
        lease_ttl_seconds: float = 30.0,
        max_retries: int = 2,
        now: float | None = None,
    ) -> IntentReservation:
        current = now if now is not None else time.time()
        key = intent.idempotency_key
        if key not in self._records:
            token = "lease-" + uuid.uuid4().hex
            self._records[key] = (
                IntentState.DISPATCHED,
                None,
                current + lease_ttl_seconds,
                0,
                token,
            )
            reservation = IntentReservation(
                intent=intent,
                state=IntentState.DISPATCHED,
                owned=True,
                lease_token=token,
            )
        else:
            state, delivery, lease_left, retries, existing_token = self._records[key]
            stateless = state in (
                IntentState.PENDING,
                IntentState.RETRYABLE,
            )
            lease_expired = (
                state is IntentState.DISPATCHED and current > lease_left
            )
            if stateless or lease_expired:
                if retries < max_retries:
                    new_token = "lease-" + uuid.uuid4().hex
                    self._records[key] = (
                        IntentState.DISPATCHED,
                        delivery,
                        current + lease_ttl_seconds,
                        retries + 1,
                        new_token,
                    )
                    reservation = IntentReservation(
                        intent=intent,
                        state=IntentState.DISPATCHED,
                        owned=True,
                        lease_token=new_token,
                    )
                else:
                    self._records[key] = (
                        IntentState.FAILED,
                        delivery,
                        0.0,
                        retries,
                        existing_token,
                    )
                    reservation = IntentReservation(
                        intent=intent, state=IntentState.FAILED, owned=False
                    )
            else:
                reservation = IntentReservation(
                    intent=intent, state=state, owned=False, lease_token=None
                )
        self.reservations.append(reservation)
        return reservation

    def record_state(
        self,
        intent: HeroActionIntent,
        state: IntentState,
        *,
        lease_token: str,
        delivery: EffectDelivery | None = None,
    ) -> bool:
        prior = self._records.get(intent.idempotency_key)
        if prior is None:
            return False
        if prior[4] != lease_token:
            # Stale owner: a newer generation owns the intent; do not mutate.
            return False
        self._records[intent.idempotency_key] = (
            state,
            delivery,
            prior[2],
            prior[3],
            prior[4],
        )
        self.state_transitions.append(state)
        return True

    def state(self, intent: HeroActionIntent) -> IntentState:
        return self._records[intent.idempotency_key][0]

    def delivery(self, intent: HeroActionIntent) -> EffectDelivery | None:
        return self._records[intent.idempotency_key][1]
