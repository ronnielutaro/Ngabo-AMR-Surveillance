# Ngabo — Google ADK Runtime, Resumability & Evaluation Contract

**Status:** Required v0.1 agent-runtime contract  
**Applies to:** `services/core/ngabo/infrastructure/ai/adk` and the application workflows it drives

---

## 1. Objective

Ngabo must use Google ADK as a real agent runtime rather than a thin wrapper around a single Gemini call.

The ADK runtime is responsible for orchestrating a bounded investigation across tools, preserving agent execution continuity, requesting targeted human input when necessary, and producing a validated structured incident package.

ADK remains an **outer infrastructure concern** under Clean Architecture. Ngabo's scientific/domain rules and authoritative workflow state do not depend on ADK classes.

---

## 2. Clean Architecture Boundary

```text
Google ADK / Gemini
        ↓
infrastructure adapter
        ↓
application workflow / ports
        ↓
domain entities + deterministic services
```

Allowed:

```text
ADK tool adapter -> application query/use case
ADK orchestrator -> application ports
application -> domain
```

Forbidden:

```text
domain -> google.adk
application use case -> Gemini SDK directly
ADK tool -> Firestore directly
ADK tool -> Pub/Sub directly
ADK tool -> notification provider directly
```

All infrastructure access flows through application-defined ports.

---

## 3. Orchestrator Scope

The Ngabo Orchestrator may:

- inspect a persisted incident through bounded tools;
- choose which approved investigation tool to invoke;
- compare existing deterministic outputs;
- retrieve approved evidence;
- identify missing information;
- request targeted clarification;
- resume after clarification;
- construct labelled hypotheses;
- prepare a schema-constrained incident package;
- stop when evidence is insufficient.

The orchestrator may not:

- create the surveillance signal;
- calculate AST statistics itself;
- alter canonical isolate facts;
- prescribe antimicrobial treatment;
- confirm an outbreak;
- send external notifications directly;
- bypass review;
- fabricate evidence.

---

## 4. Required Tools

The runtime tool surface should remain small and typed.

Core v0.1 tools:

```text
get_incident_context()
compare_resistance_profiles()
get_baseline_summary()
get_missing_fields()
search_approved_guidance()
request_clarification()
prepare_incident_package()
```

Optional supporting tools may be added only if they have a clear investigation purpose.

Every tool should define:

- typed input schema;
- typed output schema;
- whether it is read-only or side-effecting;
- authorization expectations;
- timeout;
- retry behavior;
- idempotency behavior where applicable;
- error categories.

---

## 5. Tool Execution Rule

The model may decide **which tool to call**.

It must not decide the authoritative result of a deterministic calculation.

Example:

```text
Agent:
“Compare the resistance profiles for this incident.”
        ↓
compare_resistance_profiles()
        ↓
deterministic Python implementation
        ↓
validated similarity result
        ↓
Agent interprets result
```

Not:

```text
Agent reads AST text and estimates similarity itself.
```

---

## 6. Agent Execution Identity

Persist enough execution metadata to correlate an Ngabo incident with its ADK execution.

Suggested application-level record:

```json
{
  "incident_id": "...",
  "agent_session_id": "...",
  "agent_invocation_id": "...",
  "agent_run_id": "...",
  "agent_run_status": "RUNNING",
  "agent_attempt": 1,
  "started_at": "...",
  "updated_at": "...",
  "last_checkpoint": "..."
}
```

Exact ADK field names may differ by the selected library version. The application schema should avoid leaking ADK-specific classes into domain entities.

---

## 7. Resumability

Where the selected ADK version/runtime provides resumable workflows, Ngabo should use them for the investigation portion of the incident.

### Goal

If execution is interrupted after expensive/read-only tool calls, Ngabo should be able to continue the same investigation rather than blindly repeat the entire workflow.

### Layer responsibilities

```text
Firestore
  durable incident/business state

ADK resume/checkpoint mechanism
  execution continuity inside the agent workflow

Pub/Sub
  asynchronous external triggers / retries
```

