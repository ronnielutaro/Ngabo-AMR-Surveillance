"""Focused tests for the deadline hero: verification -> A1 -> durable intent
-> delivery -> machine acknowledgement."""

from __future__ import annotations

import dataclasses
import json
from typing import cast

import pytest

from ngabo.application.enums.evidence_search_outcome import EvidenceSearchOutcome
from ngabo.application.enums.hero_error_code import HeroErrorCode
from ngabo.application.enums.hero_outcome import HeroOutcome
from ngabo.application.enums.intent_state import IntentState
from ngabo.application.enums.investigation_execution_outcome import (
    InvestigationExecutionOutcome,
)
from ngabo.application.enums.package_candidate_outcome import (
    PackageCandidateOutcome,
)
from ngabo.application.enums.triage_outcome import TriageOutcome
from ngabo.application.services.hero_support_context_builder import (
    HeroSupportContextBuilder,
)
from ngabo.application.services.incident_package_codec import parse_incident_package
from ngabo.application.use_cases.check_hero_freshness import CheckHeroFreshness
from ngabo.application.use_cases.hero_action_policy import HeroActionPolicy
from ngabo.application.use_cases.hero_orchestrator import HeroOrchestrator
from ngabo.application.use_cases.verify_hero_ack import VerifyHeroAck
from ngabo.application.use_cases.verify_hero_package import VerifyHeroPackage
from ngabo.application.value_objects.canonical_binding import (
    CanonicalEvidence,
    CanonicalFinding,
    HeroStateBinding,
)
from ngabo.application.value_objects.effect_delivery import EffectDelivery
from ngabo.application.value_objects.evidence_search import EvidenceSearchHit, EvidenceSearchResult
from ngabo.application.value_objects.hero_action_intent import HeroActionIntent
from ngabo.application.value_objects.hero_completion_result import HeroCompletionResult
from ngabo.application.value_objects.hero_payload import (
    HeroCoordinationPayload,
    validate_coordination_message,
)
from ngabo.application.value_objects.hero_support_context import HeroSupportContext
from ngabo.application.value_objects.incident_package import IncidentPackageCandidate
from ngabo.application.value_objects.investigation_execution import (
    EventInvestigationCommand,
    EventInvocationResult,
    InvestigationExecutionId,
)
from ngabo.application.value_objects.package_candidate_result import (
    PackageCandidateResult,
)
from ngabo.application.value_objects.triage_result import TriageResult
from ngabo.bootstrap.hero import HeroComposition
from ngabo.bootstrap.hero_serve import build_hero_composition
from ngabo.domain.enums.action_class import ActionClass
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.source_watermark import SourceWatermark
from ngabo.infrastructure.effect.fake_action_intent_store import FakeActionIntentStore
from ngabo.infrastructure.effect.fake_effect_port import FakeEffectPort
from ngabo.infrastructure.effect.fake_freshness_state_port import FakeFreshnessStatePort
from ngabo.infrastructure.hero.hero_runtime import HeroRuntime

INCIDENT = IncidentId("INC-001")
VERSION = IncidentVersion(1)
WATERMARK = SourceWatermark("ngabo-source-v1:sha256:abc123")
EXECUTION_ID = "RUN-" + "a" * 32
CORPUS_DIGEST = "575a8552d35eb1ab6b2bb8ffa60f020bf643f4358fa28c50865fbe79e9085aeb"
ACK_SECRET = "demo-ack-secret-not-for-production"


def _package_primitive(**overrides: object) -> dict[str, object]:
    primitive: dict[str, object] = {
        "package_id": "PKG-1",
        "package_contract_version": "1.0",
        "incident_id": INCIDENT.value,
        "incident_version": VERSION.value,
        "source_watermark": WATERMARK.value,
        "metadata": {
            "policy_config_version": "v1",
            "model_identifier": "google-adk",
            "model_version": "gemini-3.6-flash",
            "generation_run_id": EXECUTION_ID,
            "evidence_binding": {
                "corpus_id": "ngabo-approved-evidence-v1",
                "manifest_version": "1.0",
                "corpus_digest": CORPUS_DIGEST,
                "evidence_references": ["WHO-AMR-001::ipc-principle-01"],
            },
        },
        "claims": [
            {
                "claim_id": "claim-01",
                "claim_type": "OBSERVED_FACT",
                "statement": "ISO-031 organism_code is kle.",
                "supporting_record_refs": [
                    {
                        "record_id": "ISO-031",
                        "field_path": "organism_code",
                        "expected_value": "kle",
                    }
                ],
                "supporting_finding_refs": [],
                "supporting_evidence_refs": [],
                "supporting_claim_ids": [],
                "contradicting_claim_ids": [],
                "uncertainties": [],
                "requested_action_class": "A0",
                "confidence_label": "high",
            },
            {
                "claim_id": "claim-02",
                "claim_type": "DERIVED_FINDING",
                "statement": (
                    "psim-abc123 reports similarity=1.0000;matching=6;shared=6: "
                    "the two isolates share a high resistance phenotype."
                ),
                "supporting_record_refs": [],
                "supporting_finding_refs": [
                    {
                        "finding_id": "psim-abc123",
                        "policy_version": "v1",
                        "input_refs": ["ISO-031", "ISO-034"],
                        "output_value": "similarity=1.0000;matching=6;shared=6",
                    }
                ],
                "supporting_evidence_refs": [],
                "supporting_claim_ids": [],
                "contradicting_claim_ids": [],
                "uncertainties": [],
                "requested_action_class": "A0",
                "confidence_label": "high",
            },
            {
                "claim_id": "claim-03",
                "claim_type": "EVIDENCE_STATEMENT",
                "statement": (
                    "WHO-AMR-001::ipc-principle-01 states WHO-AMR-001 guidance "
                    "addresses surveillance interpretation."
                ),
                "supporting_record_refs": [],
                "supporting_finding_refs": [],
                "supporting_evidence_refs": [
                    {
                        "source_id": "WHO-AMR-001",
                        "chunk_id": "WHO-AMR-001::ipc-principle-01",
                        "provenance": "ngabo-approved-evidence-v1",
                        "support": "supports the surveillance interpretation",
                    }
                ],
                "supporting_claim_ids": [],
                "contradicting_claim_ids": [],
                "uncertainties": [],
                "requested_action_class": "A0",
                "confidence_label": "high",
            },
            {
                "claim_id": "claim-04",
                "claim_type": "ACTION_JUSTIFICATION",
                "statement": "Draft demo justification for a synthetic surveillance review.",
                "supporting_record_refs": [],
                "supporting_finding_refs": [],
                "supporting_evidence_refs": [],
                "supporting_claim_ids": ["claim-01", "claim-02", "claim-03"],
                "contradicting_claim_ids": [],
                "uncertainties": [],
                "requested_action_class": "A1",
                "confidence_label": "medium",
            },
        ],
        "uncertainties": ["Synthetic demo; not clinical truth."],
        "limitations": ["No final verification before this candidate."],
        "draft_coordination_message": {
            "subject": "Synthetic AMR surveillance review",
            "body": "Draft only. Synthetic demonstration.",
            "intended_purpose": "informational",
            "candidate_recipient_role": "demo review",
        },
    }
    primitive.update(overrides)
    return primitive


