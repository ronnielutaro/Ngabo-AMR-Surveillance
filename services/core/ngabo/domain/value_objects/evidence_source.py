"""Framework-free approved evidence source contract (Issue #51).

``EvidenceSource`` is the provenance-complete record for one source in the
approved evidence manifest. It carries the full provenance set required by
``docs/THIRD_PARTY_PROVENANCE.md`` §5 (source identity, canonical URL,
publication/version date, local content type, usage/license basis,
attribution, approval state) plus the deterministic chunks that may be
retrieved. It holds no retrieval behavior.

Construction enforces structural/type validity only. Provenance
completeness (''no empty/TODO/TBD/unknown fields on an approved source'') is
enforced by :func:`ngabo.domain.services.evidence_provenance.validate_evidence_source`
at the manifest/loader boundary so a committed approved entry cannot reach
the retrieval path incomplete.
"""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.domain.value_objects.evidence_reference import EvidenceChunk, EvidenceSourceId


def _require_nonblank(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected non-blank text")
    return value


@dataclass(frozen=True)
class EvidenceSource:
    """Immutable provenance-complete evidence source manifest entry."""

    source_id: EvidenceSourceId
    publisher: str
    canonical_title: str
    canonical_url: str
    publication_date: str
    source_version: str
    local_content_present: bool
    local_content_type: str
    usage_basis_or_license: str
    attribution_required: bool
    approved_for_retrieval: bool
    notes: str
    retrieval_tags: tuple[str, ...]
    chunks: tuple[EvidenceChunk, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, EvidenceSourceId):
            raise ValueError("source_id must be an EvidenceSourceId")
        _require_nonblank(self.publisher, "publisher")
        _require_nonblank(self.canonical_title, "canonical title")
        _require_nonblank(self.canonical_url, "canonical URL")
        _require_nonblank(self.publication_date, "publication date")
        _require_nonblank(self.source_version, "source version")
        if not isinstance(self.local_content_present, bool):
            raise ValueError("local_content_present must be a bool")
        _require_nonblank(self.local_content_type, "local content type")
        _require_nonblank(self.usage_basis_or_license, "usage basis/license")
        if not isinstance(self.attribution_required, bool):
            raise ValueError("attribution_required must be a bool")
        if not isinstance(self.approved_for_retrieval, bool):
            raise ValueError("approved_for_retrieval must be a bool")
        _require_nonblank(self.notes, "notes")
        if not isinstance(self.retrieval_tags, tuple):
            raise ValueError(f"Invalid retrieval_tags {self.retrieval_tags!r}; expected a tuple")
        for index, tag in enumerate(self.retrieval_tags):
            if not isinstance(tag, str) or not tag.strip():
                raise ValueError(
                    f"Invalid retrieval tag at position {index}: {tag!r}; "
                    "expected non-blank text"
                )
        if not isinstance(self.chunks, tuple):
            raise ValueError(f"Invalid chunks {self.chunks!r}; expected a tuple")
        for index, chunk in enumerate(self.chunks):
            if not isinstance(chunk, EvidenceChunk):
                raise ValueError(
                    f"Invalid chunk at position {index}: {chunk!r}; "
                    "expected an EvidenceChunk"
                )
            if chunk.source_id != self.source_id:
                raise ValueError(
                    f"Chunk {chunk.reference_id!r} must belong to source "
                    f"{self.source_id!r}"
                )
