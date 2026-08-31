"""Production event-invoked ADK outer execution adapter (Issue #53).

This is the OUTER execution boundary. A backend/event-shaped command is turned
into a machine-generated ADK message carrier and invoked through the real
pinned ``google-adk`` ``Runner``/``Workflow``/``FunctionNode`` path with NO
interactive chat, ``adk web``, or user prompt. The workflow contains a single
thin ``FunctionNode`` that invokes a deterministic inward capability
(``GetInvestigationContext``) supplied by dependency injection.

Dependency direction:

    backend event
        -> EventInvestigationCommand
        -> this adapter (infrastructure)
        -> ADK Runner / session / Workflow
        -> thin FunctionNode wrapper
        -> injected application capability
        -> deterministic domain behavior

Clean-architecture rules honored here:

- ADK/Gemini imports stay in infrastructure;
- the wrapper never queries persistence, never recomputes scientific values,
  never applies thresholds, and never mutates canonical state;
- application/domain code never receives an ADK ``Runner``/``Session``/
  ``InvocationContext``/``Workflow``/``FunctionNode`` parameter;
- the run is replay-safe (no side effects) and never synthesizes an
  ``IncidentPackageCandidate`` or takes an external action.

ADK session/invocation identifiers are execution-runtime identifiers only; they
are NOT canonical incident state and are never interpreted as patient/clinician
identity or an authorization principal. ``user_id`` is an ADK runtime namespace.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from google.adk import Context, Runner
from google.adk.sessions import InMemorySessionService
from google.adk.workflow import FunctionNode, Workflow
from google.genai import types

from ngabo.application.enums.capability_outcome import CapabilityOutcome
from ngabo.application.enums.investigation_execution_error_code import (
    InvestigationExecutionErrorCode,
)
from ngabo.application.enums.investigation_execution_outcome import (
    InvestigationExecutionOutcome,
)
from ngabo.application.value_objects.investigation_context import (
    GetInvestigationContextQuery,
    InvestigationContextResult,
)
from ngabo.application.value_objects.investigation_execution import (
    DEFAULT_INVESTIGATION_RUNTIME_BUDGET,
    EVENT_INVESTIGATION_CONTRACT_VERSION,
    ADKExecutionMetadata,
    EventInvestigationCommand,
    EventInvocationResult,
    InvestigationExecutionId,
    InvestigationRuntimeBudget,
)
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.source_watermark import SourceWatermark

DEFAULT_APP_NAME = "ngabo-amt-investigation"
# An ADK runtime namespace for backend automation. It is NEVER patient/clinician
# identity or an authorization principal (problem #9).
DEFAULT_RUNTIME_USER_ID = "ngabo-service"

# Callable signature for the injected deterministic inward capability.
InvestigationContextHandler = Callable[[GetInvestigationContextQuery], InvestigationContextResult]


def detect_google_adk_version() -> str:
    """Return the installed google-adk distribution version (verified, not guessed)."""
    try:
        return _pkg_version("google-adk")
    except PackageNotFoundError:
        return "unknown"


@dataclass(frozen=True)
class _CapabilityMapping:
    """Outcome/error-code mapping between an inward capability and the outer runtime."""

    outcome: InvestigationExecutionOutcome
    failure_code: InvestigationExecutionErrorCode | None


@dataclass
class _RunTelemetry:
    """Per-run mutable counter carriers (infrastructure-internal)."""

    wrapper_calls: int = 0
    tool_calls: int = 0
    model_calls: int = 0


def _require_opaque(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected a non-blank opaque value")
    return value


class EventInvestigationRuntime:
    """Production composition root for the event-invoked ADK investigation run.

    Dependency injection: the deterministic inward application capability is
    supplied (not constructed from raw persistence). ADK infrastructure is built
    per invocation so run-scoped state and tool-call counters never bleed between
    runs. ``InMemorySessionService`` is an execution-runtime adapter choice for
    this boundary only — it is NOT canonical incident state.
    """

    def __init__(
        self,
        *,
        get_context: InvestigationContextHandler,
        budget: InvestigationRuntimeBudget = DEFAULT_INVESTIGATION_RUNTIME_BUDGET,
        app_name: str = DEFAULT_APP_NAME,
        user_id: str = DEFAULT_RUNTIME_USER_ID,
        adk_version: str | None = None,
    ) -> None:
        if not callable(get_context):
            raise TypeError("get_context must be a callable investigation-context handler")
        if not isinstance(budget, InvestigationRuntimeBudget):
            raise TypeError("budget must be an InvestigationRuntimeBudget")
        _require_opaque(app_name, "app name")
        _require_opaque(user_id, "runtime user id")
        self._get_context = get_context
        self._budget = budget
        self._app_name = app_name
        self._user_id = user_id
        self._adk_version = adk_version or detect_google_adk_version()
        # Per-run typed resolution carriers, keyed by opaque execution_id.
        self._capability_results: dict[str, InvestigationContextResult] = {}
        self._run_telemetry: dict[str, _RunTelemetry] = {}

    @property
    def adk_version(self) -> str:
        """The verified installed google-adk version in use by this runtime."""
        return self._adk_version

    @property
    def budget(self) -> InvestigationRuntimeBudget:
        """The immutable runtime budget this runtime enforces."""
        return self._budget

    def __call__(self, command: EventInvestigationCommand) -> EventInvocationResult:
        """Synchronous convenience wrapper (for non-async backend callers)."""
        return self.execute(command)

    def execute(self, command: EventInvestigationCommand) -> EventInvocationResult:
        """Synchronous convenience wrapper around :meth:`execute_async`."""
        return asyncio.run(self.execute_async(command))

    async def execute_async(self, command: EventInvestigationCommand) -> EventInvocationResult:
        """Run one event-invoked investigation through the real ADK runtime."""
        if not isinstance(command, EventInvestigationCommand):
            execution_id = self._new_execution_id()
            return self._rejected_result(
                execution_id, InvestigationExecutionErrorCode.MALFORMED_COMMAND
            )

        execution_id = self._new_execution_id()
        session_id = self._new_session_id()
        invocation_id = self._new_invocation_id()
        envelope = self._build_envelope(command, execution_id, session_id, invocation_id)
        telemetry = _RunTelemetry()
        self._run_telemetry[execution_id.value] = telemetry

        start = time.monotonic()
        try:
            terminal = await asyncio.wait_for(
                self._run_workflow(envelope, telemetry, session_id, invocation_id),
                timeout=self._budget.max_runtime_seconds,
            )
            duration_ms = _duration_ms(start)
            return self._interpret(
                terminal,
                execution_id=execution_id,
                session_id=session_id,
                invocation_id=invocation_id,
                envelope=envelope,
                telemetry=telemetry,
                duration_ms=duration_ms,
            )
        except TimeoutError:
            duration_ms = _duration_ms(start)
            return self._failure_result(
                execution_id,
                InvestigationExecutionErrorCode.EXECUTION_TIMEOUT,
                session_id=session_id,
                invocation_id=invocation_id,
                envelope=envelope,
                telemetry=telemetry,
                duration_ms=duration_ms,
            )
        except Exception:
            duration_ms = _duration_ms(start)
            return self._failure_result(
                execution_id,
                InvestigationExecutionErrorCode.ADK_RUNTIME_EXCEPTION,
                session_id=session_id,
                invocation_id=invocation_id,
                envelope=envelope,
                telemetry=telemetry,
                duration_ms=duration_ms,
            )

    def execute_primitive(self, data: Mapping[str, object]) -> EventInvocationResult:
        """Synchronous convenience wrapper around :meth:`execute_primitive_async`."""
        return asyncio.run(self.execute_primitive_async(data))

    async def execute_primitive_async(self, data: Mapping[str, object]) -> EventInvocationResult:
        """Build a command from a primitive event payload, failing closed on malformed input.

        A future Pub/Sub/backend adapter maps its payload into the same
        framework-free command here. Malformed input is rejected with a stable
        ``MALFORMED_COMMAND`` result rather than an escaping exception.
        """
        try:
            command = EventInvestigationCommand.from_primitive(data)
        except (ValueError, TypeError):
            return self._rejected_result(
                self._new_execution_id(),
                InvestigationExecutionErrorCode.MALFORMED_COMMAND,
            )
        return await self.execute_async(command)

    # -- infrastructure construction -------------------------------------------------

    def _build_envelope(
        self,
        command: EventInvestigationCommand,
        execution_id: InvestigationExecutionId,
        session_id: str,
        invocation_id: str,
    ) -> dict[str, object]:
        """Build the machine-generated event envelope (no user prose / chat intent)."""
        return {
            "contract_version": EVENT_INVESTIGATION_CONTRACT_VERSION,
            "incident_id": command.incident_id.value,
            "incident_version": command.incident_version.value,
            "source_watermark": command.source_watermark.value,
            "event_id": command.event_id,
            "correlation_id": command.correlation_id,
            "execution_id": execution_id.value,
            "session_id": session_id,
            "invocation_id": invocation_id,
        }

    def _construct_message(self, envelope: Mapping[str, object]) -> types.Content:
        """Construct the ADK carrier message from the machine envelope."""
        return types.Content(
            role="user",
            parts=[types.Part(text=json.dumps(envelope, sort_keys=True, separators=(",", ":")))],
        )

    def _make_context_node(self) -> FunctionNode:
        """Build the thin FunctionNode wrapper (all-deterministic, no Agent/model)."""

        async def get_context_node(ctx: Context, node_input: object) -> dict[str, object]:
            return await self._run_context_node(ctx, node_input)

        return FunctionNode(func=get_context_node, name="get_investigation_context")

    async def _run_context_node(self, ctx: Context, node_input: object) -> dict[str, object]:
        """Run the thin inward-capability wrapper (no scientific recomputation).

        The sync deterministic handler is awaited via ``asyncio.to_thread`` so a
        slow canonical fetch never blocks the event loop and the outer
        ``asyncio.wait_for`` deadline can actually preempt the run (fail closed).
        """
        envelope = self._extract_envelope(node_input)
        execution_id = str(envelope.get("execution_id")) if envelope is not None else None
        telemetry = (
            self._run_telemetry[execution_id]
            if execution_id is not None and execution_id in self._run_telemetry
            else _RunTelemetry()
        )
        telemetry.wrapper_calls += 1
        telemetry.tool_calls += 1
        telemetry.model_calls += 0  # deterministic path: no model call
        adk_session_id = str(getattr(ctx.session, "id", ""))
        adk_invocation_id = str(ctx.get_invocation_context().invocation_id)

        # Tool/function-call budget is enforced before invoking the capability.
        if telemetry.tool_calls > self._budget.max_tool_calls:
            return self._payload(
                outcome=InvestigationExecutionOutcome.FAILED,
                failure_code=InvestigationExecutionErrorCode.EXECUTION_BUDGET_EXCEEDED,
                envelope=envelope,
                telemetry=telemetry,
                adk_session_id=adk_session_id,
                adk_invocation_id=adk_invocation_id,
            )

        if envelope is None:
            return self._payload(
                outcome=InvestigationExecutionOutcome.FAILED,
                failure_code=InvestigationExecutionErrorCode.MALFORMED_COMMAND,
                envelope=envelope,
                telemetry=telemetry,
                adk_session_id=adk_session_id,
                adk_invocation_id=adk_invocation_id,
            )

        try:
            incident_id = IncidentId(str(envelope["incident_id"]))
            requested_version = IncidentVersion(
                _as_int(envelope["incident_version"], "incident_version")
            )
            query = GetInvestigationContextQuery(
                incident_id=incident_id,
                requested_version=requested_version,
            )
            capability_result = await asyncio.to_thread(self._get_context, query)
        except Exception as exc:  # noqa: BLE001 - fail closed on a wrapper exception
            return self._payload(
                outcome=InvestigationExecutionOutcome.FAILED,
                failure_code=InvestigationExecutionErrorCode.WRAPPER_EXCEPTION,
                envelope=envelope,
                telemetry=telemetry,
                detail=type(exc).__name__,
                adk_session_id=adk_session_id,
                adk_invocation_id=adk_invocation_id,
            )

        if execution_id is not None:
            self._capability_results[execution_id] = capability_result
        mapping = self._map_capability(capability_result)
        return self._payload(
            outcome=mapping.outcome,
            failure_code=mapping.failure_code,
            envelope=envelope,
            telemetry=telemetry,
            capability_outcome=capability_result.outcome.value,
            adk_session_id=adk_session_id,
            adk_invocation_id=adk_invocation_id,
        )

    async def _run_workflow(
        self,
        envelope: Mapping[str, object],
        telemetry: _RunTelemetry,
        session_id: str,
        invocation_id: str,
    ) -> dict[str, object] | None:
        """Run the real pinned ADK workflow and return the terminal output payload."""
        node = self._make_context_node()
        workflow = Workflow(
            name="ngabo_investigation_runtime",
            edges=[("START", node)],
        )
        session_service = InMemorySessionService()
        runner = Runner(
            node=workflow,
            app_name=self._app_name,
            session_service=session_service,
            auto_create_session=True,
        )
        message = self._construct_message(envelope)
        terminal: dict[str, object] | None = None
        async for event in runner.run_async(
            user_id=self._user_id,
            session_id=session_id,
            invocation_id=invocation_id,
            new_message=message,
        ):
            output = event.output
            if isinstance(output, dict) and output.get("_ngabo_result") is True:
                terminal = output
        return terminal

    # -- interpretation ----------------------------------------------------------------

    def _interpret(
        self,
        terminal: dict[str, object] | None,
        *,
        execution_id: InvestigationExecutionId,
        session_id: str,
        invocation_id: str,
        envelope: Mapping[str, object],
        telemetry: _RunTelemetry,
        duration_ms: int,
    ) -> EventInvocationResult:
        if terminal is None or terminal.get("_ngabo_result") is not True:
            # ADK produced no recognized terminal payload: fail closed, never false success.
            return self._failure_result(
                execution_id,
                InvestigationExecutionErrorCode.ADK_RUNTIME_EXCEPTION,
                session_id=session_id,
                invocation_id=invocation_id,
                envelope=envelope,
                telemetry=telemetry,
                duration_ms=duration_ms,
            )

        # Identifier consistency proof: the real ADK session/invocation IDs read
        # inside the wrapper must match the ones assigned to this run.
        reported_session = terminal.get("adk_session_id")
        reported_invocation = terminal.get("adk_invocation_id")
        if reported_session != session_id or reported_invocation != invocation_id:
            return self._failure_result(
                execution_id,
                InvestigationExecutionErrorCode.ADK_RUNTIME_EXCEPTION,
                session_id=session_id,
                invocation_id=invocation_id,
                envelope=envelope,
                telemetry=telemetry,
                duration_ms=duration_ms,
            )

        outcome = InvestigationExecutionOutcome(str(terminal.get("outcome")))
        raw_failure = terminal.get("failure_code")
        failure_code = (
            InvestigationExecutionErrorCode(str(raw_failure)) if raw_failure is not None else None
        )
        metadata = self._build_metadata(
            execution_id=execution_id,
            session_id=session_id,
            invocation_id=invocation_id,
            envelope=envelope,
            telemetry=telemetry,
            duration_ms=duration_ms,
        )
        capability_result = self._pop_capability_result(execution_id.value)
        result = EventInvocationResult(
            outcome=outcome,
            execution_id=execution_id,
            metadata=metadata,
            capability_result=capability_result,
            failure_code=failure_code,
        )
        self._cleanup(execution_id.value)
        return result

    def _failure_result(
        self,
        execution_id: InvestigationExecutionId,
        code: InvestigationExecutionErrorCode,
        *,
        session_id: str | None = None,
        invocation_id: str | None = None,
        envelope: Mapping[str, object] | None = None,
        telemetry: _RunTelemetry | None = None,
        duration_ms: int = 0,
    ) -> EventInvocationResult:
        if envelope is not None and session_id is not None and invocation_id is not None:
            metadata = self._build_metadata(
                execution_id=execution_id,
                session_id=session_id,
                invocation_id=invocation_id,
                envelope=envelope,
                telemetry=telemetry or _RunTelemetry(),
                duration_ms=duration_ms,
            )
        else:
            metadata = None
        capability_result = self._pop_capability_result(execution_id.value)
        result = EventInvocationResult(
            outcome=InvestigationExecutionOutcome.FAILED,
            execution_id=execution_id,
            metadata=metadata,
            capability_result=capability_result,
            failure_code=code,
        )
        self._cleanup(execution_id.value)
        return result

    def _rejected_result(
        self,
        execution_id: InvestigationExecutionId,
        code: InvestigationExecutionErrorCode,
    ) -> EventInvocationResult:
        return EventInvocationResult(
            outcome=InvestigationExecutionOutcome.FAILED,
            execution_id=execution_id,
            metadata=None,
            capability_result=None,
            failure_code=code,
        )

    def _build_metadata(
        self,
        *,
        execution_id: InvestigationExecutionId,
        session_id: str,
        invocation_id: str,
        envelope: Mapping[str, object],
        telemetry: _RunTelemetry,
        duration_ms: int,
    ) -> ADKExecutionMetadata:
        return ADKExecutionMetadata(
            execution_id=execution_id,
            session_id=session_id,
            invocation_id=invocation_id,
            event_id=_require_opaque(envelope.get("event_id"), "event id"),
            correlation_id=(
                _require_opaque(envelope["correlation_id"], "correlation id")
                if envelope.get("correlation_id") is not None
                else None
            ),
            incident_id=IncidentId(str(envelope["incident_id"])),
            incident_version=IncidentVersion(
                _as_int(envelope["incident_version"], "incident_version")
            ),
            source_watermark=SourceWatermark(str(envelope["source_watermark"])),
            wrapper_calls=telemetry.wrapper_calls,
            model_calls=telemetry.model_calls,
            tool_calls=telemetry.tool_calls,
            duration_ms=duration_ms,
            budget=self._budget,
            adk_version=self._adk_version,
        )

    def _map_capability(self, result: InvestigationContextResult) -> _CapabilityMapping:
        if result.outcome is CapabilityOutcome.SUCCESS:
            return _CapabilityMapping(InvestigationExecutionOutcome.COMPLETED_CURRENT_STAGE, None)
        if result.outcome is CapabilityOutcome.INCIDENT_NOT_FOUND:
            return _CapabilityMapping(
                InvestigationExecutionOutcome.BLOCKED,
                InvestigationExecutionErrorCode.INCIDENT_NOT_FOUND,
            )
        if result.outcome is CapabilityOutcome.STALE_INCIDENT_VERSION:
            return _CapabilityMapping(
                InvestigationExecutionOutcome.BLOCKED,
                InvestigationExecutionErrorCode.STALE_INCIDENT_VERSION,
            )
        if result.outcome is CapabilityOutcome.MISSING_INPUT:
            return _CapabilityMapping(
                InvestigationExecutionOutcome.BLOCKED,
                InvestigationExecutionErrorCode.MISSING_INPUT,
            )
        return _CapabilityMapping(
            InvestigationExecutionOutcome.FAILED,
            InvestigationExecutionErrorCode.INWARD_CAPABILITY_FAILED,
        )

    # -- helpers -----------------------------------------------------------------------

    @staticmethod
    def _payload(
        *,
        outcome: InvestigationExecutionOutcome,
        failure_code: InvestigationExecutionErrorCode | None,
        envelope: Mapping[str, object] | None,
        telemetry: _RunTelemetry,
        capability_outcome: str | None = None,
        detail: str | None = None,
        adk_session_id: str | None = None,
        adk_invocation_id: str | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "_ngabo_result": True,
            "outcome": outcome.value,
            "failure_code": failure_code.value if failure_code is not None else None,
            "capability_outcome": capability_outcome,
            "wrapper_calls": telemetry.wrapper_calls,
            "tool_calls": telemetry.tool_calls,
            "model_calls": telemetry.model_calls,
            "adk_session_id": adk_session_id,
            "adk_invocation_id": adk_invocation_id,
        }
        if envelope is not None:
            payload.update(
                {
                    "execution_id": envelope.get("execution_id"),
                    "session_id": envelope.get("session_id"),
                    "invocation_id": envelope.get("invocation_id"),
                    "event_id": envelope.get("event_id"),
                    "correlation_id": envelope.get("correlation_id"),
                    "incident_id": envelope.get("incident_id"),
                    "incident_version": envelope.get("incident_version"),
                    "source_watermark": envelope.get("source_watermark"),
                }
            )
        if detail is not None:
            payload["detail"] = detail
        return payload

    def _extract_envelope(self, node_input: object) -> dict[str, object] | None:
        """Extract the machine event envelope from the ADK node input."""
        text: str | None = None
        if isinstance(node_input, types.Content):
            text = "".join(
                getattr(part, "text", "") or "" for part in (node_input.parts or ())
            )
        elif isinstance(node_input, str):
            text = node_input
        elif isinstance(node_input, dict):
            return node_input
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except (ValueError, TypeError):
            return None
        if not isinstance(parsed, dict):
            return None
        if parsed.get("contract_version") != EVENT_INVESTIGATION_CONTRACT_VERSION:
            return None
        return parsed

    def _pop_capability_result(self, execution_id: str) -> InvestigationContextResult | None:
        return self._capability_results.pop(execution_id, None)

    def _cleanup(self, execution_id: str) -> None:
        self._capability_results.pop(execution_id, None)
        self._run_telemetry.pop(execution_id, None)

    @staticmethod
    def _new_execution_id() -> InvestigationExecutionId:
        return InvestigationExecutionId(f"RUN-{uuid.uuid4().hex}")

    @staticmethod
    def _new_session_id() -> str:
        return f"ngabo-session-{uuid.uuid4().hex}"

    @staticmethod
    def _new_invocation_id() -> str:
        return f"ngabo-invocation-{uuid.uuid4().hex}"


def _duration_ms(start_monotonic: float) -> int:
    elapsed = (time.monotonic() - start_monotonic) * 1000.0
    return int(round(elapsed))


def _as_int(value: object, label: str) -> int:
    """Return an int from a primitive envelope field, failing closed on non-int."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value
