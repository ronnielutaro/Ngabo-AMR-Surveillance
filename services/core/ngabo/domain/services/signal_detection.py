"""Deterministic baseline comparison and investigation-priority scoring (Issue #47).

Implements the maintainer-approved Ngabo v0.1 Prototype Investigation-Priority
Signal Policy (ADR 0012).

Primary Invariant: The result is an INVESTIGATION-PRIORITY POLICY OUTPUT.
It is NEVER an outbreak declaration, outbreak probability, diagnosis, model
confidence score, clinical decision, or prescribing/treatment guidance.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.enums.profile_similarity_status import ProfileSimilarityStatus
from ngabo.domain.enums.signal_status import SignalReason, SignalStatus
from ngabo.domain.services.concentration_analysis import (
    compute_location_concentration_findings,
    compute_temporal_concentration_findings,
)
from ngabo.domain.services.resistance_profile_similarity import compare_canonical_isolates
from ngabo.domain.value_objects.concentration_config import ConcentrationConfig
from ngabo.domain.value_objects.investigation_priority_signal import (
    InvestigationPrioritySignal,
    SignalComponents,
)
from ngabo.domain.value_objects.signal_config import SignalConfig


@dataclass(frozen=True)
class SignalEvaluationResult:
    """Evaluation outcome for a candidate cohort (organism, facility, ward)."""

    organism_code: str
    facility_id: str
    ward: str
    window_start: date
    window_end: date
    ward_organism_count: int
    status: SignalStatus
    reason: SignalReason
    components: SignalComponents | None
    signal_score: float | None
    signal: InvestigationPrioritySignal | None


def _resolve_governed_config(config: SignalConfig | None) -> SignalConfig:
    """Validate and resolve signal configuration with exact-type checking.

    Rejects subclasses, duck objects, mappings, or arbitrary objects to preserve
    closed policy governance established by ADR 0012.
    """
    if config is None:
        return SignalConfig()
    if type(config) is not SignalConfig:
        raise TypeError("config must be an exact validated SignalConfig")
    return config


def _deduplicate_and_validate_isolates(
    isolates: Sequence[CanonicalIsolate],
) -> tuple[CanonicalIsolate, ...]:
    """Validate isolate sequence and deduplicate identical records idempotently.

    Conflicting records sharing an isolate_id fail closed with ValueError.
    """
    if not isinstance(isolates, Sequence):
        raise TypeError(
            f"isolates must be a sequence of CanonicalIsolate; got {type(isolates).__name__}"
        )

    seen: dict[str, CanonicalIsolate] = {}
    for iso in isolates:
        if not isinstance(iso, CanonicalIsolate):
            raise TypeError(
                f"Expected CanonicalIsolate instance; got {type(iso).__name__}"
            )
        existing = seen.get(iso.isolate_id)
        if existing is not None:
            if existing != iso:
                raise ValueError(
                    f"Conflicting duplicate isolate_id detected: {iso.isolate_id!r}"
                )
            continue
        seen[iso.isolate_id] = iso

    return tuple(seen.values())


def _compute_signal_id(
    *,
    policy_version: str,
    config_version: str,
    algorithm_version: str,
    precision: int,
    facility_id: str,
    ward: str,
    organism_code: str,
    window_start: date,
    window_end: date,
    ward_organism_count: int,
    facility_organism_count: int,
    c_phenotype: float,
    c_location: float,
    c_temporal: float,
    c_baseline: float,
    signal_score: float,
    trigger_threshold: float,
    status: SignalStatus,
    supporting_finding_refs: Sequence[str],
    supporting_isolate_refs: Sequence[str],
    output_value: str,
) -> str:
    """Compute stable cryptographic signal identity from canonical serialized payload."""
    payload = {
        "algorithm_version": algorithm_version,
        "c_baseline": f"{c_baseline:.{precision}f}",
        "c_location": f"{c_location:.{precision}f}",
        "c_phenotype": f"{c_phenotype:.{precision}f}",
        "c_temporal": f"{c_temporal:.{precision}f}",
        "config_version": config_version,
        "facility_id": facility_id,
        "facility_organism_count": facility_organism_count,
        "organism_code": organism_code,
        "output_value": output_value,
        "policy_version": policy_version,
        "precision": precision,
        "signal_score": f"{signal_score:.{precision}f}",
        "status": status.value,
        "supporting_finding_refs": sorted(supporting_finding_refs),
        "supporting_isolate_refs": sorted(supporting_isolate_refs),
        "trigger_threshold": f"{trigger_threshold:.{precision}f}",
        "ward": ward,
        "ward_organism_count": ward_organism_count,
        "window_end": window_end.isoformat(),
        "window_start": window_start.isoformat(),
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(serialized).hexdigest()
    return f"sig-{digest[:16]}"


def evaluate_cohort_signal(
    organism_code: str,
    facility_id: str,
    ward: str,
    isolates: Sequence[CanonicalIsolate],
    window_end: date,
    config: SignalConfig | None = None,
) -> SignalEvaluationResult:
    """Evaluate an individual candidate cohort for investigation-priority signal criteria."""
    cfg = _resolve_governed_config(config)
    if type(window_end) is not date:
        raise TypeError(
            f"window_end must be an exact datetime.date; got {type(window_end).__name__}"
        )

    deduped = _deduplicate_and_validate_isolates(isolates)
    window_start = cfg.calculate_window_start(window_end)

    window_isolates = [
        iso for iso in deduped if window_start <= iso.collection_date <= window_end
    ]

    ward_isolates = sorted(
        [
            iso
            for iso in window_isolates
            if iso.organism_code == organism_code
            and iso.facility_id == facility_id
            and iso.ward == ward
        ],
        key=lambda x: x.isolate_id,
    )
    ward_organism_count = len(ward_isolates)

    facility_isolates = [
        iso
        for iso in window_isolates
        if iso.organism_code == organism_code and iso.facility_id == facility_id
    ]
    facility_organism_count = len(facility_isolates)

    # Minimum structural gate: ward_organism_count >= 3
    if ward_organism_count < cfg.min_candidate_count:
        return SignalEvaluationResult(
            organism_code=organism_code,
            facility_id=facility_id,
            ward=ward,
            window_start=window_start,
            window_end=window_end,
            ward_organism_count=ward_organism_count,
            status=SignalStatus.NO_SIGNAL,
            reason=SignalReason.INSUFFICIENT_CLUSTER_SIZE,
            components=None,
            signal_score=None,
            signal=None,
        )

    # Component 1: Phenotype similarity among candidate cohort isolates
    pairwise_findings = []
    pairwise_scores: list[float] = []
    for i in range(len(ward_isolates)):
        for j in range(i + 1, len(ward_isolates)):
            sim_finding = compare_canonical_isolates(ward_isolates[i], ward_isolates[j])
            if (
                sim_finding.status != ProfileSimilarityStatus.SUCCESS
                or sim_finding.similarity_score is None
            ):
                return SignalEvaluationResult(
                    organism_code=organism_code,
                    facility_id=facility_id,
                    ward=ward,
                    window_start=window_start,
                    window_end=window_end,
                    ward_organism_count=ward_organism_count,
                    status=SignalStatus.INSUFFICIENT_DATA,
                    reason=SignalReason.INSUFFICIENT_PHENOTYPE_EVIDENCE,
                    components=None,
                    signal_score=None,
                    signal=None,
                )
            pairwise_findings.append(sim_finding)
            pairwise_scores.append(sim_finding.similarity_score)

    if not pairwise_scores:
        return SignalEvaluationResult(
            organism_code=organism_code,
            facility_id=facility_id,
            ward=ward,
            window_start=window_start,
            window_end=window_end,
            ward_organism_count=ward_organism_count,
            status=SignalStatus.INSUFFICIENT_DATA,
            reason=SignalReason.INSUFFICIENT_PHENOTYPE_EVIDENCE,
            components=None,
            signal_score=None,
            signal=None,
        )

    c_phenotype = round(sum(pairwise_scores) / len(pairwise_scores), cfg.precision)
    c_phenotype = min(1.0, max(0.0, c_phenotype))

    # Component 2: Location concentration from Issue #46 findings
    loc_findings = compute_location_concentration_findings(
        deduped, window_end, ConcentrationConfig()
    )
    matching_loc = [
        f
        for f in loc_findings
        if f.organism_code == organism_code
        and f.facility_id == facility_id
        and f.ward == ward
    ]
    if not matching_loc:
        return SignalEvaluationResult(
            organism_code=organism_code,
            facility_id=facility_id,
            ward=ward,
            window_start=window_start,
            window_end=window_end,
            ward_organism_count=ward_organism_count,
            status=SignalStatus.INSUFFICIENT_DATA,
            reason=SignalReason.INSUFFICIENT_CLUSTER_SIZE,
            components=None,
            signal_score=None,
            signal=None,
        )
    loc_finding = matching_loc[0]
    if loc_finding.location_concentration_ratio is None:
        return SignalEvaluationResult(
            organism_code=organism_code,
            facility_id=facility_id,
            ward=ward,
            window_start=window_start,
            window_end=window_end,
            ward_organism_count=ward_organism_count,
            status=SignalStatus.INSUFFICIENT_DATA,
            reason=SignalReason.INSUFFICIENT_CLUSTER_SIZE,
            components=None,
            signal_score=None,
            signal=None,
        )
    c_location = min(1.0, max(0.0, loc_finding.location_concentration_ratio))

    # Component 3: Temporal concentration
    temp_findings = compute_temporal_concentration_findings(
        deduped, window_end, ConcentrationConfig()
    )
    matching_temp = [
        f
        for f in temp_findings
        if f.organism_code == organism_code and f.facility_id == facility_id
    ]
    if not matching_temp:
        return SignalEvaluationResult(
            organism_code=organism_code,
            facility_id=facility_id,
            ward=ward,
            window_start=window_start,
            window_end=window_end,
            ward_organism_count=ward_organism_count,
            status=SignalStatus.INSUFFICIENT_DATA,
            reason=SignalReason.INSUFFICIENT_CLUSTER_SIZE,
            components=None,
            signal_score=None,
            signal=None,
        )
    temp_finding = matching_temp[0]
    temp_ratio = round(ward_organism_count / float(cfg.min_candidate_count), cfg.precision)
    c_temporal = min(1.0, max(0.0, temp_ratio))

    # Component 4: Baseline excess calculation
    baseline_multiplier = facility_organism_count / cfg.configured_synthetic_baseline_count
    c_baseline = (baseline_multiplier - 1.0) / (cfg.baseline_saturation_multiplier - 1.0)
    c_baseline = min(1.0, max(0.0, round(c_baseline, cfg.precision)))

    components = SignalComponents(
        c_phenotype=c_phenotype,
        c_location=c_location,
        c_temporal=c_temporal,
        c_baseline=c_baseline,
    )

    # Composite score
    raw_score = (
        cfg.w_phenotype * c_phenotype
        + cfg.w_location * c_location
        + cfg.w_temporal * c_temporal
        + cfg.w_baseline * c_baseline
    )
    signal_score = min(1.0, max(0.0, round(raw_score, cfg.precision)))

    # Trigger rule: signal_score >= trigger_threshold AND ward_organism_count >= 3
    if signal_score >= cfg.trigger_threshold and ward_organism_count >= cfg.min_candidate_count:
        supporting_findings = sorted(
            [temp_finding.finding_id, loc_finding.finding_id]
            + [f.finding_id for f in pairwise_findings]
        )
        supporting_isolates = tuple(iso.isolate_id for iso in ward_isolates)

        output_val = (
            f"signal_score={signal_score:.{cfg.precision}f};"
            f"c_pheno={c_phenotype:.{cfg.precision}f};"
            f"c_loc={c_location:.{cfg.precision}f};"
            f"c_temp={c_temporal:.{cfg.precision}f};"
            f"c_base={c_baseline:.{cfg.precision}f};"
            f"ward={ward};k={ward_organism_count}"
        )

        signal_id = _compute_signal_id(
            policy_version=cfg.policy_version,
            config_version=cfg.config_version,
            algorithm_version=cfg.algorithm_version,
            precision=cfg.precision,
            facility_id=facility_id,
            ward=ward,
            organism_code=organism_code,
            window_start=window_start,
            window_end=window_end,
            ward_organism_count=ward_organism_count,
            facility_organism_count=facility_organism_count,
            c_phenotype=c_phenotype,
            c_location=c_location,
            c_temporal=c_temporal,
            c_baseline=c_baseline,
            signal_score=signal_score,
            trigger_threshold=cfg.trigger_threshold,
            status=SignalStatus.TRIGGERED,
            supporting_finding_refs=supporting_findings,
            supporting_isolate_refs=supporting_isolates,
            output_value=output_val,
        )

        signal = InvestigationPrioritySignal(
            signal_id=signal_id,
            policy_version=cfg.policy_version,
            algorithm_version=cfg.algorithm_version,
            config_version=cfg.config_version,
            organism_code=organism_code,
            facility_id=facility_id,
            ward=ward,
            window_start=window_start,
            window_end=window_end,
            ward_organism_count=ward_organism_count,
            facility_organism_count=facility_organism_count,
            components=components,
            signal_score=signal_score,
            trigger_threshold=cfg.trigger_threshold,
            status=SignalStatus.TRIGGERED,
            reason=SignalReason.HIGH_PRIORITY_CLUSTER,
            supporting_finding_refs=tuple(supporting_findings),
            supporting_isolate_refs=supporting_isolates,
            output_value=output_val,
        )

        return SignalEvaluationResult(
            organism_code=organism_code,
            facility_id=facility_id,
            ward=ward,
            window_start=window_start,
            window_end=window_end,
            ward_organism_count=ward_organism_count,
            status=SignalStatus.TRIGGERED,
            reason=SignalReason.HIGH_PRIORITY_CLUSTER,
            components=components,
            signal_score=signal_score,
            signal=signal,
        )

    return SignalEvaluationResult(
        organism_code=organism_code,
        facility_id=facility_id,
        ward=ward,
        window_start=window_start,
        window_end=window_end,
        ward_organism_count=ward_organism_count,
        status=SignalStatus.NO_SIGNAL,
        reason=SignalReason.BELOW_PRIORITY_THRESHOLD,
        components=components,
        signal_score=signal_score,
        signal=None,
    )


def evaluate_surveillance_signals(
    isolates: Sequence[CanonicalIsolate],
    window_end: date,
    config: SignalConfig | None = None,
) -> tuple[InvestigationPrioritySignal, ...]:
    """Evaluate surveillance signals across all candidate cohorts in the analysis window.

    Returns a deterministically sorted tuple of emitted investigation-priority
    signal candidates that satisfy both the structural gate and trigger threshold.
    """
    cfg = _resolve_governed_config(config)
    if type(window_end) is not date:
        raise TypeError(
            f"window_end must be an exact datetime.date; got {type(window_end).__name__}"
        )

    deduped = _deduplicate_and_validate_isolates(isolates)
    window_start = cfg.calculate_window_start(window_end)

    window_isolates = [
        iso for iso in deduped if window_start <= iso.collection_date <= window_end
    ]

    cohorts: set[tuple[str, str, str]] = {
        (iso.organism_code, iso.facility_id, iso.ward) for iso in window_isolates
    }

    signals: list[InvestigationPrioritySignal] = []
    for organism_code, facility_id, ward in sorted(cohorts):
        eval_result = evaluate_cohort_signal(
            organism_code=organism_code,
            facility_id=facility_id,
            ward=ward,
            isolates=deduped,
            window_end=window_end,
            config=cfg,
        )
        if eval_result.status == SignalStatus.TRIGGERED and eval_result.signal is not None:
            signals.append(eval_result.signal)

    return tuple(signals)
