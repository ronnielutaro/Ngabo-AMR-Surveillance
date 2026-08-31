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

import os
from typing import Final, Protocol, runtime_checkable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ngabo.application.value_objects.investigation_execution import (
    EventInvestigationCommand,
)
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


@app.post("/surveillance", response_model=dict[str, object], summary="Run the canonical hero")
def run_surveillance(payload: dict[str, object]) -> dict[str, object]:
    """Accept one governed synthetic surveillance event and run the canonical hero.

    This is the deployed ingress seam: it builds an ``EventInvestigationCommand``
    from the typed payload and invokes ``HeroComposition.execute``, which runs the
    existing #54 -> #55 -> #56 -> #176 hero chain. It owns no scientific policy or
    model authority and fails closed on any stage.
    """
    command = EventInvestigationCommand.from_primitive(payload)
    result = _hero().execute(command)
    return _sanitized_hero_result(result)


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
