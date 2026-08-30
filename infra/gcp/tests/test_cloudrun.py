"""Tests for infra/gcp/cloudrun.py — Cloud Run desired-state tooling (Issue #90)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

MODULE_DIR = Path(__file__).parents[1]
sys.path.insert(0, str(MODULE_DIR))

from infra.gcp.cloudrun import artifact_uri, desired_services  # noqa: E402
from infra.gcp.config import DEFAULT_PROJECT_ID, PRIMARY_REGION  # noqa: E402

CORE_DIGEST = "sha256:" + "a" * 64
WEB_DIGEST = "sha256:" + "b" * 64


class DesiredStateTests(unittest.TestCase):
    def test_desired_services_bind_certified_digests(self) -> None:
        services = desired_services(CORE_DIGEST, WEB_DIGEST)
        self.assertEqual([s.name for s in services], ["ngabo-core", "ngabo-web"])
        core, web = services
        self.assertEqual(core.image, artifact_uri("ngabo-core", CORE_DIGEST))
        self.assertEqual(web.image, artifact_uri("ngabo-web", WEB_DIGEST))
        self.assertIn(CORE_DIGEST, core.image)
        self.assertIn(WEB_DIGEST, web.image)

    def test_core_is_private_web_is_public(self) -> None:
        core, web = desired_services(CORE_DIGEST, WEB_DIGEST)
        self.assertFalse(core.allow_unauthenticated)
        self.assertTrue(web.allow_unauthenticated)

    def test_runtime_service_accounts_are_dedicated(self) -> None:
        core_email = f"ngabo-core-runtime@{DEFAULT_PROJECT_ID}.iam.gserviceaccount.com"
        web_email = f"ngabo-web-runtime@{DEFAULT_PROJECT_ID}.iam.gserviceaccount.com"
        core, web = desired_services(CORE_DIGEST, WEB_DIGEST)
        self.assertEqual(core.runtime_sa, core_email)
        self.assertEqual(web.runtime_sa, web_email)

    def test_web_gets_core_url_env(self) -> None:
        _, web = desired_services(CORE_DIGEST, WEB_DIGEST)
        self.assertEqual(
            web.env_vars["CORE_API_URL"],
            f"https://ngabo-core-{DEFAULT_PROJECT_ID}.{PRIMARY_REGION}.run.app",
        )

    def test_bounds_come_from_caps_contract(self) -> None:
        core, web = desired_services(CORE_DIGEST, WEB_DIGEST)
        for service in (core, web):
            self.assertEqual(service.caps["min_instances"], 0)
            self.assertEqual(service.caps["max_instances"], 2)
            self.assertEqual(service.caps["cpu"], "1")
            self.assertEqual(service.caps["memory"], "512Mi")
            self.assertEqual(service.caps["timeout_seconds"], 60)
            self.assertTrue(service.caps["scale_to_zero_required"])

    def test_rejects_mutable_tags_and_bad_digests(self) -> None:
        for bad in ("latest", "ngabo-core:latest", "sha256:abc", "sha256:" + "g" * 64, ""):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                desired_services(bad, WEB_DIGEST)

    def test_gcloud_args_include_bounds_and_labels(self) -> None:
        core, web = desired_services(CORE_DIGEST, WEB_DIGEST)
        args = web.to_gcloud_args()
        self.assertIn("--max-instances", args)
        self.assertIn("2", args)
        self.assertIn("--min-instances", args)
        self.assertIn("0", args)
        self.assertIn("--memory", args)
        self.assertIn("512Mi", args)
        self.assertIn("--timeout", args)
        self.assertIn("60s", args)
        self.assertIn("--allow-unauthenticated", args)
        self.assertIn("--service-account", args)
        self.assertIn(f"ngabo-web-runtime@{DEFAULT_PROJECT_ID}.iam.gserviceaccount.com", args)
        self.assertIn("--set-env-vars", args)
        self.assertIn("CORE_API_URL=", " ".join(args))

    def test_core_gcloud_args_deny_unauthenticated(self) -> None:
        core, _ = desired_services(CORE_DIGEST, WEB_DIGEST)
        args = core.to_gcloud_args()
        self.assertIn("--no-allow-unauthenticated", args)
        self.assertNotIn("--allow-unauthenticated", args)

    @staticmethod
    def _live_state(
        name: str,
        digest: str,
        runtime_sa: str,
        annotations: dict[str, str] | None = None,
    ) -> dict[str, object]:
        return {
            "spec": {
                "template": {
                    "spec": {
                        "serviceAccountName": runtime_sa,
                        "containers": [{"image": artifact_uri(name, digest)}],
                    },
                    "metadata": {
                        "annotations": annotations
                        or {
                            "autoscaling.knative.dev/maxScale": "2",
                            "autoscaling.knative.dev/minScale": "0",
                        }
                    },
                }
            }
        }

    def test_validate_uses_live_describe(self) -> None:
        from infra.gcp import cloudrun

        core_email = f"ngabo-core-runtime@{DEFAULT_PROJECT_ID}.iam.gserviceaccount.com"
        web_email = f"ngabo-web-runtime@{DEFAULT_PROJECT_ID}.iam.gserviceaccount.com"
        live = {
            "ngabo-core": self._live_state("ngabo-core", CORE_DIGEST, core_email),
            "ngabo-web": self._live_state("ngabo-web", WEB_DIGEST, web_email),
        }
        with mock.patch.object(
            cloudrun, "describe_service", side_effect=lambda name: live[name]
        ):
            self.assertEqual(cloudrun.validate(CORE_DIGEST, WEB_DIGEST), 0)

    def test_validate_fails_on_drift(self) -> None:
        from infra.gcp import cloudrun

        live = {
            "ngabo-core": self._live_state(
                "ngabo-core",
                CORE_DIGEST,
                f"ngabo-core-runtime@{DEFAULT_PROJECT_ID}.iam.gserviceaccount.com",
            ),
            "ngabo-web": {
                "spec": {
                    "template": {
                        "spec": {
                            "serviceAccountName": "someone-else",
                            "containers": [{"image": "wrong-image"}],
                        },
                        "metadata": {"annotations": {}},
                    }
                }
            },
        }
        with mock.patch.object(
            cloudrun, "describe_service", side_effect=lambda name: live[name]
        ):
            self.assertEqual(cloudrun.validate(CORE_DIGEST, WEB_DIGEST), 1)


if __name__ == "__main__":
    unittest.main()
