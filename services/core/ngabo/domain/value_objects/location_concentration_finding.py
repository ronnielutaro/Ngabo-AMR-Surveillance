"""Deterministic location concentration finding contract (Issue #46)."""

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
class LocationConcentrationFinding:
    """Versioned deterministic finding representing spatial (ward) isolate concentration.

    Directly convertible to a DeterministicFindingReference for Proof-Carrying
    Reasoning claims. Represents the descriptive proportion of facility isolates
    observed in a specific ward over the governed 7-day retrospective surveillance window.
    """

    finding_id: str
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
    location_concentration_ratio: float | None
    ward_input_refs: tuple[str, ...]
    facility_window_input_refs: tuple[str, ...]
    input_refs: tuple[str, ...]
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
        _require_opaque_id(self.ward, "ward")
        _require_opaque_id(self.output_value, "output_value")

        if type(self.window_start) is not date:
            raise TypeError("window_start must be an exact datetime.date")
        if type(self.window_end) is not date:
            raise TypeError("window_end must be an exact datetime.date")
        if self.window_start > self.window_end:
            raise ValueError(
                f"window_start ({self.window_start}) cannot exceed window_end ({self.window_end})"
            )

        for attr_name in ("ward_input_refs", "facility_window_input_refs", "input_refs"):
            refs = getattr(self, attr_name)
            if not isinstance(refs, tuple):
                raise TypeError(f"{attr_name} must be a tuple; got {type(refs).__name__}")
            for ref in refs:
                _require_opaque_id(ref, f"{attr_name} item")
            if refs != tuple(sorted(refs)):
                raise ValueError(f"{attr_name} must be sorted lexicographically; got {refs!r}")

        # Authoritative proof input authority: input_refs must include every record materially
        # used in the finding (the full facility window denominator union).
        if self.input_refs != self.facility_window_input_refs:
            raise ValueError(
                "Authoritative input_refs must equal facility_window_input_refs "
                "(all records materially affecting the denominator must be referenceable)"
            )

        if not set(self.ward_input_refs).issubset(set(self.facility_window_input_refs)):
            raise ValueError("ward_input_refs must be a subset of facility_window_input_refs")

        if (
            not isinstance(self.ward_organism_count, int)
            or isinstance(self.ward_organism_count, bool)
            or self.ward_organism_count < 0
        ):
            raise ValueError(
                f"ward_organism_count must be an integer >= 0; got {self.ward_organism_count!r}"
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

        if self.ward_organism_count != len(self.ward_input_refs):
            raise ValueError(
                f"ward_organism_count ({self.ward_organism_count}) "
                f"must match len(ward_input_refs) ({len(self.ward_input_refs)})"
            )

        if self.facility_organism_count != len(self.facility_window_input_refs):
            raise ValueError(
                f"facility_organism_count ({self.facility_organism_count}) "
                f"must match len(facility_window_input_refs) "
                f"({len(self.facility_window_input_refs)})"
            )

        if not isinstance(self.status, ConcentrationStatus):
            raise TypeError(f"Invalid status {self.status!r}; expected ConcentrationStatus")

        if self.reason is not None and not isinstance(self.reason, ConcentrationReason):
            raise TypeError(f"Invalid reason {self.reason!r}; expected ConcentrationReason")

        if self.status == ConcentrationStatus.SUCCESS:
            if self.facility_organism_count == 0:
                raise ValueError("SUCCESS status requires facility_organism_count > 0")
            if self.ward_organism_count > self.facility_organism_count:
                raise ValueError(
                    f"ward_organism_count ({self.ward_organism_count}) "
                    f"cannot exceed facility_organism_count ({self.facility_organism_count})"
                )
            if not isinstance(self.location_concentration_ratio, float) or isinstance(
                self.location_concentration_ratio, bool
            ):
                raise TypeError("location_concentration_ratio must be a float on SUCCESS")
            if not (0.0 <= self.location_concentration_ratio <= 1.0):
                raise ValueError(
                    f"location_concentration_ratio must be in range [0.0, 1.0]; "
                    f"got {self.location_concentration_ratio}"
                )
            expected_ratio = round(self.ward_organism_count / self.facility_organism_count, 4)
            if self.location_concentration_ratio != expected_ratio:
                raise ValueError(
                    f"location_concentration_ratio ({self.location_concentration_ratio}) "
                    f"does not match expected calculated ratio ({expected_ratio})"
                )
            if self.reason is not None:
                raise ValueError("reason must be None on SUCCESS status")
        else:
            if self.facility_organism_count != 0:
                raise ValueError("INSUFFICIENT_DATA status requires facility_organism_count == 0")
            if self.location_concentration_ratio is not None:
                raise ValueError("location_concentration_ratio must be None on INSUFFICIENT_DATA")
            if self.reason != ConcentrationReason.EMPTY_DENOMINATOR:
                raise ValueError(
                    "INSUFFICIENT_DATA status requires reason=ConcentrationReason.EMPTY_DENOMINATOR"
                )

    def to_finding_reference(self) -> DeterministicFindingReference:
        """Convert finding directly to a DeterministicFindingReference for reasoning claims."""
        return DeterministicFindingReference(
            finding_id=self.finding_id,
            policy_version=self.policy_version,
            input_refs=self.input_refs,
            output_value=self.output_value,
        )
