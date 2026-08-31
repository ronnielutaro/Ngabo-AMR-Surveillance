"""Allow-listed evidence-intent vocabulary for bounded Gemini triage (Issue #55).

Gemini may propose ONLY one of these deterministic evidence intents. The model
never invents arbitrary domains or URLs; deterministic code decides which
approved evidence sources satisfy the intent.
"""

from __future__ import annotations

from enum import StrEnum


class EvidenceIntent(StrEnum):
    """Deterministic allow-list of approved-evidence retrieval intents."""

    IP_C = "IP_C"
    """Infection-prevention and control guidance."""

    SURVEILLANCE_INTERPRETATION = "SURVEILLANCE_INTERPRETATION"
    """Surveillance / early-recognition interpretation guidance."""

    RESISTANCE_MECHANISM = "RESISTANCE_MECHANISM"
    """Resistance-mechanism / definition guidance."""

    ORGANISM_AMR = "ORGANISM_AMR"
    """Organism-specific AMR guidance."""

    ANTIMICROBIAL_STEWARDSHIP = "ANTIMICROBIAL_STEWARDSHIP"
    """Antimicrobial-stewardship guidance."""
