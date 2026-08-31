"""Deterministic evidence-intent -> approved source / query mapping (Issue #55).

The model proposes an ``EvidenceIntent``; deterministic code decides which
approved sources satisfy it and builds the retrieval query. No model-supplied
URL, domain, or arbitrary source scope is ever accepted here.
"""

from __future__ import annotations

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


def build_evidence_search_query(proposal: EvidenceIntentProposal) -> EvidenceSearchQuery:
    """Build a framework-free approved-evidence query from a validated proposal.

    The query text is bounded and derived only from the proposal's structured
    terms plus the deterministic intent vocabulary. The source scope comes
    exclusively from the manifest-based allow-list.
    """
    if not isinstance(proposal, EvidenceIntentProposal):
        raise TypeError("proposal must be an EvidenceIntentProposal")
    terms = list(proposal.query_terms)
    if proposal.resistance_concept is not None and proposal.resistance_concept not in terms:
        terms.append(proposal.resistance_concept)
    query_text = " ".join(terms).strip()
    if not query_text:
        # Fall back to the deterministic intent vocabulary so retrieval is never
        # driven purely by a blank model field.
        query_text = proposal.evidence_intent.value.replace("_", " ")
    return EvidenceSearchQuery(
        query_text=query_text,
        source_ids=approved_sources_for(proposal.evidence_intent),
    )
