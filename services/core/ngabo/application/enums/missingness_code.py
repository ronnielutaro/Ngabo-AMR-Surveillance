"""Typed material-missingness vocabulary for deterministic investigation (Issue #50).

The deterministic missingness capability must distinguish material absence
from ordinary empty values so future Gemini reasoning knows where evidence/data
is missing rather than hallucinating completeness. The model never decides
materiality; ordinary deterministic code does.
"""

from __future__ import annotations

from enum import StrEnum


class MissingnessCode(StrEnum):
    """Stable family of material data-absence conditions."""

    REQUIRED_FIELD_ABSENT = "REQUIRED_FIELD_ABSENT"
    REQUIRED_FINDING_UNAVAILABLE = "REQUIRED_FINDING_UNAVAILABLE"
    INCOMPLETE_SOURCE_WINDOW = "INCOMPLETE_SOURCE_WINDOW"
    MISSING_COMPARISON_INPUT = "MISSING_COMPARISON_INPUT"
    UNAVAILABLE_REQUIRED_BRANCH_RESULT = "UNAVAILABLE_REQUIRED_BRANCH_RESULT"
