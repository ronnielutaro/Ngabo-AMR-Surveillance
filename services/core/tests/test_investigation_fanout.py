"""Focused tests for the Issue #54 deterministic fan-out/join graph.

These exercise the REAL pinned ``google-adk==2.8.0`` ``Runner``/``Workflow``/
``FunctionNode``/``JoinNode`` path with deterministic in-memory inward handlers
and dependency injection. They prove: all three required branches run
concurrently, exactly once per logical attempt; the joined result is a
framework-free immutable context; canonical incident/version/source-watermark
binding is enforced; required branch failure blocks downstream readiness;
retry, timeout, cancellation, replay and zero-model-call semantics hold.
"""

from __future__ import annotations

import asyncio
import threading
from datetime import date
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
from ngabo.application.value_objects.baseline_summary import (
    BaselineSummaryResult,
    GetBaselineSummaryQuery,
)
from ngabo.application.value_objects.deterministic_investigation import (
    JoinedInvestigationContext,
)
from ngabo.application.value_objects.investigation_context import (
    StoredIncidentContext,
)
from ngabo.application.value_objects.investigation_execution import (
    EventInvestigationCommand,
    EventInvocationResult,
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
)

INCIDENT = IncidentId("INC-001")
VERSION = IncidentVersion(1)
WATERMARK = SourceWatermark("ngabo-source-v1:sha256:abc123")
WINDOW_END = date(2026, 8, 17)
ORG = "kle"
FACILITY = "SYNTH-FACILITY-001"
WARD = "SYNTH-WARD-A"
ISOLATE_A = "ISO-001"
ISOLATE_B = "ISO-002"


def _isolate(
    isolate_id: str,
    *,
    organism_code: str = ORG,
    facility_id: str = FACILITY,
) -> CanonicalIsolate:
    ast = {
        "AMK": Interpretation.SUSCEPTIBLE,
        "CAZ": Interpretation.RESISTANT,
        "CIP": Interpretation.RESISTANT,
        "CRO": Interpretation.RESISTANT,
        "MEM": Interpretation.RESISTANT,
        "SXT": Interpretation.RESISTANT,
    }
    return CanonicalIsolate(
        isolate_id=isolate_id,
        collection_date=WINDOW_END,
        organism_code=organism_code,
        organism_name="Klebsiella pneumoniae",
        facility_id=facility_id,
        lab_id="SYNTH-LAB-001",
        ward=WARD,
        specimen_type="blood",
        patient_token=f"SYNTH-CASE-{isolate_id.replace('ISO-', '')}",
        source_import_id="SYNTH-IMPORT-001",
        ast_results=MappingProxyType(
            {code: AstObservation(interp) for code, interp in ast.items()}
        ),
    )


def _stored() -> StoredIncidentContext:
    return StoredIncidentContext(
        incident_id=INCIDENT,
        incident_version=VERSION,
        source_watermark=WATERMARK,
        isolates=(_isolate(ISOLATE_A), _isolate(ISOLATE_B)),
        signal_config=SignalConfig(),
        window_end=WINDOW_END,
    )


class _Repo:
    """In-memory InvestigationContextRepository fake."""

    def __init__(self, context: StoredIncidentContext | None = None) -> None:
        self._context = context if context is not None else _stored()

    def get(self, incident_id: IncidentId) -> StoredIncidentContext | None:
        return self._context if incident_id.value == INCIDENT.value else None


def _budget(**overrides: object) -> InvestigationRuntimeBudget:
    values: dict[str, object] = {
        "max_runtime_seconds": 30.0,
        "max_model_calls": 0,
        "max_tool_calls": 8,
        "max_loop_iterations": 1,
        "max_repair_attempts": 0,
    }
    values.update(overrides)
    return InvestigationRuntimeBudget(**values)  # type: ignore[arg-type]


def _command() -> EventInvestigationCommand:
    return EventInvestigationCommand(
        incident_id=INCIDENT,
        incident_version=VERSION,
        source_watermark=WATERMARK,
        event_id="evt-synth-0001",
        correlation_id="corr-synth-0001",
    )


def _capabilities(
    repo: _Repo,
) -> tuple[
    GetInvestigationContext,
    CompareResistanceProfiles,
    GetBaselineSummary,
    AssessMaterialMissingness,
]:
    return (
        GetInvestigationContext(repo),
        CompareResistanceProfiles(repo),
        GetBaselineSummary(repo),
        AssessMaterialMissingness(repo),
    )


