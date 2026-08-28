"""Immutable result of canonical source import orchestration (Issue #44)."""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.application.enums.import_outcome_disposition import ImportOutcomeDisposition
from ngabo.application.value_objects.import_error_detail import ImportErrorDetail
from ngabo.domain.entities.canonical_import_batch import CanonicalImportBatch
from ngabo.domain.value_objects.duplicate_record_finding import DuplicateRecordFinding
from ngabo.domain.value_objects.source_digest import SourceDigest
from ngabo.domain.value_objects.source_watermark import SourceWatermark


@dataclass(frozen=True)
class CanonicalImportResult:
    """Deterministic, immutable result of a canonical import use case invocation."""

    success: bool
    disposition: ImportOutcomeDisposition
    source_key: str
    raw_digest: SourceDigest | None = None
    watermark: SourceWatermark | None = None
    batch: CanonicalImportBatch | None = None
    exact_duplicates: tuple[DuplicateRecordFinding, ...] = ()
    errors: tuple[ImportErrorDetail, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError(f"Invalid success {self.success!r}; expected bool")
        if not isinstance(self.disposition, ImportOutcomeDisposition):
            raise TypeError(
                f"Invalid disposition {self.disposition!r}; expected ImportOutcomeDisposition"
            )
        if not isinstance(self.source_key, str) or not self.source_key.strip():
            raise ValueError("source_key must be a non-empty string")
        if not isinstance(self.exact_duplicates, tuple):
            raise TypeError(
                f"Invalid exact_duplicates {self.exact_duplicates!r}; expected tuple"
            )
        for dup in self.exact_duplicates:
            if not isinstance(dup, DuplicateRecordFinding):
                raise TypeError(
                    f"Invalid exact_duplicate element {dup!r}; expected DuplicateRecordFinding"
                )
        if not isinstance(self.errors, tuple):
            raise TypeError(f"Invalid errors {self.errors!r}; expected tuple")
        for err in self.errors:
            if not isinstance(err, ImportErrorDetail):
                raise TypeError(
                    f"Invalid error element {err!r}; expected ImportErrorDetail"
                )

        if self.success:
            if self.disposition not in (
                ImportOutcomeDisposition.FIRST_IMPORT,
                ImportOutcomeDisposition.EXACT_REPLAY,
                ImportOutcomeDisposition.MATERIAL_CHANGE,
            ):
                raise ValueError(
                    f"Successful import cannot have disposition {self.disposition!r}"
                )
            if self.raw_digest is None or not isinstance(self.raw_digest, SourceDigest):
                raise ValueError("Successful import requires a valid raw_digest (SourceDigest)")
            if self.watermark is None or not isinstance(self.watermark, SourceWatermark):
                raise ValueError("Successful import requires a valid watermark (SourceWatermark)")
            if self.batch is None or not isinstance(self.batch, CanonicalImportBatch):
                raise ValueError("Successful import requires a valid batch (CanonicalImportBatch)")
            if self.errors:
                raise ValueError("Successful import must not contain errors")
        else:
            if self.disposition != ImportOutcomeDisposition.FAILED:
                raise ValueError(
                    f"Failed import must have disposition FAILED; got {self.disposition!r}"
                )
            if self.batch is not None:
                raise ValueError("Failed import must not have an accepted batch")
            if self.watermark is not None:
                raise ValueError("Failed import must not have a watermark")
            if not self.errors:
                raise ValueError("Failed import must contain at least one error")
            if self.raw_digest is not None and not isinstance(self.raw_digest, SourceDigest):
                raise TypeError(
                    f"Invalid raw_digest {self.raw_digest!r}; expected SourceDigest or None"
                )
