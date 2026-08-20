"""Inward application port for deterministic claim verification (M1B.5 / #29).

``VerifyReasoningClaims`` is the framework-free behaviour contract that the
deterministic verifier (a later issue) implements and application workflows
depend on. It accepts proof-carrying claims in their immutable form and
returns the ``ClaimVerificationReport``. No behaviour lives here — this is
a seam, not an implementation.

Deliberate simplification versus the conceptual signature in
``docs/PROOF_CARRYING_REASONING.md`` §6: that document sketches
``verify(incident_id, incident_version, package_version, canonical_context,
deterministic_findings, approved_evidence_manifest, policy_version,
claims)``. Those context/package types do not exist yet and Issue #29
forbids inventing placeholder models, so this Sprint 1 port exposes the
smallest contract surface the issue actually requires: claims in, report
out. The fuller signature is the verifier issue's concern once those
contracts exist.

Placement: Issue #29 and ``docs/CLEAN_ARCHITECTURE.md`` specify the port as
an inward application contract under ``application/ports/`` (mirroring the
``EvidenceSearchPort`` convention). PROOF_CARRYING_REASONING §11 mentions
``application/use_cases/verify_reasoning_claims.py``; a Protocol is a port
contract, not a use case, so the ports package is the faithful placement
for the contract this issue defines. The use-case/implementation wiring
belongs to the verifier issue.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ngabo.domain.value_objects.claim_verification_report import ClaimVerificationReport
from ngabo.domain.value_objects.reasoning_claim import ReasoningClaim


@runtime_checkable
class VerifyReasoningClaims(Protocol):
    """Inward contract the deterministic claim verifier satisfies.

    Implementations (outer layers) receive the claim batch and return a
    ``ClaimVerificationReport``; application workflows depend only on this
    Protocol. Claims must be supplied as a tuple of ``ReasoningClaim`` —
    the immutable form established in #28.
    """

    def __call__(self, claims: tuple[ReasoningClaim, ...]) -> ClaimVerificationReport: ...
