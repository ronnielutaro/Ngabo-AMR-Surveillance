"""Framework-free incident package codec: strict parser + canonical serializer (#52).

This is the deterministic boundary a future infrastructure Gemini adapter will
use to turn raw primitive model output into an immutable
:class:`IncidentPackageCandidate`, and to emit a canonical framework-free
representation for round-trip and review. It uses only stdlib ``json``; no
Pydantic, no Google SDK, no ADK, no cloud/network.

Parsing is strict: it validates against an explicit allowlist of fields at every
level, rejects unknown fields (including authority-bearing fields such as
``verified`` / ``authorized`` / ``ready_to_send``), rejects forbidden claim
families, rejects duplicate claim identities, and returns a stable typed
:class:`IncidentPackageParseResult` rather than raising bare ``ValueError``.

Serialization is canonical: all collections are normalized to primitives and
the JSON encoding uses sorted keys, so semantically equivalent packages always
produce the exact same canonical representation.
"""

from __future__ import annotations

import json

from ngabo.application.enums.incident_package_error_code import IncidentPackageErrorCode
from ngabo.application.value_objects.incident_package import (
    PACKAGE_CONTRACT_VERSION,
    DraftCoordinationMessage,
    IncidentPackageCandidate,
    IncidentPackageEvidenceBinding,
    IncidentPackageId,
    IncidentPackageMetadata,
    PackageContractVersion,
    PackageLimitation,
)
from ngabo.application.value_objects.incident_package_parse import (
    IncidentPackageParseFailure,
    IncidentPackageParseResult,
)
from ngabo.domain.enums.action_class import ActionClass
from ngabo.domain.enums.claim_type import ClaimType
from ngabo.domain.value_objects.claim_id import ClaimId
from ngabo.domain.value_objects.evidence_reference import (
    EvidenceReferenceId,
)
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.proof_references import (
    ApprovedEvidenceReference,
    CanonicalRecordReference,
    DeterministicFindingReference,
)
from ngabo.domain.value_objects.reasoning_claim import ReasoningClaim
from ngabo.domain.value_objects.source_watermark import SourceWatermark

_TOP_LEVEL_FIELDS = frozenset(
    {
        "package_id",
        "package_contract_version",
        "incident_id",
        "incident_version",
        "source_watermark",
        "metadata",
        "claims",
        "uncertainties",
        "limitations",
        "draft_coordination_message",
    }
)
_METADATA_FIELDS = frozenset(
    {
        "policy_config_version",
        "model_identifier",
        "model_version",
        "generation_run_id",
        "evidence_binding",
    }
)
_EVIDENCE_BINDING_FIELDS = frozenset(
    {"corpus_id", "manifest_version", "corpus_digest", "evidence_references"}
)
_CLAIM_FIELDS = frozenset(
    {
        "claim_id",
        "claim_type",
        "statement",
        "supporting_record_refs",
        "supporting_finding_refs",
        "supporting_evidence_refs",
        "supporting_claim_ids",
        "contradicting_claim_ids",
        "uncertainties",
        "requested_action_class",
        "confidence_label",
    }
)
_RECORD_REF_FIELDS = frozenset({"record_id", "field_path", "expected_value"})
_FINDING_REF_FIELDS = frozenset(
    {"finding_id", "policy_version", "input_refs", "output_value"}
)
_EVIDENCE_REF_FIELDS = frozenset({"source_id", "chunk_id", "provenance", "support"})
_DRAFT_FIELDS = frozenset(
    {"subject", "body", "intended_purpose", "candidate_recipient_role"}
)


def _add_error(
    errors: list[IncidentPackageParseFailure],
    code: IncidentPackageErrorCode,
    path: tuple[str, ...] = (),
    detail: str | None = None,
) -> None:
    errors.append(
        IncidentPackageParseFailure(code=code, path=path, detail=detail)
    )


def _check_unknown_fields(
    value: dict[str, object],
    allowed: frozenset[str],
    errors: list[IncidentPackageParseFailure],
    path: tuple[str, ...],
) -> None:
    for key in value:
        if key not in allowed:
            _add_error(
                errors,
                IncidentPackageErrorCode.FORBIDDEN_FIELD,
                (*path, key),
                f"unknown/unauthorized field {key!r}",
            )


