"""FastAPI HTTP adapter for the ngabo-core skeleton (Issue #90).

FastAPI is the sanctioned outer delivery mechanism (docs/SYSTEM_DESIGN.md,
docs/TECH_STACK.md): it lives in the interfaces layer, owns HTTP concerns
only, and never leaks into domain or application modules. The adapter
serves three typed endpoints backed by the framework-free contracts in
``ngabo.interfaces.health``:

- ``GET /health``  — liveness (status/service/version/revision).
- ``GET /ready``   — readiness (liveness plus ``ready: true``).
- ``GET /version`` — runtime/artifact identity (service/version/revision/
  image_digest/environment).

Routes contain no AMR business logic; they only forward the health
contracts. The production entry point ``ngabo-http`` runs uvicorn bound to
``0.0.0.0:$PORT`` (Cloud Run convention; default 8080).
"""

from __future__ import annotations

import base64
import binascii
import json
import os
from datetime import date
from typing import Final, Protocol, runtime_checkable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ngabo.application.connect.processor import process_connect_csv
from ngabo.application.enums.hero_error_code import HeroErrorCode
from ngabo.application.enums.hero_outcome import HeroOutcome
from ngabo.application.value_objects.investigation_execution import (
    EventInvestigationCommand,
)
from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.infrastructure.connect.firestore_incident_repository import (
    FirestoreInvestigationContextRepository,
    persist_batch_events,
)
from ngabo.infrastructure.connect.hmac_auth import verify_upload
from ngabo.interfaces.health import health, readiness, runtime_identity

SERVICE_NAME: Final[str] = "ngabo-core"
DEFAULT_PORT: Final[int] = 8080

app = FastAPI(
    title=f"{SERVICE_NAME} skeleton API",
    version="0.1.0",
    description=(
        "Ngabo core skeleton HTTP adapter (Issue #90): typed health, "
        "readiness, and runtime/artifact identity endpoints."
    ),
)


@runtime_checkable
class HeroCompositionProtocol(Protocol):
    """The deployed hero application seam, injected by the bootstrap layer.

    Defined here (never imported from bootstrap) so ``interfaces`` preserves the
    Clean Architecture dependency direction: interfaces never import bootstrap.
    """

    def execute(self, command: EventInvestigationCommand) -> object:
        ...


# Composition seam: set at deploy (or in tests) to a concrete HeroComposition. If
# unset, a real composition is built lazily on first /surveillance request.
hero_composition: HeroCompositionProtocol | None = None
_last_connect_batch: dict[str, object] | None = None


def configure_hero_composition(composition: HeroCompositionProtocol | None) -> None:
    """Set the deployed hero composition before serving requests (deploy/bootstrap)."""
    global hero_composition
    hero_composition = composition


def _hero() -> HeroCompositionProtocol:
    global hero_composition
    if hero_composition is None:
        # Deploy passes a real composition here; the default is deliberately null
        # so a misconfigured deployment fails closed rather than fabricating a run.
        raise RuntimeError("hero composition is not configured; deploy must inject it")
    return hero_composition


@app.get("/health", response_model=dict[str, str], summary="Liveness")
def get_health() -> dict[str, str]:
    """Liveness payload (status/service/version/revision)."""
    return health()


@app.get("/ready", response_model=dict[str, str | bool], summary="Readiness")
def get_ready() -> dict[str, str | bool]:
    """Readiness payload (liveness plus ready: true)."""
    return readiness()


@app.get("/version", response_model=dict[str, str], summary="Runtime identity")
def get_version() -> dict[str, str]:
    """Runtime/artifact identity (service/version/revision/image_digest/environment).

    ``image_digest`` is present only when a valid immutable digest was
    injected by the trusted deployment (``NGABO_IMAGE_DIGEST``); absent or
    malformed values are omitted so consumers can treat identity as
    incomplete rather than invented.
    """
    return runtime_identity()


@app.get("/", response_model=dict[str, str], summary="Root alias")
def get_root() -> dict[str, str]:
    """Root alias for the liveness payload (Cloud Run startup probe friendly)."""
    return health()


