"""Deterministic finding evidence value object (Issue #48).

Captures machine-verifiable finding metadata establishing ID, type, versions, and input refs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ngabo.domain.value_objects.proof_references import _require_opaque_id


@dataclass(frozen=True)
class DeterministicFindingEvidence:
    """Machine-verifiable metadata for an upstream deterministic finding."""

    finding_id: str
    finding_type: str
    policy_version: str
    algorithm_version: str
    config_version: str
    input_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_opaque_id(self.finding_id, "finding_id")
        _require_opaque_id(self.finding_type, "finding_type")
        _require_opaque_id(self.policy_version, "policy_version")
        _require_opaque_id(self.algorithm_version, "algorithm_version")
        _require_opaque_id(self.config_version, "config_version")
        if not isinstance(self.input_refs, tuple):
            raise TypeError("input_refs must be a tuple")
        for ref in self.input_refs:
            _require_opaque_id(ref, "input_refs item")

    def to_dict(self) -> dict[str, Any]:
        """Convert to a JSON-serializable dictionary."""
        return {
            "finding_id": self.finding_id,
            "finding_type": self.finding_type,
            "policy_version": self.policy_version,
            "algorithm_version": self.algorithm_version,
            "config_version": self.config_version,
            "input_refs": list(self.input_refs),
        }
