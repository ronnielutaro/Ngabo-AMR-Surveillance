"""Stable verification error-code vocabulary (M1B.5 / Issue #29).

Exactly the eight error families the deterministic claim verifier needs for
routing, repair, telemetry and evaluation, per
``docs/PROOF_CARRYING_REASONING.md`` §6–7, ``docs/AGENT_ARCHITECTURE.md`` §7
and ADR 0009. Smallest stable taxonomy covering the required families — no
speculative codes for mechanisms that do not exist yet.

Codes:

- ``UNKNOWN_RECORD_REFERENCE`` — a referenced canonical record ID does not
  exist in the current incident context.
- ``UNKNOWN_FINDING_REFERENCE`` — a referenced deterministic finding ID is
  unknown for this incident/run/version.
- ``UNKNOWN_EVIDENCE_SOURCE`` — a referenced evidence source was never
  actually retrieved and approved for this package. One code covers both
  "unknown" and "unretrieved": the governing contract gives no useful
  deterministic distinction between the two.
- ``UNSUPPORTED_FACTUAL_ASSERTION`` — the claim asserts a fact that the
  referenced canonical record/finding/evidence values do not support.
- ``CLAIM_TYPE_EPISTEMIC_MISMATCH`` — the claim's epistemic stance does not
  match its claim type (e.g. a hypothesis stated as an observed fact).
- ``FORBIDDEN_CLAIM_OR_AUTHORITY`` — the claim attempts a forbidden
  authority or escalates authority (diagnosis, prescription, outbreak
  confirmation, mandatory containment, official public-health declaration,
  or any authority the v0.1 claim vocabulary cannot express).
- ``STALE_REFERENCE_OR_VERSION`` — a referenced record/finding/source
  version or package state no longer matches current incident truth.
- ``MISSING_UNCERTAINTY`` — a claim that requires explicit
  uncertainty/limitations carries none.

``UNKNOWN_FINDING_REFERENCE`` and ``UNSUPPORTED_FACTUAL_ASSERTION`` are
preserved verbatim from PROOF_CARRYING_REASONING §7. Aggregate repair
outcomes such as ``VALIDATION_FAILED`` (§8) are workflow states, not
per-claim error codes, and are deliberately outside this vocabulary.

A code identifies the error family only — it is vocabulary, not a
verification result. Per-claim detail lives on ``ClaimVerificationError``
and the aggregate pass/fail result on ``ClaimVerificationReport``.
"""

from __future__ import annotations

from enum import StrEnum


class VerificationErrorCode(StrEnum):
    """The eight stable claim-verification error families (v0.1)."""

    UNKNOWN_RECORD_REFERENCE = "UNKNOWN_RECORD_REFERENCE"
    UNKNOWN_FINDING_REFERENCE = "UNKNOWN_FINDING_REFERENCE"
    UNKNOWN_EVIDENCE_SOURCE = "UNKNOWN_EVIDENCE_SOURCE"
    UNSUPPORTED_FACTUAL_ASSERTION = "UNSUPPORTED_FACTUAL_ASSERTION"
    CLAIM_TYPE_EPISTEMIC_MISMATCH = "CLAIM_TYPE_EPISTEMIC_MISMATCH"
    FORBIDDEN_CLAIM_OR_AUTHORITY = "FORBIDDEN_CLAIM_OR_AUTHORITY"
    STALE_REFERENCE_OR_VERSION = "STALE_REFERENCE_OR_VERSION"
    MISSING_UNCERTAINTY = "MISSING_UNCERTAINTY"
