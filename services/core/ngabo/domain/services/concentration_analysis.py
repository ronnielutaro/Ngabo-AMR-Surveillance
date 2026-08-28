"""Deterministic scientific logic for temporal and location concentration (Issue #46)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from datetime import date

from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.enums.concentration_status import (
    ConcentrationReason,
    ConcentrationStatus,
)
from ngabo.domain.value_objects.concentration_config import ConcentrationConfig
from ngabo.domain.value_objects.location_concentration_finding import (
    LocationConcentrationFinding,
)
from ngabo.domain.value_objects.temporal_concentration_finding import (
    TemporalConcentrationFinding,
)


def _deduplicate_and_validate_isolates(
    isolates: Sequence[CanonicalIsolate],
) -> list[CanonicalIsolate]:
    """Deduplicate canonical isolates with fail-closed conflict semantics.

    - Value-identical duplicate CanonicalIsolates collapse idempotently.
    - Conflicting CanonicalIsolates sharing the same isolate_id raise ValueError.
    - Preserves deterministic lexicographic ordering by isolate_id.
    """
    seen: dict[str, CanonicalIsolate] = {}
    for iso in isolates:
        if not isinstance(iso, CanonicalIsolate):
            raise TypeError(
                f"Expected CanonicalIsolate instance; got {type(iso).__name__}"
            )
        if iso.isolate_id in seen:
            existing = seen[iso.isolate_id]
            if existing != iso:
                raise ValueError(
                    f"Conflicting CanonicalIsolate records for {iso.isolate_id!r} in collection; "
                    "conflicting duplicate inputs must fail closed"
                )
            continue
        seen[iso.isolate_id] = iso
    return sorted(seen.values(), key=lambda x: x.isolate_id)


def _compute_temporal_finding_id(
    *,
    policy_version: str,
    algorithm_version: str,
    config_version: str,
    window_start: date,
    window_end: date,
    organism_code: str,
    facility_id: str,
    input_refs: tuple[str, ...],
    facility_organism_count: int,
    observed_min_date: date | None,
    observed_max_date: date | None,
    observed_span_days: int | None,
    status: ConcentrationStatus,
    output_value: str,
) -> str:
    """Compute a deterministic, opaque SHA-256 finding ID for temporal concentration."""
    payload = {
        "algorithm_version": algorithm_version,
        "config_version": config_version,
        "facility_id": facility_id,
        "facility_organism_count": facility_organism_count,
        "input_refs": list(input_refs),
        "observed_max_date": observed_max_date.isoformat() if observed_max_date else None,
        "observed_min_date": observed_min_date.isoformat() if observed_min_date else None,
        "observed_span_days": observed_span_days,
        "organism_code": organism_code,
        "output_value": output_value,
        "policy_version": policy_version,
        "status": status.value,
        "window_end": window_end.isoformat(),
        "window_start": window_start.isoformat(),
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(serialized).hexdigest()
    return f"tconc-{digest[:16]}"


def _compute_location_finding_id(
    *,
    policy_version: str,
    algorithm_version: str,
    config_version: str,
    window_start: date,
    window_end: date,
    organism_code: str,
    facility_id: str,
    ward: str,
    ward_input_refs: tuple[str, ...],
    facility_window_input_refs: tuple[str, ...],
    input_refs: tuple[str, ...],
    ward_organism_count: int,
    facility_organism_count: int,
    location_concentration_ratio: float | None,
    precision: int,
    status: ConcentrationStatus,
    output_value: str,
) -> str:
    """Compute a deterministic, opaque SHA-256 finding ID for location concentration."""
    payload = {
        "algorithm_version": algorithm_version,
        "authoritative_input_refs": list(input_refs),
        "config_version": config_version,
        "facility_id": facility_id,
        "facility_organism_count": facility_organism_count,
        "facility_window_input_refs": list(facility_window_input_refs),
        "location_concentration_ratio": (
            f"{location_concentration_ratio:.{precision}f}"
            if location_concentration_ratio is not None
            else None
        ),
        "organism_code": organism_code,
        "output_value": output_value,
        "policy_version": policy_version,
        "precision": precision,
        "status": status.value,
        "ward": ward,
        "ward_input_refs": list(ward_input_refs),
        "ward_organism_count": ward_organism_count,
        "window_end": window_end.isoformat(),
        "window_start": window_start.isoformat(),
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(serialized).hexdigest()
    return f"lconc-{digest[:16]}"


def compute_temporal_concentration_findings(
    isolates: Sequence[CanonicalIsolate],
    window_end: date,
    config: ConcentrationConfig | None = None,
) -> tuple[TemporalConcentrationFinding, ...]:
    """Calculate deterministic temporal concentration findings across canonical isolates.

    Follows the maintainer-approved v0.1 policy (ADR 0011):
    1. Consumes an explicit date-only window_end without system clock access.
    2. Filters deduplicated isolates into the inclusive 7-day retrospective window.
    3. Groups isolates by (organism_code, facility_id).
    4. Computes descriptive count, observed span days, and lexicographical input_refs.
    5. Issue #46 produces factual measurements; it does NOT enforce an investigation threshold.
    """
    cfg = config if config is not None else ConcentrationConfig()
    if type(window_end) is not date:
        raise TypeError(
            f"window_end must be an exact datetime.date; got {type(window_end).__name__}"
        )
    window_start = cfg.calculate_window_start(window_end)

    unique_isolates = _deduplicate_and_validate_isolates(isolates)
    in_window = [
        iso for iso in unique_isolates if window_start <= iso.collection_date <= window_end
    ]

    # Group by (organism_code, facility_id)
    groups: dict[tuple[str, str], list[CanonicalIsolate]] = {}
    for iso in in_window:
        key = (iso.organism_code, iso.facility_id)
        groups.setdefault(key, []).append(iso)

    findings: list[TemporalConcentrationFinding] = []
    for (organism_code, facility_id), group_isolates in sorted(groups.items()):
        group_isolates.sort(key=lambda x: x.isolate_id)
        count = len(group_isolates)
        input_refs = tuple(iso.isolate_id for iso in group_isolates)
        min_date = min(iso.collection_date for iso in group_isolates)
        max_date = max(iso.collection_date for iso in group_isolates)
        span_days = (max_date - min_date).days + 1
        output_value = (
            f"temporal_count={count};span_days={span_days};window_days={cfg.window_days}"
        )
        status = ConcentrationStatus.SUCCESS

        finding_id = _compute_temporal_finding_id(
            policy_version=cfg.policy_version,
            algorithm_version=cfg.temporal_algorithm_version,
            config_version=cfg.config_version,
            window_start=window_start,
            window_end=window_end,
            organism_code=organism_code,
            facility_id=facility_id,
            input_refs=input_refs,
            facility_organism_count=count,
            observed_min_date=min_date,
            observed_max_date=max_date,
            observed_span_days=span_days,
            status=status,
            output_value=output_value,
        )

        findings.append(
            TemporalConcentrationFinding(
                finding_id=finding_id,
                policy_version=cfg.policy_version,
                algorithm_version=cfg.temporal_algorithm_version,
                config_version=cfg.config_version,
                organism_code=organism_code,
                facility_id=facility_id,
                window_start=window_start,
                window_end=window_end,
                facility_organism_count=count,
                input_refs=input_refs,
                observed_min_date=min_date,
                observed_max_date=max_date,
                observed_span_days=span_days,
                status=status,
                output_value=output_value,
            )
        )

    return tuple(findings)


def compute_location_concentration_findings(
    isolates: Sequence[CanonicalIsolate],
    window_end: date,
    config: ConcentrationConfig | None = None,
) -> tuple[LocationConcentrationFinding, ...]:
    """Calculate deterministic location concentration (ward-share) findings across isolates.

    Follows the maintainer-approved v0.1 policy (ADR 0011):
    1. Consumes an explicit date-only window_end without system clock access.
    2. Primary grouping by (organism_code, facility_id) defines the denominator cohort.
    3. Secondary grouping by ward defines the numerator count.
    4. Computes location_concentration_ratio = ward_count / facility_count, rounded to 4 decimals.
    5. Proof authority: authoritative input_refs includes ALL facility window records because
       every denominator record materially affects the computed ratio.
    """
    cfg = config if config is not None else ConcentrationConfig()
    if type(window_end) is not date:
        raise TypeError(
            f"window_end must be an exact datetime.date; got {type(window_end).__name__}"
        )
    window_start = cfg.calculate_window_start(window_end)

    unique_isolates = _deduplicate_and_validate_isolates(isolates)
    in_window = [
        iso for iso in unique_isolates if window_start <= iso.collection_date <= window_end
    ]

    # Primary grouping: (organism_code, facility_id)
    fac_groups: dict[tuple[str, str], list[CanonicalIsolate]] = {}
    for iso in in_window:
        fac_key = (iso.organism_code, iso.facility_id)
        fac_groups.setdefault(fac_key, []).append(iso)

    findings: list[LocationConcentrationFinding] = []
    for (organism_code, facility_id), fac_isolates in sorted(fac_groups.items()):
        fac_isolates.sort(key=lambda x: x.isolate_id)
        facility_count = len(fac_isolates)
        facility_refs = tuple(iso.isolate_id for iso in fac_isolates)

        # Secondary grouping by ward
        ward_groups: dict[str, list[CanonicalIsolate]] = {}
        for iso in fac_isolates:
            ward_groups.setdefault(iso.ward, []).append(iso)

        for ward, ward_isolates in sorted(ward_groups.items()):
            ward_isolates.sort(key=lambda x: x.isolate_id)
            ward_count = len(ward_isolates)
            ward_refs = tuple(iso.isolate_id for iso in ward_isolates)
            ratio = round(ward_count / facility_count, cfg.precision)
            formatted_ratio = f"{ratio:.{cfg.precision}f}"
            output_value = (
                f"ward_share={formatted_ratio};ward_count={ward_count};"
                f"facility_count={facility_count};ward={ward}"
            )
            status = ConcentrationStatus.SUCCESS

            finding_id = _compute_location_finding_id(
                policy_version=cfg.policy_version,
                algorithm_version=cfg.location_algorithm_version,
                config_version=cfg.config_version,
                window_start=window_start,
                window_end=window_end,
                organism_code=organism_code,
                facility_id=facility_id,
                ward=ward,
                ward_input_refs=ward_refs,
                facility_window_input_refs=facility_refs,
                input_refs=facility_refs,
                ward_organism_count=ward_count,
                facility_organism_count=facility_count,
                location_concentration_ratio=ratio,
                precision=cfg.precision,
                status=status,
                output_value=output_value,
            )

            findings.append(
                LocationConcentrationFinding(
                    finding_id=finding_id,
                    policy_version=cfg.policy_version,
                    algorithm_version=cfg.location_algorithm_version,
                    config_version=cfg.config_version,
                    organism_code=organism_code,
                    facility_id=facility_id,
                    ward=ward,
                    window_start=window_start,
                    window_end=window_end,
                    ward_organism_count=ward_count,
                    facility_organism_count=facility_count,
                    location_concentration_ratio=ratio,
                    ward_input_refs=ward_refs,
                    facility_window_input_refs=facility_refs,
                    input_refs=facility_refs,
                    status=status,
                    output_value=output_value,
                )
            )

    return tuple(findings)


def evaluate_temporal_cohort(
    organism_code: str,
    facility_id: str,
    isolates: Sequence[CanonicalIsolate],
    window_end: date,
    config: ConcentrationConfig | None = None,
) -> TemporalConcentrationFinding:
    """Evaluate temporal concentration for a specific (organism, facility) cohort.

    If zero isolates exist in the window, returns an INSUFFICIENT_DATA finding with
    reason EMPTY_DENOMINATOR.
    """
    cfg = config if config is not None else ConcentrationConfig()
    if type(window_end) is not date:
        raise TypeError(
            f"window_end must be an exact datetime.date; got {type(window_end).__name__}"
        )
    window_start = cfg.calculate_window_start(window_end)

    unique_isolates = _deduplicate_and_validate_isolates(isolates)
    cohort = [
        iso
        for iso in unique_isolates
        if iso.organism_code == organism_code
        and iso.facility_id == facility_id
        and window_start <= iso.collection_date <= window_end
    ]
    cohort.sort(key=lambda x: x.isolate_id)

    count = len(cohort)
    if count == 0:
        status = ConcentrationStatus.INSUFFICIENT_DATA
        reason = ConcentrationReason.EMPTY_DENOMINATOR
        output_value = "status=INSUFFICIENT_DATA;reason=EMPTY_DENOMINATOR;temporal_count=0"
        finding_id = _compute_temporal_finding_id(
            policy_version=cfg.policy_version,
            algorithm_version=cfg.temporal_algorithm_version,
            config_version=cfg.config_version,
            window_start=window_start,
            window_end=window_end,
            organism_code=organism_code,
            facility_id=facility_id,
            input_refs=(),
            facility_organism_count=0,
            observed_min_date=None,
            observed_max_date=None,
            observed_span_days=None,
            status=status,
            output_value=output_value,
        )
        return TemporalConcentrationFinding(
            finding_id=finding_id,
            policy_version=cfg.policy_version,
            algorithm_version=cfg.temporal_algorithm_version,
            config_version=cfg.config_version,
            organism_code=organism_code,
            facility_id=facility_id,
            window_start=window_start,
            window_end=window_end,
            facility_organism_count=0,
            input_refs=(),
            observed_min_date=None,
            observed_max_date=None,
            observed_span_days=None,
            status=status,
            reason=reason,
            output_value=output_value,
        )

    input_refs = tuple(iso.isolate_id for iso in cohort)
    min_date = min(iso.collection_date for iso in cohort)
    max_date = max(iso.collection_date for iso in cohort)
    span_days = (max_date - min_date).days + 1
    output_value = f"temporal_count={count};span_days={span_days};window_days={cfg.window_days}"
    status = ConcentrationStatus.SUCCESS

    finding_id = _compute_temporal_finding_id(
        policy_version=cfg.policy_version,
        algorithm_version=cfg.temporal_algorithm_version,
        config_version=cfg.config_version,
        window_start=window_start,
        window_end=window_end,
        organism_code=organism_code,
        facility_id=facility_id,
        input_refs=input_refs,
        facility_organism_count=count,
        observed_min_date=min_date,
        observed_max_date=max_date,
        observed_span_days=span_days,
        status=status,
        output_value=output_value,
    )

    return TemporalConcentrationFinding(
        finding_id=finding_id,
        policy_version=cfg.policy_version,
        algorithm_version=cfg.temporal_algorithm_version,
        config_version=cfg.config_version,
        organism_code=organism_code,
        facility_id=facility_id,
        window_start=window_start,
        window_end=window_end,
        facility_organism_count=count,
        input_refs=input_refs,
        observed_min_date=min_date,
        observed_max_date=max_date,
        observed_span_days=span_days,
        status=status,
        output_value=output_value,
    )


def evaluate_location_cohort(
    organism_code: str,
    facility_id: str,
    ward: str,
    isolates: Sequence[CanonicalIsolate],
    window_end: date,
    config: ConcentrationConfig | None = None,
) -> LocationConcentrationFinding:
    """Evaluate location concentration for a specific (organism, facility, ward) cohort.

    If zero isolates exist in the facility window, returns an INSUFFICIENT_DATA finding
    with reason EMPTY_DENOMINATOR.
    """
    cfg = config if config is not None else ConcentrationConfig()
    if type(window_end) is not date:
        raise TypeError(
            f"window_end must be an exact datetime.date; got {type(window_end).__name__}"
        )
    window_start = cfg.calculate_window_start(window_end)

    unique_isolates = _deduplicate_and_validate_isolates(isolates)
    fac_cohort = [
        iso
        for iso in unique_isolates
        if iso.organism_code == organism_code
        and iso.facility_id == facility_id
        and window_start <= iso.collection_date <= window_end
    ]
    fac_cohort.sort(key=lambda x: x.isolate_id)
    facility_count = len(fac_cohort)

    if facility_count == 0:
        status = ConcentrationStatus.INSUFFICIENT_DATA
        reason = ConcentrationReason.EMPTY_DENOMINATOR
        output_value = f"status=INSUFFICIENT_DATA;reason=EMPTY_DENOMINATOR;ward={ward}"
        finding_id = _compute_location_finding_id(
            policy_version=cfg.policy_version,
            algorithm_version=cfg.location_algorithm_version,
            config_version=cfg.config_version,
            window_start=window_start,
            window_end=window_end,
            organism_code=organism_code,
            facility_id=facility_id,
            ward=ward,
            ward_input_refs=(),
            facility_window_input_refs=(),
            input_refs=(),
            ward_organism_count=0,
            facility_organism_count=0,
            location_concentration_ratio=None,
            precision=cfg.precision,
            status=status,
            output_value=output_value,
        )
        return LocationConcentrationFinding(
            finding_id=finding_id,
            policy_version=cfg.policy_version,
            algorithm_version=cfg.location_algorithm_version,
            config_version=cfg.config_version,
            organism_code=organism_code,
            facility_id=facility_id,
            ward=ward,
            window_start=window_start,
            window_end=window_end,
            ward_organism_count=0,
            facility_organism_count=0,
            location_concentration_ratio=None,
            ward_input_refs=(),
            facility_window_input_refs=(),
            input_refs=(),
            status=status,
            reason=reason,
            output_value=output_value,
        )

    facility_refs = tuple(iso.isolate_id for iso in fac_cohort)
    ward_cohort = [iso for iso in fac_cohort if iso.ward == ward]
    ward_cohort.sort(key=lambda x: x.isolate_id)
    ward_count = len(ward_cohort)
    ward_refs = tuple(iso.isolate_id for iso in ward_cohort)

    ratio = round(ward_count / facility_count, cfg.precision)
    formatted_ratio = f"{ratio:.{cfg.precision}f}"
    output_value = (
        f"ward_share={formatted_ratio};ward_count={ward_count};"
        f"facility_count={facility_count};ward={ward}"
    )
    status = ConcentrationStatus.SUCCESS

    finding_id = _compute_location_finding_id(
        policy_version=cfg.policy_version,
        algorithm_version=cfg.location_algorithm_version,
        config_version=cfg.config_version,
        window_start=window_start,
        window_end=window_end,
        organism_code=organism_code,
        facility_id=facility_id,
        ward=ward,
        ward_input_refs=ward_refs,
        facility_window_input_refs=facility_refs,
        input_refs=facility_refs,
        ward_organism_count=ward_count,
        facility_organism_count=facility_count,
        location_concentration_ratio=ratio,
        precision=cfg.precision,
        status=status,
        output_value=output_value,
    )

    return LocationConcentrationFinding(
        finding_id=finding_id,
        policy_version=cfg.policy_version,
        algorithm_version=cfg.location_algorithm_version,
        config_version=cfg.config_version,
        organism_code=organism_code,
        facility_id=facility_id,
        ward=ward,
        window_start=window_start,
        window_end=window_end,
        ward_organism_count=ward_count,
        facility_organism_count=facility_count,
        location_concentration_ratio=ratio,
        ward_input_refs=ward_refs,
        facility_window_input_refs=facility_refs,
        input_refs=facility_refs,
        status=status,
        output_value=output_value,
    )
