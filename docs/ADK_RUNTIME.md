# Ngabo — Google ADK Runtime, Resumability & Evaluation Contract

**Status:** Required v0.1 agent-runtime contract  
**Applies to:** `services/core/ngabo/infrastructure/ai/adk` and the application workflows it drives

---

## 1. Objective

Ngabo must use Google ADK as a real agent runtime rather than a thin wrapper around a single Gemini call.

The v0.1 runtime uses a **graph-first hybrid workflow**: deterministic function/workflow nodes execute known reproducible steps, Gemini agent nodes handle genuinely ambiguous reasoning, independent deterministic work fans out and joins where safe, and fixed routing rules stay deterministic.

The governing rule is:

> **Deterministic when the workflow is known; agentic when the decision is ambiguous; dynamic only when the workflow itself cannot reasonably be known in advance.**

ADK remains an **outer infrastructure concern** under Clean Architecture. Ngabo's scientific/domain rules and authoritative workflow state do not depend on ADK classes.

Read `docs/ORCHESTRATION_PATTERNS.md` and ADR 0005 before implementing the runtime.

---

## 2. Clean Architecture Boundary

```text
Google ADK / Gemini
        ↓
infrastructure orchestration adapter
        ↓
application workflow / ports
        ↓
domain entities + deterministic services
```

Allowed:

```text
ADK function node -> application query/use case
ADK agent tool -> application query/use case/port
ADK orchestrator -> application ports
application -> domain
```

Forbidden:

```text
domain -> google.adk
application use case -> Gemini SDK directly
ADK function/tool node -> Firestore directly
ADK function/tool node -> Pub/Sub directly
ADK function/tool node -> notification provider directly
ADK node -> duplicated ad hoc domain/scientific calculation
```

All infrastructure access flows through application-defined ports.

---

## 3. v0.1 Orchestration Shape

The core investigation should be implemented as an explicit graph rather than asking a single agent prompt to remember and sequence the entire workflow.

Target topology:

```text
surveillance.signal.detected
          ↓
create/load incident
          ↓
FUNCTION: get_incident_context
          ↓
      FAN OUT
   ┌──────┼──────────┐
   │      │          │
   ▼      ▼          ▼
FUNCTION FUNCTION   FUNCTION
profile  baseline   missing-field
compare  summary    assessment
   │      │          │
   └──────┼──────────┘
          ▼
         JOIN
          ↓
AGENT: investigation triage
          │
          ├── clarification required? -> pause/resume
          │
          └── bounded evidence-search intent
                         ↓
                 EvidenceSearchPort
                         ↓
                 optional MedGemma*
                         ↓
AGENT: evidence-grounded synthesis
          ↓
FUNCTION: package validation
          ↓
WAITING_FOR_REVIEW
```

`*` MedGemma remains a gated stretch.

The graph may evolve during implementation if exact ADK APIs require a different mechanical representation, but the functional boundaries and dependency rules above must remain unless an ADR changes them.

---

## 4. Node Selection Rule

### Function/workflow node

Use when the same valid inputs should follow the same reproducible logic.

Examples:

- incident-context loading through application ports;
- profile comparison;
- baseline calculation;
- missing-field extraction;
- schema/package validation;
- fixed event/state routing;
- idempotency checks.

### Agent node

Use when Gemini reasoning materially adds value.

Examples:

- reasoning across multiple structured findings;
- deciding whether a missing field is materially blocking;
- choosing a bounded optional evidence topic/capability;
- generating labelled hypotheses;
- deciding that evidence is insufficient;
- source-grounded package synthesis.

### Dynamic workflow

Do not use runtime-generated workflow topology for the core v0.1 investigation. Reserve it for a later requirement where the execution tree itself cannot reasonably be known before runtime.

---

## 5. Routing Rule

A routing decision must not invoke Gemini merely because an agent router is available.

### Deterministic router

Required when rules are explicit/exhaustive, for example:

```text
event type -> handler
incident state -> legal transition
duplicate event -> idempotency path
validation pass/fail -> next state
review approved -> notification workflow
review rejected -> stop/close path
```

### Agentic router

Allowed for bounded ambiguous choices such as:

