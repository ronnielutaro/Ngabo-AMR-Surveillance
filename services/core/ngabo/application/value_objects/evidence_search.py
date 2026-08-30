"""Framework-free approved-evidence retrieval contracts (Issue #51).

``EvidenceSearchQuery`` is the inbound request; ``EvidenceSearchHit`` is one
approved retrieved chunk; ``EvidenceSearchResult`` is the typed, versioned
outcome. These are the contracts the future Gemini/ADK layer consumes without
knowing how local retrieval is implemented.

Two modes are supported:

1. **Keyword/tag search** — ``query_text`` is non-blank and the adapter matches
   approved chunks by deterministic normalization/tags/score. The optional
   ``source_ids`` narrow the scope.
2. **Exact reference lookup** — ``reference_ids`` is non-empty; the adapter
   retrieves exactly those approved references and fails closed on any
   approval/version/integrity condition.

The optional ``requested_source_versions`` pins a source version for the
stale-version fail-closed test: if a requested source's manifest version
differs, the adapter returns ``STALE_SOURCE``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ngabo.application.enums.evidence_search_outcome import EvidenceSearchOutcome
from ngabo.domain.value_objects.evidence_reference import (
    EvidenceReferenceId,
    EvidenceSourceId,
)


@dataclass(frozen=True)
class EvidenceSearchQuery:
    """Inbound approved-evidence retrieval request."""

    query_text: str = ""
    source_ids: tuple[EvidenceSourceId, ...] = ()
    reference_ids: tuple[EvidenceReferenceId, ...] = ()
    requested_source_versions: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.query_text, str):
            raise ValueError("query_text must be a str")
        if not isinstance(self.source_ids, tuple):
            raise ValueError(f"Invalid source_ids {self.source_ids!r}; expected a tuple")
        for index, source_id in enumerate(self.source_ids):
            if not isinstance(source_id, EvidenceSourceId):
                raise ValueError(
                    f"Invalid source_id at position {index}: {source_id!r}; "
                    "expected an EvidenceSourceId"
                )
        if not isinstance(self.reference_ids, tuple):
            raise ValueError(
                f"Invalid reference_ids {self.reference_ids!r}; expected a tuple"
            )
        for index, reference_id in enumerate(self.reference_ids):
            if not isinstance(reference_id, EvidenceReferenceId):
                raise ValueError(
                    f"Invalid reference_id at position {index}: {reference_id!r}; "
                    "expected an EvidenceReferenceId"
                )
        if not isinstance(self.requested_source_versions, Mapping):
            raise ValueError(
                "requested_source_versions must be a Mapping[str, str]"
            )
        for key, value in self.requested_source_versions.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError(
                    f"Invalid requested source version key {key!r}; "
                    "expected a non-blank source ID"
                )
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Invalid requested source version for {key!r}: {value!r}; "
                    "expected non-blank text"
                )

        is_exact_ref = bool(self.reference_ids)
        is_keyword = bool(self.query_text.strip())
        has_scope = bool(self.source_ids)
        if is_exact_ref:
            # Exact-reference mode; query text/scope are optional.
            return
        if not (is_keyword or has_scope):
            raise ValueError(
                "EvidenceSearchQuery must carry either non-blank query_text "
                "or a non-empty source scope"
            )


@dataclass(frozen=True)
class EvidenceSearchHit:
    """One retrieved approved evidence chunk plus its provenance and score."""

    reference_id: EvidenceReferenceId
    source_id: EvidenceSourceId
    publisher: str
    source_title: str
    canonical_url: str
    publication_date: str
    source_version: str
    attribution_required: bool
    content: str
    chunk_tags: tuple[str, ...]
    score: int

    def __post_init__(self) -> None:
        if not isinstance(self.reference_id, EvidenceReferenceId):
            raise ValueError("reference_id must be an EvidenceReferenceId")
        if not isinstance(self.source_id, EvidenceSourceId):
            raise ValueError("source_id must be an EvidenceSourceId")
        if self.reference_id.source_id != self.source_id.value:
            raise ValueError(
                f"reference_id {self.reference_id!r} must belong to source_id "
                f"{self.source_id!r}"
            )
        for label, value in (
            ("publisher", self.publisher),
            ("source_title", self.source_title),
            ("canonical_url", self.canonical_url),
            ("publication_date", self.publication_date),
            ("source_version", self.source_version),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Invalid {label} {value!r}; expected non-blank text")
        if not isinstance(self.attribution_required, bool):
            raise ValueError("attribution_required must be a bool")
        if not isinstance(self.content, str):
            raise ValueError("content must be a str")
        if not isinstance(self.chunk_tags, tuple):
            raise ValueError(f"Invalid chunk_tags {self.chunk_tags!r}; expected a tuple")
        if not isinstance(self.score, int):
            raise ValueError(f"Invalid score {self.score!r}; expected an int")


@dataclass(frozen=True)
class EvidenceSearchResult:
    """Typed outcome of an approved-evidence retrieval."""

    outcome: EvidenceSearchOutcome
    hits: tuple[EvidenceSearchHit, ...] = ()
    query_text: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, EvidenceSearchOutcome):
            raise ValueError("outcome must be an EvidenceSearchOutcome")
        if not isinstance(self.hits, tuple):
            raise ValueError(f"Invalid hits {self.hits!r}; expected a tuple")
        for index, hit in enumerate(self.hits):
            if not isinstance(hit, EvidenceSearchHit):
                raise ValueError(
                    f"Invalid hit at position {index}: {hit!r}; "
                    "expected an EvidenceSearchHit"
                )
        if not isinstance(self.query_text, str):
            raise ValueError("query_text must be a str")
