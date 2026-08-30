"""Deterministic tests for the Issue #49 ADK/Gemini capability spike.

These tests exercise the real ADK 2.8 ``Workflow`` graph and ``Runner`` with
an injectable ``SpikeFakeLlm``, so no paid model call is required in CI. They
prove the orchestration semantics: non-chat invocation, parallel/join, a
single bounded repair, deterministic verifier routing, and fail-closed
blocking on required-branch failure / fabricated reference / malformed output.
"""

from __future__ import annotations

import json

from ngabo.application.enums.spike_verification_code import SpikeVerificationCode
from ngabo.application.services.spike_proof_verifier import (
    BranchResult,
    SpikeProofVerifier,
    VerificationContext,
)
from ngabo.domain.enums.claim_type import ClaimType
from ngabo.domain.enums.spike_outcome import SpikeOutcome
from ngabo.domain.value_objects.spike_proof_claim import SpikeProofClaim
from ngabo.infrastructure.adk.fake_llm import SpikeFakeLlm
from ngabo.infrastructure.adk.live_capability import _redacted_result, _vertex_mode_from
from ngabo.infrastructure.adk.spike_adapter import SpikeRunResult, run_spike


def _context() -> VerificationContext:
    return VerificationContext(
        known_record_ids=frozenset({"rec-01"}),
        known_finding_ids=frozenset({"finding-amr-a", "finding-amr-b"}),
        known_source_ids=frozenset({"src-01"}),
        known_claim_ids=frozenset({"claim-01", "claim-02"}),
    )


def _valid_claim_json(*, finding_ids: list[str] | None = None) -> str:
    return json.dumps(
        {
            "claim_id": "claim-01",
            "claim_type": "DERIVED_FINDING",
            "statement": "suspected clonal cluster in source data",
            "supporting_record_ids": ["rec-01"],
            "supporting_finding_ids": finding_ids or ["finding-amr-a", "finding-amr-b"],
            "supporting_source_ids": ["src-01"],
            "contradicting_claim_ids": [],
            "uncertainties": ["coverage is incomplete"],
            "requested_action_class": "A0",
            "confidence_label": "low",
        }
    )


def _malformed_json() -> str:
    return json.dumps({"claim_id": "not-a-claim", "statement": 42})


class TestVerifier:
    def test_valid_claim_passes_verifier(self) -> None:
        verifier = SpikeProofVerifier(_context())
        claim = SpikeProofClaim(
            claim_id="claim-01",
            claim_type=ClaimType.DERIVED_FINDING,
            statement="suspected clonal cluster",
            supporting_finding_ids=("finding-amr-a", "finding-amr-b"),
        )
        branches = (
            BranchResult("branch_a", ok=True, finding_id="finding-amr-a"),
            BranchResult("branch_b", ok=True, finding_id="finding-amr-b"),
        )
        report = verifier.verify(claim, branches)
        assert report.valid is True
        assert report.errors == ()

    def test_required_branch_failure_blocks(self) -> None:
        verifier = SpikeProofVerifier(_context())
        claim = SpikeProofClaim(
            claim_id="claim-01",
            claim_type=ClaimType.DERIVED_FINDING,
            statement="suspected clonal cluster",
            supporting_finding_ids=("finding-amr-a",),
        )
        branches = (
            BranchResult("branch_a", ok=True, finding_id="finding-amr-a"),
            BranchResult(
                "branch_b",
                ok=False,
                failure_reason="branch_b produced no valid output",
            ),
        )
        report = verifier.verify(claim, branches)
        assert report.valid is False
        assert report.errors[0].code is SpikeVerificationCode.REQUIRED_BRANCH_FAILED
        assert report.errors[0].field == "branch_b"

    def test_fabricated_finding_reference_rejected(self) -> None:
        verifier = SpikeProofVerifier(_context())
        claim = SpikeProofClaim(
            claim_id="claim-01",
            claim_type=ClaimType.DERIVED_FINDING,
            statement="suspected clonal cluster",
            supporting_finding_ids=("finding-does-not-exist",),
        )
        branches = (
            BranchResult("branch_a", ok=True, finding_id="finding-amr-a"),
            BranchResult("branch_b", ok=True, finding_id="finding-amr-b"),
        )
        report = verifier.verify(claim, branches)
        assert report.valid is False
        assert report.errors[0].code is SpikeVerificationCode.UNKNOWN_FINDING_REFERENCE

    def test_derived_finding_without_findings_blocks(self) -> None:
        # A proof-free DERIVED_FINDING must not be accepted (P1).
        verifier = SpikeProofVerifier(_context())
        claim = SpikeProofClaim(
            claim_id="claim-01",
            claim_type=ClaimType.DERIVED_FINDING,
            statement="suspected clonal cluster",
        )
        branches = (
            BranchResult("branch_a", ok=True, finding_id="finding-amr-a"),
            BranchResult("branch_b", ok=True, finding_id="finding-amr-b"),
        )
        report = verifier.verify(claim, branches)
        assert report.valid is False
        assert report.errors[0].code is SpikeVerificationCode.MISSING_REQUIRED_REFERENCE
        assert report.errors[0].field == "supporting_finding_ids"

    def test_fabricated_contradicting_claim_blocks(self) -> None:
        # A fabricated contra claim ID must not pass (P2).
        verifier = SpikeProofVerifier(_context())
        claim = SpikeProofClaim(
            claim_id="claim-03",
            claim_type=ClaimType.DERIVED_FINDING,
            statement="suspected clonal cluster",
            supporting_finding_ids=("finding-amr-a", "finding-amr-b"),
            contradicting_claim_ids=("claim-does-not-exist",),
        )
        branches = (
            BranchResult("branch_a", ok=True, finding_id="finding-amr-a"),
            BranchResult("branch_b", ok=True, finding_id="finding-amr-b"),
        )
        report = verifier.verify(claim, branches)
        assert report.valid is False
        assert report.errors[0].code is SpikeVerificationCode.UNKNOWN_CLAIM_REFERENCE
        assert report.errors[0].field == "contradicting_claim_ids"


