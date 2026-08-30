"""Spike verifier error-code vocabulary (Issue #49).

The spike issue requests stable structured verifier codes for the capability
proof. The certified ``VerificationErrorCode`` vocabulary (#29) is
deliberately closed (exactly nine families, guarded by a regression test), so
this issue-scoped vocabulary carries the spike-specific codes the issue
names without mutating the certified contract. Reference-existence checks map
onto the certified ``UNKNOWN_*_REFERENCE`` families at the boundary; the
additional ``MALFORMED_PROOF`` / ``REQUIRED_BRANCH_FAILED`` outcomes are
spike-workflow states and live here.

Codes:
- ``UNKNOWN_RECORD_REFERENCE`` — referenced canonical record ID does not exist.
- ``UNKNOWN_FINDING_REFERENCE`` — referenced deterministic finding ID does not exist.
- ``UNKNOWN_SOURCE_REFERENCE`` — referenced evidence source ID does not exist.
- ``MALFORMED_PROOF`` — the structured claim could not satisfy the DTO/schema.
- ``REQUIRED_BRANCH_FAILED`` — a required deterministic parallel branch failed.
"""

from __future__ import annotations

from enum import StrEnum


class SpikeVerificationCode(StrEnum):
    """Stable error-family vocabulary used by the spike deterministic verifier."""

    UNKNOWN_RECORD_REFERENCE = "UNKNOWN_RECORD_REFERENCE"
    UNKNOWN_FINDING_REFERENCE = "UNKNOWN_FINDING_REFERENCE"
    UNKNOWN_SOURCE_REFERENCE = "UNKNOWN_SOURCE_REFERENCE"
    MALFORMED_PROOF = "MALFORMED_PROOF"
    REQUIRED_BRANCH_FAILED = "REQUIRED_BRANCH_FAILED"
