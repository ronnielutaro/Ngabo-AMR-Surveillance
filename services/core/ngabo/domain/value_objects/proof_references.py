"""Typed proof references for proof-carrying claims (M1B.4 / Issue #28).

Three authority sources from ``docs/PROOF_CARRYING_REASONING.md`` §3–4 and
ADR 0009:

- :class:`CanonicalRecordReference` — canonical Ngabo source records;
- :class:`DeterministicFindingReference` — deterministic Ngabo calculations;
- :class:`ApprovedEvidenceReference` — approved retrieved evidence/sources.

IDs are opaque Ngabo-owned references, never free-form authority text.
These value objects preserve reference semantics only; whether a referenced
ID actually exists is checked by the later deterministic verifier (#29).
"""

from __future__ import annotations

from dataclasses import dataclass


def _require_opaque_id(value: object, label: str) -> None:
    """Reject IDs that are not non-blank strings without edge whitespace.

    Structural validation only — no existence check happens here.
    """
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
    ):
        raise ValueError(f"Invalid {label} {value!r}; expected a non-blank opaque ID")


@dataclass(frozen=True)
class CanonicalRecordReference:
    """Proof reference pointing a claim at one Ngabo-owned canonical record.

    ``field_path`` and ``expected_value`` preserve the exact field/value
    provenance used by the claim where practical; the later verifier may
    compare them against the canonical record.
    """

    record_id: str
    field_path: str
    expected_value: str

    def __post_init__(self) -> None:
        _require_opaque_id(self.record_id, "canonical record ID")
        _require_opaque_id(self.field_path, "canonical record field path")
        _require_opaque_id(self.expected_value, "expected canonical record value")


@dataclass(frozen=True)
class DeterministicFindingReference:
    """Proof reference pointing a claim at a deterministic Ngabo result.

    ``input_refs`` are the opaque IDs of the finding's referenced inputs;
    ``output_value`` preserves the output value/reference used by the claim.
    """

    finding_id: str
    policy_version: str
    input_refs: tuple[str, ...]
    output_value: str

    def __post_init__(self) -> None:
        _require_opaque_id(self.finding_id, "deterministic finding ID")
        _require_opaque_id(self.policy_version, "calculation/policy version")
        _require_opaque_id(self.output_value, "deterministic finding output value")
        for ref in self.input_refs:
            _require_opaque_id(ref, "deterministic finding input reference")


@dataclass(frozen=True)
class ApprovedEvidenceReference:
    """Proof reference pointing a claim at approved retrieved evidence.

    ``chunk_id`` optionally narrows the reference to the retrieved
    chunk/excerpt used by the claim; ``provenance`` preserves the source's
    provenance/version metadata; ``support`` records the support
    relationship between the evidence and the claim.
    """

    source_id: str
    chunk_id: str | None
    provenance: str
    support: str

    def __post_init__(self) -> None:
        _require_opaque_id(self.source_id, "approved source ID")
        if self.chunk_id is not None:
            _require_opaque_id(self.chunk_id, "retrieved chunk/excerpt ID")
        _require_opaque_id(self.provenance, "source provenance/version")
        _require_opaque_id(self.support, "evidence support relationship")
