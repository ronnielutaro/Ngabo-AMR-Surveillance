"""ADK 2.8 Workflow graph + non-interactive runner for the #49 capability spike.

The graph proves the exact runtime shape:

    START → prepare → (branch_a ∥ branch_b) → JoinNode → synthesize
          → verify → {ACCEPT | REPAIR | BLOCK} → (repair ⇄ verify, bounded)

where ``synthesize`` and ``repair`` are real ADK LLM agents (with
``output_schema=ClaimSynthesis``) and ``verify`` is deterministic
application-owned code. ``run_spike`` invokes the workflow WITHOUT an
interactive chat, via ``Runner.run_async``, and returns a framework-free
``SpikeRunResult``.

Dependency direction: Google ADK/Gemini live here (infrastructure); the
deterministic verifier lives in the application layer; the proof carrier is a
domain DTO. No inner layer imports ``google.*``.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from google.adk import Agent, Context, Event, Runner
from google.adk.sessions import InMemorySessionService
from google.adk.workflow import FunctionNode, JoinNode, Workflow
from google.genai import types
from pydantic import ValidationError

from ngabo.application.enums.spike_verification_code import SpikeVerificationCode
from ngabo.application.services.spike_proof_verifier import (
    BranchResult,
    SpikeProofVerifier,
    VerificationContext,
)
from ngabo.application.value_objects.spike_verification_result import (
    SpikeVerificationError,
    SpikeVerificationResult,
)
from ngabo.domain.enums.spike_outcome import SpikeOutcome
from ngabo.domain.value_objects.spike_proof_claim import SpikeProofClaim
from ngabo.infrastructure.adk.claim_synthesis import (
    ClaimSynthesis,
    to_spike_proof_claim,
)

MAX_REPAIR_ATTEMPTS_DEFAULT: int = 1
SYNTHESIZE_INSTRUCTION: str = (
    "You are Ngabo's proof-carrying synthesis step. The user message is the "
    "deterministic evidence context: it contains branch_a and branch_b, each "
    "with a finding_id and output_value. Produce a proof-carrying claim that "
    "cites ONLY finding IDs that actually appear in the provided context. "
    "Set claim_type to exactly the string 'DERIVED_FINDING'. "
    "Set requested_action_class to 'A0'. Return strict JSON matching the "
    "response schema. Do not invent evidence IDs."
)
REPAIR_INSTRUCTION: str = (
    "You are Ngabo's bounded repair step. The user message contains the "
    "original proof-carrying claim, the deterministic evidence context, and "
    "the deterministic verification errors. Return a corrected proof-carrying "
    "claim that fixes every listed error. Use ONLY a claim_type value from the "
    "response schema (prefer 'DERIVED_FINDING'), cite ONLY evidence IDs that "
    "exist in the provided context, and return strict JSON matching the "
    "response schema."
)


@dataclass(frozen=True)
class SpikeRunResult:
    """Framework-free result returned by ``run_spike``."""

    status: SpikeOutcome
    claim: SpikeProofClaim | None
    verification: SpikeVerificationResult | None
    repair_attempts: int
    invocation_id: str | None
    session_id: str
    agent_path: str


def _extract_text(node_input: object) -> str:
    """Best-effort text extraction from the runner's entry message."""
    if isinstance(node_input, types.Content):
        return "".join(
            getattr(part, "text", "") or "" for part in (node_input.parts or ())
        )
    if isinstance(node_input, str):
        return node_input
    return json.dumps(node_input, default=str)


def _branch(ctx: Context, name: str) -> BranchResult:
    stored = ctx.state.get(name)
    if not isinstance(stored, dict):
        return BranchResult(branch_name=name, ok=False, failure_reason="missing branch data")
    finding_id = stored.get("finding_id")
    output_value = stored.get("output_value")
    failure_reason = stored.get("failure_reason")
    return BranchResult(
        branch_name=name,
        ok=bool(stored.get("ok", False)),
        finding_id=finding_id if isinstance(finding_id, str) else None,
        output_value=output_value if isinstance(output_value, str) else None,
        failure_reason=failure_reason if isinstance(failure_reason, str) else None,
    )


def _make_prepare_node() -> FunctionNode:
    def prepare(node_input: object) -> dict[str, str]:
        return {"input": _extract_text(node_input) or "spike"}

    return FunctionNode(func=prepare, name="prepare")


