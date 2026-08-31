"""Inward application port for the deadline hero external effect (#176).

The port returns a receiver-produced delivery identity + signed acknowledgement.
It is the only seam through which ngabo-core leaves the process over a real
network boundary. The model never supplies the destination, target, idempotency
key, or acknowledgement.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ngabo.application.value_objects.effect_delivery import EffectDelivery
from ngabo.application.value_objects.hero_action_intent import HeroActionIntent
from ngabo.application.value_objects.hero_payload import HeroCoordinationPayload


@runtime_checkable
class EffectPort(Protocol):
    """Deliver one authorized fake/synthetic effect and return its ack."""

    def deliver(
        self,
        intent: HeroActionIntent,
        payload: HeroCoordinationPayload,
    ) -> EffectDelivery:
        """Send ``intent`` to the configured authorized receiver.

        Returns a receiver-produced ``EffectDelivery``. Must never fabricate a
        success on failure.
        """
        ...
