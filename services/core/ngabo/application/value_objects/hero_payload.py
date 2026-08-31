"""Framework-free safe synthetic coordination payload for the deadline hero (#176).

The payload is explicitly labelled synthetic/demo. Its ``sha256`` is the payload
hash bound to the immutable action intent; both the intent and the receiver ack
carry the same hash so a tampered payload is detected.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


def _require_nonblank(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected non-blank text")
    return value


@dataclass(frozen=True)
class HeroCoordinationPayload:
    """Safe, draft-only, explicitly-synthetic coordination message."""

    incident_id: str
    verified_package_id: str
    action_class: str
    message: str
    synthetic: bool = True

    def __post_init__(self) -> None:
        _require_nonblank(self.incident_id, "incident id")
        _require_nonblank(self.verified_package_id, "verified package id")
        _require_nonblank(self.action_class, "action class")
        _require_nonblank(self.message, "coordination message")
        if not self.synthetic:
            raise ValueError("the deadline hero payload must be synthetic=true")

    def to_primitive(self) -> dict[str, object]:
        return {
            "incident_id": self.incident_id,
            "verified_package_id": self.verified_package_id,
            "action_class": self.action_class,
            "message": self.message,
            "synthetic": self.synthetic,
        }

    def payload_hash(self) -> str:
        canonical = json.dumps(
            self.to_primitive(), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()
