# Ngabo — System Design

**Version:** 0.4  
**Date:** 2026-08-16  
**Status:** Hackathon MVP system design  
**Architecture:** Clean Architecture in a monorepo

## 1. Design Objective

Build the smallest architecture that convincingly demonstrates:

> **event-driven AMR surveillance → graph-orchestrated autonomous investigation → human-reviewed response → real observable action**

while preserving deterministic scientific logic, resumability, auditable state, strict Clean Architecture dependency boundaries, and strong hackathon proof of execution.

See:

- `docs/CLEAN_ARCHITECTURE.md`
- `docs/HACKATHON_ALIGNMENT.md`
- `docs/ADK_RUNTIME.md`
- `docs/ORCHESTRATION_PATTERNS.md`
- ADR 0005

## 2. Architectural Principles

Ngabo follows these system-wide rules:

1. **Clean Architecture:** dependencies point inward toward domain/application policy.
2. **Monorepo:** frontend, backend, data, infra, docs, tests, and release governance share one repository.
3. **Independent deployables:** monorepo does not collapse `ngabo-web` and `ngabo-core` into one runtime.
4. **Deterministic scientific core:** surveillance calculations remain ordinary reproducible code.
5. **Graph-first orchestration:** known/reproducible investigation steps use deterministic workflow/function nodes; Gemini is reserved for ambiguity, optional routing, clarification, hypotheses, and synthesis.
6. **Deterministic routing by default:** exhaustive fixed rules never require an LLM call.
7. **Parallelism where safe:** independent read-only deterministic investigation branches may fan out and join.
8. **No multi-agent theater:** specialist agents are introduced only when evaluation shows a real benefit.
9. **Dynamic topology is deferred:** runtime-generated workflow trees are not required for the core v0.1 path.
10. **Ports/adapters:** Firestore, Pub/Sub, GCS, ADK, Gemini, EmbeddingGemma, optional MedGemma, and notifications are outer implementations.
11. **Persisted workflow:** Firestore is canonical operational state.
12. **Resumable execution:** ADK execution continuity complements Firestore state where supported/stable.
13. **Bounded autonomy:** human approval gates consequential escalation.
14. **Proof of action:** the hosted demo performs at least one real authorized external action after approval.
15. **Observable autonomy:** logs/traces expose graph/node/tool facts without exposing private chain-of-thought.

## 3. System Context

```mermaid
flowchart LR
    U[Microbiologist / AMR Officer]
    W[Ngabo Web Console]
    C[Ngabo Core]
    G[Google ADK Graph + Gemini 3.6 Flash]
    EG[EmbeddingGemma - planned]
    MG[MedGemma - gated stretch]
    F[(Firestore)]
    S[(Cloud Storage)]
    P[Pub/Sub]
    N[Real Notification Adapter]
    D[Demo Notification Adapter]
    E[Approved Evidence Library]
    O[Cloud Logging / Trace]

    U --> W
    W --> C
    C --> S
    C --> F
    C --> P
    P --> C
    C --> G
    G --> C
    C --> E
    E --> EG
    EG --> C
    MG -. optional .-> C
    C --> N
    C --> D
    C --> O
```

EmbeddingGemma and MedGemma are outer adapters. EmbeddingGemma is planned only after the core deployed graph is green; MedGemma is optional and may be omitted.

## 4. Clean Architecture View

```mermaid
flowchart TB
    subgraph Outer[Frameworks / Infrastructure]
        FastAPI[FastAPI]
        Firestore[Firestore]
        PubSub[Pub/Sub]
        GCS[Cloud Storage]
        ADK[Google ADK / Gemini]
        Gemma[EmbeddingGemma / optional MedGemma]
        Notify[Notification Providers]
        Observe[Cloud Logging / Trace]
    end

    subgraph Interfaces[Interfaces / Adapters]
        HTTP[HTTP Controllers]
        EventHandlers[Event Handlers]
        InfraAdapters[Repository / Messaging / AI Adapters]
    end

    subgraph Application[Application Layer]
        UseCases[Use Cases]
        Workflows[Incident / Investigation Workflows]
        Ports[Ports / Contracts]
    end

    subgraph Domain[Domain Layer]
        Entities[Entities / Value Objects]
        Rules[AMR / Surveillance Rules]
        State[Incident State Policy]
    end

    FastAPI --> HTTP
    PubSub --> EventHandlers
    Firestore --> InfraAdapters
    GCS --> InfraAdapters
    ADK --> InfraAdapters
    Gemma --> InfraAdapters
    Notify --> InfraAdapters
    Observe --> InfraAdapters

    HTTP --> UseCases
    EventHandlers --> UseCases
    InfraAdapters --> Ports
    UseCases --> Entities
    Workflows --> Rules
    Ports --> Domain
```

