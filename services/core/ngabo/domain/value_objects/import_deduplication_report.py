"""Framework-free value object for canonical import deduplication report (Issue #40).

The aggregate immutable result of canonical import deduplication and source
watermarking. Invariant rules:
- success=True requires a non-None CanonicalImportBatch, a non-None
  SourceWatermark, and empty errors;
- success=False requires batch=None, watermark=None, and at least one
  ImportDeduplicationError;
- exact_duplicates records all collapsed duplicate occurrences.
"""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.domain.entities.canonical_import_batch import CanonicalImportBatch
from ngabo.domain.value_objects.duplicate_record_finding import DuplicateRecordFinding
from ngabo.domain.value_objects.import_deduplication_error import ImportDeduplicationError
from ngabo.domain.value_objects.source_watermark import SourceWatermark


@dataclass(frozen=True)
class ImportDeduplicationReport:
    """Immutable aggregate outcome of canonical import deduplication."""

    success: bool
    batch: CanonicalImportBatch | None
    watermark: SourceWatermark | None
    exact_duplicates: tuple[DuplicateRecordFinding, ...] = ()
    errors: tuple[ImportDeduplicationError, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError(f"Invalid success {self.success!r}; expected bool")
        if not isinstance(self.exact_duplicates, tuple):
            raise TypeError(
                f"Invalid exact_duplicates {self.exact_duplicates!r}; expected tuple"
            )
        for idx, finding in enumerate(self.exact_duplicates):
            if not isinstance(finding, DuplicateRecordFinding):
                raise TypeError(
                    f"Invalid finding at position {idx}: {finding!r}; "
                    "expected DuplicateRecordFinding"
                )
        if not isinstance(self.errors, tuple):
            raise TypeError(f"Invalid errors {self.errors!r}; expected tuple")
        for idx, error in enumerate(self.errors):
            if not isinstance(error, ImportDeduplicationError):
                raise TypeError(
                    f"Invalid error at position {idx}: {error!r}; "
                    "expected ImportDeduplicationError"
                )

        if self.success:
            if not isinstance(self.batch, CanonicalImportBatch):
                raise ValueError(
                    "A successful deduplication report must provide a CanonicalImportBatch"
                )
            if not isinstance(self.watermark, SourceWatermark):
                raise ValueError(
                    "A successful deduplication report must provide a SourceWatermark"
                )
            if self.errors:
                raise ValueError("A successful deduplication report cannot carry errors")
        else:
            if self.batch is not None:
                raise ValueError(
                    "A failed deduplication report must not provide a CanonicalImportBatch"
                )
            if self.watermark is not None:
                raise ValueError(
                    "A failed deduplication report must not provide a SourceWatermark"
                )
            if not self.errors:
                raise ValueError(
                    "A failed deduplication report must carry at least one error"
                )
