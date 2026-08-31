"""Deployed hero HTTP bootstrap: construct + install the composition before serving (#176).

This is the production ``ngabo-http`` entry point. It builds the real hero
composition from deployment configuration (or injected adapters) and installs it
into the FastAPI adapter BEFORE it serves any ``/surveillance`` request. It fails
startup clearly if required hero deployment configuration is absent, rather than
serving a route that is guaranteed to return HTTP 500.
"""

from __future__ import annotations

from ngabo.application.services.hero_support_context_builder import (
    HeroSupportContextBuilder,
)
from ngabo.application.use_cases.hero_orchestrator import HeroOrchestrator
from ngabo.bootstrap.hero import HeroComposition
from ngabo.infrastructure.hero.hero_runtime import HeroRuntime


def build_hero_composition(
    *,
    investigation_runtime: object,
    triage_runtime: object,
    synthesis_runtime: object,
    hero_orchestrator: HeroOrchestrator,
    context_builder: HeroSupportContextBuilder | None = None,
) -> HeroComposition:
    """Build the deployed hero composition (deploy injects the real adapters).

    Production callers must supply the real EventInvestigationRuntime (#54),
    BoundedTriageRuntime (#55), BoundedSynthesisRuntime (#56), HeroOrchestrator
    (#176), and the injected FreshnessStatePort / FirestoreActionIntentStore /
    SignedReceiverClient bound inside the orchestrator via its constructor.
    """
    if investigation_runtime is None:
        raise RuntimeError("hero deployment configuration missing: investigation_runtime")
    if triage_runtime is None:
        raise RuntimeError("hero deployment configuration missing: triage_runtime")
    if synthesis_runtime is None:
        raise RuntimeError("hero deployment configuration missing: synthesis_runtime")
    if hero_orchestrator is None:
        raise RuntimeError("hero deployment configuration missing: hero_orchestrator")
    runtime = HeroRuntime(
        investigation_runtime=investigation_runtime,
        triage_runtime=triage_runtime,
        synthesis_runtime=synthesis_runtime,
        hero_orchestrator=hero_orchestrator,
        context_builder=context_builder,
    )
    return HeroComposition(hero_runtime=runtime)


def main() -> None:
    """Production ``ngabo-http`` entry point: wire the hero and serve."""
    from ngabo.interfaces import http as http_adapter

    if http_adapter.hero_composition is None:
        raise RuntimeError(
            "hero composition not configured: the deployment must call "
            "bootstrap.hero_serve.build_hero_composition(...) with the real "
            "adapter graph (EventInvestigationRuntime, BoundedTriageRuntime, "
            "BoundedSynthesisRuntime, HeroOrchestrator, FreshnessStatePort, "
            "FirestoreActionIntentStore, SignedReceiverClient) and configure it "
            "on the HTTP adapter before serving /surveillance"
        )
    http_adapter.serve()
