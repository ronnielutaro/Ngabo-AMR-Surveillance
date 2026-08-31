"""Stable failure codes for the incident package parse boundary (#52).

The framework-free parser converts malformed/fragmentary model-produced
primitives into stable typed outcomes rather than exposing bare ``ValueError``
as the only contract. These codes exist for deterministic routing later;
they carry no verification or authority semantics.

Codes:

- ``MALFORMED_PACKAGE`` — the primitive is not the correct basic shape/type.
- ``UNSUPPORTED_PACKAGE_VERSION`` — the package contract version is not the
  supported v0.1 version.
- ``DUPLICATE_CLAIM_ID`` — two claims share one claim identity.
- ``FORBIDDEN_FIELD`` — an unknown/unauthorized field (incl. ``verified``,
  ``authorized``, ``ready_to_send``) is present; strict allowlist rejected it.
- ``MISSING_REQUIRED_FIELD`` — a required field is absent.
- ``INVALID_REFERENCE_SHAPE`` — a proof/evidence reference does not match its
  required typed shape.
- ``MUTABLE_OR_INVALID_COLLECTION_SHAPE`` — a collection has the wrong shape
  (e.g. a dict where a list is required, or vice versa).
"""

from __future__ import annotations

from enum import StrEnum


class IncidentPackageErrorCode(StrEnum):
    """Stable failure family for incident package parsing/construction."""

    MALFORMED_PACKAGE = "MALFORMED_PACKAGE"
    UNSUPPORTED_PACKAGE_VERSION = "UNSUPPORTED_PACKAGE_VERSION"
    DUPLICATE_CLAIM_ID = "DUPLICATE_CLAIM_ID"
    FORBIDDEN_FIELD = "FORBIDDEN_FIELD"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_REFERENCE_SHAPE = "INVALID_REFERENCE_SHAPE"
    MUTABLE_OR_INVALID_COLLECTION_SHAPE = "MUTABLE_OR_INVALID_COLLECTION_SHAPE"
