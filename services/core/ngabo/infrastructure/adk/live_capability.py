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

Keyless Vertex mode: when ``GOOGLE_GENAI_USE_VERTEXAI=true``, the module
relies on Application Default Credentials (ADC) over WIF and does NOT require
an API key. In that mode the caller supplies ``GOOGLE_CLOUD_PROJECT`` and
``GOOGLE_CLOUD_LOCATION``, and the runtime identity must hold the Vertex/Gemini
caller permission.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping

from ngabo.application.services.spike_proof_verifier import VerificationContext
from ngabo.infrastructure.adk.spike_adapter import SpikeRunResult, run_spike

DEFAULT_MODEL: str = "gemini-3.6-flash"


def _vertex_mode_from(env: Mapping[str, str]) -> bool:
    """True when the google-genai client should use the keyless Vertex path."""
    value = env.get("GOOGLE_GENAI_USE_VERTEXAI", "")
    return value.strip().lower() in ("1", "true", "yes")


def _is_vertex_mode() -> bool:
    """Convenience wrapper reading the process environment."""
    return _vertex_mode_from(os.environ)


def _normalized_vertex_env(env: Mapping[str, str]) -> dict[str, str]:
    """Return ``env`` with the Vertex flag normalized to the SDK spelling.

    ``_vertex_mode_from`` accepts ``true`` / ``1`` / ``yes`` as intent, but the
    pinned ``google-genai`` client enables Vertex mode only when
    ``GOOGLE_GENAI_USE_VERTEXAI`` equals ``true`` (case-insensitive). This
    normalizes the intent to the exact spelling so the client and this helper
    agree on the keyless Vertex path.
    """
    normalized = dict(env)
    if _vertex_mode_from(env):
        normalized["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
    return normalized


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
    vertex_mode = _is_vertex_mode()
    api_key = os.environ.get("GEMINI_API_KEY")
    if vertex_mode:
        # Keyless Vertex path: rely on ADC/WIF. No API key is required.
        # Normalize the flag to the exact spelling the pinned google-genai
        # client recognizes (true/1/yes intent -> "true").
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
    else:
        # Developer-API path: google.genai's default client reads
        # GOOGLE_API_KEY; ADK's GoogleLlm uses it.
        if not api_key:
            raise SystemExit(
                "GEMINI_API_KEY is required for the live ADK capability proof "
                "(or set GOOGLE_GENAI_USE_VERTEXAI=true for the keyless Vertex path)"
            )
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
