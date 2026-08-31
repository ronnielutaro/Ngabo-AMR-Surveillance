# Ngabo — Google ADK Capability Spike

**Status:** Required before implementing the v0.1 agent runtime  
**Date:** 2026-08-17

---

## 1. Purpose

Ngabo's architecture is graph-first, resumable, observable, and now requires **Proof-Carrying Autonomy**. Workshop terminology and rapidly evolving ADK APIs must not be treated as stable implementation names without verification.

Before writing production ADK orchestration, perform a small executable capability spike against the **exact pinned Google ADK Python version** that the repository will ship.

The goal is to remove framework/API uncertainty before it can threaten the hackathon critical path.

### Official Google documentation rule

Before implementing any Google ADK, Gemini, Vertex AI, Firestore, Pub/Sub, Cloud Storage, Cloud Run, or related Google integration, the coding agent **must consult the current official Google documentation for the exact SDK/API/version being used** and, where applicable, the current Google GEAR learning resources.

Repository architecture/governance defines Ngabo's required semantics; current official Google materials define how those semantics are implemented using supported APIs. Do **not** implement Google behavior from model memory, workshop screenshots, blog posts, stale examples, or assumed class/API names when current official documentation is available. Pin exact dependencies/versions where applicable, verify material API assumptions with a small executable capability proof, and record material version/API/fallback decisions in the implementation PR.

---

## 2. Required Outputs

The spike must produce:

1. exact Python version;
2. exact `google-adk` version;
3. exact Gemini model configuration;
4. a tiny runnable orchestration example;
5. a mapping from Ngabo architecture concepts to supported ADK primitives;
6. explicit fallback choices for any workshop primitive not available/stable;
7. tests proving the selected implementation path works;
8. proof that Gemini structured output can be parsed into Ngabo's proof-carrying DTO/schema;
9. proof that deterministic claim verification remains outside Gemini/ADK authority;
10. a short result section in this document or an ADR amendment.

Do not merge graph runtime implementation until this spike is green.

---

## 3. Capabilities to Verify

### Core agent/tool runtime

- LLM agent construction;
- ordinary function tools;
- structured outputs / schema-constrained output path;
- invocation/session identifiers;
- callbacks/lifecycle hooks;
- configured model/tool/time/loop bounds where supported.

### Proof-Carrying Autonomy compatibility

Verify the chosen ADK/Gemini path can return a typed object equivalent to:

```text
claim_id
claim_type
statement
supporting_record_ids[]
supporting_finding_ids[]
supporting_source_ids[]
contradicting_claim_ids[]
uncertainties[]
requested_action_class
confidence_label
```

The spike must demonstrate:

- valid structured output parses successfully;
- malformed output is caught before action;
- model output can be passed to ordinary deterministic Python/application verification;
- verifier result—not model self-assessment—controls downstream route;
- verifier can return stable structured error codes to a bounded repair call;
- private chain-of-thought is neither required nor persisted as proof.

### Deterministic orchestration

Determine supported implementation for:

- sequential execution;
- parallel execution;
- join/synchronization;
- fixed deterministic routing;
- deterministic Python/function work inside workflow;
- passing typed outputs between stages;
- routing verifier failure to bounded repair or abstention.

If exact first-class `function node` / `join node` workshop API is unavailable, preserve architecture using supported ADK workflow agents and ordinary Python/application orchestration rather than inventing unsupported APIs.

### Resumability / long-running execution

Verify:

- resumability configuration/API;
- human-input or pause/resume primitives if relevant to non-hero evaluation paths;
- long-running function/tool primitives;
- session persistence requirements;
- what survives process restart;
- what must remain in Firestore/application state;
- proof/package verification status can be rebuilt/rechecked from canonical state after restart.

### Evaluation / observability

Verify:

