"""Deterministic validator for the #92 cloud-foundation certification evidence.

The bundle must be redacted (no credentials, personal email, billing
identifiers) and must carry the authoritative source commit, immutable
digests, governance/identity/artifact/delivery assertions, and an honest
residual-risk list. This module is stdlib-only so it runs in trusted lanes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

REQUIRED_TOP = (
    "certification_schema",
    "certified_at",
    "source_commit",
    "repository",
    "ci",
    "infrastructure",
    "identity",
    "artifacts",
    "dev_delivery",
    "browser",
    "failure_recovery",
    "promotion",
    "cost_bounds",
    "freeze_policy",
    "residual_risks",
)

FORBIDDEN_PATTERNS = (
    "BEGIN PRIVATE KEY",
    "AIza",
    "gha-creds-",
    "@gmail.com",
    "client_secret",
    "AKIA",
    "billing_account",
    "billing_id",
)


class FoundationEvidenceError(Exception):
    """Raised when the evidence bundle is invalid or leaks sensitive data."""


def _has(record: dict[str, Any], key: str) -> bool:
    if key not in record or record[key] in (None, "", [], {}):
        raise FoundationEvidenceError(f"evidence missing required field '{key}'")
    return True


def validate(record: dict[str, Any]) -> bool:
    """Fail closed unless ``record`` satisfies the certification schema."""
    for key in REQUIRED_TOP:
        _has(record, key)

    artifacts = record["artifacts"]
    for service in ("core", "web"):
        _has(artifacts, service)
        digest = artifacts[service]["digest"]
        if not DIGEST_RE.fullmatch(str(digest)):
            raise FoundationEvidenceError(f"invalid {service} digest {digest!r}")
        if artifacts[service].get("scan") != "PASS":
            raise FoundationEvidenceError(f"{service} scan must be PASS")

    for path in (
        ("infrastructure", "reproducible"),
        ("infrastructure", "converged"),
        ("identity", "wif_keyless"),
        ("identity", "least_privilege"),
        ("identity", "runtime_identities_separated"),
        ("failure_recovery", "broken_revision_promoted"),
        ("promotion", "no_rebuild"),
        ("promotion", "digest_parity"),
    ):
        node: Any = record
        for part in path:
            if not isinstance(node, dict) or part not in node:
                raise FoundationEvidenceError(
                    f"evidence missing required field '{'.'.join(path)}'"
                )
            node = node[part]
        if not isinstance(node, bool):
            raise FoundationEvidenceError(f"{'.'.join(path)} must be boolean")

    text = json.dumps(record)
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.lower() in text.lower():
            raise FoundationEvidenceError(f"evidence leaks sensitive value '{pattern}'")
    return True


def load_evidence(path: str) -> dict[str, Any]:
    """Load and validate the evidence bundle."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise FoundationEvidenceError("evidence is not a JSON object")
    validate(data)
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True)
    args = parser.parse_args(argv)
    try:
        load_evidence(args.file)
    except FoundationEvidenceError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print("VALID: foundation evidence bundle acceptable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
