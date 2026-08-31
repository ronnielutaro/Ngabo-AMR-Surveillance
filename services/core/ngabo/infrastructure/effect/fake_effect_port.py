"""Deterministic test-only fake ``EffectPort`` (#176).

Never used in the deployed hero; used to prove the gate chain offline. It
produces a valid signed ``EffectDelivery`` mirroring the receiver contract with a
caller-supplied shared secret.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime

from ngabo.application.value_objects.effect_delivery import EffectDelivery
from ngabo.application.value_objects.hero_action_intent import HeroActionIntent
from ngabo.application.value_objects.hero_payload import HeroCoordinationPayload


class FakeEffectPort:
    """Test-only fake effect port producing a signed delivery."""

    def __init__(self, *, ack_secret: str) -> None:
        if not ack_secret.strip():
            raise ValueError("ack_secret must be non-blank")
        self._secret = ack_secret.encode("utf-8")
        self.calls: list[HeroActionIntent] = []

    def deliver(
        self,
        intent: HeroActionIntent,
        payload: HeroCoordinationPayload,
    ) -> EffectDelivery:
        self.calls.append(intent)
        delivery_id = f"dlv-{len(self.calls)}"
        ack_id = f"ack-{len(self.calls)}"
        received_at = datetime.now(UTC).isoformat(timespec="seconds")
        signature = hmac.new(
            self._secret,
            "|".join(
                (
                    intent.action_id,
                    intent.payload_hash,
                    delivery_id,
                    ack_id,
                    received_at,
                    "RECEIVED",
                )
            ).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return EffectDelivery(
            delivery_id=delivery_id,
            ack_id=ack_id,
            action_id=intent.action_id,
            payload_hash=intent.payload_hash,
            received_at=received_at,
            status="RECEIVED",
            signature=signature,
        )