def _runtime(
    *,
    repo: _Repo | None = None,
    budget: InvestigationRuntimeBudget | None = None,
    compare_profiles: object | None = None,
    get_baseline_summary: object | None = None,
    assess_missingness: object | None = None,
    get_context: object | None = None,
) -> EventInvestigationRuntime:
    repo = repo or _Repo()
    get_context_cap, compare_cap, baseline_cap, missingness_cap = _capabilities(repo)
    return EventInvestigationRuntime(
        get_context=(
            get_context if get_context is not None else get_context_cap  # type: ignore[arg-type]
        ),
        compare_profiles=(
            compare_profiles if compare_profiles is not None else compare_cap  # type: ignore[arg-type]
        ),
        get_baseline_summary=(
            get_baseline_summary if get_baseline_summary is not None else baseline_cap  # type: ignore[arg-type]
        ),
        assess_missingness=(
            assess_missingness if assess_missingness is not None else missingness_cap  # type: ignore[arg-type]
        ),
        budget=budget or _budget(),
        app_name=DEFAULT_APP_NAME,
    )


class TestSuccessfulFanout:
    def test_all_three_required_branches_run(self) -> None:
        calls: dict[str, int] = {}
        lock = threading.Lock()

        def wrap(name: str, handler: object) -> object:
            def wrapper(*args: object) -> object:
                with lock:
                    calls[name] = calls.get(name, 0) + 1
                return handler(*args)  # type: ignore[operator]

            return wrapper

        repo = _Repo()
        cap = _capabilities(repo)
        rt = _runtime(
            repo=repo,
            compare_profiles=wrap("profile", cap[1]),
            get_baseline_summary=wrap("baseline", cap[2]),
            assess_missingness=wrap("missingness", cap[3]),
        )
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
        assert result.failure_code is None
        assert result.is_success() is True
        assert result.joined_investigation is not None
        assert result.joined_investigation.ready_for_downstream is True
        assert calls == {"profile": 1, "baseline": 1, "missingness": 1}

    def test_branches_start_concurrently(self) -> None:
        repo = _Repo()
        cap = _capabilities(repo)
        barrier = threading.Barrier(3, timeout=5.0)

        def with_barrier(handler: object) -> object:
            def wrapper(query: object) -> object:
                barrier.wait()  # proves all three daemon workers are alive at once
                return handler(query)  # type: ignore[operator]

            return wrapper

        rt = _runtime(
            repo=repo,
            compare_profiles=with_barrier(cap[1]),
            get_baseline_summary=with_barrier(cap[2]),
            assess_missingness=with_barrier(cap[3]),
        )
        result = rt.execute(_command())
        # If the branches ran sequentially the barrier would break and the run
        # would not reach READY_FOR_DOWNSTREAM; reaching it proves overlap.
        assert result.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM

    def test_exactly_once_per_branch_per_attempt(self) -> None:
        repo = _Repo()
        cap = _capabilities(repo)
        counts: dict[str, int] = {}
        lock = threading.Lock()

        def wrap(name: str, handler: object) -> object:
            def wrapper(*args: object) -> object:
                with lock:
                    counts[name] = counts.get(name, 0) + 1
                return handler(*args)  # type: ignore[operator]

            return wrapper

        rt = _runtime(
            repo=repo,
            compare_profiles=wrap("profile", cap[1]),
            get_baseline_summary=wrap("baseline", cap[2]),
            assess_missingness=wrap("missingness", cap[3]),
        )
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
        # The ADK graph must not invoke a branch twice via scheduling/join/telemetry.
        assert counts == {"profile": 1, "baseline": 1, "missingness": 1}
        records = {r.branch.value: r for r in result.branch_records}
        for branch in ("PROFILE", "BASELINE", "MISSINGNESS"):
            assert records[branch].invocation_count == 1
            assert records[branch].started is True
            assert records[branch].completed is True

    def test_joined_result_is_typed_and_framework_free(self) -> None:
        result = _runtime().execute(_command())
        joined = result.joined_investigation
        assert joined is not None
        assert isinstance(joined, JoinedInvestigationContext)
        assert joined.incident_id == INCIDENT
        assert joined.incident_version == VERSION
        assert joined.source_watermark == WATERMARK
        assert joined.ready_for_downstream is True
        assert joined.failure_code is None
        assert joined.model_calls == 0
        # The joined contract carries the three typed deterministic results.
        assert isinstance(joined.profile_result, ProfileComparisonResult)
        assert isinstance(joined.baseline_result, BaselineSummaryResult)
        assert isinstance(joined.missingness_result, MissingnessResult)
        assert joined.profile_result.outcome is CapabilityOutcome.SUCCESS
        assert joined.baseline_result.outcome is CapabilityOutcome.SUCCESS
        assert joined.missingness_result.outcome is CapabilityOutcome.SUCCESS

    def test_canonical_binding_survives_every_branch(self) -> None:
        result = _runtime().execute(_command())
        joined = result.joined_investigation
        assert joined is not None
        for branch_result in (
            joined.profile_result,
            joined.baseline_result,
            joined.missingness_result,
        ):
            assert branch_result is not None
            assert branch_result.incident_id == INCIDENT
            assert branch_result.incident_version == VERSION
            assert branch_result.source_watermark == WATERMARK

    def test_zero_model_calls_success(self) -> None:
        result = _runtime().execute(_command())
        assert result.metadata is not None
        assert result.metadata.model_calls == 0
        assert result.joined_investigation is not None
        assert result.joined_investigation.model_calls == 0


