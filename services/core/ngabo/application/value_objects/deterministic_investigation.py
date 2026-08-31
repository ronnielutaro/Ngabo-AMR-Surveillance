"""Framework-free deterministic investigation fan-out/join contracts (Issue #54).

This module defines the immutable boundary contracts for the #54 deterministic
investigation graph: one immutable fan-out input snapshot (``Deterministic
InvestigationInput``) and one immutable typed joined result
(``JoinedInvestigationContext``). These are application-layer value objects —
no ADK, Gemini, Pydantic, cloud, or persistence type appears here.

Authority boundary: the joined result carries deterministic scientific findings
only. It has NO ``package_completed`` / ``verified`` / ``authorized`` field and
never represents itself as action-ready or package-complete.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ngabo.application.enums.investigation_execution_error_code import (
    InvestigationExecutionErrorCode,
)
from ngabo.application.value_objects.baseline_summary import BaselineSummaryResult
from ngabo.application.value_objects.missingness import MissingnessResult
from ngabo.application.value_objects.profile_comparison import ProfileComparisonResult
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.source_watermark import SourceWatermark


def _require_opaque_id(value: object, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
    ):
        raise ValueError(f"Invalid {label} {value!r}; expected a non-blank opaque ID")


class BranchIdentity(StrEnum):
    """Stable deterministic branch identities for the fixed investigation fan-out."""

    PROFILE = "PROFILE"
    BASELINE = "BASELINE"
    MISSINGNESS = "MISSINGNESS"


@dataclass(frozen=True)
class BranchRunRecord:
    """One immutable, secret-free branch execution record for telemetry/tracing."""

    branch: BranchIdentity
    required: bool
    started: bool
    completed: bool
    blocked: bool
    failed: bool
    timed_out: bool
    invocation_count: int
    capability_outcome: str | None
    duration_ms: int

    def __post_init__(self) -> None:
        if not isinstance(self.branch, BranchIdentity):
            raise ValueError("branch must be a BranchIdentity")
        if not isinstance(self.required, bool):
            raise ValueError("required must be a bool")
        for name in ("started", "completed", "blocked", "failed", "timed_out"):
            if not isinstance(getattr(self, name), bool):
                raise ValueError(f"{name} must be a bool")
        if (
            isinstance(self.invocation_count, bool)
            or not isinstance(self.invocation_count, int)
            or self.invocation_count < 0
        ):
            raise ValueError("invocation_count must be a non-negative integer")
        if self.capability_outcome is not None and (
            not isinstance(self.capability_outcome, str) or not self.capability_outcome.strip()
        ):
            raise ValueError("capability_outcome must be non-blank text or None")
        if (
            isinstance(self.duration_ms, bool)
            or not isinstance(self.duration_ms, int)
            or self.duration_ms < 0
        ):
            raise ValueError("duration_ms must be a non-negative integer")

    def to_primitive(self) -> dict[str, object]:
        return {
            "branch": self.branch.value,
            "required": self.required,
            "started": self.started,
            "completed": self.completed,
            "blocked": self.blocked,
            "failed": self.failed,
            "timed_out": self.timed_out,
            "invocation_count": self.invocation_count,
            "capability_outcome": self.capability_outcome,
            "duration_ms": self.duration_ms,
        }


@dataclass(frozen=True)
class GraphAttemptId:
    """Opaque, monotonic identity for one logical investigation graph attempt.

    The parent ``InvestigationExecutionId`` identifies the backend invocation;
    this distinguishes a retry of the same invocation (attempt 1..N). It is an
    execution-runtime identity, never canonical incident state.
    """

    value: int

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, int) or self.value < 1:
            raise ValueError(
                f"Invalid graph attempt id {self.value!r}; expected an integer >= 1"
            )

    def __str__(self) -> str:
        return f"ATTEMPT-{self.value}"


@dataclass(frozen=True)
class DeterministicInvestigationInput:
    """Immutable framework-free snapshot consumed by all three fan-out branches.

    The context stage establishes ONE canonical input snapshot after the event
    watermark binding passes. The fan-out consumes this snapshot; each ADK node
    never independently reinterprets the incoming event.
    """

    incident_id: IncidentId
    incident_version: IncidentVersion
    source_watermark: SourceWatermark
    graph_attempt: GraphAttemptId
    isolate_id_a: str
    isolate_id_b: str
    organism_code: str
    facility_id: str
    ward: str
    required_isolate_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.incident_id, IncidentId):
            raise ValueError("incident_id must be an IncidentId")
        if not isinstance(self.incident_version, IncidentVersion):
            raise ValueError("incident_version must be an IncidentVersion")
        if not isinstance(self.source_watermark, SourceWatermark):
            raise ValueError("source_watermark must be a SourceWatermark")
        if not isinstance(self.graph_attempt, GraphAttemptId):
            raise ValueError("graph_attempt must be a GraphAttemptId")
        _require_opaque_id(self.isolate_id_a, "isolate_id_a")
        _require_opaque_id(self.isolate_id_b, "isolate_id_b")
        if self.isolate_id_a == self.isolate_id_b:
            raise ValueError("the profile comparison requires two distinct isolates")
        _require_opaque_id(self.organism_code, "organism_code")
        _require_opaque_id(self.facility_id, "facility_id")
        _require_opaque_id(self.ward, "ward")
        if not isinstance(self.required_isolate_ids, tuple) or not self.required_isolate_ids:
            raise ValueError("required_isolate_ids must be a non-empty tuple of the full cohort")
        for isolate_id in self.required_isolate_ids:
            _require_opaque_id(isolate_id, "required_isolate_ids element")
        required = set(self.required_isolate_ids)
        if {self.isolate_id_a, self.isolate_id_b}.issubset(required) is False:
            raise ValueError("required_isolate_ids must include the profile comparison pair")


@dataclass(frozen=True)
class JoinedInvestigationContext:
    """Immutable typed result of the deterministic fan-out/join graph.

    This is the framework-free contract that #55 (bounded Gemini triage/synthesis)
    consumes. ``ready_for_downstream`` is only True when every required branch
    completed with SUCCESS and the canonical binding (incident id/version/source
    watermark) held across all branches. It never represents package completion
    or action authority.
    """

    incident_id: IncidentId
    incident_version: IncidentVersion
    source_watermark: SourceWatermark
    graph_attempt: GraphAttemptId
    profile_result: ProfileComparisonResult | None
    baseline_result: BaselineSummaryResult | None
    missingness_result: MissingnessResult | None
    ready_for_downstream: bool
    failure_code: InvestigationExecutionErrorCode | None
    model_calls: int

    def __post_init__(self) -> None:
        if not isinstance(self.incident_id, IncidentId):
            raise ValueError("incident_id must be an IncidentId")
        if not isinstance(self.incident_version, IncidentVersion):
            raise ValueError("incident_version must be an IncidentVersion")
        if not isinstance(self.source_watermark, SourceWatermark):
            raise ValueError("source_watermark must be a SourceWatermark")
        if not isinstance(self.graph_attempt, GraphAttemptId):
            raise ValueError("graph_attempt must be a GraphAttemptId")
        if self.profile_result is not None and not isinstance(
            self.profile_result, ProfileComparisonResult
        ):
            raise ValueError("profile_result must be a ProfileComparisonResult or None")
        if self.baseline_result is not None and not isinstance(
            self.baseline_result, BaselineSummaryResult
        ):
            raise ValueError("baseline_result must be a BaselineSummaryResult or None")
        if self.missingness_result is not None and not isinstance(
            self.missingness_result, MissingnessResult
        ):
            raise ValueError("missingness_result must be a MissingnessResult or None")
        if not isinstance(self.ready_for_downstream, bool):
            raise ValueError("ready_for_downstream must be a bool")
        if self.failure_code is not None and not isinstance(
            self.failure_code, InvestigationExecutionErrorCode
        ):
            raise ValueError("failure_code must be an InvestigationExecutionErrorCode or None")
        if (
            isinstance(self.model_calls, bool)
            or not isinstance(self.model_calls, int)
            or self.model_calls < 0
        ):
            raise ValueError("model_calls must be a non-negative integer")
        if self.ready_for_downstream and self.failure_code is not None:
            raise ValueError("a ready-for-downstream join cannot carry a failure_code")
        if self.ready_for_downstream and (
            self.profile_result is None
            or self.baseline_result is None
            or self.missingness_result is None
        ):
            raise ValueError(
                "a ready-for-downstream join requires all three typed branch results"
            )

    @property
    def ready(self) -> bool:
        """Alias so downstream code reads an explicit, non-ambiguous readiness flag."""
        return self.ready_for_downstream

    def to_safe_summary(self) -> dict[str, object]:
        """Return a secret-free summary (no isolate records / scientific details)."""
        return {
            "incident_id": self.incident_id.value,
            "incident_version": self.incident_version.value,
            "source_watermark": self.source_watermark.value,
            "graph_attempt": self.graph_attempt.value,
            "ready_for_downstream": self.ready_for_downstream,
            "failure_code": self.failure_code.value if self.failure_code is not None else None,
            "profile_outcome": (
                self.profile_result.outcome.value if self.profile_result is not None else None
            ),
            "baseline_outcome": (
                self.baseline_result.outcome.value if self.baseline_result is not None else None
            ),
            "missingness_outcome": (
                self.missingness_result.outcome.value
                if self.missingness_result is not None
                else None
            ),
            "has_material_missingness": (
                self.missingness_result.has_material_missingness
                if self.missingness_result is not None
                else None
            ),
            "model_calls": self.model_calls,
        }