def _package(**overrides: object) -> IncidentPackageCandidate:
    parse = parse_incident_package(_package_primitive(**overrides))
    assert parse.ok and parse.package is not None
    return parse.package


def _canonical(**overrides: object) -> HeroSupportContext:
    return HeroSupportContext(
        incident_id=cast(IncidentId, overrides.get("incident_id", INCIDENT)),
        incident_version=cast(
            IncidentVersion, overrides.get("incident_version", VERSION)
        ),
        source_watermark=cast(
            SourceWatermark, overrides.get("source_watermark", WATERMARK)
        ),
        execution_id=cast(str, overrides.get("execution_id", EXECUTION_ID)),
        policy_config_version=cast(
            str, overrides.get("policy_config_version", "v1")
        ),
        canonical_records=cast(
            "dict[str, dict[str, str]]",
            overrides.get(
                "canonical_records",
                {"ISO-031": {"organism_code": "kle", "ward": "SYNTH-WARD-A"}},
            ),
        ),
        canonical_findings=cast(
            "dict[str, CanonicalFinding]",
            overrides.get(
                "canonical_findings",
                {
                    "psim-abc123": CanonicalFinding(
                        finding_id="psim-abc123",
                        policy_version="v1",
                        input_refs=("ISO-031", "ISO-034"),
                        output_value="similarity=1.0000;matching=6;shared=6",
                    )
                },
            ),
        ),
        canonical_evidence=cast(
            "dict[str, CanonicalEvidence]",
            overrides.get(
                "canonical_evidence",
                {
                    "WHO-AMR-001": CanonicalEvidence(
                        source_id="WHO-AMR-001",
                        provenance="ngabo-approved-evidence-v1",
                        chunk_ids=("WHO-AMR-001::ipc-principle-01",),
                    )
                },
            ),
        ),
        authorized_target_ids=frozenset(
            cast(
                "frozenset[str]",
                overrides.get("authorized_target_ids", frozenset({"demo-receiver-01"})),
            )
        ),
    )


def _binding(**overrides: object) -> HeroStateBinding:
    return HeroStateBinding(
        incident_id=cast(IncidentId, overrides.get("incident_id", INCIDENT)),
        incident_version=cast(
            IncidentVersion, overrides.get("incident_version", VERSION)
        ),
        source_watermark=cast(
            SourceWatermark, overrides.get("source_watermark", WATERMARK)
        ),
        policy_config_version=cast(
            str, overrides.get("policy_config_version", "v1")
        ),
    )


def _orchestrator(
    *,
    ack_secret: str = ACK_SECRET,
    port: FakeEffectPort | None = None,
    intent_store: FakeActionIntentStore | None = None,
    freshness: FakeFreshnessStatePort | None = None,
    coordination_message: str = "Synthetic demo surveillance review; draft only.",
) -> tuple[HeroOrchestrator, FakeEffectPort, FakeActionIntentStore, FakeFreshnessStatePort]:
    effect = port if port is not None else FakeEffectPort(ack_secret=ack_secret)
    store = intent_store if intent_store is not None else FakeActionIntentStore()
    fresh = (
        freshness
        if freshness is not None
        else FakeFreshnessStatePort(_binding())
    )
    orchestrator = HeroOrchestrator(
        verifier=VerifyHeroPackage(),
        policy=HeroActionPolicy(freshness=CheckHeroFreshness()),
        effect_port=effect,
        ack_verifier=VerifyHeroAck(ack_secret=ack_secret),
        intent_store=store,
        freshness_port=fresh,
        coordination_message=coordination_message,
    )
    return orchestrator, effect, store, fresh


