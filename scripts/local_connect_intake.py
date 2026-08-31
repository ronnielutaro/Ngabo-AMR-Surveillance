"""Local Connect intake echo for testing the desktop app (no GCP needed).

Accepts a POST /connect/batches from the desktop client, verifies the HMAC + SHA-256
(same contract as ngabo-core), and returns RAW_BATCH_ACCEPTED. GET /connect/status
returns the last batch. Bind it before the desktop app.

  python scripts/local_connect_intake.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "core"))

from ngabo.infrastructure.connect.hmac_auth import verify_upload  # noqa: E402

SECRET = os.environ.get("NGABO_HMAC_SECRET", "demo-secret").encode("utf-8")
LAST: dict[str, object] = {}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/connect/batches":
            self._reply(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        ok, err = verify_upload(
            headers={k: v for k, v in self.headers.items()},
            body=body,
            secret=SECRET,
            configured_lab_ids={"synthetic-lab-gulu"},
            configured_source_ids={"whonet-demo"},
        )
        if not ok:
            self._reply(400, {"status": "rejected", "error": err})
            return
        sha256 = self.headers.get("X-Ngabo-Content-SHA256", "")
        rows = body.decode("utf-8").count("\n")
        global LAST
        LAST = {
            "status": "RAW_BATCH_ACCEPTED",
            "file_sha256": sha256,
            "bytes_received": len(body),
            "rows": rows,
            "lab_id": self.headers.get("X-Ngabo-Lab-Id", ""),
            "source_id": self.headers.get("X-Ngabo-Source-Id", ""),
        }
        self._reply(200, LAST)

    def do_GET(self) -> None:  # noqa: N802
        self._reply(200, LAST or {"status": "none"})

    def _reply(self, code: int, payload: dict[str, object]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args: object) -> None:  # noqa: A003
        return


def main() -> None:
    print("Local Ngabo Connect intake on http://127.0.0.1:8099/connect/batches")
    HTTPServer(("127.0.0.1", 8099), Handler).serve_forever()


if __name__ == "__main__":
    main()
