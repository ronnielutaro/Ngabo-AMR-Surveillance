"""Deterministic local approved-evidence adapter (Issue #51).

Implements :class:`EvidenceSearchPort` against one immutable corpus of
:class:`EvidenceSource` objects. Retrieval is fully local and deterministic:
Unicode normalization, case folding, whitespace splitting, exact tag/keyword
token matching, a documented integer score, and a stable reference-identity
tie-break. No embeddings, no probabilistic ranking, no network, no filesystem
ordering — manifest/source declaration order can never change the semantic
result.

Approval, version and integrity are enforced *before* authority:

- an unapproved source is never returned (keyword search excludes it; an
  exact-reference lookup fails with ``UNAPPROVED_SOURCE``);
- a source pinned to a different version fails with ``STALE_SOURCE``;
- a chunk whose content no longer matches its declared SHA-256 fails with
  ``INTEGRITY_FAILURE``;
- an unknown requested source/reference fails with ``SOURCE_NOT_FOUND``.

Keyword search does **not** collapse an untrusted match into ``NO_MATCH``. It
returns a stable outcome that lets downstream orchestration distinguish "no
relevant evidence exists" from "relevant evidence matched but is not approved"
from "relevant approved evidence matched but integrity verification failed".
When no valid approved hit exists, the deterministic precedence is
``INTEGRITY_FAILURE`` > ``UNAPPROVED_SOURCE`` > ``NO_MATCH``. Rejected
evidence is never returned as authority or as a warning.
"""

from __future__ import annotations

import re
import unicodedata

from ngabo.application.enums.evidence_search_outcome import EvidenceSearchOutcome
from ngabo.application.value_objects.evidence_search import (
    EvidenceSearchHit,
    EvidenceSearchQuery,
    EvidenceSearchResult,
)
from ngabo.domain.services.evidence_provenance import (
    compute_content_digest,
    validate_evidence_corpus,
)
from ngabo.domain.value_objects.evidence_reference import (
    EvidenceChunk,
)
from ngabo.domain.value_objects.evidence_source import EvidenceSource

_NON_WORD = re.compile(r"[^\w]+", re.UNICODE)


def normalize_tokens(text: str) -> tuple[str, ...]:
    """Deterministic query/corpus normalization to a token tuple.

    UTF-8 NFKC normalization, ASCII-compatible lowercasing, then split on any
    run of non-word characters. Both query text and corpus text pass through
    this exactly once, so semantically equivalent input always tokenizes to the
    same tuple.
    """
    normalized = unicodedata.normalize("NFKC", text)
    return tuple(token for token in _NON_WORD.split(normalized.lower()) if token)


def _score_chunk(
    chunk_tokens: tuple[str, ...],
    content_tokens: tuple[str, ...],
    query_tokens: tuple[str, ...],
) -> int:
    """Deterministic relevance score.

    ``score = 2 * |query ∩ tag| + 1 * |query ∩ content|``. Tag matches carry
    more weight than arbitrary content-keyword matches, but both are exact
    normalized-token intersections. ``0`` means no match.
    """
    tag_hits = len(frozenset(query_tokens) & frozenset(chunk_tokens))
    content_hits = len(frozenset(query_tokens) & frozenset(content_tokens))
    return 2 * tag_hits + content_hits


