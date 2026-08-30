"""Tests for Issue #91 guarded delivery/promotion/rollback helpers."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from infra.github import delivery

CORE_DIGEST = "sha256:" + "a" * 64
WEB_DIGEST = "sha256:" + "b" * 64
COMMIT = "4befd8107ab956800c249caba5a8e4e64ea5f4a6"


class DeliveryHelpersTest(unittest.TestCase):
    def test_affected_services_core_only(self) -> None:
        self.assertEqual(
            delivery.affected_services(["services/core/ngabo/interfaces/http.py"]),
            ["core"],
        )

    def test_affected_services_web_only(self) -> None:
        self.assertEqual(
            delivery.affected_services(["apps/web/src/app/page.tsx"]),
            ["web"],
        )

    def test_affected_services_shared_returns_both(self) -> None:
        self.assertEqual(
            delivery.affected_services(["infra/gcp/cloudrun.py"]),
            ["core", "web"],
        )
        self.assertEqual(
            delivery.affected_services([".github/workflows/delivery-develop.yml"]),
            ["core", "web"],
        )

    def test_affected_services_docs_only_is_empty(self) -> None:
        self.assertEqual(delivery.affected_services(["docs/IMPLEMENTATION_PLAN.md"]), [])

    def test_affected_services_mixed(self) -> None:
        self.assertEqual(
            delivery.affected_services(
                ["services/core/Dockerfile", "apps/web/src/app/page.tsx", "README.md"]
            ),
            ["core", "web"],
        )

    def test_validate_digest(self) -> None:
        self.assertTrue(delivery.validate_digest(CORE_DIGEST))
        self.assertFalse(delivery.validate_digest("latest"))
        self.assertFalse(delivery.validate_digest("sha256:1234"))
        self.assertFalse(delivery.validate_digest(""))

    def test_is_stale(self) -> None:
        self.assertFalse(delivery.is_stale(COMMIT, COMMIT))
        self.assertTrue(delivery.is_stale(COMMIT, "0" * 40))

    def test_write_evidence_roundtrip(self) -> None:
        record = {
            "environment": "dev",
            "commit_sha": COMMIT,
            "workflow_run_id": "123",
            "actor": "ronnielutaro",
            "timestamp": "2026-08-30T14:00:00Z",
            "core_digest": CORE_DIGEST,
            "web_digest": WEB_DIGEST,
            "core_revision": "ngabo-core-00002-sgk",
            "web_revision": "ngabo-web-00002-st4",
            "smoke_result": "pass",
            "previous_known_good": {"core_digest": "sha256:" + "c" * 64},
        }
        out = Path("delivery-test-evidence.json")
        try:
            delivery.write_evidence(record, str(out))
            loaded = delivery.load_evidence(str(out))
        finally:
            out.unlink(missing_ok=True)
        self.assertEqual(loaded["core_digest"], CORE_DIGEST)
        self.assertEqual(loaded["previous_known_good"]["core_digest"], "sha256:" + "c" * 64)

    def test_evidence_sanitizes_secrets(self) -> None:
        record = {
            "environment": "release",
            "commit_sha": COMMIT,
            "workflow_run_id": "5",
            "actor": "ronnielutaro",
            "timestamp": "2026-08-30T14:00:00Z",
            "core_digest": CORE_DIGEST,
            "access_token": "gho_secretvalue",
            "naive": "text AKIA secret",
        }
        out = Path("delivery-test-evidence.json")
        try:
            delivery.write_evidence(record, str(out))
            loaded = json.loads(out.read_text(encoding="utf-8"))
        finally:
            out.unlink(missing_ok=True)
        self.assertNotIn("access_token", loaded)
        self.assertEqual(loaded["naive"], "<redacted>")

    def test_evidence_rejects_missing_required(self) -> None:
        with self.assertRaises(delivery.DeliveryError):
            delivery.write_evidence({"environment": "dev"}, "unused.json")

    def test_previous_known_good(self) -> None:
        evidence = {
            "previous_known_good": {"core_digest": "sha256:" + "d" * 64, "web_digest": WEB_DIGEST}
        }
        self.assertEqual(delivery.previous_known_good(evidence, "core"), "sha256:" + "d" * 64)
        self.assertIsNone(delivery.previous_known_good({}, "core"))
        self.assertIsNone(delivery.previous_known_good(evidence, "missing"))

    def test_evidence_check_accepts_matching_successful_record(self) -> None:
        record = {
            "environment": "dev",
            "commit_sha": COMMIT,
            "workflow_run_id": "7",
            "actor": "ronnielutaro",
            "timestamp": "2026-08-30T14:00:00Z",
            "core_digest": CORE_DIGEST,
            "web_digest": WEB_DIGEST,
            "smoke_result": "pass",
        }
        out = Path("delivery-test-evidence.json")
        try:
            delivery.write_evidence(record, str(out))
            loaded = delivery.load_evidence(str(out))
        finally:
            out.unlink(missing_ok=True)
        delivery.evidence_check(loaded, CORE_DIGEST, WEB_DIGEST)
        with self.assertRaises(delivery.DeliveryError):
            delivery.evidence_check(loaded, "sha256:" + "e" * 64, WEB_DIGEST)

    def test_rollback_check_accepts_recorded_previous_good(self) -> None:
        prev_core = "sha256:" + "c" * 64
        prev_web = "sha256:" + "d" * 64
        record = {
            "environment": "dev",
            "commit_sha": COMMIT,
            "workflow_run_id": "8",
            "actor": "ronnielutaro",
            "timestamp": "2026-08-30T15:00:00Z",
            "core_digest": CORE_DIGEST,
            "web_digest": WEB_DIGEST,
            "smoke_result": "pass",
            "previous_known_good": {"core_digest": prev_core, "web_digest": prev_web},
        }
        out = Path("delivery-test-evidence.json")
        try:
            delivery.write_evidence(record, str(out))
            loaded = delivery.load_evidence(str(out))
        finally:
            out.unlink(missing_ok=True)
        delivery.rollback_check(loaded, prev_core, prev_web)
        with self.assertRaises(delivery.DeliveryError):
            delivery.rollback_check(loaded, CORE_DIGEST, WEB_DIGEST)


if __name__ == "__main__":
    unittest.main()
