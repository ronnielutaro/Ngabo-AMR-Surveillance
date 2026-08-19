"""Framework-free proof-carrying reasoning claim (M1B.4 / Issue #28).

``ReasoningClaim`` is the immutable structured claim contract that Gemini
synthesis will populate and the deterministic verifier (#29) will later
check. It preserves the semantic fields of the canonical claim schema in
``docs/PROOF_CARRYING_REASONING.md`` §5 with idiomatic Python names:

- ``supporting_record_refs``   -> ``supporting_record_ids`` (typed);
- ``supporting_finding_refs``  -> ``supporting_finding_ids`` (typed);
- ``supporting_evidence_refs`` -> ``supporting_source_ids`` (typed);
- ``supporting_claim_ids``     -> supporting observed/derived claim IDs;
- ``contradicting_claim_ids``  -> ``contradicting_claim_ids``;
- ``uncertainties``            -> ``uncertainties``;
- ``requested_action_class``   -> ``requested_action_class``;
- ``confidence_label``         -> ``confidence_label``.

Construction-time validation covers intrinsic contract invariants only:
non-blank statement, non-blank uncertainty/limitation entries, non-blank
confidence label, type guards, structural collection enforcement (actual
tuples with per-element type checks), and the hypothesis uncertainty rule.
Whether a particular claim type carries *sufficient* proof is deliberately
NOT checked here — that is deterministic verifier work (#29).

``requested_action_class`` is descriptive input only: it is not an
``AutonomyDecision``, not authorization, and not permission to execute.
Deterministic policy (later issues) owns classification and authorization;
no field on this contract grants, waives or passes any policy gate.
"""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.domain.enums.action_class import ActionClass
from ngabo.domain.enums.claim_type import ClaimType
from ngabo.domain.value_objects.claim_id import ClaimId
from ngabo.domain.value_objects.proof_references import (
    ApprovedEvidenceReference,
    CanonicalRecordReference,
    DeterministicFindingReference,
)


def _require_typed_elements(values: object, label: str, expected_type: type[object]) -> None:
    """Fail closed unless ``values`` is an actual tuple of ``expected_type``.

    Structural runtime enforcement: Python does not enforce annotations,
    so these checks are what keeps the constructed claim deeply immutable
    and correctly typed regardless of the calling layer.
    """
    if not isinstance(values, tuple):
        raise ValueError(f"Invalid {label} {values!r}; expected a tuple")
    for index, element in enumerate(values):
        if not isinstance(element, expected_type):
            raise ValueError(
                f"Invalid {label} element at position {index}: {element!r}; "
                f"expected {expected_type.__name__}"
            )


@dataclass(frozen=True)
class ReasoningClaim:
    """Immutable typed proof-carrying claim proposed by the model layer.

    Deeply immutable: all collections are tuples of immutable value
    objects/strings, enforced at construction time — non-tuple collections
    and wrong element types are rejected, so a constructed claim cannot be
    mutated through aliases or in-place operations.
    """

    claim_id: ClaimId
    claim_type: ClaimType
    statement: str
    supporting_record_refs: tuple[CanonicalRecordReference, ...] = ()
    supporting_finding_refs: tuple[DeterministicFindingReference, ...] = ()
    supporting_evidence_refs: tuple[ApprovedEvidenceReference, ...] = ()
    supporting_claim_ids: tuple[ClaimId, ...] = ()
    contradicting_claim_ids: tuple[ClaimId, ...] = ()
    uncertainties: tuple[str, ...] = ()
    requested_action_class: ActionClass | None = None
    confidence_label: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.claim_id, ClaimId):
            raise ValueError(
                f"Invalid claim ID {self.claim_id!r}; expected a ClaimId value object"
            )
        # StrEnum members compare equal to their string values, so the type
        # must be guarded with isinstance rather than a mapping lookup.
        if not isinstance(self.claim_type, ClaimType):
            raise ValueError(
                f"Invalid claim type {self.claim_type!r}; expected a ClaimType member"
            )
        if not isinstance(self.statement, str) or not self.statement.strip():
            raise ValueError("Invalid claim statement; expected non-blank text")
        _require_typed_elements(
            self.supporting_record_refs,
            "supporting record reference",
            CanonicalRecordReference,
        )
        _require_typed_elements(
            self.supporting_finding_refs,
            "supporting finding reference",
            DeterministicFindingReference,
        )
        _require_typed_elements(
            self.supporting_evidence_refs,
            "supporting evidence reference",
            ApprovedEvidenceReference,
        )
        _require_typed_elements(self.supporting_claim_ids, "supporting claim ID", ClaimId)
        _require_typed_elements(self.contradicting_claim_ids, "contradicting claim ID", ClaimId)
        _require_typed_elements(self.uncertainties, "uncertainty entry", str)
        for index, uncertainty in enumerate(self.uncertainties):
            if not uncertainty.strip():
                raise ValueError(
                    f"Invalid uncertainty entry at position {index}: "
                    f"{uncertainty!r}; expected non-blank text"
                )
        if self.confidence_label is not None and (
            not isinstance(self.confidence_label, str)
            or not self.confidence_label.strip()
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
                "uncertainty/limitation entry; hypotheses cannot silently "
                "claim certainty"
            )