class TestBindingMismatch:
    def test_branch_success_with_wrong_watermark_blocks(self) -> None:
        repo = _Repo()
        cap = _capabilities(repo)
        good = cap[1]

        def bad_profile(query: CompareProfilesQuery) -> ProfileComparisonResult:
            result = good.execute(query)
            return ProfileComparisonResult(
                outcome=result.outcome,
                incident_id=result.incident_id,
                incident_version=result.incident_version,
                source_watermark=SourceWatermark("ngabo-source-v9:sha256:forged"),
                finding=result.finding,
                finding_reference=result.finding_reference,
                isolate_id_a=result.isolate_id_a,
                isolate_id_b=result.isolate_id_b,
            )

        rt = _runtime(repo=repo, compare_profiles=bad_profile)
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.BLOCKED
        assert result.failure_code is InvestigationExecutionErrorCode.BRANCH_BINDING_MISMATCH
        assert result.is_success() is False
        assert result.joined_investigation is not None
        assert result.joined_investigation.ready_for_downstream is False

    def test_branch_success_with_wrong_incident_id_blocks(self) -> None:
        repo = _Repo()
        cap = _capabilities(repo)
        good = cap[1]

        def bad_profile(query: CompareProfilesQuery) -> ProfileComparisonResult:
            result = good.execute(query)
            return ProfileComparisonResult(
                outcome=result.outcome,
                incident_id=IncidentId("INC-999"),
                incident_version=result.incident_version,
                source_watermark=result.source_watermark,
                finding=result.finding,
                finding_reference=result.finding_reference,
                isolate_id_a=result.isolate_id_a,
                isolate_id_b=result.isolate_id_b,
            )

        rt = _runtime(repo=repo, compare_profiles=bad_profile)
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.BLOCKED
        assert result.failure_code is InvestigationExecutionErrorCode.BRANCH_BINDING_MISMATCH
        assert result.joined_investigation is not None
        assert result.joined_investigation.ready_for_downstream is False

    def test_branch_success_with_wrong_version_blocks(self) -> None:
        repo = _Repo()
        cap = _capabilities(repo)
        good = cap[1]

        def bad_profile(query: CompareProfilesQuery) -> ProfileComparisonResult:
            result = good.execute(query)
            return ProfileComparisonResult(
                outcome=result.outcome,
                incident_id=result.incident_id,
                incident_version=IncidentVersion(99),
                source_watermark=result.source_watermark,
                finding=result.finding,
                finding_reference=result.finding_reference,
                isolate_id_a=result.isolate_id_a,
                isolate_id_b=result.isolate_id_b,
            )

        rt = _runtime(repo=repo, compare_profiles=bad_profile)
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.BLOCKED
        assert result.failure_code is InvestigationExecutionErrorCode.BRANCH_BINDING_MISMATCH
        assert result.is_success() is False