### Recovery behavior

On resume:

1. load the canonical incident state;
2. validate that the incident is still in a resumable state;
3. recover/reuse ADK execution state when available;
4. ensure any tool that may run again is safe to repeat;
5. continue toward clarification/package generation;
6. append an audit event describing resume/retry.

---

## 8. The Idempotency Trap

Resumability and Pub/Sub redelivery mean a tool or handler can run more than once.

Therefore:

- read-only tools should be naturally repeatable;
- state-changing tools must carry an idempotency key;
- the agent must not directly execute non-idempotent external effects;
- final notification remains behind application review + idempotent notification workflow.

For a notification:

```text
idempotency_key = incident_id + action_type + package_version
```

For processed events:

```text
processed_events/{event_id}
```

Duplicate execution must converge on the same state.

---

## 9. Targeted Human Input

Clarification is the primary ADK human-input use case.

The agent can request clarification only when:

- the information is materially relevant to investigation;
- it cannot be recovered from canonical data/tools;
- the question can be stated clearly;
- the missing value should not be guessed.

Clarification output contract:

```json
{
  "incident_id": "...",
  "question_id": "...",
  "field": "specimen_type",
  "isolate_ids": ["UGA-039"],
  "question": "Please confirm the specimen source for isolate UGA-039.",
  "allowed_values": ["blood", "urine", "csf", "other"],
  "reason": "Required to complete the incident assessment."
}
```

The application persists the question and transitions to `WAITING_FOR_CLARIFICATION`.

After the answer is recorded, the same incident resumes.

---

## 10. Final Human Approval Is Not an Agent Confirmation Primitive

The consequential approval boundary remains authoritative application/domain behavior.

ADK may help prepare the package and proposed action, but the final state transition is controlled by the application workflow:

```text
WAITING_FOR_REVIEW
       ↓
APPROVED / REJECTED / NEEDS_MORE_INFO
```

Do not couple Ngabo's safety model exclusively to an experimental framework confirmation feature.

---

## 11. Structured Output

The final package must be returned through a schema-constrained boundary and validated after generation.

Required shape:

```json
{
  "title": "...",
  "priority": "HIGH",
  "observed_evidence": [],
  "derived_findings": [],
  "hypotheses": [],
  "uncertainties": [],
  "missing_information": [],
  "guidance": [],
  "investigation_checklist": [],
  "draft_escalation": "...",
  "limitations": []
}
```

Post-generation validators must check at least:

- every isolate ID exists;
- every guidance source ID was returned by the approved evidence tool;
- prohibited treatment/confirmation language is absent or correctly bounded;
- observed evidence is backed by source data;
- derived findings correspond to deterministic tool outputs;
- hypotheses remain labelled as hypotheses.

Invalid output does not advance the incident to review.

---

## 12. Model Selection

Primary orchestrator model:

`gemini-3.6-flash`

Use Flash first for the full workflow. Introduce a more expensive model only if evaluation shows a material improvement for a narrowly scoped step.

Do not add model routing purely for architecture spectacle.

---

## 13. Evidence Retrieval with EmbeddingGemma

After the core workflow is stable, `search_approved_guidance()` should support semantic retrieval using **EmbeddingGemma**.

Clean Architecture placement:

```text
application EvidenceSearchPort
        ↑
infrastructure EmbeddingGemmaEvidenceAdapter
```

Suggested flow:

1. load a curated/versioned guidance corpus;
2. precompute document/chunk embeddings;
3. embed query text with EmbeddingGemma;
4. perform deterministic cosine similarity;
5. return top approved source IDs/chunks/scores;
6. Gemini may summarize only returned approved evidence.

No arbitrary web results enter the approved evidence path in v0.1.

---

## 14. Optional MedGemma Tool

MedGemma is an optional bounded tool only after core behavior is stable.

Potential interface:

