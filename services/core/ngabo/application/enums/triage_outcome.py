"""Typed outcomes for the bounded Gemini triage / evidence-intent stage (Issue #55).

These describe the outer triage stage as a whole, distinct from the inner
evidence-search outcomes. A model proposal is provisional; it never carries
decision, completion, authorization, or action semantics.
"""

from __future__ import annotations

from enum import StrEnum


class TriageOutcome(StrEnum):
    """Terminal outcome of one bounded triage + evidence-intent stage."""

    EVIDENCE_RETRIEVED = "EVIDENCE_RETRIEVED"
    """The model produced a valid allow-listed proposal and approved evidence
    was retrieved. This is a narrow, truthful success: Gemini proposed, code
    validated, deterministic retrieval returned approved sources."""

    NO_EVIDENCE = "NO_EVIDENCE"
    """The proposal was valid but no approved evidence satisfied the intent."""

    BLOCKED = "BLOCKED"
    """The stage could not proceed: the #54 entry gate was not downstream-ready,
    the model produced a forbidden/invalid intent, or a deterministic gate
    rejected the proposal. Never authorizes synthesis or action."""

    FAILED = "FAILED"
    """The model/provider/runtime failed (malformed output, schema violation,
    timeout, rate limit, provider failure) or approved-evidence retrieval
    failed. Bounded and typed; no free-form prose fallback."""

    @property
    def is_success(self) -> bool:
        """True only for the narrow ``EVIDENCE_RETRIEVED`` completion."""
        return self is TriageOutcome.EVIDENCE_RETRIEVED