class TestRequiredBranchFailure:
    def _non_success_profile_handler(self) -> object:
        repo = _Repo()
        cap = _capabilities(repo)
        good = cap[1]

        def handler(query: CompareProfilesQuery) -> ProfileComparisonResult:
            result = good.execute(query)
            return ProfileComparisonResult(
                outcome=CapabilityOutcome.REQUIRED_CAPABILITY_FAILED,
                incident_id=result.incident_id,
                incident_version=result.incident_version,
                source_watermark=result.source_watermark,
                finding=None,
                finding_reference=None,
                isolate_id_a=result.isolate_id_a,
                isolate_id_b=result.isolate_id_b,
            )

        return handler

    def test_profile_failure_blocks(self) -> None:
        rt = _runtime(compare_profiles=self._non_success_profile_handler())
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.BLOCKED
        assert result.failure_code is InvestigationExecutionErrorCode.REQUIRED_BRANCH_FAILED
        assert result.joined_investigation is not None
        assert result.joined_investigation.ready_for_downstream is False

    def _non_success_baseline_handler(self) -> object:
        repo = _Repo()
        cap = _capabilities(repo)
        good = cap[2]

        def handler(query: GetBaselineSummaryQuery) -> BaselineSummaryResult:
            result = good.execute(query)
            return BaselineSummaryResult(
                outcome=CapabilityOutcome.MISSING_INPUT,
                incident_id=result.incident_id,
                incident_version=result.incident_version,
                source_watermark=result.source_watermark,
                signal_evaluation=None,
                organism_code=result.organism_code,
                facility_id=result.facility_id,
                ward=result.ward,
            )

        return handler

    def test_baseline_failure_blocks(self) -> None:
        rt = _runtime(get_baseline_summary=self._non_success_baseline_handler())
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.BLOCKED
        assert result.failure_code is InvestigationExecutionErrorCode.REQUIRED_BRANCH_FAILED
        assert result.joined_investigation is not None
        assert result.joined_investigation.ready_for_downstream is False

    def _non_success_missingness_handler(self) -> object:
        repo = _Repo()
        cap = _capabilities(repo)
        good = cap[3]

        def handler(query: AssessMissingnessQuery) -> MissingnessResult:
            result = good.execute(query)
            return MissingnessResult(
                outcome=CapabilityOutcome.REQUIRED_CAPABILITY_FAILED,
                incident_id=result.incident_id,
                incident_version=result.incident_version,
                source_watermark=result.source_watermark,
                missing_items=result.missing_items,
                has_material_missingness=result.has_material_missingness,
            )

        return handler

    def test_missingness_failure_blocks(self) -> None:
        rt = _runtime(assess_missingness=self._non_success_missingness_handler())
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.BLOCKED
        assert result.failure_code is InvestigationExecutionErrorCode.REQUIRED_BRANCH_FAILED
        assert result.joined_investigation is not None
        assert result.joined_investigation.ready_for_downstream is False

    def test_wrapper_exception_fails_closed(self) -> None:
        def exploding(query: CompareProfilesQuery) -> ProfileComparisonResult:
            del query
            raise RuntimeError("branch boom")

        rt = _runtime(compare_profiles=exploding)
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.FAILED
        assert result.failure_code is InvestigationExecutionErrorCode.WRAPPER_EXCEPTION
        assert result.is_success() is False
        assert result.joined_investigation is not None
        assert result.joined_investigation.ready_for_downstream is False

    def test_multiple_required_failures_have_deterministic_failure_semantics(self) -> None:
        # Both profile and baseline fail; missingness succeeds. The join must
        # still report REQUIRED_BRANCH_FAILED (branch-identity canonicalized),
        # and independent failures are not hidden merely because one arrived first.
        rt = _runtime(
            compare_profiles=self._non_success_profile_handler(),
            get_baseline_summary=self._non_success_baseline_handler(),
        )
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.BLOCKED
        assert result.failure_code is InvestigationExecutionErrorCode.REQUIRED_BRANCH_FAILED
        assert result.joined_investigation is not None
        assert result.joined_investigation.ready_for_downstream is False
        # Both failed branches are truthfully recorded.
        failed = {r.branch.value for r in result.branch_records if r.failed or r.blocked}
        assert {"PROFILE", "BASELINE"}.issubset(failed)


class TestOrderIndependence:
    def test_randomized_completion_order_yields_equivalent_join(self) -> None:
        import random

        baseline_joined = None
        for seed in range(4):
            repo = _Repo()
            cap = _capabilities(repo)
            rng = random.Random(seed)

            def delay(
                handler: object,
                low: float,
                high: float,
                _rng: random.Random = rng,
            ) -> object:
                wait = _rng.uniform(low, high)

                def wrapper(query: object) -> object:
                    import time

                    time.sleep(wait)
                    return handler(query)  # type: ignore[operator]

                return wrapper

            rt = _runtime(
                repo=repo,
                compare_profiles=delay(cap[1], 0.01, 0.06),
                get_baseline_summary=delay(cap[2], 0.01, 0.06),
                assess_missingness=delay(cap[3], 0.01, 0.06),
            )
            result = rt.execute(_command())
            assert result.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
            joined = result.joined_investigation
            assert joined is not None
            summary = joined.to_safe_summary()
            if baseline_joined is None:
                baseline_joined = summary
            else:
                # Branch identity fixes canonical ordering, so the semantic joined
                # summary is identical regardless of actual completion order.
                assert summary == baseline_joined