- which optional evidence topic is relevant;
- whether a missing value materially blocks synthesis;
- whether an optional specialist capability adds value;
- whether evidence is sufficient for a bounded hypothesis.

Agentic routing remains allow-listed, typed, step-bounded, and evaluated.

---

## 6. Parallel Fan-Out / Join

Once canonical incident context is loaded, independent read-only deterministic work should normally fan out concurrently when the exact ADK implementation supports this cleanly.

Core candidates:

```text
compare_resistance_profiles()
get_baseline_summary()
get_missing_fields()
```

The join must wait for required branches and produce one typed investigation-context object for the reasoning node.

Evidence retrieval may run in the same fan-out only when the retrieval query can be formed deterministically from canonical context. If query intent requires contextual reasoning, perform it after the triage agent node.

Parallelism must not hide dependencies or shared-state races. Reliability outranks speed.

---

## 7. Orchestrator Scope

The Ngabo reasoning/orchestrator agent may:

- inspect structured results produced by graph/function nodes;
- choose bounded optional investigation capabilities;
- compare existing deterministic outputs;
- formulate approved evidence-search intent;
- identify materially missing information;
- request targeted clarification;
- resume after clarification;
- construct labelled hypotheses;
- prepare a schema-constrained incident package;
- stop when evidence is insufficient.

The agent may not:

- create the surveillance signal;
- decide whether mandatory deterministic graph nodes should be skipped merely to save work;
- calculate AST statistics itself;
- alter canonical isolate facts;
- prescribe antimicrobial treatment;
- confirm an outbreak;
- send external notifications directly;
- bypass review;
- fabricate evidence.

---

## 8. Required Application-Facing Capabilities

Core v0.1 capability contracts remain small and typed:

```text
get_incident_context()
compare_resistance_profiles()
get_baseline_summary()
get_missing_fields()
search_approved_guidance()
request_clarification()
prepare_incident_package()
```

Important distinction:

- a capability may be represented as a deterministic graph/function node when it is a known workflow step;
- it may also be exposed as a bounded agent tool when agent-driven optional invocation is justified;
- do not duplicate its business/scientific implementation in both places.

Every capability defines:

- typed input schema;
- typed output schema;
- read-only vs side-effecting behavior;
- authorization expectations;
- timeout;
- retry behavior;
- idempotency behavior where applicable;
- error categories.

---

## 9. Deterministic Calculation Rule

The model must not decide the authoritative result of a deterministic calculation.

Correct:

```text
FUNCTION NODE / bounded tool:
compare_resistance_profiles()
        ↓
deterministic Python implementation
        ↓
validated similarity result
        ↓
Gemini interprets result with other findings
```

Incorrect:

```text
Gemini reads AST text and estimates similarity itself.
```

Do not use an LLM call to apply a fixed if/else rule, join structured results, identify syntactically missing fields, or repeat calculations that domain/application code already owns.

---

## 10. Agent Execution Identity

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

Exact ADK field names may differ by the selected library version. The application schema must avoid leaking ADK-specific classes into domain entities.

Where practical also correlate graph/node execution with:

```text
graph_run_id
node_name
branch_id
join_id
```

without making those runtime identifiers domain concepts.

---

## 11. Resumability

Where the selected ADK version/runtime provides resumable workflows, Ngabo should use them for the investigation portion of the incident.

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

1. load canonical incident state;
2. validate that the incident is still in a resumable state;
3. recover/reuse ADK execution state when available;
4. ensure any graph branch/tool that may run again is safe to repeat;
5. continue toward clarification/package generation;
6. append an audit event describing resume/retry.

A resumed graph must not bypass a deterministic node whose previous completion/result cannot be verified.

---

## 12. The Idempotency Trap

Resumability, parallel branch retry, and Pub/Sub redelivery mean a node/tool/handler can run more than once.

Therefore:

- read-only nodes/tools should be naturally repeatable;
- state-changing operations carry an idempotency key;
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

## 13. Targeted Human Input

Clarification is the primary ADK human-input use case.

The triage/reasoning agent can request clarification only when:

- the information is materially relevant to investigation;
- it cannot be recovered from canonical data/function nodes/tools;
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

After the answer is recorded, the same incident resumes through the graph from a safe checkpoint/application state.

---

## 14. Final Human Approval Is Not an Agent Confirmation Primitive

