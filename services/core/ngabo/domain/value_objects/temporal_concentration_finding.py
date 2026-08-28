"""Deterministic temporal concentration finding contract (Issue #46)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ngabo.domain.enums.concentration_status import (
    ConcentrationReason,
    ConcentrationStatus,
)
from ngabo.domain.value_objects.proof_references import (
    DeterministicFindingReference,
)


def _require_opaque_id(value: object, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
    ):
        raise ValueError(f"Invalid {label} {value!r}; expected a non-blank opaque ID")


@dataclass(frozen=True)
class TemporalConcentrationFinding:
    """Versioned deterministic finding representing temporal isolate accumulation.

    Directly convertible to a DeterministicFindingReference for Proof-Carrying
    Reasoning claims. Represents descriptive isolate count and observed temporal span
    within the governed 7-day retrospective surveillance window.
    """

    finding_id: str
    policy_version: str
    algorithm_version: str
    config_version: str
    organism_code: str
    facility_id: str
    window_start: date
    window_end: date
    facility_organism_count: int
    input_refs: tuple[str, ...]
    observed_min_date: date | None
    observed_max_date: date | None
    observed_span_days: int | None
    status: ConcentrationStatus
    output_value: str
    reason: ConcentrationReason | None = None

    def __post_init__(self) -> None:
        _require_opaque_id(self.finding_id, "finding_id")
        _require_opaque_id(self.policy_version, "policy_version")
        _require_opaque_id(self.algorithm_version, "algorithm_version")
        _require_opaque_id(self.config_version, "config_version")
        _require_opaque_id(self.organism_code, "organism_code")
        _require_opaque_id(self.facility_id, "facility_id")
        _require_opaque_id(self.output_value, "output_value")

        if type(self.window_start) is not date:
            raise TypeError("window_start must be an exact datetime.date")
        if type(self.window_end) is not date:
            raise TypeError("window_end must be an exact datetime.date")
        if self.window_start > self.window_end:
            raise ValueError(
                f"window_start ({self.window_start}) cannot exceed window_end ({self.window_end})"
            )

        if not isinstance(self.input_refs, tuple):
            raise TypeError(f"input_refs must be a tuple; got {type(self.input_refs).__name__}")
        for ref in self.input_refs:
            _require_opaque_id(ref, "input_refs item")
        if self.input_refs != tuple(sorted(self.input_refs)):
            raise ValueError(
                f"input_refs must be sorted lexicographically; got {self.input_refs!r}"
            )

        if (
            not isinstance(self.facility_organism_count, int)
            or isinstance(self.facility_organism_count, bool)
            or self.facility_organism_count < 0
        ):
            raise ValueError(
                f"facility_organism_count must be an integer >= 0; "
                f"got {self.facility_organism_count!r}"
            )

        if self.facility_organism_count != len(self.input_refs):
            raise ValueError(
                f"facility_organism_count ({self.facility_organism_count}) "
                f"must match len(input_refs) ({len(self.input_refs)})"
            )

        if not isinstance(self.status, ConcentrationStatus):
            raise TypeError(f"Invalid status {self.status!r}; expected ConcentrationStatus")

        if self.status != ConcentrationStatus.SUCCESS:
            raise ValueError(
                "TemporalConcentrationFinding only supports ConcentrationStatus.SUCCESS in v0.1 "
                "(retrospective-count-v1 has no denominator)"
            )

        if self.reason is not None:
            raise ValueError("reason must be None on TemporalConcentrationFinding")

        if self.facility_organism_count == 0:
            raise ValueError("SUCCESS status requires facility_organism_count > 0")
        if type(self.observed_min_date) is not date:
            raise TypeError("observed_min_date must be an exact datetime.date on SUCCESS")
        if type(self.observed_max_date) is not date:
            raise TypeError("observed_max_date must be an exact datetime.date on SUCCESS")
        if not (
            self.window_start
            <= self.observed_min_date
            <= self.observed_max_date
            <= self.window_end
        ):
            raise ValueError(
                f"Observed date span [{self.observed_min_date}, {self.observed_max_date}] "
                f"must fall within window [{self.window_start}, {self.window_end}]"
            )
        expected_span = (self.observed_max_date - self.observed_min_date).days + 1
        if self.observed_span_days != expected_span:
            raise ValueError(
                f"observed_span_days ({self.observed_span_days}) does not match "
                f"calculated span ({expected_span})"
            )

    def to_finding_reference(self) -> DeterministicFindingReference:
        """Convert finding directly to a DeterministicFindingReference for reasoning claims."""
        return DeterministicFindingReference(
            finding_id=self.finding_id,
            policy_version=self.policy_version,
            input_refs=self.input_refs,
            output_value=self.output_value,
        )