class TestRetry:
    def test_retryable_runtime_failure_then_success(self) -> None:
        repo = _Repo()
        cap = _capabilities(repo)
        good = cap[1]
        attempts: list[str] = []
        lock = threading.Lock()
        profile_calls = 0

        def handler(query: CompareProfilesQuery) -> ProfileComparisonResult:
            nonlocal profile_calls
            with lock:
                profile_calls += 1
                attempt = profile_calls
                attempts.append(f"profile-{attempt}")
            if attempt == 1:
                raise RuntimeError("transient")
            return good.execute(query)

        rt = _runtime(
            repo=repo,
            compare_profiles=handler,
            budget=_budget(max_loop_iterations=2),
        )
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
        assert result.joined_investigation is not None
        assert result.joined_investigation.ready_for_downstream is True
        # Attempt 1 raised; attempt 2 succeeded -> the branch ran once per attempt.
        assert profile_calls == 2

    def test_retry_budget_exhaustion_is_terminal(self) -> None:
        repo = _Repo()
        profile_calls = 0
        lock = threading.Lock()

        def handler(query: CompareProfilesQuery) -> ProfileComparisonResult:
            nonlocal profile_calls
            with lock:
                profile_calls += 1
            raise RuntimeError("always transient")

        rt = _runtime(
            repo=repo,
            compare_profiles=handler,
            budget=_budget(max_loop_iterations=2),
        )
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.FAILED
        assert result.failure_code is InvestigationExecutionErrorCode.GRAPH_RETRY_EXHAUSTED
        assert result.is_success() is False
        assert result.joined_investigation is not None
        assert result.joined_investigation.ready_for_downstream is False
        assert profile_calls == 2


class TestTimeoutAndCancellation:
    def test_overall_timeout_is_bounded_and_fails_closed(self) -> None:
        import time

        def slow(query: GetBaselineSummaryQuery) -> BaselineSummaryResult:
            del query
            time.sleep(2.0)
            raise AssertionError("should never return")

        rt = _runtime(
            get_baseline_summary=slow,
            budget=_budget(max_runtime_seconds=0.8),
        )
        start = time.monotonic()
        result = rt.execute(_command())
        elapsed = time.monotonic() - start
        assert result.outcome is InvestigationExecutionOutcome.FAILED
        assert result.failure_code is InvestigationExecutionErrorCode.EXECUTION_TIMEOUT
        assert result.is_success() is False
        assert result.metadata is not None
        # A branch that started but was interrupted by the overall deadline is
        # truthfully reported as timed out; downstream readiness is false.
        assert any(r.timed_out for r in result.branch_records)
        assert elapsed < 3.0

    def test_async_cancellation_never_reports_ready(self) -> None:
        import time

        def slow(query: GetBaselineSummaryQuery) -> BaselineSummaryResult:
            del query
            time.sleep(0.6)
            raise AssertionError("should never return")

        rt = _runtime(
            get_baseline_summary=slow,
            budget=_budget(max_runtime_seconds=10.0),
        )

        async def main() -> EventInvocationResult:
            return await rt.execute_async(_command())

        async def run_and_cancel() -> None:
            task = asyncio.create_task(main())
            await asyncio.sleep(0.2)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        asyncio.run(run_and_cancel())


class TestReplayAndArchitecture:
    def test_replay_same_command_semantic_stability_no_side_effects(self) -> None:
        first = _runtime().execute(_command())
        second = _runtime().execute(_command())
        assert first.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
        assert second.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
        assert first.joined_investigation is not None
        assert second.joined_investigation is not None
        assert (
            first.joined_investigation.to_safe_summary()
            == second.joined_investigation.to_safe_summary()
        )
        assert first.execution_id != second.execution_id
        # No action/package authority is ever produced.
        assert first.joined_investigation.ready_for_downstream is True
        assert not hasattr(first, "package_completed")
        assert not hasattr(first, "verified")
        assert not hasattr(first, "action_authorized")

    def test_fanout_value_objects_import_no_adk_or_model_sdk(self) -> None:
        from pathlib import Path

        module = Path(__file__).resolve().parents[1] / (
            "ngabo/application/value_objects/deterministic_investigation.py"
        )
        source = module.read_text(encoding="utf-8")
        assert "from google.adk" not in source
        assert "import google.adk" not in source
        assert "from google.genai" not in source
        assert "import google.genai" not in source
        assert "from pydantic" not in source.lower()
        assert "import pydantic" not in source.lower()

    def test_runtime_module_has_no_raw_persistence(self) -> None:
        from pathlib import Path

        path = Path(__file__).resolve().parents[1] / (
            "ngabo/infrastructure/adk/investigation_runtime.py"
        )
        source = path.read_text(encoding="utf-8")
        for forbidden in ("firestore", "cloud_storage", "pubsub", "sqlalchemy", "psycopg"):
            assert forbidden not in source.lower()
        assert "import firebase" not in source.lower()


