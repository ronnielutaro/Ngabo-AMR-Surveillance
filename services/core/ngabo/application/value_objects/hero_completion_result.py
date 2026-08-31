"""Typed result of one deadline hero run (#176)."""

from __future__ import annotations

from dataclasses import dataclass, field

from ngabo.application.enums.hero_error_code import HeroErrorCode
from ngabo.application.enums.hero_outcome import HeroOutcome
from ngabo.application.value_objects.effect_delivery import EffectDelivery
from ngabo.application.value_objects.hero_action_decision import HeroActionDecision
from ngabo.application.value_objects.hero_action_intent import HeroActionIntent
from ngabo.application.value_objects.hero_observability_event import (
    HeroObservabilityEvent,
)
from ngabo.application.value_objects.hero_verification import HeroVerificationResult


@dataclass(frozen=True)
class HeroCompletionResult:
    """Aggregate outcome of the deadline hero gate chain."""

    outcome: HeroOutcome
    verification: HeroVerificationResult | None
    decision: HeroActionDecision | None
    intent: HeroActionIntent | None
    delivery: EffectDelivery | None
    ack_verified: bool
    events: tuple[HeroObservabilityEvent, ...] = ()
    error_code: HeroErrorCode | None = None
    execution_id: str | None = None
    zero_human: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, HeroOutcome):
            raise ValueError("outcome must be a HeroOutcome")
        if self.error_code is not None and not isinstance(
            self.error_code, HeroErrorCode
        ):
            raise ValueError("error_code must be a HeroErrorCode or None")
        if self.outcome.is_success:
            if self.error_code is not None:
                raise ValueError("HERO_COMPLETED cannot carry an error_code")
            if self.delivery is None or not self.ack_verified:
                raise ValueError("HERO_COMPLETED requires a verified delivery+ack")
        self.zero_human.setdefault("manual_prompt_count_to_start", 0)
        self.zero_human.setdefault("human_intervention_count", 0)
        self.zero_human.setdefault("clarification_count", 0)
        self.zero_human.setdefault("approval_click_count", 0)
        self.zero_human.setdefault("manual_continuation_count", 0)
        self.zero_human.setdefault("human_active_steps", 0)
