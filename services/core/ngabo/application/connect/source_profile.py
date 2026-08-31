"""Governed synthetic source profile + deterministic normalizer (Epic #171).

Reuses the existing canonical isolate vocabulary. Only ONE governed source profile
is implemented for the demo (``WHONET_DEMO_V1``). It performs deterministic alias
mapping (messy WHONET-style display forms -> canonical codes), and quarantines any
row it cannot unambiguously normalize. It never invokes a model.
"""

from __future__ import annotations

import re
from datetime import date

from ngabo.application.connect.contracts import (
    AcceptedRecord,
    DataQualityReport,
    QuarantinedRecord,
    SourceProfile,
)

_DATE_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
_CANONICAL_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


WHONET_DEMO_V1 = SourceProfile(
    name="WHONET_DEMO_V1",
    version="1.0",
    organism_aliases={
        "KPN": "kle",
        "K. pneumoniae": "kle",
        "K pneumoniae": "kle",
        "Klebsiella pneumoniae": "kle",
        "kle": "kle",
    },
    organism_name_aliases={
        "K pneumoniae": "Klebsiella pneumoniae",
        "K. pneumoniae": "Klebsiella pneumoniae",
        "Klebsiella pneumoniae": "Klebsiella pneumoniae",
    },
    interpretation_aliases={
        "Resistant": "R",
        "R": "R",
        "Susceptible": "S",
        "S": "S",
        "Intermediate": "I",
        "I": "I",
        "UNKNOWN": "UNKNOWN",
    },
)


def normalize_record(
    row: dict[str, object], profile: SourceProfile
) -> AcceptedRecord | QuarantinedRecord:
    """Normalize one raw row deterministically, or quarantine it.

    Returns an ``AcceptedRecord`` when every required field maps unambiguously,
    otherwise a ``QuarantinedRecord`` with a stable reason code.
    """
    row_index_raw = row.get("row_index", 0)
    row_index = int(row_index_raw) if isinstance(row_index_raw, int) else 0
    organism_code = str(row.get("organism_code", "")).strip()
    if organism_code not in profile.organism_aliases:
        return _quarantine(row_index, "UNKNOWN_ORGANISM_CODE", f"no mapping for {organism_code!r}")
    organism_name_raw = str(row.get("organism_name", "")).strip()
    organism_name = profile.organism_name_aliases.get(
        organism_name_raw, organism_name_raw
    )
    if not organism_name:
        return _quarantine(
            row_index, "MISSING_ORGANISM_NAME", "organism_name is blank"
        )

    collection_date = str(row.get("collection_date", "")).strip()
    canonical_date = _canonical_date(collection_date)
    if canonical_date is None:
        return _quarantine(
            row_index, "INVALID_DATE", f"unparseable collection_date {collection_date!r}"
        )

    ast_raw = row.get("ast_results")
    if not isinstance(ast_raw, dict):
        return _quarantine(row_index, "MISSING_AST", "ast_results must be a mapping")
    ast: dict[str, str] = {}
    for code, raw_interp in ast_raw.items():
        interp = str(raw_interp).strip()
        if interp not in profile.interpretation_aliases:
            return _quarantine(
                row_index,
                "UNKNOWN_INTERPRETATION",
                f"no mapping for AST {code!r}={interp!r}",
            )
        ast[code] = profile.interpretation_aliases[interp]

    required = {
        "isolate_id": "isolate_id",
        "facility_id": "facility_id",
        "lab_id": "lab_id",
        "ward": "ward",
        "specimen_type": "specimen_type",
        "patient_token": "patient_token",
        "source_import_id": "source_import_id",
    }
    values: dict[str, str] = {}
    for field in required.values():
        value = str(row.get(field, "")).strip()
        if not value:
            return _quarantine(row_index, "MISSING_REQUIRED_FIELD", f"{field} is blank")
        values[field] = value

    return AcceptedRecord(
        isolate_id=values["isolate_id"],
        organism_code=profile.organism_aliases[organism_code],
        organism_name=organism_name,
        collection_date=canonical_date,
        facility_id=values["facility_id"],
        lab_id=values["lab_id"],
        ward=values["ward"],
        specimen_type=values["specimen_type"],
        patient_token=values["patient_token"],
        source_import_id=values["source_import_id"],
        ast_results=ast,
        row_index=row_index,
    )


def clean_rows(
    rows: list[dict[str, object]],
    profile: SourceProfile,
) -> tuple[list[AcceptedRecord], list[QuarantinedRecord], DataQualityReport]:
    """Run a full deterministic cleaning pass over ``rows``."""
    accepted: list[AcceptedRecord] = []
    quarantined: list[QuarantinedRecord] = []
    normalized = 0
    for index, row in enumerate(rows):
        if "row_index" not in row:
            row = dict(row)
            row["row_index"] = index
        result = normalize_record(row, profile)
        if isinstance(result, AcceptedRecord):
            accepted.append(result)
            normalized += 1
        else:
            quarantined.append(result)
    report = DataQualityReport(
        received_count=len(rows),
        accepted_count=len(accepted),
        quarantined_count=len(quarantined),
        normalization_count=normalized,
    )
    return accepted, quarantined, report


def _canonical_date(value: str) -> str | None:
    value = value.strip()
    if _CANONICAL_DATE_RE.fullmatch(value):
        return value
    m = _DATE_RE.fullmatch(value)
    if m is None:
        return None
    day, month, year = m.groups()
    try:
        canonical = date(int(year), int(month), int(day))
    except ValueError:
        return None
    return canonical.isoformat()


def _quarantine(row_index: int, code: str, detail: str) -> QuarantinedRecord:
    return QuarantinedRecord(row_index=row_index, reason_code=code, detail=detail)
