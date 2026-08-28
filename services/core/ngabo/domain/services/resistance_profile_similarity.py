"""Deterministic scientific logic for resistance profile similarity (Issue #45)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence

from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.enums.profile_similarity_status import ProfileSimilarityStatus
from ngabo.domain.value_objects.profile_similarity_config import (
    ProfileSimilarityConfig,
)
from ngabo.domain.value_objects.profile_similarity_finding import (
    ProfileSimilarityFinding,
)
from ngabo.domain.value_objects.resistance_profile import ResistanceProfile


def _compute_stable_finding_id(
    *,
    policy_version: str,
    algorithm_version: str,
    config_version: str,
    input_refs: tuple[str, str],
    organism_code: str | None,
    status: ProfileSimilarityStatus,
    comparable_antibiotics: tuple[str, ...],
    matching_antibiotics: tuple[str, ...],
    differing_antibiotics: tuple[str, ...],
    untested_or_unknown_antibiotics: tuple[str, ...],
    similarity_score: float | None,
    similarity_precision: int,
    output_value: str,
) -> str:
    """Compute a deterministic, opaque SHA-256 finding ID based on canonical attributes.

    Uses deterministic canonical JSON serialization with sorted keys and compact
    separators, binding the ID to all scientifically material finding content.
    """
    payload = {
        "algorithm_version": algorithm_version,
        "comparable_antibiotics": list(comparable_antibiotics),
        "config_version": config_version,
        "differing_antibiotics": list(differing_antibiotics),
        "input_refs": list(input_refs),
        "matching_antibiotics": list(matching_antibiotics),
        "organism_code": organism_code,
        "output_value": output_value,
        "policy_version": policy_version,
        "similarity_precision": similarity_precision,
        "similarity_score": (
            f"{similarity_score:.{similarity_precision}f}"
            if similarity_score is not None
            else None
        ),
        "status": status.value,
        "untested_or_unknown_antibiotics": list(untested_or_unknown_antibiotics),
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(serialized).hexdigest()
    return f"psim-{digest[:16]}"


def compute_profile_similarity(
    profile_a: ResistanceProfile,
    profile_b: ResistanceProfile,
    config: ProfileSimilarityConfig | None = None,
) -> ProfileSimilarityFinding:
    """Calculate the deterministic resistance profile similarity between two isolates.

    Follows the proposed v0.1 prototype similarity policy (pending explicit maintainer
    approval; see docs/DATA_SAFETY_EVALUATION.md for background):
    1. Symmetric pair ordering: input_refs is always sorted lexicographically by isolate ID.
    2. Self-comparison guard: identical isolate IDs yield IDENTICAL_INPUTS (similarity is None).
    3. Strict organism compatibility: differing organism codes yield INCOMPATIBLE_ORGANISM
       (similarity is None) in a symmetric manner.
    4. Panel overlap: only tested antibiotics with known interpretations (S, I, R) in BOTH profiles
       are comparable. UNKNOWN and untested values are strictly excluded from the denominator.
    5. Minimum panel threshold: if fewer than min_comparable_antibiotics (default 3, a synthetic
       prototype configuration rather than a clinical threshold) are shared,
       yields INSUFFICIENT_DATA (similarity is None).
    6. Exact agreement ratio: matching count / comparable count, rounded to similarity_precision.
    7. Pure phenotype similarity: findings represent AST profile agreement only; they do not
       constitute genomic relatedness, transmission links, outbreak confirmation, or clinical
       guidance.
    """
    cfg = config if config is not None else ProfileSimilarityConfig()

    ordered_refs: tuple[str, str] = (
        (profile_a.isolate_id, profile_b.isolate_id)
        if profile_a.isolate_id <= profile_b.isolate_id
        else (profile_b.isolate_id, profile_a.isolate_id)
    )

    # 1. Self-comparison guard
    if profile_a.isolate_id == profile_b.isolate_id:
        status = ProfileSimilarityStatus.IDENTICAL_INPUTS
        output_value = f"status=IDENTICAL_INPUTS;isolate_id={profile_a.isolate_id}"
        finding_id = _compute_stable_finding_id(
            policy_version=cfg.policy_version,
            algorithm_version=cfg.algorithm_version,
            config_version=cfg.config_version,
            input_refs=ordered_refs,
            organism_code=profile_a.organism_code,
            status=status,
            comparable_antibiotics=(),
            matching_antibiotics=(),
            differing_antibiotics=(),
            untested_or_unknown_antibiotics=(),
            similarity_score=None,
            similarity_precision=cfg.similarity_precision,
            output_value=output_value,
        )
        return ProfileSimilarityFinding(
            finding_id=finding_id,
            policy_version=cfg.policy_version,
            algorithm_version=cfg.algorithm_version,
            config_version=cfg.config_version,
            isolate_id_a=ordered_refs[0],
            isolate_id_b=ordered_refs[1],
            input_refs=ordered_refs,
            organism_code=profile_a.organism_code,
            status=status,
            comparable_antibiotics=(),
            matching_antibiotics=(),
            differing_antibiotics=(),
            untested_or_unknown_antibiotics=(),
            similarity_score=None,
            output_value=output_value,
        )

    # 2. Strict organism compatibility check
    if cfg.strict_organism_match and profile_a.organism_code != profile_b.organism_code:
        status = ProfileSimilarityStatus.INCOMPATIBLE_ORGANISM
        sorted_orgs = sorted([profile_a.organism_code, profile_b.organism_code])
        output_value = (
            f"status=INCOMPATIBLE_ORGANISM;org_a={sorted_orgs[0]};"
            f"org_b={sorted_orgs[1]}"
        )
        finding_id = _compute_stable_finding_id(
            policy_version=cfg.policy_version,
            algorithm_version=cfg.algorithm_version,
            config_version=cfg.config_version,
            input_refs=ordered_refs,
            organism_code=None,
            status=status,
            comparable_antibiotics=(),
            matching_antibiotics=(),
            differing_antibiotics=(),
            untested_or_unknown_antibiotics=(),
            similarity_score=None,
            similarity_precision=cfg.similarity_precision,
            output_value=output_value,
        )
        return ProfileSimilarityFinding(
            finding_id=finding_id,
            policy_version=cfg.policy_version,
            algorithm_version=cfg.algorithm_version,
            config_version=cfg.config_version,
            isolate_id_a=ordered_refs[0],
            isolate_id_b=ordered_refs[1],
            input_refs=ordered_refs,
            organism_code=None,
            status=status,
            comparable_antibiotics=(),
            matching_antibiotics=(),
            differing_antibiotics=(),
            untested_or_unknown_antibiotics=(),
            similarity_score=None,
            output_value=output_value,
        )

    shared_organism = profile_a.organism_code

    # 3. Determine comparable antibiotics (both tested and known in both profiles)
    set_a = set(profile_a.known_antibiotics)
    set_b = set(profile_b.known_antibiotics)
    comparable_set = set_a.intersection(set_b)
    comparable_antibiotics = tuple(sorted(comparable_set))

    # Identify untested or unknown antibiotics across union of tested
    all_tested_union = set(profile_a.tested_antibiotics).union(profile_b.tested_antibiotics)
    untested_or_unknown = tuple(sorted(all_tested_union.difference(comparable_set)))

    # 4. Minimum panel threshold check
    if len(comparable_antibiotics) < cfg.min_comparable_antibiotics:
        status = ProfileSimilarityStatus.INSUFFICIENT_DATA
        output_value = (
            f"status=INSUFFICIENT_DATA;shared={len(comparable_antibiotics)};"
            f"min_required={cfg.min_comparable_antibiotics}"
        )
        finding_id = _compute_stable_finding_id(
            policy_version=cfg.policy_version,
            algorithm_version=cfg.algorithm_version,
            config_version=cfg.config_version,
            input_refs=ordered_refs,
            organism_code=shared_organism,
            status=status,
            comparable_antibiotics=comparable_antibiotics,
            matching_antibiotics=(),
            differing_antibiotics=(),
            untested_or_unknown_antibiotics=untested_or_unknown,
            similarity_score=None,
            similarity_precision=cfg.similarity_precision,
            output_value=output_value,
        )
        return ProfileSimilarityFinding(
            finding_id=finding_id,
            policy_version=cfg.policy_version,
            algorithm_version=cfg.algorithm_version,
            config_version=cfg.config_version,
            isolate_id_a=ordered_refs[0],
            isolate_id_b=ordered_refs[1],
            input_refs=ordered_refs,
            organism_code=shared_organism,
            status=status,
            comparable_antibiotics=comparable_antibiotics,
            matching_antibiotics=(),
            differing_antibiotics=(),
            untested_or_unknown_antibiotics=untested_or_unknown,
            similarity_score=None,
            output_value=output_value,
        )

    # 5. Exact interpretation agreement ratio
    matching = tuple(
        code
        for code in comparable_antibiotics
        if profile_a.observations[code] == profile_b.observations[code]
    )
    differing = tuple(
        code
        for code in comparable_antibiotics
        if profile_a.observations[code] != profile_b.observations[code]
    )

    similarity_score = round(
        len(matching) / len(comparable_antibiotics), cfg.similarity_precision
    )
    status = ProfileSimilarityStatus.SUCCESS
    formatted_score = f"{similarity_score:.{cfg.similarity_precision}f}"
    output_value = (
        f"similarity={formatted_score};matching={len(matching)};"
        f"shared={len(comparable_antibiotics)}"
    )

    finding_id = _compute_stable_finding_id(
        policy_version=cfg.policy_version,
        algorithm_version=cfg.algorithm_version,
        config_version=cfg.config_version,
        input_refs=ordered_refs,
        organism_code=shared_organism,
        status=status,
        comparable_antibiotics=comparable_antibiotics,
        matching_antibiotics=matching,
        differing_antibiotics=differing,
        untested_or_unknown_antibiotics=untested_or_unknown,
        similarity_score=similarity_score,
        similarity_precision=cfg.similarity_precision,
        output_value=output_value,
    )

    return ProfileSimilarityFinding(
        finding_id=finding_id,
        policy_version=cfg.policy_version,
        algorithm_version=cfg.algorithm_version,
        config_version=cfg.config_version,
        isolate_id_a=ordered_refs[0],
        isolate_id_b=ordered_refs[1],
        input_refs=ordered_refs,
        organism_code=shared_organism,
        status=status,
        comparable_antibiotics=comparable_antibiotics,
        matching_antibiotics=matching,
        differing_antibiotics=differing,
        untested_or_unknown_antibiotics=untested_or_unknown,
        similarity_score=similarity_score,
        output_value=output_value,
    )


def compare_canonical_isolates(
    isolate_a: CanonicalIsolate,
    isolate_b: CanonicalIsolate,
    config: ProfileSimilarityConfig | None = None,
) -> ProfileSimilarityFinding:
    """Compare two CanonicalIsolates directly by deriving their ResistanceProfiles."""
    prof_a = ResistanceProfile.from_canonical_isolate(isolate_a)
    prof_b = ResistanceProfile.from_canonical_isolate(isolate_b)
    return compute_profile_similarity(prof_a, prof_b, config)


def compare_isolate_collection(
    isolates: Sequence[CanonicalIsolate],
    config: ProfileSimilarityConfig | None = None,
) -> tuple[ProfileSimilarityFinding, ...]:
    """Deterministically compute all pairwise profile similarities for an isolate collection.

    - Consumes canonical isolates.
    - Idempotently collapses exact value-identical duplicate records with the same isolate_id.
    - Fails closed (raises ValueError) if conflicting records share the same isolate_id.
    - Sorts records by isolate_id so input order does not affect output.
    - Generates non-reflexive combinations of 2 (i < j).
    - Returns findings ordered deterministically by input_refs.
    """
    cfg = config if config is not None else ProfileSimilarityConfig()

    seen_isolates: dict[str, CanonicalIsolate] = {}
    for iso in isolates:
        if iso.isolate_id in seen_isolates:
            existing = seen_isolates[iso.isolate_id]
            if existing != iso:
                raise ValueError(
                    f"Conflicting CanonicalIsolate records for {iso.isolate_id!r} in collection; "
                    "conflicting duplicate inputs must fail closed"
                )
            continue
        seen_isolates[iso.isolate_id] = iso

    sorted_isolates = sorted(seen_isolates.values(), key=lambda x: x.isolate_id)

    findings: list[ProfileSimilarityFinding] = []
    n = len(sorted_isolates)
    for i in range(n):
        for j in range(i + 1, n):
            finding = compare_canonical_isolates(sorted_isolates[i], sorted_isolates[j], cfg)
            findings.append(finding)

    return tuple(findings)