The diagram expresses **source-code dependency direction**, not runtime data flow. ADK function nodes do not get permission to bypass application/domain boundaries.

## 5. Monorepo / Deployment View

```text
repository
├── apps/web                  Next.js source
├── services/core             Python/FastAPI/ADK source
├── data                      synthetic data, schemas, guidance
├── docs                      product, architecture, ADR, release docs
├── infra                     deployment/configuration
└── .github                   CI/repository automation

runtime
├── Cloud Run: ngabo-web
└── Cloud Run: ngabo-core
```

**One repository; two primary deployables.** Additional deployables require a justified architecture decision.

## 6. Cloud Deployment

```mermaid
flowchart TD
    Browser --> Web[Cloud Run: ngabo-web]
    Web --> Core[Cloud Run: ngabo-core]
    Core --> GCS[Cloud Storage]
    Core --> DB[(Firestore)]
    Core --> PS[Pub/Sub]
    PS --> Core
    Core --> Graph[Google ADK Investigation Graph]
    Graph --> Gemini[Gemini 3.6 Flash Agent Nodes]
    Core --> Embed[EmbeddingGemma if completed]
    Core -. gated .-> Med[MedGemma if completed]
    Core --> Logs[Cloud Logging / Trace]
    Core --> Notify[Authorized External Action]
```

### MVP deployment principle

Use one backend deployment with clean internal layers. Split services later only when real scale, fault isolation, or product boundaries justify the operational cost.

### Hackathon deployment controls

Required:

- Cloud Run minimum instances `0` unless a documented exception exists;
- explicit max-instance caps;
- right-sized CPU/RAM;
- Google Cloud budget and email alert;
- Secret Manager/injected secrets;
- protected internal event endpoints;
- judge-accessible hosted service through the required judging window;
- light artifact/log retention appropriate for a demo system.

## 7. Backend Package Boundaries

```text
services/core/ngabo/
├── domain/
│   ├── entities/
│   ├── value_objects/
│   ├── enums/
│   ├── events/
│   ├── exceptions/
│   └── services/surveillance/
├── application/
│   ├── use_cases/
│   ├── workflows/
│   ├── commands/
│   ├── queries/
│   ├── dto/
│   ├── ports/
│   └── agent_contracts/
├── interfaces/
│   ├── api/
│   └── events/
├── infrastructure/
│   ├── persistence/firestore/
│   ├── storage/gcs/
│   ├── messaging/pubsub/
│   ├── ai/gemini/
│   ├── ai/adk/
│   │   ├── graph/
│   │   ├── nodes/
│   │   └── tracing/
│   ├── ai/embedding_gemma/
│   ├── ai/medgemma/          # only if stretch accepted
│   ├── evidence/
│   ├── observability/
│   └── notifications/
└── bootstrap/
```

### Layer responsibilities

**Domain** — AMR/surveillance entities, value objects, rules, state policy, pure deterministic services.  
**Application** — use cases, workflows, commands/queries, ports, agent-facing contracts.  
**Interfaces** — HTTP and event translation into application commands.  
**Infrastructure** — Firestore/GCS/PubSub/Gemini/ADK/Gemma/notification/telemetry implementations.  
**Bootstrap** — composition root and dependency wiring.

ADK graph/function/agent nodes remain infrastructure orchestration adapters around inward-defined application contracts.

## 8. Core Domain / Application Records

### ImportBatch
- ID
- raw file URI reference
- SHA-256
- status
- received time
- row counts
- validation summary

### Isolate
Canonical normalized organism/specimen/ward/AST record.

### SurveillanceSignal
Deterministic output indicating a pattern deserves investigation.

### Incident
Long-lived response workflow.

### IncidentEvent
Append-only audit event.

### AgentRunReference
Application-level metadata correlating an incident to agent/graph execution without leaking ADK classes into the domain.

Suggested fields:

```text
incident_id
agent_session_id
agent_invocation_id
agent_run_id
agent_run_status
agent_attempt
started_at
updated_at
last_checkpoint
```

