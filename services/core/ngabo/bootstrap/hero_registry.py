"""Deployment hero adapter registry (NGABO_HERO_ADAPTER_REGISTRY).

Builds the real #54/#55/#56/#176 adapter graph from environment configuration:
Firestore canonical repository, approved evidence (local corpus), the pinned
Gemini model, a Firestore ActionIntent store, a SignedReceiverClient to the demo
receiver, a Firestore freshness port, and the configured authorized target.
"""

from __future__ import annotations

import os
from pathlib import Path

from ngabo.application.use_cases.assess_material_missingness import (
    AssessMaterialMissingness,
)
from ngabo.application.use_cases.check_hero_freshness import CheckHeroFreshness
from ngabo.application.use_cases.compare_resistance_profiles import (
    CompareResistanceProfiles,
)
from ngabo.application.use_cases.get_baseline_summary import GetBaselineSummary
from ngabo.application.use_cases.get_investigation_context import GetInvestigationContext
from ngabo.application.use_cases.hero_action_policy import HeroActionPolicy
from ngabo.application.use_cases.hero_orchestrator import HeroOrchestrator
from ngabo.application.use_cases.verify_hero_ack import VerifyHeroAck
from ngabo.application.use_cases.verify_hero_package import VerifyHeroPackage
from ngabo.application.value_objects.investigation_execution import (
    InvestigationRuntimeBudget,
)
from ngabo.application.value_objects.synthesis_support_manifest import (
    EvidenceCorpusMetadata,
)
from ngabo.infrastructure.adk.investigation_runtime import (
    DEFAULT_APP_NAME,
    EventInvestigationRuntime,
)
from ngabo.infrastructure.adk.synthesis_runtime import (
    BoundedSynthesisRuntime,
    SynthesisBudget,
)
from ngabo.infrastructure.adk.triage_runtime import BoundedTriageRuntime, TriageBudget
from ngabo.infrastructure.connect.firestore_freshness_port import (
    FirestoreFreshnessStatePort,
)
from ngabo.infrastructure.connect.firestore_incident_repository import (
    FirestoreInvestigationContextRepository,
)
from ngabo.infrastructure.effect.firestore_action_intent_store import (
    FirestoreActionIntentStore,
)
from ngabo.infrastructure.effect.signed_receiver_client import SignedReceiverClient
from ngabo.infrastructure.evidence.evidence_manifest_loader import (
    load_evidence_corpus,
)
from ngabo.infrastructure.evidence.local_evidence_search import LocalEvidenceSearch

REPO_ROOT = Path(__file__).resolve().parents[3]


def build_registry() -> dict[str, object]:
    project = _required("NGABO_GCP_PROJECT")
    model = os.environ.get("NGABO_ADK_MODEL", "gemini-3.6-flash")
    receiver_url = os.environ.get("NGABO_RECEIVER_URL", "")
    ack_secret = os.environ.get("NGABO_ACK_SECRET", "")
    if not receiver_url or not ack_secret:
        raise RuntimeError("NGABO_RECEIVER_URL and NGABO_ACK_SECRET are required")

    repo = FirestoreInvestigationContextRepository(project=project)
    evidence_dir = os.environ.get("NGABO_EVIDENCE_DIR", "")
    if evidence_dir:
        sources = load_evidence_corpus(Path(evidence_dir))
    else:
        bundled = Path(REPO_ROOT) / "data" / "guidance"
        if bundled.exists():
            sources = load_evidence_corpus(bundled)
        else:
            raise RuntimeError(
                "hero deployment configuration missing approved evidence corpus; "
                "set NGABO_EVIDENCE_DIR to the bundled data/guidance directory"
            )
    evidence_search = LocalEvidenceSearch(sources)
    corpus_metadata = EvidenceCorpusMetadata(
        corpus_id="ngabo-approved-evidence-v1",
        manifest_version="1.0",
        corpus_digest=_corpus_digest(),
    )
    investigation_runtime = EventInvestigationRuntime(
        get_context=GetInvestigationContext(repo),
        compare_profiles=CompareResistanceProfiles(repo),
        get_baseline_summary=GetBaselineSummary(repo),
        assess_missingness=AssessMaterialMissingness(repo),
        budget=InvestigationRuntimeBudget(60.0, 0, 8, 1, 0),
        app_name=DEFAULT_APP_NAME,
    )
    triage_runtime = BoundedTriageRuntime(
        model=model,
        evidence_search=evidence_search,
        budget=TriageBudget(max_model_calls=1, max_runtime_seconds=60.0),
        app_name=DEFAULT_APP_NAME,
    )
    synthesis_runtime = BoundedSynthesisRuntime(
        model=model,
        corpus_metadata=corpus_metadata,
        budget=SynthesisBudget(max_model_calls=1, max_runtime_seconds=60.0),
        app_name=DEFAULT_APP_NAME,
    )
    intent_store = FirestoreActionIntentStore(project=project)
    freshness_port = FirestoreFreshnessStatePort(repo)
    hero_orchestrator = HeroOrchestrator(
        verifier=VerifyHeroPackage(),
        policy=HeroActionPolicy(freshness=CheckHeroFreshness()),
        effect_port=SignedReceiverClient(receiver_url=receiver_url),
        ack_verifier=VerifyHeroAck(ack_secret=ack_secret),
        intent_store=intent_store,
        freshness_port=freshness_port,
        coordination_message=os.environ.get(
            "NGABO_COORDINATION_MESSAGE",
            "Synthetic demo surveillance review; draft only.",
        ),
    )
    return {
        "investigation_runtime": investigation_runtime,
        "triage_runtime": triage_runtime,
        "synthesis_runtime": synthesis_runtime,
        "hero_orchestrator": hero_orchestrator,
    }


REGISTRY: dict[str, object] = {}


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"hero deployment configuration missing: {name}")
    return value


def _corpus_digest() -> str:
    return "575a8552d35eb1ab6b2bb8ffa60f020bf643f4358fa28c50865fbe79e9085aeb"
