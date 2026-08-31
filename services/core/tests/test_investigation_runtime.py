"""Focused tests for the Issue #53 event-invoked ADK outer execution adapter.

These exercise the REAL pinned ``google-adk`` ``Runner`` / ``Workflow`` /
``FunctionNode`` runtime (asserted to be the certified 2.8.0), with a
deterministic in-memory inward capability and dependency injection. No live
Gemini call, no interactive chat, no ADK Web, no cloud persistence.

They prove the outer boundary: event-shaped command -> adapter -> ADK runtime ->
thin wrapper -> typed inward result -> structured outcome; budgets/identifiers
observable; timeout enforced; failure can never be mislabeled as package
completion; and no raw persistence / scientific logic in the wrapper.
"""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

import pytest

from ngabo.application.enums.capability_outcome import CapabilityOutcome
from ngabo.application.enums.investigation_execution_error_code import (
    InvestigationExecutionErrorCode,
)
from ngabo.application.enums.investigation_execution_outcome import (
    InvestigationExecutionOutcome,
)
from ngabo.application.use_cases.assess_material_missingness import (
    AssessMaterialMissingness,
)
from ngabo.application.use_cases.compare_resistance_profiles import (
    CompareResistanceProfiles,
)
from ngabo.application.use_cases.get_baseline_summary import (
    GetBaselineSummary,
)
from ngabo.application.use_cases.get_investigation_context import (
    GetInvestigationContext,
)
from ngabo.application.value_objects.investigation_context import (
    GetInvestigationContextQuery,
    InvestigationContextResult,
    StoredIncidentContext,
)
from ngabo.application.value_objects.investigation_execution import (
    ADKExecutionMetadata,
    EventInvestigationCommand,
    EventInvocationResult,
    InvestigationExecutionId,
    InvestigationRuntimeBudget,
)
from ngabo.domain.entities.ast_observation import AstObservation
from ngabo.domain.entities.canonical_isolate import CanonicalIsolate
from ngabo.domain.enums.interpretation import Interpretation
from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.signal_config import SignalConfig
from ngabo.domain.value_objects.source_watermark import SourceWatermark
from ngabo.infrastructure.adk.investigation_runtime import (
    DEFAULT_APP_NAME,
    EventInvestigationRuntime,
    detect_google_adk_version,
)

INCIDENT_1 = IncidentId("INC-001")
INCIDENT_2 = IncidentId("INC-002")
VERSION_1 = IncidentVersion(1)
VERSION_2 = IncidentVersion(2)
WATERMARK = SourceWatermark("ngabo-source-v1:sha256:abc123")
WINDOW_END = date(2026, 8, 17)
COHORT_ORG = "kle"
COHORT_FACILITY = "SYNTH-FACILITY-001"
COHORT_WARD = "SYNTH-WARD-A"


def _make_isolate(isolate_id: str, *, collection_date: date = WINDOW_END) -> CanonicalIsolate:
    ast = {
        "AMK": Interpretation.SUSCEPTIBLE,
        "CAZ": Interpretation.RESISTANT,
        "CIP": Interpretation.RESISTANT,
        "CRO": Interpretation.RESISTANT,
        "MEM": Interpretation.RESISTANT,
        "SXT": Interpretation.RESISTANT,
    }
    ast_obs = MappingProxyType(
        {code: AstObservation(interp) for code, interp in ast.items()}
    )
    return CanonicalIsolate(
        isolate_id=isolate_id,
        collection_date=collection_date,
        organism_code=COHORT_ORG,
        organism_name="Klebsiella pneumoniae",
        facility_id=COHORT_FACILITY,
        lab_id="SYNTH-LAB-001",
        ward=COHORT_WARD,
        specimen_type="blood",
        patient_token=f"SYNTH-CASE-{isolate_id.replace('ISO-', '')}",
        source_import_id="SYNTH-IMPORT-001",
        ast_results=ast_obs,
    )


def _make_context(incident_id: IncidentId, *, version: IncidentVersion) -> StoredIncidentContext:
    return StoredIncidentContext(
        incident_id=incident_id,
        incident_version=version,
        source_watermark=WATERMARK,
        # The #53/#54 fixture incident contains exactly the intended comparison
        # pair so the deterministic fan-out input is unambiguous.
        isolates=tuple(_make_isolate(i) for i in ("ISO-001", "ISO-002")),
        signal_config=SignalConfig(),
        window_end=WINDOW_END,
    )