def _require_str(
    value: dict[str, object],
    key: str,
    errors: list[IncidentPackageParseFailure],
    path: tuple[str, ...],
) -> str | None:
    raw = value.get(key)
    if raw is None:
        _add_error(
            errors,
            IncidentPackageErrorCode.MISSING_REQUIRED_FIELD,
            (*path, key),
            f"missing required field {key!r}",
        )
        return None
    if not isinstance(raw, str) or not raw.strip():
        _add_error(
            errors,
            IncidentPackageErrorCode.MALFORMED_PACKAGE,
            (*path, key),
            f"field {key!r} must be a non-blank string",
        )
        return None
    return raw


def _require_dict(
    value: dict[str, object],
    key: str,
    errors: list[IncidentPackageParseFailure],
    path: tuple[str, ...],
) -> dict[str, object] | None:
    raw = value.get(key)
    if raw is None:
        _add_error(
            errors,
            IncidentPackageErrorCode.MISSING_REQUIRED_FIELD,
            (*path, key),
            f"missing required field {key!r}",
        )
        return None
    if not isinstance(raw, dict):
        _add_error(
            errors,
            IncidentPackageErrorCode.MUTABLE_OR_INVALID_COLLECTION_SHAPE,
            (*path, key),
            f"field {key!r} must be a JSON object",
        )
        return None
    return raw


def _require_list(
    value: dict[str, object],
    key: str,
    errors: list[IncidentPackageParseFailure],
    path: tuple[str, ...],
) -> list[object] | None:
    raw = value.get(key)
    if raw is None:
        _add_error(
            errors,
            IncidentPackageErrorCode.MISSING_REQUIRED_FIELD,
            (*path, key),
            f"missing required field {key!r}",
        )
        return None
    if not isinstance(raw, list):
        _add_error(
            errors,
            IncidentPackageErrorCode.MUTABLE_OR_INVALID_COLLECTION_SHAPE,
            (*path, key),
            f"field {key!r} must be a JSON array",
        )
        return None
    return raw


def _str_list(
    value: object,
    errors: list[IncidentPackageParseFailure],
    path: tuple[str, ...],
) -> tuple[str, ...] | None:
    if not isinstance(value, list):
        _add_error(
            errors,
            IncidentPackageErrorCode.MUTABLE_OR_INVALID_COLLECTION_SHAPE,
            path,
            f"{'.'.join(path) or 'value'} must be a JSON array of strings",
        )
        return None
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            _add_error(
                errors,
                IncidentPackageErrorCode.MALFORMED_PACKAGE,
                (*path, str(index)),
                "expected a non-blank string",
            )
            continue
        result.append(item)
    return tuple(result)


def _parse_record_ref(
    value: object,
    errors: list[IncidentPackageParseFailure],
    path: tuple[str, ...],
) -> CanonicalRecordReference | None:
    if not isinstance(value, dict):
        _add_error(
            errors,
            IncidentPackageErrorCode.INVALID_REFERENCE_SHAPE,
            path,
            "canonical record reference must be a JSON object",
        )
        return None
    _check_unknown_fields(value, _RECORD_REF_FIELDS, errors, path)
    record_id = _require_str(value, "record_id", errors, path)
    field_path = _require_str(value, "field_path", errors, path)
    expected_value = _require_str(value, "expected_value", errors, path)
    if record_id is None or field_path is None or expected_value is None:
        return None
    try:
        return CanonicalRecordReference(
            record_id=record_id, field_path=field_path, expected_value=expected_value
        )
    except ValueError as exc:
        _add_error(errors, IncidentPackageErrorCode.INVALID_REFERENCE_SHAPE, path, str(exc))
        return None


def _parse_finding_ref(
    value: object,
    errors: list[IncidentPackageParseFailure],
    path: tuple[str, ...],
) -> DeterministicFindingReference | None:
    if not isinstance(value, dict):
        _add_error(
            errors,
            IncidentPackageErrorCode.INVALID_REFERENCE_SHAPE,
            path,
            "deterministic finding reference must be a JSON object",
        )
        return None
    _check_unknown_fields(value, _FINDING_REF_FIELDS, errors, path)
    finding_id = _require_str(value, "finding_id", errors, path)
    policy_version = _require_str(value, "policy_version", errors, path)
    output_value = _require_str(value, "output_value", errors, path)
    input_refs = _str_list(value.get("input_refs"), errors, (*path, "input_refs"))
    if (
        finding_id is None
        or policy_version is None
        or output_value is None
        or input_refs is None
    ):
        return None
    try:
        return DeterministicFindingReference(
            finding_id=finding_id,
            policy_version=policy_version,
            input_refs=input_refs,
            output_value=output_value,
        )
    except ValueError as exc:
        _add_error(errors, IncidentPackageErrorCode.INVALID_REFERENCE_SHAPE, path, str(exc))
        return None


