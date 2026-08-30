"""Load and validate the committed approved-evidence manifest (Issue #51).

Runtime retrieval is local, so the committed ``data/guidance/manifest.json``
plus its ``corpus/`` content files are the source of truth. This loader
parses the JSON into immutable :class:`EvidenceSource` objects, enforces
provenance completeness (via :mod:`ngabo.domain.services.evidence_provenance`),
verifies each chunk's declared content digest against the actual committed
bytes, verifies the manifest's corpus digest reproduces exactly, and enforces
path safety so corpus material can only be read from a trusted manifest-derived
location.

No network/cloud/model access and no arbitrary user path is accepted here.
"""

from __future__ import annotations

import json
from pathlib import Path

from ngabo.domain.services.evidence_provenance import (
    compute_content_digest,
    compute_corpus_digest,
    validate_evidence_corpus,
)
from ngabo.domain.value_objects.evidence_reference import (
    EvidenceChunk,
    EvidenceReferenceId,
    EvidenceSourceId,
)
from ngabo.domain.value_objects.evidence_source import EvidenceSource

MANIFEST_FILENAME = "manifest.json"
DEFAULT_CORPUS_DIRNAME = "corpus"


class EvidenceCorpusLoadError(Exception):
    """Raised when the committed manifest/corpus is invalid or untrusted."""


def _parse_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise EvidenceCorpusLoadError(f"Manifest field {label!r} must be a boolean")
    return value


