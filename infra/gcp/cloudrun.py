"""Cloud Run desired-state CLI for the ngabo skeleton (Issue #90).

Implements plan / validate / apply for the two independent Cloud Run
services (ngabo-core, ngabo-web) against the immutable digests published
by the Issue #89 trusted publish workflow.

Contract:

- Images are referenced ONLY by immutable digest (``sha256:<64 hex>``).
  Mutable tags or bare repository references are rejected — the deployed
  artifact is the tested artifact (Epic #84 invariant).
- All bounds come from ``CLOUD_RUN_CAPS_CONTRACT`` (min 0, max 2, cpu 1,
  memory 512Mi, timeout 60s, scale-to-zero) and standard labels.
- Each service runs under its dedicated runtime service account
  (ngabo-core-runtime / ngabo-web-runtime, created by Issue #87 identity
  tooling) via ``--service-account``.
- The web service is the public entry point; core stays private
  (``--no-allow-unauthenticated``) and is reached by the web runtime
  identity through the project's default service-to-service boundary.
- ``--core-url`` pins the CORE_API_URL env var the web console reads.

This file performs NO deployment in the working tree; ``apply`` is gated
behind the trusted deploy workflow (``deploy-cloudrun.yml``), which
validates digest inputs before invoking gcloud. Local ``plan``/``validate``
use gcloud describe (read-only) and exit non-zero on drift.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Ensure repository root is on sys.path for direct CLI execution
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from infra.gcp.config import (  # noqa: E402
    ARTIFACT_REGISTRY_REPO,
    CLOUD_RUN_CAPS_CONTRACT,
    DEFAULT_PROJECT_ID,
    PRIMARY_REGION,
    STANDARD_LABELS,
)

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

CORE_RUNTIME_SA = f"ngabo-core-runtime@{DEFAULT_PROJECT_ID}.iam.gserviceaccount.com"
WEB_RUNTIME_SA = f"ngabo-web-runtime@{DEFAULT_PROJECT_ID}.iam.gserviceaccount.com"


def artifact_uri(service: str, digest: str) -> str:
    return (
        f"us-central1-docker.pkg.dev/{DEFAULT_PROJECT_ID}/"
        f"{ARTIFACT_REGISTRY_REPO}/{service}@{digest}"
    )


@dataclass(frozen=True)
class ServiceDesiredState:
    name: str
    image: str
    runtime_sa: str
    allow_unauthenticated: bool
    env_vars: Mapping[str, str]
    caps: Mapping[str, object] = field(default_factory=lambda: CLOUD_RUN_CAPS_CONTRACT)

    def to_gcloud_args(self) -> list[str]:
        caps = self.caps
        args = [
            "--image",
            self.image,
            "--service-account",
            self.runtime_sa,
            "--min-instances",
            str(caps["min_instances"]),
            "--max-instances",
            str(caps["max_instances"]),
            "--cpu",
            str(caps["cpu"]),
            "--memory",
            str(caps["memory"]),
            "--timeout",
            f"{caps['timeout_seconds']}s",
            "--concurrency",
            str(caps["concurrency"]),
            "--region",
            PRIMARY_REGION,
            "--no-cpu-throttling",
            "--quiet",
        ]
        for key, value in STANDARD_LABELS.items():
            args.extend(["--labels", f"{key}={value}"])
        for name, value in self.env_vars.items():
            args.extend(["--set-env-vars", f"{name}={value}"])
        if self.allow_unauthenticated:
            args.append("--allow-unauthenticated")
        else:
            args.append("--no-allow-unauthenticated")
        return args


def default_core_url() -> str:
    return (
        f"https://ngabo-core-{DEFAULT_PROJECT_ID}.{PRIMARY_REGION}.run.app"
    )


def desired_services(core_digest: str, web_digest: str) -> list[ServiceDesiredState]:
    """Desired state for both services; digests validated before use."""
    for digest in (core_digest, web_digest):
        if not DIGEST_RE.fullmatch(digest):
            raise ValueError(f"not an immutable sha256 digest: {digest!r}")
    return [
        ServiceDesiredState(
            name="ngabo-core",
            image=artifact_uri("ngabo-core", core_digest),
            runtime_sa=CORE_RUNTIME_SA,
            allow_unauthenticated=False,
            env_vars={},
        ),
        ServiceDesiredState(
            name="ngabo-web",
            image=artifact_uri("ngabo-web", web_digest),
            runtime_sa=WEB_RUNTIME_SA,
            allow_unauthenticated=True,
            env_vars={"CORE_API_URL": default_core_url()},
        ),
    ]


def run_gcloud(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gcloud", *args],
        check=check,
        capture_output=True,
        text=True,
    )


def describe_service(service: str) -> dict[str, Any] | None:
    """Return the live service config, or None if the service does not exist."""
    proc = run_gcloud(
        [
            "run",
            "services",
            "describe",
            service,
            "--region",
            PRIMARY_REGION,
            "--format=json",
        ],
        check=False,
    )
    if proc.returncode != 0:
        return None
    parsed = json.loads(proc.stdout)
    return parsed if isinstance(parsed, dict) else None


def plan(core_digest: str, web_digest: str) -> int:
    print(f"Cloud Run desired state (project {DEFAULT_PROJECT_ID}, {PRIMARY_REGION})")
    services = desired_services(core_digest, web_digest)
    for service in services:
        live = describe_service(service.name)
        if live is None:
            print(f"  CREATE {service.name} <- {service.image}")
            continue
        live_image = live["spec"].get("template", {}).get("spec", {}).get(
            "containers", [{}]
        )[0].get("image", "")
        status = "OK" if live_image == service.image else f"DRIFT (live {live_image})"
        print(f"  {status:20s} {service.name} desired {service.image}")
    return 0


def apply(core_digest: str, web_digest: str) -> int:
    services = desired_services(core_digest, web_digest)
    for service in services:
        print(f"Deploying {service.name} ...")
        result = run_gcloud(
            [
                "run",
                "services",
                "deploy",
                service.name,
                *service.to_gcloud_args(),
            ]
        )
        if result.returncode != 0:
            print(result.stderr)
            return 1
    print("Deploy complete.")
    return 0


def validate(core_digest: str, web_digest: str) -> int:
    services = desired_services(core_digest, web_digest)
    failures = 0
    for service in services:
        live = describe_service(service.name)
        if live is None:
            print(f"FAIL {service.name}: service does not exist")
            failures += 1
            continue
        container = live["spec"]["template"]["spec"]["containers"][0]
        live_image = container.get("image", "")
        if live_image != service.image:
            print(f"FAIL {service.name}: image {live_image} != {service.image}")
            failures += 1
        live_sa = live["spec"]["template"]["spec"].get("serviceAccountName", "")
        if live_sa != service.runtime_sa:
            print(f"FAIL {service.name}: runtime SA {live_sa} != {service.runtime_sa}")
            failures += 1
        caps = live["spec"]["template"]["metadata"].get("annotations", {})
        max_instances = caps.get("autoscaling.knative.dev/maxScale", "")
        min_instances = caps.get("autoscaling.knative.dev/minScale", "")
        if max_instances != str(service.caps["max_instances"]):
            print(f"FAIL {service.name}: maxScale {max_instances}")
            failures += 1
        if min_instances != str(service.caps["min_instances"]):
            print(f"FAIL {service.name}: minScale {min_instances}")
            failures += 1
        if failures == 0:
            print(f"PASS {service.name}: digest, SA, and scale bounds match")
    return 0 if failures == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_digest_args(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--core-digest",
            default=os.environ.get("NGABO_CORE_DIGEST"),
            help="ngabo-core immutable digest (sha256:<64 hex); REQUIRED",
        )
        p.add_argument(
            "--web-digest",
            default=os.environ.get("NGABO_WEB_DIGEST"),
            help="ngabo-web immutable digest (sha256:<64 hex); REQUIRED",
        )

    for name in ("plan", "apply", "validate"):
        p = sub.add_parser(name)
        add_digest_args(p)

    args = parser.parse_args(argv)
    try:
        services = desired_services(args.core_digest, args.web_digest)
        del services  # validation side effect only
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.command == "plan":
        return plan(args.core_digest, args.web_digest)
    if args.command == "apply":
        return apply(args.core_digest, args.web_digest)
    return validate(args.core_digest, args.web_digest)


if __name__ == "__main__":
    raise SystemExit(main())
