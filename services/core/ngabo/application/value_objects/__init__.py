"""Application-level value objects (Issue #44)."""

from __future__ import annotations

from ngabo.application.value_objects.canonical_import_result import CanonicalImportResult
from ngabo.application.value_objects.import_error_detail import ImportErrorDetail

__all__ = [
    "CanonicalImportResult",
    "ImportErrorDetail",
]