class TestVerificationProofValues:
    def test_valid_package_verifies(self) -> None:
        result = VerifyHeroPackage().verify(_package(), _canonical())
        assert result.verified is True
        assert result.package is not None
        assert result.claim_count == 4

    def test_valid_record_id_wrong_field_value_blocks(self) -> None:
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[0]["supporting_record_refs"] = [
            {
                "record_id": "ISO-031",
                "field_path": "organism_code",
                "expected_value": "ecoli",  # altered vs canonical "kle"
            }
        ]
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False
        assert any("expected value" in e.detail for e in result.errors)

    def test_valid_finding_id_wrong_output_blocks(self) -> None:
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[1]["supporting_finding_refs"] = [
            {
                "finding_id": "psim-abc123",
                "policy_version": "v1",
                "input_refs": ["ISO-031", "ISO-034"],
                "output_value": "similarity=0.1000",
            }
        ]
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False
        assert any("output value" in e.detail for e in result.errors)

    def test_valid_finding_id_wrong_input_refs_blocks(self) -> None:
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[1]["supporting_finding_refs"] = [
            {
                "finding_id": "psim-abc123",
                "policy_version": "v1",
                "input_refs": ["ISO-031", "ISO-999"],
                "output_value": "similarity=1.0000;matching=6;shared=6",
            }
        ]
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False
        assert any("input refs" in e.detail for e in result.errors)

    def test_valid_finding_id_wrong_policy_version_blocks(self) -> None:
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[1]["supporting_finding_refs"] = [
            {
                "finding_id": "psim-abc123",
                "policy_version": "v2",
                "input_refs": ["ISO-031", "ISO-034"],
                "output_value": "similarity=1.0000;matching=6;shared=6",
            }
        ]
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False
        assert any("policy version" in e.detail for e in result.errors)

    def test_evidence_provenance_mismatch_blocks(self) -> None:
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[2]["supporting_evidence_refs"] = [
            {
                "source_id": "WHO-AMR-001",
                "chunk_id": "WHO-AMR-001::ipc-principle-01",
                "provenance": "fabricated-v999",
                "support": "supports",
            }
        ]
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False
        assert any("provenance" in e.detail for e in result.errors)

    def test_statement_unrelated_to_support_blocks(self) -> None:
        # OBSERVED_FACT claiming ten isolates in Ward Z but referencing only
        # ISO-031.organism_code == kle is not grounded in its support.
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[0]["statement"] = "Ten isolates were collected in Ward Z."
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False
        assert any("support material" in e.detail for e in result.errors)

    def test_statement_mentions_id_but_asserts_unrelated_fact_blocks(self) -> None:
        # OBSERVED_FACT mentions an existing record id but asserts a different,
        # unsupported proposition (isolate count / ward) than the referenced field.
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[0]["statement"] = (
            "ISO-031 was recorded; ten isolates were collected in Ward Z."
        )
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False
        assert any("support material" in e.detail for e in result.errors)

    def test_grounded_statement_with_unsupported_clause_blocks(self) -> None:
        # A grounded OBSERVED_FACT clause plus an extra unsupported clause must
        # not be accepted just because the grounded substrings are present.
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[0]["statement"] = (
            "ISO-031 organism_code is kle; ten isolates were collected in Ward Z."
        )
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False
        assert any("support material" in e.detail for e in result.errors)

    def test_completion_denial_claim_blocks(self) -> None:
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[1]["statement"] = (
            "psim-abc123 reports similarity=1.0000;matching=6;shared=6: "
            "PACKAGE_COMPLETED."
        )
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False
        assert any("authority" in e.detail for e in result.errors)

    def test_escalate_claim_blocks(self) -> None:
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[1]["statement"] = (
            "psim-abc123 reports similarity=1.0000;matching=6;shared=6: ESCALATE."
        )
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False

    def test_derived_statement_contradicting_output_blocks(self) -> None:
        # Statement asserts a different similarity while the reference copies the
        # canonical output; the statement cannot be related to the support.
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[1]["statement"] = (
            "The isolates are not similar (similarity=0.0)."
        )
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False
        assert any("support material" in e.detail for e in result.errors)

    def test_natural_language_authority_claim_blocks(self) -> None:
        # Ordinary-spaced authority claim must be rejected in package verification.
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[1]["statement"] = (
            "psim-abc123 reports similarity=1.0000;matching=6;shared=6: "
            "the outbreak is confirmed in ward A."
        )
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False
        assert any("authority" in e.detail for e in result.errors)

    def test_fabricated_record_finding_evidence_refs_block(self) -> None:
        for claim_index, field in (
            (0, "supporting_record_refs"),
            (1, "supporting_finding_refs"),
            (2, "supporting_evidence_refs"),
        ):
            mutated = _package_primitive()
            claims = cast("list[dict[str, object]]", mutated["claims"])
            claims[claim_index][field] = []  # empty family support -> family error
            parse = parse_incident_package(mutated)
            assert parse.ok and parse.package is not None
            result = VerifyHeroPackage().verify(parse.package, _canonical())
            assert result.verified is False

    def test_url_substituted_for_support_blocks(self) -> None:
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[0]["supporting_record_refs"] = [
            {
                "record_id": "https://evil.example.com",
                "field_path": "organism_code",
                "expected_value": "kle",
            }
        ]
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False


class TestClaimResolution:
    def test_nonexistent_supporting_claim_blocks(self) -> None:
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[3]["supporting_claim_ids"] = ["claim-99"]
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False
        assert any("non-existent claim" in e.detail for e in result.errors)

    def test_nonexistent_contradicting_claim_blocks(self) -> None:
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[1]["contradicting_claim_ids"] = ["claim-99"]
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False
        assert any("non-existent claim" in e.detail for e in result.errors)

    def test_self_reference_blocks(self) -> None:
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[3]["supporting_claim_ids"] = ["claim-04"]
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False
        assert any("itself" in e.detail for e in result.errors)

    def test_claim_dependency_cycle_blocks(self) -> None:
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        # Make OBSERVED_FACT support the DERIVED_FINDING and vice versa -> cycle.
        claims[0]["supporting_claim_ids"] = ["claim-02"]
        claims[1]["supporting_claim_ids"] = ["claim-01"]
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False
        assert any("cycle" in e.detail for e in result.errors)

    def test_requested_a2_action_class_blocks(self) -> None:
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[3]["requested_action_class"] = "A2"
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False
        assert any("A2" in e.detail for e in result.errors)

    def test_requested_a3_action_class_blocks(self) -> None:
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[3]["requested_action_class"] = "A3"
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _canonical())
        assert result.verified is False
        assert any("A3" in e.detail for e in result.errors)


class TestFreshnessReload:
    def test_unchanged_current_state_happy_path(self) -> None:
        orchestrator, effect, store, _ = _orchestrator(
            freshness=FakeFreshnessStatePort(_binding())
        )
        result = orchestrator.run(_package(), _canonical())
        assert result.outcome is HeroOutcome.HERO_COMPLETED
        assert result.intent is not None
        assert store.state(result.intent) is IntentState.ACKNOWLEDGED

    def test_canonical_state_advances_before_policy_blocks(self) -> None:
        # Verify against V1; the freshness port returns V2 at the pre-action reload.
        orchestrator, effect, store, _ = _orchestrator(
            freshness=FakeFreshnessStatePort(_binding(incident_version=IncidentVersion(2)))
        )
        result = orchestrator.run(_package(), _canonical())
        assert result.outcome is HeroOutcome.BLOCKED
        assert result.error_code is HeroErrorCode.STALE_VERSION_BINDING
        assert effect.calls == []
        assert store.state_transitions == []


