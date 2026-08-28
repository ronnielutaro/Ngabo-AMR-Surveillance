"""Versioned configuration for resistance profile similarity evaluation (Issue #45)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileSimilarityConfig:
    """Immutable, versioned configuration for resistance profile similarity calculations."""

    algorithm_version: str = "exact-ratio-v1"
    config_version: str = "min3-strict-org-v1"
    policy_version: str = "ngabo-profile-sim-v1"
    min_comparable_antibiotics: int = 3
    strict_organism_match: bool = True
    similarity_precision: int = 4

    def __post_init__(self) -> None:
        if (
            not isinstance(self.algorithm_version, str)
            or not self.algorithm_version.strip()
            or self.algorithm_version != self.algorithm_version.strip()
        ):
            raise ValueError("algorithm_version must be a non-blank, trimmed string")
        if (
            not isinstance(self.config_version, str)
            or not self.config_version.strip()
            or self.config_version != self.config_version.strip()
        ):
            raise ValueError("config_version must be a non-blank, trimmed string")
        if (
            not isinstance(self.policy_version, str)
            or not self.policy_version.strip()
            or self.policy_version != self.policy_version.strip()
        ):
            raise ValueError("policy_version must be a non-blank, trimmed string")
        if (
            not isinstance(self.min_comparable_antibiotics, int)
            or isinstance(self.min_comparable_antibiotics, bool)
            or self.min_comparable_antibiotics < 1
        ):
            raise ValueError("min_comparable_antibiotics must be an integer >= 1")
        if not isinstance(self.strict_organism_match, bool):
            raise TypeError("strict_organism_match must be a boolean")
        if not self.strict_organism_match:
            raise ValueError(
                "strict_organism_match=False is not permitted; v0.1 policy strictly enforces "
                "organism compatibility"
            )
        if (
            not isinstance(self.similarity_precision, int)
            or isinstance(self.similarity_precision, bool)
            or self.similarity_precision < 1
        ):
            raise ValueError("similarity_precision must be an integer >= 1")
