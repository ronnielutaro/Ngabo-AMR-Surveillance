"""Machine-verifiable acknowledgement verification for the deadline hero (#176).

The acknowledgement MUST come from the receiver, not a timer, UI click, internal
fake, or bare HTTP 200. For this deadline slice the receiver returns an
authenticated synchronous response: a ``HMAC-SHA256`` signature over the
receiver-produced correlation identity (action_id, payload_hash, delivery_id,
ack_id, received_at, status) using configured secret material. ngabo-core
recomputes and compares the signature and checks the correlation fields.
"""

from __future__ import annotations

import hashlib
import hmac

from ngabo.application.enums.hero_error_code import HeroErrorCode
from ngabo.application.value_objects.effect_delivery import EffectDelivery
from ngabo.application.value_objects.hero_action_intent import HeroActionIntent


def _hmac_signature(secret: bytes, message: bytes) -> str:
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


class VerifyHeroAck:
    """Verify a receiver-produced signed acknowledgement against the intent."""

    _ACCEPTED_STATUSES = frozenset({"RECEIVED", "ACKNOWLEDGED", "OK"})

    def __init__(self, *, ack_secret: str) -> None:
        if not isinstance(ack_secret, str) or not ack_secret.strip():
            raise ValueError("ack_secret must be non-blank configured secret material")
        self._secret = ack_secret.encode("utf-8")

    @classmethod
    def canonical_message(
        cls,
        delivery: EffectDelivery,
    ) -> bytes:
        return "|".join(
            (
                delivery.action_id,
                delivery.payload_hash,
                delivery.delivery_id,
                delivery.ack_id,
                delivery.received_at,
                delivery.status,
            )
        ).encode("utf-8")

    def verify(
        self,
        intent: HeroActionIntent,
        delivery: EffectDelivery,
    ) -> tuple[bool, HeroErrorCode | None, str]:
        if delivery.action_id != intent.action_id:
            return (
                False,
                HeroErrorCode.ACK_CORRELATION_MISMATCH,
                "ack action_id does not match the intent",
            )
        if delivery.payload_hash != intent.payload_hash:
            return (
                False,
                HeroErrorCode.ACK_CORRELATION_MISMATCH,
                "ack payload_hash does not match the intent",
            )
        if delivery.status not in self._ACCEPTED_STATUSES:
            return (
                False,
                HeroErrorCode.ACK_INVALID,
                f"ack status {delivery.status!r} is not a success status",
            )
        expected = _hmac_signature(self._secret, self.canonical_message(delivery))
        if not hmac.compare_digest(expected, delivery.signature):
            return (
                False,
                HeroErrorCode.ACK_SIGNATURE_INVALID,
                "ack signature does not verify",
            )
        return True, None, "ack correlation + signature verified"