class TestIdempotency:
    def test_same_logical_action_two_executions_same_key(self) -> None:
        orchestrator, _, _, _ = _orchestrator()
        ctx_a = _canonical(execution_id="RUN-" + "a" * 32)
        ctx_b = _canonical(execution_id="RUN-" + "b" * 32)
        intent_a = orchestrator._build_intent(
            ctx_a, "PKG-1", "demo-receiver-01", "0" * 64
        )
        intent_b = orchestrator._build_intent(
            ctx_b, "PKG-1", "demo-receiver-01", "0" * 64
        )
        assert intent_a.action_id == intent_b.action_id
        assert intent_a.idempotency_key == intent_b.idempotency_key

    def test_materially_different_action_different_key(self) -> None:
        orchestrator, _, _, _ = _orchestrator()
        ctx = _canonical()
        base = orchestrator._build_intent(ctx, "PKG-1", "demo-receiver-01", "0" * 64)
        different_target = orchestrator._build_intent(
            ctx, "PKG-1", "other-receiver", "0" * 64
        )
        different_payload = orchestrator._build_intent(
            ctx, "PKG-1", "demo-receiver-01", "1" * 64
        )
        assert base.idempotency_key != different_target.idempotency_key
        assert base.idempotency_key != different_payload.idempotency_key

    def test_same_logical_effect_different_package_id_same_key(self) -> None:
        orchestrator, _, _, _ = _orchestrator()
        ctx = _canonical()
        # The same logical effect must be idempotent even if the run-scoped
        # package ID differs (package ids derive from execution_id upstream).
        a = orchestrator._build_intent(ctx, "PKG-1", "demo-receiver-01", "0" * 64)
        b = orchestrator._build_intent(ctx, "PKG-2", "demo-receiver-01", "0" * 64)
        assert a.action_id == b.action_id
        assert a.idempotency_key == b.idempotency_key

    def test_duplicate_dispatch_cannot_become_duplicate_intent(self) -> None:
        orchestrator, effect, store, _ = _orchestrator()
        first = orchestrator.run(_package(), _canonical())
        assert first.outcome is HeroOutcome.HERO_COMPLETED
        assert len(effect.calls) == 1
        second = orchestrator.run(_package(), _canonical())
        # The same logical action re-dispatched cannot acquire ownership again.
        assert second.outcome is HeroOutcome.BLOCKED
        assert second.error_code is HeroErrorCode.INTENT_ALREADY_ACQUIRED
        assert len(effect.calls) == 1


class TestActionIntentPersistence:
    def test_persisted_intent_exists_before_effect(self) -> None:
        orchestrator, effect, store, _ = _orchestrator()
        result = orchestrator.run(_package(), _canonical())
        assert result.outcome is HeroOutcome.HERO_COMPLETED
        assert result.intent is not None
        assert store.state(result.intent) is IntentState.ACKNOWLEDGED
        assert effect.calls  # effect was sent after the intent was reserved

    def test_no_intent_no_effect(self) -> None:
        orchestrator, effect, store, _ = _orchestrator()
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[1]["supporting_finding_refs"] = [
            {
                "finding_id": "fake",
                "policy_version": "v1",
                "input_refs": ["ISO-031", "ISO-034"],
                "output_value": "x",
            }
        ]
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = orchestrator.run(parse.package, _canonical())
        assert result.outcome is HeroOutcome.BLOCKED
        assert effect.calls == []
        assert store.state_transitions == []

    def test_effect_error_never_becomes_success(self) -> None:
        class _RaisePort:
            def deliver(self, intent: object, payload: object) -> object:
                raise RuntimeError("transport down")

        orchestrator, effect, store, _ = _orchestrator(
            port=cast(FakeEffectPort, _RaisePort())
        )
        result = orchestrator.run(_package(), _canonical())
        assert result.outcome is HeroOutcome.FAILED
        assert result.error_code is HeroErrorCode.DELIVERY_FAILED
        assert result.intent is not None
        assert store.state(result.intent) is IntentState.RETRYABLE

    def test_ack_failure_never_acknowledged(self) -> None:
        store = FakeActionIntentStore()
        result = _run_with_mutated_delivery(action_id="WRONG", store=store)
        assert result.outcome is HeroOutcome.FAILED
        assert result.ack_verified is False
        assert result.intent is not None
        assert store.state(result.intent) is IntentState.FAILED

    def test_transient_delivery_failure_is_retryable_and_reacquires_same_key(self) -> None:
        class _RetryablePort(FakeEffectPort):
            def __init__(self) -> None:
                super().__init__(ack_secret=ACK_SECRET)
                self._attempts = 0

            def deliver(
                self,
                intent: HeroActionIntent,
                payload: HeroCoordinationPayload,
            ) -> EffectDelivery:
                self._attempts += 1
                if self._attempts == 1:
                    raise RuntimeError("transport down")
                return super().deliver(intent, payload)

        port = _RetryablePort()
        store = FakeActionIntentStore()
        orchestrator = HeroOrchestrator(
            verifier=VerifyHeroPackage(),
            policy=HeroActionPolicy(freshness=CheckHeroFreshness()),
            effect_port=port,
            ack_verifier=VerifyHeroAck(ack_secret=ACK_SECRET),
            intent_store=store,
            freshness_port=FakeFreshnessStatePort(_binding()),
            coordination_message="Synthetic demo surveillance review; draft only.",
        )
        first = orchestrator.run(_package(), _canonical())
        assert first.outcome is HeroOutcome.FAILED
        assert first.error_code is HeroErrorCode.DELIVERY_FAILED
        assert first.intent is not None
        assert store.state(first.intent) is IntentState.RETRYABLE
        # A redelivery reacquires the SAME logical intent + idempotency key and
        # proceeds to completion rather than blocking forever.
        second = orchestrator.run(_package(), _canonical())
        assert second.outcome is HeroOutcome.HERO_COMPLETED
        assert second.intent is not None
        assert store.state(second.intent) is IntentState.ACKNOWLEDGED

    def test_lease_expiry_reacquires_same_intent(self) -> None:
        store = FakeActionIntentStore()
        intent = HeroActionIntent(
            action_id="ACT-lease",
            incident_id=INCIDENT,
            incident_version=VERSION,
            source_watermark=WATERMARK,
            verified_package_id="PKG-1",
            action_class=ActionClass.SAFE_EXTERNAL_COORDINATION,
            authorized_target_id="demo-receiver-01",
            payload_hash="0" * 64,
            idempotency_key="idem-lease",
        )
        first = store.reserve(intent, lease_ttl_seconds=10.0, now=100.0)
        assert first.owned is True
        # Lease still valid -> duplicate acquire is NOT owned.
        second = store.reserve(intent, lease_ttl_seconds=10.0, now=105.0)
        assert second.owned is False
        # Lease expired -> reacquire SAME intent/key.
        third = store.reserve(intent, lease_ttl_seconds=10.0, now=115.0)
        assert third.owned is True
        assert third.intent.idempotency_key == intent.idempotency_key
        # Expired-lease redispatches count against the retry budget; after
        # max_retries the intent becomes terminal FAILED (never redispatched forever).
        fourth = store.reserve(intent, lease_ttl_seconds=10.0, now=126.0, max_retries=2)
        assert fourth.owned is True
        fifth = store.reserve(intent, lease_ttl_seconds=10.0, now=137.0, max_retries=2)
        assert fifth.owned is False
        assert fifth.state is IntentState.FAILED


