"""Provisional, framework-free evidence-intent proposal (Issue #55).

``EvidenceIntentProposal`` is the ONLY contract Gemini produces. It is
provisional and carries no decision, completion, authorization, or action
semantics. It names a deterministic allow-listed evidence intent plus bounded
structured query facets; deterministic code decides authority and retrieval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ngabo.application.enums.evidence_intent import EvidenceIntent

_TERM_PATTERN = re.compile(r"^[\w\s\-:]{1,64}$")
MAX_QUERY_TERMS = 6


def _require_opaque(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected a non-blank opaque value")
    return value


@dataclass(frozen=True)
class EvidenceIntentProposal:
    """A model-proposed, deterministically-validated evidence intent."""

    proposal_id: str
    evidence_intent: EvidenceIntent
    query_terms: tuple[str, ...]
    organism_code: str | None = None
    resistance_concept: str | None = None
    optional_topic: str | None = None
    uncertainty_code: str | None = None

    def __post_init__(self) -> None:
        _require_opaque(self.proposal_id, "proposal id")
        if not self.proposal_id.startswith("prop-"):
            raise ValueError(f"proposal_id must start with 'prop-'; got {self.proposal_id!r}")
        if not isinstance(self.evidence_intent, EvidenceIntent):
            raise ValueError("evidence_intent must be an EvidenceIntent")
        if not isinstance(self.query_terms, tuple) or not self.query_terms:
            raise ValueError("query_terms must be a non-empty tuple")
        if len(self.query_terms) > MAX_QUERY_TERMS:
            raise ValueError(f"query_terms must have at most {MAX_QUERY_TERMS} terms")
        for term in self.query_terms:
            if not isinstance(term, str) or not _TERM_PATTERN.fullmatch(term):
                raise ValueError(f"Invalid query term {term!r}; expected bounded non-blank text")
        for label, value in (
            ("organism_code", self.organism_code),
            ("resistance_concept", self.resistance_concept),
            ("optional_topic", self.optional_topic),
            ("uncertainty_code", self.uncertainty_code),
        ):
            if value is not None:
                _require_opaque(value, label)
                if len(value) > 64:
                    raise ValueError(f"{label} must be <=64 characters")

    def to_safe_primitive(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "evidence_intent": self.evidence_intent.value,
            "query_terms": list(self.query_terms),
            "organism_code": self.organism_code,
            "resistance_concept": self.resistance_concept,
            "optional_topic": self.optional_topic,
            "uncertainty_code": self.uncertainty_code,
        }