Runtime-only correlation may also include `graph_run_id`, `node_name`, `branch_id`, and `join_id`.

### EvidenceSource
Approved guidance/reference metadata.

### Clarification
Question + human answer/provenance.

### Notification
Outbound action + delivery/ack state.

These concepts remain meaningful without knowing which database, web framework, agent runtime, or LLM provider is used.

## 9. Import Sequence

```mermaid
sequenceDiagram
    actor User
    participant UI
    participant API as HTTP Interface
    participant App as Import Use Case
    participant Store as RawFileStore Port
    participant Repo as ImportRepository Port
    participant Bus as EventPublisher Port

    User->>UI: Upload CSV
    UI->>API: POST /imports
    API->>App: ImportLabData command
    App->>Store: Save immutable raw file
    App->>Repo: Create ImportBatch
    App->>Bus: lab.import.received
    App-->>API: import_id
    API-->>UI: import_id
```

At runtime, infrastructure adapters implement the ports with GCS, Firestore, and Pub/Sub.

## 10. Normalization + Detection Sequence

```mermaid
sequenceDiagram
    participant Bus as Pub/Sub Adapter
    participant Handler as Event Interface
    participant App as AnalyzeImport Use Case
    participant Domain as Deterministic Surveillance
    participant Repo as Repository Ports
    participant Events as EventPublisher Port

    Bus->>Handler: lab.import.received
    Handler->>App: AnalyzeImport command
    App->>Domain: Parse/validate/normalize
    App->>Repo: Persist normalized isolates + validation
    App->>Domain: Run surveillance detector

    alt suspicious pattern
        App->>Repo: Persist SurveillanceSignal
        App->>Events: surveillance.signal.detected
    else no signal
        App->>Repo: Mark import analyzed
    end
```

The event handler contains no AMR/scientific logic.

## 11. Graph-Orchestrated Investigation

```mermaid
flowchart TD
    S[Pub/Sub: surveillance.signal.detected] --> I[Application: Start Investigation]
    I --> C[Function Node: Incident Context]
    C --> F[Fan-Out]
    F --> P[Function Node: Profile Comparison]
    F --> B[Function Node: Baseline Summary]
    F --> M[Function Node: Missing Fields]
    P --> J[Join]
    B --> J
    M --> J
    J --> T[Gemini Agent Node: Triage]
    T --> Q{Material clarification?}
    Q -- yes --> H[Human Clarification]
    H --> T
    Q -- no --> E[EvidenceSearchPort]
    E --> X[Optional MedGemma]
    X --> Y[Gemini Agent Node: Synthesis]
    E --> Y
    Y --> V[Function Node: Package Validation]
    V --> R[WAITING_FOR_REVIEW]
```

### Graph rules

- context loads before branches that depend on it;
- profile comparison, baseline summary, and missing-field extraction are deterministic;
- independent read-only branches should run in parallel where reliable;
- a join produces typed findings before Gemini reasoning;
- fixed routing/state rules stay deterministic;
- Gemini decides only bounded ambiguous investigation choices;
- required branch failure stops or visibly degrades the workflow according to typed policy;
- a required deterministic failure cannot be hidden by model prose.

## 12. Investigation Sequence

```mermaid
sequenceDiagram
    participant Bus as Pub/Sub Adapter
    participant Handler as Event Interface
    participant App as Investigation Workflow
    participant Graph as ADK Graph Adapter
    participant Ctx as Context Function Node
    participant Calc as Parallel Deterministic Nodes
    participant Agent as Gemini Agent Node
    participant Evidence as EvidenceSearchPort
    participant Repo as Repository Ports
    participant UI

    Bus->>Handler: surveillance.signal.detected
    Handler->>App: StartInvestigation command
    App->>Repo: Create Incident + agent run reference
    App->>Graph: Start/resume graph
    Graph->>Ctx: get_incident_context
    Ctx-->>Graph: canonical typed context
    par independent deterministic branches
        Graph->>Calc: compare_resistance_profiles
        Graph->>Calc: get_baseline_summary
        Graph->>Calc: get_missing_fields
    end
    Calc-->>Graph: joined deterministic findings
    Graph->>Agent: triage joined findings

    alt clarification materially required
        Agent->>App: Request clarification
        App->>Repo: WAITING_FOR_CLARIFICATION
        UI->>App: Submit clarification
        App->>Graph: Resume same incident/graph where supported
    else continue
        Agent->>Evidence: bounded evidence-search intent
        Evidence-->>Agent: approved source IDs/chunks
    end

    Agent-->>Graph: structured incident package
    Graph->>App: package candidate
    App->>App: deterministic validation
    App->>Repo: WAITING_FOR_REVIEW
```

