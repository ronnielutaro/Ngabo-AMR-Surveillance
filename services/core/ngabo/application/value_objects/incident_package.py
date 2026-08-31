"""Framework-free versioned proof-carrying incident package contract (#52).

``IncidentPackageCandidate`` is the typed boundary between the deterministic
investigation capabilities + approved evidence retrieval + Gemini synthesis
proposal (upstream) and deterministic proof verification (downstream). It
carries a package identity/version, the incident/source identity it was
produced against, descriptive policy/model metadata, immutable proof-carrying
claims, explicit uncertainty and limitations, an approved-evidence binding,
and a draft coordination message.

Authority boundary (the central #52 invariant):

- the package is a PROPOSAL/CANDIDATE and is structurally incapable of
  declaring itself verified, approved, or action-authorized;
- there is no ``verified``/``approved``/``authorized``/``ready_to_send`` field
  and no authorization token on this contract;
- ``requested_action_class`` on a claim remains descriptive input to later
  deterministic policy and grants no authority;
- the strict primitive parser rejects any authority-bearing unknown field.

All collections are immutable after construction; claims are canonicalized by
``claim_id`` so semantically unordered claim sets never change the package.
This module defines constants and value objects only — no verification,
repair, action policy, persistence, or model/cloud behavior.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ngabo.domain.value_objects.evidence_reference import (
    EvidenceReferenceId,
)
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.reasoning_claim import ReasoningClaim
from ngabo.domain.value_objects.source_watermark import SourceWatermark

# The single supported package contract/schema version for the v0.1 lane.
PACKAGE_CONTRACT_VERSION = "1.0"

_PACKAGE_ID_PATTERN = re.compile(r"PKG-\d+")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _require_nonblank(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected non-blank text")
    return value


@dataclass(frozen=True)
class IncidentPackageId:
    """Opaque, stable identifier of one Ngabo incident package candidate."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not _PACKAGE_ID_PATTERN.fullmatch(self.value):
            raise ValueError(
                f"Invalid incident package ID {self.value!r}; expected 'PKG-<digits>'"
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PackageContractVersion:
    """Explicit package contract/schema version (distinct from incident version).

    Only the single currently supported ``PACKAGE_CONTRACT_VERSION`` is
    constructible. The typed internal construction boundary rejects anything
    else; the parser keeps returning
    ``IncidentPackageErrorCode.UNSUPPORTED_PACKAGE_VERSION`` for external
    primitive input. This guarantees every constructible package round-trips
    through its own canonical serializer/parser.
    """

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError(
                f"Invalid package contract version {self.value!r}; expected non-blank text"
            )
        if self.value != PACKAGE_CONTRACT_VERSION:
            raise ValueError(
                f"Unsupported package contract version {self.value!r}; "
                f"the only supported value is {PACKAGE_CONTRACT_VERSION!r}"
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PackageLimitation:
    """Explicit, immutable limitation on the package (separate from uncertainty)."""

    value: str

    def __post_init__(self) -> None:
        _require_nonblank(self.value, "package limitation")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class IncidentPackageEvidenceBinding:
    """Binds a package to the approved-evidence corpus/manifest it was proposed against."""

    corpus_id: str
    manifest_version: str
    corpus_digest: str
    evidence_references: tuple[EvidenceReferenceId, ...]

    def __post_init__(self) -> None:
        _require_nonblank(self.corpus_id, "evidence corpus id")
        _require_nonblank(self.manifest_version, "evidence manifest version")
        if (
            not isinstance(self.corpus_digest, str)
            or not _SHA256_PATTERN.fullmatch(self.corpus_digest)
        ):
            raise ValueError(
                f"Invalid evidence corpus digest {self.corpus_digest!r}; "
                "expected a 64-character lowercase hexadecimal digest"
            )
        if not isinstance(self.evidence_references, tuple):
            raise ValueError(
                f"Invalid evidence references {self.evidence_references!r}; expected a tuple"
            )
        for index, reference in enumerate(self.evidence_references):
            if not isinstance(reference, EvidenceReferenceId):
                raise ValueError(
                    f"Invalid evidence reference at position {index}: {reference!r}; "
                    "expected an EvidenceReferenceId"
                )
        # Canonical deterministic ordering: the evidence reference identity is
        # the stable key, so semantically unordered sets produce the same binding.
        object.__setattr__(
            self,
            "evidence_references",
            tuple(sorted(self.evidence_references, key=lambda ref: ref.value)),
        )


@dataclass(frozen=True)
class IncidentPackageMetadata:
    """Descriptive, non-authorizing provenance about how the package was produced."""

    policy_config_version: str
    model_identifier: str
    model_version: str
    evidence_binding: IncidentPackageEvidenceBinding
    generation_run_id: str | None = None

    def __post_init__(self) -> None:
        _require_nonblank(self.policy_config_version, "policy config version")
        _require_nonblank(self.model_identifier, "model identifier")
        _require_nonblank(self.model_version, "model version")
        if self.generation_run_id is not None:
            _require_nonblank(self.generation_run_id, "generation run id")
        if not isinstance(self.evidence_binding, IncidentPackageEvidenceBinding):
            raise ValueError("evidence_binding must be an IncidentPackageEvidenceBinding")


@dataclass(frozen=True)
class DraftCoordinationMessage:
    """Draft-only coordination message PROPOSAL. It carries no send/authorization state."""

    subject: str
    body: str
    intended_purpose: str
    candidate_recipient_role: str

    def __post_init__(self) -> None:
        _require_nonblank(self.subject, "draft subject")
        _require_nonblank(self.body, "draft body")
        _require_nonblank(self.intended_purpose, "draft intended purpose")
        _require_nonblank(self.candidate_recipient_role, "draft recipient role")


@dataclass(frozen=True)
class IncidentPackageCandidate:
    """Immutable, versioned proof-carrying incident package PROPOSAL.

    Structural invariants:

    - all collections are tuples (deeply immutable), enforced at construction;
    - claims are canonicalized by ``claim_id`` so equivalent orderings are equal;
    - claim IDs are unique at the package level (duplicates are rejected);
    - this contract carries no ``verified``/``approved``/``authorized`` state.

    It does NOT semantically verify whether a claim/reference is true — that is
    the later deterministic ``VerifyReasoningClaims`` boundary (#29).
    """

    package_id: IncidentPackageId
    contract_version: PackageContractVersion
    incident_id: IncidentId
    incident_version: IncidentVersion
    source_watermark: SourceWatermark
    metadata: IncidentPackageMetadata
    claims: tuple[ReasoningClaim, ...]
    uncertainties: tuple[str, ...] = ()
    limitations: tuple[PackageLimitation, ...] = ()
    draft_coordination_message: DraftCoordinationMessage | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.package_id, IncidentPackageId):
            raise ValueError("package_id must be an IncidentPackageId")
        if not isinstance(self.contract_version, PackageContractVersion):
            raise ValueError("contract_version must be a PackageContractVersion")
        if not isinstance(self.incident_id, IncidentId):
            raise ValueError("incident_id must be an IncidentId")
        if not isinstance(self.incident_version, IncidentVersion):
            raise ValueError("incident_version must be an IncidentVersion")
        if not isinstance(self.source_watermark, SourceWatermark):
            raise ValueError("source_watermark must be a SourceWatermark")
        if not isinstance(self.metadata, IncidentPackageMetadata):
            raise ValueError("metadata must be an IncidentPackageMetadata")

        if not isinstance(self.claims, tuple):
            raise ValueError(f"Invalid claims {self.claims!r}; expected a tuple")
        for index, claim in enumerate(self.claims):
            if not isinstance(claim, ReasoningClaim):
                raise ValueError(
                    f"Invalid claim at position {index}: {claim!r}; expected a ReasoningClaim"
                )
        # Canonical deterministic claim ordering: claim identity is the stable key.
        object.__setattr__(
            self,
            "claims",
            tuple(sorted(self.claims, key=lambda claim: claim.claim_id.value)),
        )
        seen_claim_ids: set[str] = set()
        for claim in self.claims:
            if claim.claim_id.value in seen_claim_ids:
                raise ValueError(
                    f"Duplicate claim ID {claim.claim_id!r}; claim IDs must be unique "
                    "within an incident package"
                )
            seen_claim_ids.add(claim.claim_id.value)

        if not isinstance(self.uncertainties, tuple):
            raise ValueError(
                f"Invalid package uncertainties {self.uncertainties!r}; expected a tuple"
            )
        for index, uncertainty in enumerate(self.uncertainties):
            if not isinstance(uncertainty, str) or not uncertainty.strip():
                raise ValueError(
                    f"Invalid package uncertainty at position {index}: "
                    f"{uncertainty!r}; expected non-blank text"
                )
        # Canonical deterministic ordering for a semantically unordered set.
        object.__setattr__(
            self, "uncertainties", tuple(sorted(self.uncertainties))
        )

        if not isinstance(self.limitations, tuple):
            raise ValueError(
                f"Invalid package limitations {self.limitations!r}; expected a tuple"
            )
        for index, limitation in enumerate(self.limitations):
            if not isinstance(limitation, PackageLimitation):
                raise ValueError(
                    f"Invalid package limitation at position {index}: {limitation!r}; "
                    "expected a PackageLimitation"
                )
        # Canonical deterministic ordering by limitation value.
        object.__setattr__(
            self,
            "limitations",
            tuple(sorted(self.limitations, key=lambda limitation: limitation.value)),
        )

        if self.draft_coordination_message is not None and not isinstance(
            self.draft_coordination_message, DraftCoordinationMessage
        ):
            raise ValueError(
                "draft_coordination_message must be a DraftCoordinationMessage or None"
            )
