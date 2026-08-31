"""Dev/offline filesystem-backed ``ActionIntentStore`` for the deadline hero (#176).

This is a single-process/dev artifact. It is NOT cross-instance durable: Cloud Run
instances have container-local filesystems, so this must never back the deployed
hero. Prefer :class:`FirestoreActionIntentStore` for shared durable state. It is
kept only so offline/adversarial tests can exercise the store boundary without a
cloud SDK.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from ngabo.application.enums.intent_state import IntentState
from ngabo.application.value_objects.effect_delivery import EffectDelivery
from ngabo.application.value_objects.hero_action_intent import HeroActionIntent
from ngabo.application.value_objects.intent_reservation import IntentReservation


class FileActionIntentStore:
    """Durable intent/outbox boundary backed by one JSON file per logical action."""

    def __init__(self, root: Path) -> None:
        if not isinstance(root, Path):
            raise TypeError("root must be a pathlib.Path")
        root.mkdir(parents=True, exist_ok=True)
        self._root = root

    def _path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self._root / f"{digest}.json"

    def reserve(self, intent: HeroActionIntent) -> IntentReservation:
        path = self._path(intent.idempotency_key)
        desired = _record(intent, IntentState.DISPATCHED, None)
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            # Duplicate logical action: read the existing durable record.
            return IntentReservation(
                intent=intent,
                state=_read_state(path),
                owned=False,
            )
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(desired)
        return IntentReservation(
            intent=intent, state=IntentState.DISPATCHED, owned=True
        )

    def record_state(
        self,
        intent: HeroActionIntent,
        state: IntentState,
        delivery: EffectDelivery | None = None,
    ) -> None:
        path = self._path(intent.idempotency_key)
        path.write_text(_record(intent, state, delivery), encoding="utf-8")


def _record(
    intent: HeroActionIntent,
    state: IntentState,
    delivery: EffectDelivery | None,
) -> str:
    document: dict[str, object] = {
        "action_id": intent.action_id,
        "idempotency_key": intent.idempotency_key,
        "incident_id": intent.incident_id.value,
        "incident_version": intent.incident_version.value,
        "source_watermark": intent.source_watermark.value,
        "verified_package_id": intent.verified_package_id,
        "action_class": intent.action_class.value,
        "authorized_target_id": intent.authorized_target_id,
        "payload_hash": intent.payload_hash,
        "synthetic": intent.synthetic,
        "state": state.value,
        "delivery": delivery.to_primitive() if delivery is not None else None,
    }
    return json.dumps(document, sort_keys=True, separators=(",", ":"))


def _read_state(path: Path) -> IntentState:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return IntentState(data["state"])
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"corrupt intent record at {path}: {exc}") from exc
