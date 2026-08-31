"""Immutable, framework-free autonomous action intent for the deadline hero (#176).

``HeroActionIntent`` is the deterministic record of ONE authorized safe
synthetic external coordination action. It is created BEFORE the external send,
carries a stable idempotency key, a deterministic payload hash, and the
incident/version/watermark/package binding. The model never supplies the
idempotency key, the destination, or the target authorization.
"""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.domain.enums.action_class import ActionClass
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.source_watermark import SourceWatermark


def _require_nonblank(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected non-blank text")
    return value


@dataclass(frozen=True)
class HeroActionIntent:
    """Immutable intent to perform one authorized safe synthetic action."""

    action_id: str
    incident_id: IncidentId
    incident_version: IncidentVersion
    source_watermark: SourceWatermark
    verified_package_id: str
    action_class: ActionClass
    authorized_target_id: str
    payload_hash: str
    idempotency_key: str
    synthetic: bool = True

    def __post_init__(self) -> None:
        _require_nonblank(self.action_id, "action id")
        if not isinstance(self.incident_id, IncidentId):
            raise ValueError("incident_id must be an IncidentId")
        if not isinstance(self.incident_version, IncidentVersion):
            raise ValueError("incident_version must be an IncidentVersion")
        if not isinstance(self.source_watermark, SourceWatermark):
            raise ValueError("source_watermark must be a SourceWatermark")
        _require_nonblank(self.verified_package_id, "verified package id")
        if not isinstance(self.action_class, ActionClass):
            raise ValueError("action_class must be an ActionClass")
        if self.action_class is not ActionClass.SAFE_EXTERNAL_COORDINATION:
            raise ValueError("the deadline hero may only author a safe A1 action")
        _require_nonblank(self.authorized_target_id, "authorized target id")
        if len(self.payload_hash) != 64 or any(
            c not in "0123456789abcdef" for c in self.payload_hash
        ):
            raise ValueError("payload_hash must be a 64-hex sha256 digest")
        _require_nonblank(self.idempotency_key, "idempotency key")
        if not isinstance(self.synthetic, bool) or not self.synthetic:
            raise ValueError("the deadline hero payload must be synthetic=true")

    def to_primitive(self) -> dict[str, object]:
        """Return a secret-free, JSON-safe primitive."""
        return {
            "action_id": self.action_id,
            "incident_id": self.incident_id.value,
            "incident_version": self.incident_version.value,
            "source_watermark": self.source_watermark.value,
            "verified_package_id": self.verified_package_id,
            "action_class": self.action_class.value,
            "authorized_target_id": self.authorized_target_id,
            "payload_hash": self.payload_hash,
            "idempotency_key": self.idempotency_key,
            "synthetic": self.synthetic,
        }
