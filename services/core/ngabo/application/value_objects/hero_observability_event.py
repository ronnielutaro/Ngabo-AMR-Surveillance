"""Sanitized, secret-free hero observability event (#176).

Every stage of the canonical hero emits one structured event keyed by the same
incident id. The model identifier, model-call counts, agent/session/invocation
ids, evidence refs, verification outcome, action/delivery/ack ids and zero-human
counters are exposed; secrets, credentials and private chain-of-thought are NOT.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def _require_nonblank(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected non-blank text")
    return value


@dataclass(frozen=True)
class HeroObservabilityEvent:
    """One sanitized hero stage event."""

    event_name: str
    incident_id: str
    execution_id: str | None = None
    stage_fields: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_nonblank(self.event_name, "event name")
        _require_nonblank(self.incident_id, "incident id")
        if self.execution_id is not None and (
            not isinstance(self.execution_id, str) or not self.execution_id.strip()
        ):
            raise ValueError("execution_id must be non-blank text or None")
        if not isinstance(self.stage_fields, dict):
            raise ValueError("stage_fields must be a dict")

    def to_primitive(self) -> dict[str, object]:
        return {
            "event": self.event_name,
            "incident_id": self.incident_id,
            "execution_id": self.execution_id,
            **self.stage_fields,
        }