- eval dataset format;
- trajectory/tool evaluation support;
- trace identifiers;
- Cloud Trace/OpenTelemetry path;
- safe content-capture controls;
- Agents CLI compatibility if used;
- custom metadata/events for `CLAIM_VERIFICATION_*` and repair events where practical.

---

## 4. Architecture Preservation Rule

Framework APIs may change. Ngabo's dependency direction may not.

```text
ADK primitive
     ↓
infrastructure adapter
     ↓
application use case/query/port
     ↓
domain policy
```

Proof verification stays inside application/domain contracts and does not depend on Google SDK classes.

If ADK requires a different outer composition shape, change infrastructure implementation—not domain/application contract merely to fit vendor APIs.

---

## 5. Graph Fallback Ladder

Use simplest supported mechanism preserving semantics.

### Preferred

First-class supported ADK graph/workflow primitives expressing:

```text
context
→ parallel deterministic work
→ join
→ Gemini triage
→ approved evidence
→ Gemini proof-carrying synthesis
→ deterministic claim verifier
→ bounded repair / abstention
```

### Fallback A

Supported `SequentialAgent` / `ParallelAgent` / related workflow agents plus thin custom deterministic adapters.

### Fallback B

Application-owned deterministic workflow state machine invokes bounded ADK agent nodes at model-reasoning boundaries.

Fallback B is acceptable because business workflow and proof policy are application-owned; ADK still provides the actual Gemini agent runtime, capability integration, sessions/evals/observability.

Do **not**:

- invent undocumented ADK class names;
- block the hackathon waiting for a preview API;
- move scientific/proof/action policy into prompts to fit framework abstraction;
- add LangGraph or another orchestration framework merely because an ADK primitive is missing.

---

## 6. Minimum Spike Scenario

The spike need not use AMR data initially.

It must prove this shape:

```text
input
  ↓
deterministic context function
  ↓
parallel deterministic function A + B
  ↓
join
  ↓
Gemini structured proof-carrying decision
  ↓
deterministic verifier
  ├─ valid → structured result
  └─ invalid → structured errors → bounded repair → verifier
```

Then repeat with:

1. a controlled required-branch failure and prove downstream synthesis does not falsely report success;
2. a fabricated proof reference and prove deterministic verifier blocks continuation;
3. a deliberately malformed structured model output and prove it cannot reach action routing.

---

## 7. Zero-Human Hero Compatibility

Selected ADK path must support canonical autonomous hero without requiring an interactive prompt once event handler starts workflow.

Runtime API must allow application to invoke/run agent workflow from a Pub/Sub-triggered process or equivalent backend event path.

`adk web` / developer playground interaction is not evidence of Taskmaster autonomy.

---

## 8. Version Pinning

Once spike passes:

- pin exact runtime dependency in `uv.lock`;
- record version in README/EVALUATION/deployment evidence;
- do not upgrade during demo freeze unless fixing a blocking defect;
- rerun graph/proof/resume/eval tests after any ADK version change.

---

## 9. Acceptance Criteria

- [ ] exact ADK Python version recorded;
- [ ] exact supported orchestration primitives recorded;
- [ ] parallel deterministic execution proven;
- [ ] join/failure semantics proven;
- [ ] proof-carrying structured Gemini output proven;
- [ ] deterministic claim-verifier boundary proven;
- [ ] fabricated reference blocks downstream continuation;
- [ ] bounded repair route proven;
- [ ] backend/event invocation proven without interactive chat;
- [ ] resume API/fallback decision recorded;
- [ ] eval/observability path recorded;
- [ ] framework fallback selected if workshop terminology differs;
- [ ] no unsupported API assumptions remain in implementation plan.

---

## 10. RESULTS (Issue #49 — 2026-08-30)

The spike was executed against the exact pinned runtime in
`services/core/pyproject.toml` / `uv.lock`.

### Exact versions

- Python: **3.11** (project target `requires-python >=3.11`; verified 3.11.15)
- `google-adk`: **2.8.0**
- `google-genai`: **2.20.0** (pinned `<3.0.0` per upstream guidance; exact
  resolved version recorded)
