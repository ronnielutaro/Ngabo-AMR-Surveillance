"""Tests for infra/gcp/cloudrun.py — canonical Cloud Run deployment (Issue #90)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

MODULE_DIR = Path(__file__).parents[1]
sys.path.insert(0, str(MODULE_DIR))

from infra.gcp.cloudrun import artifact_uri, desired_services, resolve_core_url  # noqa: E402
from infra.gcp.config import CLOUD_RUN_LABELS, DEFAULT_PROJECT_ID  # noqa: E402

CORE_DIGEST = "sha256:" + "a" * 64
WEB_DIGEST = "sha256:" + "b" * 64

CORE_EMAIL = f"ngabo-core-runtime@{DEFAULT_PROJECT_ID}.iam.gserviceaccount.com"
WEB_EMAIL = f"ngabo-web-runtime@{DEFAULT_PROJECT_ID}.iam.gserviceaccount.com"


def live_service(
    name: str,
    digest: str,
    runtime_sa: str,
    env: dict[str, str] | None = None,
    labels: dict[str, str] | None = None,
    cpu: str = "1",
    memory: str = "512Mi",
    max_scale: str = "2",
    min_scale: str = "0",
    timeout: str = "60s",
    cpu_throttling: str = "false",
) -> dict[str, object]:
    return {
        "metadata": {"labels": labels or dict(CLOUD_RUN_LABELS)},
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "autoscaling.knative.dev/maxScale": max_scale,
                        "autoscaling.knative.dev/minScale": min_scale,
                        "run.googleapis.com/timeout": timeout,
                        "run.googleapis.com/cpu-throttling": cpu_throttling,
                    }
                },
                "spec": {
                    "serviceAccountName": runtime_sa,
                    "containers": [
                        {
                            "image": artifact_uri(name, digest),
                            "resources": {"cpu": cpu, "memory": memory},
                            "env": [
                                {"name": k, "value": v} for k, v in (env or {}).items()
                            ],
                        }
                    ],
                },
            }
        },
    }


def live_iam(members: list[str] | None = None) -> dict[str, object]:
    return {"bindings": [{"role": "roles/run.invoker", "members": members or []}]}


def converged_live() -> dict[str, dict[str, object]]:
    return {
        "ngabo-core": live_service(
            "ngabo-core",
            CORE_DIGEST,
            CORE_EMAIL,
            env={"NGABO_IMAGE_DIGEST": CORE_DIGEST},
        ),
        "ngabo-web": live_service(
            "ngabo-web",
            WEB_DIGEST,
            WEB_EMAIL,
            env={"CORE_API_URL": "https://core.example.run.app"},
        ),
    }


class DesiredStateTests(unittest.TestCase):
    def test_desired_services_bind_immutable_digests(self) -> None:
        services = desired_services(CORE_DIGEST, WEB_DIGEST)
        self.assertEqual([s.name for s in services], ["ngabo-core", "ngabo-web"])
        core, web = services
        self.assertEqual(core.image, artifact_uri("ngabo-core", CORE_DIGEST))
        self.assertEqual(web.image, artifact_uri("ngabo-web", WEB_DIGEST))

    def test_core_is_private_web_is_public(self) -> None:
        core, web = desired_services(CORE_DIGEST, WEB_DIGEST)
        self.assertFalse(core.allow_unauthenticated)
        self.assertTrue(web.allow_unauthenticated)

    def test_core_injects_immutable_digest_as_runtime_metadata(self) -> None:
        core, _ = desired_services(CORE_DIGEST, WEB_DIGEST)
        self.assertEqual(core.env_vars["NGABO_IMAGE_DIGEST"], CORE_DIGEST)

    def test_web_env_set_at_apply_time_not_in_desired_state(self) -> None:
        _, web = desired_services(CORE_DIGEST, WEB_DIGEST)
        self.assertNotIn("CORE_API_URL", web.env_vars)

    def test_runtime_service_accounts_are_dedicated(self) -> None:
        core, web = desired_services(CORE_DIGEST, WEB_DIGEST)
        self.assertEqual(core.runtime_sa, CORE_EMAIL)
        self.assertEqual(web.runtime_sa, WEB_EMAIL)

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

    def test_gcloud_args_use_canonical_labels_not_terraform(self) -> None:
        core, _ = desired_services(CORE_DIGEST, WEB_DIGEST)
        args = core.to_gcloud_args()
        joined = " ".join(args)
        self.assertIn("managed-by=ngabo-bootstrap", joined)
        self.assertNotIn("terraform", joined)
        self.assertIn("environment=dev", joined)
        self.assertIn("--no-allow-unauthenticated", args)

    def test_gcloud_args_include_bounds(self) -> None:
        _, web = desired_services(CORE_DIGEST, WEB_DIGEST)
        args = web.to_gcloud_args()
        self.assertIn("--max-instances", args)
        self.assertIn("--min-instances", args)
        self.assertIn("512Mi", args)
        self.assertIn("60s", args)
        self.assertIn("--allow-unauthenticated", args)
        self.assertIn(WEB_EMAIL, args)

    def test_apply_sequence_is_canonical(self) -> None:
        from infra.gcp import cloudrun

        calls: list[list[str]] = []

        def fake_run(args: list[str], check: bool = True) -> mock.Mock:
            calls.append(args)
            result = mock.Mock()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            if args[0] == "run" and args[1] == "services" and args[2] == "describe":
                result.stdout = "https://ngabo-core-123456.run.app"
            return result

        with mock.patch.object(cloudrun, "run_gcloud", side_effect=fake_run):
            self.assertEqual(cloudrun.apply(CORE_DIGEST, WEB_DIGEST), 0)

        deploy_calls = [
            c for c in calls if c[0:2] == ["run", "services"] and c[2] == "deploy"
        ]
        self.assertEqual(len(deploy_calls), 2)
        self.assertEqual(deploy_calls[0][3], "ngabo-core")
        self.assertEqual(deploy_calls[1][3], "ngabo-web")

        iam_calls = [
            c
            for c in calls
            if c[0:2] == ["run", "services"] and c[2] == "add-iam-policy-binding"
        ]
        self.assertEqual(len(iam_calls), 1)
        self.assertEqual(iam_calls[0][3], "ngabo-core")
        self.assertIn("roles/run.invoker", iam_calls[0])

        # The web deploy must carry the resolved core URL
        web_deploy = deploy_calls[1]
        self.assertIn("CORE_API_URL=https://ngabo-core-123456.run.app", web_deploy)

    def test_apply_fails_when_core_url_unresolvable(self) -> None:
        from infra.gcp import cloudrun

        def fake_run(args: list[str], check: bool = True) -> mock.Mock:
            result = mock.Mock()
            result.returncode = 1
            result.stdout = ""
            result.stderr = "not found"
            return result

        with (
            mock.patch.object(cloudrun, "run_gcloud", side_effect=fake_run),
            self.assertRaises(RuntimeError),
        ):
            cloudrun.apply(CORE_DIGEST, WEB_DIGEST)

    def test_resolve_core_url_uses_status_url(self) -> None:
        from infra.gcp import cloudrun

        with mock.patch.object(
            cloudrun,
            "run_gcloud",
            return_value=mock.Mock(
                returncode=0, stdout="https://ngabo-core-123.run.app\n", stderr=""
            ),
        ) as mocked:
            url = resolve_core_url()
            self.assertEqual(url, "https://ngabo-core-123.run.app")
        args = mocked.call_args.args[0]
        self.assertIn("--format=value(status.url)", args)


class ValidateTests(unittest.TestCase):
    def _validate(self, live: dict[str, dict[str, object]]) -> int:
        from infra.gcp import cloudrun

        def describe(name: str) -> dict[str, object] | None:
            return live.get(name)

        def iam(name: str) -> list[str]:
            if name == "ngabo-core":
                return [f"roles/run.invoker:serviceAccount:{WEB_EMAIL}"]
            return ["roles/run.invoker:allUsers"]

        def fake_run(args: list[str], check: bool = True) -> mock.Mock:
            result = mock.Mock()
            result.returncode = 0
            result.stderr = ""
            if args[0:2] == ["run", "services"] and args[2] == "get-iam-policy":
                import json as _json

                result.stdout = _json.dumps(
                    {
                        "bindings": [
                            {
                                "role": "roles/run.invoker",
                                "members": [f"serviceAccount:{WEB_EMAIL}"],
                            }
                        ]
                    }
                )
            elif args[0:2] == ["run", "services"] and args[2] == "describe":
                result.stdout = "https://core.example.run.app"
            else:
                result.stdout = ""
            return result

        with (
            mock.patch.object(cloudrun, "describe_service", side_effect=describe),
            mock.patch.object(cloudrun, "_service_iam_members", side_effect=iam),
            mock.patch.object(cloudrun, "run_gcloud", side_effect=fake_run),
        ):
            return cloudrun.validate(CORE_DIGEST, WEB_DIGEST)

    def test_validate_passes_on_converged_state(self) -> None:
        self.assertEqual(self._validate(converged_live()), 0)

    def test_validate_fails_on_wrong_image(self) -> None:
        live = converged_live()
        live["ngabo-core"] = live_service(
            "ngabo-core", "sha256:" + "c" * 64, CORE_EMAIL
        )
        self.assertEqual(self._validate(live), 1)

    def test_validate_fails_on_mutable_tag_image(self) -> None:
        live = converged_live()
        bad = live_service("ngabo-web", WEB_DIGEST, WEB_EMAIL)
        bad["spec"]["template"]["spec"]["containers"][0]["image"] = "ngabo-web:latest"  # type: ignore[index]
        live["ngabo-web"] = bad
        self.assertEqual(self._validate(live), 1)

    def test_validate_fails_on_wrong_sa(self) -> None:
        live = converged_live()
        live["ngabo-core"] = live_service(
            "ngabo-core", CORE_DIGEST, "someone-else@x.iam.gserviceaccount.com"
        )
        self.assertEqual(self._validate(live), 1)

    def test_validate_fails_on_max_instances_drift(self) -> None:
        live = converged_live()
        live["ngabo-web"] = live_service(
            "ngabo-web", WEB_DIGEST, WEB_EMAIL,
            env={"CORE_API_URL": "https://core.example.run.app"},
            max_scale="5",
        )
        self.assertEqual(self._validate(live), 1)

    def test_validate_fails_on_memory_drift(self) -> None:
        live = converged_live()
        live["ngabo-web"] = live_service(
            "ngabo-web", WEB_DIGEST, WEB_EMAIL,
            env={"CORE_API_URL": "https://core.example.run.app"},
            memory="1Gi",
        )
        self.assertEqual(self._validate(live), 1)

    def test_validate_fails_on_timeout_drift(self) -> None:
        live = converged_live()
        live["ngabo-web"] = live_service(
            "ngabo-web", WEB_DIGEST, WEB_EMAIL,
            env={"CORE_API_URL": "https://core.example.run.app"},
            timeout="300s",
        )
        self.assertEqual(self._validate(live), 1)

    def test_validate_fails_on_cpu_throttling_enabled(self) -> None:
        live = converged_live()
        live["ngabo-web"] = live_service(
            "ngabo-web", WEB_DIGEST, WEB_EMAIL,
            env={"CORE_API_URL": "https://core.example.run.app"},
            cpu_throttling="true",
        )
        self.assertEqual(self._validate(live), 1)

    def test_validate_fails_on_label_drift(self) -> None:
        live = converged_live()
        drifted = live_service("ngabo-core", CORE_DIGEST, CORE_EMAIL)
        drifted["metadata"]["labels"] = {**CLOUD_RUN_LABELS, "managed-by": "terraform"}  # type: ignore[index]
        live["ngabo-core"] = drifted
        self.assertEqual(self._validate(live), 1)

    def test_validate_fails_on_wrong_core_url(self) -> None:
        live = converged_live()
        live["ngabo-web"] = live_service(
            "ngabo-web", WEB_DIGEST, WEB_EMAIL,
            env={"CORE_API_URL": "https://wrong.example.run.app"},
        )
        self.assertEqual(self._validate(live), 1)

    def test_validate_fails_when_core_missing_injected_digest(self) -> None:
        live = converged_live()
        live["ngabo-core"] = live_service("ngabo-core", CORE_DIGEST, CORE_EMAIL, env={})
        self.assertEqual(self._validate(live), 1)


if __name__ == "__main__":
    unittest.main()