def _parse_evidence_ref(
    value: object,
    errors: list[IncidentPackageParseFailure],
    path: tuple[str, ...],
) -> ApprovedEvidenceReference | None:
    if not isinstance(value, dict):
        _add_error(
            errors,
            IncidentPackageErrorCode.INVALID_REFERENCE_SHAPE,
            path,
            "approved evidence reference must be a JSON object",
        )
        return None
    _check_unknown_fields(value, _EVIDENCE_REF_FIELDS, errors, path)
    source_id = _require_str(value, "source_id", errors, path)
    provenance = _require_str(value, "provenance", errors, path)
    support = _require_str(value, "support", errors, path)
    chunk_id = value.get("chunk_id")
    if chunk_id is not None and (not isinstance(chunk_id, str) or not chunk_id.strip()):
        _add_error(
            errors,
            IncidentPackageErrorCode.INVALID_REFERENCE_SHAPE,
            (*path, "chunk_id"),
            "chunk_id must be a non-blank string or null",
        )
        chunk_id = None
    if source_id is None or provenance is None or support is None:
        return None
    try:
        return ApprovedEvidenceReference(
            source_id=source_id,
            chunk_id=chunk_id,
            provenance=provenance,
            support=support,
        )
    except ValueError as exc:
        _add_error(errors, IncidentPackageErrorCode.INVALID_REFERENCE_SHAPE, path, str(exc))
        return None


