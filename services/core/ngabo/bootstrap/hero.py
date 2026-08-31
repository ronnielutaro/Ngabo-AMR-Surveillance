"""Deployed hero composition root (#176).

``HeroComposition`` is the HTTP/bootstrap seam the deployed `ngabo-core` runtime
uses to convert one governed synthetic surveillance event into the full canonical
hero. It wraps the pre-built ``HeroRuntime`` and owns no scientific policy or model
authority. Real adapters (canonical repository, model, evidence search, Firestore
intent store, signed receiver, freshness port) are injected at deployment.
"""

from __future__ import annotations

from ngabo.application.value_objects.hero_completion_result import HeroCompletionResult
from ngabo.application.value_objects.investigation_execution import (
    EventInvestigationCommand,
)
from ngabo.infrastructure.hero.hero_runtime import HeroRuntime


class HeroComposition:
    """Deployed application seam that invokes ``HeroRuntime``."""

    def __init__(self, *, hero_runtime: HeroRuntime) -> None:
        if not isinstance(hero_runtime, HeroRuntime):
            raise TypeError("hero_runtime must be a HeroRuntime")
        self._runtime = hero_runtime

    def execute(self, command: EventInvestigationCommand) -> HeroCompletionResult:
        """Run the canonical hero from one governed surveillance event."""
        return self._runtime.execute(command)
