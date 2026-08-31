"""Minimum deterministic A1 action policy for the deadline hero (#176).

For the canonical synthetic hero exactly ONE safe autonomous external action is
authorized. The deterministic policy requires:

- a VERIFIED hero package (never the raw candidate);
- no material verification blockers;
- a current freshness/version binding;
- an explicitly synthetic/demo coordination payload;
- one configured, authorized test/sandbox target;
- safe wording (no forbidden authority semantics).

Gemini may suggest an ACTION_JUSTIFICATION; it may NOT classify A1, choose the
target URL, authorize, override a block, execute, or mark delivery successful.
Only deterministic code decides AUTO_EXECUTE_A1 versus POLICY_BLOCKED. A2/A3
always block.
"""

from __future__ import annotations

from ngabo.application.enums.hero_error_code import HeroErrorCode
from ngabo.application.use_cases.check_hero_freshness import CheckHeroFreshness
from ngabo.application.value_objects.hero_action_decision import HeroActionDecision
from ngabo.application.value_objects.hero_support_context import HeroSupportContext
from ngabo.application.value_objects.hero_verification import HeroVerificationResult
from ngabo.domain.enums.action_class import ActionClass


class HeroActionPolicy:
    """Deterministic A1 authorization gate for the deadline hero."""

    def __init__(
        self,
        freshness: CheckHeroFreshness | None = None,
    ) -> None:
        self._freshness = freshness or CheckHeroFreshness()

    def decide(
        self,
        verification: HeroVerificationResult,
        context: HeroSupportContext,
    ) -> HeroActionDecision:
        if not verification.verified or verification.package is None:
            return HeroActionDecision(
                auto_execute_a1=False,
                action_class=ActionClass.SAFE_EXTERNAL_COORDINATION,
                authorized_target_id=None,
                reason="unverified package cannot reach A1 policy",
                error_code=HeroErrorCode.UNVERIFIED_PACKAGE,
            )
        if not context.authorized_target_ids:
            return HeroActionDecision(
                auto_execute_a1=False,
                action_class=ActionClass.SAFE_EXTERNAL_COORDINATION,
                authorized_target_id=None,
                reason="no configured authorized test/sandbox target",
                error_code=HeroErrorCode.UNAUTHORIZED_TARGET,
            )
        fresh, code, detail = self._freshness.check(
            verification.package, context
        )
        if not fresh:
            return HeroActionDecision(
                auto_execute_a1=False,
                action_class=ActionClass.SAFE_EXTERNAL_COORDINATION,
                authorized_target_id=None,
                reason=detail,
                error_code=code or HeroErrorCode.POLICY_BLOCKED,
            )
        # The test/sandbox target is configured (never model-visible). Choose the
        # single deterministic authorized target for this slice.
        target_id = sorted(context.authorized_target_ids)[0]
        return HeroActionDecision(
            auto_execute_a1=True,
            action_class=ActionClass.SAFE_EXTERNAL_COORDINATION,
            authorized_target_id=target_id,
            reason="verified, fresh, authorized synthetic A1 demo action",
        )