def _parse_str_tuple(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise EvidenceCorpusLoadError(f"Manifest field {label!r} must be a list")
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise EvidenceCorpusLoadError(
                f"Manifest field {label!r} must contain only non-blank strings"
            )
    return tuple(value)


def _resolve_content_path(corpus_dir: Path, content_path: str) -> Path:
    """Resolve a manifest-relative content path safely within ``corpus_dir``.

    Rejects absolute paths, empty paths, and any ``..`` traversal so corpus
    content can only be read from the trusted manifest-derived corpus folder.
    """
    if not isinstance(content_path, str) or not content_path.strip():
        raise EvidenceCorpusLoadError("chunk content_path must be a non-blank string")
    if content_path.startswith(("/", "\\")) or ":" in content_path:
        raise EvidenceCorpusLoadError(
            f"chunk content_path {content_path!r} must be relative"
        )
    parts = Path(content_path).parts
    if any(part in ("..", "", ".") for part in parts):
        raise EvidenceCorpusLoadError(
            f"chunk content_path {content_path!r} must not traverse directories"
        )
    resolved = (corpus_dir / content_path).resolve()
    if not resolved.is_relative_to(corpus_dir.resolve()):
        raise EvidenceCorpusLoadError(
            f"chunk content_path {content_path!r} resolves outside the corpus directory"
        )
    return resolved


def _chunk_from_dict(
    raw: dict[str, object],
    source_id: EvidenceSourceId,
    corpus_dir: Path,
) -> EvidenceChunk:
    reference_id = raw.get("reference_id")
    content_path = raw.get("content_path")
    content_sha256 = raw.get("content_sha256")
    tags = raw.get("tags")
    if not isinstance(reference_id, str):
        raise EvidenceCorpusLoadError("chunk reference_id must be a string")
    if not isinstance(content_path, str):
        raise EvidenceCorpusLoadError("chunk content_path must be a string")
    if (
        not isinstance(content_sha256, str)
        or len(content_sha256) != 64
        or any(c not in "0123456789abcdef" for c in content_sha256)
    ):
        raise EvidenceCorpusLoadError("chunk content_sha256 must be a 64-hex digest")
    if not isinstance(tags, list):
        raise EvidenceCorpusLoadError("chunk tags must be a list")

    path = _resolve_content_path(corpus_dir, content_path)
    if not path.exists():
        raise EvidenceCorpusLoadError(
            f"chunk {reference_id!r} content path does not exist: {path}"
        )
    content = path.read_text(encoding="utf-8")
    if compute_content_digest(content) != content_sha256:
        raise EvidenceCorpusLoadError(
            f"chunk {reference_id!r} content digest mismatch (tampered or stale content)"
        )

    return EvidenceChunk(
        reference_id=EvidenceReferenceId(reference_id),
        source_id=source_id,
        content=content,
        content_sha256=content_sha256,
        tags=_parse_str_tuple(tags, "chunk tags"),
    )


def _source_from_dict(raw: dict[str, object], corpus_dir: Path) -> EvidenceSource:
    source_id = EvidenceSourceId(_required_str(raw, "source_id"))
    chunks_raw = raw.get("chunks")
    if not isinstance(chunks_raw, list):
        raise EvidenceCorpusLoadError("source chunks must be a list")
    chunks = tuple(
        _chunk_from_dict(entry, source_id, corpus_dir)
        for entry in chunks_raw
        if isinstance(entry, dict)
    )
    if len(chunks) != len(chunks_raw):
        raise EvidenceCorpusLoadError("source chunks must be a list of objects")

    return EvidenceSource(
        source_id=source_id,
        publisher=_required_str(raw, "publisher"),
        canonical_title=_required_str(raw, "canonical_title"),
        canonical_url=_required_str(raw, "canonical_url"),
        publication_date=_required_str(raw, "publication_date"),
        source_version=_required_str(raw, "source_version"),
        local_content_present=_parse_bool(
            raw.get("local_content_present"), "local_content_present"
        ),
        local_content_type=_required_str(raw, "local_content_type"),
        usage_basis_or_license=_required_str(raw, "usage_basis_or_license"),
        attribution_required=_parse_bool(raw.get("attribution_required"), "attribution_required"),
        approved_for_retrieval=_parse_bool(
            raw.get("approved_for_retrieval"), "approved_for_retrieval"
        ),
        notes=_required_str(raw, "notes"),
        retrieval_tags=_parse_str_tuple(raw.get("retrieval_tags", []), "retrieval_tags"),
        chunks=chunks,
    )


def _required_str(raw: dict[str, object], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise EvidenceCorpusLoadError(f"Manifest field {key!r} must be a non-blank string")
    return value


def load_evidence_corpus(
    root: Path,
    *,
    manifest_filename: str = MANIFEST_FILENAME,
    corpus_dirname: str = DEFAULT_CORPUS_DIRNAME,
) -> tuple[EvidenceSource, ...]:
    """Load and validate the approved-evidence corpus rooted at ``root``.

    Args:
        root: Directory containing ``manifest.json`` and the ``corpus/`` folder.
        manifest_filename: Manifest filename within ``root``.
        corpus_dirname: Corpus subdirectory name within ``root``.

    Returns:
        The validated, immutable tuple of approved/unapproved evidence sources.

    Raises:
        EvidenceCorpusLoadError: If the manifest is unreadable, provenance is
            incomplete for an approved source, a chunk hash mismatches, the
            corpus digest does not reproduce, or path safety is violated.
    """
    manifest_path = root / manifest_filename
    if not manifest_path.is_file():
        raise EvidenceCorpusLoadError(
            f"Evidence manifest not found at {manifest_path}"
        )
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvidenceCorpusLoadError(
            f"Evidence manifest is not valid JSON: {exc}"
        ) from exc

    if not isinstance(raw, dict):
        raise EvidenceCorpusLoadError("Evidence manifest must be a JSON object")
    sources_raw = raw.get("sources")
    if not isinstance(sources_raw, list):
        raise EvidenceCorpusLoadError("Evidence manifest 'sources' must be a list")
    corpus_dir = root / corpus_dirname

    sources = tuple(
        _source_from_dict(entry, corpus_dir)
        for entry in sources_raw
        if isinstance(entry, dict)
    )
    if len(sources) != len(sources_raw):
        raise EvidenceCorpusLoadError("Evidence manifest 'sources' must be objects")

    validate_evidence_corpus(sources)

    declared_corpus_digest = raw.get("corpus_sha256")
    actual_corpus_digest = compute_corpus_digest(sources)
    if declared_corpus_digest != actual_corpus_digest:
        raise EvidenceCorpusLoadError(
            "Evidence corpus digest mismatch: manifest declared "
            f"{declared_corpus_digest!r} but recomputed {actual_corpus_digest!r}"
        )

    return sources
