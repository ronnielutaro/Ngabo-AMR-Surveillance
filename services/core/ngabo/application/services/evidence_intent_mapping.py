"""Deterministic evidence-intent -> approved source / query mapping (Issue #55).

The model proposes an ``EvidenceIntent``; deterministic code decides which
approved sources satisfy it and builds the retrieval query. No model-supplied
URL, domain, or arbitrary source scope is ever accepted here.
"""

from __future__ import annotations

import unicodedata

from ngabo.application.enums.evidence_intent import EvidenceIntent
from ngabo.application.value_objects.evidence_intent_proposal import (
    EvidenceIntentProposal,
)
from ngabo.application.value_objects.evidence_search import EvidenceSearchQuery
from ngabo.domain.value_objects.evidence_reference import EvidenceSourceId

# Deterministic allow-list of approved sources per evidence intent. These are
# committed, approved manifest source IDs; empty means the intent has no
# approved source (retrieval yields NO_EVIDENCE rather than inventing one).
EVIDENCE_INTENT_TO_APPROVED_SOURCES: dict[EvidenceIntent, tuple[EvidenceSourceId, ...]] = {
    EvidenceIntent.IP_C: (
        EvidenceSourceId("WHO-AMR-001"),
        EvidenceSourceId("CDC-CRE-001"),
    ),
    EvidenceIntent.SURVEILLANCE_INTERPRETATION: (
        EvidenceSourceId("WHO-AMR-001"),
    ),
    EvidenceIntent.RESISTANCE_MECHANISM: (
        EvidenceSourceId("CDC-CRE-001"),
    ),
    EvidenceIntent.ORGANISM_AMR: (
        EvidenceSourceId("CDC-CRE-001"),
    ),
    EvidenceIntent.ANTIMICROBIAL_STEWARDSHIP: (),
}


def approved_sources_for(intent: EvidenceIntent) -> tuple[EvidenceSourceId, ...]:
    """Return the deterministic approved source scope for ``intent``."""
    if not isinstance(intent, EvidenceIntent):
        raise TypeError("intent must be an EvidenceIntent")
    return EVIDENCE_INTENT_TO_APPROVED_SOURCES[intent]


def _facet_key(text: str) -> str:
    """Deterministic normalization key for query facets (NFKC + lower + space-collapse)."""
    return " ".join(unicodedata.normalize("NFKC", text).lower().split())


def complete_query_facets(proposal: EvidenceIntentProposal) -> tuple[str, ...]:
    """Return the COMPLETE set of model-controlled retrieval facets.

    This is the single source of truth for the query-term budget: it combines
    ``query_terms`` and the optional ``resistance_concept``, deterministically
    de-duplicating facets that are identical under normalization. The budget
    check and the rendered ``EvidenceSearchQuery`` both consume this exact list,
    so no model-controlled facet can be appended after validation.
    """
    if not isinstance(proposal, EvidenceIntentProposal):
        raise TypeError("proposal must be an EvidenceIntentProposal")
    facets: list[str] = []
    seen: set[str] = set()
    for term in list(proposal.query_terms) + (
        [proposal.resistance_concept] if proposal.resistance_concept is not None else []
    ):
        key = _facet_key(term)
        if key not in seen:
            seen.add(key)
            facets.append(term)
    return tuple(facets)


def build_evidence_search_query(proposal: EvidenceIntentProposal) -> EvidenceSearchQuery:
    """Build a framework-free approved-evidence query from a validated proposal.

    The query text is bounded and derived only from the proposal's structured
    terms plus the deterministic intent vocabulary. The source scope comes
    exclusively from the manifest-based allow-list.
    """
    if not isinstance(proposal, EvidenceIntentProposal):
        raise TypeError("proposal must be an EvidenceIntentProposal")
    terms = list(complete_query_facets(proposal))
    query_text = " ".join(terms).strip()
    if not query_text:
        # Fall back to the deterministic intent vocabulary so retrieval is never
        # driven purely by a blank model field.
        query_text = proposal.evidence_intent.value.replace("_", " ")
    return EvidenceSearchQuery(
        query_text=query_text,
        source_ids=approved_sources_for(proposal.evidence_intent),
    )
