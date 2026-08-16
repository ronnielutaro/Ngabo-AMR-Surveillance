# Ngabo — ADK Orchestration Patterns

**Status:** Required v0.1 orchestration contract  
**Date:** 2026-08-16  
**Framework:** Google ADK  
**Applies to:** investigation orchestration inside `ngabo-core`

---

## 1. Decision

Ngabo uses a **graph-first hybrid orchestration model** for v0.1.

The governing rule is:

> **Deterministic when the workflow is known; agentic when the decision is ambiguous; dynamic only when the workflow itself cannot reasonably be known in advance.**

This rule exists to improve reliability, cost, latency, testability, and architectural clarity while still giving Gemini meaningful autonomy where reasoning is genuinely required.

The project must not turn every operation into an agent merely because Google ADK supports multi-agent systems.

---

## 2. Why This Fits Ngabo

Ngabo's core investigation has a largely known shape:

```text
surveillance signal
    ↓
load canonical context
    ↓
perform reproducible investigation calculations
    ↓
reason over findings
    ↓
retrieve appropriate approved evidence
    ↓
clarify if material information is missing
    ↓
synthesize incident package
    ↓
human review
```

Many of these steps are reproducible and should not consume model reasoning.

The official All Things Agentic workshop on ADK orchestration demonstrates the same architectural distinction: deterministic work belongs in function/workflow nodes, model reasoning belongs in agent nodes, independent deterministic work can fan out in parallel and join, and routing may be deterministic or agentic depending on whether the decision can be exhaustively expressed as rules.

---

## 3. Node Taxonomy

### 3.1 Function node

Use for deterministic work that should produce the same result for the same inputs.

Ngabo examples:

- load canonical incident context through application ports;
- resistance-profile comparison;
- baseline calculation;
- missing-field extraction;
- validation;
- state-policy checks;
- idempotency checks;
- deterministic event routing;
- package post-generation validation.

A function node must not call Gemini merely to perform logic that ordinary code can implement.

### 3.2 Agent node

Use where model reasoning materially adds value.

Ngabo examples:

- deciding whether a data gap materially blocks a defensible assessment;
- forming a bounded investigation hypothesis;
- deciding which optional evidence topic or specialist capability is relevant;
- interpreting multiple structured findings together;
- producing the source-grounded incident package;
- deciding when evidence is insufficient and the workflow should stop.

### 3.3 Join node

Use after independent parallel work to create one explicit synchronization point before reasoning proceeds.

### 3.4 Router node

Routing may be deterministic or agentic.

Use a **deterministic router** when rules are known and exhaustive.

Use an **agentic router** only when the input space is ambiguous enough that fixed rules would become brittle or incomplete.

---

## 4. v0.1 Selected Topology

The target investigation topology is:

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
          ├── material clarification required?
          │       ↓ yes
          │   request clarification
          │       ↓
          │   pause / resume
          │
          └── evidence needed
                  ↓
          EvidenceSearchPort
          ├── curated/tag retrieval initially
          └── EmbeddingGemma after core green
                  ↓
          optional MedGemma interpretation*
                  ↓
AGENT: evidence-grounded synthesis
          ↓
FUNCTION: package validation
          ↓
WAITING_FOR_REVIEW
          ↓
human approval
          ↓