class TestSpikeGraph:
    def test_success_event_invoked(self) -> None:
        fake = SpikeFakeLlm(responses=[_valid_claim_json()])
        result = run_spike(
            {"synthetic": True},
            model=fake,
            context=_context(),
        )
        assert result.status is SpikeOutcome.ACCEPTED
        assert result.claim is not None
        assert result.verification is not None
        assert result.verification.valid is True
        assert fake.call_count == 1

    def test_required_branch_failure_blocks(self) -> None:
        fake = SpikeFakeLlm(responses=[_valid_claim_json()])
        result = run_spike(
            {"synthetic": True},
            model=fake,
            context=_context(),
            branch_health=(True, False),
        )
        assert result.status is SpikeOutcome.REQUIRED_BRANCH_FAILED
        assert result.verification is not None
        assert result.verification.valid is False
        assert result.verification.errors[0].code is SpikeVerificationCode.REQUIRED_BRANCH_FAILED

    def test_malformed_output_blocks_before_action(self) -> None:
        fake = SpikeFakeLlm(responses=[_malformed_json()])
        result = run_spike(
            {"synthetic": True},
            model=fake,
            context=_context(),
        )
        # ADK's ``output_schema`` enforces the proof schema and refuses
        # malformed output before it ever reaches the deterministic verifier or
        # any downstream routing: the runner records a MALFORMED_PROOF block.
        assert result.status is SpikeOutcome.MALFORMED_PROOF
        assert result.verification is None

    def test_fabricated_reference_is_bounded_then_blocks(self) -> None:
        # Synthesize and repair BOTH cite a fabricated finding id.
        bad = _valid_claim_json(finding_ids=["finding-does-not-exist"])
        fake = SpikeFakeLlm(responses=[bad, bad])
        result = run_spike(
            {"synthetic": True},
            model=fake,
            context=_context(),
            max_repair=1,
        )
        assert result.status is SpikeOutcome.BLOCKED
        assert result.repair_attempts == 1
        assert result.verification is not None
        assert result.verification.valid is False
        assert result.verification.errors[0].code is SpikeVerificationCode.UNKNOWN_FINDING_REFERENCE
        assert fake.call_count == 2

    def test_bounded_repair_can_recover(self) -> None:
        # First attempt cites a fabricated id; repair corrects to a valid one.
        bad = _valid_claim_json(finding_ids=["finding-does-not-exist"])
        good = _valid_claim_json()
        fake = SpikeFakeLlm(responses=[bad, good])
        result = run_spike(
            {"synthetic": True},
            model=fake,
            context=_context(),
            max_repair=1,
        )
        assert result.status is SpikeOutcome.ACCEPTED
        assert result.repair_attempts == 1
        assert result.verification is not None
        assert result.verification.valid is True
        assert fake.call_count == 2

    def test_repair_receives_structured_errors(self) -> None:
        # Prove the repair turn was fed the deterministic verifier errors,
        # not a "is your evidence valid?" self-assessment.
        bad = _valid_claim_json(finding_ids=["finding-does-not-exist"])
        good = _valid_claim_json()
        fake = SpikeFakeLlm(responses=[bad, good])
        run_spike(
            {"synthetic": True},
            model=fake,
            context=_context(),
            max_repair=1,
        )
        # The second request (repair) must contain the verifier error code.
        assert fake.call_count == 2
        repair_request = fake.requests[1]
        text = "".join(
            getattr(part, "text", "") or "" for part in (repair_request.contents[0].parts or ())
        )
        assert "UNKNOWN_FINDING_REFERENCE" in text


class TestLiveRedaction:
    def test_vertex_mode_detection(self) -> None:
        assert _vertex_mode_from({"GOOGLE_GENAI_USE_VERTEXAI": "true"}) is True
        assert _vertex_mode_from({"GOOGLE_GENAI_USE_VERTEXAI": "1"}) is True
        assert _vertex_mode_from({"GOOGLE_GENAI_USE_VERTEXAI": "TRUE"}) is True
        assert _vertex_mode_from({"GOOGLE_GENAI_USE_VERTEXAI": ""}) is False
        assert _vertex_mode_from({}) is False

    def test_redacted_result_never_exposes_secret_env(self) -> None:
        result = SpikeRunResult(
            status=SpikeOutcome.ACCEPTED,
            claim=None,
            verification=None,
            repair_attempts=0,
            invocation_id=None,
            session_id="spike-abc",
            agent_path="spike_workflow",
        )
        payload = _redacted_result(result)
        as_json = json.dumps(payload)
        assert "GEMINI_API_KEY" not in as_json
        assert "GOOGLE_API_KEY" not in as_json
        assert "api_key" not in as_json.lower()
        assert payload["status"] == "ACCEPTED"