def _parse_claim(
    value: object,
    errors: list[IncidentPackageParseFailure],
    path: tuple[str, ...],
) -> ReasoningClaim | None:
    if not isinstance(value, dict):
        _add_error(
            errors,
            IncidentPackageErrorCode.MUTABLE_OR_INVALID_COLLECTION_SHAPE,
            path,
            "each claim must be a JSON object",
        )
        return None
    _check_unknown_fields(value, _CLAIM_FIELDS, errors, path)
    claim_id = _require_str(value, "claim_id", errors, path)
    claim_type_raw = _require_str(value, "claim_type", errors, path)
    statement = _require_str(value, "statement", errors, path)
    if claim_id is None or claim_type_raw is None or statement is None:
        return None
    try:
        claim_type = ClaimType(claim_type_raw)
    except ValueError:
        _add_error(
            errors,
            IncidentPackageErrorCode.MALFORMED_PACKAGE,
            (*path, "claim_type"),
            f"unsupported claim family {claim_type_raw!r}; forbidden clinical "
            "authority families are not in the v0.1 vocabulary",
        )
        return None

    record_refs: list[CanonicalRecordReference] = []
    finding_refs: list[DeterministicFindingReference] = []
    evidence_refs: list[ApprovedEvidenceReference] = []
    supporting_claim_ids: list[ClaimId] = []
    contradicting_claim_ids: list[ClaimId] = []
    uncertainties: tuple[str, ...] = ()

    record_refs_raw = value.get("supporting_record_refs", [])
    if not isinstance(record_refs_raw, list):
        _add_error(
            errors,
            IncidentPackageErrorCode.MUTABLE_OR_INVALID_COLLECTION_SHAPE,
            (*path, "supporting_record_refs"),
            "supporting_record_refs must be a JSON array",
        )
    else:
        for index, ref in enumerate(record_refs_raw):
            parsed = _parse_record_ref(ref, errors, (*path, "supporting_record_refs", str(index)))
            if parsed is not None:
                record_refs.append(parsed)

    finding_refs_raw = value.get("supporting_finding_refs", [])
    if not isinstance(finding_refs_raw, list):
        _add_error(
            errors,
            IncidentPackageErrorCode.MUTABLE_OR_INVALID_COLLECTION_SHAPE,
            (*path, "supporting_finding_refs"),
            "supporting_finding_refs must be a JSON array",
        )
    else:
        for index, ref in enumerate(finding_refs_raw):
            parsed_finding = _parse_finding_ref(
                ref, errors, (*path, "supporting_finding_refs", str(index))
            )
            if parsed_finding is not None:
                finding_refs.append(parsed_finding)

    evidence_refs_raw = value.get("supporting_evidence_refs", [])
    if not isinstance(evidence_refs_raw, list):
        _add_error(
            errors,
            IncidentPackageErrorCode.MUTABLE_OR_INVALID_COLLECTION_SHAPE,
            (*path, "supporting_evidence_refs"),
            "supporting_evidence_refs must be a JSON array",
        )
    else:
        for index, ref in enumerate(evidence_refs_raw):
            parsed_evidence = _parse_evidence_ref(
                ref, errors, (*path, "supporting_evidence_refs", str(index))
            )
            if parsed_evidence is not None:
                evidence_refs.append(parsed_evidence)

    for field in ("supporting_claim_ids", "contradicting_claim_ids"):
        raw_ids = value.get(field, [])
        if not isinstance(raw_ids, list):
            _add_error(
                errors,
                IncidentPackageErrorCode.MUTABLE_OR_INVALID_COLLECTION_SHAPE,
                (*path, field),
                f"{field} must be a JSON array",
            )
            continue
        for index, item in enumerate(raw_ids):
            if not isinstance(item, str):
                _add_error(
                    errors,
                    IncidentPackageErrorCode.MALFORMED_PACKAGE,
                    (*path, field, str(index)),
                    "expected a claim ID string",
                )
                continue
            try:
                target = ClaimId(item)
            except ValueError as exc:
                _add_error(
                    errors,
                    IncidentPackageErrorCode.INVALID_REFERENCE_SHAPE,
                    (*path, field, str(index)),
                    str(exc),
                )
                continue
            if field == "supporting_claim_ids":
                supporting_claim_ids.append(target)
            else:
                contradicting_claim_ids.append(target)

    if "uncertainties" in value:
        parsed_uncertainties = _str_list(
            value["uncertainties"], errors, (*path, "uncertainties")
        )
        if parsed_uncertainties is not None:
            uncertainties = parsed_uncertainties

    requested_action_class: ActionClass | None = None
    raw_action = value.get("requested_action_class")
    if raw_action is not None:
        try:
            requested_action_class = ActionClass(raw_action)
        except ValueError:
            _add_error(
                errors,
                IncidentPackageErrorCode.MALFORMED_PACKAGE,
                (*path, "requested_action_class"),
                f"unsupported action class {raw_action!r}",
            )

    confidence_label = value.get("confidence_label")
    if confidence_label is not None and (
        not isinstance(confidence_label, str) or not confidence_label.strip()
    ):
        _add_error(
            errors,
            IncidentPackageErrorCode.MALFORMED_PACKAGE,
            (*path, "confidence_label"),
            "confidence_label must be a non-blank string or null",
        )
        confidence_label = None

    if claim_type is ClaimType.HYPOTHESIS and not uncertainties:
        _add_error(
            errors,
            IncidentPackageErrorCode.MISSING_REQUIRED_FIELD,
            (*path, "uncertainties"),
            "a HYPOTHESIS claim must carry at least one uncertainty",
        )
        return None

    try:
        return ReasoningClaim(
            claim_id=ClaimId(claim_id),
            claim_type=claim_type,
            statement=statement,
            supporting_record_refs=tuple(record_refs),
            supporting_finding_refs=tuple(finding_refs),
            supporting_evidence_refs=tuple(evidence_refs),
            supporting_claim_ids=tuple(supporting_claim_ids),
            contradicting_claim_ids=tuple(contradicting_claim_ids),
            uncertainties=uncertainties,
            requested_action_class=requested_action_class,
            confidence_label=confidence_label,
        )
    except ValueError as exc:
        _add_error(errors, IncidentPackageErrorCode.MALFORMED_PACKAGE, path, str(exc))
        return None


