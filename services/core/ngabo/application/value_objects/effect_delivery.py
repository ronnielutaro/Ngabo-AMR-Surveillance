"""Typed result of one real external effect delivery (#176)."""

from __future__ import annotations

from dataclasses import dataclass


def _require_nonblank(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected non-blank text")
    return value


@dataclass(frozen=True)
class EffectDelivery:
    """Receiver-produced delivery identity plus a signed machine acknowledgement."""

    delivery_id: str
    ack_id: str
    action_id: str
    payload_hash: str
    received_at: str
    status: str
    signature: str

    def __post_init__(self) -> None:
        _require_nonblank(self.delivery_id, "delivery id")
        _require_nonblank(self.ack_id, "ack id")
        _require_nonblank(self.action_id, "action id")
        if len(self.payload_hash) != 64 or any(
            c not in "0123456789abcdef" for c in self.payload_hash
        ):
            raise ValueError("payload_hash must be a 64-hex sha256 digest")
        _require_nonblank(self.received_at, "received_at")
        _require_nonblank(self.status, "status")
        _require_nonblank(self.signature, "ack signature")

    def to_primitive(self) -> dict[str, object]:
        return {
            "delivery_id": self.delivery_id,
            "ack_id": self.ack_id,
            "action_id": self.action_id,
            "payload_hash": self.payload_hash,
            "received_at": self.received_at,
            "status": self.status,
            "signature": self.signature,
        }
