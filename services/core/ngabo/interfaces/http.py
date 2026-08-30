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
from typing import Final

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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
