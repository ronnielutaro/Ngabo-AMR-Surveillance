"""Tests for the minimal stdlib HTTP adapter (Issue #90)."""

from __future__ import annotations

import json
import os
import threading
import unittest
from http.client import HTTPConnection
from typing import Any

from ngabo.interfaces.http import serve

HOST = "127.0.0.1"


class HttpAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env = dict(os.environ)
        # Deterministic metadata for the /version contract.
        os.environ["NGABO_SERVICE_VERSION"] = "0.1.0"
        os.environ["NGABO_SOURCE_REVISION"] = "a" * 40
        os.environ["NGABO_ENVIRONMENT"] = "test"

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    @staticmethod
    def _start_server() -> tuple[threading.Thread, int]:
        """Start the adapter on an ephemeral port; return (thread, port)."""
        import socket

        probe = socket.socket()
        probe.bind((HOST, 0))
        port = probe.getsockname()[1]
        probe.close()

        # serve() reads PORT from the environment; bind the chosen port.
        old = os.environ.get("PORT")
        os.environ["PORT"] = str(port)
        thread = threading.Thread(
            target=serve, kwargs={"host": HOST, "port": port}, daemon=True
        )
        thread.start()
        if old is None:
            os.environ.pop("PORT", None)
        else:
            os.environ["PORT"] = old
        return thread, port

    @staticmethod
    def _get(port: int, path: str) -> tuple[int, dict[str, Any]]:
        conn = HTTPConnection(HOST, port, timeout=5)
        conn.request("GET", path)
        response = conn.getresponse()
        body = json.loads(response.read().decode("utf-8"))
        conn.close()
        return response.status, body

    def test_health_returns_ok_payload(self) -> None:
        thread, port = self._start_server()
        try:
            status, body = self._get(port, "/health")
            self.assertEqual(status, 200)
            self.assertEqual(body["status"], "ok")
            self.assertEqual(body["service"], "ngabo-core")
            self.assertEqual(body["version"], "0.1.0")
            self.assertEqual(body["revision"], "a" * 40)
        finally:
            thread.join(timeout=2)

    def test_root_alias_returns_health(self) -> None:
        thread, port = self._start_server()
        try:
            status, body = self._get(port, "/")
            self.assertEqual(status, 200)
            self.assertEqual(body["status"], "ok")
        finally:
            thread.join(timeout=2)

    def test_ready_returns_ready_true(self) -> None:
        thread, port = self._start_server()
        try:
            status, body = self._get(port, "/ready")
            self.assertEqual(status, 200)
            self.assertEqual(body["status"], "ok")
            self.assertTrue(body["ready"])
        finally:
            thread.join(timeout=2)

    def test_version_returns_service_identity(self) -> None:
        thread, port = self._start_server()
        try:
            status, body = self._get(port, "/version")
            self.assertEqual(status, 200)
            self.assertEqual(
                body,
                {
                    "service": "ngabo-core",
                    "version": "0.1.0",
                    "revision": "a" * 40,
                    "environment": "test",
                },
            )
        finally:
            thread.join(timeout=2)

    def test_unknown_path_returns_typed_404(self) -> None:
        thread, port = self._start_server()
        try:
            status, body = self._get(port, "/definitely-not-a-route")
            self.assertEqual(status, 404)
            self.assertEqual(body["error"], "not_found")
        finally:
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
