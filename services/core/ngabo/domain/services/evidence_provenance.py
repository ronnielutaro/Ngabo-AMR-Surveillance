"""Deterministic evidence-provenance and integrity checks (Issue #51).

These pure functions enforce the two controls that make the approved-evidence
boundary real rather than documentation:

- :func:`validate_evidence_source` / :func:`validate_evidence_corpus` reject an
  *approved* source whose provenance is incomplete (empty or placeholder
  fields) or whose manifest has duplicate/unowned identities. An unapproved
  source may carry a placeholder for history/provenance, but can never be
  retrieved as authority.
- :func:`compute_content_digest` / :func:`compute_corpus_digest` produce the
  deterministic SHA-256 digests the manifest (content/chunk) and a corpus-wide
  digest (canonical manifest + corpus identity) that must reproduce exactly.

No model, cloud, filesystem or framework dependency lives here.
"""

from __future__ import annotations

import hashlib

from ngabo.domain.value_objects.evidence_reference import EvidenceChunk
from ngabo.domain.value_objects.evidence_source import EvidenceSource

# Placeholder tokens that may never appear in an APPROVED source's provenance.
_PLACEHOLDERS = frozenset({"todo", "tbd", "unknown", "n/a", "verify later", "later"})


def _contains_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in _PLACEHOLDERS or any(
        normalized.startswith(f"{token} ") or normalized.endswith(f" {token}")
        for token in _PLACEHOLDERS
    )


def compute_content_digest(content: str) -> str:
    """SHA-256 (hex) of the exact UTF-8 bytes of ``content``."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def compute_corpus_digest(sources: tuple[EvidenceSource, ...]) -> str:
    """Deterministic corpus-wide SHA-256 digest.

    Chunks are canonicalized by ``reference_id`` (ascending) and each chunk
    contributes its reference ID and content digest. Manifest/source
    declaration ordering cannot change the digest. The committed manifest's
    ``corpus_sha256`` must equal this recomputation.
    """
    chunks: list[EvidenceChunk] = []
    for source in sources:
        chunks.extend(source.chunks)
    chunks.sort(key=lambda chunk: chunk.reference_id.value)

    hasher = hashlib.sha256()
    for chunk in chunks:
        hasher.update(chunk.reference_id.value.encode("utf-8"))
        hasher.update(b"\x00")
        hasher.update(compute_content_digest(chunk.content).encode("ascii"))
        hasher.update(b"\x00")
    return hasher.hexdigest()


def validate_evidence_source(source: EvidenceSource) -> None:
    """Fail closed on an approved source with incomplete provenance.

    Approved sources must be complete and retrievable: every provenance field
    is non-blank and free of placeholder tokens, local content is present, and
    at least one chunk exists. Unapproved sources are structural only — they
    remain in the manifest for provenance/history but cannot be retrieved.
    """
    if not source.approved_for_retrieval:
        return

    provenance_fields = (
        ("publisher", source.publisher),
        ("canonical_title", source.canonical_title),
        ("canonical_url", source.canonical_url),
        ("publication_date", source.publication_date),
        ("source_version", source.source_version),
        ("local_content_type", source.local_content_type),
        ("usage_basis_or_license", source.usage_basis_or_license),
        ("notes", source.notes),
    )
    for label, value in provenance_fields:
        if not value.strip() or _contains_placeholder(value):
            raise ValueError(
                f"Approved source {source.source_id!r} has incomplete "
                f"{label!r}: {value!r}; placeholders are not allowed on an "
                "approved source"
            )

    if not source.local_content_present:
        raise ValueError(
            f"Approved source {source.source_id!r} declares no local content "
            "but is approved_for_retrieval=true"
        )
    if not source.chunks:
        raise ValueError(
            f"Approved source {source.source_id!r} has no chunks; an approved "
            "source cannot be retrieval authority without retrievable content"
        )


def validate_evidence_corpus(sources: tuple[EvidenceSource, ...]) -> None:
    """Validate the whole manifest: per-source completeness plus identity uniqueness."""
    seen_source_ids: set[str] = set()
    seen_reference_ids: set[str] = set()
    for source in sources:
        validate_evidence_source(source)
        if source.source_id.value in seen_source_ids:
            raise ValueError(f"Duplicate evidence source ID {source.source_id!r}")
        seen_source_ids.add(source.source_id.value)
        for chunk in source.chunks:
            if chunk.reference_id.value in seen_reference_ids:
                raise ValueError(
                    f"Duplicate evidence reference ID {chunk.reference_id!r}"
                )
            seen_reference_ids.add(chunk.reference_id.value)
