"""Deterministic WHONET-style CSV parser and normalizer (M2.2 / Issue #39).

Parses synthetic WHONET-style tabular microbiology data into canonical
isolate candidates and typed ``CanonicalIsolate`` / ``CanonicalImportBatch``
entities using the #30 schema and #38 validation boundaries.

Key invariants:
- Deterministic CSV stream parsing: stdlib csv in strict mode with physical
  line number tracking via ``csv.reader.line_num``.
- Source-oriented column names: default mapping connects WHONET CSV headers
  (e.g. ``ISOLATE_ID``, ``COLLECTION_DATE``, ``ORGANISM_CODE``, ``AMK``)
  to canonical fields.
- Synthetic-only identifier enforcement: ``facility_id``, ``lab_id``,
  ``ward``, ``patient_token``, and ``source_import_id`` must match the #30
  schema pattern ``^SYNTH-[A-Z0-9-]+$``. Real/unprefixed identifiers fail
  closed with structured ``INVALID_SYNTHETIC_ID`` errors.
- Blank-row policy:
  - Leading blank lines before header: rejected with ``MALFORMED_CSV_ROW``;
  - Trailing blank lines after final record: ignored as EOF padding;
  - Interior blank rows between data records: fail closed with
    ``MALFORMED_CSV_ROW``.
- Narrow deterministic normalization:
  - Whitespace trimming on headers and cell values;
  - Supported susceptibility interpretations mapped to ``Interpretation``:
    ``"S"`` -> ``Interpretation.SUSCEPTIBLE``
    ``"I"`` -> ``Interpretation.INTERMEDIATE``
    ``"R"`` -> ``Interpretation.RESISTANT``
    ``"UNKNOWN"`` -> ``Interpretation.UNKNOWN``
  - Exact ISO ``YYYY-MM-DD`` full calendar date validation;
  - Construction of typed ``AstObservation`` and ``CanonicalIsolate``;
  - Preservation of source row order and stable isolate IDs.
- Fail-closed structured errors: malformed rows, missing headers, missing
  required values, invalid AST columns, unsupported susceptibility values,
  non-synthetic identifiers, or canonical validation failures emit
  structured ``WhonetParserError``s with physical row number, column name,
  isolate ID context, and diagnostic detail.
- Multi-error collection: independent row and field errors are collected
  across the batch in deterministic order (physical row order -> canonical
  field order -> AST column order).
- Duplicate isolate IDs remain preserved in source order for Issue #40.
  No hashing, no deduplication, no replay logic is performed here.
- Framework-free: depends only on Python stdlib and ngabo domain entities.
"""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import TextIO

from ngabo.domain.entities.ast_observation import AstObservation
from ngabo.domain.entities.canonical_import_batch import CanonicalImportBatch
from ngabo.domain.entities.canonical_isolate import (
    ANTIBIOTIC_CODE_PATTERN,
    ISOLATE_ID_PATTERN,
    SYNTHETIC_ID_PATTERN,
    CanonicalIsolate,
)
from ngabo.domain.enums.interpretation import Interpretation
from ngabo.domain.services.import_validation import validate_isolate_candidate
from ngabo.interfaces.parsers.whonet_parse_result import WhonetParseResult
from ngabo.interfaces.parsers.whonet_parser_error import WhonetParserError
from ngabo.interfaces.parsers.whonet_parser_error_code import WhonetParserErrorCode

DEFAULT_WHONET_COLUMN_MAPPING: MappingProxyType[str, str] = MappingProxyType(
    {
        "ISOLATE_ID": "isolate_id",
        "COLLECTION_DATE": "collection_date",
        "ORGANISM_CODE": "organism_code",
        "ORGANISM_NAME": "organism_name",
        "FACILITY_ID": "facility_id",
        "LAB_ID": "lab_id",
        "WARD": "ward",
        "SPECIMEN_TYPE": "specimen_type",
        "PATIENT_TOKEN": "patient_token",
        "SOURCE_IMPORT_ID": "source_import_id",
    }
)
"""Default v0.1 synthetic WHONET-style source column to canonical field mapping."""