def _make_branch_node(
    name: str, finding_id: str, output_value: str, *, ok: bool = True
) -> FunctionNode:
    def branch(ctx: Context, node_input: object) -> dict[str, object]:
        del node_input
        result: dict[str, object] = {
            "ok": ok,
            "finding_id": finding_id,
            "output_value": output_value,
        }
        if not ok:
            result["failure_reason"] = f"{name} produced no valid output"
        ctx.state[name] = result
        return result

    return FunctionNode(func=branch, name=name)


def _make_verify_node(
    verifier: SpikeProofVerifier,
    *,
    max_repair: int,
) -> FunctionNode:
    def verify(ctx: Context, node_input: object) -> Event:
        claim: SpikeProofClaim | None = None
        try:
            raw = _usable_model_output(node_input) or _recover_model_text(ctx)
            synthesis = _parse_synthesis(raw)
            claim = to_spike_proof_claim(synthesis)
        except (ValidationError, ValueError):  # malformed / invalid enum
            pass

        branches = (_branch(ctx, "branch_a"), _branch(ctx, "branch_b"))
        report = verifier.verify(claim, branches)

        outcome = _classify(claim, report, branches)
        if outcome is SpikeOutcome.ACCEPTED:
            ctx.state["spike_repair_attempts"] = ctx.state.get("spike_repair_attempts", 0)
            return _routed_event(
                {"spike_result": _result_payload(outcome, claim, report, ctx)},
                "ACCEPT",
            )

        if (
            outcome is SpikeOutcome.REQUIRED_BRANCH_FAILED
            or outcome is SpikeOutcome.MALFORMED_PROOF
        ):
            return _routed_event(
                {"spike_result": _result_payload(outcome, None, report, ctx)},
                "BLOCK",
            )

        # Repairable reference-failure path, bounded by max_repair.
        attempts = int(ctx.state.get("spike_repair_attempts", 0))
        if attempts < max_repair:
            ctx.state["spike_repair_attempts"] = attempts + 1
            payload = {
                "claim": _claim_dump(claim),
                "joined": {
                    "branch_a": asdict(_branch(ctx, "branch_a")),
                    "branch_b": asdict(_branch(ctx, "branch_b")),
                },
                "errors": [_error_dict(e) for e in report.errors],
                "attempt": attempts + 1,
            }
            return _routed_event(payload, "REPAIR")

        return _routed_event(
            {"spike_result": _result_payload(SpikeOutcome.BLOCKED, claim, report, ctx)},
            "BLOCK",
        )

    return FunctionNode(func=verify, name="verify")


def _usable_model_output(node_input: object) -> object | None:
    """Return ``node_input`` when it looks like a usable model proposal."""
    if isinstance(node_input, str) and node_input.strip():
        return node_input
    if isinstance(node_input, dict) and node_input:
        return node_input
    return None


def _recover_model_text(ctx: Context) -> str | None:
    """Recover the latest non-thought model text from the canonical session.

    ADK 2.8's ``output_schema`` node delivery sets ``node_input`` to ``None``
    for live Gemini turns even though the structured carrier is emitted as a
    model-role content part. Recovering it from the session keeps the
    deterministic adapter in charge of parsing the proposed carrier and never
    reads private chain-of-thought (thought parts are excluded).
    """
    events = getattr(ctx.session, "events", ())
    for event in reversed(events):
        content = getattr(event, "content", None)
        if content is None:
            continue
        if getattr(content, "role", None) != "model":
            continue
        text = "".join(
            getattr(part, "text", "") or ""
            for part in getattr(content, "parts", ())
            if not getattr(part, "thought", False)
        )
        if text.strip():
            return text
    return None


def _parse_synthesis(node_input: object) -> ClaimSynthesis:
    """Parse the model's proposed proof carrier (JSON text or dict).

    The deterministic adapter owns parsing/validation: Gemini only proposes a
    schema-constrained JSON payload (``generate_content_config``), and this
    code — not the model — decides whether it is structurally usable.
    """
    if isinstance(node_input, str):
        return ClaimSynthesis.model_validate_json(node_input)
    if isinstance(node_input, dict):
        return ClaimSynthesis.model_validate(node_input)
    raise ValueError("model output is not a recognizable proof payload")


def _claim_dump(claim: SpikeProofClaim | None) -> dict[str, object] | None:
    if claim is None:
        return None
    return {
        "claim_id": claim.claim_id,
        "claim_type": claim.claim_type.value,
        "statement": claim.statement,
        "supporting_record_ids": list(claim.supporting_record_ids),
        "supporting_finding_ids": list(claim.supporting_finding_ids),
        "supporting_source_ids": list(claim.supporting_source_ids),
        "contradicting_claim_ids": list(claim.contradicting_claim_ids),
        "uncertainties": list(claim.uncertainties),
        "requested_action_class": claim.requested_action_class.value
        if claim.requested_action_class is not None
        else None,
        "confidence_label": claim.confidence_label,
    }


