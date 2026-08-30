"""Gemini structured-output schema for the spike proof carrier (#49).

``ClaimSynthesis`` is the Pydantic ``output_schema`` bound to the ADK LLM
agent. It mirrors the issue's required proof-carrying shape using opaque
reference IDs. ADK/Gemini treats this model as the response schema; the
adapter maps a validated instance onto the framework-free
``SpikeProofClaim`` (domain) at the boundary.

The schema is intentionally not the production ``ReasoningClaim``: it carries
the plain ID-reference shape a same-day Gemini structured output can enforce.
Enum member validity (``claim_type`` / ``requested_action_class``) is decided
by deterministic code, not by the schema — the model proposes, code decides.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ngabo.domain.enums.action_class import ActionClass
from ngabo.domain.enums.claim_type import ClaimType
from ngabo.domain.value_objects.spike_proof_claim import SpikeProofClaim


class ClaimSynthesis(BaseModel):
    """Schema-constrained proof carrier proposed by the Gemini agent."""

    claim_id: str = Field(min_length=1, pattern=r"claim-\d+")
    claim_type: Literal[
        "OBSERVED_FACT",
        "DERIVED_FINDING",
        "EVIDENCE_STATEMENT",
        "HYPOTHESIS",
        "ACTION_JUSTIFICATION",
    ] = "DERIVED_FINDING"
    statement: str = Field(min_length=1)
    supporting_record_ids: list[str] = Field(default_factory=list)
    supporting_finding_ids: list[str] = Field(default_factory=list)
    supporting_source_ids: list[str] = Field(default_factory=list)
    contradicting_claim_ids: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    requested_action_class: Literal["A0", "A1", "A2", "A3"] = "A0"
    confidence_label: str = Field(default="low", min_length=1)


def to_spike_proof_claim(synthesis: ClaimSynthesis) -> SpikeProofClaim:
    """Map validated schema output onto the framework-free domain DTO.

    Deterministic validation of the enum-valued fields happens here, not in
    the schema or the prompt: the model proposes raw strings and this code
    decides whether they are legitimate ``ClaimType``/``ActionClass`` members.
    An invalid enum (or a structurally invalid claim) raises, which the caller
    converts to a ``MALFORMED_PROOF`` outcome rather than trusting the model.
    """
    claim_type = ClaimType(synthesis.claim_type)
    action_class = (
        ActionClass(synthesis.requested_action_class)
        if synthesis.requested_action_class
        else None
    )
    return SpikeProofClaim(
        claim_id=synthesis.claim_id,
        claim_type=claim_type,
        statement=synthesis.statement,
        supporting_record_ids=tuple(synthesis.supporting_record_ids),
        supporting_finding_ids=tuple(synthesis.supporting_finding_ids),
        supporting_source_ids=tuple(synthesis.supporting_source_ids),
        contradicting_claim_ids=tuple(synthesis.contradicting_claim_ids),
        uncertainties=tuple(synthesis.uncertainties),
        requested_action_class=action_class,
        confidence_label=synthesis.confidence_label,
    )
