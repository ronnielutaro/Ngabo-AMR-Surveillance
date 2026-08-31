"""Dev/offline filesystem-backed ``ActionIntentStore`` for the deadline hero (#176).

This is a single-process/dev artifact. It implements the SAME bounded
lease/retry semantics as the deployment ``FirestoreActionIntentStore`` (and the
test ``FakeActionIntentStore``) so the orchestrator contract is honored offline.
It is NOT cross-instance durable: Cloud Run instances have container-local
filesystems, so it must never back the deployed hero. The deployed hero always
uses :class:`FirestoreActionIntentStore`.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from pathlib import Path

from ngabo.application.enums.intent_state import IntentState
from ngabo.application.value_objects.effect_delivery import EffectDelivery
from ngabo.application.value_objects.hero_action_intent import HeroActionIntent
from ngabo.application.value_objects.intent_reservation import IntentReservation


class FileActionIntentStore:
    """Bounded lease/retry intent store backed by one JSON file per logical action."""

    def __init__(self, root: Path) -> None:
        if not isinstance(root, Path):
            raise TypeError("root must be a pathlib.Path")
        root.mkdir(parents=True, exist_ok=True)
        self._root = root

    def _path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self._root / f"{digest}.json"

    def reserve(
        self,
        intent: HeroActionIntent,
        *,
        lease_ttl_seconds: float = 30.0,
        max_retries: int = 2,
        now: float | None = None,
    ) -> IntentReservation:
        current = now if now is not None else time.time()
        deadline = current + lease_ttl_seconds
        path = self._path(intent.idempotency_key)
        if not path.exists():
            # Atomic single-process create: only the first caller wins.
            try:
                fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                pass
            else:
                token = "lease-" + uuid.uuid4().hex
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    fh.write(
                        _record(intent, IntentState.DISPATCHED, None, deadline, 0, token)
                    )
                return IntentReservation(
                    intent=intent,
                    state=IntentState.DISPATCHED,
                    owned=True,
                    lease_token=token,
                )
        record = _read_record(path)
        state = IntentState(str(record["state"]))
        retries_raw = record.get("retries")
        retries = int(retries_raw) if isinstance(retries_raw, int) else 0
        lease_raw = record.get("lease_expires_at")
        lease_expires = float(lease_raw) if isinstance(lease_raw, (int, float)) else 0.0
        stateless = state in (IntentState.PENDING, IntentState.RETRYABLE)
        lease_expired = state is IntentState.DISPATCHED and current > lease_expires
        if stateless or lease_expired:
            if retries < max_retries:
                token = "lease-" + uuid.uuid4().hex
                path.write_text(
                    _record(
                        intent, IntentState.DISPATCHED, None, deadline, retries + 1, token
                    ),
                    encoding="utf-8",
                )
                return IntentReservation(
                    intent=intent,
                    state=IntentState.DISPATCHED,
                    owned=True,
                    lease_token=token,
                )
            path.write_text(
                _record(
                    intent,
                    IntentState.FAILED,
                    None,
                    0.0,
                    retries,
                    (str(record.get("lease_token")) if record.get("lease_token") else None),
                ),
                encoding="utf-8",
            )
            return IntentReservation(
                intent=intent, state=IntentState.FAILED, owned=False
            )
        return IntentReservation(intent=intent, state=state, owned=False)

    def record_state(
        self,
        intent: HeroActionIntent,
        state: IntentState,
        *,
        lease_token: str,
        delivery: EffectDelivery | None = None,
    ) -> bool:
        path = self._path(intent.idempotency_key)
        record = _read_record(path)
        if record.get("lease_token") != lease_token:
            return False
        lease_raw = record.get("lease_expires_at")
        retries_raw = record.get("retries")
        lease_value = float(lease_raw) if isinstance(lease_raw, (int, float)) else 0.0
        retries_value = int(retries_raw) if isinstance(retries_raw, int) else 0
        path.write_text(
            _record(
                intent,
                state,
                delivery,
                lease_value,
                retries_value,
                (str(record.get("lease_token")) if record.get("lease_token") else None),
            ),
            encoding="utf-8",
        )
        return True


def _record(
    intent: HeroActionIntent,
    state: IntentState,
    delivery: EffectDelivery | None,
    lease_expires_at: float | None = None,
    retries: int = 0,
    lease_token: str | None = None,
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
        "lease_expires_at": lease_expires_at,
        "retries": retries,
        "lease_token": lease_token,
        "delivery": delivery.to_primitive() if delivery is not None else None,
    }
    return json.dumps(document, sort_keys=True, separators=(",", ":"))


def _read_record(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"corrupt intent record at {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"corrupt intent record at {path}: not an object")
    return data


def _read_state(path: Path) -> IntentState:
    return IntentState(str(_read_record(path)["state"]))
