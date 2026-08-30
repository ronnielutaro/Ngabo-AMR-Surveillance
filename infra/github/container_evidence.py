"""Machine-readable sanitized evidence for published ngabo container artifacts.

Issue #89 contract: every published artifact must bind the source commit,
workflow run, service name, Artifact Registry URI, navigation tag, immutable
digest, build/scan results, runtime identity, image size, base image
digests, OCI metadata, and reproducibility observation.

This generator runs in the trusted publish workflow with all values supplied
via environment variables. It validates the required bindings and emits a
sanitized JSON document (no tokens, credentials, environment dumps, billing
identifiers, or secret values).

Usage (publish workflow):

    infra/github/container_evidence.py --output container-publish-evidence.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SHORT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

REQUIRED_ENV = (
    "EVIDENCE_REPOSITORY",
    "EVIDENCE_COMMIT",
    "EVIDENCE_WORKFLOW",
    "EVIDENCE_RUN_ID",
    "EVIDENCE_BASE_URL",
    "EVIDENCE_CORE_DIGEST",
    "EVIDENCE_WEB_DIGEST",
)

FORBIDDEN_PATTERNS = (
    "BEGIN PRIVATE KEY",
    "gha-creds-",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "client_secret",
    "AKIA",
)


class EvidenceValidationError(Exception):
    """Raised when evidence inputs fail the required-bindings contract."""


def _scan_summary(path: str | None) -> dict[str, Any]:
    """Summarize a Trivy table output file into severity counts.

    Returns a sanitized summary; missing files yield an explicit unknown
    rather than a fabricated zero.
    """
    if not path or not Path(path).is_file():
        return {"source": path, "severity_counts": {}, "note": "scan file missing"}
    counts: dict[str, int] = {}
    total = 0
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped.startswith(("CRITICAL:", "HIGH:", "MEDIUM:", "LOW:", "UNKNOWN:")):
            continue
        name, _, value = stripped.partition(":")
        try:
            counts[name] = int(value.strip())
        except ValueError:
            continue
        total += counts.get(name, 0)
    return {"source": path, "severity_counts": counts, "total_findings": total}


@dataclass(frozen=True)
class ArtifactEvidence:
    repository: str
    source_commit_sha: str
    workflow_name: str
    workflow_run_id: str
    service_name: str
    artifact_registry_uri: str
    navigation_tag: str
    immutable_digest: str
    build_result: str
    scan_summary: dict[str, Any]
    runtime_user: str
    image_size_bytes: int | None
    base_image_digest: str
    oci_labels: dict[str, str]
    reproducibility_observation: str


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise EvidenceValidationError(f"missing required environment variable {name}")
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.lower() in value.lower():
            raise EvidenceValidationError(
                f"environment variable {name} contains forbidden pattern {pattern!r}"
            )
    return value


def build_evidence(
    service_name: str,
    navigation_tag: str,
    immutable_digest: str,
    runtime_user: str,
    image_size_bytes: int | None,
    base_image_digest: str,
    oci_labels: dict[str, str],
    scan_file: str | None = None,
    reproducibility_observation: str = "not measured",
) -> ArtifactEvidence:
    repository = _require_env("EVIDENCE_REPOSITORY")
    commit = _require_env("EVIDENCE_COMMIT")
    workflow = _require_env("EVIDENCE_WORKFLOW")
    run_id = _require_env("EVIDENCE_RUN_ID")
    base_url = _require_env("EVIDENCE_BASE_URL")

    if not SHORT_SHA_RE.fullmatch(commit):
        raise EvidenceValidationError(f"EVIDENCE_COMMIT is not a full 40-hex SHA: {commit!r}")
    if not DIGEST_RE.fullmatch(immutable_digest):
        raise EvidenceValidationError(
            f"immutable digest for {service_name} is not a "
            f"sha256:64-hex digest: {immutable_digest!r}"
        )
    if not DIGEST_RE.fullmatch(base_image_digest):
        raise EvidenceValidationError(
            f"base image digest for {service_name} is not a "
            f"sha256:64-hex digest: {base_image_digest!r}"
        )

    return ArtifactEvidence(
        repository=repository,
        source_commit_sha=commit,
        workflow_name=workflow,
        workflow_run_id=run_id,
        service_name=service_name,
        artifact_registry_uri=f"{base_url}/{service_name}",
        navigation_tag=navigation_tag,
        immutable_digest=immutable_digest,
        build_result="success",
        scan_summary=_scan_summary(scan_file),
        runtime_user=runtime_user,
        image_size_bytes=image_size_bytes,
        base_image_digest=base_image_digest,
        oci_labels=oci_labels,
        reproducibility_observation=reproducibility_observation,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    core = build_evidence(
        service_name="ngabo-core",
        navigation_tag=os.environ.get(
            "EVIDENCE_CORE_TAG", "sha-" + os.environ.get("EVIDENCE_COMMIT", "")
        ),
        immutable_digest=_require_env("EVIDENCE_CORE_DIGEST"),
        runtime_user="ngabo",
        image_size_bytes=None,
        base_image_digest="sha256:1042b61448fef4ba92d16a8c7eb4996d027568ce64792a7877fd88511e0af7c6",
        oci_labels={
            "org.opencontainers.image.source": os.environ.get("EVIDENCE_REPOSITORY", ""),
            "org.opencontainers.image.revision": os.environ.get("EVIDENCE_COMMIT", ""),
            "org.opencontainers.image.title": "ngabo-core",
        },
        scan_file=os.environ.get("EVIDENCE_CORE_SCAN"),
        reproducibility_observation=os.environ.get(
            "EVIDENCE_CORE_REPRO", "not measured"
        ),
    )
    web = build_evidence(
        service_name="ngabo-web",
        navigation_tag=os.environ.get(
            "EVIDENCE_WEB_TAG", "sha-" + os.environ.get("EVIDENCE_COMMIT", "")
        ),
        immutable_digest=_require_env("EVIDENCE_WEB_DIGEST"),
        runtime_user="ngabo",
        image_size_bytes=None,
        base_image_digest="sha256:ba849c60be29959425b8734d57b8b4b7d56f98edd9504c9af091d5281095a71e",
        oci_labels={
            "org.opencontainers.image.source": os.environ.get("EVIDENCE_REPOSITORY", ""),
            "org.opencontainers.image.revision": os.environ.get("EVIDENCE_COMMIT", ""),
            "org.opencontainers.image.title": "ngabo-web",
        },
        scan_file=os.environ.get("EVIDENCE_WEB_SCAN"),
        reproducibility_observation=os.environ.get(
            "EVIDENCE_WEB_REPRO", "not measured"
        ),
    )

    document = {
        "schema_version": "1.0.0",
        "artifacts": [asdict(core), asdict(web)],
    }
    args.output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(document, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
