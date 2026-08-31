"""Deterministic deadline-hero gate chain orchestration (#176).

This composes the outputs of the real #54/#55/#56 stages into the canonical
hero tail:

    candidate + support context
      -> VerifyHeroPackage       (deterministic, all-or-nothing)
      -> HeroActionPolicy        (deterministic A1, freshness + authorized target)
      -> immutable HeroActionIntent + safe synthetic payload
      -> EffectPort.deliver      (real network boundary; model never supplies it)
      -> VerifyHeroAck           (correlation + HMAC signature)
      -> HERO_COMPLETED

The model never creates HERO_COMPLETED. Every failed stage emits sanitized
observability and ends in BLOCKED/FAILED.
"""

from __future__ import annotations

import hashlib

from ngabo.application.enums.hero_error_code import HeroErrorCode
from ngabo.application.enums.hero_outcome import HeroOutcome
from ngabo.application.ports.effect_port import EffectPort
from ngabo.application.use_cases.hero_action_policy import HeroActionPolicy
from ngabo.application.use_cases.verify_hero_ack import VerifyHeroAck
from ngabo.application.use_cases.verify_hero_package import VerifyHeroPackage
from ngabo.application.value_objects.effect_delivery import EffectDelivery
from ngabo.application.value_objects.hero_action_decision import HeroActionDecision
from ngabo.application.value_objects.hero_action_intent import HeroActionIntent
from ngabo.application.value_objects.hero_completion_result import HeroCompletionResult
from ngabo.application.value_objects.hero_observability_event import (
    HeroObservabilityEvent,
)
from ngabo.application.value_objects.hero_payload import HeroCoordinationPayload
from ngabo.application.value_objects.hero_support_context import HeroSupportContext
from ngabo.application.value_objects.hero_verification import HeroVerificationResult
from ngabo.application.value_objects.incident_package import IncidentPackageCandidate
from ngabo.domain.enums.action_class import ActionClass


def _hex_digest(*parts: str, length: int = 16) -> str:
    material = "|".join(parts).encode("utf-8")
    return hashlib.sha256(material).hexdigest()[:length]