Google ADK/Gemini are concrete infrastructure implementations behind application contracts. Firestore remains business/workflow truth even when ADK checkpoint/resume is used.

## 13. Routing Strategy

### Deterministic routing

Use ordinary code/function-node policy for:

- event type -> handler;
- incident state -> legal transition;
- duplicate event -> idempotency path;
- validation outcome -> next state;
- approval -> notification workflow;
- rejection -> stop/close path;
- explicit retry policy.

### Agentic routing

Allow Gemini to select only bounded ambiguous next steps, such as:

- evidence topic;
- whether a missing field materially blocks synthesis;
- optional specialist capability;
- evidence sufficiency for a bounded hypothesis.

Do not spend model calls on fixed routing rules.

## 14. Interruption / Resume Sequence

```mermaid
sequenceDiagram
    participant App as Investigation Workflow
    participant Repo as Firestore Port
    participant ADK as ADK Graph Adapter

    App->>ADK: Start graph
    ADK--xADK: Invocation interrupted / retryable failure
    App->>Repo: Load incident + AgentRunReference
    App->>ADK: Resume graph if supported
    ADK->>ADK: Reuse verified completed nodes or safely repeat idempotent/read-only nodes
    ADK->>App: Continue / package / clarification
    App->>Repo: Append resume/retry audit event
```

All nodes/tools must be safe under possible repeated execution. Resumability is not permission to create non-idempotent agent side effects.

## 15. Evidence Retrieval Sequence

Initial core may use deterministic/tag retrieval. Planned post-core semantic retrieval:

```mermaid
sequenceDiagram
    participant Agent as Gemini Agent Node
    participant Port as EvidenceSearchPort
    participant Embed as EmbeddingGemma Adapter
    participant Corpus as Approved Guidance Corpus

    Agent->>Port: bounded approved-guidance query
    Port->>Embed: embed query
    Corpus->>Embed: precomputed approved embeddings
    Embed->>Embed: cosine similarity
    Embed-->>Port: approved source IDs + chunks + scores
    Port-->>Agent: traceable evidence only
```

Evidence retrieval may happen before the triage agent only when query intent can be composed deterministically from canonical incident context.

No arbitrary web result becomes approved evidence in v0.1.

## 16. Collaborative / Dynamic Pattern Boundary

### Collaborative agents

Not required for core v0.1. Add specialist agents only if evaluation demonstrates a real benefit. A future coordinator may invoke only the relevant subset of epidemiology/evidence/genomics/medical specialists.

### Dynamic workflow topology

Deferred from the core v0.1 path. It may be appropriate for future open-ended research or genomics investigations whose execution tree cannot be known in advance.

The core AMR incident workflow is known enough to remain an explicit graph.

## 17. Human Review + Real Action Sequence

```mermaid
sequenceDiagram
    actor Reviewer
    participant UI
    participant API as HTTP Interface
    participant App as Review Use Case
    participant Repo as Repository Port
    participant Events as EventPublisher Port
    participant Notify as Notification Port
    participant Target as Authorized External Target

    Reviewer->>UI: Review package
    UI->>API: Approve / Reject / More Info
    API->>App: ReviewIncident command

    alt approved
        App->>Repo: Record approval
        App->>Events: incident.notification.requested
        Events->>App: Notification workflow
        App->>Notify: Send with idempotency key
        Notify->>Target: Real external action
        Notify-->>App: Delivery result
        App->>Repo: Persist result
    else rejected
        App->>Repo: Record rejection
    end
```

The real adapter is required for the hosted/filmed v0.1 demonstration. The deterministic demo adapter remains for tests/local usage.

## 18. Incident State Machine