def _error_dict(error: Any) -> dict[str, str | None]:
    return {
        "code": str(error.code),
        "field": error.field,
        "reference": error.reference,
        "detail": error.detail,
    }


def _routed_event(output: object, route: str) -> Event:
    """Construct an ADK ``Event`` carrying a graph ``route``.

    ADK's ``Event`` accepts ``route`` as a runtime ``extra="allow"`` field
    (verified against the installed 2.8.0 source), but the shipped type stubs
    omit it. This is a single, scoped narrow for that known upstream stub gap,
    not a blanket ignore.
    """
    return Event(output=output, route=route)  # type: ignore[call-arg]


def _classify(
    claim: SpikeProofClaim | None,
    report: SpikeVerificationResult,
    branches: tuple[BranchResult, ...],
) -> SpikeOutcome:
    if not report.valid:
        codes = {error.code for error in report.errors}
        if SpikeVerificationCode.REQUIRED_BRANCH_FAILED in codes:
            return SpikeOutcome.REQUIRED_BRANCH_FAILED
        if SpikeVerificationCode.MALFORMED_PROOF in codes:
            return SpikeOutcome.MALFORMED_PROOF
    return SpikeOutcome.ACCEPTED if report.valid else SpikeOutcome.BLOCKED


def _result_payload(
    outcome: SpikeOutcome,
    claim: SpikeProofClaim | None,
    report: SpikeVerificationResult | None,
    _ctx: Context,
) -> dict[str, object]:
    attempts = int(_ctx.state.get("spike_repair_attempts", 0))
    return {
        "status": outcome.value,
        "claim": _claim_dump(claim),
        "verification": {
            "valid": report.valid if report is not None else False,
            "errors": [_error_dict(e) for e in (report.errors if report is not None else ())],
        },
        "repair_attempts": attempts,
    }


def build_spike_agent(
    model: Any,
    *,
    context: VerificationContext,
    max_repair: int = MAX_REPAIR_ATTEMPTS_DEFAULT,
    branch_health: tuple[bool, bool] = (True, True),
) -> Workflow:
    """Build the ADK Workflow graph for the spike."""
    verifier = SpikeProofVerifier(context)
    synthesize = Agent(
        name="synthesize",
        model=model,
        output_schema=ClaimSynthesis,
        instruction=SYNTHESIZE_INSTRUCTION,
    )
    repair = Agent(
        name="repair",
        model=model,
        output_schema=ClaimSynthesis,
        instruction=REPAIR_INSTRUCTION,
    )
    prepare_node = _make_prepare_node()
    branch_a = _make_branch_node("branch_a", "finding-amr-a", "0.42", ok=branch_health[0])
    branch_b = _make_branch_node("branch_b", "finding-amr-b", "0.17", ok=branch_health[1])
    join = JoinNode(name="join")
    verify_node = _make_verify_node(verifier, max_repair=max_repair)

    def accept(node_input: object) -> dict[str, object]:
        return (
            node_input
            if isinstance(node_input, dict)
            else {"spike_result": {"status": "ACCEPTED"}}
        )

    def block(node_input: object) -> dict[str, object]:
        return (
            node_input
            if isinstance(node_input, dict)
            else {"spike_result": {"status": "BLOCKED"}}
        )

    accept_node = FunctionNode(func=accept, name="accept")
    block_node = FunctionNode(func=block, name="block")

    return Workflow(
        name="spike_workflow",
        edges=[
            ("START", prepare_node),
            (prepare_node, (branch_a, branch_b)),
            ((branch_a, branch_b), join),
            (join, synthesize),
            (synthesize, verify_node),
            (verify_node, {"ACCEPT": accept_node, "REPAIR": repair, "BLOCK": block_node}),
            (repair, verify_node),
        ],
    )


def _message_text(input_event: object) -> str:
    if isinstance(input_event, str):
        return input_event
    return json.dumps(input_event, default=str)


def _is_schema_validation_error(exc: BaseException) -> bool:
    """True if ``exc`` (or its cause chain) is a structured-output schema failure."""
    cursor: BaseException | None = exc
    while cursor is not None:
        if isinstance(cursor, ValidationError):
            return True
        type_name = type(cursor).__name__.lower()
        if "validation" in type_name and "error" in type_name:
            return True
        cursor = cursor.__cause__ if cursor.__cause__ is not None else cursor.__context__
    return False