real authorized action
```

`*` MedGemma remains a gated stretch and is not required for the core graph.

### Why context runs before fan-out

The parallel branches require a canonical incident/signal/isolate context. Load that once through the application boundary, then pass immutable typed inputs to independent branches.

### Evidence retrieval timing

Evidence retrieval may join the first fan-out **only when the retrieval query can be composed deterministically from canonical incident fields**.

If the evidence topic requires contextual reasoning, the triage agent should first decide the bounded search intent, then call `EvidenceSearchPort`.

Do not force evidence retrieval into parallel execution when doing so weakens relevance or traceability.

---

## 5. Deterministic Routing Rules

The following must not require Gemini:

```text
event type -> event handler
incident state -> permitted transition
duplicate event -> idempotency path
invalid schema -> validation failure
review approved -> notification workflow
review rejected -> stop/close path
notification failed -> retry policy
critical package validation failure -> do not advance to review
```

If a routing decision can be exhaustively expressed in ordinary code, implement it as ordinary code/function-node policy.

Do not put fixed routing rules into prompts merely to make the workflow appear more agentic.

---

## 6. Agentic Routing Rules

Agentic routing is appropriate for questions such as:

- Which optional investigation capability is relevant to this signal?
- Is the missing information materially important enough to pause for clarification?
- Which approved evidence topic should be searched?
- Would a specialized interpretation tool add value to the current evidence?
- Is there enough evidence to synthesize a bounded hypothesis, or should Ngabo stop with uncertainty?

Agentic routing must still be bounded by:

- an allow-list of capabilities;
- typed inputs/outputs;
- maximum step/tool budgets;
- evaluation;
- no direct consequential side effects.

---

## 7. Parallel Fan-Out / Join

Independent, read-only deterministic steps should normally run concurrently once their required inputs are available.

Core candidate fan-out:

```text
compare_resistance_profiles
get_baseline_summary
get_missing_fields
```

Expected benefits:

- lower investigation latency;
- fewer unnecessary model turns;
- lower token use;
- easier deterministic testing;
- clearer traces;
- a visually legible hackathon demo.

### Guardrail

Parallelism is not a goal by itself.

Do not parallelize operations that:

- have real data dependencies;
- create ordering ambiguity;
- mutate shared state unsafely;
- make failure semantics harder to understand;
- materially increase complexity without measurable benefit.

---

## 8. Collaborative Pattern — Selective Use

Ngabo does **not** require a fleet of specialist agents for v0.1.

The collaborative pattern becomes appropriate only when evaluation demonstrates that distinct specialist reasoning domains improve the result.

Possible future specialists:

```text
Ngabo Orchestrator
   ├── epidemiology specialist
   ├── evidence specialist
   ├── genomics specialist
   └── medical-evidence interpretation specialist
```

A coordinator may select only the subset relevant to an incident rather than invoking all specialists.

For v0.1, prefer:

- deterministic function nodes;
- one primary Gemini orchestrator/synthesis agent;
- bounded model-tools such as optional MedGemma;
- additional sub-agents only when they improve evaluation, traceability, or capability separation.

Do not create a sub-agent when a deterministic function or stateless bounded tool is sufficient.

---

## 9. Dynamic Pattern — Deferred for Core v0.1

A dynamic workflow is appropriate when the execution structure itself cannot be reasonably known in advance, for example:

- open-ended deep research;
- adaptive multi-source outbreak investigation with unknown branches;
- later genomics investigations where available evidence determines a runtime research tree.

Ngabo's v0.1 core workflow is sufficiently known to use an explicit graph.

Therefore:

> **Do not use runtime-generated dynamic workflow topology for the core hackathon flow unless a concrete requirement proves the graph insufficient.**

Introducing a dynamic topology to the core path requires an ADR or an amendment to this architecture decision.

---

## 10. Model-Call Budget Principle

A model call must have a reason.

Do not use Gemini to:

- fetch data that an adapter can fetch;
- apply fixed if/else routing;
- calculate similarity;
- calculate baselines;
- detect missing fields;
- validate schema;
- join already structured results.

Use Gemini to:

- reason across results;
- resolve ambiguity;
- decide bounded optional next steps;
- formulate a targeted clarification;
- synthesize an evidence-grounded package.

Evaluation should track model/tool call counts for the canonical demo scenario so architectural changes do not silently create unnecessary LLM turns.

---

## 11. Clean Architecture Placement

ADK graph primitives remain infrastructure/runtime implementation details.

```text
ADK graph / function nodes / agent nodes
                 ↓
infrastructure orchestration adapter
                 ↓
application use cases / queries / ports
                 ↓