_CANONICAL_TO_SOURCE_ORDER = (
    "isolate_id",
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
"""Fixed canonical metadata field ordering for deterministic field error reporting."""

SYNTHETIC_ID_PATTERN = SYNTHETIC_ID_PATTERN
"""Exact #30 synthetic identifier pattern: SYNTH- prefix with uppercase alphanumerics/dashes."""

_SYNTHETIC_ID_FIELDS = frozenset(
    {
        "facility_id",
        "lab_id",
        "ward",
        "patient_token",
        "source_import_id",
    }
)
"""Canonical fields required to carry synthetic identifiers matching SYNTHETIC_ID_PATTERN."""

ACCEPTED_INTERPRETATIONS: MappingProxyType[str, Interpretation] = MappingProxyType(
    {
        "S": Interpretation.SUSCEPTIBLE,
        "I": Interpretation.INTERMEDIATE,
        "R": Interpretation.RESISTANT,
        "UNKNOWN": Interpretation.UNKNOWN,
    }
)
"""Exact accepted raw susceptibility tokens and their Interpretation enum mappings."""

_COLLECTION_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
"""Exact canonical date shape: YYYY-MM-DD."""


def parse_whonet_csv(
    source: str | TextIO | Path,
    *,
    column_mapping: Mapping[str, str] | None = None,
    ast_columns: tuple[str, ...] | None = None,
) -> WhonetParseResult:
    """Parse and normalize a WHONET-style CSV into canonical isolate records.

    Args:
        source: CSV content as a string, an open text stream, or a Path.
        column_mapping: Optional mapping from source column names to canonical
            field names. Defaults to ``DEFAULT_WHONET_COLUMN_MAPPING``.
        ast_columns: Optional tuple of antimicrobial codes allowed as AST
            observation columns. When None, any column matching
            ``^[A-Z]{2,6}$`` that is not in ``column_mapping`` is treated as
            an AST column.

    Returns:
        A ``WhonetParseResult`` containing either validated ``CanonicalIsolate``
        records and a ``CanonicalImportBatch`` (on success) or a tuple of
        structured ``WhonetParserError`` instances (on failure).
    """
    mapping = column_mapping if column_mapping is not None else DEFAULT_WHONET_COLUMN_MAPPING
    raw_text = _read_source(source)
    if not raw_text or not raw_text.strip():
        return WhonetParseResult(
            success=False,
            records=(),
            batch=None,
            errors=(
                WhonetParserError(
                    code=WhonetParserErrorCode.EMPTY_CSV,
                    row_number=None,
                    record_index=None,
                    column=None,
                    record_id=None,
                    detail="CSV content is empty",
                ),
            ),
        )

    reader = csv.reader(io.StringIO(raw_text), strict=True)
    header: list[str] | None = None
    header_line_num: int = 1
    detected_ast_columns: list[str] = []
    header_errors: list[WhonetParserError] = []

    stream_errors: list[WhonetParserError] = []
    data_records: list[tuple[int, list[str], int]] = []
    pending_empty_rows: list[int] = []

    start_line = 1
    try:
        for raw_row in reader:
            end_line = reader.line_num
            is_empty = not raw_row or all(not cell.strip() for cell in raw_row)

            if header is None:
                if is_empty:
                    stream_errors.append(
                        WhonetParserError(
                            code=WhonetParserErrorCode.MALFORMED_CSV_ROW,
                            row_number=start_line,
                            record_index=None,
                            column=None,
                            record_id=None,
                            detail="unexpected blank line before CSV header",
                        )
                    )
                else:
                    header = [cell.strip() for cell in raw_row]
                    header_line_num = start_line
                    header_errors, detected_ast_columns = _validate_header(
                        header_row=header,
                        header_line_num=header_line_num,
                        mapping=mapping,
                        configured_ast_columns=ast_columns,
                    )
            else:
                if is_empty:
                    pending_empty_rows.append(start_line)
                else:
                    if pending_empty_rows:
                        for empty_start in pending_empty_rows:
                            stream_errors.append(
                                WhonetParserError(
                                    code=WhonetParserErrorCode.MALFORMED_CSV_ROW,
                                    row_number=empty_start,
                                    record_index=len(data_records),
                                    column=None,
                                    record_id=None,
                                    detail="unexpected blank row between CSV data records",
                                )
                            )
                        pending_empty_rows.clear()

                    record_idx = len(data_records)
                    data_records.append(
                        (start_line, [cell.strip() for cell in raw_row], record_idx)
                    )

            start_line = end_line + 1
    except csv.Error as exc:
        if pending_empty_rows:
            for empty_start in pending_empty_rows:
                stream_errors.append(
                    WhonetParserError(
                        code=WhonetParserErrorCode.MALFORMED_CSV_ROW,
                        row_number=empty_start,
                        record_index=len(data_records),
                        column=None,
                        record_id=None,
                        detail="unexpected blank row between CSV data records",
                    )
                )
            pending_empty_rows.clear()
        stream_errors.append(
            WhonetParserError(
                code=WhonetParserErrorCode.MALFORMED_CSV_ROW,
                row_number=reader.line_num,
                record_index=len(data_records) if header is not None else None,
                column=None,
                record_id=None,
                detail=f"CSV format error: {exc}",
            )
        )

    if header is None:
        header_missing_errors = tuple(stream_errors) if stream_errors else (
            WhonetParserError(
                code=WhonetParserErrorCode.EMPTY_CSV,
                row_number=None,
                record_index=None,
                column=None,
                record_id=None,
                detail="CSV contains no header row",
            ),
        )
        return WhonetParseResult(
            success=False,
            records=(),
            batch=None,
            errors=header_missing_errors,
        )

    if header_errors:
        all_header_errors = stream_errors + header_errors
        all_header_errors.sort(
            key=lambda e: (
                e.row_number if e.row_number is not None else 0,
                e.record_index if e.record_index is not None else -1,
            )
        )
        return WhonetParseResult(
            success=False,
            records=(),
            batch=None,
            errors=tuple(all_header_errors),
        )

    if not data_records and not stream_errors:
        return WhonetParseResult(
            success=False,
            records=(),
            batch=None,
            errors=(
                WhonetParserError(
                    code=WhonetParserErrorCode.EMPTY_CSV,
                    row_number=header_line_num,
                    record_index=None,
                    column=None,
                    record_id=None,
                    detail="CSV contains a header but no data rows",
                ),
            ),
        )

    # Invert mapping: canonical field -> source column header in this CSV
    field_to_col: dict[str, str] = {}
    for src_col, canon_field in mapping.items():
        if src_col in header:
            field_to_col[canon_field] = src_col

    errors: list[WhonetParserError] = list(stream_errors)
    parsed_isolates: list[CanonicalIsolate] = []

    for row_start_line, row_cells, record_idx in data_records:
        if len(row_cells) != len(header):
            errors.append(
                WhonetParserError(
                    code=WhonetParserErrorCode.MALFORMED_CSV_ROW,
                    row_number=row_start_line,
                    record_index=record_idx,
                    column=None,
                    record_id=None,
                    detail=f"row has {len(row_cells)} columns; expected {len(header)}",
                )
            )
            continue

        row_dict = {header[i]: row_cells[i] for i in range(len(header))}
        isolate_col = field_to_col.get("isolate_id")
        raw_isolate_id = row_dict.get(isolate_col, "") if isolate_col else ""
        record_id = (
            raw_isolate_id
            if raw_isolate_id and ISOLATE_ID_PATTERN.fullmatch(raw_isolate_id)
            else None
        )

        row_errors, typed_opt = _parse_and_validate_row(
            row_dict=row_dict,
            row_line_num=row_start_line,
            record_idx=record_idx,
            record_id=record_id,
            field_to_col=field_to_col,
            detected_ast_columns=detected_ast_columns,
        )
        if row_errors:
            errors.extend(row_errors)
        elif typed_opt is not None:
            parsed_isolates.append(typed_opt)

    if errors:
        errors.sort(
            key=lambda e: (
                e.row_number if e.row_number is not None else 0,
                e.record_index if e.record_index is not None else -1,
            )
        )
        return WhonetParseResult(
            success=False,
            records=(),
            batch=None,
            errors=tuple(errors),
        )

    batch = CanonicalImportBatch(records=tuple(parsed_isolates))
    return WhonetParseResult(
        success=True,
        records=tuple(parsed_isolates),
        batch=batch,
        errors=(),
    )


def _read_source(source: str | TextIO | Path) -> str:
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8")
    if isinstance(source, str):
        return source
    if hasattr(source, "read"):
        return source.read()
    raise TypeError(
        f"Unsupported source type: {type(source)!r}; expected str, Path, or TextIO"
    )


def _validate_header(
    header_row: list[str],
    header_line_num: int,
    mapping: Mapping[str, str],
    configured_ast_columns: tuple[str, ...] | None,
) -> tuple[list[WhonetParserError], list[str]]:
    errors: list[WhonetParserError] = []
    seen: list[str] = []

    # Check for duplicate headers
    for col in header_row:
        if col in seen:
            errors.append(
                WhonetParserError(
                    code=WhonetParserErrorCode.DUPLICATE_COLUMN_HEADER,
                    row_number=header_line_num,
                    record_index=None,
                    column=col,
                    record_id=None,
                    detail=f"duplicate column header {col!r}",
                )
            )
        else:
            seen.append(col)

    # Check required metadata columns in mapping definition order
    for src_col in mapping:
        if src_col not in header_row:
            errors.append(
                WhonetParserError(
                    code=WhonetParserErrorCode.MISSING_REQUIRED_COLUMN,
                    row_number=header_line_num,
                    record_index=None,
                    column=src_col,
                    record_id=None,
                    detail=f"missing required column {src_col!r}",
                )
            )

    # Check AST columns
    detected_ast: list[str] = []
    for col in header_row:
        if col in mapping:
            continue
        if configured_ast_columns is not None:
            if col in configured_ast_columns:
                detected_ast.append(col)
            else:
                errors.append(
                    WhonetParserError(
                        code=WhonetParserErrorCode.INVALID_AST_COLUMN,
                        row_number=header_line_num,
                        record_index=None,
                        column=col,
                        record_id=None,
                        detail=f"column {col!r} is not in the configured AST column list",
                    )
                )
        else:
            if ANTIBIOTIC_CODE_PATTERN.fullmatch(col):
                detected_ast.append(col)
            else:
                errors.append(
                    WhonetParserError(
                        code=WhonetParserErrorCode.INVALID_AST_COLUMN,
                        row_number=header_line_num,
                        record_index=None,
                        column=col,
                        record_id=None,
                        detail=(
                            f"invalid AST column {col!r}; expected antimicrobial "
                            f"code matching {ANTIBIOTIC_CODE_PATTERN.pattern}"
                        ),
                    )
                )

    return errors, detected_ast


def _parse_and_validate_row(
    row_dict: dict[str, str],
    row_line_num: int,
    record_idx: int,
    record_id: str | None,
    field_to_col: dict[str, str],
    detected_ast_columns: list[str],
) -> tuple[list[WhonetParserError], CanonicalIsolate | None]:
    row_errors: list[WhonetParserError] = []

    # Validate metadata fields in fixed canonical order
    field_values: dict[str, str] = {}
    for canon_field in _CANONICAL_TO_SOURCE_ORDER:
        src_col = field_to_col.get(canon_field)
        val = row_dict.get(src_col, "").strip() if src_col else ""
        field_values[canon_field] = val

        if not val:
            row_errors.append(
                WhonetParserError(
                    code=WhonetParserErrorCode.MISSING_REQUIRED_VALUE,
                    row_number=row_line_num,
                    record_index=record_idx,
                    column=src_col,
                    record_id=record_id,
                    detail=f"missing required value for {canon_field} (column {src_col!r})",
                )
            )
            continue

        if canon_field == "isolate_id":
            if not ISOLATE_ID_PATTERN.fullmatch(val):
                row_errors.append(
                    WhonetParserError(
                        code=WhonetParserErrorCode.INVALID_ISOLATE_ID,
                        row_number=row_line_num,
                        record_index=record_idx,
                        column=src_col,
                        record_id=record_id,
                        detail=f"invalid isolate ID {val!r}; expected {ISOLATE_ID_PATTERN.pattern}",
                    )
                )
        elif canon_field == "collection_date":
            if not _COLLECTION_DATE_PATTERN.fullmatch(val):
                row_errors.append(
                    WhonetParserError(
                        code=WhonetParserErrorCode.INVALID_COLLECTION_DATE,
                        row_number=row_line_num,
                        record_index=record_idx,
                        column=src_col,
                        record_id=record_id,
                        detail="expected a valid ISO calendar date (YYYY-MM-DD)",
                    )
                )
            else:
                try:
                    date.fromisoformat(val)
                except ValueError:
                    row_errors.append(
                        WhonetParserError(
                            code=WhonetParserErrorCode.INVALID_COLLECTION_DATE,
                            row_number=row_line_num,
                            record_index=record_idx,
                            column=src_col,
                            record_id=record_id,
                            detail="expected a valid ISO calendar date (YYYY-MM-DD)",
                        )
                    )
        elif canon_field in _SYNTHETIC_ID_FIELDS and not SYNTHETIC_ID_PATTERN.fullmatch(val):
            row_errors.append(
                WhonetParserError(
                    code=WhonetParserErrorCode.INVALID_SYNTHETIC_ID,
                    row_number=row_line_num,
                    record_index=record_idx,
                    column=src_col,
                    record_id=record_id,
                    detail=(
                        f"invalid synthetic identifier {val!r} for {canon_field}; "
                        f"expected pattern {SYNTHETIC_ID_PATTERN.pattern}"
                    ),
                )
            )

    # Validate AST observations in header column order
    row_ast_results: dict[str, Interpretation] = {}
    for ast_col in detected_ast_columns:
        cell_val = row_dict.get(ast_col, "").strip()
        if not cell_val:
            continue
        interp = ACCEPTED_INTERPRETATIONS.get(cell_val)
        if interp is None:
            row_errors.append(
                WhonetParserError(
                    code=WhonetParserErrorCode.INVALID_AST_VALUE,
                    row_number=row_line_num,
                    record_index=record_idx,
                    column=ast_col,
                    record_id=record_id,
                    detail=(
                        f"unsupported susceptibility interpretation {cell_val!r}; "
                        "expected S, I, R, or UNKNOWN"
                    ),
                )
            )
        else:
            row_ast_results[ast_col] = interp

    # If no field errors so far, check that AST results are not empty
    if not row_errors and not row_ast_results:
        row_errors.append(
            WhonetParserError(
                code=WhonetParserErrorCode.EMPTY_AST_RESULTS,
                row_number=row_line_num,
                record_index=record_idx,
                column=None,
                record_id=record_id,
                detail="isolate record must contain at least one AST observation",
            )
        )

    if row_errors:
        return row_errors, None

    # Construct raw candidate mapping for #38 validation
    candidate: dict[str, object] = {
        "isolate_id": field_values["isolate_id"],
        "collection_date": field_values["collection_date"],
        "organism_code": field_values["organism_code"],
        "organism_name": field_values["organism_name"],
        "facility_id": field_values["facility_id"],
        "lab_id": field_values["lab_id"],
        "ward": field_values["ward"],
        "specimen_type": field_values["specimen_type"],
        "patient_token": field_values["patient_token"],
        "source_import_id": field_values["source_import_id"],
        "ast_results": {
            code: {"interpretation": interp.value}
            for code, interp in row_ast_results.items()
        },
    }

    # Verify against #38 canonical import validation boundary
    report = validate_isolate_candidate(candidate)
    if not report.valid:
        for err in report.errors:
            row_errors.append(
                WhonetParserError(
                    code=WhonetParserErrorCode.CANONICAL_VALIDATION_ERROR,
                    row_number=row_line_num,
                    record_index=record_idx,
                    column=err.field,
                    record_id=record_id,
                    detail=f"canonical validation error: {err.code.value} on {err.field}",
                )
            )
        return row_errors, None

    # Construct typed domain entities
    typed_ast = {
        code: AstObservation(interp)
        for code, interp in row_ast_results.items()
    }
    typed_isolate = CanonicalIsolate(
        isolate_id=field_values["isolate_id"],
        collection_date=date.fromisoformat(field_values["collection_date"]),
        organism_code=field_values["organism_code"],
        organism_name=field_values["organism_name"],
        facility_id=field_values["facility_id"],
        lab_id=field_values["lab_id"],
        ward=field_values["ward"],
        specimen_type=field_values["specimen_type"],
        patient_token=field_values["patient_token"],
        source_import_id=field_values["source_import_id"],
        ast_results=typed_ast,
    )

    return [], typed_isolate