- Gemini model (live proof): **`gemini-3.6-flash`** — `gemini-2.5-flash` is no
  longer available to new users (404 from the API; official guidance points
  to `gemini-3.6-flash`)

### Supported primitives (verified first-hand against 2.8.0)

- sequential: `Workflow(edges=[("START", a, b, ...)])` — chains are linear;
  Python `FunctionNode` steps along an edge run in order.
- parallel: `Workflow(edges=[("START", (node_a, node_b), join)])` — a tuple
  element flattens into parallel fan-out.
- join: `JoinNode` — a barrier that waits for all predecessors and passes
  through the aggregated per-node outputs as `node_input`.
- function tools: `FunctionNode(func=..., name=...)`; bound pre-existing SQL
  framework, plus `google.adk.tools.FunctionTool`/`@tool` for tools; a node
  can be a generator and yield `Event(output=..., route=...)` for routing.
- structured output: `Agent(output_schema=<Pydantic>)`; Gemini is constrained
  to produce the structured carrier; deterministic adapter parses it.
- callbacks: `LlmAgent` exposes `before_model_callback`, `after_model_callback`,
  `before_agent_callback`, `after_agent_callback`, `before_tool_callback`,
  `after_tool_callback`, `on_model_error_callback`.
- sessions: `InMemorySessionService` (and `DatabaseSessionService` /
  `VertexAiSessionService`); `Session`/`State` available.
- eval: `google.adk.evaluation` module present; trajectory/tool evaluation
  package exists (full Ngabo eval suite is a later issue).
- tracing/observability: ADK is wired to OpenTelemetry (pulls
  `opentelemetry-*`); `InvocationContext` carries `invocation_id`/`session_id`.
- resumability: `Runner.run_async(..., invocation_id=...)`; documented decision
  below (application/Firestore owns canonical proof state).

### Selected runtime path / fallback level

**Preferred-level ADK graph** for orchestration plus **Fallback B** reasoning
boundary:

```text
START → prepare → (branch_a ∥ branch_b) → JoinNode → synthesize (ADK Agent,
  output_schema=ClaimSynthesis) → verify (deterministic FunctionNode)
  → {ACCEPT | REPAIR | BLOCK} → (repair ⇄ verify, bounded)
```

`Runner.run_async(...)` is invoked programmatically (non-interactive — no
`adk web`, no chat). The graph owns deterministic parallel/join and the
single bounded repair loop. The deterministic verifier (application-owned)
owns accept/reject; Gemini never self-verifies.

### Proof-Carrying Autonomy compatibility: **PASS**

`ClaimSynthesis` -> `SpikeProofClaim` (domain DTO) -> `SpikeProofVerifier`
(deterministic). Live `gemini-3.6-flash` produced a schema-valid
`DERIVED_FINDING` carrier; the verifier accepted it (`valid: true`).

### Deterministic verifier boundary: **PASS**

Verifier checks required-branch completeness, DTO structural validity, and
the proof-reference family required by the claim type (so a proof-free claim
cannot be accepted), and record/finding/source/contradicting-claim reference
existence. Error codes:
`UNKNOWN_RECORD_REFERENCE`, `UNKNOWN_FINDING_REFERENCE`,
`UNKNOWN_SOURCE_REFERENCE`, `UNKNOWN_CLAIM_REFERENCE`,
`MISSING_REQUIRED_REFERENCE`, `MALFORMED_PROOF`, `REQUIRED_BRANCH_FAILED`.
No model self-"is my evidence valid?" answer is used for routing.

### Bounded repair: **PASS**

`max_repair` default = 1. A fabricated-reference failure is fed back to a
repair Agent as structured verifier errors; if still invalid after the bound,
the workflow routes to `BLOCK`. The bound is enforced (no unbounded loop).

