"""Baseline-summary investigation capability (Issue #50).

Coordinates the existing deterministic signal-detection owner to produce the
typed baseline/signal evaluation for a cohort within an incident. It does NOT
create an LLM baseline summary and does NOT duplicate formulas or thresholds.
The ``evaluate_cohort`` seam defaults to the existing ``evaluate_cohort_signal``
domain service. The result is bound to the incident identity, version, and
source watermark.
"""

from __future__ import annotations

from collections.abc import Callable

from ngabo.application.enums.capability_outcome import CapabilityOutcome
from ngabo.application.ports.investigation_context_repository import (
    InvestigationContextRepository,
)
from ngabo.application.value_objects.baseline_summary import (
    BaselineSummaryResult,
    GetBaselineSummaryQuery,
)
from ngabo.domain.services.signal_detection import (
    SignalEvaluationResult,
    evaluate_cohort_signal,
)


class GetBaselineSummary:
    """Framework-free baseline-summary application capability."""

    def __init__(
        self,
        repository: InvestigationContextRepository,
        *,
        evaluate_cohort: Callable[..., SignalEvaluationResult] = evaluate_cohort_signal,
    ) -> None:
        if not hasattr(repository, "get"):
            raise TypeError("repository must satisfy InvestigationContextRepository")
        if not callable(evaluate_cohort):
            raise TypeError("evaluate_cohort must be callable")
        self._repository = repository
        self._evaluate_cohort = evaluate_cohort

    def execute(self, query: GetBaselineSummaryQuery) -> BaselineSummaryResult:
        """Return the typed versioned baseline summary for ``query``."""
        if not isinstance(query, GetBaselineSummaryQuery):
            raise TypeError(f"query must be a GetBaselineSummaryQuery; got {type(query).__name__}")

        stored = self._repository.get(query.incident_id)
        if stored is None:
            return BaselineSummaryResult(
                outcome=CapabilityOutcome.INCIDENT_NOT_FOUND,
                incident_id=None,
                incident_version=None,
                source_watermark=None,
                signal_evaluation=None,
                organism_code=query.organism_code,
                facility_id=query.facility_id,
                ward=query.ward,
            )

        if (
            query.requested_version is not None
            and query.requested_version != stored.incident_version
        ):
            return BaselineSummaryResult(
                outcome=CapabilityOutcome.STALE_INCIDENT_VERSION,
                incident_id=stored.incident_id,
                incident_version=stored.incident_version,
                source_watermark=stored.source_watermark,
                signal_evaluation=None,
                organism_code=query.organism_code,
                facility_id=query.facility_id,
                ward=query.ward,
            )

        evaluation = self._evaluate_cohort(
            organism_code=query.organism_code,
            facility_id=query.facility_id,
            ward=query.ward,
            isolates=stored.isolates,
            window_end=stored.window_end,
            config=stored.signal_config,
        )
        if not isinstance(evaluation, SignalEvaluationResult):
            raise TypeError("evaluate_cohort must return a SignalEvaluationResult")

        return BaselineSummaryResult(
            outcome=CapabilityOutcome.SUCCESS,
            incident_id=stored.incident_id,
            incident_version=stored.incident_version,
            source_watermark=stored.source_watermark,
            signal_evaluation=evaluation,
            organism_code=query.organism_code,
            facility_id=query.facility_id,
            ward=query.ward,
        )

    def __call__(self, query: GetBaselineSummaryQuery) -> BaselineSummaryResult:
        """Callable protocol support."""
        return self.execute(query)