def _parse_evidence_binding(
    value: dict[str, object],
    errors: list[IncidentPackageParseFailure],
    path: tuple[str, ...],
) -> IncidentPackageEvidenceBinding | None:
    _check_unknown_fields(value, _EVIDENCE_BINDING_FIELDS, errors, path)
    corpus_id = _require_str(value, "corpus_id", errors, path)
    manifest_version = _require_str(value, "manifest_version", errors, path)
    corpus_digest = _require_str(value, "corpus_digest", errors, path)
    references = _require_list(value, "evidence_references", errors, path)
    if corpus_id is None or manifest_version is None or corpus_digest is None or references is None:
        return None
    parsed_refs: list[EvidenceReferenceId] = []
    for index, item in enumerate(references):
        if not isinstance(item, str):
            _add_error(
                errors,
                IncidentPackageErrorCode.INVALID_REFERENCE_SHAPE,
                (*path, "evidence_references", str(index)),
                "evidence reference must be a string",
            )
            continue
        try:
            parsed_refs.append(EvidenceReferenceId(item))
        except ValueError as exc:
            _add_error(
                errors,
                IncidentPackageErrorCode.INVALID_REFERENCE_SHAPE,
                (*path, "evidence_references", str(index)),
                str(exc),
            )
    try:
        return IncidentPackageEvidenceBinding(
            corpus_id=corpus_id,
            manifest_version=manifest_version,
            corpus_digest=corpus_digest,
            evidence_references=tuple(parsed_refs),
        )
    except ValueError as exc:
        _add_error(errors, IncidentPackageErrorCode.INVALID_REFERENCE_SHAPE, path, str(exc))
        return None


def _parse_metadata(
    value: dict[str, object],
    errors: list[IncidentPackageParseFailure],
    path: tuple[str, ...],
) -> IncidentPackageMetadata | None:
    _check_unknown_fields(value, _METADATA_FIELDS, errors, path)
    policy_config = _require_str(value, "policy_config_version", errors, path)
    model_identifier = _require_str(value, "model_identifier", errors, path)
    model_version = _require_str(value, "model_version", errors, path)
    generation_run_id = value.get("generation_run_id")
    if generation_run_id is not None and (
        not isinstance(generation_run_id, str) or not generation_run_id.strip()
    ):
        _add_error(
            errors,
            IncidentPackageErrorCode.MALFORMED_PACKAGE,
            (*path, "generation_run_id"),
            "generation_run_id must be a non-blank string or null",
        )
        generation_run_id = None
    evidence_dict = _require_dict(value, "evidence_binding", errors, path)
    if (
        policy_config is None
        or model_identifier is None
        or model_version is None
        or evidence_dict is None
    ):
        return None
    evidence_binding = _parse_evidence_binding(
        evidence_dict, errors, (*path, "evidence_binding")
    )
    if evidence_binding is None:
        return None
    try:
        return IncidentPackageMetadata(
            policy_config_version=policy_config,
            model_identifier=model_identifier,
            model_version=model_version,
            generation_run_id=generation_run_id,
            evidence_binding=evidence_binding,
        )
    except ValueError as exc:
        _add_error(errors, IncidentPackageErrorCode.MALFORMED_PACKAGE, path, str(exc))
        return None


def _parse_draft(
    value: dict[str, object],
    errors: list[IncidentPackageParseFailure],
    path: tuple[str, ...],
) -> DraftCoordinationMessage | None:
    _check_unknown_fields(value, _DRAFT_FIELDS, errors, path)
    subject = _require_str(value, "subject", errors, path)
    body = _require_str(value, "body", errors, path)
    intended_purpose = _require_str(value, "intended_purpose", errors, path)
    recipient_role = _require_str(value, "candidate_recipient_role", errors, path)
    if (
        subject is None
        or body is None
        or intended_purpose is None
        or recipient_role is None
    ):
        return None
    try:
        return DraftCoordinationMessage(
            subject=subject,
            body=body,
            intended_purpose=intended_purpose,
            candidate_recipient_role=recipient_role,
        )
    except ValueError as exc:
        _add_error(errors, IncidentPackageErrorCode.MALFORMED_PACKAGE, path, str(exc))
        return None