async def run_spike_async(
    input_event: object,
    *,
    model: Any,
    context: VerificationContext,
    max_repair: int = MAX_REPAIR_ATTEMPTS_DEFAULT,
    branch_health: tuple[bool, bool] = (True, True),
    user_id: str = "ngabo-spike-user",
    session_id: str | None = None,
    invocation_id: str | None = None,
    app_name: str = "ngabo-adk-spike",
) -> SpikeRunResult:
    """Invoke the ADK workflow non-interactively and return the terminal result.

    This is the executable proof that a backend event can start the ADK
    runtime without ``adk web`` / an interactive chat. It returns a
    framework-free ``SpikeRunResult`` for the caller to record.
    """
    agent = build_spike_agent(
        model,
        context=context,
        max_repair=max_repair,
        branch_health=branch_health,
    )
    session_service = InMemorySessionService()
    runner = Runner(
        node=agent,
        app_name=app_name,
        session_service=session_service,
        auto_create_session=True,
    )
    resolved_session_id = session_id or f"spike-{uuid.uuid4().hex}"
    events: list[Event] = []
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=resolved_session_id,
            invocation_id=invocation_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=_message_text(input_event))],
            ),
        ):
            events.append(event)
    except Exception as exc:  # ADK enforces output_schema; treat refusal as a block.
        if _is_schema_validation_error(exc):
            return SpikeRunResult(
                status=SpikeOutcome.MALFORMED_PROOF,
                claim=None,
                verification=None,
                repair_attempts=0,
                invocation_id=invocation_id,
                session_id=resolved_session_id,
                agent_path="spike_workflow",
            )
        raise

    terminal: dict[str, object] | None = None
    for event in events:
        if isinstance(event.output, dict) and "spike_result" in event.output:
            terminal = event.output["spike_result"]

    if terminal is None:
        raise RuntimeError("ADK spike produced no terminal spike_result; graph misconfigured")

    return _build_spike_run_result(terminal, resolved_session_id, invocation_id)


def run_spike(
    input_event: object,
    *,
    model: Any,
    context: VerificationContext,
    max_repair: int = MAX_REPAIR_ATTEMPTS_DEFAULT,
    branch_health: tuple[bool, bool] = (True, True),
    user_id: str = "ngabo-spike-user",
    session_id: str | None = None,
    invocation_id: str | None = None,
    app_name: str = "ngabo-adk-spike",
) -> SpikeRunResult:
    """Synchronous convenience wrapper around ``run_spike_async``."""
    return asyncio.run(
        run_spike_async(
            input_event,
            model=model,
            context=context,
            max_repair=max_repair,
            branch_health=branch_health,
            user_id=user_id,
            session_id=session_id,
            invocation_id=invocation_id,
            app_name=app_name,
        )
    )


def _build_spike_run_result(
    terminal: dict[str, object],
    session_id: str,
    invocation_id: str | None,
) -> SpikeRunResult:
    status = SpikeOutcome(str(terminal.get("status", SpikeOutcome.BLOCKED.value)))
    claim = _claim_from_payload(terminal.get("claim"))
    verification = _verification_from_payload(terminal.get("verification"))
    raw_attempts = terminal.get("repair_attempts", 0)
    repair_attempts = raw_attempts if isinstance(raw_attempts, int) else 0
    return SpikeRunResult(
        status=status,
        claim=claim,
        verification=verification,
        repair_attempts=repair_attempts,
        invocation_id=invocation_id,
        session_id=session_id,
        agent_path="spike_workflow",
    )


def _claim_from_payload(payload: object) -> SpikeProofClaim | None:
    if not isinstance(payload, dict):
        return None
    try:
        return to_spike_proof_claim(ClaimSynthesis.model_validate(payload))
    except (ValidationError, ValueError):
        return None


def _verification_from_payload(payload: object) -> SpikeVerificationResult | None:
    if not isinstance(payload, dict):
        return None
    valid = bool(payload.get("valid", False))
    errors: list[Any] = []
    for raw in payload.get("errors", []) if isinstance(payload.get("errors"), list) else []:
        if isinstance(raw, dict):
            errors.append(
                SpikeVerificationError(
                    code=SpikeVerificationCode(str(raw.get("code"))),
                    reference=_optional_str(raw.get("reference")),
                    field=_optional_str(raw.get("field")),
                    detail=_optional_str(raw.get("detail")),
                )
            )
    return SpikeVerificationResult(valid=valid, errors=tuple(errors))


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None