class FakeContextRepository:
    """In-memory InvestigationContextRepository fake."""

    def __init__(self, contexts: dict[str, StoredIncidentContext]) -> None:
        self._contexts = dict(contexts)

    def get(self, incident_id: IncidentId) -> StoredIncidentContext | None:
        return self._contexts.get(incident_id.value)


def _repo() -> FakeContextRepository:
    return FakeContextRepository(
        {
            INCIDENT_1.value: _make_context(INCIDENT_1, version=VERSION_1),
            INCIDENT_2.value: _make_context(INCIDENT_2, version=VERSION_2),
        }
    )


def _command(*, incident_id: IncidentId, version: IncidentVersion) -> EventInvestigationCommand:
    return EventInvestigationCommand(
        incident_id=incident_id,
        incident_version=version,
        source_watermark=WATERMARK,
        event_id="evt-synth-0001",
        correlation_id="corr-synth-0001",
    )


def _budget(**overrides: object) -> InvestigationRuntimeBudget:
    values: dict[str, object] = {
        "max_runtime_seconds": 30.0,
        "max_model_calls": 0,
        "max_tool_calls": 4,
        "max_loop_iterations": 1,
        "max_repair_attempts": 0,
    }
    values.update(overrides)
    return InvestigationRuntimeBudget(**values)  # type: ignore[arg-type]


def _runtime(
    *,
    get_context: object | None = None,
    compare_profiles: object | None = None,
    get_baseline_summary: object | None = None,
    assess_missingness: object | None = None,
    budget: InvestigationRuntimeBudget | None = None,
) -> EventInvestigationRuntime:
    handler = get_context if get_context is not None else GetInvestigationContext(_repo())
    repo = _repo()
    return EventInvestigationRuntime(
        get_context=handler,  # type: ignore[arg-type]
        compare_profiles=compare_profiles or CompareResistanceProfiles(repo),  # type: ignore[arg-type]
        get_baseline_summary=get_baseline_summary or GetBaselineSummary(repo),  # type: ignore[arg-type]
        assess_missingness=assess_missingness or AssessMaterialMissingness(repo),  # type: ignore[arg-type]
        budget=budget or _budget(),
        app_name=DEFAULT_APP_NAME,
    )


class TestCommandContract:
    def test_command_from_and_to_primitive_roundtrip(self) -> None:
        command = _command(incident_id=INCIDENT_1, version=VERSION_1)
        primitive = command.to_primitive()
        rebuilt = EventInvestigationCommand.from_primitive(primitive)
        assert rebuilt == command

    def test_command_missing_incident_id_is_malformed(self) -> None:
        with pytest.raises(ValueError):
            EventInvestigationCommand.from_primitive(
                {
                    "incident_version": 1,
                    "source_watermark": WATERMARK.value,
                    "event_id": "evt-x",
                }
            )

    def test_command_invalid_version_is_malformed(self) -> None:
        with pytest.raises(ValueError):
            EventInvestigationCommand.from_primitive(
                {
                    "incident_id": INCIDENT_1.value,
                    "incident_version": "not-an-int",
                    "source_watermark": WATERMARK.value,
                    "event_id": "evt-x",
                }
            )


class TestPinnedRuntime:
    def test_installed_google_adk_version_is_asserted(self) -> None:
        # #53 requires executing the ACTUAL pinned runtime, not a facsimile.
        assert detect_google_adk_version() == "2.8.0"
        runtime = _runtime()
        assert runtime.adk_version == "2.8.0"


