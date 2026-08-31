"""Production event-invoked ADK deterministic investigation graph (Issue #53/#54).

This is the OUTER execution boundary. A backend/event-shaped command is turned
into a machine-generated ADK message carrier and invoked through the real
pinned ``google-adk`` ``Runner``/``Workflow``/``FunctionNode``/``JoinNode``
path with NO interactive chat, ``adk web``, or user prompt. The workflow is the
#54 fixed deterministic graph:

    backend event
        -> context node (GetInvestigationContext + canonical watermark binding)
        -> immutable DeterministicInvestigationInput
        -> explicit parallel fan-out
             |- profile comparison (CompareResistanceProfiles)
             |- baseline summary   (GetBaselineSummary)
             `- material missingness (AssessMaterialMissingness)
        -> JoinNode barrier
        -> deterministic join -> JoinedInvestigationContext
        -> READY_FOR_DOWNSTREAM | BLOCKED | FAILED

Dependency direction:

    ADK infrastructure graph
        -> thin ADK wrappers (FunctionNode)
        -> injected application capabilities
        -> deterministic domain science

Clean-architecture rules honored here:

- ADK/Gemini imports stay in infrastructure;
- ADK wrappers never compute scientific values, never apply thresholds, never
  query persistence directly, and never mutate canonical state;
- application/domain code never receives an ADK ``Runner``/``Session``/
  ``InvocationContext``/``Workflow``/``FunctionNode``/``JoinNode`` parameter;
- this stage is zero-model (model_calls == 0 always);
- the run is replay-safe (no side effects), never synthesizes an
  ``IncidentPackageCandidate``, and never takes an external action.

ADK session/invocation identifiers are execution-runtime identifiers only; they
are NOT canonical incident state and are never interpreted as patient/clinician
identity or an authorization principal. ``user_id`` is an ADK runtime namespace.
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
import uuid
from collections.abc import Callable, Mapping
from contextlib import suppress
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import Any, TypeVar, cast

from google.adk import Context, Runner
from google.adk.sessions import InMemorySessionService
from google.adk.workflow import FunctionNode, JoinNode, Workflow
from google.genai import types

from ngabo.application.enums.capability_outcome import CapabilityOutcome
from ngabo.application.enums.investigation_execution_error_code import (
    InvestigationExecutionErrorCode,
)
from ngabo.application.enums.investigation_execution_outcome import (
    InvestigationExecutionOutcome,
)
from ngabo.application.value_objects.baseline_summary import (
    BaselineSummaryResult,
    GetBaselineSummaryQuery,
)
from ngabo.application.value_objects.deterministic_investigation import (
    BranchIdentity,
    BranchRunRecord,
    DeterministicInvestigationInput,
    GraphAttemptId,
    JoinedInvestigationContext,
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
from ngabo.application.value_objects.missingness import (
    AssessMissingnessQuery,
    MissingnessResult,
)
from ngabo.application.value_objects.profile_comparison import (
    CompareProfilesQuery,
    ProfileComparisonResult,
)
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.source_watermark import SourceWatermark

DEFAULT_APP_NAME = "ngabo-amt-investigation"
# An ADK runtime namespace for backend automation. It is NEVER patient/clinician
# identity or an authorization principal (problem #9).
DEFAULT_RUNTIME_USER_ID = "ngabo-service"

# Number of required deterministic branches; fixed by code, never model-selected.
# Canonical branch ordering is by BranchIdentity, not completion order.
REQUIRED_BRANCH_IDENTITIES = (
    BranchIdentity.PROFILE,
    BranchIdentity.BASELINE,
    BranchIdentity.MISSINGNESS,
)

# Callable signatures for the injected deterministic inward capabilities.
InvestigationContextHandler = Callable[[GetInvestigationContextQuery], InvestigationContextResult]
ProfileComparisonHandler = Callable[[CompareProfilesQuery], ProfileComparisonResult]
BaselineSummaryHandler = Callable[[GetBaselineSummaryQuery], BaselineSummaryResult]
MissingnessHandler = Callable[[AssessMissingnessQuery], MissingnessResult]

_T = TypeVar("_T")


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
    """Per-run mutable counters and per-branch state (infrastructure-internal)."""

    wrapper_calls: int = 0
    tool_calls: int = 0
    model_calls: int = 0
    # branch identity value -> mutable per-branch state.
    branches: dict[str, dict[str, object]] = field(default_factory=dict)

    def branch_state(self, branch: BranchIdentity) -> dict[str, object]:
        state = self.branches.setdefault(
            branch.value,
            {
                "started": False,
                "completed": False,
                "failed": False,
                "blocked": False,
                "timed_out": False,
                "invocation_count": 0,
                "capability_outcome": None,
                "start_monotonic": None,
                "duration_ms": 0,
            },
        )
        return state


@dataclass
class _RunBudget:
    """Concurrency-safe per-run tool-call budget (infrastructure-owned).

    The max_tool_calls budget is a HARD per-run bound: every deterministic
    capability invocation (context + each required branch) acquires a slot, and
    retry attempts share the SAME run-level budget (attempt 1 is never reset).
    The lock makes concurrent branch acquisition race-safe so the hard limit
    cannot be exceeded nondeterministically.
    """

    max_calls: int
    used: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def try_acquire(self) -> bool:
        """Atomically reserve one tool slot if the run budget remains."""
        with self.lock:
            if self.used >= self.max_calls:
                return False
            self.used += 1
            return True


def _require_opaque(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Invalid {label} {value!r}; expected a non-blank opaque value")
    return value


class EventInvestigationRuntime:
    """Production composition root for the event-invoked ADK investigation graph.

    Dependency injection: the deterministic inward application capabilities are
    supplied (not constructed from raw persistence). ADK infrastructure is built
    per invocation so run-scoped state and counters never bleed between runs.
    ``InMemorySessionService`` is an execution-runtime adapter choice for this
    boundary only - it is NOT canonical incident state.
    """

    def __init__(
        self,
        *,
        get_context: InvestigationContextHandler,
        compare_profiles: ProfileComparisonHandler,
        get_baseline_summary: BaselineSummaryHandler,
        assess_missingness: MissingnessHandler,
        budget: InvestigationRuntimeBudget = DEFAULT_INVESTIGATION_RUNTIME_BUDGET,
        app_name: str = DEFAULT_APP_NAME,
        user_id: str = DEFAULT_RUNTIME_USER_ID,
        adk_version: str | None = None,
    ) -> None:
        if not callable(get_context):
            raise TypeError("get_context must be a callable investigation-context handler")
        if not callable(compare_profiles):
            raise TypeError("compare_profiles must be a callable profile-comparison handler")
        if not callable(get_baseline_summary):
            raise TypeError("get_baseline_summary must be a callable baseline-summary handler")
        if not callable(assess_missingness):
            raise TypeError("assess_missingness must be a callable missingness handler")
        if not isinstance(budget, InvestigationRuntimeBudget):
            raise TypeError("budget must be an InvestigationRuntimeBudget")
        _require_opaque(app_name, "app name")
        _require_opaque(user_id, "runtime user id")
        self._get_context = get_context
        self._compare_profiles = compare_profiles
        self._get_baseline_summary = get_baseline_summary
        self._assess_missingness = assess_missingness
        self._budget = budget
        self._app_name = app_name
        self._user_id = user_id
        self._adk_version = adk_version or detect_google_adk_version()
        # Per-run typed resolution carriers, keyed by opaque execution_id.
        self._capability_results: dict[str, InvestigationContextResult] = {}
        self._joined_results: dict[str, JoinedInvestigationContext] = {}
        self._run_telemetry: dict[str, _RunTelemetry] = {}
        # Per-run hard tool-call budget, keyed by opaque execution_id. It is
        # created once per backend invocation and survives retry attempts.
        self._run_budget: dict[str, _RunBudget] = {}
        # Last started attempt identifiers so a boundary timeout can still emit
        # run metadata (the run did start even though it did not complete).
        self._last_attempt: dict[str, tuple[str, str, dict[str, object]]] = {}

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
        """Run one event-invoked deterministic investigation through the real ADK runtime."""
        if not isinstance(command, EventInvestigationCommand):
            execution_id = self._new_execution_id()
            return self._rejected_result(
                execution_id, InvestigationExecutionErrorCode.MALFORMED_COMMAND
            )

        execution_id = self._new_execution_id()
        self._run_budget[execution_id.value] = _RunBudget(max_calls=self._budget.max_tool_calls)
        start = time.monotonic()
        try:
            # Overall runtime deadline wraps the whole deterministic graph
            # (including any bounded retry attempts).
            result = await asyncio.wait_for(
                self._run_attempts(command, execution_id, start),
                timeout=self._budget.max_runtime_seconds,
            )
            return result
        except asyncio.CancelledError:
            # Cancellation never converts to success. Clean up carriers and let
            # the cancellation propagate so the caller knows the graph was halted.
            raise
        except TimeoutError:
            duration_ms = _duration_ms(start)
            return self._failure_result(
                execution_id,
                InvestigationExecutionErrorCode.EXECUTION_TIMEOUT,
                telemetry=self._pop_telemetry(execution_id.value),
                duration_ms=duration_ms,
            )
        except Exception:
            duration_ms = _duration_ms(start)
            return self._failure_result(
                execution_id,
                InvestigationExecutionErrorCode.ADK_RUNTIME_EXCEPTION,
                telemetry=self._pop_telemetry(execution_id.value),
                duration_ms=duration_ms,
            )
        finally:
            # Every terminal path (success, blocked, deterministic failure,
            # wrapper failure, retry exhaustion, timeout, cancellation, ADK
            # runtime failure) releases all run-scoped carriers here. The
            # returned EventInvocationResult already holds the popped
            # metadata/branch records/joined result, so cleanup is safe.
            self._cleanup(execution_id.value)

    async def _run_attempts(
        self,
        command: EventInvestigationCommand,
        execution_id: InvestigationExecutionId,
        start: float,
    ) -> EventInvocationResult:
        """Run the deterministic graph across a bounded number of logical attempts."""
        max_attempts = max(1, self._budget.max_loop_iterations)
        for attempt_number in range(1, max_attempts + 1):
            graph_attempt = GraphAttemptId(attempt_number)
            telemetry = _RunTelemetry()
            self._run_telemetry[execution_id.value] = telemetry
            session_id = self._new_session_id()
            invocation_id = self._new_invocation_id()
            envelope = self._build_envelope(
                command, execution_id, session_id, invocation_id, graph_attempt
            )
            self._last_attempt[execution_id.value] = (session_id, invocation_id, dict(envelope))
            terminal = await self._run_graph(
                envelope, telemetry, session_id, invocation_id, graph_attempt
            )
            duration_ms = _duration_ms(start)
            result = self._interpret(
                terminal,
                execution_id=execution_id,
                session_id=session_id,
                invocation_id=invocation_id,
                envelope=envelope,
                telemetry=telemetry,
                duration_ms=duration_ms,
            )
            if result.outcome.is_success or not self._is_retryable(result):
                return result
            # Retryable failure.
            if attempt_number == max_attempts:
                # No budget left to retry. A single-attempt budget surfaces the
                # actual transparent failure; a multi-attempt retry budget that
                # still fails is terminal retry exhaustion.
                if max_attempts == 1:
                    return result
                # Terminal retry exhaustion: surface the typed failure while
                # preserving the last attempt's joined snapshot + telemetry so
                # downstream sees a truthful non-ready context.
                exhausted = EventInvocationResult(
                    outcome=InvestigationExecutionOutcome.FAILED,
                    execution_id=execution_id,
                    metadata=result.metadata,
                    capability_result=result.capability_result,
                    failure_code=InvestigationExecutionErrorCode.GRAPH_RETRY_EXHAUSTED,
                    joined_investigation=result.joined_investigation,
                    branch_records=result.branch_records,
                )
                self._cleanup(execution_id.value)
                return exhausted
        # Unreachable (range is non-empty); defensive.
        return self._failure_result(
            execution_id,
            InvestigationExecutionErrorCode.GRAPH_RETRY_EXHAUSTED,
            telemetry=self._pop_telemetry(execution_id.value),
            duration_ms=_duration_ms(start),
        )

    def execute_primitive(self, data: Mapping[str, object]) -> EventInvocationResult:
        """Synchronous convenience wrapper around :meth:`execute_primitive_async`."""
        return asyncio.run(self.execute_primitive_async(data))

    async def execute_primitive_async(self, data: Mapping[str, object]) -> EventInvocationResult:
        """Build a command from a primitive event payload, failing closed on malformed input."""
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
        graph_attempt: GraphAttemptId,
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
            "graph_attempt": graph_attempt.value,
        }

    def _construct_message(self, envelope: Mapping[str, object]) -> types.Content:
        """Construct the ADK carrier message from the machine envelope."""
        return types.Content(
            role="user",
            parts=[types.Part(text=json.dumps(envelope, sort_keys=True, separators=(",", ":")))],
        )

    def _make_context_node(self) -> FunctionNode:
        """Build the thin context FunctionNode wrapper (all-deterministic, no model)."""

        async def context_node(ctx: Context, node_input: object) -> dict[str, object]:
            del ctx
            return await self._run_context_node(node_input)

        return FunctionNode(func=context_node, name="get_investigation_context")

    def _make_profile_node(self) -> FunctionNode:
        async def profile_node(ctx: Context, node_input: object) -> dict[str, object]:
            del ctx
            return await self._run_profile_node(node_input)

        return FunctionNode(func=profile_node, name="profile_comparison")

    def _make_baseline_node(self) -> FunctionNode:
        async def baseline_node(ctx: Context, node_input: object) -> dict[str, object]:
            del ctx
            return await self._run_baseline_node(node_input)

        return FunctionNode(func=baseline_node, name="baseline_summary")

    def _make_missingness_node(self) -> FunctionNode:
        async def missingness_node(ctx: Context, node_input: object) -> dict[str, object]:
            del ctx
            return await self._run_missingness_node(node_input)

        return FunctionNode(func=missingness_node, name="missingness_assessment")

    def _make_join_node(self) -> FunctionNode:
        async def join_node(ctx: Context, node_input: object) -> dict[str, object]:
            del ctx
            return await self._run_join_node(node_input)

        return FunctionNode(func=join_node, name="join_investigation")

    async def _run_graph(
        self,
        envelope: Mapping[str, object],
        telemetry: _RunTelemetry,
        session_id: str,
        invocation_id: str,
        graph_attempt: GraphAttemptId,
    ) -> dict[str, object] | None:
        """Run the real pinned ADK fan-out/join workflow and return the terminal payload."""
        context_node = self._make_context_node()
        profile_node = self._make_profile_node()
        baseline_node = self._make_baseline_node()
        missingness_node = self._make_missingness_node()
        join_barrier = JoinNode(name="investigation_join_barrier")
        join_node = self._make_join_node()
        workflow = Workflow(
            name="ngabo_investigation_graph",
            edges=[
                (
                    "START",
                    context_node,
                    (profile_node, baseline_node, missingness_node),
                    join_barrier,
                    join_node,
                )
            ],
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
        if terminal is None:
            return None
        return terminal

    # -- node wrappers -----------------------------------------------------------------

    async def _run_context_node(self, node_input: object) -> dict[str, object]:
        """Fetch canonical context and produce one immutable fan-out input snapshot."""
        envelope = self._extract_envelope(node_input)
        execution_id = str(envelope.get("execution_id")) if envelope is not None else None
        telemetry = (
            self._run_telemetry[execution_id]
            if execution_id is not None and execution_id in self._run_telemetry
            else _RunTelemetry()
        )
        telemetry.wrapper_calls += 1
        telemetry.model_calls += 0  # deterministic path: no model call
        budget = self._run_budget.get(execution_id) if execution_id is not None else None
        snapshot = self._snapshot_fields(envelope)
        if envelope is None:
            return self._context_blocked_payload(
                envelope,
                InvestigationExecutionOutcome.FAILED,
                InvestigationExecutionErrorCode.MALFORMED_COMMAND,
                telemetry,
                snapshot,
            )

        try:
            incident_id = IncidentId(str(envelope["incident_id"]))
            requested_version = IncidentVersion(
                _as_int(envelope["incident_version"], "incident_version")
            )
            requested_watermark = SourceWatermark(str(envelope["source_watermark"]))
            query = GetInvestigationContextQuery(
                incident_id=incident_id,
                requested_version=requested_version,
            )
            if budget is not None and not budget.try_acquire():
                return self._context_blocked_payload(
                    envelope,
                    InvestigationExecutionOutcome.FAILED,
                    InvestigationExecutionErrorCode.EXECUTION_BUDGET_EXCEEDED,
                    telemetry,
                    snapshot,
                )
            context_result = await self._await_daemon_sync(lambda: self._get_context(query))
        except Exception as exc:  # noqa: BLE001 - fail closed on a wrapper exception
            return self._context_blocked_payload(
                envelope,
                InvestigationExecutionOutcome.FAILED,
                InvestigationExecutionErrorCode.WRAPPER_EXCEPTION,
                telemetry,
                snapshot,
                detail=type(exc).__name__,
            )

        if execution_id is not None:
            self._capability_results[execution_id] = context_result

        mapping = self._map_context(context_result, requested_watermark)
        if mapping.outcome is not InvestigationExecutionOutcome.COMPLETED_CURRENT_STAGE:
            return self._context_blocked_payload(
                envelope,
                mapping.outcome,
                mapping.failure_code,
                telemetry,
                snapshot,
                capability_outcome=context_result.outcome.value,
            )

        try:
            graph_attempt = GraphAttemptId(_as_int(envelope.get("graph_attempt"), "graph_attempt"))
            investigation_input = self._build_investigation_input(context_result, graph_attempt)
        except ValueError:
            return self._context_blocked_payload(
                envelope,
                InvestigationExecutionOutcome.BLOCKED,
                InvestigationExecutionErrorCode.REQUIRED_INPUT_UNAVAILABLE,
                telemetry,
                snapshot,
                capability_outcome=context_result.outcome.value,
            )

        return {
            "context_ready": True,
            "investigation_input": investigation_input,
            "capability_outcome": context_result.outcome.value,
            "execution_id": execution_id,
            **snapshot,
        }

    async def _run_profile_node(self, node_input: object) -> dict[str, object]:
        return await self._run_branch(
            node_input,
            BranchIdentity.PROFILE,
            self._compare_profiles,
            lambda inv: CompareProfilesQuery(
                incident_id=inv.incident_id,
                isolate_id_a=inv.isolate_id_a,
                isolate_id_b=inv.isolate_id_b,
                requested_version=inv.incident_version,
            ),
            lambda result, inv: (
                result.incident_id == inv.incident_id
                and result.incident_version == inv.incident_version
                and result.source_watermark == inv.source_watermark
                # Scientific input binding: the reported pair must be the exact
                # canonicalized comparison pair from DeterministicInvestigationInput.
                # CompareResistanceProfiles canonicalizes the unordered pair to a
                # sorted A/B identity, matching the canonicalized input pair.
                and result.isolate_id_a == inv.isolate_id_a
                and result.isolate_id_b == inv.isolate_id_b
            ),
        )

    async def _run_baseline_node(self, node_input: object) -> dict[str, object]:
        return await self._run_branch(
            node_input,
            BranchIdentity.BASELINE,
            self._get_baseline_summary,
            lambda inv: GetBaselineSummaryQuery(
                incident_id=inv.incident_id,
                organism_code=inv.organism_code,
                facility_id=inv.facility_id,
                ward=inv.ward,
                requested_version=inv.incident_version,
            ),
            lambda result, inv: (
                result.incident_id == inv.incident_id
                and result.incident_version == inv.incident_version
                and result.source_watermark == inv.source_watermark
                # Scientific input binding: the reported cohort dimensions must be
                # the exact deterministic cohort identity from the fan-out input.
                and result.organism_code == inv.organism_code
                and result.facility_id == inv.facility_id
                and result.ward == inv.ward
            ),
        )

    async def _run_missingness_node(self, node_input: object) -> dict[str, object]:
        return await self._run_branch(
            node_input,
            BranchIdentity.MISSINGNESS,
            self._assess_missingness,
            lambda inv: AssessMissingnessQuery(
                incident_id=inv.incident_id,
                required_isolate_ids=inv.required_isolate_ids,
                requested_version=inv.incident_version,
            ),
            lambda result, inv: (
                result.incident_id == inv.incident_id
                and result.incident_version == inv.incident_version
                and result.source_watermark == inv.source_watermark
            ),
        )

    async def _run_branch(
        self,
        node_input: object,
        branch: BranchIdentity,
        handler: Callable[..., Any],
        query_builder: Callable[[DeterministicInvestigationInput], Any],
        binding_ok: Callable[[Any, DeterministicInvestigationInput], bool],
    ) -> dict[str, object]:
        """Run one required deterministic branch via a thin wrapper (no science)."""
        payload = self._branch_input(node_input)
        execution_id = str(payload.get("execution_id")) if payload is not None else None
        telemetry = (
            self._run_telemetry[execution_id]
            if execution_id is not None and execution_id in self._run_telemetry
            else _RunTelemetry()
        )
        state = telemetry.branch_state(branch)
        state["started"] = True
        started_monotonic = time.monotonic()
        state["start_monotonic"] = started_monotonic
        telemetry.model_calls += 0
        budget = self._run_budget.get(execution_id) if execution_id is not None else None

        context_ready = bool(payload.get("context_ready")) if payload is not None else False
        investigation_input = (
            payload.get("investigation_input") if payload is not None else None
        )
        if not context_ready or not isinstance(
            investigation_input, DeterministicInvestigationInput
        ):
            state["blocked"] = True
            state["duration_ms"] = _duration_ms(started_monotonic)
            return self._branch_payload(
                branch,
                self._context_outcome(payload),
                self._context_failure_code(payload),
                None,
                state,
                payload,
                invoked=False,
                binding_ok=None,
            )

        if budget is not None and not budget.try_acquire():
            # Hard per-run tool budget exhausted before this branch handler is
            # invoked: fail closed and never report the branch as executed.
            state["blocked"] = True
            state["duration_ms"] = _duration_ms(started_monotonic)
            return self._branch_payload(
                branch,
                InvestigationExecutionOutcome.FAILED,
                InvestigationExecutionErrorCode.EXECUTION_BUDGET_EXCEEDED,
                None,
                state,
                payload,
                invoked=False,
                binding_ok=None,
            )

        state["invocation_count"] = cast(int, state["invocation_count"]) + 1
        try:
            query = query_builder(investigation_input)
            result = await self._await_daemon_sync(lambda: handler(query))
        except Exception:
            state["failed"] = True
            state["duration_ms"] = _duration_ms(started_monotonic)
            return self._branch_payload(
                branch,
                InvestigationExecutionOutcome.FAILED,
                InvestigationExecutionErrorCode.WRAPPER_EXCEPTION,
                None,
                state,
                payload,
                invoked=True,
                binding_ok=None,
            )

        state["completed"] = True
        state["duration_ms"] = _duration_ms(started_monotonic)
        capability_outcome = getattr(result, "outcome", None)
        state["capability_outcome"] = (
            capability_outcome.value if capability_outcome is not None else None
        )
        if (
            isinstance(capability_outcome, CapabilityOutcome)
            and capability_outcome is CapabilityOutcome.SUCCESS
        ):
            if not binding_ok(result, investigation_input):
                state["blocked"] = True
                state["failed"] = False
                return self._branch_payload(
                    branch,
                    InvestigationExecutionOutcome.BLOCKED,
                    InvestigationExecutionErrorCode.BRANCH_BINDING_MISMATCH,
                    result,
                    state,
                    payload,
                    invoked=True,
                    binding_ok=False,
                )
            return self._branch_payload(
                branch,
                InvestigationExecutionOutcome.COMPLETED_CURRENT_STAGE,
                None,
                result,
                state,
                payload,
                invoked=True,
                binding_ok=True,
            )

        state["blocked"] = True
        return self._branch_payload(
            branch,
            InvestigationExecutionOutcome.BLOCKED,
            InvestigationExecutionErrorCode.REQUIRED_BRANCH_FAILED,
            result,
            state,
            payload,
            invoked=True,
            binding_ok=None,
        )

    async def _run_join_node(self, node_input: object) -> dict[str, object]:
        """Deterministically join the three required branch results."""
        by_branch: dict[str, dict[str, object]] = {}
        if isinstance(node_input, Mapping):
            for key, value in node_input.items():
                if isinstance(value, dict):
                    by_branch[key] = value
        payloads = self._branch_payloads_for_join(by_branch)
        if payloads is None:
            return self._failed_terminal(None)

        reference = next((p for p in payloads if p), None)
        if reference is None:
            return self._failed_terminal(None)
        execution_id = str(reference.get("execution_id")) if reference.get("execution_id") else None
        telemetry = (
            self._run_telemetry[execution_id]
            if execution_id is not None and execution_id in self._run_telemetry
            else _RunTelemetry()
        )
        telemetry.model_calls += 0

        investigation_input = reference.get("investigation_input") if reference else None
        context_ready = bool(reference.get("context_ready")) if reference else False
        if not context_ready or not isinstance(
            investigation_input, DeterministicInvestigationInput
        ):
            failure_code = self._context_failure_code(reference)
            outcome = self._context_outcome(reference)
            return self._terminal(outcome, failure_code, None, execution_id, reference)

        branch_results: dict[BranchIdentity, object] = {}
        binding_all_ok = True
        outcomes_all_ok = True
        wrapper_failure = False
        budget_exceeded = False
        for branch in REQUIRED_BRANCH_IDENTITIES:
            branch_payload = self._payload_for_branch(payloads, branch)
            if branch_payload is None:
                return self._failed_terminal(execution_id)
            result = branch_payload.get("result")
            branch_results[branch] = result
            branch_outcome = branch_payload.get("outcome")
            if branch_outcome != InvestigationExecutionOutcome.COMPLETED_CURRENT_STAGE.value:
                outcomes_all_ok = False
            if branch_payload.get("binding_ok") is False:
                binding_all_ok = False
            branch_failure = branch_payload.get("failure_code")
            if branch_failure == InvestigationExecutionErrorCode.WRAPPER_EXCEPTION.value:
                wrapper_failure = True
            if branch_failure == InvestigationExecutionErrorCode.EXECUTION_BUDGET_EXCEEDED.value:
                budget_exceeded = True

        profile_result = self._as_profile_result(branch_results.get(BranchIdentity.PROFILE))
        baseline_result = self._as_baseline_result(branch_results.get(BranchIdentity.BASELINE))
        missingness_result = self._as_missingness_result(
            branch_results.get(BranchIdentity.MISSINGNESS)
        )
        all_results_present = (
            profile_result is not None
            and baseline_result is not None
            and missingness_result is not None
        )
        ready = (
            context_ready
            and binding_all_ok
            and outcomes_all_ok
            and all_results_present
            and not budget_exceeded
        )
        failure_code = self._resolve_join_failure_code(
            payloads, wrapper_failure, budget_exceeded, binding_all_ok, outcomes_all_ok
        )
        joined = JoinedInvestigationContext(
            incident_id=investigation_input.incident_id,
            incident_version=investigation_input.incident_version,
            source_watermark=investigation_input.source_watermark,
            graph_attempt=investigation_input.graph_attempt,
            profile_result=profile_result,
            baseline_result=baseline_result,
            missingness_result=missingness_result,
            ready_for_downstream=ready,
            failure_code=failure_code,
            model_calls=telemetry.model_calls,
        )
        if execution_id is not None:
            self._joined_results[execution_id] = joined
        outcome = (
            InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
            if ready
            else (
                InvestigationExecutionOutcome.FAILED
                if failure_code
                in (
                    InvestigationExecutionErrorCode.WRAPPER_EXCEPTION,
                    InvestigationExecutionErrorCode.ADK_RUNTIME_EXCEPTION,
                    InvestigationExecutionErrorCode.EXECUTION_BUDGET_EXCEEDED,
                )
                else InvestigationExecutionOutcome.BLOCKED
            )
        )
        return self._terminal(outcome, failure_code, joined, execution_id, reference)

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
            return self._failure_result(
                execution_id,
                InvestigationExecutionErrorCode.ADK_RUNTIME_EXCEPTION,
                telemetry=telemetry,
                duration_ms=duration_ms,
            )

        outcome = InvestigationExecutionOutcome(str(terminal.get("outcome")))
        raw_failure = terminal.get("failure_code")
        failure_code = (
            InvestigationExecutionErrorCode(str(raw_failure)) if raw_failure is not None else None
        )
        capability_result = self._pop_capability_result(execution_id.value)
        joined = self._pop_joined_result(execution_id.value)
        metadata = self._build_metadata(
            execution_id=execution_id,
            session_id=session_id,
            invocation_id=invocation_id,
            envelope=envelope,
            telemetry=telemetry,
            duration_ms=duration_ms,
            capability_result=capability_result,
        )
        result = EventInvocationResult(
            outcome=outcome,
            execution_id=execution_id,
            metadata=metadata,
            capability_result=capability_result,
            failure_code=failure_code,
            joined_investigation=joined,
            branch_records=self._build_branch_records(telemetry),
        )
        if outcome.is_success and joined is not None and joined.ready_for_downstream is not True:
            return self._failure_result(
                execution_id,
                InvestigationExecutionErrorCode.ADK_RUNTIME_EXCEPTION,
                telemetry=telemetry,
                duration_ms=duration_ms,
            )
        return result

    def _failure_result(
        self,
        execution_id: InvestigationExecutionId,
        code: InvestigationExecutionErrorCode,
        *,
        telemetry: _RunTelemetry | None = None,
        duration_ms: int = 0,
    ) -> EventInvocationResult:
        capability_result = self._pop_capability_result(execution_id.value)
        joined = self._pop_joined_result(execution_id.value)
        telemetry = telemetry or _RunTelemetry()
        last_attempt = self._last_attempt.pop(execution_id.value, None)
        if last_attempt is not None:
            session_id, invocation_id, envelope = last_attempt
            metadata = self._build_metadata(
                execution_id=execution_id,
                session_id=session_id,
                invocation_id=invocation_id,
                envelope=envelope,
                telemetry=telemetry,
                duration_ms=duration_ms,
                capability_result=capability_result,
            )
        else:
            metadata = None
        result = EventInvocationResult(
            outcome=InvestigationExecutionOutcome.FAILED,
            execution_id=execution_id,
            metadata=metadata,
            capability_result=capability_result,
            failure_code=code,
            joined_investigation=joined,
            branch_records=self._build_branch_records(telemetry),
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
        capability_result: InvestigationContextResult | None = None,
    ) -> ADKExecutionMetadata:
        canonical_watermark: SourceWatermark
        if capability_result is not None and capability_result.source_watermark is not None:
            canonical_watermark = capability_result.source_watermark
        else:
            canonical_watermark = SourceWatermark(str(envelope["source_watermark"]))
        run_budget = self._run_budget.get(execution_id.value)
        tool_calls = run_budget.used if run_budget is not None else telemetry.tool_calls
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
            source_watermark=canonical_watermark,
            wrapper_calls=telemetry.wrapper_calls,
            model_calls=telemetry.model_calls,
            tool_calls=tool_calls,
            duration_ms=duration_ms,
            budget=self._budget,
            adk_version=self._adk_version,
        )

    def _map_context(
        self,
        result: InvestigationContextResult,
        requested_watermark: SourceWatermark,
    ) -> _CapabilityMapping:
        if result.outcome is CapabilityOutcome.SUCCESS:
            if result.source_watermark != requested_watermark:
                return _CapabilityMapping(
                    InvestigationExecutionOutcome.BLOCKED,
                    InvestigationExecutionErrorCode.SOURCE_WATERMARK_MISMATCH,
                )
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

    # -- input preparation -------------------------------------------------------------

    def _build_investigation_input(
        self,
        context_result: InvestigationContextResult,
        graph_attempt: GraphAttemptId,
    ) -> DeterministicInvestigationInput:
        """Derive ONE unambiguous deterministic fan-out input.

        The fan-out input preserves the COMPLETE canonical investigation cohort
        (all isolates) and derives a deterministic profile-comparison pair from
        canonical signal/context data:

        - if the canonical context carries an explicit governed
          ``profile_comparison_isolate_ids`` (the signal's primary phenotype pair,
          e.g. "ISO-031"/"ISO-034" for the canonical hero), that pair is used;
        - otherwise, if the cohort has exactly two isolates, those two are the pair;
        - otherwise the intended pair cannot be determined unambiguously and the
          runtime fails closed with REQUIRED_INPUT_UNAVAILABLE (no "first two",
          "best pair", or model-selected heuristic is invented here).

        The baseline cohort must be homogeneous on organism/facility/ward, and the
        missingness branch operates against the full required isolate cohort.
        """
        if context_result.incident_id is None or context_result.incident_version is None:
            raise ValueError("context result lacks canonical incident identity")
        if context_result.source_watermark is None:
            raise ValueError("context result lacks a canonical source watermark")
        isolates = context_result.isolates
        if not isolates:
            raise ValueError("incident cohort is empty")
        provided_pair = context_result.profile_comparison_isolate_ids
        if provided_pair is not None:
            pair_a, pair_b = provided_pair
        elif len(isolates) == 2:
            pair_a, pair_b = isolates[0].isolate_id, isolates[1].isolate_id
        else:
            raise ValueError(
                "the intended profile comparison pair cannot be derived "
                f"unambiguously from a {len(isolates)}-isolate cohort"
            )
        by_id = {iso.isolate_id: iso for iso in isolates}
        if pair_a not in by_id or pair_b not in by_id or pair_a == pair_b:
            raise ValueError("the canonical profile comparison pair is not a valid cohort pair")
        isolate_id_a, isolate_id_b = sorted((pair_a, pair_b))
        organism_code = by_id[isolate_id_a].organism_code
        facility_id = by_id[isolate_id_a].facility_id
        ward = by_id[isolate_id_a].ward
        for iso in isolates:
            if (
                iso.organism_code != organism_code
                or iso.facility_id != facility_id
                or iso.ward != ward
            ):
                raise ValueError("incident cohort is not homogeneous on organism/facility/ward")
        return DeterministicInvestigationInput(
            incident_id=context_result.incident_id,
            incident_version=context_result.incident_version,
            source_watermark=context_result.source_watermark,
            graph_attempt=graph_attempt,
            isolate_id_a=isolate_id_a,
            isolate_id_b=isolate_id_b,
            organism_code=organism_code,
            facility_id=facility_id,
            ward=ward,
            required_isolate_ids=tuple(sorted(iso.isolate_id for iso in isolates)),
        )

    # -- helpers -----------------------------------------------------------------------

    async def _await_daemon_sync(self, thunk: Callable[[], _T]) -> _T:
        """Await a synchronous thunk on a daemon thread with thread-safe Future delivery."""
        loop = asyncio.get_running_loop()
        future: asyncio.Future[_T] = loop.create_future()

        def deliver_result(result: _T) -> None:
            if future.done() or future.cancelled():
                return
            future.set_result(result)

        def deliver_exception(exc: Exception) -> None:
            if future.done() or future.cancelled():
                return
            future.set_exception(exc)

        def worker() -> None:
            try:
                result = thunk()
            except Exception as exc:  # noqa: BLE001 - captured and re-raised on await
                with suppress(RuntimeError):
                    loop.call_soon_threadsafe(deliver_exception, exc)
            else:
                with suppress(RuntimeError):
                    loop.call_soon_threadsafe(deliver_result, result)

        threading.Thread(target=worker, daemon=True).start()
        return await future

    def _build_branch_records(self, telemetry: _RunTelemetry) -> tuple[BranchRunRecord, ...]:
        records: list[BranchRunRecord] = []
        for branch in REQUIRED_BRANCH_IDENTITIES:
            state = telemetry.branches.get(branch.value, {})
            started = bool(state.get("started", False))
            completed = bool(state.get("completed", False))
            blocked = bool(state.get("blocked", False))
            failed = bool(state.get("failed", False))
            timed_out = started and not completed and not blocked and not failed
            records.append(
                BranchRunRecord(
                    branch=branch,
                    required=True,
                    started=started,
                    completed=completed,
                    blocked=blocked,
                    failed=failed,
                    timed_out=timed_out,
                    invocation_count=cast(int, state.get("invocation_count", 0)),
                    capability_outcome=(
                        str(state["capability_outcome"])
                        if state.get("capability_outcome") is not None
                        else None
                    ),
                    duration_ms=cast(int, state.get("duration_ms", 0)),
                )
            )
        return tuple(records)

    def _resolve_join_failure_code(
        self,
        payloads: list[dict[str, object]],
        wrapper_failure: bool,
        budget_exceeded: bool,
        binding_all_ok: bool,
        outcomes_all_ok: bool,
    ) -> InvestigationExecutionErrorCode | None:
        del payloads
        if wrapper_failure:
            return InvestigationExecutionErrorCode.WRAPPER_EXCEPTION
        if budget_exceeded:
            return InvestigationExecutionErrorCode.EXECUTION_BUDGET_EXCEEDED
        if not binding_all_ok:
            return InvestigationExecutionErrorCode.BRANCH_BINDING_MISMATCH
        if not outcomes_all_ok:
            return InvestigationExecutionErrorCode.REQUIRED_BRANCH_FAILED
        return None

    @staticmethod
    def _is_retryable(result: EventInvocationResult) -> bool:
        return result.failure_code in (
            InvestigationExecutionErrorCode.WRAPPER_EXCEPTION,
            InvestigationExecutionErrorCode.ADK_RUNTIME_EXCEPTION,
        )

    def _snapshot_fields(self, envelope: Mapping[str, object] | None) -> dict[str, object]:
        if envelope is None:
            return {}
        return {
            "execution_id": envelope.get("execution_id"),
            "session_id": envelope.get("session_id"),
            "invocation_id": envelope.get("invocation_id"),
            "event_id": envelope.get("event_id"),
            "correlation_id": envelope.get("correlation_id"),
            "incident_id": envelope.get("incident_id"),
            "incident_version": envelope.get("incident_version"),
            "source_watermark": envelope.get("source_watermark"),
            "graph_attempt": envelope.get("graph_attempt"),
        }

    def _context_blocked_payload(
        self,
        envelope: Mapping[str, object] | None,
        outcome: InvestigationExecutionOutcome,
        failure_code: InvestigationExecutionErrorCode | None,
        telemetry: _RunTelemetry,
        snapshot: dict[str, object],
        *,
        capability_outcome: str | None = None,
        detail: str | None = None,
    ) -> dict[str, object]:
        del envelope, telemetry
        payload: dict[str, object] = {
            "context_ready": False,
            "outcome": outcome.value,
            "failure_code": failure_code.value if failure_code is not None else None,
            "capability_outcome": capability_outcome,
            **snapshot,
        }
        if detail is not None:
            payload["detail"] = detail
        return payload

    def _branch_input(self, node_input: object) -> dict[str, object] | None:
        if isinstance(node_input, Mapping):
            return dict(node_input)
        if isinstance(node_input, types.Content):
            text = "".join(getattr(part, "text", "") or "" for part in (node_input.parts or ()))
            if text:
                try:
                    parsed = json.loads(text)
                except (ValueError, TypeError):
                    return None
                if isinstance(parsed, dict):
                    return parsed
        return None

    def _branch_payload(
        self,
        branch: BranchIdentity,
        outcome: InvestigationExecutionOutcome,
        failure_code: InvestigationExecutionErrorCode | None,
        result: object | None,
        state: dict[str, object],
        parent: dict[str, object] | None,
        *,
        invoked: bool,
        binding_ok: bool | None,
    ) -> dict[str, object]:
        del invoked
        payload: dict[str, object] = {
            "branch": branch.value,
            "outcome": outcome.value,
            "failure_code": failure_code.value if failure_code is not None else None,
            "result": result,
            "context_ready": bool(parent.get("context_ready")) if parent else False,
            "investigation_input": parent.get("investigation_input") if parent else None,
            "binding_ok": binding_ok,
            "invocation_count": state.get("invocation_count", 0),
            "branch_started": state.get("started", False),
            "branch_completed": state.get("completed", False),
            "branch_failed": state.get("failed", False),
            "branch_blocked": state.get("blocked", False),
            "branch_duration_ms": state.get("duration_ms", 0),
        }
        if parent is not None:
            for key in (
                "execution_id",
                "session_id",
                "invocation_id",
                "event_id",
                "correlation_id",
                "incident_id",
                "incident_version",
                "source_watermark",
                "graph_attempt",
            ):
                if key in parent:
                    payload[key] = parent[key]
        return payload

    def _branch_payloads_for_join(
        self, by_branch: dict[str, dict[str, object]]
    ) -> list[dict[str, object]] | None:
        branch_node_names = (
            "profile_comparison",
            "baseline_summary",
            "missingness_assessment",
        )
        payloads: list[dict[str, object]] = []
        for node_name in branch_node_names:
            payload = by_branch.get(node_name)
            if payload is None:
                return None
            payloads.append(payload)
        return payloads

    def _payload_for_branch(
        self, payloads: list[dict[str, object]], branch: BranchIdentity
    ) -> dict[str, object] | None:
        by_branch = {
            BranchIdentity.PROFILE: payloads[0],
            BranchIdentity.BASELINE: payloads[1],
            BranchIdentity.MISSINGNESS: payloads[2],
        }
        return by_branch.get(branch)

    @staticmethod
    def _context_failure_code(
        payload: Mapping[str, object] | None,
    ) -> InvestigationExecutionErrorCode | None:
        if payload is None:
            return None
        value = payload.get("failure_code")
        if value is None:
            return None
        try:
            return InvestigationExecutionErrorCode(str(value))
        except ValueError:
            return None

    @staticmethod
    def _context_outcome(
        payload: Mapping[str, object] | None,
    ) -> InvestigationExecutionOutcome:
        if payload is not None:
            raw = payload.get("outcome")
            if isinstance(raw, str):
                try:
                    return InvestigationExecutionOutcome(raw)
                except ValueError:
                    pass
        return InvestigationExecutionOutcome.BLOCKED

    def _terminal(
        self,
        outcome: InvestigationExecutionOutcome,
        failure_code: InvestigationExecutionErrorCode | None,
        joined: JoinedInvestigationContext | None,
        execution_id: str | None,
        reference: Mapping[str, object] | None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "_ngabo_result": True,
            "outcome": outcome.value,
            "failure_code": failure_code.value if failure_code is not None else None,
            "execution_id": execution_id,
            "joined_ready": joined.ready_for_downstream if joined is not None else None,
        }
        if reference is not None:
            for key in (
                "session_id",
                "invocation_id",
                "event_id",
                "correlation_id",
                "incident_id",
                "incident_version",
                "source_watermark",
                "graph_attempt",
            ):
                if key in reference:
                    payload[key] = reference[key]
        return payload

    def _failed_terminal(self, execution_id: str | None) -> dict[str, object]:
        return self._terminal(
            InvestigationExecutionOutcome.FAILED,
            InvestigationExecutionErrorCode.ADK_RUNTIME_EXCEPTION,
            None,
            execution_id,
            None,
        )

    def _extract_envelope(self, node_input: object) -> dict[str, object] | None:
        """Extract the machine event envelope from the ADK node input."""
        text: str | None = None
        if isinstance(node_input, types.Content):
            text = "".join(getattr(part, "text", "") or "" for part in (node_input.parts or ()))
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

    def _pop_joined_result(self, execution_id: str) -> JoinedInvestigationContext | None:
        return self._joined_results.pop(execution_id, None)

    def _pop_telemetry(self, execution_id: str) -> _RunTelemetry:
        return self._run_telemetry.pop(execution_id, _RunTelemetry())

    def _cleanup(self, execution_id: str) -> None:
        self._capability_results.pop(execution_id, None)
        self._joined_results.pop(execution_id, None)
        self._run_telemetry.pop(execution_id, None)
        self._run_budget.pop(execution_id, None)
        self._last_attempt.pop(execution_id, None)

    @staticmethod
    def _new_execution_id() -> InvestigationExecutionId:
        return InvestigationExecutionId(f"RUN-{uuid.uuid4().hex}")

    @staticmethod
    def _new_session_id() -> str:
        return f"ngabo-session-{uuid.uuid4().hex}"

    @staticmethod
    def _new_invocation_id() -> str:
        return f"ngabo-invocation-{uuid.uuid4().hex}"

    @staticmethod
    def _as_profile_result(value: object) -> ProfileComparisonResult | None:
        return value if isinstance(value, ProfileComparisonResult) else None

    @staticmethod
    def _as_baseline_result(value: object) -> BaselineSummaryResult | None:
        return value if isinstance(value, BaselineSummaryResult) else None

    @staticmethod
    def _as_missingness_result(value: object) -> MissingnessResult | None:
        return value if isinstance(value, MissingnessResult) else None


def _duration_ms(start_monotonic: float) -> int:
    elapsed = (time.monotonic() - start_monotonic) * 1000.0
    return int(round(elapsed))


def _as_int(value: object, label: str) -> int:
    """Return an int from a primitive envelope field, failing closed on non-int."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value
