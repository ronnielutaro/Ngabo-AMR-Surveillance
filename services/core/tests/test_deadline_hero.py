"""Focused tests for the deadline hero verification -> A1 -> delivery -> ack slice."""

from __future__ import annotations

from typing import cast

import pytest

from ngabo.application.enums.hero_error_code import HeroErrorCode
from ngabo.application.enums.hero_outcome import HeroOutcome
from ngabo.application.services.incident_package_codec import parse_incident_package
from ngabo.application.use_cases.check_hero_freshness import CheckHeroFreshness
from ngabo.application.use_cases.hero_action_policy import HeroActionPolicy
from ngabo.application.use_cases.hero_orchestrator import HeroOrchestrator
from ngabo.application.use_cases.verify_hero_ack import VerifyHeroAck
from ngabo.application.use_cases.verify_hero_package import VerifyHeroPackage
from ngabo.application.value_objects.effect_delivery import EffectDelivery
from ngabo.application.value_objects.hero_action_intent import HeroActionIntent
from ngabo.application.value_objects.hero_completion_result import HeroCompletionResult
from ngabo.application.value_objects.hero_payload import HeroCoordinationPayload
from ngabo.application.value_objects.hero_support_context import HeroSupportContext
from ngabo.application.value_objects.hero_verification import HeroVerificationResult
from ngabo.application.value_objects.incident_package import IncidentPackageCandidate
from ngabo.domain.enums.action_class import ActionClass
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.source_watermark import SourceWatermark
from ngabo.infrastructure.effect.fake_effect_port import FakeEffectPort

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
                "statement": "ISO-031 and ISO-034 were collected in the synthetic ward.",
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
                "statement": "The two isolates share a high resistance phenotype.",
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
                "statement": "WHO-AMR-001 guidance addresses surveillance interpretation.",
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


def _context(**overrides: object) -> HeroSupportContext:
    def _frozen(key: str, default: frozenset[str]) -> frozenset[str]:
        value = overrides.get(key, default)
        return value if isinstance(value, frozenset) else default

    incident_id = cast(IncidentId, overrides.get("incident_id", INCIDENT))
    incident_version = cast(
        IncidentVersion, overrides.get("incident_version", VERSION)
    )
    source_watermark = cast(
        SourceWatermark, overrides.get("source_watermark", WATERMARK)
    )
    execution_id = cast(str, overrides.get("execution_id", EXECUTION_ID))
    policy_config_version = cast(
        str, overrides.get("policy_config_version", "v1")
    )
    return HeroSupportContext(
        incident_id=incident_id,
        incident_version=incident_version,
        source_watermark=source_watermark,
        execution_id=execution_id,
        policy_config_version=policy_config_version,
        record_ids=_frozen("record_ids", frozenset({"ISO-031", "ISO-034"})),
        finding_ids=_frozen("finding_ids", frozenset({"psim-abc123"})),
        evidence_source_ids=_frozen(
            "evidence_source_ids", frozenset({"WHO-AMR-001"})
        ),
        evidence_reference_ids=_frozen(
            "evidence_reference_ids",
            frozenset({"WHO-AMR-001::ipc-principle-01"}),
        ),
        authorized_target_ids=_frozen(
            "authorized_target_ids", frozenset({"demo-receiver-01"})
        ),
    )


def _orchestrator(
    *,
    ack_secret: str = ACK_SECRET,
    port: FakeEffectPort | None = None,
) -> tuple[HeroOrchestrator, FakeEffectPort]:
    fake: FakeEffectPort = (
        port if port is not None else FakeEffectPort(ack_secret=ack_secret)
    )
    orchestrator = HeroOrchestrator(
        verifier=VerifyHeroPackage(),
        policy=HeroActionPolicy(freshness=CheckHeroFreshness()),
        effect_port=fake,
        ack_verifier=VerifyHeroAck(ack_secret=ack_secret),
        coordination_message="Synthetic demo surveillance review; draft only.",
    )
    return orchestrator, fake