### Backend non-chat invocation: **PASS**

`run_spike(...)` calls `Runner.run_async(user_id, session_id, new_message,
invocation_id)` from plain application/Python code; a synthetic event dict is
the entry message. No interactive chat required.

### Cloud Run proof: **PASS**

The exact locked deps and the `ngabo-adk-spike` console entry are shipped.
`live_capability.py` supports both an API-key developer path
(`GEMINI_API_KEY`) and the **keyless Vertex path** (`GOOGLE_GENAI_USE_VERTEXAI=true`
with ADC/WIF and a Vertex/Gemini caller grant).

Disposable Cloud Run Job verification (post-merge, develop `7478e68e`):

- source SHA: `7478e68e8c1f510231365d19a556eeea4c8b7c83`
- core image digest: `sha256:17bdabb957fc6e3426ef30011167ae58965b1cbdfbbd82e716e4586bc32866a1`
- job/execution: `ngabo-adk-spike-proof-x4zr2` (and `-cxncb`), `succeeded`
- ADK version / model: `google-adk==2.8.0` / `gemini-3.6-flash`
- result: `status=ACCEPTED`, claim `claim-101` (`DERIVED_FINDING`),
  `verification.valid=true`, `repair_attempts=0`

Keyless Vertex note: the project `aiplatform.googleapis.com` was enabled for
the keyless path, but the Agent Platform API returned `SERVICE_DISABLED`
until propagation. The disposable proof was therefore completed via the
developer-API path with a temporary Secret Manager key (never printed); the
temp SA/secret/job were deleted afterward. The keyless Vertex path is expected
to work once the AI Platform activation fully propagates.

### Material unsupported / ambiguous APIs

- **ADK `output_schema` node delivery is unreliable for live Gemini**: for
  `gemini-3.6-flash` / `gemini-3.5-flash`, the structured carrier is emitted
  as a model-role content part but the workflow-node `node_input` is `None`
  (the shipped type-stub `Event` also omits `route`). The spike adapter
  recovers the proposed carrier from the canonical `ctx.session` events and
  parses it deterministically. Documented as a decision, not a blocker.
- `generate_content_config.response_schema` is rejected by ADK 2.8
  (`Response schema must be set via LlmAgent.output_schema`); use `output_schema`.
- `thinking_config` (`thinking_budget=0`) alongside `output_schema` returned
  `400 INVALID_ARGUMENT` for `gemini-3.6-flash`; avoid it.

### Official documentation consulted (date 2026-08-30)

- https://pypi.org/project/google-adk/ (2.8.0)
- https://pypi.org/project/google-genai/ (2.20.0; pin <3.0.0 guidance)
- https://adk.dev/get-started/python/
- https://github.com/google/adk-docs (Workflow agents, graph-routes)
- https://github.com/google/adk-python (Workflow engine, JoinNode, Runner,
  `_llm_agent_wrapper.process_llm_agent_output`)
- https://ai.google.dev/gemini-api/docs/libraries

Primary API verification was performed first-hand against the installed
`google-adk==2.8.0` / `google-genai==2.20.0` source (imports, model fields,
edge parsing, `FunctionNode` parameter binding, `Runner.run_async`) and by
running an executable `Workflow` probe with a `JoinNode` and an `Agent` with a
controllable `BaseLlm` fake.

---

## 11. Production event-invoked outer adapter (Issue #53 — 2026-08-31)

