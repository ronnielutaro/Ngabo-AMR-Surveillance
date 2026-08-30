"""Framework-free proof-carrying claim used by the ADK/Gemini spike (#49).

The spike issue requires Gemini to produce a schema-constrained typed object
equivalent to the canonical proof-carrier, expressed as opaque reference IDs:

    claim_id
    claim_type
    statement
    supporting_record_ids[]
    supporting_finding_ids[]
    supporting_source_ids[]
    contradicting_claim_ids[]
    uncertainties[]
    requested_action_class
    confidence_label

This is a *spike* DTO: it is intentionally the simple ID-reference shape the
Gemini ``output_schema`` can enforce and that a same-day verifier can check
deterministically. It is NOT the production ``ReasoningClaim`` (#28), which
carries fully-typed ``*Reference`` value objects and richer provenance. The
ADK infrastructure adapter is responsible for mapping a validated
``SpikeProofClaim`` onto the canonical ``ReasoningClaim`` shape at the
boundary, proving the production contract remains reachable.

Construction-time validation covers intrinsic invariants only (non-blank
statement, typed collections, hypothesis-uncertainty rule). Whether a
referenced ID actually exists is deterministic verifier work.
"""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.domain.enums.action_class import ActionClass
from ngabo.domain.enums.claim_type import ClaimType


def _require_opaque_id(value: object, label: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected a non-blank opaque ID")


def _require_id_tuple(values: object, label: str) -> None:
    if not isinstance(values, tuple):
        raise ValueError(f"Invalid {label} {values!r}; expected a tuple of opaque IDs")
    for index, element in enumerate(values):
        _require_opaque_id(element, f"{label} element at position {index}")


@dataclass(frozen=True)
class SpikeProofClaim:
    """Immutable structured proof claim proposed by the Gemini synthesis step."""

    claim_id: str
    claim_type: ClaimType
    statement: str
    supporting_record_ids: tuple[str, ...] = ()
    supporting_finding_ids: tuple[str, ...] = ()
    supporting_source_ids: tuple[str, ...] = ()
    contradicting_claim_ids: tuple[str, ...] = ()
    uncertainties: tuple[str, ...] = ()
    requested_action_class: ActionClass | None = None
    confidence_label: str | None = None

    def __post_init__(self) -> None:
        _require_opaque_id(self.claim_id, "claim ID")
        if not isinstance(self.claim_type, ClaimType):
            raise ValueError(
                f"Invalid claim type {self.claim_type!r}; expected a ClaimType member"
            )
        if not isinstance(self.statement, str) or not self.statement.strip():
            raise ValueError("Invalid claim statement; expected non-blank text")
        _require_id_tuple(self.supporting_record_ids, "supporting record IDs")
        _require_id_tuple(self.supporting_finding_ids, "supporting finding IDs")
        _require_id_tuple(self.supporting_source_ids, "supporting source IDs")
        _require_id_tuple(self.contradicting_claim_ids, "contradicting claim IDs")
        _require_id_tuple(self.uncertainties, "uncertainty entry")
        for index, uncertainty in enumerate(self.uncertainties):
            if not uncertainty.strip():
                raise ValueError(
                    f"Invalid uncertainty entry at position {index}: "
                    f"{uncertainty!r}; expected non-blank text"
                )
        if self.confidence_label is not None and (
            not isinstance(self.confidence_label, str) or not self.confidence_label.strip()
        ):
            raise ValueError(
                f"Invalid confidence label {self.confidence_label!r}; "
                "expected non-blank descriptive text or None"
            )
        if self.requested_action_class is not None and not isinstance(
            self.requested_action_class, ActionClass
        ):
            raise ValueError(
                f"Invalid requested action class {self.requested_action_class!r}; "
                "expected an ActionClass member or None"
            )
        if self.claim_type is ClaimType.HYPOTHESIS and not self.uncertainties:
            raise ValueError(
                "A HYPOTHESIS claim must carry at least one explicit "
                "uncertainty/limitation entry"
            )
