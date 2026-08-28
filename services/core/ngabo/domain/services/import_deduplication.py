"""Deterministic canonical import deduplication service (Issue #40).

Enforces the dataset-level isolate uniqueness invariant:
'Every isolate_id MUST be unique within one canonical dataset.'

Behavioral rules (M2.3 / Issue #40):
- Unique records: preserved in their exact input source order;
- Exact duplicate records: collapsed into one logical canonical record (at the
  first occurrence index), with all duplicate occurrences documented in
  ``DuplicateRecordFinding`` instances;
- Conflicting duplicate records: FAIL CLOSED. If two records share an
  ``isolate_id`` but differ in any material canonical field, an
  ``ImportDeduplicationError`` is emitted detailing the differing fields and
  indices. No heuristic merge, no first-wins, no last-wins, no guessing;
- Deduplicated batch: on success, emits a validated ``CanonicalImportBatch``
  preserving original source order, and computes a deterministic,
  order-independent ``SourceWatermark``.
"""

from __future__ import annotations

from ngabo.domain.entities.canonical_import_batch import CanonicalImportBatch
from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.enums.import_deduplication_error_code import ImportDeduplicationErrorCode
from ngabo.domain.services.source_identity import (
    compute_isolate_fingerprint,
    compute_source_watermark,
)
from ngabo.domain.value_objects.duplicate_record_finding import DuplicateRecordFinding
from ngabo.domain.value_objects.import_deduplication_error import ImportDeduplicationError
from ngabo.domain.value_objects.import_deduplication_report import ImportDeduplicationReport

_MATERIAL_METADATA_FIELDS = (
    "collection_date",
    "organism_code",
    "organism_name",
    "facility_id",
    "lab_id",
    "ward",
    "specimen_type",
    "patient_token",
    "source_import_id",
)


def _find_differing_fields(
    rec_a: CanonicalIsolate,
    rec_b: CanonicalIsolate,
) -> tuple[str, ...]:
    """Identify which canonical fields differ between two records."""
    differing: list[str] = []
    for field_name in _MATERIAL_METADATA_FIELDS:
        if getattr(rec_a, field_name) != getattr(rec_b, field_name):
            differing.append(field_name)
    if rec_a.ast_results != rec_b.ast_results:
        differing.append("ast_results")
    return tuple(differing)


def deduplicate_canonical_batch(
    batch: CanonicalImportBatch,
) -> ImportDeduplicationReport:
    """Deduplicate an imported canonical batch and compute its source watermark.

    Args:
        batch: A validated ``CanonicalImportBatch`` containing imported records.

    Returns:
        An ``ImportDeduplicationReport`` containing:
        - on success: the deduplicated ``batch``, the computed ``watermark``,
          any ``exact_duplicates`` findings, and empty ``errors``;
        - on failure: ``batch=None``, ``watermark=None``, any documented
          ``exact_duplicates``, and structured ``errors`` detailing conflicts.
    """
    if not isinstance(batch, CanonicalImportBatch):
        raise TypeError(f"Invalid batch {batch!r}; expected CanonicalImportBatch")

    if not batch.records:
        error = ImportDeduplicationError(
            code=ImportDeduplicationErrorCode.EMPTY_BATCH,
            isolate_id=None,
            indices=(),
            differing_fields=(),
            detail="Batch contains no records to deduplicate",
        )
        return ImportDeduplicationReport(
            success=False,
            batch=None,
            watermark=None,
            exact_duplicates=(),
            errors=(error,),
        )

    unique_records: list[CanonicalIsolate] = []
    # isolate_id -> (first_record, first_fingerprint, first_index)
    seen_isolates: dict[str, tuple[CanonicalIsolate, str, int]] = {}
    # isolate_id -> list of subsequent duplicate indices
    duplicate_map: dict[str, list[int]] = {}
    conflicts: list[ImportDeduplicationError] = []

    for record_idx, record in enumerate(batch.records):
        iso_id = record.isolate_id
        curr_fingerprint = compute_isolate_fingerprint(record)

        if iso_id not in seen_isolates:
            seen_isolates[iso_id] = (record, curr_fingerprint, record_idx)
            unique_records.append(record)
        else:
            first_record, first_fingerprint, first_idx = seen_isolates[iso_id]
            if curr_fingerprint == first_fingerprint:
                if iso_id not in duplicate_map:
                    duplicate_map[iso_id] = []
                duplicate_map[iso_id].append(record_idx)
            else:
                differing = _find_differing_fields(first_record, record)
                diff_summary = ", ".join(differing) if differing else "unspecified"
                conflicts.append(
                    ImportDeduplicationError(
                        code=ImportDeduplicationErrorCode.CONFLICTING_DUPLICATE_RECORD,
                        isolate_id=iso_id,
                        indices=(first_idx, record_idx),
                        differing_fields=differing,
                        detail=(
                            f"conflicting duplicate records for isolate_id {iso_id!r} "
                            f"at indices ({first_idx}, {record_idx}); "
                            f"differing fields: {diff_summary}"
                        ),
                    )
                )

    exact_findings: list[DuplicateRecordFinding] = []
    for iso_id, dup_indices in duplicate_map.items():
        _, _, first_idx = seen_isolates[iso_id]
        exact_findings.append(
            DuplicateRecordFinding(
                isolate_id=iso_id,
                occurrences=1 + len(dup_indices),
                original_index=first_idx,
                duplicate_indices=tuple(dup_indices),
            )
        )
    exact_findings.sort(key=lambda f: f.original_index)

    if conflicts:
        conflicts.sort(key=lambda c: c.indices[0])
        return ImportDeduplicationReport(
            success=False,
            batch=None,
            watermark=None,
            exact_duplicates=tuple(exact_findings),
            errors=tuple(conflicts),
        )

    deduped_batch = CanonicalImportBatch(records=tuple(unique_records))
    watermark = compute_source_watermark(unique_records)
    return ImportDeduplicationReport(
        success=True,
        batch=deduped_batch,
        watermark=watermark,
        exact_duplicates=tuple(exact_findings),
        errors=(),
    )
