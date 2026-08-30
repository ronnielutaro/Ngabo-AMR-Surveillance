"""Focused tests for Issue #51 approved-evidence manifest + deterministic search."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from ngabo.application.enums.evidence_search_outcome import EvidenceSearchOutcome
from ngabo.application.ports.evidence_search_port import EvidenceSearchPort
from ngabo.application.value_objects.evidence_search import (
    EvidenceSearchQuery,
)
from ngabo.domain.services.evidence_provenance import (
    compute_content_digest,
    compute_corpus_digest,
    validate_evidence_corpus,
    validate_evidence_source,
)
from ngabo.domain.value_objects.evidence_reference import (
    EvidenceChunk,
    EvidenceReferenceId,
    EvidenceSourceId,
)
from ngabo.domain.value_objects.evidence_source import EvidenceSource
from ngabo.infrastructure.evidence.evidence_manifest_loader import (
    EvidenceCorpusLoadError,
    load_evidence_corpus,
)
from ngabo.infrastructure.evidence.local_evidence_search import (
    LocalEvidenceSearch,
    normalize_tokens,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
GUIDANCE_DIR = REPO_ROOT / "data" / "guidance"
MANIFEST_PATH = GUIDANCE_DIR / "manifest.json"
SCHEMA_PATH = REPO_ROOT / "data" / "schemas" / "evidence_manifest.schema.json"

# Representative v0.1 hero evidence query (carbapenem-resistant Enterobacterales
# cluster). The synthetic hero needs approved guidance on IPC/containment,
# contact precautions, and CRE recognition/surveillance.
HERO_QUERY = (
    "carbapenem-resistant enterobacterales infection prevention and control "
    "contact precautions surveillance in healthcare facilities"
)
EXPECTED_HERO_REFS = [
    "CDC-CRE-001::facility-response-01",
    "WHO-AMR-001::ipc-principle-01",
    "CDC-CRE-001::cre-definition-01",
    "WHO-AMR-001::surveillance-principle-01",
]


def _chunk(
    reference_id: str,
    source_id: str,
    content: str,
    tags: tuple[str, ...],
) -> EvidenceChunk:
    return EvidenceChunk(
        reference_id=EvidenceReferenceId(reference_id),
        source_id=EvidenceSourceId(source_id),
        content=content,
        content_sha256=compute_content_digest(content),
        tags=tags,
    )


def _source(
    source_id: str,
    *,
    chunks: tuple[EvidenceChunk, ...],
    approved: bool = True,
    version: str = "1",
    retrieval_tags: tuple[str, ...] = (),
    publisher: str = "Publisher",
    title: str = "Title",
    url: str = "https://example.test/source",
    usage: str = "Public domain indexing summary",
    local_type: str = "indexing_summary",
    local_present: bool = True,
    notes: str = "Provenance note",
) -> EvidenceSource:
    return EvidenceSource(
        source_id=EvidenceSourceId(source_id),
        publisher=publisher,
        canonical_title=title,
        canonical_url=url,
        publication_date="2026-01-01",
        source_version=version,
        local_content_present=local_present,
        local_content_type=local_type,
        usage_basis_or_license=usage,
        attribution_required=True,
        approved_for_retrieval=approved,
        notes=notes,
        retrieval_tags=retrieval_tags,
        chunks=chunks,
    )


def _loaded_corpus() -> tuple[EvidenceSource, ...]:
    return load_evidence_corpus(GUIDANCE_DIR)


@pytest.fixture
def living_corpus() -> tuple[EvidenceSource, ...]:
    return _loaded_corpus()


def test_manifest_schema_and_corpus_loads(living_corpus: tuple[EvidenceSource, ...]) -> None:
    assert len(living_corpus) == 3
    source_ids = {s.source_id.value for s in living_corpus}
    assert source_ids == {"WHO-AMR-001", "CDC-CRE-001", "UNKNOWN-PUBLISHER-001"}
    approved = [s for s in living_corpus if s.approved_for_retrieval]
    assert len(approved) == 2
    for source in approved:
        assert source.chunks, f"{source.source_id} must have retrievable chunks"


def test_manifest_validates_against_schema() -> None:
    raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(raw),
        key=lambda err: list(err.path),
    )
    assert errors == [], f"manifest schema errors: {[e.message for e in errors]}"


def test_manifest_corpus_hash_reproduces(living_corpus: tuple[EvidenceSource, ...]) -> None:
    raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert compute_corpus_digest(living_corpus) == raw["corpus_sha256"]


def test_provenance_completeness_rejects_placeholder_on_approved() -> None:
    source = _source(
        "WHO-AMR-001",
        chunks=(_chunk("WHO-AMR-001::x-01", "WHO-AMR-001", "content", ("cre",)),),
        publisher="TBD",
    )
    with pytest.raises(ValueError, match="publisher"):
        validate_evidence_source(source)


def test_provenance_rejects_approved_without_local_content() -> None:
    source = _source(
        "WHO-AMR-001",
        chunks=(),
        local_present=False,
    )
    with pytest.raises(ValueError, match="local content"):
        validate_evidence_source(source)


def test_provenance_rejects_approved_without_chunks() -> None:
    source = _source("WHO-AMR-001", chunks=())
    with pytest.raises(ValueError, match="no chunks"):
        validate_evidence_source(source)


def test_unapproved_placeholder_allowed_in_manifest() -> None:
    source = _source(
        "UNKNOWN-001",
        chunks=(),
        approved=False,
        publisher="TBD",
        usage="TBD",
    )
    # Unapproved sources may hold a provenance placeholder for history but can
    # never be retrieved; validation must allow it.
    validate_evidence_source(source)
    with pytest.raises(ValueError, match="Duplicate evidence source ID"):
        validate_evidence_corpus((source, source))


def test_hero_retrieval_returns_exactly_expected_approved_refs(
    living_corpus: tuple[EvidenceSource, ...],
) -> None:
    search = LocalEvidenceSearch(living_corpus)
    result = search.search(EvidenceSearchQuery(query_text=HERO_QUERY))
    assert result.outcome == EvidenceSearchOutcome.SUCCESS
    assert [hit.reference_id.value for hit in result.hits] == EXPECTED_HERO_REFS
    assert all(
        hit.source_id.value.startswith(("WHO-AMR-001", "CDC-CRE-001"))
        for hit in result.hits
    )


def test_no_match_is_stable(living_corpus: tuple[EvidenceSource, ...]) -> None:
    search = LocalEvidenceSearch(living_corpus)
    result = search.search(
        EvidenceSearchQuery(query_text="quantum teleportation orbital mechanics")
    )
    assert result.outcome == EvidenceSearchOutcome.NO_MATCH
    assert result.hits == ()


def test_unapproved_matching_source_does_not_leak(
    living_corpus: tuple[EvidenceSource, ...],
) -> None:
    # "unverified license authorization" appears only in the unapproved
    # source's content/title. Because approval is enforced before authority,
    # the matching-but-unapproved source is excluded and retrieval reports the
    # UNAPPROVED_SOURCE rejection class (not NO_MATCH) with zero hits.
    search = LocalEvidenceSearch(living_corpus)
    result = search.search(
        EvidenceSearchQuery(query_text="unverified license authorization")
    )
    assert result.outcome == EvidenceSearchOutcome.UNAPPROVED_SOURCE
    assert result.hits == ()


def test_unapproved_direct_lookup_fails_closed(
    living_corpus: tuple[EvidenceSource, ...],
) -> None:
    search = LocalEvidenceSearch(living_corpus)
    result = search.search(
        EvidenceSearchQuery(
            reference_ids=(EvidenceReferenceId("UNKNOWN-PUBLISHER-001::generic-claim-01"),)
        )
    )
    assert result.outcome == EvidenceSearchOutcome.UNAPPROVED_SOURCE
    assert result.hits == ()


def test_missing_reference_fails_closed(
    living_corpus: tuple[EvidenceSource, ...],
) -> None:
    search = LocalEvidenceSearch(living_corpus)
    result = search.search(
        EvidenceSearchQuery(reference_ids=(EvidenceReferenceId("NOPE-999::phantom"),))
    )
    assert result.outcome == EvidenceSearchOutcome.SOURCE_NOT_FOUND


def test_missing_source_scope_fails_closed(
    living_corpus: tuple[EvidenceSource, ...],
) -> None:
    search = LocalEvidenceSearch(living_corpus)
    result = search.search(
        EvidenceSearchQuery(
            source_ids=(EvidenceSourceId("NOPE-999"),),
            query_text="carbapenem",
        )
    )
    assert result.outcome == EvidenceSearchOutcome.SOURCE_NOT_FOUND


def test_stale_requested_version_fails_closed(
    living_corpus: tuple[EvidenceSource, ...],
) -> None:
    search = LocalEvidenceSearch(living_corpus)
    result = search.search(
        EvidenceSearchQuery(
            reference_ids=(EvidenceReferenceId("WHO-AMR-001::ipc-principle-01"),),
            requested_source_versions={"WHO-AMR-001": "9"},
        )
    )
    assert result.outcome == EvidenceSearchOutcome.STALE_SOURCE


def test_tampered_content_returns_integrity_failure() -> None:
    source = _source(
        "WHO-AMR-001",
        chunks=(
            EvidenceChunk(
                reference_id=EvidenceReferenceId("WHO-AMR-001::tampered-01"),
                source_id=EvidenceSourceId("WHO-AMR-001"),
                content="tampered bytes",
                content_sha256=compute_content_digest("original bytes"),
                tags=("cre",),
            ),
        ),
    )
    search = LocalEvidenceSearch((source,))
    result = search.search(
        EvidenceSearchQuery(
            reference_ids=(EvidenceReferenceId("WHO-AMR-001::tampered-01"),)
        )
    )
    assert result.outcome == EvidenceSearchOutcome.INTEGRITY_FAILURE
    assert result.hits == ()


def test_tampered_content_not_retrieved_in_keyword_mode() -> None:
    good = _source(
        "WHO-AMR-001",
        chunks=(
            EvidenceChunk(
                reference_id=EvidenceReferenceId("WHO-AMR-001::tampered-01"),
                source_id=EvidenceSourceId("WHO-AMR-001"),
                content="tampered",
                content_sha256=compute_content_digest("original"),
                tags=("carbapenem-resistant enterobacterales",),
            ),
        ),
    )
    search = LocalEvidenceSearch((good,))
    result = search.search(EvidenceSearchQuery(query_text="carbapenem-resistant enterobacterales"))
    # No valid approved hit; the matching-but-tampered approved evidence must
    # surface INTEGRITY_FAILURE, not a misleading NO_MATCH.
    assert result.outcome == EvidenceSearchOutcome.INTEGRITY_FAILURE
    assert result.hits == ()


def test_cdc_canonical_provenance_matches_2015_source(
    living_corpus: tuple[EvidenceSource, ...],
) -> None:
    cdc = next(s for s in living_corpus if s.source_id.value == "CDC-CRE-001")
    # The November 2015 Facility Guidance record (CDC Stacks cdc:79104), not the
    # earlier 2012 CRE Toolkit (cdc:13205).
    assert cdc.canonical_url == "https://stacks.cdc.gov/view/cdc/79104"
    assert "November 2015" in cdc.canonical_title
    assert cdc.publication_date == "2015-11-01"


def test_cdc_attribution_required(living_corpus: tuple[EvidenceSource, ...]) -> None:
    cdc = next(s for s in living_corpus if s.source_id.value == "CDC-CRE-001")
    assert cdc.attribution_required is True
    assert "attribution" in cdc.notes.lower()
    assert "does not imply endorsement" in cdc.notes.lower()


def test_keyword_precedence_integrity_over_unapproved() -> None:
    # A tampered approved chunk AND an unapproved matching chunk are both
    # rejected. With no valid approved hit, INTEGRITY_FAILURE must take
    # precedence over UNAPPROVED_SOURCE per the documented deterministic rule.
    tampered = _source(
        "WHO-AMR-001",
        chunks=(
            EvidenceChunk(
                reference_id=EvidenceReferenceId("WHO-AMR-001::tampered-01"),
                source_id=EvidenceSourceId("WHO-AMR-001"),
                content="tampered",
                content_sha256=compute_content_digest("original"),
                tags=("carbapenem-resistant enterobacterales",),
            ),
        ),
    )
    unapproved = _source(
        "UNKNOWN-PUBLISHER-001",
        chunks=(
            _chunk(
                "UNKNOWN-PUBLISHER-001::x-01",
                "UNKNOWN-PUBLISHER-001",
                "unverified license authorization claim",
                ("carbapenem-resistant enterobacterales",),
            ),
        ),
        approved=False,
        notes="Unverified placeholder source.",
    )
    search = LocalEvidenceSearch((tampered, unapproved))
    result = search.search(EvidenceSearchQuery(query_text="carbapenem-resistant enterobacterales"))
    assert result.outcome == EvidenceSearchOutcome.INTEGRITY_FAILURE
    assert result.hits == ()


def test_orphan_local_content_cannot_become_authority(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    # A committed source with a real chunk.
    chunk_content = "carbapenem-resistant enterobacterales infection control"
    chunk_path = corpus_dir / "WHO-AMR-001--ipc-principle-01.txt"
    chunk_path.write_text(chunk_content, encoding="utf-8")
    # An orphan content file that is NOT referenced by any manifest source.
    (corpus_dir / "orphan-unmanifested.txt").write_text(
        "carbapenem-resistant enterobacterales contact precautions whisper",
        encoding="utf-8",
    )
    manifest = {
        "manifest_version": "1.0",
        "corpus_id": "tmp-corpus",
        "corpus_sha256": "0" * 64,  # corrected just below
        "sources": [
            {
                "source_id": "WHO-AMR-001",
                "publisher": "Publisher",
                "canonical_title": "Title",
                "canonical_url": "https://example.test/source",
                "publication_date": "2026-01-01",
                "source_version": "1",
                "local_content_present": True,
                "local_content_type": "indexing_summary",
                "usage_basis_or_license": "Public domain indexing summary",
                "attribution_required": True,
                "approved_for_retrieval": True,
                "notes": "Provenance note",
                "retrieval_tags": ["carbapenem-resistant enterobacterales"],
                "chunks": [
                    {
                        "reference_id": "WHO-AMR-001::ipc-principle-01",
                        "content_path": "WHO-AMR-001--ipc-principle-01.txt",
                        "content_sha256": compute_content_digest(chunk_content),
                        "tags": ["carbapenem-resistant enterobacterales"],
                    }
                ],
            }
        ],
    }
    # Compute the correct corpus digest (content + reference id only) so the
    # tmp corpus loads; the orphan file is deliberately not part of this digest.
    chunk = _chunk(
        "WHO-AMR-001::ipc-principle-01",
        "WHO-AMR-001",
        chunk_content,
        ("carbapenem-resistant enterobacterales",),
    )
    source = _source(
        "WHO-AMR-001",
        chunks=(chunk,),
        retrieval_tags=("carbapenem-resistant enterobacterales",),
    )
    manifest["corpus_sha256"] = compute_corpus_digest((source,))
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    sources = load_evidence_corpus(tmp_path)
    search = LocalEvidenceSearch(sources)
    result = search.search(EvidenceSearchQuery(query_text="contact precautions whisper"))
    # Orphan content is not in the manifest, so it is not authority.
    assert result.outcome == EvidenceSearchOutcome.NO_MATCH


def test_missing_local_content_fails_load(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    manifest = {
        "manifest_version": "1.0",
        "corpus_id": "tmp-corpus",
        "corpus_sha256": "0" * 64,
        "sources": [
            {
                "source_id": "WHO-AMR-001",
                "publisher": "Publisher",
                "canonical_title": "Title",
                "canonical_url": "https://example.test/source",
                "publication_date": "2026-01-01",
                "source_version": "1",
                "local_content_present": True,
                "local_content_type": "indexing_summary",
                "usage_basis_or_license": "Public domain indexing summary",
                "attribution_required": True,
                "approved_for_retrieval": True,
                "notes": "Provenance note",
                "retrieval_tags": ["cre"],
                "chunks": [
                    {
                        "reference_id": "WHO-AMR-001::missing-01",
                        "content_path": "WHO-AMR-001--missing-01.txt",
                        "content_sha256": "0" * 64,
                        "tags": ["cre"],
                    }
                ],
            }
        ],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(EvidenceCorpusLoadError):
        load_evidence_corpus(tmp_path)


def test_manifest_corpus_digest_fail_closed(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    content = "carbapenem-resistant enterobacterales"
    (corpus_dir / "WHO-AMR-001--ipc-principle-01.txt").write_text(content, encoding="utf-8")
    manifest = {
        "manifest_version": "1.0",
        "corpus_id": "tmp-corpus",
        "corpus_sha256": "f" * 64,  # wrong digest -> must fail closed
        "sources": [
            {
                "source_id": "WHO-AMR-001",
                "publisher": "Publisher",
                "canonical_title": "Title",
                "canonical_url": "https://example.test/source",
                "publication_date": "2026-01-01",
                "source_version": "1",
                "local_content_present": True,
                "local_content_type": "indexing_summary",
                "usage_basis_or_license": "Public domain indexing summary",
                "attribution_required": True,
                "approved_for_retrieval": True,
                "notes": "Provenance note",
                "retrieval_tags": ["cre"],
                "chunks": [
                    {
                        "reference_id": "WHO-AMR-001::ipc-principle-01",
                        "content_path": "WHO-AMR-001--ipc-principle-01.txt",
                        "content_sha256": compute_content_digest(content),
                        "tags": ["cre"],
                    }
                ],
            }
        ],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(EvidenceCorpusLoadError, match="digest"):
        load_evidence_corpus(tmp_path)


def test_order_independence_of_manifest(living_corpus: tuple[EvidenceSource, ...]) -> None:
    forwards = LocalEvidenceSearch(living_corpus)
    reversed_sources = tuple(reversed(living_corpus))
    backwards = LocalEvidenceSearch(reversed_sources)
    query = EvidenceSearchQuery(query_text=HERO_QUERY)
    forward_result = forwards.search(query)
    backward_result = backwards.search(query)
    assert [h.reference_id.value for h in forward_result.hits] == [
        h.reference_id.value for h in backward_result.hits
    ]


def test_deterministic_normalization_and_ranking(
    living_corpus: tuple[EvidenceSource, ...],
) -> None:
    search = LocalEvidenceSearch(living_corpus)
    query = EvidenceSearchQuery(query_text="CRE Infection Prevention")
    assert "cre" in normalize_tokens("CRE Infection Prevention")
    first = search.search(query)
    second = search.search(query)
    assert first.outcome == second.outcome == EvidenceSearchOutcome.SUCCESS
    assert [h.reference_id.value for h in first.hits] == [
        h.reference_id.value for h in second.hits
    ]


def test_local_search_satisfies_evidence_search_port(
    living_corpus: tuple[EvidenceSource, ...],
) -> None:
    search = LocalEvidenceSearch(living_corpus)
    assert isinstance(search, EvidenceSearchPort)


def test_corpus_digest_changes_when_content_mutates() -> None:
    chunk_a = _chunk("WHO-AMR-001::a", "WHO-AMR-001", "carbapenem resistant", ("cre",))
    chunk_b = _chunk("WHO-AMR-001::b", "WHO-AMR-001", "carbapenem resistant", ("cre",))
    source = _source("WHO-AMR-001", chunks=(chunk_a, chunk_b))
    digest_one = compute_corpus_digest((source,))
    mutated = _chunk("WHO-AMR-001::b", "WHO-AMR-001", "tampered content", ("cre",))
    source_mutated = _source("WHO-AMR-001", chunks=(chunk_a, mutated))
    assert compute_corpus_digest((source_mutated,)) != digest_one