```text
interpret_medical_guidance(
    approved_source_ids,
    approved_chunks,
    incident_context
) -> structured interpretation
```

The tool output is supportive interpretation, not authority.

It must retain source IDs and may not introduce uncited claims.

If MedGemma does not improve measured evaluation results or adds too much deployment complexity, omit it from v0.1 and do not claim the bonus.

---

## 15. Evaluation Requirements

ADK behavior must be evaluated as a trajectory, not only by final prose quality.

The suite should evaluate where supported:

- correct tool choice;
- required tool execution;
- avoiding forbidden tools/actions;
- clarification behavior;
- stop behavior;
- final package validity;
- source integrity;
- failure handling.

### Required datasets

Store committed synthetic eval cases under a stable location such as:

```text
services/core/tests/eval/datasets/
```

Include:

- happy path;
- clarification path;
- weak/noisy evidence;
- empty evidence;
- tool failure;
- prompt injection;
- overclaiming;
- duplicate/redelivery behavior.

### Development loop

```text
baseline eval
    ↓
implementation change
    ↓
candidate eval
    ↓
compare results
    ↓
accept only if behavior is not regressed
```

Use current official ADK/Agents CLI evaluation tooling where it fits the repository without breaking Clean Architecture.

---

## 16. Observability

The agent runtime must emit enough telemetry to reconstruct what happened without exposing hidden chain-of-thought.

Track:

- invocation start/end;
- model name;
- tool start/end;
- tool result category;
- errors/retries;
- pause/resume;
- clarification;
- package validation;
- token/latency metrics where available.

### Cloud Trace / OpenTelemetry

Prefer the current ADK/Agents CLI tracing path if it integrates cleanly with `ngabo-core`.

Do not enable full prompt/response capture by default merely because the tooling supports it. Preserve a privacy-safe metadata-first configuration.

---

## 17. Loop and Cost Controls

Each investigation requires bounded execution.

Define configuration for:

```text
max_agent_steps
max_tool_calls
agent_timeout_seconds
tool_timeout_seconds
max_retries
```

A model loop must terminate into an inspectable failure state rather than burn credits indefinitely.

---

## 18. Failure States

At minimum distinguish:

```text
AGENT_TIMEOUT
AGENT_MODEL_ERROR
AGENT_TOOL_ERROR
AGENT_INVALID_OUTPUT
AGENT_EVIDENCE_UNAVAILABLE
AGENT_RESUME_FAILED
```

The application decides whether each is retryable.

Do not produce a final package after a critical unhandled agent failure.

---

## 19. Demo-Proof Events

Expose public-safe timeline events such as:

```text
AGENT_INVESTIGATION_STARTED
AGENT_TOOL_STARTED
AGENT_TOOL_COMPLETED
EVIDENCE_RETRIEVED
CLARIFICATION_REQUESTED
CLARIFICATION_RECEIVED
AGENT_INVESTIGATION_RESUMED
INCIDENT_PACKAGE_VALIDATED
```

These events are not model chain-of-thought. They are observable workflow facts.

---

## 20. Definition of Done

The ADK runtime is v0.1-ready when:

- [ ] a Pub/Sub signal automatically starts the agent;
- [ ] agent tools are typed and bounded;
- [ ] deterministic calculations remain outside the LLM;
- [ ] execution identifiers are persisted;
- [ ] interruption/retry behavior is safe;
- [ ] clarification pauses and resumes the same incident;
- [ ] output is schema validated;
- [ ] source IDs are validated;
- [ ] agent loops/timeouts are bounded;
- [ ] ADK eval scenarios pass at the agreed threshold;
- [ ] trace/log metadata makes execution inspectable;
- [ ] no consequential external action bypasses the human review gate.

---

## 21. References

- Hackathon Resources: https://allthingsagentichackathon.devpost.com/resources
- Google ADK docs: https://google.github.io/adk-docs/
- Google Agents CLI: https://google.github.io/agents-cli/

Always implement against the exact installed ADK version rather than assuming an API from this design document.
