"""Stable typed reason codes for the bounded package-candidate synthesis stage (#56).

These describe WHY the #56 synthesis stage sank to ``BLOCKED`` / ``FAILED`` /
``NO_EVIDENCE``. They are deterministic and machine-checkable; they carry no
verification or authority semantics.
"""

from __future__ import annotations

from enum import StrEnum


class PackageCandidateErrorCode(StrEnum):
    """Deterministic reason a #56 synthesis stage did not generate a package."""

    ENTRY_GATE_NOT_READY = "ENTRY_GATE_NOT_READY"
    """The #54 result was not READY_FOR_DOWNSTREAM or the #55 result was not
    EVIDENCE_RETRIEVED, so synthesis must not begin."""

    NO_APPROVED_EVIDENCE = "NO_APPROVED_EVIDENCE"
    """The #55 outcome reported no approved evidence hits, so synthesis has no
    grounded authority to build a candidate on."""

    MALFORMED_MODEL_OUTPUT = "MALFORMED_MODEL_OUTPUT"
    """The model produced no recognizable structured package payload."""

    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    """The model output did not satisfy the structured synthesis schema."""

    FORBIDDEN_SEMANTIC = "FORBIDDEN_SEMANTIC"
    """The model output asserted an authority/completion/verification semantic
    (e.g. VERIFIED, APPROVED, OUTBREAK_CONFIRMED) that must fail closed."""

    UNKNOWN_SUPPORT_REFERENCE = "UNKNOWN_SUPPORT_REFERENCE"
    """A claim referenced a record/finding/evidence/support ID that was NOT in
    the supplied support manifest (covers fabricated/unknown references)."""

    URL_AS_SUPPORT = "URL_AS_SUPPORT"
    """A claim used a URL/domain as a support reference instead of an opaque
    Ngabo-owned reference ID."""

    FORBIDDEN_CLAIM_SHAPE = "FORBIDDEN_CLAIM_SHAPE"
    """A non-hypothesis claim carried no support reference, or a reference had
    the wrong family shape for its claim family."""

    INVALID_SUPPORT_MANIFEST = "INVALID_SUPPORT_MANIFEST"
    """The support manifest itself could not be constructed/unambiguous."""

    PACKAGE_PARSE_FAILED = "PACKAGE_PARSE_FAILED"
    """The schema-validated payload failed the strict #52 package parser (bad
    shape, forbidden field, duplicate claim ID, invalid reference)."""

    MODEL_TIMEOUT = "MODEL_TIMEOUT"
    """The model invocation exceeded the bounded runtime deadline."""

    MODEL_PROVIDER_FAILURE = "MODEL_PROVIDER_FAILURE"
    """The model provider/runtime failed."""

    RATE_LIMIT = "RATE_LIMIT"
    """The model provider returned a rate-limit/quota error."""

    MODEL_BUDGET_EXCEEDED = "MODEL_BUDGET_EXCEEDED"
    """The invocation made more model calls than the per-run hard budget."""
