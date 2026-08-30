"""Live capability entry point for the Issue #49 ADK/Gemini spike.

This runs the real ADK ``Workflow`` against an actual Gemini model and prints
the redacted ``SpikeRunResult`` as JSON. It is a one-off, governed capability
invocation path — NOT a public FastAPI endpoint. It is the executable proof
that a backend event can drive the real ADK agent to structured output, then
through deterministic verification.

Credential handling: it reads ``GEMINI_API_KEY`` (a build/secret-provided
value) and exposes it to ADK's ``google.genai`` client via ``GOOGLE_API_KEY``
without ever printing either. In Cloud Run, prefer WIF; this module never
persists or logs secret material.
"""

from __future__ import annotations

import json
import os

from ngabo.application.services.spike_proof_verifier import VerificationContext
from ngabo.infrastructure.adk.spike_adapter import SpikeRunResult, run_spike

DEFAULT_MODEL: str = "gemini-3.6-flash"


def _redacted_result(result: SpikeRunResult) -> dict[str, object]:
    """Explicit, secret-free JSON-safe representation of a ``SpikeRunResult``."""
    claim = result.claim
    verification = result.verification
    return {
        "status": result.status.value,
        "repair_attempts": result.repair_attempts,
        "session_id": result.session_id,
        "invocation_id": result.invocation_id,
        "agent_path": result.agent_path,
        "claim": {
            "claim_id": claim.claim_id,
            "claim_type": claim.claim_type.value,
            "statement": claim.statement,
            "supporting_record_ids": list(claim.supporting_record_ids),
            "supporting_finding_ids": list(claim.supporting_finding_ids),
            "supporting_source_ids": list(claim.supporting_source_ids),
            "requested_action_class": claim.requested_action_class.value
            if claim.requested_action_class is not None
            else None,
            "confidence_label": claim.confidence_label,
        }
        if claim is not None
        else None,
        "verification": {
            "valid": verification.valid if verification is not None else False,
            "errors": [
                {
                    "code": error.code.value,
                    "reference": error.reference,
                    "field": error.field,
                }
                for error in (verification.errors if verification is not None else ())
            ],
        },
    }


def main() -> None:
    """Run the live capability spike and print a redacted JSON result."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY is required for the live ADK capability proof")
    # google.genai's default client reads GOOGLE_API_KEY; ADK's GoogleLlm uses it.
    os.environ.setdefault("GOOGLE_API_KEY", api_key)

    model = os.environ.get("NGABO_ADK_MODEL", DEFAULT_MODEL)
    context = VerificationContext(
        known_record_ids=frozenset({"rec-01"}),
        known_finding_ids=frozenset({"finding-amr-a", "finding-amr-b"}),
        known_source_ids=frozenset({"src-01"}),
        known_claim_ids=frozenset({"claim-initial"}),
    )
    result = run_spike(
        {
            "synthetic_incident": True,
            "input": "report a suspected clonal cluster from the synthetic data",
        },
        model=model,
        context=context,
        max_repair=1,
    )
    payload = _redacted_result(result)
    payload["model"] = model
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