domain policy and deterministic services
```

Function nodes do **not** get permission to bypass Clean Architecture.

Forbidden:

```text
ADK function node -> raw Firestore business query
ADK function node -> duplicated domain calculation
ADK router -> direct notification provider
ADK agent -> direct state transition mutation
```

The graph coordinates inward-facing application contracts; it does not replace them.

---

## 12. Failure Semantics

Each parallel branch reports a typed success/failure result.

The join must define behavior for:

- all required branches successful;
- optional branch unavailable;
- required branch failed;
- branch timeout;
- retryable failure;
- stale incident/version conflict.

A required deterministic failure must not be hidden by later Gemini synthesis.

If required findings are unavailable, the agent receives an explicit failure/unknown state or the workflow stops visibly.

---

## 13. Observability / Demo Events

The graph should emit public-safe execution facts such as:

```text
INVESTIGATION_GRAPH_STARTED
FUNCTION_NODE_STARTED
FUNCTION_NODE_COMPLETED
PARALLEL_FANOUT_STARTED
PARALLEL_BRANCH_COMPLETED
PARALLEL_JOIN_COMPLETED
AGENT_NODE_STARTED
EVIDENCE_SEARCH_COMPLETED
CLARIFICATION_REQUESTED
INVESTIGATION_RESUMED
PACKAGE_VALIDATION_COMPLETED
```

Include where relevant:

- incident ID;
- node name;
- execution/invocation ID;
- start/end timestamp;
- latency;
- success/failure category;
- model name only for agent/model nodes.

Do not expose hidden chain-of-thought.

The incident UI may translate these events into concise operational timeline entries so judges can see fan-out, join, reasoning, pause/resume, and action.

---

## 14. Testing Requirements

### Function nodes

- deterministic unit tests;
- same input -> same output;
- no model/network dependency unless the node is explicitly an adapter operation;
- typed failure cases.

### Fan-out/join

- branches may complete in different orders;
- join produces the same semantic result regardless of completion order;
- one required branch failure produces the expected bounded failure;
- no duplicate branch side effect on retry.

### Deterministic router

Table-driven tests must cover every branch and fallback.

### Agentic router

Use ADK evaluations to verify appropriate capability selection and no forbidden routing.

### Cost/trajectory

For the canonical seeded scenario, record:

- number of model calls;
- tool/function-node calls;
- retries;
- clarification count;
- total agent duration.

Use these metrics as regression signals, not as clinical performance metrics.

---

## 15. Implementation Sequence

1. Implement application/domain contracts independently of ADK.
2. Implement deterministic function-node adapters around existing application queries/services.
3. Implement the initial graph with canonical context -> fan-out -> join.
4. Add Gemini triage/synthesis agent nodes.
5. Add deterministic and agentic routing only where specified.
6. Add clarification pause/resume.
7. Add evidence retrieval.
8. Add package validation and human gate.
9. Add observability and graph-trajectory evaluation.
10. Add EmbeddingGemma only after the core graph is green.
11. Consider MedGemma only after EmbeddingGemma/core evaluations are stable.
12. Defer dynamic topology until a real requirement exists.

---

## 16. Acceptance Criteria

The v0.1 orchestration design is satisfied when:

- [ ] a surveillance event starts the graph without a user prompt;
- [ ] canonical incident context is loaded through application contracts;
- [ ] profile comparison, baseline summary, and missing-field assessment are deterministic nodes;
- [ ] independent deterministic nodes fan out and join safely;
- [ ] fixed routing decisions do not invoke Gemini;
- [ ] Gemini is used only for genuinely ambiguous investigation/interpretation/synthesis steps;
- [ ] clarification can pause and resume the same incident;
- [ ] required branch failures are visible and cannot be papered over by model output;
- [ ] package validation is deterministic;
- [ ] consequential action remains behind human approval;
- [ ] graph execution is observable without exposing chain-of-thought;
- [ ] the canonical demo has a documented model/tool-call trajectory;
- [ ] no unnecessary multi-agent or dynamic topology is introduced.

---

## 17. Pattern Selection Cheat Sheet

| Problem shape | Ngabo pattern |
|---|---|
| Same input should yield same operation/result | deterministic function node |
| Several independent reproducible calculations | parallel function nodes + join |
| Exhaustive fixed routing rule | deterministic router |
| Ambiguous bounded decision | agent node / agentic router |
| Need only a relevant subset of reasoning specialists | collaborative pattern |
| Workflow topology unknowable until runtime | dynamic pattern |
| Core v0.1 AMR investigation | graph-first hybrid workflow |

---

## 18. Reference Principle

When in doubt, start with the smallest reliable pattern and introduce more autonomy only where the simpler architecture demonstrably fails to meet the product requirement.

The goal is not maximum agent count. The goal is **maximum useful autonomy with minimum unnecessary nondeterminism**.