The consequential approval boundary remains authoritative application/domain behavior.

ADK may help prepare the package and proposed action, but the final state transition is controlled by the application workflow:

```text
WAITING_FOR_REVIEW
       ↓
APPROVED / REJECTED / NEEDS_MORE_INFO
```

Do not couple Ngabo's safety model exclusively to an experimental framework confirmation feature.

---

## 15. Structured Output and Deterministic Validation

The final package must be returned through a schema-constrained boundary and then validated in a deterministic function/application step.

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

Post-generation validators check at least:

- every isolate ID exists;
- every guidance source ID was returned by the approved evidence path;
- prohibited treatment/confirmation language is absent or correctly bounded;
- observed evidence is backed by source data;
- derived findings correspond to deterministic outputs;
- hypotheses remain labelled as hypotheses.

Invalid output does not advance the incident to review.

---

## 16. Model Selection and Model-Call Budget

Primary reasoning/orchestration model:

`gemini-3.6-flash`

Use Flash first for the workflow. Introduce a more expensive model only if evaluation shows a material improvement for a narrowly scoped step.

A model call must have a reason. Do not spend a Gemini turn on behavior that a deterministic graph node can execute reliably.

For the canonical demo scenario, record:

- model-call count;
- function/tool call count;
- retries;
- clarification count;
- total agent duration.

Treat these as engineering regression metrics, not clinical metrics.

---

## 17. Evidence Retrieval with EmbeddingGemma

After the core graph is stable, `search_approved_guidance()` should support semantic retrieval using **EmbeddingGemma**.

Clean Architecture placement:

```text
application EvidenceSearchPort
        ↑
infrastructure EmbeddingGemmaEvidenceAdapter
```

Suggested flow:

1. load a curated/versioned guidance corpus;
2. precompute document/chunk embeddings;
3. embed bounded query text with EmbeddingGemma;
4. perform deterministic cosine similarity;
5. return top approved source IDs/chunks/scores;
6. Gemini may summarize only returned approved evidence.

No arbitrary web results enter the approved evidence path in v0.1.

---

## 18. Optional MedGemma Capability

MedGemma is an optional bounded capability only after core behavior and EmbeddingGemma are stable.

Potential interface:

```text
interpret_medical_guidance(
    approved_source_ids,
    approved_chunks,
    incident_context
) -> structured interpretation
```

Prefer treating it as a bounded/stateless specialist capability rather than creating an autonomous subordinate agent unless evaluation proves an agent topology is beneficial.

Its output is supportive interpretation, not authority. It must retain source IDs and may not introduce uncited claims.

If MedGemma does not improve measured evaluation results or adds too much deployment complexity, omit it from v0.1 and do not claim the bonus.

---

## 19. Collaborative-Agent Pattern

Ngabo does not need multiple reasoning agents merely because ADK supports them.

A collaborative pattern is allowed later when:

- distinct specialist reasoning domains exist;
- the coordinator benefits from invoking only a relevant subset;
- evaluation shows the separation improves quality, traceability, or reliability.

Potential later specialists include epidemiology, genomics, evidence, and medical-evidence interpretation.

For v0.1, one primary Gemini reasoning/synthesis agent plus deterministic graph nodes and bounded specialist capabilities is preferred.

---

## 20. Dynamic Pattern

Runtime-generated dynamic workflow topology is deferred for the core v0.1 flow.

It may become useful for future open-ended research or genomics investigations where the available evidence determines the execution tree at runtime.

Do not introduce dynamic topology to the canonical hackathon path without a concrete requirement and an ADR/amendment.

---

## 21. Evaluation Requirements

ADK behavior must be evaluated as a trajectory, not only by final prose quality.

The suite should evaluate where supported:

- required graph/function-node execution;
- safe parallel fan-out/join;
- deterministic router behavior;
- correct bounded agentic routing;
- avoiding forbidden tools/actions;
- clarification behavior;
- stop behavior;
- final package validity;
- source integrity;
- failure handling;
- unnecessary model-call regression.

Store committed synthetic eval cases under a stable location such as:

```text
services/core/tests/eval/datasets/
```

Include:

