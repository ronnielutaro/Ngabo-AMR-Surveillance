"""Real HTTPS demo-receiver effect adapter for the deadline hero (#176).

``SignedReceiverClient`` is the infrastructure ``EffectPort`` implementation. It
POSTs the immutable intent + synthetic payload to the one configured authorized
test/sandbox receiver URL (never model-supplied) and parses the receiver's
signed response into an ``EffectDelivery``. It does NOT hard-code success; a
non-2xx/invalid response raises ``EffectDeliveryError`` and the orchestrator
fails closed.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from ngabo.application.value_objects.effect_delivery import EffectDelivery
from ngabo.application.value_objects.hero_action_intent import HeroActionIntent
from ngabo.application.value_objects.hero_payload import HeroCoordinationPayload


class EffectDeliveryError(RuntimeError):
    """Raised when the receiver does not return a valid delivery."""


class SignedReceiverClient:
    """Send one authorized synthetic effect to a configured receiver."""

    def __init__(self, *, receiver_url: str, timeout_seconds: float = 10.0) -> None:
        if not isinstance(receiver_url, str) or not receiver_url.strip():
            raise ValueError("receiver_url must be non-blank configured text")
        if not receiver_url.startswith("https://"):
            raise ValueError("the demo receiver must be an HTTPS origin")
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or timeout_seconds <= 0
        ):
            raise ValueError("timeout_seconds must be a positive finite number")
        self._url = receiver_url
        self._timeout = float(timeout_seconds)

    def deliver(
        self,
        intent: HeroActionIntent,
        payload: HeroCoordinationPayload,
    ) -> EffectDelivery:
        if payload.payload_hash() != intent.payload_hash:
            raise EffectDeliveryError("payload hash does not match the intent")
        body = {
            **intent.to_primitive(),
            "payload": payload.to_primitive(),
        }
        request = urllib.request.Request(
            self._url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                raw = response.read().decode("utf-8")
                if response.status < 200 or response.status >= 300:
                    raise EffectDeliveryError(
                        f"receiver returned HTTP {response.status}"
                    )
        except urllib.error.URLError as exc:
            raise EffectDeliveryError(f"receiver unreachable: {exc}") from exc
        except TimeoutError as exc:
            raise EffectDeliveryError("receiver timed out") from exc
        data = json.loads(raw)
        try:
            return EffectDelivery(
                delivery_id=str(data["delivery_id"]),
                ack_id=str(data["ack_id"]),
                action_id=str(data["action_id"]),
                payload_hash=str(data["payload_hash"]),
                received_at=str(data["received_at"]),
                status=str(data["status"]),
                signature=str(data["signature"]),
            )
        except (KeyError, ValueError) as exc:
            raise EffectDeliveryError(f"receiver response malformed: {exc}") from exc
