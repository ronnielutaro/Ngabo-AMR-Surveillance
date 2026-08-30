"""Tests for the FastAPI HTTP adapter (Issue #90)."""

from __future__ import annotations

import os
import unittest

from fastapi.testclient import TestClient

from ngabo.interfaces.http import app

VALID_DIGEST = "sha256:" + "a" * 64


class HttpAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env = dict(os.environ)
        # Deterministic metadata for the /version contract.
        os.environ["NGABO_SERVICE_VERSION"] = "0.1.0"
        os.environ["NGABO_SOURCE_REVISION"] = "a" * 40
        os.environ["NGABO_ENVIRONMENT"] = "test"
        os.environ["NGABO_IMAGE_DIGEST"] = VALID_DIGEST
        self.client = TestClient(app)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    def test_health_returns_ok_payload(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "service": "ngabo-core",
                "version": "0.1.0",
                "revision": "a" * 40,
            },
        )

    def test_root_alias_returns_health(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_ready_returns_ready_true(self) -> None:
        response = self.client.get("/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertTrue(response.json()["ready"])

    def test_version_returns_full_runtime_identity(self) -> None:
        response = self.client.get("/version")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "service": "ngabo-core",
                "version": "0.1.0",
                "revision": "a" * 40,
                "environment": "test",
                "image_digest": VALID_DIGEST,
            },
        )

    def test_version_omits_missing_digest(self) -> None:
        os.environ.pop("NGABO_IMAGE_DIGEST", None)
        response = self.client.get("/version")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("image_digest", response.json())

    def test_version_omits_malformed_digest(self) -> None:
        os.environ["NGABO_IMAGE_DIGEST"] = "latest"
        response = self.client.get("/version")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("image_digest", response.json())

    def test_version_omits_non_sha_digest(self) -> None:
        os.environ["NGABO_IMAGE_DIGEST"] = "sha256:nothex"
        response = self.client.get("/version")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("image_digest", response.json())

    def test_unknown_path_returns_typed_404(self) -> None:
        response = self.client.get("/definitely-not-a-route")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "not_found")


if __name__ == "__main__":
    unittest.main()
