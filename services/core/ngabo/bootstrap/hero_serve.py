"""Deployed hero HTTP bootstrap: construct + install the composition before serving (#176).

This is the production ``ngabo-http`` entry point. It builds the real hero
composition from deployment configuration (or injected/factory-provided adapters)
and installs it into the FastAPI adapter BEFORE it serves any ``/surveillance``
request. It fails startup clearly if required hero deployment configuration is
absent, rather than serving a route that is guaranteed to return HTTP 500.
"""

from __future__ import annotations

import os

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
    hero_orchestrator: HeroOrchestrator | None,
    context_builder: HeroSupportContextBuilder | None = None,
) -> HeroComposition:
    """Build the deployed hero composition (deploy supplies the real adapters).

    The production caller must supply a real EventInvestigationRuntime (#54),
    BoundedTriageRuntime (#55), BoundedSynthesisRuntime (#56), and a
    HeroOrchestrator (#176) whose constructor already binds the FreshnessStatePort,
    FirestoreActionIntentStore, SignedReceiverClient, and configured target.
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


def build_hero_composition_from_config(
    *,
    deployment: dict[str, object] | None = None,
    adapters: dict[str, object] | None = None,
    context_builder: HeroSupportContextBuilder | None = None,
) -> HeroComposition:
    """Construct the real composition from deployment configuration.

    ``adapters`` maps the required runtime seams (investigation_runtime,
    triage_runtime, synthesis_runtime, hero_orchestrator) provided by the
    deployment (canonical repository adapter, model, evidence search, Firestore
    intent store, signed receiver, freshness port, configured target). ``deployment``
    carries the configured versions/bindings. Raises clearly if a required seam is
    absent so a misconfigured deploy fails at startup.
    """
    adapters = adapters or {}
    missing = [
        key
        for key in (
            "investigation_runtime",
            "triage_runtime",
            "synthesis_runtime",
            "hero_orchestrator",
        )
        if adapters.get(key) is None
    ]
    if missing:
        raise RuntimeError(
            "hero deployment configuration missing required runtime adapters: "
            f"{', '.join(missing)}"
        )
    return build_hero_composition(
        investigation_runtime=adapters["investigation_runtime"],
        triage_runtime=adapters["triage_runtime"],
        synthesis_runtime=adapters["synthesis_runtime"],
        hero_orchestrator=adapters["hero_orchestrator"],  # type: ignore[arg-type]
        context_builder=context_builder,
    )


def main() -> None:
    """Production ``ngabo-http`` entry point: wire the hero from config and serve."""
    from ngabo.interfaces import http as http_adapter

    composition = build_hero_composition_from_config(
        adapters=_registered_adapters()
    )
    http_adapter.configure_hero_composition(composition)
    http_adapter.serve()


def _registered_adapters() -> dict[str, object]:
    """Return the deployment-registered adapter graph, failing clearly if absent."""
    registry = os.environ.get("NGABO_HERO_ADAPTER_REGISTRY")
    if not registry:
        raise RuntimeError(
            "hero deployment configuration missing: NGABO_HERO_ADAPTER_REGISTRY "
            "(deploy must register the real #54/#55/#56/#176 adapter graph before "
            "serving /surveillance)"
        )
    # Deployment code registers the concrete adapters; this entry point treats a
    # missing registry as a fatal startup misconfiguration rather than serving a
    # route that is guaranteed to 500.
    raise RuntimeError(
        "hero deployment configuration is incomplete for an offline environment; "
        "the deployment image must supply NGABO_HERO_ADAPTER_REGISTRY"
    )