- happy path;
- clarification path;
- weak/noisy evidence;
- empty evidence;
- required parallel branch failure;
- branch completion in different orders;
- tool failure;
- prompt injection;
- overclaiming;
- duplicate/redelivery behavior;
- interruption/resume.

### Development loop

```text
baseline eval
    ↓
implementation change
    ↓
candidate eval
    ↓
compare outcome + trajectory + model-call budget
    ↓
accept only if behavior is not regressed
```

Use current official ADK/Agents CLI evaluation tooling where it fits the repository without breaking Clean Architecture.

---

## 22. Observability

The runtime must emit enough telemetry to reconstruct what happened without exposing hidden chain-of-thought.

Track:

- graph/invocation start/end;
- node/branch start/end;
- fan-out/join completion;
- deterministic vs agent node type;
- model name for model nodes;
- tool result category;
- errors/retries;
- pause/resume;
- clarification;
- package validation;
- token/latency metrics where available.

Public-safe events may include:

```text
INVESTIGATION_GRAPH_STARTED
FUNCTION_NODE_STARTED
FUNCTION_NODE_COMPLETED
PARALLEL_FANOUT_STARTED
PARALLEL_BRANCH_COMPLETED
PARALLEL_JOIN_COMPLETED
AGENT_NODE_STARTED
EVIDENCE_RETRIEVED
CLARIFICATION_REQUESTED
CLARIFICATION_RECEIVED
AGENT_INVESTIGATION_RESUMED
PACKAGE_VALIDATION_COMPLETED
```

Prefer the current ADK/Agents CLI tracing path if it integrates cleanly with `ngabo-core`.

Do not enable full prompt/response capture by default merely because tooling supports it. Preserve a privacy-safe metadata-first configuration.

---

## 23. Loop and Cost Controls

Each investigation requires bounded execution.

Define configuration for:

```text
max_agent_steps
max_model_calls
max_tool_calls
agent_timeout_seconds
tool_timeout_seconds
max_retries
```

A model loop must terminate into an inspectable failure state rather than burn credits indefinitely.

---

## 24. Failure States

At minimum distinguish:

```text
AGENT_TIMEOUT
AGENT_MODEL_ERROR
AGENT_TOOL_ERROR
AGENT_INVALID_OUTPUT
AGENT_EVIDENCE_UNAVAILABLE
AGENT_RESUME_FAILED
GRAPH_REQUIRED_BRANCH_FAILED
GRAPH_JOIN_FAILED
GRAPH_ROUTING_ERROR
```

The application decides whether each is retryable.

A required deterministic branch failure must not be papered over by later Gemini synthesis.

Do not produce a final package after a critical unhandled failure.

---

## 25. Definition of Done

The ADK runtime is v0.1-ready when:

- [ ] a Pub/Sub signal automatically starts the investigation graph;
- [ ] canonical incident context loads through application contracts;
- [ ] profile comparison, baseline summary, and missing-field assessment are deterministic nodes;
- [ ] independent deterministic nodes fan out and join safely;
- [ ] fixed routing decisions do not invoke Gemini;
- [ ] Gemini is reserved for genuinely ambiguous reasoning/synthesis;
- [ ] agent tools/capabilities remain typed and bounded;
- [ ] deterministic calculations remain outside the LLM;
- [ ] execution identifiers are persisted;
- [ ] interruption/retry behavior is safe;
- [ ] clarification pauses and resumes the same incident;
- [ ] output is schema validated by deterministic code;
- [ ] source IDs are validated;
- [ ] model loops/timeouts are bounded;
- [ ] ADK eval scenarios pass at the agreed threshold;
- [ ] trace/log metadata makes fan-out, join, agent reasoning stages, and resume inspectable;
- [ ] the canonical scenario has a recorded model/tool-call trajectory;
- [ ] no consequential external action bypasses the human review gate;
- [ ] no unnecessary multi-agent or dynamic topology is introduced.

---

## 26. References

- `docs/ORCHESTRATION_PATTERNS.md`
- `docs/adr/0005-adk-graph-first-orchestration.md`
- Hackathon Resources: https://allthingsagentichackathon.devpost.com/resources
- Google ADK docs: https://google.github.io/adk-docs/
- Google Agents CLI: https://google.github.io/agents-cli/

Always implement against the exact installed ADK version rather than assuming an API or workshop terminology from this design document.
