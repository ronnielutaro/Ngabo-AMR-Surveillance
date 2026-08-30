"""Guarded delivery, promotion and rollback helpers for Ngabo.

Issue #91 contract: an approved merge may build once and deploy the exact
immutable digest(s) of the changed service(s) to dev, and a maintainer may
promote or roll back to a previously tested digest without rebuilding or
mutating the frozen judged environment. Every step writes sanitized evidence
and a failed/stale gate must fail closed.

This module is Python-stdlib-only so it runs in the trusted GitHub Actions
lanes (python3) without uv, matching ``infra/github/container_evidence.py``.

Service identity is the immutable ``sha256:<64 hex>`` digest. Tags are
navigation only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SHORT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

SERVICES: tuple[str, ...] = ("core", "web")

# Path prefixes that map a changed file to an affected service. Anything
# shared/cross-cutting (infra, workflows, actions, lockfiles, root build
# config) affects both and must be delivered as a coordinated change.
CORE_PREFIXES: tuple[str, ...] = ("services/core/",)
WEB_PREFIXES: tuple[str, ...] = (
    "apps/web/",
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
)
SHARED_PREFIXES: tuple[str, ...] = (
    "infra/",
    ".github/workflows/",
    ".github/actions/",
    "scripts/",
    ".gitignore",
    "Dockerfile",
    "Makefile",
)

# Evidence fields that must never be recorded (secrets, credentials, personal
# identity, billing identifiers).
FORBIDDEN_KEY_PATTERNS: tuple[str, ...] = (
    "token",
    "secret",
    "credential",
    "password",
    "key_id",
    "private_key",
    "billing",
    "email",
    "account_email",
    "access_token",
)

FORBIDDEN_VALUE_PATTERNS: tuple[str, ...] = (
    "BEGIN PRIVATE KEY",
    "AIza",
    "gha-creds-",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "client_secret",
    "AKIA",
    "@gmail.com",
)


class DeliveryError(Exception):
    """Raised when a delivery/promotion/rollback precondition fails."""


def affected_services(changed_paths: list[str]) -> list[str]:
    """Return the sorted, de-duplicated services affected by `changed_paths`.

    ``core``/``web`` are returned when an owned path changed. A shared or
    cross-cutting path returns both so the change is delivered atomically. An
    unrelated (e.g. docs-only) change returns an empty list, meaning no
    delivery is required.
    """
    touched: set[str] = set()
    for path in changed_paths:
        normalized = path.strip().replace("\\", "/")
        if any(normalized.startswith(p) for p in CORE_PREFIXES):
            touched.add("core")
        if any(normalized.startswith(p) for p in WEB_PREFIXES):
            touched.add("web")
        if any(normalized.startswith(p) for p in SHARED_PREFIXES):
            touched.update(SERVICES)
    return sorted(touched)


def validate_digest(digest: str) -> bool:
    """Return True iff `digest` is an immutable ``sha256:<64 hex>`` reference."""
    return bool(DIGEST_RE.fullmatch(str(digest or "")))


def is_stale(current_sha: str, run_sha: str) -> bool:
    """Return True when the supplied run head no longer matches develop head."""
    return run_sha != current_sha


def _sanitize(value: Any) -> Any:
    """Recursively strip forbidden keys and redact forbidden values."""
    if isinstance(value, dict):
        return {
            key: _sanitize(val)
            for key, val in value.items()
            if not any(p in str(key).lower() for p in FORBIDDEN_KEY_PATTERNS)
        }
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, str):
        text = value
        for pattern in FORBIDDEN_VALUE_PATTERNS:
            if pattern.lower() in text.lower():
                return "<redacted>"
        return text
    return value


def validate_record(record: dict[str, Any]) -> None:
    """Fail closed when a delivery record lacks the required bindings."""
    required = ("environment", "commit_sha", "workflow_run_id", "actor", "timestamp")
    for field in required:
        if not record.get(field):
            raise DeliveryError(f"delivery record missing required field '{field}'")
    for service in SERVICES:
        digest = record.get(f"{service}_digest")
        if digest and not validate_digest(str(digest)):
            raise DeliveryError(f"invalid {service} digest {digest!r}")
    if record.get("created_at"):
        raise DeliveryError("record must not contain a 'created_at' key")


def write_evidence(record: dict[str, Any], output_path: str) -> None:
    """Sanitize, validate and write a delivery evidence JSON document."""
    validate_record(record)
    sanitized = _sanitize(dict(record))
    Path(output_path).write_text(
        json.dumps(sanitized, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_evidence(path: str) -> dict[str, Any]:
    """Load and validate a delivery evidence document."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise DeliveryError("evidence is not a JSON object")
    validate_record(data)
    return data


def previous_known_good(evidence: dict[str, Any], service: str) -> str | None:
    """Return the immediately previous known-good digest for ``service``."""
    prev = evidence.get("previous_known_good")
    if not isinstance(prev, dict):
        return None
    digest = prev.get(f"{service}_digest")
    return str(digest) if digest and validate_digest(str(digest)) else None


