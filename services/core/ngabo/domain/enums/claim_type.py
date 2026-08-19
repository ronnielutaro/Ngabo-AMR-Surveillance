"""Domain enum for the five allowed v0.1 proof-carrying claim families.

Exactly the five families required by ``docs/PROOF_CARRYING_REASONING.md``
§4 and ADR 0009 (M1B.4, Issue #28). The forbidden authority claim types —
diagnosis, prescription, outbreak confirmation, mandatory containment
order, official public-health declaration — are intentionally NOT part of
this vocabulary; model output attempting such authority is rejected by the
later deterministic verification policy (#29).
"""

from __future__ import annotations

from enum import StrEnum


class ClaimType(StrEnum):
    """The five claim families the v0.1 autonomous path recognizes."""

    OBSERVED_FACT = "OBSERVED_FACT"
    DERIVED_FINDING = "DERIVED_FINDING"
    EVIDENCE_STATEMENT = "EVIDENCE_STATEMENT"
    HYPOTHESIS = "HYPOTHESIS"
    ACTION_JUSTIFICATION = "ACTION_JUSTIFICATION"
