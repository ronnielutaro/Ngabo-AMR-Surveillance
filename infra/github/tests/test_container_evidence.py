"""Tests for infra/github/container_evidence.py — published-artifact evidence contract."""

import json
import os
import pathlib
import sys
import unittest

MODULE_DIR = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(MODULE_DIR))
import container_evidence  # noqa: E402


class EvidenceContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env = dict(os.environ)
        os.environ["EVIDENCE_REPOSITORY"] = "ronnielutaro/Ngabo-AMR-Surveillance"
        os.environ["EVIDENCE_COMMIT"] = "a" * 40
        os.environ["EVIDENCE_WORKFLOW"] = "Publish Containers"
        os.environ["EVIDENCE_RUN_ID"] = "1234567890"
        os.environ["EVIDENCE_BASE_URL"] = (
            "us-central1-docker.pkg.dev/ngabo-amr-2026/ngabo-artifacts"
        )
        os.environ["EVIDENCE_CORE_DIGEST"] = "sha256:" + "b" * 64
        os.environ["EVIDENCE_WEB_DIGEST"] = "sha256:" + "c" * 64

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    def test_build_evidence_binds_required_fields(self) -> None:
        evidence = container_evidence.build_evidence(
            service_name="ngabo-core",
            navigation_tag="sha-" + "a" * 40,
            immutable_digest="sha256:" + "b" * 64,
            runtime_user="ngabo",
            image_size_bytes=12345,
            base_image_digest="sha256:" + "d" * 64,
            oci_labels={"org.opencontainers.image.revision": "a" * 40},
        )
        self.assertEqual(evidence.repository, "ronnielutaro/Ngabo-AMR-Surveillance")
        self.assertEqual(evidence.source_commit_sha, "a" * 40)
        self.assertEqual(evidence.workflow_run_id, "1234567890")
        self.assertEqual(evidence.service_name, "ngabo-core")
        self.assertEqual(
            evidence.artifact_registry_uri,
            "us-central1-docker.pkg.dev/ngabo-amr-2026/ngabo-artifacts/ngabo-core",
        )
        self.assertEqual(evidence.immutable_digest, "sha256:" + "b" * 64)
        self.assertEqual(evidence.runtime_user, "ngabo")

    def test_rejects_non_sha_commit(self) -> None:
        os.environ["EVIDENCE_COMMIT"] = "short"
        with self.assertRaises(container_evidence.EvidenceValidationError):
            container_evidence.build_evidence(
                service_name="ngabo-core",
                navigation_tag="tag",
                immutable_digest="sha256:" + "b" * 64,
                runtime_user="ngabo",
                image_size_bytes=None,
                base_image_digest="sha256:" + "d" * 64,
                oci_labels={},
            )

    def test_rejects_unpinned_digest(self) -> None:
        with self.assertRaises(container_evidence.EvidenceValidationError):
            container_evidence.build_evidence(
                service_name="ngabo-core",
                navigation_tag="tag",
                immutable_digest="sha256:abc",
                runtime_user="ngabo",
                image_size_bytes=None,
                base_image_digest="sha256:" + "d" * 64,
                oci_labels={},
            )

    def test_rejects_forbidden_secret_pattern_in_env(self) -> None:
        os.environ["EVIDENCE_REPOSITORY"] = "x gha-creds-123.json"
        with self.assertRaises(container_evidence.EvidenceValidationError):
            container_evidence.build_evidence(
                service_name="ngabo-core",
                navigation_tag="tag",
                immutable_digest="sha256:" + "b" * 64,
                runtime_user="ngabo",
                image_size_bytes=None,
                base_image_digest="sha256:" + "d" * 64,
                oci_labels={},
            )

    def test_scan_summary_counts_severities(self) -> None:
        with open("scan-sample.txt", "w", encoding="utf-8") as handle:
            handle.write("CRITICAL: 2\nHIGH: 3\nMEDIUM: 0\nLOW: 5\n")
        try:
            summary = container_evidence._scan_summary("scan-sample.txt")
            self.assertEqual(summary["severity_counts"]["CRITICAL"], 2)
            self.assertEqual(summary["severity_counts"]["HIGH"], 3)
            self.assertEqual(summary["total_findings"], 10)
        finally:
            os.remove("scan-sample.txt")

    def test_scan_summary_missing_file_is_unknown_not_zero(self) -> None:
        summary = container_evidence._scan_summary("does-not-exist.txt")
        self.assertIn("note", summary)
        self.assertEqual(summary["severity_counts"], {})

    def test_main_emits_sanitized_document(self) -> None:
        with open("scan-core.txt", "w", encoding="utf-8") as handle:
            handle.write("CRITICAL: 0\nHIGH: 0\n")
        with open("scan-web.txt", "w", encoding="utf-8") as handle:
            handle.write("CRITICAL: 0\nHIGH: 1\n")
        os.environ["EVIDENCE_CORE_SCAN"] = "scan-core.txt"
        os.environ["EVIDENCE_WEB_SCAN"] = "scan-web.txt"
        try:
            rc = container_evidence.main(["--output", "evidence-out.json"])
            self.assertEqual(rc, 0)
            document = json.loads(
                pathlib.Path("evidence-out.json").read_text(encoding="utf-8")
            )
            self.assertEqual(document["schema_version"], "1.0.0")
            self.assertEqual(len(document["artifacts"]), 2)
            services = {a["service_name"] for a in document["artifacts"]}
            self.assertEqual(services, {"ngabo-core", "ngabo-web"})
            for artifact in document["artifacts"]:
                self.assertEqual(artifact["build_result"], "success")
                self.assertEqual(artifact["runtime_user"], "ngabo")
                self.assertEqual(
                    artifact["source_commit_sha"], "a" * 40
                )
        finally:
            for name in ("scan-core.txt", "scan-web.txt", "evidence-out.json"):
                if os.path.exists(name):
                    os.remove(name)


if __name__ == "__main__":
    unittest.main()
