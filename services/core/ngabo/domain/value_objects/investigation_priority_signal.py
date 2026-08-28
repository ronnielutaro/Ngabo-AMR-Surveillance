"""Investigation-priority signal candidate and component value objects (Issue #47)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from ngabo.domain.enums.signal_status import SignalReason, SignalStatus
from ngabo.domain.value_objects.proof_references import (
    DeterministicFindingReference,
    _require_opaque_id,
)
from ngabo.domain.value_objects.signal_config import SignalConfig


@dataclass(frozen=True)
class SignalComponents:
    """Normalized four-component metrics contributing to an investigation-priority score.

    Every component is deterministically bounded within [0.0000, 1.0000].
    """

    c_phenotype: float
    c_location: float
    c_temporal: float
    c_baseline: float

    def __post_init__(self) -> None:
        for name, val in (
            ("c_phenotype", self.c_phenotype),
            ("c_location", self.c_location),
            ("c_temporal", self.c_temporal),
            ("c_baseline", self.c_baseline),
        ):
            if not isinstance(val, float) or isinstance(val, bool):
                raise TypeError(f"{name} must be a float; got {type(val).__name__}")
            if not math.isfinite(val) or not (0.0 <= val <= 1.0):
                raise ValueError(f"{name} must be finite and within [0.0, 1.0]; got {val}")


@dataclass(frozen=True)
class InvestigationPrioritySignal:
    """Immutable, machine-verifiable investigation-priority signal candidate.

    Primary Invariant: This finding is an INVESTIGATION-PRIORITY POLICY OUTPUT.
    It is NEVER an outbreak declaration, outbreak probability, diagnosis, model
    confidence, clinical decision, or prescribing/treatment guidance.
    """

    signal_id: str
    policy_version: str
    algorithm_version: str
    config_version: str
    organism_code: str
    facility_id: str
    ward: str
    window_start: date
    window_end: date
    ward_organism_count: int
    facility_organism_count: int
    components: SignalComponents
    signal_score: float
    trigger_threshold: float
    status: SignalStatus
    reason: SignalReason
    supporting_finding_refs: tuple[str, ...]
    supporting_isolate_refs: tuple[str, ...]
    output_value: str
    policy_config: SignalConfig

    def __post_init__(self) -> None:
        _require_opaque_id(self.signal_id, "signal ID")
        if not self.signal_id.startswith("sig-"):
            raise ValueError(f"signal_id must start with 'sig-'; got {self.signal_id!r}")

        _require_opaque_id(self.policy_version, "policy_version")
        _require_opaque_id(self.algorithm_version, "algorithm_version")
        _require_opaque_id(self.config_version, "config_version")
        _require_opaque_id(self.organism_code, "organism_code")
        _require_opaque_id(self.facility_id, "facility_id")
        _require_opaque_id(self.ward, "ward")
        _require_opaque_id(self.output_value, "output_value")

        if type(self.window_start) is not date:
            raise TypeError("window_start must be an exact datetime.date")
        if type(self.window_end) is not date:
            raise TypeError("window_end must be an exact datetime.date")
        if self.window_start > self.window_end:
            raise ValueError("window_start must be <= window_end")

        if (
            not isinstance(self.ward_organism_count, int)
            or isinstance(self.ward_organism_count, bool)
            or self.ward_organism_count <= 0
        ):
            raise ValueError("ward_organism_count must be an integer > 0")

        if (
            not isinstance(self.facility_organism_count, int)
            or isinstance(self.facility_organism_count, bool)
            or self.facility_organism_count < self.ward_organism_count
        ):
            raise ValueError("facility_organism_count must be an integer >= ward_organism_count")

        if not isinstance(self.components, SignalComponents):
            cls_name = type(self.components).__name__
            raise TypeError(f"components must be a SignalComponents instance; got {cls_name}")

        if not isinstance(self.policy_config, SignalConfig):
            cls_name = type(self.policy_config).__name__
            raise TypeError(f"policy_config must be a SignalConfig instance; got {cls_name}")

        if not isinstance(self.signal_score, float) or isinstance(self.signal_score, bool):
            raise TypeError("signal_score must be a float")
        if not math.isfinite(self.signal_score) or not (0.0 <= self.signal_score <= 1.0):
            raise ValueError(
                f"signal_score must be finite and within [0.0, 1.0]; got {self.signal_score}"
            )

        if not isinstance(self.trigger_threshold, float) or isinstance(
            self.trigger_threshold, bool
        ):
            raise TypeError("trigger_threshold must be a float")
        if not math.isfinite(self.trigger_threshold) or not (0.0 <= self.trigger_threshold <= 1.0):
            raise ValueError(
                f"trigger_threshold must be finite and within [0.0, 1.0]; "
                f"got {self.trigger_threshold}"
            )

        if self.policy_config.trigger_threshold != self.trigger_threshold:
            raise ValueError(
                f"trigger_threshold ({self.trigger_threshold}) does not match "
                f"policy_config.trigger_threshold ({self.policy_config.trigger_threshold})"
            )
        if self.policy_config.policy_version != self.policy_version:
            raise ValueError("policy_version does not match policy_config.policy_version")
        if self.policy_config.config_version != self.config_version:
            raise ValueError("config_version does not match policy_config.config_version")
        if self.policy_config.algorithm_version != self.algorithm_version:
            raise ValueError("algorithm_version does not match policy_config.algorithm_version")

        if not isinstance(self.status, SignalStatus):
            raise TypeError(f"Invalid status {self.status!r}; expected SignalStatus")

        if not isinstance(self.reason, SignalReason):
            raise TypeError(f"Invalid reason {self.reason!r}; expected SignalReason")

        if not isinstance(self.supporting_finding_refs, tuple):
            raise TypeError("supporting_finding_refs must be a tuple of strings")
        if not self.supporting_finding_refs:
            raise ValueError("supporting_finding_refs must not be empty")
        for ref in self.supporting_finding_refs:
            _require_opaque_id(ref, "supporting finding reference")

        if not isinstance(self.supporting_isolate_refs, tuple):
            raise TypeError("supporting_isolate_refs must be a tuple of strings")
        if len(self.supporting_isolate_refs) != self.ward_organism_count:
            raise ValueError(
                f"supporting_isolate_refs length ({len(self.supporting_isolate_refs)}) "
                f"must equal ward_organism_count ({self.ward_organism_count})"
            )
        for ref in self.supporting_isolate_refs:
            _require_opaque_id(ref, "supporting isolate reference")

        if self.status == SignalStatus.TRIGGERED:
            if self.ward_organism_count < self.policy_config.min_candidate_count:
                raise ValueError(
                    f"TRIGGERED signal status requires ward_organism_count >= "
                    f"{self.policy_config.min_candidate_count}"
                )
            if self.signal_score < self.trigger_threshold:
                raise ValueError(
                    "TRIGGERED signal status requires signal_score >= trigger_threshold"
                )
            if self.reason != SignalReason.HIGH_PRIORITY_CLUSTER:
                raise ValueError(
                    "TRIGGERED signal status requires reason=SignalReason.HIGH_PRIORITY_CLUSTER"
                )

    @property
    def w_phenotype(self) -> float:
        """Governed weight for phenotype similarity component."""
        return self.policy_config.w_phenotype

    @property
    def w_location(self) -> float:
        """Governed weight for location concentration component."""
        return self.policy_config.w_location

    @property
    def w_temporal(self) -> float:
        """Governed weight for temporal accumulation component."""
        return self.policy_config.w_temporal

    @property
    def w_baseline(self) -> float:
        """Governed weight for baseline excess component."""
        return self.policy_config.w_baseline

    @property
    def min_candidate_count(self) -> int:
        """Governed minimum cohort size gate."""
        return self.policy_config.min_candidate_count

    @property
    def configured_synthetic_baseline_count(self) -> float:
        """Governed synthetic baseline reference count."""
        return self.policy_config.configured_synthetic_baseline_count

    @property
    def baseline_saturation_multiplier(self) -> float:
        """Governed baseline saturation multiplier."""
        return self.policy_config.baseline_saturation_multiplier

    @property
    def precision(self) -> int:
        """Governed decimal rounding precision."""
        return self.policy_config.precision

    def recompute_score(self) -> float:
        """Deterministically recompute composite score from persisted components and config."""
        raw = (
            self.policy_config.w_phenotype * self.components.c_phenotype
            + self.policy_config.w_location * self.components.c_location
            + self.policy_config.w_temporal * self.components.c_temporal
            + self.policy_config.w_baseline * self.components.c_baseline
        )
        return min(1.0, max(0.0, round(raw, self.policy_config.precision)))

    def verify_trigger_decision(self) -> bool:
        """Deterministically verify whether this candidate satisfies the trigger policy."""
        return (
            self.signal_score >= self.policy_config.trigger_threshold
            and self.ward_organism_count >= self.policy_config.min_candidate_count
        )

    def to_finding_reference(self) -> DeterministicFindingReference:
        """Convert signal candidate to a DeterministicFindingReference for reasoning claims."""
        return DeterministicFindingReference(
            finding_id=self.signal_id,
            policy_version=self.policy_version,
            input_refs=self.supporting_finding_refs,
            output_value=self.output_value,
        )