```mermaid
stateDiagram-v2
    [*] --> DETECTED
    DETECTED --> INVESTIGATING
    INVESTIGATING --> WAITING_FOR_CLARIFICATION
    WAITING_FOR_CLARIFICATION --> INVESTIGATING
    INVESTIGATING --> WAITING_FOR_REVIEW
    WAITING_FOR_REVIEW --> APPROVED
    WAITING_FOR_REVIEW --> REJECTED
    WAITING_FOR_REVIEW --> NEEDS_MORE_INFO
    NEEDS_MORE_INFO --> INVESTIGATING
    APPROVED --> NOTIFICATION_PENDING
    NOTIFICATION_PENDING --> NOTIFIED
    NOTIFICATION_PENDING --> NOTIFICATION_FAILED
    NOTIFICATION_FAILED --> NOTIFICATION_PENDING
    NOTIFIED --> ACKNOWLEDGED
    ACKNOWLEDGED --> CLOSED
    REJECTED --> CLOSED
```

Graph/agent failures and retries are execution/audit metadata unless product semantics require a new incident state.

## 19. Idempotency

Pub/Sub, resumed graph execution, and branch retry can cause repeated work.

Every event has a unique `event_id`.

Before a state-changing side effect:

1. application workflow applies the idempotency contract;
2. infrastructure persistence performs the required transactional operation where possible;
3. processed-event state is persisted;
4. side effect is not repeated on redelivery/retry.

Notifications use an idempotency key such as:

```text
incident_id + action_type + package_version
```

Read-only deterministic branches are naturally repeatable. Any state-changing capability must be explicitly idempotent. The agent itself must not directly own consequential external effects.

## 20. Concurrency

Incident has numeric `version`.

Updates require expected version and valid state transition. Conflicts return `409` at the HTTP boundary.

Parallel graph branches operate from immutable/typed investigation inputs and must not race to mutate incident business state.

This prevents reviewer approval racing against a changing/resumed investigation.

## 21. Data Integrity

### Immutable
- raw import file;
- canonical source facts;
- detector configuration used;
- incident event history;
- generated package versions.

### Explicitly mutable through use cases
- current incident state;
- human clarification;
- review decision;
- acknowledgement;
- retryable graph/agent execution metadata.

The agent cannot mutate immutable source facts.

## 22. API Surface

HTTP interfaces expose application use cases.

Imports:
- `POST /api/v1/imports`
- `GET /api/v1/imports/{id}`
- `GET /api/v1/imports/{id}/validation`

Incidents:
- `GET /api/v1/incidents`
- `GET /api/v1/incidents/{id}`
- `GET /api/v1/incidents/{id}/events`
- `POST /api/v1/incidents/{id}/clarifications`
- `POST /api/v1/incidents/{id}/review`

Demo:
- `POST /api/v1/demo/reset`
- `POST /api/v1/demo/run-seeded-scenario`

Private event interfaces:
- `/internal/events/imports`
- `/internal/events/surveillance`
- `/internal/events/incidents`

Routes/controllers remain thin transport adapters.

## 23. Frontend Architecture

```text
apps/web/src/
├── domain/
├── application/
├── infrastructure/
│   ├── api/
│   └── streaming/
├── presentation/
└── app/
```

The Next.js application follows the dependency philosophy pragmatically:

- React/presentation renders state;
- application owns meaningful client-side workflow behavior;
- API/SSE access lives in infrastructure;
- UI never calls GCP/model infrastructure directly;
- Next.js `app/` is route/composition wiring.

See `docs/UI_UX_SPEC.md` and `docs/UI_UX_HACKATHON_ADDENDUM.md`.

## 24. Live UI / Demo-Proof Timeline

Preferred: Server-Sent Events for incident state/graph events.

Fallback: short polling if SSE threatens implementation stability.

Public-safe timeline events include:

```text
DATA_NORMALIZED
SURVEILLANCE_SIGNAL_DETECTED
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
REVIEW_APPROVED
NOTIFICATION_SENT
NOTIFICATION_ACKNOWLEDGED
```

These events expose observable workflow facts, not hidden model chain-of-thought.

The incident screen should make the fan-out -> join -> reasoning -> clarification/resume -> package progression legible to a judge without requiring logs to understand the story.

## 25. Required Failure Behaviors

| Failure | Behavior |
|---|---|
| invalid CSV | visible validation failure |
| unknown organism | flag unknown; never invent mapping |
| missing ward/specimen | persist missingness |
| duplicate Pub/Sub event | no duplicate incident/action |
| required graph branch failure | visible bounded failure; no Gemini synthesis around missing required computation |
| graph join failure | visible failure/retry path |
| deterministic routing error | fail visibly; never silently substitute agent routing |
| Gemini timeout | bounded retry + visible error |
| ADK invocation interruption | safe resume/retry using persisted references where supported |
| optional capability failure | continue only if policy explicitly permits degraded operation |
| no guidance result | say evidence unavailable |
| malformed model package | reject with deterministic schema/claim validation |
| reviewer rejection | stop action and persist reason |
| notification failure | retryable state with idempotency |
| app restart | resume from persisted application state |
| trace/log unavailable | workflow still functions; observability degrades only |