Issue #49 proved the capability spike. Issue #53 ships the
**production outer ADK execution boundary** that later orchestration (#54+)
plugs into. It does NOT implement the #54 fan-out/join or any synthesis.

### Production adapter entry point

`services/core/ngabo/infrastructure/adk/investigation_runtime.py`:

- `EventInvestigationRuntime` — DI composition root. A backend/event-shaped
  `EventInvestigationCommand` is accepted and run through the real pinned ADK
  `Runner`/`Workflow`/`FunctionNode` path with NO interactive chat, `adk web`,
  or user prompt.
- framework-free inbound command/result/telemetry contracts live in
  `services/core/ngabo/application/value_objects/investigation_execution.py`
  and the two enums under `application/enums/`.

### Pinned ADK path reused

- actual installed runtime: `google-adk==2.8.0`, `google-genai==2.20.0`,
  Python 3.11 (verified via `importlib.metadata`, asserted in tests).
- all-deterministic single-node `Workflow(edges=[("START", FunctionNode)])`.
  **No `Agent`, no model call** — the #53 deterministic path uses
  `model_calls == 0`.
- the thin `FunctionNode` is `async def`; the injected sync inward capability
  is awaited via `asyncio.to_thread` so a slow deterministic fetch never blocks
  the event loop and the outer `asyncio.wait_for` deadline can preempt it
  (fail closed).

### Session strategy

`InMemorySessionService` + `auto_create_session=True` per invocation is an
**execution-runtime adapter choice** for this boundary. It is explicitly NOT
canonical incident state. ADK session state ≠ Ngabo canonical incident state; a
future durable-repository issue owns persistence. No Firestore/PubSub/Cloud
Storage adapter was introduced.

### Invocation identifiers

One `InvestigationExecutionId` (`RUN-<32 hex>`), `session_id`
(`ngabo-session-<hex>`), and `invocation_id` (`ngabo-invocation-<hex>`) are
generated once at the adapter boundary and propagated into the machine envelope
and ADK. ADK `user_id` is only an ADK runtime namespace
(`ngabo-service`); it is never patient/clinician identity or an authorization
principal.

### Budget enforcement owners

- `max_runtime_seconds`: enforced by `asyncio.wait_for` around `Runner` (fail
  closed on `EXECUTION_TIMEOUT`).
- `max_tool_calls`: enforced inside the thin wrapper before invoking the inward
  capability (fail closed on `EXECUTION_BUDGET_EXCEEDED`).
- `max_model_calls`: no model call on the deterministic path; observed 0.
- `max_loop_iterations` / `max_repair_attempts`: no loop/repair stage exists in
  this boundary; recorded as configuration only (not claimed as enforced).

### Zero-chat backend invocation proof

`tests/test_investigation_runtime.py` runs the real ADK 2.8 runtime with an
in-memory deterministic inward capability and asserts:

- event-shaped command -> adapter -> ADK `Runner` -> thin wrapper -> typed
  `InvestigationContextResult` -> structured `EventInvocationResult`;
- `run_id`/`session_id`/`invocation_id` are emitted and internally consistent
  (the wrapper reads the real ADK `ctx.session.id` /
  `ctx.get_invocation_context().invocation_id` and the runtime cross-checks);
- missing incident / stale version / inward failure / wrapper exception /
  timeout / budget-exceeded all produce stable non-success outcomes;
- `model_calls == 0` on the deterministic path;
- replay is safe (no side effects, no action authority);
- the outcome vocabulary contains NO `PACKAGE_COMPLETED` / `VERIFIED` /
  `ACTION_READY` state, so a failure can never be mislabeled as package success.

Machine-readable success + failure trace fixtures are committed under
`services/core/tests/fixtures/`.

### Explicit #53 / #54 boundary

#53 owns the OUTER event/ADK seam only. It does NOT implement the #54
production three-branch fan-out/join semantics, concurrent-branch retry/timeout,
required-branch-blocking-synthesis, evidence retrieval wiring, package
synthesis, claim verification, repair loop, or any external action.

### Residual limitations

- `InMemorySessionService` is not durable/restart-safe (canonical state must
  stay application-owned; deferred persistence).
- `max_loop_iterations` / `max_repair_attempts` are configured but not enforced
  in this boundary.
- The run generates fresh opaque identifiers per invocation (freshness policy is
  explicitly out of #53); replay/idempotency identity is a #54/later concern.