class LocalEvidenceSearch:
    """Deterministic local implementation of :class:`EvidenceSearchPort`."""

    def __init__(self, sources: tuple[EvidenceSource, ...]) -> None:
        # Defensive: the corpus must already pass provenance/identity checks.
        validate_evidence_corpus(sources)
        self._sources = tuple(sorted(sources, key=lambda src: src.source_id.value))
        self._sources_by_id = {src.source_id.value: src for src in self._sources}
        self._chunks_by_ref: dict[str, tuple[EvidenceSource, EvidenceChunk]] = {}
        for source in self._sources:
            for chunk in source.chunks:
                self._chunks_by_ref[chunk.reference_id.value] = (source, chunk)

    def search(self, query: EvidenceSearchQuery) -> EvidenceSearchResult:
        """Execute a deterministic approved-evidence search/lookup."""
        if not isinstance(query, EvidenceSearchQuery):
            raise TypeError(
                f"query must be an EvidenceSearchQuery; got {type(query).__name__}"
            )
        if query.reference_ids:
            return self._exact_reference_search(query)
        return self._keyword_search(query)

    def __call__(self, query: EvidenceSearchQuery) -> EvidenceSearchResult:
        """Callable protocol support."""
        return self.search(query)

    def _exact_reference_search(self, query: EvidenceSearchQuery) -> EvidenceSearchResult:
        # Deterministic: validate in canonical reference-ID order, then return
        # hits in the same canonical order.
        requested = tuple(sorted(query.reference_ids, key=lambda ref: ref.value))
        hits: list[EvidenceSearchHit] = []
        for reference_id in requested:
            entry = self._chunks_by_ref.get(reference_id.value)
            if entry is None:
                return EvidenceSearchResult(
                    outcome=EvidenceSearchOutcome.SOURCE_NOT_FOUND,
                    query_text=query.query_text,
                )
            source, chunk = entry
            if not source.approved_for_retrieval:
                return EvidenceSearchResult(
                    outcome=EvidenceSearchOutcome.UNAPPROVED_SOURCE,
                    query_text=query.query_text,
                )
            pinned_version = query.requested_source_versions.get(source.source_id.value)
            if pinned_version is not None and pinned_version != source.source_version:
                return EvidenceSearchResult(
                    outcome=EvidenceSearchOutcome.STALE_SOURCE,
                    query_text=query.query_text,
                )
            if compute_content_digest(chunk.content) != chunk.content_sha256:
                return EvidenceSearchResult(
                    outcome=EvidenceSearchOutcome.INTEGRITY_FAILURE,
                    query_text=query.query_text,
                )
            hits.append(self._to_hit(source, chunk, score=0))

        if not hits:
            return EvidenceSearchResult(
                outcome=EvidenceSearchOutcome.SOURCE_NOT_FOUND,
                query_text=query.query_text,
            )
        hits.sort(key=lambda hit: hit.reference_id.value)
        return EvidenceSearchResult(
            outcome=EvidenceSearchOutcome.SUCCESS,
            hits=tuple(hits),
            query_text=query.query_text,
        )

    def _keyword_search(self, query: EvidenceSearchQuery) -> EvidenceSearchResult:
        scope_ids = self._resolve_scope(query)
        if isinstance(scope_ids, EvidenceSearchResult):
            return scope_ids

        query_tokens = normalize_tokens(query.query_text)
        hits: list[EvidenceSearchHit] = []
        unapproved_matched = False
        integrity_failed_matched = False
        for source_id in scope_ids:
            source = self._sources_by_id[source_id]
            for chunk in source.chunks:
                chunk_tokens = normalize_tokens(
                    " ".join((*source.retrieval_tags, *chunk.tags))
                )
                content_tokens = normalize_tokens(chunk.content)
                score = _score_chunk(chunk_tokens, content_tokens, query_tokens)
                if score <= 0:
                    continue
                if not source.approved_for_retrieval:
                    # Approval is enforced before authority: an unapproved
                    # match is a rejection class, never a result/warning.
                    unapproved_matched = True
                    continue
                if compute_content_digest(chunk.content) != chunk.content_sha256:
                    # An approved source whose content is tampered is a
                    # rejection class; it may not be returned as authority.
                    integrity_failed_matched = True
                    continue
                hits.append(self._to_hit(source, chunk, score=score))

        hits.sort(key=lambda hit: (-hit.score, hit.reference_id.value))
        if hits:
            return EvidenceSearchResult(
                outcome=EvidenceSearchOutcome.SUCCESS,
                hits=tuple(hits),
                query_text=query.query_text,
            )
        # No valid approved hit: report the most severe rejection that matched.
        if integrity_failed_matched:
            return EvidenceSearchResult(
                outcome=EvidenceSearchOutcome.INTEGRITY_FAILURE,
                query_text=query.query_text,
            )
        if unapproved_matched:
            return EvidenceSearchResult(
                outcome=EvidenceSearchOutcome.UNAPPROVED_SOURCE,
                query_text=query.query_text,
            )
        return EvidenceSearchResult(
            outcome=EvidenceSearchOutcome.NO_MATCH,
            query_text=query.query_text,
        )

    def _resolve_scope(
        self, query: EvidenceSearchQuery
    ) -> tuple[str, ...] | EvidenceSearchResult:
        if query.source_ids:
            scope: list[str] = []
            for source_id in query.source_ids:
                if source_id.value not in self._sources_by_id:
                    return EvidenceSearchResult(
                        outcome=EvidenceSearchOutcome.SOURCE_NOT_FOUND,
                        query_text=query.query_text,
                    )
                if source_id.value not in scope:
                    scope.append(source_id.value)
        else:
            # Sorted keys keep the implicit all-sources scope deterministic.
            scope = sorted(self._sources_by_id)

        # Fail closed on a pinned version mismatch for a scoped source.
        for source_key in scope:
            pinned = query.requested_source_versions.get(source_key)
            if pinned is not None and pinned != self._sources_by_id[source_key].source_version:
                return EvidenceSearchResult(
                    outcome=EvidenceSearchOutcome.STALE_SOURCE,
                    query_text=query.query_text,
                )
        return tuple(scope)

    def _to_hit(
        self, source: EvidenceSource, chunk: EvidenceChunk, *, score: int
    ) -> EvidenceSearchHit:
        return EvidenceSearchHit(
            reference_id=chunk.reference_id,
            source_id=source.source_id,
            publisher=source.publisher,
            source_title=source.canonical_title,
            canonical_url=source.canonical_url,
            publication_date=source.publication_date,
            source_version=source.source_version,
            attribution_required=source.attribution_required,
            content=chunk.content,
            chunk_tags=chunk.tags,
            score=score,
        )