def parse_incident_package(primitive: object) -> IncidentPackageParseResult:
    """Strictly parse primitive output into an immutable :class:`IncidentPackageCandidate`."""
    errors: list[IncidentPackageParseFailure] = []
    if not isinstance(primitive, dict):
        _add_error(
            errors,
            IncidentPackageErrorCode.MALFORMED_PACKAGE,
            (),
            "incident package primitive must be a JSON object",
        )
        return IncidentPackageParseResult(ok=False, errors=tuple(errors))
    _check_unknown_fields(primitive, _TOP_LEVEL_FIELDS, errors, ())

    package_id = _require_str(primitive, "package_id", errors, ())
    contract_version = _require_str(primitive, "package_contract_version", errors, ())
    incident_id = _require_str(primitive, "incident_id", errors, ())
    source_watermark = _require_str(primitive, "source_watermark", errors, ())
    metadata_raw = _require_dict(primitive, "metadata", errors, ())
    claims_raw = _require_list(primitive, "claims", errors, ())

    incident_version_raw = primitive.get("incident_version")
    if incident_version_raw is None:
        _add_error(
            errors,
            IncidentPackageErrorCode.MISSING_REQUIRED_FIELD,
            ("incident_version",),
            "missing required field 'incident_version'",
        )
    elif isinstance(incident_version_raw, bool) or not isinstance(
        incident_version_raw, int
    ):
        _add_error(
            errors,
            IncidentPackageErrorCode.MALFORMED_PACKAGE,
            ("incident_version",),
            "incident_version must be an integer",
        )

    if contract_version is not None and contract_version != PACKAGE_CONTRACT_VERSION:
        _add_error(
            errors,
            IncidentPackageErrorCode.UNSUPPORTED_PACKAGE_VERSION,
            ("package_contract_version",),
            f"unsupported package contract version {contract_version!r}; "
            f"supported version is {PACKAGE_CONTRACT_VERSION!r}",
        )

    parsed_claims: list[ReasoningClaim] = []
    seen_claim_ids: set[str] = set()
    if claims_raw is not None:
        for index, claim_raw in enumerate(claims_raw):
            claim = _parse_claim(claim_raw, errors, ("claims", str(index)))
            if claim is not None:
                claim_id_value = claim.claim_id.value
                if claim_id_value in seen_claim_ids:
                    _add_error(
                        errors,
                        IncidentPackageErrorCode.DUPLICATE_CLAIM_ID,
                        ("claims", str(index)),
                        f"duplicate claim ID {claim_id_value!r}",
                    )
                else:
                    seen_claim_ids.add(claim_id_value)
                    parsed_claims.append(claim)

    metadata: IncidentPackageMetadata | None = None
    if metadata_raw is not None:
        metadata = _parse_metadata(metadata_raw, errors, ("metadata",))

    package_uncertainties: tuple[str, ...] = ()
    if "uncertainties" in primitive:
        parsed = _str_list(
            primitive["uncertainties"], errors, ("uncertainties",)
        )
        if parsed is not None:
            package_uncertainties = parsed

    limitations: list[PackageLimitation] = []
    if "limitations" in primitive:
        raw_limitations = primitive["limitations"]
        if not isinstance(raw_limitations, list):
            _add_error(
                errors,
                IncidentPackageErrorCode.MUTABLE_OR_INVALID_COLLECTION_SHAPE,
                ("limitations",),
                "limitations must be a JSON array",
            )
        else:
            for index, item in enumerate(raw_limitations):
                if (
                    not isinstance(item, str)
                    or not item.strip()
                    or item != item.strip()
                ):
                    _add_error(
                        errors,
                        IncidentPackageErrorCode.MALFORMED_PACKAGE,
                        ("limitations", str(index)),
                        "limitation must be a non-blank string without edge whitespace",
                    )
                    continue
                try:
                    limitations.append(PackageLimitation(item))
                except ValueError as exc:
                    _add_error(
                        errors,
                        IncidentPackageErrorCode.MALFORMED_PACKAGE,
                        ("limitations", str(index)),
                        str(exc),
                    )

    draft: DraftCoordinationMessage | None = None
    if "draft_coordination_message" in primitive:
        raw_draft = primitive["draft_coordination_message"]
        if raw_draft is None:
            draft = None
        elif not isinstance(raw_draft, dict):
            _add_error(
                errors,
                IncidentPackageErrorCode.MUTABLE_OR_INVALID_COLLECTION_SHAPE,
                ("draft_coordination_message",),
                "draft_coordination_message must be a JSON object or null",
            )
        else:
            draft = _parse_draft(raw_draft, errors, ("draft_coordination_message",))

    if errors:
        return IncidentPackageParseResult(ok=False, errors=tuple(errors))

    assert package_id is not None
    assert contract_version is not None
    assert incident_id is not None
    assert source_watermark is not None
    assert metadata is not None
    assert isinstance(incident_version_raw, int) and not isinstance(
        incident_version_raw, bool
    )
    try:
        package = IncidentPackageCandidate(
            package_id=IncidentPackageId(package_id),
            contract_version=PackageContractVersion(contract_version),
            incident_id=IncidentId(incident_id),
            incident_version=IncidentVersion(incident_version_raw),
            source_watermark=SourceWatermark(source_watermark),
            metadata=metadata,
            claims=tuple(parsed_claims),
            uncertainties=package_uncertainties,
            limitations=tuple(limitations),
            draft_coordination_message=draft,
        )
    except ValueError as exc:
        return IncidentPackageParseResult(
            ok=False,
            errors=(
                IncidentPackageParseFailure(
                    code=IncidentPackageErrorCode.MALFORMED_PACKAGE,
                    detail=str(exc),
                ),
            ),
        )
    return IncidentPackageParseResult(ok=True, package=package)


