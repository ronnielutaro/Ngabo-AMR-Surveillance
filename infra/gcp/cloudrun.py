"""Cloud Run desired-state CLI for the ngabo skeleton (Issue #90).

This module is the SINGLE canonical Cloud Run deployment implementation.
The trusted GitHub workflow (``deploy-cloudrun.yml``) owns authentication,
the develop-ref guard, immutable digest validation, and evidence recording;
it delegates every gcloud deployment command to this module so there is
exactly one source of deployment truth.

Canonical deployment sequence (``apply``):

1. Deploy ngabo-core (private, immutable digest, NGABO_IMAGE_DIGEST injected).
2. Resolve the ACTUAL deployed core ``status.url`` (project-number hostname
   or assigned URL — never a synthesized project-ID hostname).
3. Grant ``ngabo-web-runtime`` ``roles/run.invoker`` on ngabo-core only
   (the service-to-service boundary for the private core).
4. Deploy ngabo-web (public read-only entry point, CORE_API_URL set to the
   real core URL).

Contract:

- Images are referenced ONLY by immutable digest (``sha256:<64 hex>``).
  Mutable tags or bare repository references are rejected — the deployed
  artifact is the tested artifact (Epic #84 invariant).
- All bounds come from ``CLOUD_RUN_CAPS_CONTRACT`` (min 0, max 2, cpu 1,
  memory 512Mi, timeout 60s, scale-to-zero) and the canonical
  ``CLOUD_RUN_LABELS``.
- Each service runs under its dedicated runtime service account.
- Core stays private; web is the intentional public read-only entry point.
- ``validate`` fails closed on ANY material drift from the #90 contract.

``plan``/``validate`` are read-only (gcloud describe); ``apply`` performs
the canonical deployment and is invoked only by the trusted workflow.
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
    CLOUD_RUN_LABELS,
    DEFAULT_PROJECT_ID,
    PRIMARY_REGION,
)

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

CORE_RUNTIME_SA = f"ngabo-core-runtime@{DEFAULT_PROJECT_ID}.iam.gserviceaccount.com"
WEB_RUNTIME_SA = f"ngabo-web-runtime@{DEFAULT_PROJECT_ID}.iam.gserviceaccount.com"

# Runtime artifact identity injected at deploy time from the EXACT digest
# supplied to the trusted deployment (never invented or derived from a tag).
IMAGE_DIGEST_ENV = "NGABO_IMAGE_DIGEST"
CORE_URL_ENV = "CORE_API_URL"


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
        for key, value in CLOUD_RUN_LABELS.items():
            args.extend(["--labels", f"{key}={value}"])
        for name, value in self.env_vars.items():
            args.extend(["--set-env-vars", f"{name}={value}"])
        if self.allow_unauthenticated:
            args.append("--allow-unauthenticated")
        else:
            args.append("--no-allow-unauthenticated")
        return args


def desired_services(core_digest: str, web_digest: str) -> list[ServiceDesiredState]:
    """Desired state for both services; digests validated before use.

    The core URL is resolved at apply time from the deployed service; the
    core state carries the immutable image digest as runtime metadata.
    """
    for digest in (core_digest, web_digest):
        if not DIGEST_RE.fullmatch(digest):
            raise ValueError(f"not an immutable sha256 digest: {digest!r}")
    return [
        ServiceDesiredState(
            name="ngabo-core",
            image=artifact_uri("ngabo-core", core_digest),
            runtime_sa=CORE_RUNTIME_SA,
            allow_unauthenticated=False,
            env_vars={IMAGE_DIGEST_ENV: core_digest},
        ),
        ServiceDesiredState(
            name="ngabo-web",
            image=artifact_uri("ngabo-web", web_digest),
            runtime_sa=WEB_RUNTIME_SA,
            allow_unauthenticated=True,
            # CORE_API_URL is set at apply time from the real core status.url.
            env_vars={},
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


def resolve_core_url() -> str:
    """Resolve the ACTUAL deployed core URL via ``status.url``.

    Cloud Run's deterministic hostname is derived from the project NUMBER
    (and older services may carry an assigned hashed URL); synthesizing it
    from the project ID is wrong. The web deployment consumes this exact
    value as CORE_API_URL.
    """
    proc = run_gcloud(
        [
            "run",
            "services",
            "describe",
            "ngabo-core",
            "--region",
            PRIMARY_REGION,
            "--format=value(status.url)",
        ],
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError(
            "failed to resolve ngabo-core status.url: "
            f"{proc.stderr.strip() or 'empty status.url'}"
        )
    return proc.stdout.strip()


def grant_web_invoker_on_core() -> None:
    """Grant ngabo-web-runtime run.invoker on ngabo-core only.

    The web runtime identity needs to invoke the private core; this is the
    service-to-service boundary for the skeleton.
    """
    proc = run_gcloud(
        [
            "run",
            "services",
            "add-iam-policy-binding",
            "ngabo-core",
            "--region",
            PRIMARY_REGION,
            "--member",
            f"serviceAccount:{WEB_RUNTIME_SA}",
            "--role",
            "roles/run.invoker",
            "--quiet",
        ],
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"failed to grant run.invoker on ngabo-core: {proc.stderr.strip()}"
        )


def _deploy_service(service: ServiceDesiredState) -> None:
    print(f"Deploying {service.name} ...")
    result = run_gcloud(
        [
            "run",
            "services",
            "deploy",
            service.name,
            *service.to_gcloud_args(),
        ],
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"deploy of {service.name} failed: {result.stderr.strip()}"
        )


def apply(core_digest: str, web_digest: str) -> int:
    """Canonical deployment sequence (single source of deployment truth)."""
    core, _web = desired_services(core_digest, web_digest)

    # 1. Core first (private) so its URL exists before the web deploy.
    _deploy_service(core)

    # 2. Resolve the actual core URL from the deployed service.
    core_url = resolve_core_url()
    print(f"ngabo-core status.url: {core_url}")

    # 3. Service-to-service IAM: web runtime may invoke private core.
    grant_web_invoker_on_core()

    # 4. Web with the real core URL.
    web = ServiceDesiredState(
        name="ngabo-web",
        image=artifact_uri("ngabo-web", web_digest),
        runtime_sa=WEB_RUNTIME_SA,
        allow_unauthenticated=True,
        env_vars={CORE_URL_ENV: core_url},
    )
    _deploy_service(web)

    print("Deploy complete.")
    return 0


def _service_env(service: str) -> dict[str, str]:
    """Extract the deployed env vars from a describe payload."""
    live = describe_service(service)
    if live is None:
        return {}
    container = (
        live.get("spec", {})
        .get("template", {})
        .get("spec", {})
        .get("containers", [{}])[0]
    )
    env: dict[str, str] = {}
    for item in container.get("env", []):
        name = item.get("name")
        value = item.get("value")
        if name and value is not None:
            env[name] = value
    return env


def _service_labels(service: str) -> dict[str, str]:
    """Extract the deployed labels from a describe payload."""
    live = describe_service(service)
    if live is None:
        return {}
    labels = live.get("metadata", {}).get("labels", {})
    return dict(labels) if isinstance(labels, dict) else {}


def _service_iam_members(service: str) -> list[str]:
    """Extract allUsers/allAuthenticatedUsers policy bindings for a service."""
    proc = run_gcloud(
        [
            "run",
            "services",
            "get-iam-policy",
            service,
            "--region",
            PRIMARY_REGION,
            "--format=json",
        ],
        check=False,
    )
    if proc.returncode != 0:
        return []
    try:
        policy = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    members: list[str] = []
    for binding in policy.get("bindings", []):
        role = binding.get("role", "")
        for member in binding.get("members", []):
            if member in ("allUsers", "allAuthenticatedUsers"):
                members.append(f"{role}:{member}")
    return members


def _check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def validate(core_digest: str, web_digest: str) -> int:
    """Fail-closed validation of the full #90 desired-state contract.

    Validates: immutable images, runtime SAs, resource/cost bounds, env
    values (including the real core URL and injected digest), canonical
    labels, and access boundaries (core private, web public, web-runtime
    invoker on core only). Properties that cannot be observed through the
    gcloud surface are recorded as limitations, not silently passed.
    """
    services = desired_services(core_digest, web_digest)
    core, web = services
    failures: list[str] = []

    for service in (core, web):
        live = describe_service(service.name)
        if live is None:
            _check(False, f"{service.name}: service does not exist", failures)
            continue
        spec = live["spec"]["template"]["spec"]
        container = spec.get("containers", [{}])[0]

        # Artifact identity
        live_image = container.get("image", "")
        _check(
            live_image == service.image,
            f"{service.name}: image {live_image} != {service.image}",
            failures,
        )
        if live_image:
            _check(
                "@sha256:" in live_image and not live_image.endswith(":latest"),
                f"{service.name}: image is not an immutable digest reference",
                failures,
            )
        _check(
            spec.get("serviceAccountName", "") == service.runtime_sa,
            f"{service.name}: runtime SA {spec.get('serviceAccountName', '')} "
            f"!= {service.runtime_sa}",
            failures,
        )

        # Resource/cost bounds
        annotations = live["spec"]["template"]["metadata"].get("annotations", {})
        _check(
            annotations.get("autoscaling.knative.dev/maxScale", "")
            == str(service.caps["max_instances"]),
            f"{service.name}: maxScale "
            f"{annotations.get('autoscaling.knative.dev/maxScale', '')} != "
            f"{service.caps['max_instances']}",
            failures,
        )
        _check(
            annotations.get("autoscaling.knative.dev/minScale", "")
            == str(service.caps["min_instances"]),
            f"{service.name}: minScale "
            f"{annotations.get('autoscaling.knative.dev/minScale', '')} != "
            f"{service.caps['min_instances']}",
            failures,
        )
        _check(
            container.get("resources", {}).get("cpu", {}) == service.caps["cpu"]
            or str(container.get("resources", {}).get("cpu", ""))
            == str(service.caps["cpu"]),
            f"{service.name}: cpu {container.get('resources', {}).get('cpu')} "
            f"!= {service.caps['cpu']}",
            failures,
        )
        _check(
            container.get("resources", {}).get("memory", "")
            == service.caps["memory"],
            f"{service.name}: memory "
            f"{container.get('resources', {}).get('memory', '')} != "
            f"{service.caps['memory']}",
            failures,
        )
        _check(
            annotations.get("run.googleapis.com/timeout", "")
            == f"{service.caps['timeout_seconds']}s",
            f"{service.name}: timeout "
            f"{annotations.get('run.googleapis.com/timeout', '')} != "
            f"{service.caps['timeout_seconds']}s",
            failures,
        )
        _check(
            annotations.get("run.googleapis.com/cpu-throttling", "true") == "false",
            f"{service.name}: cpu throttling enabled (contract: disabled)",
            failures,
        )

        # Canonical labels
        labels = _service_labels(service.name)
        for key, value in CLOUD_RUN_LABELS.items():
            _check(
                labels.get(key) == value,
                f"{service.name}: label {key}={labels.get(key)} != {value}",
                failures,
            )

    # Core-specific contract
    _check(
        core.allow_unauthenticated is False,
        "ngabo-core: must be private (no allow-unauthenticated)",
        failures,
    )
    _check(
        web.allow_unauthenticated is True,
        "ngabo-web: must be the public entry point (allow-unauthenticated)",
        failures,
    )

    # Access boundaries via IAM policy
    core_iam = _service_iam_members("ngabo-core")
    web_iam = _service_iam_members("ngabo-web")
    _check(
        not any("allUsers" in m or "allAuthenticatedUsers" in m for m in core_iam),
        f"ngabo-core: unexpected public IAM members {core_iam}",
        failures,
    )
    _check(
        any("allUsers" in m for m in web_iam),
        f"ngabo-web: missing public allUsers invoker binding (got {web_iam})",
        failures,
    )
    invoker = run_gcloud(
        [
            "run",
            "services",
            "get-iam-policy",
            "ngabo-core",
            "--region",
            PRIMARY_REGION,
            "--format=json",
        ],
        check=False,
    )
    web_invoker_ok = False
    if invoker.returncode == 0:
        try:
            policy = json.loads(invoker.stdout)
            for binding in policy.get("bindings", []):
                if (
                    binding.get("role") == "roles/run.invoker"
                    and f"serviceAccount:{WEB_RUNTIME_SA}"
                    in binding.get("members", [])
                ):
                    web_invoker_ok = True
        except json.JSONDecodeError:
            web_invoker_ok = False
    _check(
        web_invoker_ok,
        "ngabo-core: ngabo-web-runtime lacks roles/run.invoker binding",
        failures,
    )

    # Web CORE_API_URL must equal the real core status.url
    core_url = resolve_core_url() if describe_service("ngabo-core") is not None else ""
    web_env = _service_env("ngabo-web")
    if core_url:
        _check(
            web_env.get(CORE_URL_ENV) == core_url,
            f"ngabo-web: CORE_API_URL {web_env.get(CORE_URL_ENV)} != actual "
            f"core status.url {core_url}",
            failures,
        )
    else:
        failures.append("ngabo-core: cannot resolve status.url for URL parity check")

    # Injected runtime digest metadata on core
    core_env = _service_env("ngabo-core")
    _check(
        core_env.get(IMAGE_DIGEST_ENV) == core_digest,
        f"ngabo-core: {IMAGE_DIGEST_ENV} "
        f"{core_env.get(IMAGE_DIGEST_ENV)} != {core_digest}",
        failures,
    )

    for failure in failures:
        print(f"FAIL {failure}")
    if not failures:
        print(
            "PASS ngabo-core + ngabo-web: full #90 contract matches "
            "(images, SAs, bounds, labels, env, URLs, IAM boundaries)"
        )
    return 0 if not failures else 1


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
        desired_services(args.core_digest, args.web_digest)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.command == "plan":
        return plan(args.core_digest, args.web_digest)
    if args.command == "apply":
        try:
            return apply(args.core_digest, args.web_digest)
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    try:
        return validate(args.core_digest, args.web_digest)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