class TestTraceArtifact:
    def test_success_trace_is_machine_readable_and_public_safe(self) -> None:
        result = _runtime().execute(_command())
        trace = cast(dict[str, Any], result.to_safe_primitive())
        assert trace["outcome"] == "READY_FOR_DOWNSTREAM"
        assert trace["is_success"] is True
        assert trace["failure_code"] is None
        joined = trace["joined_investigation"]
        assert joined is not None
        assert joined["ready_for_downstream"] is True
        assert joined["model_calls"] == 0
        assert joined["profile_outcome"] == "SUCCESS"
        assert joined["baseline_outcome"] == "SUCCESS"
        assert joined["missingness_outcome"] == "SUCCESS"
        records = {r["branch"]: r for r in trace["branch_records"]}
        assert set(records) == {"PROFILE", "BASELINE", "MISSINGNESS"}
        for record in records.values():
            assert record["started"] is True
            assert record["completed"] is True
            assert record["invocation_count"] == 1
            assert record["required"] is True
        serialized = str(trace)
        assert "ISO-001" not in serialized
        assert "SYNTH-CASE" not in serialized
        assert "verified" not in serialized.lower()
        assert "authorized" not in serialized.lower()

    def test_required_failure_trace_is_not_ready(self) -> None:
        def failing(query: CompareProfilesQuery) -> ProfileComparisonResult:
            result = _capabilities(_Repo())[1].execute(query)
            return ProfileComparisonResult(
                outcome=CapabilityOutcome.REQUIRED_CAPABILITY_FAILED,
                incident_id=result.incident_id,
                incident_version=result.incident_version,
                source_watermark=result.source_watermark,
                finding=None,
                finding_reference=None,
                isolate_id_a=result.isolate_id_a,
                isolate_id_b=result.isolate_id_b,
            )

        result = _runtime(compare_profiles=failing).execute(_command())
        trace = cast(dict[str, Any], result.to_safe_primitive())
        assert trace["outcome"] == "BLOCKED"
        assert trace["is_success"] is False
        assert trace["failure_code"] == "REQUIRED_BRANCH_FAILED"
        joined = trace["joined_investigation"]
        assert joined is not None
        assert joined["ready_for_downstream"] is False
        assert joined["model_calls"] == 0

    def test_committed_trace_fixtures_are_public_safe(self) -> None:
        import json
        from pathlib import Path

        fixtures = Path(__file__).resolve().parent / "fixtures"
        success = json.loads(
            (fixtures / "investigation_fanout_trace_success.json").read_text(encoding="utf-8")
        )
        failure = json.loads(
            (fixtures / "investigation_fanout_trace_failure.json").read_text(encoding="utf-8")
        )
        assert success["outcome"] == "READY_FOR_DOWNSTREAM"
        assert success["is_success"] is True
        assert success["metadata"]["model_calls"] == 0
        assert success["joined_investigation"]["ready_for_downstream"] is True
        assert len(success["branch_records"]) == 3
        assert any(r["timed_out"] for r in success["branch_records"]) is False
        assert failure["outcome"] == "BLOCKED"
        assert failure["is_success"] is False
        assert failure["failure_code"] == "REQUIRED_BRANCH_FAILED"
        assert failure["joined_investigation"]["ready_for_downstream"] is False
        for fixture in (success, failure):
            serialized = str(fixture)
            assert "ISO-001" not in serialized
            assert "SYNTH-CASE" not in serialized
            assert "verified" not in serialized.lower()
            assert "authorized" not in serialized.lower()