class TestBackendInvocation:
    def test_event_command_invokes_real_adk_runtime_with_no_chat(self) -> None:
        runtime = _runtime()
        result = runtime.execute(_command(incident_id=INCIDENT_1, version=VERSION_1))
        assert result.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
        assert result.failure_code is None
        assert result.is_success() is True
        assert result.metadata is not None
        assert result.capability_result is not None
        assert result.capability_result.outcome is CapabilityOutcome.SUCCESS
        assert result.capability_result.incident_id == INCIDENT_1
        assert result.metadata.adk_version == detect_google_adk_version()

    def test_thin_wrapper_invokes_capability_exactly_once(self) -> None:
        calls: list[GetInvestigationContextQuery] = []
        capability = GetInvestigationContext(_repo())

        def spy(query: GetInvestigationContextQuery) -> InvestigationContextResult:
            calls.append(query)
            return capability.execute(query)

        result = _runtime(get_context=spy).execute(
            _command(incident_id=INCIDENT_1, version=VERSION_1)
        )
        assert result.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
        assert len(calls) == 1
        assert calls[0].incident_id == INCIDENT_1
        assert calls[0].requested_version == VERSION_1

    def test_identifiers_are_emitted_and_consistent(self) -> None:
        runtime = _runtime()
        command = _command(incident_id=INCIDENT_1, version=VERSION_1)
        result = runtime.execute(command)
        metadata = result.metadata
        assert metadata is not None
        assert result.execution_id == metadata.execution_id
        assert isinstance(result.execution_id, InvestigationExecutionId)
        assert result.execution_id.value.startswith("RUN-")
        assert metadata.session_id.startswith("ngabo-session-")
        assert metadata.invocation_id.startswith("ngabo-invocation-")
        assert metadata.event_id == command.event_id
        assert metadata.correlation_id == command.correlation_id
        assert metadata.incident_id == INCIDENT_1
        assert metadata.incident_version == VERSION_1
        # A success run cannot carry a failure code.
        assert result.failure_code is None

    def test_no_chat_dependency_in_message_carrier(self) -> None:
        # The adapter builds a machine envelope, not a user instruction. We prove
        # the executed run has deterministic zero-model-call telemetry.
        result = _runtime().execute(_command(incident_id=INCIDENT_1, version=VERSION_1))
        assert result.metadata is not None
        assert result.metadata.model_calls == 0
        assert result.metadata.wrapper_calls == 1
        assert result.metadata.tool_calls == 4

    def test_primitive_event_payload_invokes_adapter(self) -> None:
        runtime = _runtime()
        payload = {
            "contract_version": "ngabo-event-investigation-v1",
            "incident_id": INCIDENT_1.value,
            "incident_version": VERSION_1.value,
            "source_watermark": WATERMARK.value,
            "event_id": "evt-synth-0001",
            "correlation_id": "corr-synth-0001",
        }
        result = runtime.execute_primitive(payload)
        assert result.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
        assert result.metadata is not None
        assert result.metadata.incident_id == INCIDENT_1


class TestFailureSemantics:
    def test_missing_incident_blocks(self) -> None:
        result = _runtime().execute(_command(incident_id=IncidentId("INC-999"), version=VERSION_1))
        assert result.outcome is InvestigationExecutionOutcome.BLOCKED
        assert result.failure_code is InvestigationExecutionErrorCode.INCIDENT_NOT_FOUND
        assert result.is_success() is False
        assert result.metadata is not None
        assert result.capability_result is not None
        assert result.capability_result.outcome is CapabilityOutcome.INCIDENT_NOT_FOUND

    def test_stale_incident_version_blocks(self) -> None:
        result = _runtime().execute(_command(incident_id=INCIDENT_1, version=IncidentVersion(5)))
        assert result.outcome is InvestigationExecutionOutcome.BLOCKED
        assert result.failure_code is InvestigationExecutionErrorCode.STALE_INCIDENT_VERSION
        assert result.is_success() is False

    def test_inward_capability_unexpected_failure(self) -> None:
        def bad_handler(query: GetInvestigationContextQuery) -> InvestigationContextResult:
            del query
            return InvestigationContextResult(
                outcome=CapabilityOutcome.REQUIRED_CAPABILITY_FAILED,
                incident_id=INCIDENT_1,
                incident_version=VERSION_1,
                source_watermark=WATERMARK,
                isolates=(),
                signal_config=None,
                window_end=None,
                requested_version=VERSION_1,
            )

        result = _runtime(get_context=bad_handler).execute(
            _command(incident_id=INCIDENT_1, version=VERSION_1)
        )
        assert result.outcome is InvestigationExecutionOutcome.FAILED
        assert result.failure_code is InvestigationExecutionErrorCode.INWARD_CAPABILITY_FAILED
        assert result.is_success() is False

    def test_wrapper_exception_fails_closed(self) -> None:
        def exploding_handler(query: GetInvestigationContextQuery) -> InvestigationContextResult:
            del query
            raise RuntimeError("boom from inward handler")

        result = _runtime(get_context=exploding_handler).execute(
            _command(incident_id=INCIDENT_1, version=VERSION_1)
        )
        assert result.outcome is InvestigationExecutionOutcome.FAILED
        assert result.failure_code is InvestigationExecutionErrorCode.WRAPPER_EXCEPTION
        assert result.is_success() is False

    def test_timeout_fails_closed_not_success(self) -> None:
        import time

        def slow_handler(query: GetInvestigationContextQuery) -> InvestigationContextResult:
            del query
            time.sleep(1.0)
            return InvestigationContextResult(
                outcome=CapabilityOutcome.SUCCESS,
                incident_id=INCIDENT_1,
                incident_version=VERSION_1,
                source_watermark=WATERMARK,
                isolates=(),
                signal_config=None,
                window_end=None,
                requested_version=VERSION_1,
            )

        runtime = _runtime(
            get_context=slow_handler,
            budget=_budget(max_runtime_seconds=0.05),
        )
        result = runtime.execute(_command(incident_id=INCIDENT_1, version=VERSION_1))
        assert result.outcome is InvestigationExecutionOutcome.FAILED
        assert result.failure_code is InvestigationExecutionErrorCode.EXECUTION_TIMEOUT
        assert result.is_success() is False
        assert result.metadata is not None

    def test_tool_call_budget_exceeded_fails_closed(self) -> None:
        runtime = _runtime(budget=_budget(max_tool_calls=0))
        result = runtime.execute(_command(incident_id=INCIDENT_1, version=VERSION_1))
        assert result.outcome is InvestigationExecutionOutcome.FAILED
        assert result.failure_code is InvestigationExecutionErrorCode.EXECUTION_BUDGET_EXCEEDED
        assert result.is_success() is False
        assert result.metadata is not None

    def test_malformed_primitive_rejected_without_exception(self) -> None:
        result = _runtime().execute_primitive(
            {"incident_id": "NOT-VALID", "incident_version": 1, "source_watermark": "wm"}
        )
        assert result.outcome is InvestigationExecutionOutcome.FAILED
        assert result.failure_code is InvestigationExecutionErrorCode.MALFORMED_COMMAND
        assert result.metadata is None
        assert result.is_success() is False


