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
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"malformed Cloud Run service JSON for {service}: {exc}") from exc
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
    """Grant ngabo-web-runtime run.invoker on ngabo-core only."""
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

    _deploy_service(core)
    core_url = resolve_core_url()
    print(f"ngabo-core status.url: {core_url}")
    grant_web_invoker_on_core()

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


def _service_env_from_live(live: dict[str, Any]) -> dict[str, str]:
    """Extract deployed env vars from one Cloud Run V1 Service payload."""
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
            env[str(name)] = str(value)
    return env


def _service_labels_from_live(live: dict[str, Any]) -> dict[str, str]:
    """Extract deployed service labels from one Cloud Run V1 Service payload."""
    labels = live.get("metadata", {}).get("labels", {})
    if not isinstance(labels, dict):
        return {}
    return {str(key): str(value) for key, value in labels.items()}


def _service_iam_policy(service: str) -> dict[str, Any]:
    """Return a service IAM policy or fail closed if it cannot be observed."""
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
        raise RuntimeError(
            f"failed to read IAM policy for {service}: {proc.stderr.strip()}"
        )
    try:
        policy = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"malformed IAM policy JSON for {service}: {exc}") from exc
    if not isinstance(policy, dict):
        raise RuntimeError(f"unexpected IAM policy payload for {service}")
    return policy


def _public_invoker_members(policy: dict[str, Any]) -> list[str]:
    """Return public caller members bound to roles/run.invoker."""
    members: list[str] = []
    for binding in policy.get("bindings", []):
        if binding.get("role") != "roles/run.invoker":
            continue
        for member in binding.get("members", []):
            if member in ("allUsers", "allAuthenticatedUsers"):
                members.append(str(member))
    return members


def _has_web_runtime_invoker(policy: dict[str, Any]) -> bool:
    expected = f"serviceAccount:{WEB_RUNTIME_SA}"
    for binding in policy.get("bindings", []):
        if binding.get("role") == "roles/run.invoker" and expected in binding.get(
            "members", []
        ):
            return True
    return False


def _check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def validate(core_digest: str, web_digest: str) -> int:
    """Fail-closed validation of the full #90 desired-state contract.

    The parser intentionally follows Cloud Run Admin API V1 / exported YAML
    structure: ``resources.limits.{cpu,memory}``, ``timeoutSeconds`` and
    ``containerConcurrency`` live under ``spec.template.spec``. Tests use
    representative V1 payloads so they cannot pass against an invented
    response shape.
    """
    core, web = desired_services(core_digest, web_digest)
    failures: list[str] = []
    live_by_name: dict[str, dict[str, Any]] = {}

    for service in (core, web):
        live = describe_service(service.name)
        if live is None:
            failures.append(f"{service.name}: service does not exist")
            continue
        live_by_name[service.name] = live

        template = live.get("spec", {}).get("template", {})
        spec = template.get("spec", {})
        containers = spec.get("containers", [])
        if not isinstance(containers, list) or not containers:
            failures.append(f"{service.name}: missing container specification")
            continue
        container = containers[0]
        if not isinstance(container, dict):
            failures.append(f"{service.name}: malformed container specification")
            continue

        live_image = container.get("image", "")
        _check(
            live_image == service.image,
            f"{service.name}: image {live_image} != {service.image}",
            failures,
        )
        _check(
            isinstance(live_image, str)
            and "@sha256:" in live_image
            and not live_image.endswith(":latest"),
            f"{service.name}: image is not an immutable digest reference",
            failures,
        )
        _check(
            spec.get("serviceAccountName", "") == service.runtime_sa,
            f"{service.name}: runtime SA {spec.get('serviceAccountName', '')} "
            f"!= {service.runtime_sa}",
            failures,
        )

        annotations = template.get("metadata", {}).get("annotations", {})
        _check(
            annotations.get("autoscaling.knative.dev/maxScale", "")
            == str(service.caps["max_instances"]),
            f"{service.name}: maxScale "
            f"{annotations.get('autoscaling.knative.dev/maxScale', '')} != "
            f"{service.caps['max_instances']}",
            failures,
        )
        _check(
            annotations.get("autoscaling.knative.dev/minScale", "0")
            == str(service.caps["min_instances"]),
            f"{service.name}: minScale "
            f"{annotations.get('autoscaling.knative.dev/minScale', '')} != "
            f"{service.caps['min_instances']}",
            failures,
        )

        resources = container.get("resources", {})
        limits = resources.get("limits", {}) if isinstance(resources, dict) else {}
        _check(
            str(limits.get("cpu", "")) == str(service.caps["cpu"]),
            f"{service.name}: cpu limit {limits.get('cpu', '')} != {service.caps['cpu']}",
            failures,
        )
        _check(
            str(limits.get("memory", "")) == str(service.caps["memory"]),
            f"{service.name}: memory limit {limits.get('memory', '')} "
            f"!= {service.caps['memory']}",
            failures,
        )
        _check(
            str(spec.get("timeoutSeconds", ""))
            == str(service.caps["timeout_seconds"]),
            f"{service.name}: timeoutSeconds {spec.get('timeoutSeconds', '')} "
            f"!= {service.caps['timeout_seconds']}",
            failures,
        )
        _check(
            str(spec.get("containerConcurrency", ""))
            == str(service.caps["concurrency"]),
            f"{service.name}: containerConcurrency "
            f"{spec.get('containerConcurrency', '')} != {service.caps['concurrency']}",
            failures,
        )
        _check(
            annotations.get("run.googleapis.com/cpu-throttling", "true") == "false",
            f"{service.name}: cpu throttling enabled (contract: disabled)",
            failures,
        )

        labels = _service_labels_from_live(live)
        for key, value in CLOUD_RUN_LABELS.items():
            _check(
                labels.get(key) == value,
                f"{service.name}: label {key}={labels.get(key)} != {value}",
                failures,
            )

    if "ngabo-core" in live_by_name and "ngabo-web" in live_by_name:
        core_policy = _service_iam_policy("ngabo-core")
        web_policy = _service_iam_policy("ngabo-web")
        core_public = _public_invoker_members(core_policy)
        web_public = _public_invoker_members(web_policy)
        _check(
            not core_public,
            f"ngabo-core: unexpected public invoker members {core_public}",
            failures,
        )
        _check(
            "allUsers" in web_public,
            f"ngabo-web: missing public allUsers invoker binding (got {web_public})",
            failures,
        )
        _check(
            _has_web_runtime_invoker(core_policy),
            "ngabo-core: ngabo-web-runtime lacks roles/run.invoker binding",
            failures,
        )

        core_url = resolve_core_url()
        web_env = _service_env_from_live(live_by_name["ngabo-web"])
        _check(
            web_env.get(CORE_URL_ENV) == core_url,
            f"ngabo-web: CORE_API_URL {web_env.get(CORE_URL_ENV)} != actual "
            f"core status.url {core_url}",
            failures,
        )

        core_env = _service_env_from_live(live_by_name["ngabo-core"])
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
    except (TypeError, ValueError) as exc:
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
