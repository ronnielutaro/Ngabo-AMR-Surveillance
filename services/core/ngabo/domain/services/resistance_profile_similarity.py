"""Deterministic scientific logic for resistance profile similarity (Issue #45)."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.enums.profile_similarity_status import ProfileSimilarityStatus
from ngabo.domain.value_objects.profile_similarity_config import ProfileSimilarityConfig
from ngabo.domain.value_objects.profile_similarity_finding import ProfileSimilarityFinding
from ngabo.domain.value_objects.resistance_profile import ResistanceProfile


def _compute_stable_finding_id(
    policy_version: str,
    algorithm_version: str,
    config_version: str,
    input_refs: tuple[str, str],
    status: ProfileSimilarityStatus,
    output_value: str,
) -> str:
    """Compute a deterministic, opaque SHA-256 finding ID based on canonical attributes."""
    canonical_representation = (
        f"{policy_version}|{algorithm_version}|{config_version}|"
        f"{input_refs[0]}|{input_refs[1]}|{status.value}|{output_value}"
    ).encode()
    digest = hashlib.sha256(canonical_representation).hexdigest()
    return f"psim-{digest[:16]}"


def compute_profile_similarity(
    profile_a: ResistanceProfile,
    profile_b: ResistanceProfile,
    config: ProfileSimilarityConfig | None = None,
) -> ProfileSimilarityFinding:
    """Calculate the deterministic resistance profile similarity between two isolates.

    Follows the approved v0.1 scientific comparison policy:
    1. Symmetric pair ordering: input_refs is always sorted lexicographically by isolate ID.
    2. Self-comparison guard: identical isolate IDs yield IDENTICAL_INPUTS (similarity is None).
    3. Organism compatibility: differing organism codes yield INCOMPATIBLE_ORGANISM
       (similarity is None) when strict_organism_match is enabled.
    4. Panel overlap: only tested antibiotics with known interpretations (S, I, R) in BOTH profiles
       are comparable. UNKNOWN and untested values are strictly excluded from the denominator.
    5. Minimum panel threshold: if fewer than min_comparable_antibiotics (default 3) are shared,
       yields INSUFFICIENT_DATA (similarity is None).
    6. Exact agreement ratio: matching count / comparable count, rounded to similarity_precision.
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
            cfg.policy_version,
            cfg.algorithm_version,
            cfg.config_version,
            ordered_refs,
            status,
            output_value,
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

    # 2. Organism compatibility check
    if cfg.strict_organism_match and profile_a.organism_code != profile_b.organism_code:
        status = ProfileSimilarityStatus.INCOMPATIBLE_ORGANISM
        output_value = (
            f"status=INCOMPATIBLE_ORGANISM;org_a={profile_a.organism_code};"
            f"org_b={profile_b.organism_code}"
        )
        finding_id = _compute_stable_finding_id(
            cfg.policy_version,
            cfg.algorithm_version,
            cfg.config_version,
            ordered_refs,
            status,
            output_value,
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
            cfg.policy_version,
            cfg.algorithm_version,
            cfg.config_version,
            ordered_refs,
            status,
            output_value,
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
    output_value = (
        f"similarity={similarity_score:.4f};matching={len(matching)};"
        f"shared={len(comparable_antibiotics)}"
    )

    finding_id = _compute_stable_finding_id(
        cfg.policy_version,
        cfg.algorithm_version,
        cfg.config_version,
        ordered_refs,
        status,
        output_value,
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

    - De-duplicates identical isolate objects by isolate_id.
    - Sorts records by isolate_id so input order does not affect output.
    - Generates non-reflexive combinations of 2 (i < j).
    - Returns findings ordered deterministically by input_refs.
    """
    cfg = config if config is not None else ProfileSimilarityConfig()

    # Deduplicate by isolate_id while preserving first occurrence
    seen_ids: set[str] = set()
    unique_isolates: list[CanonicalIsolate] = []
    for iso in isolates:
        if iso.isolate_id not in seen_ids:
            seen_ids.add(iso.isolate_id)
            unique_isolates.append(iso)

    # Sort isolates deterministically by isolate_id
    sorted_isolates = sorted(unique_isolates, key=lambda x: x.isolate_id)

    findings: list[ProfileSimilarityFinding] = []
    n = len(sorted_isolates)
    for i in range(n):
        for j in range(i + 1, n):
            finding = compare_canonical_isolates(sorted_isolates[i], sorted_isolates[j], cfg)
            findings.append(finding)

    return tuple(findings)