Errors are translated at outer interfaces; inner layers use domain/application error types rather than framework-specific HTTP exceptions.

## 26. Observability

Every log/event carries where relevant:

- correlation ID;
- incident ID;
- event ID;
- agent session/invocation/run ID;
- graph run ID;
- node name and node type;
- branch/join ID;
- model name for agent/model nodes;
- package version.

Track:

- import/normalization/detector time;
- graph duration;
- branch/node latency/error;
- fan-out/join latency;
- model-call count and latency;
- tool/capability calls;
- retries/resumes;
- clarification count;
- package-generation/validation time;
- notification latency;
- token usage where available.

Use Cloud Logging plus ADK/Cloud Trace/OpenTelemetry where stable. Prefer metadata/no-content tracing.

Observability is infrastructure. Domain behavior must not depend on telemetry availability.

## 27. Testing & Evaluation Strategy

### Domain
Pure unit tests without cloud, HTTP, model, or network access.

### Application
Use-case/workflow tests using fakes/in-memory port implementations.

### Function nodes
Verify deterministic results and typed failures without model calls.

### Parallel fan-out/join
Verify:

- branch completion order does not change semantic result;
- required branch failure is bounded/visible;
- no unsafe duplicate side effect occurs on retry.

### Deterministic routers
Table-driven tests cover every branch and fallback.

### Agentic routing / ADK evaluation
Evaluate:

- appropriate optional capability selection;
- missing-data clarification;
- no-source behavior;
- prompt injection;
- fabricated citation/isolate rejection;
- overclaiming boundaries;
- no forbidden routing/action;
- model-call budget regression.

### End-to-end

```text
upload
  -> deterministic signal
  -> Pub/Sub
  -> graph start
  -> deterministic fan-out/join
  -> Gemini triage
  -> clarify/resume
  -> approved evidence
  -> Gemini synthesis
  -> deterministic package validation
  -> review
  -> real notify
  -> acknowledge
```

The final public `EVALUATION.md` records methodology/results/limitations and the canonical graph trajectory.

## 28. Architecture Enforcement

Before completing a change, verify:

- domain imports no FastAPI/GCP/ADK/Gemini/Gemma SDK;
- application does not instantiate Firestore/PubSub/GCS/model clients;
- routes/event handlers contain no scientific/business rules;
- ADK graph/function nodes call inward application contracts rather than becoming a parallel business layer;
- mandatory reproducible investigation steps are not delegated to Gemini;
- fixed routing rules do not invoke Gemini;
- parallel branches do not mutate shared state unsafely;
- required branch failure cannot be hidden by model output;
- deterministic surveillance tests run without external services;
- concrete adapters are wired at composition roots;
- Firestore remains workflow truth even with ADK resume support;
- real notification cannot execute before approval;
- bonus models remain optional outer adapters;
- collaborative/dynamic patterns are not introduced without demonstrated need;
- monorepo boundaries remain intact;
- new deployables/repositories require an ADR.

## 29. Multimodal Stretch Boundary

Only after the core demo is frozen, Gemini multimodal input may extract a **draft** record from a photo/scanned PDF AST report:

```text
image/PDF -> Gemini extraction -> DRAFT -> human verification -> canonical ingestion
```

Model extraction never becomes a canonical lab fact without verification.

## 30. Evolution Path

```text
v0.1.x
Clean Architecture monorepo
Cloud Run + Firestore + Pub/Sub + GCS
ADK graph-first hybrid orchestration
Gemini 3.6 Flash for ambiguous reasoning
resumable investigation
curated/semantic evidence
real approved action
       ↓
0.2–0.5.x
stronger adapters, governance, observability,
selective collaborative specialists when evaluations justify them,
real-world evaluation under approved conditions
       ↓
0.9.x / 1.0.0
production-candidate/production-ready hardening
       ↓
research/deeptech extensions
adaptive/dynamic investigations where justified
pathogen genomics + AMRFinderPlus
phylogenetics
phenotype/genotype fusion
validated surveillance models
```
