"""Deterministic resistance profile similarity finding contract (Issue #45)."""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.domain.enums.profile_similarity_status import ProfileSimilarityStatus
from ngabo.domain.value_objects.proof_references import DeterministicFindingReference


def _require_opaque_id(value: object, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
    ):
        raise ValueError(f"Invalid {label} {value!r}; expected a non-blank opaque ID")


@dataclass(frozen=True)
class ProfileSimilarityFinding:
    """Versioned deterministic finding representing the phenotype similarity of two isolates.

    Directly convertible to a DeterministicFindingReference for Proof-Carrying
    Reasoning claims without requiring LLMs to recompute scientific values.
    """

    finding_id: str
    policy_version: str
    algorithm_version: str
    config_version: str
    isolate_id_a: str
    isolate_id_b: str
    input_refs: tuple[str, ...]
    organism_code: str | None
    status: ProfileSimilarityStatus
    comparable_antibiotics: tuple[str, ...]
    matching_antibiotics: tuple[str, ...]
    differing_antibiotics: tuple[str, ...]
    untested_or_unknown_antibiotics: tuple[str, ...]
    similarity_score: float | None
    output_value: str

    def __post_init__(self) -> None:
        _require_opaque_id(self.finding_id, "finding_id")
        _require_opaque_id(self.policy_version, "policy_version")
        _require_opaque_id(self.algorithm_version, "algorithm_version")
        _require_opaque_id(self.config_version, "config_version")
        _require_opaque_id(self.isolate_id_a, "isolate_id_a")
        _require_opaque_id(self.isolate_id_b, "isolate_id_b")
        _require_opaque_id(self.output_value, "output_value")

        if not isinstance(self.input_refs, tuple) or len(self.input_refs) != 2:
            raise ValueError(
                f"input_refs must be a 2-tuple of isolate IDs; got {self.input_refs!r}"
            )
        for ref in self.input_refs:
            _require_opaque_id(ref, "input_refs item")

        # Canonical symmetric pair order
        if self.input_refs != tuple(sorted(self.input_refs)):
            raise ValueError(
                f"input_refs must be sorted lexicographically; got {self.input_refs!r}"
            )

        if not isinstance(self.status, ProfileSimilarityStatus):
            raise TypeError(f"Invalid status {self.status!r}; expected ProfileSimilarityStatus")

        if self.status == ProfileSimilarityStatus.SUCCESS:
            if not isinstance(self.similarity_score, float) or isinstance(
                self.similarity_score, bool
            ):
                raise ValueError("similarity_score must be a float when status is SUCCESS")
            if not (0.0 <= self.similarity_score <= 1.0):
                raise ValueError(
                    f"similarity_score must be in range [0.0, 1.0]; got {self.similarity_score}"
                )
            if not self.comparable_antibiotics:
                raise ValueError("comparable_antibiotics cannot be empty when status is SUCCESS")
            if (
                len(self.matching_antibiotics) + len(self.differing_antibiotics)
                != len(self.comparable_antibiotics)
            ):
                raise ValueError(
                    "matching_antibiotics + differing_antibiotics must equal comparable_antibiotics"
                )
        else:
            if self.similarity_score is not None:
                raise ValueError(
                    f"similarity_score must be None when status is {self.status.name}"
                )

    def to_finding_reference(self) -> DeterministicFindingReference:
        """Convert finding directly to a DeterministicFindingReference for reasoning claims."""
        return DeterministicFindingReference(
            finding_id=self.finding_id,
            policy_version=self.policy_version,
            input_refs=self.input_refs,
            output_value=self.output_value,
        )
