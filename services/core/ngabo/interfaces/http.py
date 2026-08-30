"""Minimal stdlib HTTP adapter for the ngabo-core skeleton (Issue #90).

Cloud Run requires a listening HTTP service; the core is intentionally
framework-free (no FastAPI/uvicorn) so the production image gains no
runtime dependencies. This adapter uses only :mod:`http.server` and serves
typed JSON endpoints:

- ``GET /health``  — liveness: status/service/version/revision.
- ``GET /ready``   — readiness: same payload plus ``ready: true``.
- ``GET /version`` — service identity metadata (service/version/revision/
  environment) consumed by the web console's live-status panel.

Contract: no domain or application logic lives here; the adapter only
forwards the bootstrap ``health()`` payload and environment metadata.
Unknown paths return a typed 404 JSON body (never an HTML error page).

Entry point ``ngabo-http`` (see pyproject ``[project.scripts]``) binds
``0.0.0.0:$PORT`` (Cloud Run convention; default 8080).
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Final

from ngabo.bootstrap.health import health

SERVICE_NAME: Final[str] = "ngabo-core"
DEFAULT_PORT: Final[int] = 8080
DEFAULT_ENVIRONMENT: Final[str] = "development"

_STATUS_OK: Final[str] = "ok"
_CONTENT_TYPE: Final[tuple[str, str]] = ("Content-Type", "application/json; charset=utf-8")
_NO_STORE: Final[tuple[str, str]] = ("Cache-Control", "no-store")


def _environment() -> str:
    return os.environ.get("NGABO_ENVIRONMENT", DEFAULT_ENVIRONMENT)


def _version_payload() -> dict[str, str]:
    return {
        "service": SERVICE_NAME,
        "version": os.environ.get("NGABO_SERVICE_VERSION", "0.1.0"),
        "revision": os.environ.get("NGABO_SOURCE_REVISION", "unknown"),
        "environment": _environment(),
    }


def _ready_payload() -> dict[str, str | bool]:
    payload: dict[str, str | bool] = dict(health())
    payload["ready"] = True
    return payload


class NgaboHttpHandler(BaseHTTPRequestHandler):
    """Serves the typed health/ready/version endpoints for the skeleton."""

    server_version = f"ngabo-http/0.1.0 ({SERVICE_NAME})"

    # Silence per-request logging noise; Cloud Run surfaces structured logs
    # via stdout/stderr at the process level.
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass

    def _send_json(self, status: int, payload: Mapping[str, object]) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header(*_CONTENT_TYPE)
        self.send_header(*_NO_STORE)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in ("/", "/health"):
            self._send_json(200, dict(health()))
        elif self.path == "/ready":
            self._send_json(200, _ready_payload())
        elif self.path == "/version":
            self._send_json(200, _version_payload())
        else:
            self._send_json(404, {"status": "error", "error": "not_found"})


def serve(host: str = "0.0.0.0", port: int | None = None) -> None:
    """Run the skeleton HTTP server until interrupted."""
    bound_port = port if port is not None else int(
        os.environ.get("PORT", str(DEFAULT_PORT))
    )
    server = ThreadingHTTPServer((host, bound_port), NgaboHttpHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    """Console entry point ``ngabo-http``."""
    port = int(os.environ.get("PORT", str(DEFAULT_PORT)))
    serve(port=port)


if __name__ == "__main__":
    main()