class TestAuthorityBoundary:
    def test_outcome_vocabulary_has_no_package_success_state(self) -> None:
        names = set(InvestigationExecutionOutcome.__members__)
        assert "PACKAGE_COMPLETED" not in names
        assert "INVESTIGATION_COMPLETE" not in names
        assert "VERIFIED" not in names
        assert "ACTION_READY" not in names

    def test_result_has_no_self_verification_or_authorization_field(self) -> None:
        result = _rejected_result()
        # The result contract cannot itself hold verified/authorized/ready state.
        assert not hasattr(result, "verified")
        assert not hasattr(result, "approved")
        assert not hasattr(result, "action_authorized")
        assert not hasattr(result, "ready_to_send")
        assert not hasattr(result, "package_completed")

    def test_success_cannot_carry_a_failure_code(self) -> None:
        runtime = _runtime()
        result = runtime.execute(_command(incident_id=INCIDENT_1, version=VERSION_1))
        assert result.outcome.is_success
        with pytest.raises(ValueError):
            EventInvocationResult(
                outcome=InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM,
                execution_id=result.execution_id,
                metadata=result.metadata,
                capability_result=result.capability_result,
                failure_code=InvestigationExecutionErrorCode.WRAPPER_EXCEPTION,
            )

    def test_replay_same_command_has_no_external_side_effect_offset(self) -> None:
        runtime = _runtime()
        command = _command(incident_id=INCIDENT_1, version=VERSION_1)
        first = runtime.execute(command)
        second = runtime.execute(command)
        assert first.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
        assert second.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
        # No authority/send state is ever produced; distinct runs get distinct IDs.
        assert first.execution_id != second.execution_id
        assert first.is_success() and second.is_success()


class TestMetadataAndImmutability:
    def test_metadata_is_immutable(self) -> None:
        metadata = _sample_metadata()
        with pytest.raises(FrozenInstanceError):
            metadata.session_id = "changed"  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            metadata.budget = _budget()  # type: ignore[misc]

    def test_safe_primitive_excludes_sensitive_capability_contents(self) -> None:
        runtime = _runtime()
        result = runtime.execute(_command(incident_id=INCIDENT_1, version=VERSION_1))
        safe = cast(dict[str, Any], result.to_safe_primitive())
        assert safe["is_success"] is True
        assert safe["outcome"] == "READY_FOR_DOWNSTREAM"
        assert safe["execution_id"].startswith("RUN-")
        # No isolate records / patient tokens / free-form authority leak.
        serialized = str(safe)
        assert "ISO-001" not in serialized
        assert "SYNTH-CASE" not in serialized
        assert "verified" not in serialized.lower()
        assert "authorized" not in serialized.lower()