def evidence_check(
    record: dict[str, Any], core_digest: str, web_digest: str
) -> None:
    """Fail closed unless the record is a matching, smoke-passing delivery."""
    if record.get("smoke_result") != "pass":
        raise DeliveryError(
            f"evidence smoke_result is {record.get('smoke_result')!r}, not 'pass'"
        )
    if record.get("core_digest") != core_digest:
        raise DeliveryError(
            f"evidence core digest {record.get('core_digest')} != {core_digest}"
        )
    if record.get("web_digest") != web_digest:
        raise DeliveryError(
            f"evidence web digest {record.get('web_digest')} != {web_digest}"
        )


def rollback_check(
    record: dict[str, Any], core_digest: str, web_digest: str
) -> None:
    """Fail closed unless the digests equal the recorded previous known-good."""
    prev = record.get("previous_known_good")
    if not isinstance(prev, dict) or not prev.get("core_digest") or not prev.get(
        "web_digest"
    ):
        raise DeliveryError("evidence has no previous_known_good to roll back to")
    if prev.get("core_digest") != core_digest:
        raise DeliveryError(
            f"previous known-good core digest {prev.get('core_digest')} != {core_digest}"
        )
    if prev.get("web_digest") != web_digest:
        raise DeliveryError(
            f"previous known-good web digest {prev.get('web_digest')} != {web_digest}"
        )


def evidence_from_env() -> dict[str, Any]:
    """Build a delivery record from CI environment variables (no heredocs)."""
    record: dict[str, Any] = {
        "environment": os.environ.get("DELIVERY_ENVIRONMENT", "dev"),
        "commit_sha": os.environ.get("DELIVERY_COMMIT") or os.environ.get("GITHUB_SHA", ""),
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "actor": os.environ.get("GITHUB_ACTOR", ""),
        "timestamp": os.environ.get("DELIVERY_TIMESTAMP", ""),
        "core_digest": os.environ.get("CORE_DIGEST", ""),
        "web_digest": os.environ.get("WEB_DIGEST", ""),
        "core_revision": os.environ.get("CORE_REVISION", ""),
        "web_revision": os.environ.get("WEB_REVISION", ""),
        "smoke_result": os.environ.get("DELIVERY_SMOKE_RESULT", "pass"),
    }
    if os.environ.get("DELIVERY_REASON"):
        record["reason"] = os.environ["DELIVERY_REASON"]
    if os.environ.get("DELIVERY_TARGET"):
        record["target_environment"] = os.environ["DELIVERY_TARGET"]
    if os.environ.get("DELIVERY_PREVIOUS_GOOD"):
        record["previous_known_good"] = json.loads(os.environ["DELIVERY_PREVIOUS_GOOD"])
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    affected = sub.add_parser("affected", help="print affected services as JSON")
    affected.add_argument("--paths-file", required=True)

    stale = sub.add_parser("stale", help="fail closed when the run is stale")
    stale.add_argument("--current")
    stale.add_argument("--run")

    evidence = sub.add_parser("evidence", help="write sanitized delivery evidence")
    evidence.add_argument("--output", required=True)
    evidence.add_argument("--record", required=True, help="path to raw record JSON")

    evidence_env = sub.add_parser("evidence-env", help="write evidence from CI env")
    evidence_env.add_argument("--output", required=True)

    evidence_check_parser = sub.add_parser(
        "evidence-check", help="verify a record's digests and smoke result"
    )
    evidence_check_parser.add_argument("--record", required=True, help="evidence JSON")
    evidence_check_parser.add_argument("--core-digest", required=True)
    evidence_check_parser.add_argument("--web-digest", required=True)

    rollback_check_parser = sub.add_parser(
        "rollback-check", help="verify digests are the recorded previous known-good"
    )
    rollback_check_parser.add_argument("--record", required=True)
    rollback_check_parser.add_argument("--core-digest", required=True)
    rollback_check_parser.add_argument("--web-digest", required=True)

    args = parser.parse_args(argv)
    if args.command == "affected":
        paths = [
            line.strip()
            for line in Path(args.paths_file).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        print(json.dumps(affected_services(paths)))
        return 0
    if args.command == "stale":
        if is_stale(os.environ.get("DELIVERY_CURRENT_SHA", args.current or ""),
                    os.environ.get("DELIVERY_RUN_SHA", args.run or "")):
            print("STALE: develop head has advanced; this run must not deploy.")
            return 3
        print("CURRENT: no stale overwrite.")
        return 0
    if args.command == "evidence":
        record = json.loads(Path(args.record).read_text(encoding="utf-8"))
        write_evidence(record, args.output)
        print(f"WROTE {args.output}")
        return 0
    if args.command == "evidence-env":
        write_evidence(evidence_from_env(), args.output)
        print(f"WROTE {args.output}")
        return 0
    if args.command == "evidence-check":
        record = load_evidence(args.record)
        evidence_check(record, args.core_digest, args.web_digest)
        print("EVIDENCE_OK: digests and smoke result match the successful delivery.")
        return 0
    if args.command == "rollback-check":
        record = load_evidence(args.record)
        rollback_check(record, args.core_digest, args.web_digest)
        print("ROLLBACK_OK: digests are the recorded previous known-good.")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