def incident_package_to_primitive(package: IncidentPackageCandidate) -> dict[str, object]:
    """Deterministically serialize a package to a plain primitive mapping."""
    metadata = package.metadata
    binding = metadata.evidence_binding
    claims = []
    for claim in package.claims:
        claims.append(
            {
                "claim_id": claim.claim_id.value,
                "claim_type": claim.claim_type.value,
                "statement": claim.statement,
                "supporting_record_refs": [
                    {
                        "record_id": ref.record_id,
                        "field_path": ref.field_path,
                        "expected_value": ref.expected_value,
                    }
                    for ref in claim.supporting_record_refs
                ],
                "supporting_finding_refs": [
                    {
                        "finding_id": ref.finding_id,
                        "policy_version": ref.policy_version,
                        "input_refs": list(ref.input_refs),
                        "output_value": ref.output_value,
                    }
                    for ref in claim.supporting_finding_refs
                ],
                "supporting_evidence_refs": [
                    {
                        "source_id": ref.source_id,
                        "chunk_id": ref.chunk_id,
                        "provenance": ref.provenance,
                        "support": ref.support,
                    }
                    for ref in claim.supporting_evidence_refs
                ],
                "supporting_claim_ids": [
                    claim_id.value for claim_id in claim.supporting_claim_ids
                ],
                "contradicting_claim_ids": [
                    claim_id.value for claim_id in claim.contradicting_claim_ids
                ],
                "uncertainties": list(claim.uncertainties),
                "requested_action_class": (
                    claim.requested_action_class.value
                    if claim.requested_action_class is not None
                    else None
                ),
                "confidence_label": claim.confidence_label,
            }
        )
    primitive: dict[str, object] = {
        "package_id": package.package_id.value,
        "package_contract_version": package.contract_version.value,
        "incident_id": package.incident_id.value,
        "incident_version": package.incident_version.value,
        "source_watermark": package.source_watermark.value,
        "metadata": {
            "policy_config_version": metadata.policy_config_version,
            "model_identifier": metadata.model_identifier,
            "model_version": metadata.model_version,
            "generation_run_id": metadata.generation_run_id,
            "evidence_binding": {
                "corpus_id": binding.corpus_id,
                "manifest_version": binding.manifest_version,
                "corpus_digest": binding.corpus_digest,
                "evidence_references": [
                    reference.value for reference in binding.evidence_references
                ],
            },
        },
        "claims": claims,
        "uncertainties": list(package.uncertainties),
        "limitations": [limitation.value for limitation in package.limitations],
        "draft_coordination_message": (
            {
                "subject": package.draft_coordination_message.subject,
                "body": package.draft_coordination_message.body,
                "intended_purpose": package.draft_coordination_message.intended_purpose,
                "candidate_recipient_role": (
                    package.draft_coordination_message.candidate_recipient_role
                ),
            }
            if package.draft_coordination_message is not None
            else None
        ),
    }
    return primitive


def incident_package_to_canonical_json(package: IncidentPackageCandidate) -> str:
    """Return the canonical framework-free JSON representation of a package."""
    return json.dumps(
        incident_package_to_primitive(package),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def deserialize_incident_package(serialized: str) -> IncidentPackageParseResult:
    """Parse a canonical JSON string back into an immutable package."""
    try:
        primitive = json.loads(serialized)
    except json.JSONDecodeError as exc:
        return IncidentPackageParseResult(
            ok=False,
            errors=(
                IncidentPackageParseFailure(
                    code=IncidentPackageErrorCode.MALFORMED_PACKAGE,
                    detail=f"invalid JSON: {exc}",
                ),
            ),
        )
    return parse_incident_package(primitive)
