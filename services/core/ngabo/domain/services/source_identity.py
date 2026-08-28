"""Deterministic source identity, artifact digest, and watermark service (Issue #40).

Defines cryptographic source identity for raw input artifacts and canonical
logical AMR datasets. Key distinctions:

- Raw source digest: Answers 'What exact bytes/file did we receive?'
  (cryptographic SHA-256 over exact UTF-8 bytes). Changes on whitespace,
  quoting, line-endings, or row reordering.
- Canonical source watermark: Answers 'What deterministic canonical AMR state
  did those observations represent?' Serializes all material canonical fields
  into a versioned, sorted, whitespace-compact JSON structure and hashes via
  SHA-256, returning a version-prefixed ``SourceWatermark`` token
  (``ngabo-source-v1:sha256:<hex>``). It is order-independent over unique records
  and AST observation map order.
- Replay comparison: Pure function comparing two ``SourceWatermark`` instances
  returning ``SourceReplayDisposition`` (``EXACT_REPLAY`` vs ``MATERIAL_CHANGE``).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence

from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.enums.source_replay_disposition import SourceReplayDisposition
from ngabo.domain.value_objects.source_digest import SourceDigest
from ngabo.domain.value_objects.source_watermark import SourceWatermark

CANONICAL_SOURCE_VERSION = "ngabo-source-v1"
"""Canonical serialization format version for logical source watermarks."""

CANONICAL_HASH_ALGORITHM = "sha256"
"""Standard cryptographic hash algorithm used for source digests and watermarks."""


def compute_raw_source_digest(source: bytes | str) -> SourceDigest:
    """Compute deterministic SHA-256 digest of raw source content bytes.

    Args:
        source: Raw file bytes or a string. If a string is provided, it is
            encoded using explicit UTF-8.

    Returns:
        A ``SourceDigest`` containing the lowercase 64-character SHA-256 hex digest.
    """
    if isinstance(source, str):
        raw_bytes = source.encode("utf-8")
    elif isinstance(source, (bytes, bytearray)):
        raw_bytes = bytes(source)
    else:
        raise TypeError(
            f"Unsupported source type: {type(source)!r}; expected bytes or str"
        )
    hex_digest = hashlib.sha256(raw_bytes).hexdigest().lower()
    return SourceDigest(algorithm=CANONICAL_HASH_ALGORITHM, hex_digest=hex_digest)


def serialize_canonical_isolate_to_dict(record: CanonicalIsolate) -> dict[str, object]:
    """Serialize a ``CanonicalIsolate`` into a canonical dictionary representation.

    All 11 material canonical fields are accounted for explicitly:
    - ``isolate_id``: canonical isolate identifier;
    - ``collection_date``: ISO-8601 calendar date (YYYY-MM-DD);
    - ``organism_code``: canonical organism code;
    - ``organism_name``: canonical organism name;
    - ``facility_id``: synthetic facility identifier;
    - ``lab_id``: synthetic laboratory identifier;
    - ``ward``: synthetic ward identifier;
    - ``specimen_type``: specimen category;
    - ``patient_token``: synthetic patient token;
    - ``source_import_id``: synthetic source import batch ID;
    - ``ast_results``: susceptibility observations canonically sorted by
      antimicrobial code key.

    Args:
        record: A validated ``CanonicalIsolate`` instance.

    Returns:
        A standard dictionary suitable for deterministic JSON canonicalization.
    """
    if not isinstance(record, CanonicalIsolate):
        raise TypeError(f"Invalid record {record!r}; expected CanonicalIsolate")

    return {
        "isolate_id": record.isolate_id,
        "collection_date": record.collection_date.isoformat(),
        "organism_code": record.organism_code,
        "organism_name": record.organism_name,
        "facility_id": record.facility_id,
        "lab_id": record.lab_id,
        "ward": record.ward,
        "specimen_type": record.specimen_type,
        "patient_token": record.patient_token,
        "source_import_id": record.source_import_id,
        "ast_results": {
            code: {"interpretation": record.ast_results[code].interpretation.value}
            for code in sorted(record.ast_results.keys())
        },
    }


def compute_isolate_fingerprint(record: CanonicalIsolate) -> str:
    """Compute a deterministic 64-character SHA-256 fingerprint for a single record.

    Used for per-record identity comparison and duplicate conflict detection.

    Args:
        record: A validated ``CanonicalIsolate`` instance.

    Returns:
        A 64-character lowercase hexadecimal string.
    """
    canon_dict = serialize_canonical_isolate_to_dict(record)
    canonical_bytes = json.dumps(
        canon_dict,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest().lower()


def compute_source_watermark(records: Sequence[CanonicalIsolate]) -> SourceWatermark:
    """Compute a deterministic ``SourceWatermark`` over a collection of canonical records.

    In accordance with Issue #40 and ADR 0006/0008:
    - Logical dataset order-independence: records are sorted by ``isolate_id``
      before hashing, ensuring that reordered rows representing the same
      underlying unique observations produce the identical source watermark;
    - Field determinism: all 11 material fields are serialized using canonical
      JSON formatting (sorted keys, compact separators, UTF-8);
    - Token format: ``ngabo-source-v1:sha256:<64-char-lowercase-hex>``.

    Args:
        records: A sequence of validated unique ``CanonicalIsolate`` records.

    Returns:
        A ``SourceWatermark`` value object wrapping the deterministic token.
    """
    if not isinstance(records, (tuple, list)):
        raise TypeError(
            f"Invalid records {records!r}; expected a tuple or list of CanonicalIsolate"
        )
    for idx, rec in enumerate(records):
        if not isinstance(rec, CanonicalIsolate):
            raise TypeError(
                f"Invalid record at position {idx}: {rec!r}; expected CanonicalIsolate"
            )

    sorted_records = sorted(records, key=lambda r: r.isolate_id)
    payload = {
        "version": CANONICAL_SOURCE_VERSION,
        "records": [serialize_canonical_isolate_to_dict(r) for r in sorted_records],
    }
    canonical_bytes = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    hex_digest = hashlib.sha256(canonical_bytes).hexdigest().lower()
    return SourceWatermark(
        value=f"{CANONICAL_SOURCE_VERSION}:{CANONICAL_HASH_ALGORITHM}:{hex_digest}"
    )


def compare_source_replay(
    current: SourceWatermark,
    previous: SourceWatermark,
) -> SourceReplayDisposition:
    """Compare current and previous source watermarks to determine replay disposition.

    Args:
        current: The watermark computed from the incoming canonical source.
        previous: The watermark of the previously processed canonical source.

    Returns:
        ``SourceReplayDisposition.EXACT_REPLAY`` if watermarks match exactly;
        ``SourceReplayDisposition.MATERIAL_CHANGE`` if watermarks differ.
    """
    if not isinstance(current, SourceWatermark):
        raise TypeError(
            f"Invalid current watermark {current!r}; expected SourceWatermark"
        )
    if not isinstance(previous, SourceWatermark):
        raise TypeError(
            f"Invalid previous watermark {previous!r}; expected SourceWatermark"
        )

    if current == previous:
        return SourceReplayDisposition.EXACT_REPLAY
    return SourceReplayDisposition.MATERIAL_CHANGE
