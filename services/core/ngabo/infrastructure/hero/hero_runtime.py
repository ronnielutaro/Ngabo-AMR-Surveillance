"""Deployed hero composition root: wires #54/#55/#56 into the #176 hero tail (#176).

This is the ONLY place the full canonical hero is composed for the deployed event
workflow. It is orchestration-only: it invokes the existing deterministic ADK
runtimes and the framework-free hero gate chain, and it fails closed on every
stage. It owns no scientific policy and no model authority.
"""

from __future__ import annotations

from ngabo.application.enums.hero_error_code import HeroErrorCode
from ngabo.application.enums.hero_outcome import HeroOutcome
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
from ngabo.application.use_cases.hero_orchestrator import HeroOrchestrator
from ngabo.application.value_objects.hero_completion_result import HeroCompletionResult
from ngabo.application.value_objects.investigation_execution import (
    EventInvestigationCommand,
)


class HeroRuntime:
    """Deployed composition root for the canonical hero."""

    def __init__(
        self,
        *,
        investigation_runtime: object,
        triage_runtime: object,
        synthesis_runtime: object,
        hero_orchestrator: HeroOrchestrator,
        context_builder: HeroSupportContextBuilder | None = None,
    ) -> None:
        if not hasattr(investigation_runtime, "execute"):
            raise TypeError("investigation_runtime must expose execute(command)")
        if not hasattr(triage_runtime, "triage"):
            raise TypeError("triage_runtime must expose triage(result)")
        if not hasattr(synthesis_runtime, "synthesize"):
            raise TypeError("synthesis_runtime must expose synthesize(ready, triage)")
        if not isinstance(hero_orchestrator, HeroOrchestrator):
            raise TypeError("hero_orchestrator must be a HeroOrchestrator")
        self._investigation = investigation_runtime
        self._triage = triage_runtime
        self._synthesis = synthesis_runtime
        self._hero = hero_orchestrator
        self._context_builder = context_builder or HeroSupportContextBuilder()

    def execute(self, command: EventInvestigationCommand) -> HeroCompletionResult:
        """Run the full hero from one governed surveillance event."""
        execution_id = str(command.incident_id)
        ready = self._investigation.execute(command)
        if ready.outcome is not InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM:
            return self._terminal_blocked(
                "INVESTIGATION_STARTED",
                execution_id,
                HeroErrorCode.UNVERIFIED_PACKAGE,
            )
        triage = self._triage.triage(ready)
        if triage.outcome is not TriageOutcome.EVIDENCE_RETRIEVED:
            return self._terminal_blocked(
                "ADK_TRIAGE_COMPLETED",
                execution_id,
                HeroErrorCode.UNVERIFIED_PACKAGE,
            )
        synthesis = self._synthesis.synthesize(ready, triage)
        if (
            synthesis.outcome is not PackageCandidateOutcome.PACKAGE_CANDIDATE_GENERATED
            or synthesis.package is None
        ):
            return self._terminal_blocked(
                "ADK_SYNTHESIS_COMPLETED",
                execution_id,
                HeroErrorCode.UNVERIFIED_PACKAGE,
            )
        context = self._context_builder.build(ready, triage, synthesis)
        return self._hero.run(synthesis.package, context)

    def _terminal_blocked(
        self,
        stage: str,
        execution_id: str,
        error_code: HeroErrorCode,
    ) -> HeroCompletionResult:
        return HeroCompletionResult(
            outcome=HeroOutcome.BLOCKED,
            verification=None,
            decision=None,
            intent=None,
            delivery=None,
            ack_verified=False,
            error_code=error_code,
            execution_id=execution_id,
            zero_human={
                "manual_prompt_count_to_start": 0,
                "human_intervention_count": 0,
                "clarification_count": 0,
                "approval_click_count": 0,
                "manual_continuation_count": 0,
                "human_active_steps": 0,
            },
        )
