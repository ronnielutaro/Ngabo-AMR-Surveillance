"""Ngabo Connect deadline E2E smoke: clean -> Firestore -> signal -> hero -> signed ACK.

Run with a GCP-authenticated shell that has GEMINI_API_KEY:
  python scripts/deadline_demo_e2e_smoke.py

This exercises the REAL pipeline: real Firestore (ngabo DB), real Gemini
(google-adk/gemini-3.6-flash), and the real deployed ngabo-demo-receiver.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "core"))

# Firestore uses the gcloud user access token (local smoke). Deploy uses ADC/WIF.
from google.oauth2.credentials import Credentials  # noqa: E402
from google.cloud import firestore  # noqa: E402


def _firestore_client() -> firestore.Client:
    gcloud = r"C:\Users\BENJAMIN\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
    token = subprocess.check_output(
        [gcloud, "auth", "print-access-token"], stderr=subprocess.DEVNULL
    ).decode().strip()
    return firestore.Client(
        project="ngabo-amr-2026",
        credentials=Credentials(token),
        database="ngabo",
    )


def main() -> int:
    os.environ.setdefault("NGABO_GCP_PROJECT", "ngabo-amr-2026")
    os.environ.setdefault("NGABO_FIRESTORE_DATABASE", "ngabo")
    os.environ.setdefault(
        "NGABO_RECEIVER_URL",
        "https://ngabo-demo-receiver-2zhvmdaotq-uc.a.run.app",
    )
    os.environ.setdefault("NGABO_ACK_SECRET", "demo-ack-secret-not-for-production")
    os.environ.setdefault("NGABO_EVIDENCE_DIR", str(ROOT / "data" / "guidance"))
    if os.environ.get("GEMINI_API_KEY"):
        os.environ.setdefault("GOOGLE_API_KEY", os.environ["GEMINI_API_KEY"])

    from ngabo.application.connect.processor import process_connect_csv
    from ngabo.bootstrap.hero_registry import build_registry
    from ngabo.application.services.hero_support_context_builder import (
        HeroSupportContextBuilder,
    )
    from ngabo.infrastructure.hero.hero_runtime import HeroRuntime
    from ngabo.bootstrap.hero import HeroComposition
    from ngabo.application.value_objects.investigation_execution import (
        EventInvestigationCommand,
    )
    from ngabo.infrastructure.connect.firestore_incident_repository import (
        persist_batch_events,
    )

    client = _firestore_client()
    registry = build_registry(client=client, database="ngabo")
    runtime = HeroRuntime(
        investigation_runtime=registry["investigation_runtime"],
        triage_runtime=registry["triage_runtime"],
        synthesis_runtime=registry["synthesis_runtime"],
        hero_orchestrator=registry["hero_orchestrator"],
        context_builder=HeroSupportContextBuilder(),
    )
    composition = HeroComposition(hero_runtime=runtime)

    def execute_hero(command: dict[str, object]) -> dict[str, object]:
        parsed = EventInvestigationCommand.from_primitive(command)
        result = composition.execute(parsed)
        out: dict[str, object] = {
            "outcome": result.outcome.value,
            "is_success": result.outcome.is_success,
            "ack_verified": result.ack_verified,
            "execution_id": result.execution_id,
            "action_id": result.intent.action_id if result.intent else None,
            "delivery_id": result.delivery.delivery_id if result.delivery else None,
            "ack_id": result.delivery.ack_id if result.delivery else None,
            "error_code": result.error_code.value if result.error_code else None,
        }
        verification = getattr(result, "verification", None)
        if verification is not None:
            out["verification_errors"] = [
                {"code": e.code.value, "detail": e.detail, "claim": e.claim_id}
                for e in getattr(verification, "errors", ())
            ]
            out["package_id"] = (
                verification.verified_package_id if verification.package else None
            )
        return out

    def persist(incident_id: str, isolates: list[object]) -> None:
        # Persist isolates + incident to Firestore via the repository.
        firestore_incident_repository = _incident_repo(client)
        isolate_ids = sorted(
            str(isolate.isolate_id)  # type: ignore[attr-defined]
            for isolate in isolates
        )
        firestore_incident_repository.persist_incident(
            incident_id=incident_id,
            incident_version=1,
            source_watermark="connect/synthetic-lab-gulu/whonet-demo/v1",
            window_end=__import__("datetime").date(2026, 8, 31),
            isolates=isolates,  # type: ignore[arg-type]
            profile_pair=(isolate_ids[0], isolate_ids[1]),
        )

    fixture = ROOT / "demo" / "connect" / "synthetic_gulu_surveillance_export.csv"
    raw = fixture.read_bytes()
    result = process_connect_csv(
        raw,
        lab_id="synthetic-lab-gulu",
        source_id="whonet-demo",
        window_end_iso="2026-08-31",
        execute_hero=execute_hero,
        persist_isolates=persist,
    )
    if result.get("signal_id"):
        persist_batch_events(project="ngabo-amr-2026", batch_id=str(result["signal_id"]), payload=result, client=client)
    print(json.dumps(result, indent=2, default=str))
    hero = result.get("hero_result")
    if hero and hero.get("outcome") == "HERO_COMPLETED":
        print("\nE2E_RESULT: HERO_COMPLETED")
        return 0
    print("\nE2E_RESULT: NOT_COMPLETED")
    return 1


def _incident_repo(client: firestore.Client) -> object:
    from ngabo.infrastructure.connect.firestore_incident_repository import (
        FirestoreInvestigationContextRepository,
    )

    return FirestoreInvestigationContextRepository(project="ngabo-amr-2026", client=client)


if __name__ == "__main__":
    raise SystemExit(main())
