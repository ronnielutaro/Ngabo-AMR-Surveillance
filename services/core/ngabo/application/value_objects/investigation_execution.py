"""Framework-free event-invocation execution contracts (Issue #53).

This module defines the typed boundary between a backend/event-shaped inbound
request and the deterministic ADK outer execution runtime. It carries the
incident/source identity the run is bound to, an immutable runtime budget, the
observable execution metadata (run/session/invocation identity), and a
structured ``EventInvocationResult``.

Authority boundary (the #53 invariant):

- ``EventInvocationResult`` has NO ``verified`` / ``approved`` /
  ``authorized`` / ``ready_to_send`` / ``package_completed`` field and no
  authorization token;
- only ``InvestigationExecutionOutcome.COMPLETED_CURRENT_STAGE`` is a success
  semantic, and it is a narrow "current bounded adapter stage completed"
  meaning — it never claims a package was synthesized, verified, or sent;
- a run that carries a ``failure_code`` can never be reported as success.

No verification, persistence, action policy, or model/cloud behavior lives
here. ADK session state is execution-runtime state only and is NOT canonical
incident state (problem #19).
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass

from ngabo.application.enums.investigation_execution_error_code import (
    InvestigationExecutionErrorCode,
)
from ngabo.application.enums.investigation_execution_outcome import (
    InvestigationExecutionOutcome,
)
from ngabo.application.value_objects.investigation_context import (
    InvestigationContextResult,
)
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.source_watermark import SourceWatermark

# The single supported inbound event-invocation command contract version.
EVENT_INVESTIGATION_CONTRACT_VERSION = "ngabo-event-investigation-v1"

_EXECUTION_ID_PATTERN = re.compile(r"RUN-[0-9a-f]{32}")


def _require_nonblank(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected non-blank text")
    return value


@dataclass(frozen=True)
class InvestigationExecutionId:
    """Opaque, stable identifier for one event-invoked investigation run.

    Generated once at the adapter boundary and propagated through the run,
    ADK session/invocation identity and telemetry so a single logical run can
    be correlated without exposing PHI/sensitive record content in identifiers.
    """

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not _EXECUTION_ID_PATTERN.fullmatch(self.value):
            raise ValueError(
                f"Invalid investigation execution ID {self.value!r}; "
                "expected 'RUN-<32 hex characters>'"
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class EventInvestigationCommand:
    """Backend/event-shaped inbound command to start an investigation.

    This is the machine-generated initiating input. There is NO natural-language
    user prompt, chat history, or manual instruction; a backend event carries
    only the typed incident/source identity plus a trigger/correlation identity.
    """

    incident_id: IncidentId
    incident_version: IncidentVersion
    source_watermark: SourceWatermark
    event_id: str
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.incident_id, IncidentId):
            raise ValueError("incident_id must be an IncidentId")
        if not isinstance(self.incident_version, IncidentVersion):
            raise ValueError("incident_version must be an IncidentVersion")
        if not isinstance(self.source_watermark, SourceWatermark):
            raise ValueError("source_watermark must be a SourceWatermark")
        _require_nonblank(self.event_id, "event id")
        if self.correlation_id is not None:
            _require_nonblank(self.correlation_id, "correlation id")

    def to_primitive(self) -> dict[str, object]:
        """Return a stable, JSON-safe primitive representation."""
        return {
            "contract_version": EVENT_INVESTIGATION_CONTRACT_VERSION,
            "incident_id": self.incident_id.value,
            "incident_version": self.incident_version.value,
            "source_watermark": self.source_watermark.value,
            "event_id": self.event_id,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_primitive(cls, data: Mapping[str, object]) -> EventInvestigationCommand:
        """Build a command from a primitive payload, failing closed on malformed input.

        The adapter's ``execute_primitive`` maps any ``ValueError`` raised here
        into a stable ``InvestigationExecutionErrorCode.MALFORMED_COMMAND``
        result rather than letting an exception escape to the caller.
        """
        if not isinstance(data, Mapping):
            raise ValueError("event command primitive must be a mapping")
        contract_version = data.get("contract_version")
        if contract_version != EVENT_INVESTIGATION_CONTRACT_VERSION:
            raise ValueError(
                f"unsupported event investigation contract_version {contract_version!r}; "
                f"expected {EVENT_INVESTIGATION_CONTRACT_VERSION!r}"
            )
        incident_id = data.get("incident_id")
        if not isinstance(incident_id, str):
            raise ValueError("incident_id must be a string")
        incident_version = data.get("incident_version")
        if isinstance(incident_version, bool) or not isinstance(incident_version, int):
            raise ValueError("incident_version must be an integer")
        source_watermark = data.get("source_watermark")
        if not isinstance(source_watermark, str):
            raise ValueError("source_watermark must be a string")
        event_id = data.get("event_id")
        if not isinstance(event_id, str):
            raise ValueError("event_id must be a string")
        correlation_id = data.get("correlation_id")
        if correlation_id is not None and not isinstance(correlation_id, str):
            raise ValueError("correlation_id must be a string or null")
        return cls(
            incident_id=IncidentId(incident_id),
            incident_version=IncidentVersion(incident_version),
            source_watermark=SourceWatermark(source_watermark),
            event_id=event_id,
            correlation_id=correlation_id,
        )


@dataclass(frozen=True)
class InvestigationRuntimeBudget:
    """Immutable bounded execution envelope for one event-invoked run (#53).

    Dimensions that the pinned ADK path cannot natively enforce are enforced at
    the infrastructure application boundary and fail closed; dimensions that are
    merely configured (no loop/repair stage exists in this boundary) are recorded
    as configuration, never as enforced behavior.

    Enforcement owners in #53:

    - ``max_runtime_seconds``: enforced by ``asyncio.wait_for`` around the ADK
      Runner (infrastructure boundary);
    - ``max_tool_calls``: enforced in the thin FunctionNode wrapper before the
      inward capability is invoked (infrastructure boundary);
    - ``max_model_calls``: no model call is made on the deterministic path, so
      the observed count is 0 and remains within budget;
    - ``max_loop_iterations`` / ``max_repair_attempts``: no loop/repair stage
      exists in this boundary; recorded as configuration only.
    """

    max_runtime_seconds: float
    max_model_calls: int
    max_tool_calls: int
    max_loop_iterations: int
    max_repair_attempts: int

    def __post_init__(self) -> None:
        if (
            isinstance(self.max_runtime_seconds, bool)
            or not isinstance(self.max_runtime_seconds, (int, float))
            or not math.isfinite(self.max_runtime_seconds)
            or self.max_runtime_seconds <= 0
        ):
            raise ValueError(
                f"Invalid max runtime seconds {self.max_runtime_seconds!r}; "
                "expected a finite positive number"
            )
        for name in ("max_model_calls", "max_tool_calls", "max_loop_iterations"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(
                    f"Invalid {name} {value!r}; expected a non-negative integer"
                )
        if (
            isinstance(self.max_repair_attempts, bool)
            or not isinstance(self.max_repair_attempts, int)
            or self.max_repair_attempts < 0
        ):
            raise ValueError(
                f"Invalid max repair attempts {self.max_repair_attempts!r}; "
                "expected a non-negative integer"
            )
        if isinstance(self.max_runtime_seconds, int):
            object.__setattr__(self, "max_runtime_seconds", float(self.max_runtime_seconds))

    def to_primitive(self) -> dict[str, object]:
        """Return a stable, JSON-safe primitive representation."""
        return {
            "max_runtime_seconds": self.max_runtime_seconds,
            "max_model_calls": self.max_model_calls,
            "max_tool_calls": self.max_tool_calls,
            "max_loop_iterations": self.max_loop_iterations,
            "max_repair_attempts": self.max_repair_attempts,
        }


# Sensible immutable default bound for the event-invoked investigation runtime
# (#53). The deterministic path makes no model call and performs one tool call.
DEFAULT_INVESTIGATION_RUNTIME_BUDGET = InvestigationRuntimeBudget(
    max_runtime_seconds=30.0,
    max_model_calls=0,
    max_tool_calls=4,
    max_loop_iterations=1,
    max_repair_attempts=0,
)


@dataclass(frozen=True)
class ADKExecutionMetadata:
    """Observable, secret-free execution metadata for one run."""

    execution_id: InvestigationExecutionId
    session_id: str
    invocation_id: str
    event_id: str
    correlation_id: str | None
    incident_id: IncidentId
    incident_version: IncidentVersion
    source_watermark: SourceWatermark
    wrapper_calls: int
    model_calls: int
    tool_calls: int
    duration_ms: int
    budget: InvestigationRuntimeBudget
    adk_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, InvestigationExecutionId):
            raise ValueError("execution_id must be an InvestigationExecutionId")
        _require_nonblank(self.session_id, "session id")
        _require_nonblank(self.invocation_id, "invocation id")
        _require_nonblank(self.event_id, "event id")
        if self.correlation_id is not None:
            _require_nonblank(self.correlation_id, "correlation id")
        if not isinstance(self.incident_id, IncidentId):
            raise ValueError("incident_id must be an IncidentId")
        if not isinstance(self.incident_version, IncidentVersion):
            raise ValueError("incident_version must be an IncidentVersion")
        if not isinstance(self.source_watermark, SourceWatermark):
            raise ValueError("source_watermark must be a SourceWatermark")
        for name in ("wrapper_calls", "model_calls", "tool_calls", "duration_ms"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(
                    f"Invalid {name} {value!r}; expected a non-negative integer"
                )
        if not isinstance(self.budget, InvestigationRuntimeBudget):
            raise ValueError("budget must be an InvestigationRuntimeBudget")
        _require_nonblank(self.adk_version, "ADK version")

    def to_primitive(self) -> dict[str, object]:
        """Return a stable, secret-free JSON-safe primitive representation."""
        return {
            "execution_id": self.execution_id.value,
            "session_id": self.session_id,
            "invocation_id": self.invocation_id,
            "event_id": self.event_id,
            "correlation_id": self.correlation_id,
            "incident_id": self.incident_id.value,
            "incident_version": self.incident_version.value,
            "source_watermark": self.source_watermark.value,
            "wrapper_calls": self.wrapper_calls,
            "model_calls": self.model_calls,
            "tool_calls": self.tool_calls,
            "duration_ms": self.duration_ms,
            "budget": self.budget.to_primitive(),
            "adk_version": self.adk_version,
        }


@dataclass(frozen=True)
class EventInvocationResult:
    """Structured outcome of one event-invoked investigation run.

    ``metadata`` is ``None`` only when no run actually started (e.g. a
    malformed command was rejected before any session/invocation was created).
    This contract is structurally incapable of representing itself as verified,
    approved, or action-authorized.
    """

    outcome: InvestigationExecutionOutcome
    execution_id: InvestigationExecutionId
    metadata: ADKExecutionMetadata | None
    capability_result: InvestigationContextResult | None
    failure_code: InvestigationExecutionErrorCode | None

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, InvestigationExecutionOutcome):
            raise ValueError("outcome must be an InvestigationExecutionOutcome")
        if not isinstance(self.execution_id, InvestigationExecutionId):
            raise ValueError("execution_id must be an InvestigationExecutionId")
        if self.metadata is not None and not isinstance(self.metadata, ADKExecutionMetadata):
            raise ValueError("metadata must be an ADKExecutionMetadata or None")
        if self.capability_result is not None and not isinstance(
            self.capability_result, InvestigationContextResult
        ):
            raise ValueError("capability_result must be an InvestigationContextResult or None")
        if self.failure_code is not None and not isinstance(
            self.failure_code, InvestigationExecutionErrorCode
        ):
            raise ValueError("failure_code must be an InvestigationExecutionErrorCode or None")
        if self.outcome.is_success and self.failure_code is not None:
            raise ValueError(
                "a successful outcome cannot carry a failure_code; "
                "failure must never be mislabeled as success"
            )

    def is_success(self) -> bool:
        """True only for the narrow ``COMPLETED_CURRENT_STAGE`` success value."""
        return self.outcome.is_success

    def to_safe_primitive(self) -> dict[str, object]:
        """Return a secret-free, JSON-safe trace representation.

        This deliberately excludes the typed ``capability_result`` contents
        (which can include sensitive isolate records) and is safe to persist as
        a machine-readable trace fixture. It exposes only the outcome, the
        resolved identifiers, the execution metadata, and the capability
        outcome/error code.
        """
        metadata = self.metadata.to_primitive() if self.metadata is not None else None
        return {
            "outcome": self.outcome.value,
            "is_success": self.outcome.is_success,
            "execution_id": self.execution_id.value,
            "metadata": metadata,
            "capability_outcome": (
                self.capability_result.outcome.value if self.capability_result is not None else None
            ),
            "failure_code": self.failure_code.value if self.failure_code is not None else None,
        }
