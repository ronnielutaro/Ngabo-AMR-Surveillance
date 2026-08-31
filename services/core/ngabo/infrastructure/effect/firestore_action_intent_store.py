"""Shared durable Firestore-backed ``ActionIntentStore`` for the deadline hero (#176).

This is the deployment adapter. Cloud Run instances have container-local
filesystems, so the file-backed store is NOT cross-instance durable; Firestore
document create gives an atomic create-if-absent uniqueness keyed by the logical
idempotency digest, so two concurrent dispatchers of the same logical action
cannot both acquire the lease. The Google Cloud SDK is imported lazily inside the
methods so the framework-free application/tests never require the SDK.

Deadline note: the demo path uses the real Firestore doc-create for deterministic
logical idempotency and persisted-before-effect semantics. Full transactional
outbox recovery, distributed dispatcher hardening and asynchronous callback
lifecycle remain #67/#69/#70.
"""

from __future__ import annotations

import hashlib
import json
import time

from ngabo.application.enums.intent_state import IntentState
from ngabo.application.value_objects.effect_delivery import EffectDelivery
from ngabo.application.value_objects.hero_action_intent import HeroActionIntent
from ngabo.application.value_objects.intent_reservation import IntentReservation


class FirestoreActionIntentStore:
    """Shared durable intent/outbox boundary backed by Firestore docs."""

    def __init__(self, *, project: str, collection: str = "ngabo_action_intents") -> None:
        from google.cloud import firestore  # type: ignore[import-untyped]  # lazy: deploy-only

        self._project = project
        self._collection = collection
        self._db = firestore.Client(project=project)
        self._col = self._db.collection(collection)

    def _doc_id(self, idempotency_key: str) -> str:
        return hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()

    def reserve(
        self,
        intent: HeroActionIntent,
        *,
        lease_ttl_seconds: float = 30.0,
        max_retries: int = 2,
        now: float | None = None,
    ) -> IntentReservation:
        current = now if now is not None else time.monotonic()
        deadline = current + lease_ttl_seconds
        from google.api_core.exceptions import (  # type: ignore[import-untyped]
            AlreadyExists,
        )

        doc = self._col.document(self._doc_id(intent.idempotency_key))
        data = _record(intent, IntentState.DISPATCHED, None, deadline, 0)
        try:
            # Atomic create-if-absent: only one instance can create the doc.
            doc.create(data)
            return IntentReservation(
                intent=intent, state=IntentState.DISPATCHED, owned=True
            )
        except AlreadyExists:
            snap = doc.get()
            record = snap.to_dict() or {}
            state = IntentState(record.get("state", IntentState.DISPATCHED.value))
            lease_expires = float(record.get("lease_expires_at", 0.0))
            retries = int(record.get("retries", 0))
            stateless = state in (IntentState.PENDING, IntentState.RETRYABLE)
            lease_expired = state is IntentState.DISPATCHED and current > lease_expires
            if (stateless or lease_expired) and retries < max_retries:
                # Reacquire the SAME logical intent + idempotency key within a
                # bounded lease/retry budget. This is a best-effort CAS via doc.set;
                # production hardening under #67/#69 would use a transaction.
                doc.set(
                    _record(
                        intent,
                        IntentState.DISPATCHED,
                        None,
                        deadline,
                        retries + 1 if state is IntentState.RETRYABLE else retries,
                    )
                )
                return IntentReservation(
                    intent=intent, state=IntentState.DISPATCHED, owned=True
                )
            if state is IntentState.RETRYABLE and retries >= max_retries:
                doc.set(_record(intent, IntentState.FAILED, None, 0.0, retries))
                return IntentReservation(
                    intent=intent, state=IntentState.FAILED, owned=False
                )
            return IntentReservation(intent=intent, state=state, owned=False)

    def record_state(
        self,
        intent: HeroActionIntent,
        state: IntentState,
        delivery: EffectDelivery | None = None,
    ) -> None:
        doc = self._col.document(self._doc_id(intent.idempotency_key))
        snap = doc.get()
        record = snap.to_dict() or {}
        doc.set(
            _record(
                intent,
                state,
                delivery,
                float(record.get("lease_expires_at", 0.0)),
                int(record.get("retries", 0)),
            )
        )


def _record(
    intent: HeroActionIntent,
    state: IntentState,
    delivery: EffectDelivery | None,
    lease_expires_at: float | None = None,
    retries: int = 0,
) -> dict[str, object]:
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
        "delivery": json.dumps(
            delivery.to_primitive(), sort_keys=True, separators=(",", ":")
        )
        if delivery is not None
        else None,
    }
    return document