class TestBackendInvocationTrace:
    def test_success_trace_has_all_required_fields(self) -> None:
        runtime = _runtime()
        command = _command(incident_id=INCIDENT_1, version=VERSION_1)
        result = runtime.execute(command)
        trace = cast(dict[str, Any], result.to_safe_primitive())
        metadata = cast(dict[str, Any], trace["metadata"])
        assert metadata is not None
        for field in (
            "event_id",
            "incident_id",
            "incident_version",
            "source_watermark",
        ):
            assert field in metadata
        assert metadata["adk_version"] == "2.8.0"
        assert metadata["execution_id"].startswith("RUN-")
        assert metadata["session_id"].startswith("ngabo-session-")
        assert metadata["invocation_id"].startswith("ngabo-invocation-")
        assert metadata["wrapper_calls"] == 1
        assert metadata["model_calls"] == 0
        assert metadata["tool_calls"] == 4
        assert metadata["duration_ms"] >= 0
        assert "max_runtime_seconds" in metadata["budget"]
        assert trace["outcome"] == "READY_FOR_DOWNSTREAM"
        assert trace["is_success"] is True
        assert trace["failure_code"] is None

    def test_failure_trace_is_never_package_success(self) -> None:
        result = _runtime().execute(_command(incident_id=IncidentId("INC-999"), version=VERSION_1))
        trace = result.to_safe_primitive()
        assert trace["outcome"] == "BLOCKED"
        assert trace["is_success"] is False
        assert trace["failure_code"] == "INCIDENT_NOT_FOUND"
        # A failure trace must not smuggle a package-complete/verified/ready state.
        serialized = str(trace)
        assert "PACKAGE_COMPLETED" not in serialized
        assert "verified" not in serialized.lower()
        assert "authorized" not in serialized.lower()
        assert "ready_to_send" not in serialized.lower()

    def test_committed_trace_fixtures_match_contract(self) -> None:
        fixtures = Path(__file__).resolve().parent / "fixtures"
        success = json.loads((fixtures / "event_investigation_trace_success.json").read_text())
        failure = json.loads((fixtures / "event_investigation_trace_failure.json").read_text())
        assert success["outcome"] == "READY_FOR_DOWNSTREAM"
        assert success["is_success"] is True
        assert success["failure_code"] is None
        assert success["capability_outcome"] == "SUCCESS"
        assert "authorized" not in str(success).lower()
        assert failure["outcome"] == "BLOCKED"
        assert failure["is_success"] is False
        assert failure["failure_code"] == "INCIDENT_NOT_FOUND"


class TestArchitectureBoundary:
    def test_runtime_module_has_no_raw_persistence_imports(self) -> None:
        path = Path(__file__).resolve().parents[1] / (
            "ngabo/infrastructure/adk/investigation_runtime.py"
        )
        source = path.read_text(encoding="utf-8")
        for forbidden in ("firestore", "cloud_storage", "pubsub", "sqlalchemy", "psycopg"):
            assert forbidden not in source.lower()
        assert "import firebase" not in source.lower()

    def test_application_contracts_import_no_adk_or_model_sdk(self) -> None:
        for relative in (
            "ngabo/application/value_objects/investigation_execution.py",
            "ngabo/application/enums/investigation_execution_outcome.py",
            "ngabo/application/enums/investigation_execution_error_code.py",
        ):
            source = (Path(__file__).resolve().parents[1] / relative).read_text(encoding="utf-8")
            assert "google.adk" not in source
            assert "google.genai" not in source
            assert "pydantic" not in source.lower()