@app.post("/surveillance", summary="Run the canonical hero")
def run_surveillance(payload: dict[str, object]) -> JSONResponse:
    """Accept one governed synthetic surveillance event and run the canonical hero.

    This is the deployed ingress seam: it builds an ``EventInvestigationCommand``
    from the typed payload and invokes ``HeroComposition.execute``, which runs the
    existing #54 -> #55 -> #56 -> #176 hero chain. It owns no scientific policy or
    model authority and fails closed on any stage.

    Pub/Sub push treats HTTP 2xx as an acknowledgement (no redelivery) and
    non-2xx as a retryable failure (may redeliver). We therefore return a
    non-2xx status for a RETRYABLE hero failure (so the same logical intent +
    idempotency key is reacquired) and a 2xx status for a terminal outcome (so we
    never create an infinite redelivery loop).
    """
    try:
        command_data = _extract_command_data(payload)
        command = EventInvestigationCommand.from_primitive(command_data)
    except ValueError as exc:
        # Malformed/non-retryable command: acknowledge (2xx) so Pub/Sub does not
        # redeliver the same bad message forever.
        return JSONResponse(
            status_code=200,
            content={
                "outcome": "BLOCKED",
                "is_success": False,
                "status": "terminal",
                "error": str(exc),
            },
        )
    result = _hero().execute(command)
    return JSONResponse(
        status_code=_acknowledgement_status(result),
        content=_sanitized_hero_result(result),
    )


def _acknowledgement_status(result: object) -> int:
    """Map a hero outcome to Pub/Sub acknowledgement semantics.

    Retryable (transient) failures return non-2xx so Pub/Sub may redeliver and
    the SAME logical ActionIntent + idempotency key is reacquired. Everything
    terminal (including verification/policy/authority blocks and successful
    completion) returns 2xx so Pub/Sub acknowledges it and stops redelivering.
    """
    outcome = getattr(result, "outcome", None)
    error_code = getattr(result, "error_code", None)
    if outcome is HeroOutcome.HERO_COMPLETED:
        return 200
    if outcome is HeroOutcome.FAILED and error_code is HeroErrorCode.DELIVERY_FAILED:
        # Transient effect failure: allow Pub/Sub redelivery -> reacquire same key.
        return 503
    # Terminal outcome (verification/policy/authority block, invalid ack, etc.).
    return 200