class TestA1PayloadSafety:
    def test_safe_wording_allowed(self) -> None:
        ok, detail = validate_coordination_message(
            "Synthetic demo surveillance review; draft only."
        )
        assert ok is True and detail is None

    @pytest.mark.parametrize(
        "message",
        [
            "We prescribe IV meropenem immediately.",
            "This is a diagnosis of carbapenem-resistant infection.",
            "Outbreak confirmed in Ward A.",
            "We confirm an outbreak in Ward A.",
            "Mandatory containment is required.",
            "This is an official public health declaration.",
            "Notify the hospital immediately.",
            "We authorize immediate action.",
        ],
    )
    def test_unsafe_wording_rejected(self, message: str) -> None:
        ok, detail = validate_coordination_message(message)
        assert ok is False and detail is not None

    def test_orchestrator_rejects_unsafe_message_at_construction(self) -> None:
        with pytest.raises(ValueError):
            _orchestrator(coordination_message="Prescribe antibiotics now.")


class TestAck:
    def test_signed_correlated_ack_passes(self) -> None:
        orchestrator, effect, store, _ = _orchestrator()
        result = orchestrator.run(_package(), _canonical())
        assert result.outcome is HeroOutcome.HERO_COMPLETED
        assert result.ack_verified is True
        assert effect.calls[0].synthetic is True

    def test_wrong_action_id_blocks(self) -> None:
        result = _run_with_mutated_delivery(action_id="ACT-X")
        assert result.outcome is HeroOutcome.FAILED
        assert result.error_code is HeroErrorCode.ACK_CORRELATION_MISMATCH

    def test_wrong_payload_hash_blocks(self) -> None:
        result = _run_with_mutated_delivery(payload_hash="1" * 64)
        assert result.outcome is HeroOutcome.FAILED

    def test_invalid_signature_blocks(self) -> None:
        orchestrator = HeroOrchestrator(
            verifier=VerifyHeroPackage(),
            policy=HeroActionPolicy(),
            effect_port=FakeEffectPort(ack_secret="signer-secret"),
            ack_verifier=VerifyHeroAck(ack_secret="verifier-secret"),
            intent_store=FakeActionIntentStore(),
            freshness_port=FakeFreshnessStatePort(_binding()),
            coordination_message="draft only",
        )
        result = orchestrator.run(_package(), _canonical())
        assert result.outcome is HeroOutcome.FAILED
        assert result.error_code is HeroErrorCode.ACK_SIGNATURE_INVALID


def _run_with_mutated_delivery(
    action_id: str | None = None,
    payload_hash: str | None = None,
    store: FakeActionIntentStore | None = None,
) -> HeroCompletionResult:
    class _Port:
        def __init__(self) -> None:
            self.calls: list[HeroActionIntent] = []

        def deliver(
            self,
            intent: HeroActionIntent,
            payload: HeroCoordinationPayload,
        ) -> EffectDelivery:
            fake = FakeEffectPort(ack_secret=ACK_SECRET)
            d = fake.deliver(intent, payload)
            self.calls.append(intent)
            return dataclasses.replace(
                d,
                action_id=action_id if action_id is not None else d.action_id,
                payload_hash=payload_hash if payload_hash is not None else d.payload_hash,
            )

    port = _Port()
    store = store if store is not None else FakeActionIntentStore()
    orchestrator = HeroOrchestrator(
        verifier=VerifyHeroPackage(),
        policy=HeroActionPolicy(freshness=CheckHeroFreshness()),
        effect_port=port,
        ack_verifier=VerifyHeroAck(ack_secret=ACK_SECRET),
        intent_store=store,
        freshness_port=FakeFreshnessStatePort(_binding()),
        coordination_message="draft only",
    )
    return orchestrator.run(_package(), _canonical())