class TestSourceWatermarkBinding:
    """P1 regression: success must be bound to the canonical source watermark."""

    def test_matching_event_and_canonical_watermark_completes(self) -> None:
        runtime = _runtime()
        result = runtime.execute(_command(incident_id=INCIDENT_1, version=VERSION_1))
        assert result.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
        assert result.is_success() is True
        assert result.failure_code is None

    def test_stale_fabricated_watermark_blocks_with_stable_code(self) -> None:
        runtime = _runtime()
        forged = SourceWatermark("ngabo-source-v9:sha256:forged9")
        result = runtime.execute(
            EventInvestigationCommand(
                incident_id=INCIDENT_1,
                incident_version=VERSION_1,
                source_watermark=forged,
                event_id="evt-synth-0001",
                correlation_id="corr-synth-0001",
            )
        )
        assert result.outcome is InvestigationExecutionOutcome.BLOCKED
        assert result.failure_code is InvestigationExecutionErrorCode.SOURCE_WATERMARK_MISMATCH
        assert result.is_success() is False
        assert result.metadata is not None
        # The event carried the current incident version, so only the watermark
        # binding can explain the block.
        assert result.capability_result is not None
        assert result.capability_result.incident_version == VERSION_1

    def test_watermark_mismatch_never_reports_is_success(self) -> None:
        forged = SourceWatermark("ngabo-source-v9:sha256:forged9")
        result = _runtime().execute(
            EventInvestigationCommand(
                incident_id=INCIDENT_1,
                incident_version=VERSION_1,
                source_watermark=forged,
                event_id="evt-synth-0001",
                correlation_id="corr-synth-0001",
            )
        )
        assert result.is_success() is False

    def test_watermark_mismatch_never_ready_for_downstream(self) -> None:
        forged = SourceWatermark("ngabo-source-v9:sha256:forged9")
        result = _runtime().execute(
            EventInvestigationCommand(
                incident_id=INCIDENT_1,
                incident_version=VERSION_1,
                source_watermark=forged,
                event_id="evt-synth-0001",
                correlation_id="corr-synth-0001",
            )
        )
        assert result.outcome != InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM

    def test_success_metadata_watermark_equals_canonical_capability_watermark(self) -> None:
        runtime = _runtime()
        result = runtime.execute(_command(incident_id=INCIDENT_1, version=VERSION_1))
        assert result.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
        assert result.metadata is not None
        assert result.capability_result is not None
        assert result.metadata.source_watermark == result.capability_result.source_watermark
        # The canonical capability watermark is the authoritative owner.
        assert result.metadata.source_watermark == WATERMARK

    def test_watermark_mismatch_keeps_run_identifiers_observable(self) -> None:
        forged = SourceWatermark("ngabo-source-v9:sha256:forged9")
        runtime = _runtime()
        command = EventInvestigationCommand(
            incident_id=INCIDENT_1,
            incident_version=VERSION_1,
            source_watermark=forged,
            event_id="evt-synth-0001",
            correlation_id="corr-synth-0001",
        )
        result = runtime.execute(command)
        assert result.outcome is InvestigationExecutionOutcome.BLOCKED
        metadata = result.metadata
        assert metadata is not None
        assert result.execution_id == metadata.execution_id
        assert metadata.session_id.startswith("ngabo-session-")
        assert metadata.invocation_id.startswith("ngabo-invocation-")
        assert metadata.event_id == command.event_id
        assert metadata.correlation_id == command.correlation_id
        assert metadata.incident_id == INCIDENT_1
        assert metadata.incident_version == VERSION_1