class TestCanonicalHeroCohort:
    """P1: the runtime must accept the canonical three-isolate hero cohort."""

    def _hero_repo(self) -> _Repo:
        context = StoredIncidentContext(
            incident_id=INCIDENT,
            incident_version=VERSION,
            source_watermark=WATERMARK,
            isolates=(_isolate("ISO-031"), _isolate("ISO-034"), _isolate("ISO-039")),
            signal_config=SignalConfig(),
            window_end=WINDOW_END,
            profile_comparison_isolate_ids=("ISO-031", "ISO-034"),
        )
        return _Repo(context)

    def test_canonical_three_isolate_hero_reaches_ready(self) -> None:
        rt = _runtime(repo=self._hero_repo())
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
        joined = result.joined_investigation
        assert joined is not None
        assert joined.ready_for_downstream is True
        assert joined.profile_result is not None
        assert joined.profile_result.incident_id == INCIDENT
        # The deterministic ground pair is ISO-031 / ISO-034.
        assert joined.profile_result.isolate_id_a == "ISO-031"
        assert joined.profile_result.isolate_id_b == "ISO-034"
        # Missingness operates against the full three-isolate cohort.
        assert joined.missingness_result is not None
        assert joined.missingness_result.has_material_missingness is False
        # All three branches ran exactly once.
        records = {r.branch.value: r for r in result.branch_records}
        for branch in ("PROFILE", "BASELINE", "MISSINGNESS"):
            assert records[branch].invocation_count == 1

    def test_ambiguous_cohort_without_ground_pair_fails_closed(self) -> None:
        context = StoredIncidentContext(
            incident_id=INCIDENT,
            incident_version=VERSION,
            source_watermark=WATERMARK,
            isolates=(_isolate("ISO-031"), _isolate("ISO-034"), _isolate("ISO-039")),
            signal_config=SignalConfig(),
            window_end=WINDOW_END,
            profile_comparison_isolate_ids=None,
        )
        rt = _runtime(repo=_Repo(context))
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.BLOCKED
        assert result.failure_code is InvestigationExecutionErrorCode.REQUIRED_INPUT_UNAVAILABLE
        # The ambiguous pair fails closed before any branch is invoked, so no
        # joined snapshot exists; readiness is trivially false.
        assert result.joined_investigation is None
        assert result.is_success() is False


class TestHardToolBudget:
    """P2: max_tool_calls is a hard per-run bound (no retry reset)."""

    def test_max_tool_calls_one_fails_closed(self) -> None:
        repo = _Repo()
        cap = _capabilities(repo)
        invoked: dict[str, int] = {}
        lock = threading.Lock()

        def track(name: str, handler: object) -> object:
            def wrapper(*args: object) -> object:
                with lock:
                    invoked[name] = invoked.get(name, 0) + 1
                return handler(*args)  # type: ignore[operator]

            return wrapper

        rt = _runtime(
            repo=repo,
            budget=_budget(max_tool_calls=1),
            compare_profiles=track("profile", cap[1]),
            get_baseline_summary=track("baseline", cap[2]),
            assess_missingness=track("missingness", cap[3]),
        )
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.FAILED
        assert result.failure_code is InvestigationExecutionErrorCode.EXECUTION_BUDGET_EXCEEDED
        assert result.is_success() is False
        assert result.joined_investigation is not None
        assert result.joined_investigation.ready_for_downstream is False
        # Context consumed the single slot; no branch handler was ever invoked.
        assert invoked == {}

    def test_budget_sufficient_for_one_full_attempt(self) -> None:
        rt = _runtime(repo=_Repo(), budget=_budget(max_tool_calls=4))
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
        assert result.metadata is not None
        assert result.metadata.tool_calls == 4

    def test_retry_does_not_reset_run_level_budget(self) -> None:
        repo = _Repo()
        cap = _capabilities(repo)
        good = cap[1]
        calls = 0
        lock = threading.Lock()

        def handler(query: CompareProfilesQuery) -> ProfileComparisonResult:
            nonlocal calls
            with lock:
                calls += 1
            if calls == 1:
                raise RuntimeError("transient")
            return good.execute(query)

        # Attempt 1 consumes 4 slots; with a 5-slot budget the retried run's
        # context reserves slot 5, so the retried profile branch is budget
        # blocked before its handler is invoked -> terminal budget failure,
        # proving retry does not reset the per-run counter.
        rt = _runtime(
            repo=repo,
            compare_profiles=handler,
            budget=_budget(max_tool_calls=5, max_loop_iterations=2),
        )
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.FAILED
        assert result.failure_code is InvestigationExecutionErrorCode.EXECUTION_BUDGET_EXCEEDED
        assert result.is_success() is False
        # Only the context acquire of attempt 2 (7th slot) can be reserved; the
        # branch handler of attempt 2 is never invoked after the budget is spent.
        assert calls == 1