class TestHero:
    def test_no_downstream_action_on_verification_failure(self) -> None:
        orchestrator, effect, store, _ = _orchestrator()
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[1]["supporting_finding_refs"] = [
            {
                "finding_id": "fake",
                "policy_version": "v1",
                "input_refs": ["ISO-031", "ISO-034"],
                "output_value": "similarity=1.0000",
            }
        ]
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = orchestrator.run(parse.package, _canonical())
        assert result.outcome is HeroOutcome.BLOCKED
        assert effect.calls == []
        assert result.error_code is HeroErrorCode.UNVERIFIED_PACKAGE

    def test_hero_completed_impossible_before_ack(self) -> None:
        result = _run_with_mutated_delivery(action_id="ACT-X")
        assert result.outcome is HeroOutcome.FAILED
        assert result.ack_verified is False

    def test_zero_human_counters_remain_zero(self) -> None:
        orchestrator, _, _, _ = _orchestrator()
        result = orchestrator.run(_package(), _canonical())
        assert result.outcome is HeroOutcome.HERO_COMPLETED
        for key, value in result.zero_human.items():
            assert value == 0, f"{key} is not zero"


def _evidence_hit() -> EvidenceSearchHit:
    from ngabo.domain.value_objects.evidence_reference import (
        EvidenceReferenceId,
        EvidenceSourceId,
    )

    return EvidenceSearchHit(
        reference_id=EvidenceReferenceId("WHO-AMR-001::ipc-principle-01"),
        source_id=EvidenceSourceId("WHO-AMR-001"),
        publisher="WHO",
        source_title="IPC guidance",
        canonical_url="https://www.who.int/publications/i/item/9789241550178",
        publication_date="2017-11-01",
        source_version="1",
        attribution_required=True,
        content="Contact precautions.",
        chunk_tags=("ipc",),
        score=4,
    )


class _FixedContextBuilder(HeroSupportContextBuilder):
    def build(self, *args: object) -> HeroSupportContext:
        del args
        return _canonical()


class _StubInvestigation:
    def __init__(self, outcome: InvestigationExecutionOutcome) -> None:
        self._outcome = outcome

    def execute(self, command: object) -> EventInvocationResult:
        del command
        return EventInvocationResult(
            outcome=self._outcome,
            execution_id=InvestigationExecutionId(EXECUTION_ID),
            metadata=None,
            capability_result=None,
            failure_code=None,
        )


class _StubTriage:
    def triage(self, ready: object) -> TriageResult:
        del ready
        return TriageResult(
            outcome=TriageOutcome.EVIDENCE_RETRIEVED,
            proposal=None,
            evidence_result=EvidenceSearchResult(
                outcome=EvidenceSearchOutcome.SUCCESS, hits=(_evidence_hit(),)
            ),
            model_calls=1,
            duration_ms=1,
            model_version="gemini-3.6-flash",
            error_code=None,
            execution_id=EXECUTION_ID,
        )


class _StubSynthesis:
    def synthesize(self, ready: object, triage: object) -> PackageCandidateResult:
        del ready, triage
        return PackageCandidateResult(
            outcome=PackageCandidateOutcome.PACKAGE_CANDIDATE_GENERATED,
            package=_package(),
            model_calls=1,
            duration_ms=1,
            model_version="gemini-3.6-flash",
            error_code=None,
            execution_id=EXECUTION_ID,
        )


class TestHeroRuntimeComposition:
    def test_hero_runtime_composes_full_chain(self) -> None:
        store = FakeActionIntentStore()
        runtime = HeroRuntime(
            investigation_runtime=_StubInvestigation(
                InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
            ),
            triage_runtime=_StubTriage(),
            synthesis_runtime=_StubSynthesis(),
            hero_orchestrator=HeroOrchestrator(
                verifier=VerifyHeroPackage(),
                policy=HeroActionPolicy(freshness=CheckHeroFreshness()),
                effect_port=FakeEffectPort(ack_secret=ACK_SECRET),
                ack_verifier=VerifyHeroAck(ack_secret=ACK_SECRET),
                intent_store=store,
                freshness_port=FakeFreshnessStatePort(_binding()),
                coordination_message="Synthetic demo surveillance review; draft only.",
            ),
            context_builder=_FixedContextBuilder(),
        )
        result = runtime.execute(
            EventInvestigationCommand(
                incident_id=INCIDENT,
                incident_version=VERSION,
                source_watermark=WATERMARK,
                event_id="evt-hero-001",
                correlation_id="corr-hero-001",
            )
        )
        assert result.outcome is HeroOutcome.HERO_COMPLETED
        assert result.ack_verified is True
        for key, value in result.zero_human.items():
            assert value == 0, f"{key} is not zero"

    def test_hero_runtime_fails_closed_on_blocked_investigation(self) -> None:
        runtime = HeroRuntime(
            investigation_runtime=_StubInvestigation(
                InvestigationExecutionOutcome.BLOCKED
            ),
            triage_runtime=_StubTriage(),
            synthesis_runtime=_StubSynthesis(),
            hero_orchestrator=HeroOrchestrator(
                verifier=VerifyHeroPackage(),
                policy=HeroActionPolicy(),
                effect_port=FakeEffectPort(ack_secret=ACK_SECRET),
                ack_verifier=VerifyHeroAck(ack_secret=ACK_SECRET),
                intent_store=FakeActionIntentStore(),
                freshness_port=FakeFreshnessStatePort(_binding()),
                coordination_message="draft only",
            ),
            context_builder=_FixedContextBuilder(),
        )
        result = runtime.execute(
            EventInvestigationCommand(
                incident_id=INCIDENT,
                incident_version=VERSION,
                source_watermark=WATERMARK,
                event_id="evt-hero-002",
                correlation_id="corr-hero-002",
            )
        )
        assert result.outcome is HeroOutcome.BLOCKED