class TestSyncDeadline:
    """P1 regression: the public synchronous entry points are wall-clock bounded."""

    @staticmethod
    def _success_result(query: GetInvestigationContextQuery) -> InvestigationContextResult:
        return InvestigationContextResult(
            outcome=CapabilityOutcome.SUCCESS,
            incident_id=INCIDENT_1,
            incident_version=VERSION_1,
            source_watermark=WATERMARK,
            isolates=tuple(_make_isolate(i) for i in ("ISO-001", "ISO-002")),
            signal_config=None,
            window_end=None,
            requested_version=query.requested_version,
        )

    def test_sync_execute_returns_within_deadline(self) -> None:
        import time

        def blocking_handler(query: GetInvestigationContextQuery) -> InvestigationContextResult:
            time.sleep(3.0)  # materially longer than the 0.25s budget
            return self._success_result(query)

        runtime = _runtime(
            get_context=blocking_handler,
            budget=_budget(max_runtime_seconds=0.25),
        )
        result = runtime.execute(_command(incident_id=INCIDENT_1, version=VERSION_1))
        assert result.outcome is InvestigationExecutionOutcome.FAILED
        assert result.failure_code is InvestigationExecutionErrorCode.EXECUTION_TIMEOUT
        assert result.is_success() is False

    def test_sync_execute_is_wall_clock_bounded(self) -> None:
        import time

        def blocking_handler(query: GetInvestigationContextQuery) -> InvestigationContextResult:
            time.sleep(3.0)
            return self._success_result(query)

        runtime = _runtime(
            get_context=blocking_handler,
            budget=_budget(max_runtime_seconds=0.25),
        )
        start = time.monotonic()
        runtime.execute(_command(incident_id=INCIDENT_1, version=VERSION_1))
        elapsed = time.monotonic() - start
        # The sync caller must return near the deadline, NOT after the 3s handler
        # sleep. Current (unfixed) implementation sleeps the full 3s due to the
        # default executor shutdown blocking under asyncio.run.
        assert elapsed < 1.5, f"sync execute() blocked {elapsed:.2f}s; deadline not respected"

    def test_sync_execute_primitive_is_wall_clock_bounded(self) -> None:
        import time

        def blocking_handler(query: GetInvestigationContextQuery) -> InvestigationContextResult:
            time.sleep(3.0)
            return self._success_result(query)

        runtime = _runtime(
            get_context=blocking_handler,
            budget=_budget(max_runtime_seconds=0.25),
        )
        payload = {
            "contract_version": "ngabo-event-investigation-v1",
            "incident_id": INCIDENT_1.value,
            "incident_version": VERSION_1.value,
            "source_watermark": WATERMARK.value,
            "event_id": "evt-synth-0001",
            "correlation_id": "corr-synth-0001",
        }
        start = time.monotonic()
        result = runtime.execute_primitive(payload)
        elapsed = time.monotonic() - start
        assert result.outcome is InvestigationExecutionOutcome.FAILED
        assert result.failure_code is InvestigationExecutionErrorCode.EXECUTION_TIMEOUT
        assert result.is_success() is False
        assert elapsed < 1.5, f"sync execute_primitive() blocked {elapsed:.2f}s"

    def test_delayed_success_completes_without_false_timeout(self) -> None:
        import time

        def delayed_handler(query: GetInvestigationContextQuery) -> InvestigationContextResult:
            time.sleep(0.08)  # completes well before the 2.0s deadline
            return self._success_result(query)

        runtime = _runtime(
            get_context=delayed_handler,
            budget=_budget(max_runtime_seconds=2.0),
        )
        command = _command(incident_id=INCIDENT_1, version=VERSION_1)
        start = time.monotonic()
        result = runtime.execute(command)
        elapsed = time.monotonic() - start
        # A handler that finishes after the loop is awaiting but well before the
        # deadline MUST wake the loop instead of waiting for the timeout timer.
        # This proves the daemon-thread completion is delivered thread-safely and
        # does not become a false EXECUTION_TIMEOUT.
        assert result.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
        assert result.failure_code is None
        assert result.is_success() is True
        assert elapsed < 1.5, f"delayed success waited {elapsed:.2f}s; false timeout?"
        metadata = result.metadata
        assert metadata is not None
        assert result.capability_result is not None
        assert result.capability_result.outcome is CapabilityOutcome.SUCCESS
        assert metadata.source_watermark == result.capability_result.source_watermark
        assert metadata.source_watermark == WATERMARK
        assert metadata.wrapper_calls == 1
        assert metadata.tool_calls == 4
        assert metadata.model_calls == 0
        assert metadata.duration_ms < 2000

    def test_delayed_success_debug_mode_no_non_thread_safe_mutation(self) -> None:
        import asyncio
        import time

        def delayed_handler(query: GetInvestigationContextQuery) -> InvestigationContextResult:
            time.sleep(0.08)
            return self._success_result(query)

        runtime = _runtime(
            get_context=delayed_handler,
            budget=_budget(max_runtime_seconds=2.0),
        )

        async def main() -> EventInvocationResult:
            return await runtime.execute_async(
                _command(incident_id=INCIDENT_1, version=VERSION_1)
            )

        # asyncio debug mode surfaces non-thread-safe Future/loop scheduling
        # mistakes. The delayed success must still complete (no false timeout).
        result = asyncio.run(main(), debug=True)
        assert result.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
        assert result.failure_code is None
        assert result.is_success() is True


