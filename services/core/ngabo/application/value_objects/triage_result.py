"""Typed result of the bounded Gemini triage + evidence-intent stage (#55)."""

from __future__ import annotations

from dataclasses import dataclass

from ngabo.application.enums.triage_error_code import TriageErrorCode
from ngabo.application.enums.triage_outcome import TriageOutcome
from ngabo.application.value_objects.evidence_intent_proposal import EvidenceIntentProposal
from ngabo.application.value_objects.evidence_search import EvidenceSearchResult


@dataclass(frozen=True)
class TriageResult:
    """Outcome of one bounded triage + approved-evidence retrieval run."""

    outcome: TriageOutcome
    proposal: EvidenceIntentProposal | None
    evidence_result: EvidenceSearchResult | None
    model_calls: int
    duration_ms: int
    model_version: str | None
    error_code: TriageErrorCode | None
    execution_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, TriageOutcome):
            raise ValueError("outcome must be a TriageOutcome")
        if self.proposal is not None and not isinstance(self.proposal, EvidenceIntentProposal):
            raise ValueError("proposal must be an EvidenceIntentProposal or None")
        if self.evidence_result is not None and not isinstance(
            self.evidence_result, EvidenceSearchResult
        ):
            raise ValueError("evidence_result must be an EvidenceSearchResult or None")
        if (
            isinstance(self.model_calls, bool)
            or not isinstance(self.model_calls, int)
            or self.model_calls < 0
        ):
            raise ValueError("model_calls must be a non-negative integer")
        if (
            isinstance(self.duration_ms, bool)
            or not isinstance(self.duration_ms, int)
            or self.duration_ms < 0
        ):
            raise ValueError("duration_ms must be a non-negative integer")
        if self.model_version is not None and (
            not isinstance(self.model_version, str) or not self.model_version.strip()
        ):
            raise ValueError("model_version must be non-blank text or None")
        if self.error_code is not None and not isinstance(self.error_code, TriageErrorCode):
            raise ValueError("error_code must be a TriageErrorCode or None")
        if self.outcome.is_success and self.error_code is not None:
            raise ValueError("a successful triage outcome cannot carry an error_code")
        if self.outcome is TriageOutcome.EVIDENCE_RETRIEVED and self.evidence_result is None:
            raise ValueError("EVIDENCE_RETRIEVED requires an evidence_result")

    def is_success(self) -> bool:
        return self.outcome.is_success
