"""Framework-free safe synthetic coordination payload for the deadline hero (#176).

The payload is explicitly labelled synthetic/demo. Its ``sha256`` is the payload
hash bound to the immutable action intent; both the intent and the receiver ack
carry the same hash so a tampered payload is detected.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

# Reject the prohibited authority concepts in ordinary spaced/inflected form
# (not only internal enum-like tokens), scoped to the narrative payload so the
# #56 false-positive bug is not recreated.
# Reject the prohibited authority concepts in ordinary spaced/inflected form
# (not only internal enum-like tokens), scoped to the narrative payload so the
# #56 false-positive bug is not recreated. Stems match at a word boundary with no
# trailing boundary; phrases match the whole phrase with a trailing boundary.
_A1_FORBIDDEN_RE = re.compile(
    r"(?:\b(?:diagnos|prescrib|treat|authoriz|approv|verif))"
    r"|(?:\b(?:"
    r"outbreak\s+(?:is\s+)?confirmed"
    r"|confirm(?:ed)?\s+(?:(?:an?|the)\s+)?outbreak"
    r"|declare[ds]?\s+(?:an?\s+)?outbreak"
    r"|outbreak\s+declaration|outbreak_confirmed"
    r"|mandatory\s+containment|containment\s+order|mandatory_containment"
    r"|official\s+public\s+health\s+(?:declaration|declar)"
    r"|public\s+health\s+declaration"
    r"|notify\s+(?:the\s+)?(?:hospital|health\s+department|facility)"
    r"|action_ready|acknowledged"
    r"|send\s+samples\s+for\s+(?:treatment|testing)"
    r")\b)",
    re.I,
)


def _require_nonblank(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected non-blank text")
    return value


@dataclass(frozen=True)
class HeroCoordinationPayload:
    """Safe, draft-only, explicitly-synthetic coordination message."""

    incident_id: str
    action_class: str
    message: str
    synthetic: bool = True

    def __post_init__(self) -> None:
        _require_nonblank(self.incident_id, "incident id")
        _require_nonblank(self.action_class, "action class")
        _require_nonblank(self.message, "coordination message")
        if not self.synthetic:
            raise ValueError("the deadline hero payload must be synthetic=true")

    def to_primitive(self) -> dict[str, object]:
        return {
            "incident_id": self.incident_id,
            "action_class": self.action_class,
            "message": self.message,
            "synthetic": self.synthetic,
        }

    def payload_hash(self) -> str:
        canonical = json.dumps(
            self.to_primitive(), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()


def validate_coordination_message(message: str) -> tuple[bool, str | None]:
    """Deterministically reject unsafe authority wording in the A1 payload."""
    if not isinstance(message, str):
        return False, "coordination message must be text"
    if not message.strip():
        return False, "coordination message must be non-blank"
    if _A1_FORBIDDEN_RE.search(message):
        return False, "coordination message contains forbidden authority wording"
    return True, None