class TestCommandContractVersion:
    """P2 regression: from_primitive must validate contract_version exactly."""

    def test_correct_contract_version_parses(self) -> None:
        command = _command(incident_id=INCIDENT_1, version=VERSION_1)
        primitive = command.to_primitive()
        assert primitive["contract_version"] == "ngabo-event-investigation-v1"
        rebuilt = EventInvestigationCommand.from_primitive(primitive)
        assert rebuilt == command

    def test_roundtrip_preserves_matching_contract_version(self) -> None:
        command = _command(incident_id=INCIDENT_1, version=VERSION_1)
        rebuilt = EventInvestigationCommand.from_primitive(command.to_primitive())
        rebuilt_version = rebuilt.to_primitive()["contract_version"]
        command_version = command.to_primitive()["contract_version"]
        assert rebuilt_version == command_version

    def test_missing_contract_version_is_malformed(self) -> None:
        with pytest.raises(ValueError):
            EventInvestigationCommand.from_primitive(
                {
                    "incident_id": INCIDENT_1.value,
                    "incident_version": VERSION_1.value,
                    "source_watermark": WATERMARK.value,
                    "event_id": "evt-x",
                }
            )

    def test_missing_contract_version_maps_to_malformed_result(self) -> None:
        result = _runtime().execute_primitive(
            {
                "incident_id": INCIDENT_1.value,
                "incident_version": VERSION_1.value,
                "source_watermark": WATERMARK.value,
                "event_id": "evt-x",
            }
        )
        assert result.outcome is InvestigationExecutionOutcome.FAILED
        assert result.failure_code is InvestigationExecutionErrorCode.MALFORMED_COMMAND
        assert result.metadata is None
        assert result.is_success() is False

    def test_foreign_future_contract_version_is_malformed(self) -> None:
        with pytest.raises(ValueError):
            EventInvestigationCommand.from_primitive(
                {
                    "contract_version": "ngabo-event-investigation-v2",
                    "incident_id": INCIDENT_1.value,
                    "incident_version": VERSION_1.value,
                    "source_watermark": WATERMARK.value,
                    "event_id": "evt-x",
                }
            )

    def test_foreign_future_contract_version_maps_to_malformed_result(self) -> None:
        result = _runtime().execute_primitive(
            {
                "contract_version": "ngabo-event-investigation-v2",
                "incident_id": INCIDENT_1.value,
                "incident_version": VERSION_1.value,
                "source_watermark": WATERMARK.value,
                "event_id": "evt-x",
            }
        )
        assert result.outcome is InvestigationExecutionOutcome.FAILED
        assert result.failure_code is InvestigationExecutionErrorCode.MALFORMED_COMMAND
        assert result.metadata is None
        assert result.is_success() is False

    def test_blank_contract_version_is_malformed(self) -> None:
        with pytest.raises(ValueError):
            EventInvestigationCommand.from_primitive(
                {
                    "contract_version": "   ",
                    "incident_id": INCIDENT_1.value,
                    "incident_version": VERSION_1.value,
                    "source_watermark": WATERMARK.value,
                    "event_id": "evt-x",
                }
            )

    def test_blank_contract_version_maps_to_malformed_result(self) -> None:
        result = _runtime().execute_primitive(
            {
                "contract_version": "   ",
                "incident_id": INCIDENT_1.value,
                "incident_version": VERSION_1.value,
                "source_watermark": WATERMARK.value,
                "event_id": "evt-x",
            }
        )
        assert result.outcome is InvestigationExecutionOutcome.FAILED
        assert result.failure_code is InvestigationExecutionErrorCode.MALFORMED_COMMAND
        assert result.metadata is None
        assert result.is_success() is False

    def test_malformed_version_does_not_start_adk_runtime(self) -> None:
        calls: list[GetInvestigationContextQuery] = []

        def spy(query: GetInvestigationContextQuery) -> InvestigationContextResult:
            calls.append(query)
            raise AssertionError("ADK runtime should never invoke the capability for a bad version")

        runtime = _runtime(get_context=spy)
        result = runtime.execute_primitive(
            {
                "contract_version": "arbitrary/foreign",
                "incident_id": INCIDENT_1.value,
                "incident_version": VERSION_1.value,
                "source_watermark": WATERMARK.value,
                "event_id": "evt-x",
            }
        )
        assert result.outcome is InvestigationExecutionOutcome.FAILED
        assert result.failure_code is InvestigationExecutionErrorCode.MALFORMED_COMMAND
        assert result.metadata is None
        assert calls == []


def _sample_metadata() -> ADKExecutionMetadata:
    return ADKExecutionMetadata(
        execution_id=InvestigationExecutionId("RUN-" + "a" * 32),
        session_id="ngabo-session-abc",
        invocation_id="ngabo-invocation-def",
        event_id="evt-synth-0001",
        correlation_id="corr-synth-0001",
        incident_id=INCIDENT_1,
        incident_version=VERSION_1,
        source_watermark=WATERMARK,
        wrapper_calls=1,
        model_calls=0,
        tool_calls=1,
        duration_ms=12,
        budget=_budget(),
        adk_version="2.8.0",
    )


def _rejected_result() -> EventInvocationResult:
    return EventInvocationResult(
        outcome=InvestigationExecutionOutcome.FAILED,
        execution_id=InvestigationExecutionId("RUN-" + "b" * 32),
        metadata=None,
        capability_result=None,
        failure_code=InvestigationExecutionErrorCode.MALFORMED_COMMAND,
    )
