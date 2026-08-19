"""Ngabo domain layer — the innermost, most stable layer.

Owns entities, value objects, domain events, deterministic surveillance rules,
incident state policy, claim policy, action-class policy, and domain exceptions.

Must remain free of framework/vendor imports (FastAPI, Google Cloud SDKs,
Google ADK, Gemini SDKs, notification SDKs). Depends on no outer Ngabo layer.

Populated incrementally by milestone issues; see the subpackage docstrings.
"""