class TestVerification:
    def test_valid_package_verifies(self) -> None:
        result = VerifyHeroPackage().verify(_package(), _context())
        assert result.verified is True
        assert result.package is not None
        assert result.claim_count == 4

    def test_fabricated_record_ref_blocks(self) -> None:
        # Mutate first OBSERVED_FACT record id.
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[0]["supporting_record_refs"] = [
            {
                "record_id": "ISO-999",
                "field_path": "organism_code",
                "expected_value": "kle",
            }
        ]
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _context())
        assert result.verified is False
        assert any("record reference" in e.detail for e in result.errors)

    def test_fabricated_finding_ref_blocks(self) -> None:
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[1]["supporting_finding_refs"] = [
            {
                "finding_id": "finding-fake",
                "policy_version": "v1",
                "input_refs": ["ISO-031", "ISO-034"],
                "output_value": "similarity=1.0000",
            }
        ]
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _context())
        assert result.verified is False
        assert any("finding reference" in e.detail for e in result.errors)

    def test_fabricated_evidence_ref_blocks(self) -> None:
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[2]["supporting_evidence_refs"] = [
            {
                "source_id": "EVIL-SRC-999",
                "chunk_id": "EVIL-SRC-999::x",
                "provenance": "ngabo-approved-evidence-v1",
                "support": "supports",
            }
        ]
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _context())
        assert result.verified is False
        assert any("evidence" in e.detail for e in result.errors)

    def test_wrong_incident_or_version_or_watermark_blocks(self) -> None:
        for context in (
            _context(incident_id=IncidentId("INC-999")),
            _context(incident_version=IncidentVersion(2)),
            _context(source_watermark=SourceWatermark("other")),
        ):
            p = _package()
            result = VerifyHeroPackage().verify(p, context)
            assert result.verified is False

    def test_forbidden_authority_claim_blocks(self) -> None:
        mutated = _package_primitive()
        claims = cast("list[dict[str, object]]", mutated["claims"])
        claims[1]["statement"] = "This run declares OUTBREAK_CONFIRMED and is verified."
        parse = parse_incident_package(mutated)
        assert parse.ok and parse.package is not None
        result = VerifyHeroPackage().verify(parse.package, _context())
        assert result.verified is False
        assert any("authority" in e.detail for e in result.errors)


class TestPolicy:
    def test_verified_and_current_model_returns_a1(self) -> None:
        verification = VerifyHeroPackage().verify(_package(), _context())
        decision = HeroActionPolicy(freshness=CheckHeroFreshness()).decide(
            verification, _context()
        )
        assert decision.auto_execute_a1 is True
        assert decision.action_class is ActionClass.SAFE_EXTERNAL_COORDINATION
        assert decision.authorized_target_id == "demo-receiver-01"

    def test_unverified_package_blocks(self) -> None:
        unverified = HeroVerificationResult(verified=False, package=None)
        decision = HeroActionPolicy().decide(unverified, _context())
        assert decision.auto_execute_a1 is False
        assert decision.error_code is HeroErrorCode.UNVERIFIED_PACKAGE

    def test_stale_version_blocks(self) -> None:
        verification = VerifyHeroPackage().verify(_package(), _context())
        decision = HeroActionPolicy().decide(
            verification, _context(incident_version=IncidentVersion(9))
        )
        assert decision.auto_execute_a1 is False
        assert decision.error_code is HeroErrorCode.STALE_VERSION_BINDING

    def test_unauthorized_target_blocks(self) -> None:
        verification = VerifyHeroPackage().verify(_package(), _context())
        decision = HeroActionPolicy().decide(
            verification, _context(authorized_target_ids=frozenset())
        )
        assert decision.auto_execute_a1 is False
        assert decision.error_code is HeroErrorCode.UNAUTHORIZED_TARGET

    def test_model_cannot_authorize_a2_or_a3(self) -> None:
        # The hero intent contract only permits A1; an A2/A3 request cannot be
        # represented, and the policy always produces the canonical A1 verdict.
        with pytest.raises(ValueError):
            HeroActionIntent(
                action_id="ACT-1",
                incident_id=INCIDENT,
                incident_version=VERSION,
                source_watermark=WATERMARK,
                verified_package_id="PKG-1",
                action_class=ActionClass.REAL_OPERATIONAL_ESCALATION,
                authorized_target_id="demo-receiver-01",
                payload_hash="0" * 64,
                idempotency_key="idem-1",
            )