class TestScientificBinding:
    """P2: a successful branch result must match the requested scientific input."""

    def test_wrong_profile_pair_blocks(self) -> None:
        repo = _Repo()
        cap = _capabilities(repo)
        good = cap[1]

        def bad(query: CompareProfilesQuery) -> ProfileComparisonResult:
            result = good.execute(query)
            return ProfileComparisonResult(
                outcome=CapabilityOutcome.SUCCESS,
                incident_id=result.incident_id,
                incident_version=result.incident_version,
                source_watermark=result.source_watermark,
                finding=result.finding,
                finding_reference=result.finding_reference,
                isolate_id_a="ISO-001",
                isolate_id_b="ISO-999",
            )

        rt = _runtime(repo=repo, compare_profiles=bad)
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.BLOCKED
        assert result.failure_code is InvestigationExecutionErrorCode.BRANCH_BINDING_MISMATCH
        assert result.joined_investigation is not None
        assert result.joined_investigation.ready_for_downstream is False

    def _baseline_result_with(
        self,
        cap: GetBaselineSummary,
        *,
        organism_code: str | None = None,
        facility_id: str | None = None,
        ward: str | None = None,
    ) -> BaselineSummaryResult:
        result = cap.execute(
            GetBaselineSummaryQuery(
                incident_id=INCIDENT,
                organism_code=ORG,
                facility_id=FACILITY,
                ward=WARD,
                requested_version=VERSION,
            )
        )
        assert isinstance(result, BaselineSummaryResult)
        return BaselineSummaryResult(
            outcome=CapabilityOutcome.SUCCESS,
            incident_id=result.incident_id,
            incident_version=result.incident_version,
            source_watermark=result.source_watermark,
            signal_evaluation=result.signal_evaluation,
            organism_code=organism_code or result.organism_code,
            facility_id=facility_id or result.facility_id,
            ward=ward or result.ward,
        )

    def test_wrong_baseline_organism_blocks(self) -> None:
        repo = _Repo()
        cap = _capabilities(repo)
        rt = _runtime(
            repo=repo,
            get_baseline_summary=lambda q: self._baseline_result_with(
                cap[2], organism_code="eco"
            ),
        )
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.BLOCKED
        assert result.failure_code is InvestigationExecutionErrorCode.BRANCH_BINDING_MISMATCH
        assert result.is_success() is False

    def test_wrong_baseline_facility_blocks(self) -> None:
        repo = _Repo()
        cap = _capabilities(repo)
        rt = _runtime(
            repo=repo,
            get_baseline_summary=lambda q: self._baseline_result_with(
                cap[2], facility_id="SYNTH-FACILITY-999"
            ),
        )
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.BLOCKED
        assert result.failure_code is InvestigationExecutionErrorCode.BRANCH_BINDING_MISMATCH
        assert result.is_success() is False

    def test_wrong_baseline_ward_blocks(self) -> None:
        repo = _Repo()
        cap = _capabilities(repo)
        rt = _runtime(
            repo=repo,
            get_baseline_summary=lambda q: self._baseline_result_with(
                cap[2], ward="SYNTH-WARD-Z"
            ),
        )
        result = rt.execute(_command())
        assert result.outcome is InvestigationExecutionOutcome.BLOCKED
        assert result.failure_code is InvestigationExecutionErrorCode.BRANCH_BINDING_MISMATCH
        assert result.is_success() is False


class TestRunStateCleanup:
    """P2: run-scoped carriers are released on every terminal path."""

    def _assert_empty(self, runtime: EventInvestigationRuntime) -> None:
        assert runtime._capability_results == {}
        assert runtime._joined_results == {}
        assert runtime._run_telemetry == {}
        assert runtime._last_attempt == {}
        assert runtime._run_budget == {}

    def test_successful_terminal_cleans_run_scoped_state(self) -> None:
        runtime = _runtime()
        for _ in range(10):
            result = runtime.execute(_command())
            assert result.outcome is InvestigationExecutionOutcome.READY_FOR_DOWNSTREAM
            self._assert_empty(runtime)

    def test_blocked_terminal_cleans_run_scoped_state(self) -> None:
        def failing(query: CompareProfilesQuery) -> ProfileComparisonResult:
            result = _capabilities(_Repo())[1].execute(query)
            return ProfileComparisonResult(
                outcome=CapabilityOutcome.REQUIRED_CAPABILITY_FAILED,
                incident_id=result.incident_id,
                incident_version=result.incident_version,
                source_watermark=result.source_watermark,
                finding=None,
                finding_reference=None,
                isolate_id_a=result.isolate_id_a,
                isolate_id_b=result.isolate_id_b,
            )

        runtime = _runtime(compare_profiles=failing)
        for _ in range(10):
            result = runtime.execute(_command())
            assert result.outcome is InvestigationExecutionOutcome.BLOCKED
            self._assert_empty(runtime)

    def test_timeout_terminal_cleans_run_scoped_state(self) -> None:
        import time

        def slow(query: GetBaselineSummaryQuery) -> BaselineSummaryResult:
            del query
            time.sleep(2.0)
            raise AssertionError("should never return")

        runtime = _runtime(
            get_baseline_summary=slow,
            budget=_budget(max_runtime_seconds=0.8),
        )
        for _ in range(5):
            result = runtime.execute(_command())
            assert result.outcome is InvestigationExecutionOutcome.FAILED
            assert result.failure_code is InvestigationExecutionErrorCode.EXECUTION_TIMEOUT
            self._assert_empty(runtime)