class TestHeroIngress:
    def test_post_surveillance_runs_hero_via_composition(self) -> None:
        from fastapi.testclient import TestClient

        from ngabo.interfaces import http as http_adapter

        runtime = HeroRuntime(
            investigation_runtime=_StubInvestigation(
                InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
            ),
            triage_runtime=_StubTriage(),
            synthesis_runtime=_StubSynthesis(),
            hero_orchestrator=HeroOrchestrator(
                verifier=VerifyHeroPackage(),
                policy=HeroActionPolicy(freshness=CheckHeroFreshness()),
                effect_port=FakeEffectPort(ack_secret=ACK_SECRET),
                ack_verifier=VerifyHeroAck(ack_secret=ACK_SECRET),
                intent_store=FakeActionIntentStore(),
                freshness_port=FakeFreshnessStatePort(_binding()),
                coordination_message="Synthetic demo surveillance review; draft only.",
            ),
            context_builder=_FixedContextBuilder(),
        )
        http_adapter.hero_composition = HeroComposition(hero_runtime=runtime)
        client = TestClient(http_adapter.app)
        response = client.post(
            "/surveillance",
            json={
                "contract_version": "ngabo-event-investigation-v1",
                "incident_id": INCIDENT.value,
                "incident_version": VERSION.value,
                "source_watermark": WATERMARK.value,
                "event_id": "evt-ingress-001",
                "correlation_id": "corr-ingress-001",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["outcome"] == "HERO_COMPLETED"
        assert body["ack_verified"] is True
        assert all(value == 0 for value in body["zero_human"].values())
        assert any(evt["event"] == "HERO_COMPLETED" for evt in body["events"])

    def test_post_surveillance_decodes_pubsub_envelope(self) -> None:
        import base64 as _b64

        from fastapi.testclient import TestClient

        from ngabo.interfaces import http as http_adapter

        runtime = HeroRuntime(
            investigation_runtime=_StubInvestigation(
                InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
            ),
            triage_runtime=_StubTriage(),
            synthesis_runtime=_StubSynthesis(),
            hero_orchestrator=HeroOrchestrator(
                verifier=VerifyHeroPackage(),
                policy=HeroActionPolicy(freshness=CheckHeroFreshness()),
                effect_port=FakeEffectPort(ack_secret=ACK_SECRET),
                ack_verifier=VerifyHeroAck(ack_secret=ACK_SECRET),
                intent_store=FakeActionIntentStore(),
                freshness_port=FakeFreshnessStatePort(_binding()),
                coordination_message="Synthetic demo surveillance review; draft only.",
            ),
            context_builder=_FixedContextBuilder(),
        )
        http_adapter.hero_composition = HeroComposition(hero_runtime=runtime)
        command = {
            "contract_version": "ngabo-event-investigation-v1",
            "incident_id": INCIDENT.value,
            "incident_version": VERSION.value,
            "source_watermark": WATERMARK.value,
            "event_id": "evt-pubsub-001",
            "correlation_id": "corr-pubsub-001",
        }
        encoded_data = _b64.b64encode(
            json.dumps(command).encode("utf-8")
        ).decode("utf-8")
        envelope = {
            "message": {"data": encoded_data, "messageId": "m-1"},
            "subscription": "projects/ngabo-amr-2026/subscriptions/hero",
        }
        client = TestClient(http_adapter.app)
        response = client.post("/surveillance", json=envelope)
        assert response.status_code == 200
        assert response.json()["outcome"] == "HERO_COMPLETED"


class TestHeroAckStatusAndBootstrap:
    def _runtime(self, port: FakeEffectPort | None = None) -> HeroRuntime:
        return HeroRuntime(
            investigation_runtime=_StubInvestigation(
                InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
            ),
            triage_runtime=_StubTriage(),
            synthesis_runtime=_StubSynthesis(),
            hero_orchestrator=HeroOrchestrator(
                verifier=VerifyHeroPackage(),
                policy=HeroActionPolicy(freshness=CheckHeroFreshness()),
                effect_port=port if port is not None else FakeEffectPort(ack_secret=ACK_SECRET),
                ack_verifier=VerifyHeroAck(ack_secret=ACK_SECRET),
                intent_store=FakeActionIntentStore(),
                freshness_port=FakeFreshnessStatePort(_binding()),
                coordination_message="Synthetic demo surveillance review; draft only.",
            ),
            context_builder=_FixedContextBuilder(),
        )

    def _post(self, event_id: str, envelope: bool = False) -> object:
        from fastapi.testclient import TestClient

        from ngabo.interfaces import http as http_adapter

        http_adapter.hero_composition = HeroComposition(hero_runtime=self._runtime())
        command = {
            "contract_version": "ngabo-event-investigation-v1",
            "incident_id": INCIDENT.value,
            "incident_version": VERSION.value,
            "source_watermark": WATERMARK.value,
            "event_id": event_id,
            "correlation_id": f"corr-{event_id}",
        }
        if not envelope:
            payload = command
        else:
            import base64 as _b64

            payload = {
                "message": {
                    "data": _b64.b64encode(json.dumps(command).encode("utf-8")).decode("utf-8"),
                    "messageId": f"m-{event_id}",
                },
                "subscription": "projects/ngabo-amr-2026/subscriptions/hero",
            }
        client = TestClient(http_adapter.app)
        return client.post("/surveillance", json=payload)

    def test_bootstrap_builds_and_installs_production_composition(self) -> None:
        from fastapi.testclient import TestClient

        from ngabo.interfaces import http as http_adapter

        composition = build_hero_composition(
            investigation_runtime=_StubInvestigation(
                InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
            ),
            triage_runtime=_StubTriage(),
            synthesis_runtime=_StubSynthesis(),
            hero_orchestrator=HeroOrchestrator(
                verifier=VerifyHeroPackage(),
                policy=HeroActionPolicy(freshness=CheckHeroFreshness()),
                effect_port=FakeEffectPort(ack_secret=ACK_SECRET),
                ack_verifier=VerifyHeroAck(ack_secret=ACK_SECRET),
                intent_store=FakeActionIntentStore(),
                freshness_port=FakeFreshnessStatePort(_binding()),
                coordination_message="Synthetic demo surveillance review; draft only.",
            ),
            context_builder=_FixedContextBuilder(),
        )
        http_adapter.configure_hero_composition(composition)
        client = TestClient(http_adapter.app)
        response = client.post(
            "/surveillance",
            json={
                "contract_version": "ngabo-event-investigation-v1",
                "incident_id": INCIDENT.value,
                "incident_version": VERSION.value,
                "source_watermark": WATERMARK.value,
                "event_id": "evt-boot-001",
                "correlation_id": "corr-boot-001",
            },
        )
        assert response.status_code == 200
        assert response.json()["outcome"] == "HERO_COMPLETED"

    def test_retryable_delivery_failure_returns_non_2xx(self) -> None:
        class _RetryablePort(FakeEffectPort):
            def __init__(self) -> None:
                super().__init__(ack_secret=ACK_SECRET)

            def deliver(
                self,
                intent: HeroActionIntent,
                payload: HeroCoordinationPayload,
            ) -> EffectDelivery:
                raise RuntimeError("transport down")

        from fastapi.testclient import TestClient

        from ngabo.interfaces import http as http_adapter

        http_adapter.hero_composition = HeroComposition(
            hero_runtime=self._runtime(port=_RetryablePort())
        )
        command = {
            "contract_version": "ngabo-event-investigation-v1",
            "incident_id": INCIDENT.value,
            "incident_version": VERSION.value,
            "source_watermark": WATERMARK.value,
            "event_id": "evt-retry-001",
            "correlation_id": "corr-retry-001",
        }
        client = TestClient(http_adapter.app)
        response = client.post("/surveillance", json=command)
        assert response.status_code == 503

    def test_terminal_verification_failure_returns_2xx(self) -> None:
        from fastapi.testclient import TestClient

        from ngabo.interfaces import http as http_adapter

        class _BadSynthesis:
            def synthesize(self, ready: object, triage: object) -> PackageCandidateResult:
                del ready, triage
                mutated = _package_primitive()
                claims = cast("list[dict[str, object]]", mutated["claims"])
                claims[1]["supporting_finding_refs"] = [
                    {
                        "finding_id": "fake",
                        "policy_version": "v1",
                        "input_refs": ["ISO-031", "ISO-034"],
                        "output_value": "x",
                    }
                ]
                parse = parse_incident_package(mutated)
                assert parse.ok and parse.package is not None
                return PackageCandidateResult(
                    outcome=PackageCandidateOutcome.PACKAGE_CANDIDATE_GENERATED,
                    package=parse.package,
                    model_calls=1,
                    duration_ms=1,
                    model_version="gemini-3.6-flash",
                    error_code=None,
                    execution_id=EXECUTION_ID,
                )

        runtime = HeroRuntime(
            investigation_runtime=_StubInvestigation(
                InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
            ),
            triage_runtime=_StubTriage(),
            synthesis_runtime=_BadSynthesis(),
            hero_orchestrator=HeroOrchestrator(
                verifier=VerifyHeroPackage(),
                policy=HeroActionPolicy(freshness=CheckHeroFreshness()),
                effect_port=FakeEffectPort(ack_secret=ACK_SECRET),
                ack_verifier=VerifyHeroAck(ack_secret=ACK_SECRET),
                intent_store=FakeActionIntentStore(),
                freshness_port=FakeFreshnessStatePort(_binding()),
                coordination_message="Synthetic demo surveillance review; draft only.",
            ),
            context_builder=_FixedContextBuilder(),
        )
        http_adapter.hero_composition = HeroComposition(hero_runtime=runtime)
        command = {
            "contract_version": "ngabo-event-investigation-v1",
            "incident_id": INCIDENT.value,
            "incident_version": VERSION.value,
            "source_watermark": WATERMARK.value,
            "event_id": "evt-term-001",
            "correlation_id": "corr-term-001",
        }
        client = TestClient(http_adapter.app)
        response = client.post("/surveillance", json=command)
        # Terminal verification failure -> 2xx acknowledgement (no redelivery loop).
        assert response.status_code == 200
        assert response.json()["outcome"] == "BLOCKED"

    def test_duplicate_pubsub_delivery_reacquires_same_intent(self) -> None:
        import base64 as _b64

        from fastapi.testclient import TestClient

        from ngabo.interfaces import http as http_adapter

        class _RetryThenSuccessPort(FakeEffectPort):
            def __init__(self) -> None:
                super().__init__(ack_secret=ACK_SECRET)
                self._attempts = 0

            def deliver(
                self,
                intent: HeroActionIntent,
                payload: HeroCoordinationPayload,
            ) -> EffectDelivery:
                self._attempts += 1
                if self._attempts == 1:
                    raise RuntimeError("transport down")
                return super().deliver(intent, payload)

        store = FakeActionIntentStore()
        runtime = HeroRuntime(
            investigation_runtime=_StubInvestigation(
                InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
            ),
            triage_runtime=_StubTriage(),
            synthesis_runtime=_StubSynthesis(),
            hero_orchestrator=HeroOrchestrator(
                verifier=VerifyHeroPackage(),
                policy=HeroActionPolicy(freshness=CheckHeroFreshness()),
                effect_port=_RetryThenSuccessPort(),
                ack_verifier=VerifyHeroAck(ack_secret=ACK_SECRET),
                intent_store=store,
                freshness_port=FakeFreshnessStatePort(_binding()),
                coordination_message="Synthetic demo surveillance review; draft only.",
            ),
            context_builder=_FixedContextBuilder(),
        )
        http_adapter.hero_composition = HeroComposition(hero_runtime=runtime)
        command = {
            "contract_version": "ngabo-event-investigation-v1",
            "incident_id": INCIDENT.value,
            "incident_version": VERSION.value,
            "source_watermark": WATERMARK.value,
            "event_id": "evt-dup-001",
            "correlation_id": "corr-dup-001",
        }
        envelope = {
            "message": {
                "data": _b64.b64encode(json.dumps(command).encode("utf-8")).decode("utf-8"),
                "messageId": "m-dup",
            },
            "subscription": "projects/ngabo-amr-2026/subscriptions/hero",
        }
        client = TestClient(http_adapter.app)
        first = client.post("/surveillance", json=envelope)
        assert first.status_code == 503
        second = client.post("/surveillance", json=envelope)
        assert second.status_code == 200
        assert second.json()["outcome"] == "HERO_COMPLETED"
        assert store.state_transitions.count(IntentState.RETRYABLE) == 1