class HeroOrchestrator:
    """Framework-free composition root for the deadline hero tail."""

    def __init__(
        self,
        *,
        verifier: VerifyHeroPackage,
        policy: HeroActionPolicy,
        effect_port: EffectPort,
        ack_verifier: VerifyHeroAck,
        coordination_message: str,
    ) -> None:
        if not isinstance(verifier, VerifyHeroPackage):
            raise TypeError("verifier must be a VerifyHeroPackage")
        if not isinstance(policy, HeroActionPolicy):
            raise TypeError("policy must be a HeroActionPolicy")
        if not hasattr(effect_port, "deliver"):
            raise TypeError("effect_port must satisfy EffectPort")
        if not isinstance(ack_verifier, VerifyHeroAck):
            raise TypeError("ack_verifier must be a VerifyHeroAck")
        if not isinstance(coordination_message, str) or not coordination_message.strip():
            raise ValueError("coordination_message must be non-blank safe text")
        self._verifier = verifier
        self._policy = policy
        self._effect_port = effect_port
        self._ack_verifier = ack_verifier
        self._coordination_message = coordination_message.strip()

    def run(
        self,
        package: IncidentPackageCandidate,
        context: HeroSupportContext,
    ) -> HeroCompletionResult:
        events: list[HeroObservabilityEvent] = [
            self._event(
                "PACKAGE_CANDIDATE_GENERATED",
                context,
                package_id=package.package_id.value,
            )
        ]
        verification = self._verifier.verify(package, context)
        events.append(
            self._event(
                "DETERMINISTIC_VERIFICATION",
                context,
                package_id=package.package_id.value,
                verification_outcome=verification.verified,
                claims_checked=verification.claim_count,
            )
        )
        if not verification.verified:
            return self._terminal(
                HeroOutcome.BLOCKED,
                events,
                context,
                error_code=HeroErrorCode.UNVERIFIED_PACKAGE,
                verification=verification,
            )
        decision = self._policy.decide(verification, context)
        events.append(
            self._event(
                "A1_POLICY",
                context,
                package_id=package.package_id.value,
                auto_execute_a1=decision.auto_execute_a1,
                action_class=decision.action_class.value,
            )
        )
        if not decision.auto_execute_a1 or decision.authorized_target_id is None:
            return self._terminal(
                HeroOutcome.BLOCKED,
                events,
                context,
                error_code=decision.error_code or HeroErrorCode.POLICY_BLOCKED,
                verification=verification,
                decision=decision,
            )

        payload = HeroCoordinationPayload(
            incident_id=context.incident_id.value,
            verified_package_id=package.package_id.value,
            action_class=ActionClass.SAFE_EXTERNAL_COORDINATION.value,
            message=self._coordination_message,
            synthetic=True,
        )
        payload_hash = payload.payload_hash()
        intent = HeroActionIntent(
            action_id="ACT-" + _hex_digest("act", context.execution_id, package.package_id.value),
            incident_id=context.incident_id,
            incident_version=context.incident_version,
            source_watermark=context.source_watermark,
            verified_package_id=package.package_id.value,
            action_class=ActionClass.SAFE_EXTERNAL_COORDINATION,
            authorized_target_id=decision.authorized_target_id,
            payload_hash=payload_hash,
            idempotency_key="idem-" + _hex_digest(
                "idem",
                context.execution_id,
                package.package_id.value,
                decision.authorized_target_id,
            ),
            synthetic=True,
        )
        events.append(
            self._event(
                "ACTION_INTENT_CREATED",
                context,
                action_id=intent.action_id,
                authorized_target_id=intent.authorized_target_id,
                payload_hash=payload_hash,
                idempotency_key=intent.idempotency_key,
            )
        )
        try:
            delivery = self._effect_port.deliver(intent, payload)
        except Exception:
            return self._terminal(
                HeroOutcome.FAILED,
                events,
                context,
                error_code=HeroErrorCode.DELIVERY_FAILED,
                verification=verification,
                decision=decision,
                intent=intent,
            )
        events.append(
            self._event(
                "EXTERNAL_DELIVERY_SENT",
                context,
                action_id=intent.action_id,
                delivery_id=delivery.delivery_id,
                payload_hash=payload_hash,
            )
        )
        ack_ok, ack_error, ack_detail = self._ack_verifier.verify(intent, delivery)
        events.append(
            self._event(
                "MACHINE_ACK",
                context,
                action_id=intent.action_id,
                delivery_id=delivery.delivery_id,
                ack_id=delivery.ack_id,
                verified=ack_ok,
                detail=ack_detail,
            )
        )
        if not ack_ok:
            return self._terminal(
                HeroOutcome.FAILED,
                events,
                context,
                error_code=ack_error or HeroErrorCode.ACK_INVALID,
                verification=verification,
                decision=decision,
                intent=intent,
                delivery=delivery,
            )
        events.append(
            self._event(
                "HERO_COMPLETED",
                context,
                package_id=package.package_id.value,
                action_id=intent.action_id,
                delivery_id=delivery.delivery_id,
                ack_id=delivery.ack_id,
                zero_human_intervention=0,
            )
        )
        return HeroCompletionResult(
            outcome=HeroOutcome.HERO_COMPLETED,
            verification=verification,
            decision=decision,
            intent=intent,
            delivery=delivery,
            ack_verified=True,
            events=tuple(events),
            error_code=None,
            execution_id=context.execution_id,
            zero_human={
                "manual_prompt_count_to_start": 0,
                "human_intervention_count": 0,
                "clarification_count": 0,
                "approval_click_count": 0,
                "manual_continuation_count": 0,
                "human_active_steps": 0,
            },
        )

    def _terminal(
        self,
        outcome: HeroOutcome,
        events: list[HeroObservabilityEvent],
        context: HeroSupportContext,
        *,
        error_code: HeroErrorCode,
        verification: HeroVerificationResult | None = None,
        decision: HeroActionDecision | None = None,
        intent: HeroActionIntent | None = None,
        delivery: EffectDelivery | None = None,
    ) -> HeroCompletionResult:
        events.append(
            self._event(
                "HERO_TERMINAL",
                context,
                outcome=outcome.value,
                error_code=error_code.value,
            )
        )
        return HeroCompletionResult(
            outcome=outcome,
            verification=verification,
            decision=decision,
            intent=intent,
            delivery=delivery,
            ack_verified=False,
            events=tuple(events),
            error_code=error_code,
            execution_id=context.execution_id,
            zero_human={
                "manual_prompt_count_to_start": 0,
                "human_intervention_count": 0,
                "clarification_count": 0,
                "approval_click_count": 0,
                "manual_continuation_count": 0,
                "human_active_steps": 0,
            },
        )

    def _event(
        self,
        event_name: str,
        context: HeroSupportContext,
        **fields: object,
    ) -> HeroObservabilityEvent:
        return HeroObservabilityEvent(
            event_name=event_name,
            incident_id=context.incident_id.value,
            execution_id=context.execution_id,
            stage_fields=dict(fields),
        )
