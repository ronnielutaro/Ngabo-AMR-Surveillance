"""Ngabo demo receiver — real external signed-ACK endpoint (#176).

Standalone Cloud Run service. It receives the deterministic A1 coordination
payload, produces a delivery identity, and returns an HMAC-SHA256 authenticated
acknowledgement matching the signature contract used by ``VerifyHeroAck`` in
ngabo-core (over ``action_id|payload_hash|delivery_id|ack_id|received_at|status``
using the shared ``NGABO_ACK_SECRET``). It never fabricates an internal success;
ngabo-core verifies the signature + correlation.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone


def _sign(secret: bytes, message: str) -> str:
    return hmac.new(secret, message.encode("utf-8"), hashlib.sha256).hexdigest()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._reply(400, {"error": "invalid json"})
            return
        action_id = payload.get("action_id", "")
        payload_hash = payload.get("payload_hash", "")
        delivery_id = "dlv-" + hashlib.sha256(
            (action_id + payload_hash).encode("utf-8")
        ).hexdigest()[:16]
        ack_id = "ack-" + hashlib.sha256(
            (delivery_id + action_id).encode("utf-8")
        ).hexdigest()[:16]
        received_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        status = "RECEIVED"
        secret = os.environ.get("NGABO_ACK_SECRET", "").encode("utf-8")
        signature = _sign(
            secret,
            "|".join(
                (action_id, payload_hash, delivery_id, ack_id, received_at, status)
            ),
        )
        self._reply(
            200,
            {
                "delivery_id": delivery_id,
                "ack_id": ack_id,
                "action_id": action_id,
                "payload_hash": payload_hash,
                "received_at": received_at,
                "status": status,
                "signature": signature,
            },
        )

    def do_GET(self) -> None:  # noqa: N802
        self._reply(200, {"status": "ok", "service": "ngabo-demo-receiver"})

    def _reply(self, code: int, body: dict[str, object]) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args: object) -> None:  # noqa: A003
        return


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
