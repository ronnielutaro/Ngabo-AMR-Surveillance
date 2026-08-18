"""Ngabo core — AMR surveillance and incident-response system.

Clean Architecture layers, innermost first:

- ``domain``          — entities, value objects, deterministic scientific policy
- ``application``     — use cases, workflows, ports
- ``interfaces``      — HTTP/event translation
- ``infrastructure``  — framework/vendor adapters (FastAPI, GCP, ADK, Gemini)
- ``bootstrap``       — composition root

M1A scaffold: these layers are intentionally empty placeholders for future
milestones. No product behavior is implemented yet.
"""

__version__ = "0.1.0"