def _extract_command_data(payload: dict[str, object]) -> dict[str, object]:
    """Decode a Google Pub/Sub push envelope (``message.data``) if present.

    Pub/Sub push delivers ``{"message":{"data":"<base64>",...}, "subscription":...}``,
    not a flat command object. The envelope is authenticated by Pub/Sub; here we
    decode the payload and fail closed on malformed/absent data.
    """
    message = payload.get("message")
    if isinstance(message, dict) and "data" in message:
        encoded = message["data"]
        if not isinstance(encoded, str) or not encoded:
            raise ValueError("Pub/Sub envelope message.data is missing/invalid")
        try:
            decoded = base64.b64decode(encoded).decode("utf-8")
            data = json.loads(decoded)
        except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
            raise ValueError(f"Pub/Sub envelope data is not valid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("Pub/Sub envelope data must decode to a JSON object")
        return data
    return payload


def _sanitized_hero_result(result: object) -> dict[str, object]:
    error_code = getattr(result, "error_code", None)
    out: dict[str, object] = {
        "outcome": getattr(result, "outcome", None),
        "is_success": getattr(getattr(result, "outcome", None), "is_success", False),
        "execution_id": getattr(result, "execution_id", None),
        "error_code": (
            error_code.value if error_code is not None else None
        ),
        "ack_verified": getattr(result, "ack_verified", False),
        "zero_human": getattr(result, "zero_human", {}),
        "events": tuple(
            {
                "event": evt.event_name,
                "incident_id": evt.incident_id,
                "execution_id": evt.execution_id,
            }
            for evt in getattr(result, "events", ())
        ),
    }
    intent = getattr(result, "intent", None)
    if intent is not None:
        out["action_id"] = intent.action_id
        out["payload_hash"] = getattr(intent, "payload_hash", None)
        out["idempotency_key"] = intent.idempotency_key
    delivery = getattr(result, "delivery", None)
    if delivery is not None:
        out["delivery_id"] = delivery.delivery_id
        out["ack_id"] = delivery.ack_id
    return out


@app.post("/connect/batches", summary="Ingest one governed synthetic export batch")
def ingest_connect_batch(request: Request) -> JSONResponse:
    """Receive a raw CSV export (HMAC-signed), clean it, and hand off to the hero."""
    body = _read_body(request)
    lab_id = request.headers.get("X-Ngabo-Lab-Id", "")
    source_id = request.headers.get("X-Ngabo-Source-Id", "")
    secret = os.environ.get("NGABO_HMAC_SECRET", "demo-secret").encode("utf-8")
    headers = dict(request.headers.items())
    ok, err = verify_upload(
        headers=headers,
        body=body,
        secret=secret,
        configured_lab_ids={"synthetic-lab-gulu"},
        configured_source_ids={"whonet-demo"},
    )
    if not ok:
        return JSONResponse(status_code=400, content={"status": "rejected", "error": err})
    project = os.environ.get("NGABO_GCP_PROJECT", "")

    def _persist(incident_id: str, isolates: list[CanonicalIsolate]) -> None:
        if not project:
            return
        repo = FirestoreInvestigationContextRepository(project=project)

        repo.persist_incident(
            incident_id=incident_id,
            incident_version=1,
            source_watermark=f"connect/{lab_id}/{source_id}/v1",
            window_end=_parsed_window_end(),
            isolates=isolates,
            profile_pair=_isolate_pair(),
        )

    try:
        batch = process_connect_csv(
            body,
            lab_id=lab_id,
            source_id=source_id,
            window_end_iso=os.environ.get("NGABO_SURVEILLANCE_WINDOW_END", "2026-08-31"),
            execute_hero=_run_connect_hero,
            persist_isolates=_persist,
        )
        if project and batch.get("signal_id"):
            persist_batch_events(
                project=project, batch_id=str(batch["signal_id"]), payload=batch
            )
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=500, content={"status": "processing_failed", "error": str(exc)}
        )
    global _last_connect_batch
    _last_connect_batch = batch
    return JSONResponse(status_code=200, content=batch)


@app.get("/connect/status", summary="Latest connect batch status for the web UI")
def connect_status() -> dict[str, object]:
    return _last_connect_batch or {"status": "none"}


def _run_connect_hero(command: dict[str, object]) -> dict[str, object]:
    parsed = EventInvestigationCommand.from_primitive(command)
    return _sanitized_hero_result(_hero().execute(parsed))


def _read_body(request: Request) -> bytes:
    import asyncio

    return asyncio.run(request.body())


def _parsed_window_end() -> date:
    return date.fromisoformat(os.environ.get("NGABO_SURVEILLANCE_WINDOW_END", "2026-08-31"))


def _isolate_pair() -> tuple[str, str] | None:
    value = os.environ.get("NGABO_PROFILE_PAIR")
    if not value:
        return None
    parts = value.split(",")
    return (parts[0], parts[1]) if len(parts) == 2 else None


@app.exception_handler(404)
async def not_found_handler(_request: Request, _exc: Exception) -> JSONResponse:
    """Typed JSON 404 instead of an HTML error page."""
    return JSONResponse(status_code=404, content={"status": "error", "error": "not_found"})


def serve(host: str = "0.0.0.0", port: int | None = None) -> None:
    """Run the uvicorn production ASGI server on ``0.0.0.0:$PORT``."""
    import uvicorn

    bound_port = port if port is not None else int(
        os.environ.get("PORT", str(DEFAULT_PORT))
    )
    uvicorn.run(app, host=host, port=bound_port, log_level="info")


def main() -> None:
    """Console entry point ``ngabo-http`` (Cloud Run $PORT convention)."""
    port = int(os.environ.get("PORT", str(DEFAULT_PORT)))
    serve(port=port)


if __name__ == "__main__":
    main()
