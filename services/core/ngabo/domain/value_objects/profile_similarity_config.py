"""Versioned configuration for resistance profile similarity evaluation (Issue #45)."""

from __future__ import annotations

from dataclasses import dataclass

PROFILE_SIM_POLICY_VERSION: str = "ngabo-profile-sim-v1"
PROFILE_SIM_ALGORITHM_VERSION: str = "exact-ratio-v1"
PROFILE_SIM_CONFIG_VERSION: str = "min3-strict-org-v1"
PROFILE_SIM_MIN_COMPARABLE: int = 3
PROFILE_SIM_STRICT_ORGANISM: bool = True
PROFILE_SIM_PRECISION: int = 4


@dataclass(frozen=True)
class ProfileSimilarityConfig:
    """Immutable, versioned configuration for resistance profile similarity calculations.

    In v0.1.0, the version identifiers and calculation parameters are inseparable
    under ADR 0010. This configuration represents a closed, fail-closed policy.
    """

    algorithm_version: str = PROFILE_SIM_ALGORITHM_VERSION
    config_version: str = PROFILE_SIM_CONFIG_VERSION
    policy_version: str = PROFILE_SIM_POLICY_VERSION
    min_comparable_antibiotics: int = PROFILE_SIM_MIN_COMPARABLE
    strict_organism_match: bool = PROFILE_SIM_STRICT_ORGANISM
    similarity_precision: int = PROFILE_SIM_PRECISION

    def __post_init__(self) -> None:
        if not isinstance(self.policy_version, str):
            raise TypeError("policy_version must be a string")
        if self.policy_version != PROFILE_SIM_POLICY_VERSION:
            raise ValueError(
                f"Unsupported policy_version {self.policy_version!r}; "
                f"governed v0.1 policy enforces {PROFILE_SIM_POLICY_VERSION!r}"
            )

        if not isinstance(self.algorithm_version, str):
            raise TypeError("algorithm_version must be a string")
        if self.algorithm_version != PROFILE_SIM_ALGORITHM_VERSION:
            raise ValueError(
                f"Unsupported algorithm_version {self.algorithm_version!r}; "
                f"governed v0.1 algorithm enforces {PROFILE_SIM_ALGORITHM_VERSION!r}"
            )

        if not isinstance(self.config_version, str):
            raise TypeError("config_version must be a string")
        if self.config_version != PROFILE_SIM_CONFIG_VERSION:
            raise ValueError(
                f"Unsupported config_version {self.config_version!r}; "
                f"governed v0.1 config enforces {PROFILE_SIM_CONFIG_VERSION!r}"
            )

        if isinstance(self.min_comparable_antibiotics, bool) or not isinstance(
            self.min_comparable_antibiotics, int
        ):
            raise TypeError("min_comparable_antibiotics must be an integer")
        if self.min_comparable_antibiotics != PROFILE_SIM_MIN_COMPARABLE:
            raise ValueError(
                f"Unsupported min_comparable_antibiotics {self.min_comparable_antibiotics!r}; "
                f"governed v0.1 policy enforces {PROFILE_SIM_MIN_COMPARABLE}"
            )

        if not isinstance(self.strict_organism_match, bool):
            raise TypeError("strict_organism_match must be a boolean")
        if self.strict_organism_match is not True:
            raise ValueError(
                "strict_organism_match must be True; v0.1 policy strictly enforces "
                "organism compatibility"
            )

        if isinstance(self.similarity_precision, bool) or not isinstance(
            self.similarity_precision, int
        ):
            raise TypeError("similarity_precision must be an integer")
        if self.similarity_precision != PROFILE_SIM_PRECISION:
            raise ValueError(
                f"Unsupported similarity_precision {self.similarity_precision!r}; "
                f"governed v0.1 policy enforces {PROFILE_SIM_PRECISION}"
            )