class TestAck:
    def test_signed_correlated_ack_passes(self) -> None:
        orchestrator, fake = _orchestrator()
        result = orchestrator.run(_package(), _context())
        assert result.outcome is HeroOutcome.HERO_COMPLETED
        assert result.ack_verified is True
        assert fake.calls and fake.calls[0].synthetic is True

    def test_wrong_action_id_blocks(self) -> None:
        result = _run_with_mutated_delivery(action_id="ACT-X")
        assert result.outcome is HeroOutcome.FAILED
        assert result.error_code is HeroErrorCode.ACK_CORRELATION_MISMATCH

    def test_wrong_payload_hash_blocks(self) -> None:
        result = _run_with_mutated_delivery(payload_hash="1" * 64)
        assert result.outcome is HeroOutcome.FAILED

    def test_invalid_signature_blocks(self) -> None:
        # Delivery is signed with "signer-secret" but verified with a different
        # secret -> signature mismatch must fail closed.
        orchestrator = HeroOrchestrator(
            verifier=VerifyHeroPackage(),
            policy=HeroActionPolicy(),
            effect_port=FakeEffectPort(ack_secret="signer-secret"),
            ack_verifier=VerifyHeroAck(ack_secret="verifier-secret"),
            coordination_message="draft only",
        )
        result = orchestrator.run(_package(), _context())
        assert result.outcome is HeroOutcome.FAILED
        assert result.error_code is HeroErrorCode.ACK_SIGNATURE_INVALID


def _run_with_mutated_delivery(
    action_id: str | None = None,
    payload_hash: str | None = None,
) -> HeroCompletionResult:
    """Run the hero, then mutate the delivery before ack verification."""

    class _Port:
        def __init__(self) -> None:
            self.calls: list[object] = []

        def deliver(
            self,
            intent: HeroActionIntent,
            payload: HeroCoordinationPayload,
        ) -> EffectDelivery:
            fake = FakeEffectPort(ack_secret=ACK_SECRET)
            d = fake.deliver(intent, payload)
            self.calls.append(intent)
            import dataclasses

            return dataclasses.replace(
                d,
                action_id=action_id if action_id is not None else d.action_id,
                payload_hash=payload_hash if payload_hash is not None else d.payload_hash,
            )

    port = _Port()
    orch = HeroOrchestrator(
        verifier=VerifyHeroPackage(),
        policy=HeroActionPolicy(freshness=CheckHeroFreshness()),
        effect_port=port,
        ack_verifier=VerifyHeroAck(ack_secret=ACK_SECRET),
        coordination_message="draft only",
    )
    return orch.run(_package(), _context())


class TestHero:
    def test_no_downstream_action_on_verification_failure(self) -> None:
        port = FakeEffectPort(ack_secret=ACK_SECRET)
        orchestrator, _ = _orchestrator(port=port)
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
        result = orchestrator.run(parse.package, _context())
        assert result.outcome is HeroOutcome.BLOCKED
        assert port.calls == []
        assert result.error_code is HeroErrorCode.UNVERIFIED_PACKAGE

    def test_hero_completed_impossible_before_ack(self) -> None:
        result = _run_with_mutated_delivery(action_id="ACT-X")
        assert result.outcome is HeroOutcome.FAILED
        assert result.ack_verified is False

    def test_zero_human_counters_remain_zero(self) -> None:
        orchestrator, _ = _orchestrator()
        result = orchestrator.run(_package(), _context())
        assert result.outcome is HeroOutcome.HERO_COMPLETED
        for key, value in result.zero_human.items():
            assert value == 0, f"{key} is not zero"

