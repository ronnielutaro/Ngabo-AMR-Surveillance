# Ngabo — System Design

**Version:** 0.3  
**Date:** 2026-08-16  
**Status:** Hackathon MVP system design  
**Architecture:** Clean Architecture in a monorepo

## 1. Design Objective

Build the smallest architecture that convincingly demonstrates:

> **event-driven AMR surveillance → autonomous, resumable investigation → human-reviewed response → real observable action**

while preserving deterministic scientific logic, an auditable workflow, strict Clean Architecture dependency boundaries, and strong hackathon proof of execution.

See:

- `docs/CLEAN_ARCHITECTURE.md`
- `docs/HACKATHON_ALIGNMENT.md`
- `docs/ADK_RUNTIME.md`

## 2. Architectural Principles

Ngabo follows these system-wide rules:

1. **Clean Architecture:** dependencies point inward toward domain/application policy.
2. **Monorepo:** frontend, backend, data, infra, docs, tests, and release governance share one repository.
3. **Independent deployables:** monorepo does not collapse `ngabo-web` and `ngabo-core` into one runtime.
4. **Deterministic scientific core:** surveillance calculations remain ordinary reproducible code.
5. **Agentic ambiguity only:** Gemini/ADK handle investigation planning, context, clarification, evidence synthesis, and coordination.
6. **Ports/adapters:** Firestore, Pub/Sub, GCS, ADK, Gemini, EmbeddingGemma, optional MedGemma, and notifications are outer implementations.
7. **Persisted workflow:** Firestore is canonical operational state.
8. **Resumable execution:** ADK execution continuity complements Firestore state where supported/stable.
9. **Bounded autonomy:** human approval gates consequential escalation.
10. **Proof of action:** the hosted demo performs at least one real authorized external action after approval.
11. **Observable autonomy:** logs/traces expose workflow/tool facts without exposing private chain-of-thought.

## 3. System Context

```mermaid
flowchart LR
    U[Microbiologist / AMR Officer]
    W[Ngabo Web Console]
    C[Ngabo Core]
    G[Gemini 3.6 Flash + Google ADK]
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

EmbeddingGemma and MedGemma are shown as outer adapters. EmbeddingGemma is planned only after the core deployed path is green; MedGemma is optional and may be omitted.

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

The diagram expresses **source-code dependency direction**, not runtime data flow. Inner layers never import outer frameworks/vendors.

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
    Core --> Agent[Google ADK]
    Agent --> Gemini[Gemini 3.6 Flash]
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
Application-level metadata correlating an incident to agent execution without leaking ADK classes into the domain.

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

### EvidenceSource
Approved guidance/reference metadata.

### Clarification
Question + human answer/provenance.

### Notification
Outbound action + delivery/ack state.

These concepts must remain meaningful without knowing which database, web framework, agent runtime, or LLM provider is used.

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

## 11. Agent Investigation Sequence

```mermaid
sequenceDiagram
    participant Bus as Pub/Sub Adapter
    participant Handler as Event Interface
    participant App as Investigation Workflow
    participant Agent as AgentInvestigationPort
    participant ADK as Google ADK Adapter
    participant Tools as Application/Domain Tools
    participant Repo as Repository Ports
    participant UI

    Bus->>Handler: surveillance.signal.detected
    Handler->>App: StartInvestigation command
    App->>Repo: Create Incident + agent run reference
    App->>Agent: Investigate incident
    Agent->>ADK: Start/resume invocation
    ADK->>Tools: get_incident_context
    ADK->>Tools: compare_resistance_profiles
    ADK->>Tools: get_baseline_summary
    ADK->>Tools: search_approved_guidance
    ADK->>Tools: get_missing_fields

    alt clarification needed
        ADK->>App: Request clarification
        App->>Repo: WAITING_FOR_CLARIFICATION
        UI->>App: Submit clarification
        App->>Agent: Resume same incident/invocation where supported
        Agent->>ADK: Resume
    end

    ADK->>App: Structured incident package
    App->>App: Validate package/source IDs/claims
    App->>Repo: WAITING_FOR_REVIEW
```

Google ADK/Gemini are concrete infrastructure implementations behind the application contract. Firestore remains the business/workflow source of truth even when ADK checkpoint/resume is used.

## 12. Interruption / Resume Sequence

```mermaid
sequenceDiagram
    participant App as Investigation Workflow
    participant Repo as Firestore Port
    participant ADK as ADK Adapter

    App->>ADK: Start investigation
    ADK--xADK: Invocation interrupted / retryable failure
    ADK->>Repo: execution metadata already correlated through application workflow
    App->>Repo: Load incident + AgentRunReference
    App->>ADK: Resume invocation if supported
    ADK->>App: Continue / package / clarification
    App->>Repo: Append resume/retry audit event
```

All tools must be safe under possible repeated execution. Resumability is not permission to create non-idempotent agent side effects.

## 13. Evidence Retrieval Sequence

Initial core may use deterministic/tag retrieval. Planned post-core semantic retrieval:

```mermaid
sequenceDiagram
    participant Agent as ADK Agent
    participant Port as EvidenceSearchPort
    participant Embed as EmbeddingGemma Adapter
    participant Corpus as Approved Guidance Corpus

    Agent->>Port: search approved guidance
    Port->>Embed: embed query
    Corpus->>Embed: precomputed approved embeddings
    Embed->>Embed: cosine similarity
    Embed-->>Port: approved source IDs + chunks + scores
    Port-->>Agent: traceable evidence only
```

No arbitrary web result becomes approved evidence in v0.1.

## 14. Human Review + Real Action Sequence

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

## 15. Incident State Machine

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

Agent failures/retries are recorded as execution/audit metadata without casually inventing new business states. If implementation needs new incident states, update the domain model and docs explicitly.

## 16. Idempotency

Pub/Sub and resumed agent execution can cause repeated work.

Every event has a unique `event_id`.

Before a state-changing side effect:

1. application workflow applies the idempotency contract;
2. infrastructure persistence performs the required transactional operation where possible;
3. processed-event state is persisted;
4. side effect is not repeated on redelivery.

Notifications use an idempotency key such as:

```text
incident_id + action_type + package_version
```

Read-only agent tools are naturally repeatable. Any state-changing tool must be explicitly idempotent. The agent itself must not directly own consequential external effects.

## 17. Concurrency

Incident has numeric `version`.

Updates require expected version and valid state transition. Conflicts return `409` at the HTTP boundary.

This prevents reviewer approval racing against a still-changing package or a resumed investigation.

## 18. Data Integrity

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
- retryable agent execution metadata.

The agent cannot mutate immutable source facts.

## 19. API Surface

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

## 20. Frontend Architecture

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

See `docs/UI_UX_SPEC.md`.

## 21. Live UI / Demo-Proof Timeline

Preferred: Server-Sent Events for incident state/tool events.

Fallback: short polling if SSE threatens implementation stability.

Public-safe timeline events include:

```text
DATA_NORMALIZED
SURVEILLANCE_SIGNAL_DETECTED
AGENT_INVESTIGATION_STARTED
AGENT_TOOL_STARTED
AGENT_TOOL_COMPLETED
EVIDENCE_RETRIEVED
CLARIFICATION_REQUESTED
CLARIFICATION_RECEIVED
AGENT_INVESTIGATION_RESUMED
INCIDENT_PACKAGE_VALIDATED
REVIEW_APPROVED
NOTIFICATION_SENT
NOTIFICATION_ACKNOWLEDGED
```

These events expose observable workflow facts, not hidden model chain-of-thought.

## 22. Required Failure Behaviors

| Failure | Behavior |
|---|---|
| invalid CSV | visible validation failure |
| unknown organism | flag unknown; never invent mapping |
| missing ward/specimen | persist missingness |
| duplicate Pub/Sub event | no duplicate incident/action |
| Gemini timeout | bounded retry + visible error |
| ADK invocation interruption | safe resume/retry using persisted references where supported |
| tool failure | visible failed/retryable investigation state |
| no guidance result | say evidence unavailable |
| malformed model package | reject with schema validation |
| reviewer rejection | stop action and persist reason |
| notification failure | retryable state with idempotency |
| app restart | resume from persisted application state |
| trace/log unavailable | workflow still functions; observability degrades only |

Errors are translated at outer interfaces; inner layers use domain/application error types rather than framework-specific HTTP exceptions.

## 23. Observability

Every log/event carries where relevant:

- correlation ID;
- incident ID;
- event ID;
- agent session ID;
- agent invocation ID;
- agent run ID;
- tool name;
- package version.

Track:

- import time;
- normalization time;
- detector time;
- agent invocation time;
- tool latency/error;
- retries/resumes;
- clarification count;
- package generation time;
- notification latency;
- model/token usage where available.

Use Cloud Logging plus ADK/Cloud Trace/OpenTelemetry where stable. Prefer metadata/no-content tracing; broad prompt/response capture is not required for the hackathon and should not become the default architecture.

Observability is infrastructure. Domain behavior must not depend on telemetry availability.

## 24. Testing & Evaluation Strategy

### Domain
Pure unit tests without cloud, HTTP, model, or network access.

### Application
Use-case/workflow tests using fakes/in-memory port implementations.

### Infrastructure
Adapter integration/contract tests using emulators/test doubles or controlled integration environments.

### Interfaces
API/event contract tests.

### ADK evaluation
Evaluate both final structured behavior and trajectory/tool use where supported:

- correct tool selection;
- missing-data clarification;
- no-source behavior;
- tool failure;
- prompt injection;
- fabricated citation/isolate rejection;
- overclaiming boundaries.

### End-to-end

```text
upload
  -> deterministic signal
  -> Pub/Sub
  -> investigate
  -> clarify
  -> resume
  -> package
  -> review
  -> real notify
  -> acknowledge
```

The final public `EVALUATION.md` records methodology/results/limitations.

## 25. Architecture Enforcement

Before completing a change, verify:

- domain imports no FastAPI/GCP/ADK/Gemini/Gemma SDK;
- application does not instantiate Firestore/PubSub/GCS/model clients;
- routes/event handlers contain no scientific/business rules;
- ADK wrappers call inward use cases/contracts rather than becoming a parallel business layer;
- deterministic surveillance tests run without external services;
- concrete adapters are wired at composition roots;
- Firestore remains workflow truth even with ADK resume support;
- real notification cannot execute before approval;
- bonus models remain optional outer adapters;
- monorepo boundaries remain intact;
- new deployables/repositories require an ADR.

## 26. Multimodal Stretch Boundary

Only after the core demo is frozen, Gemini multimodal input may extract a **draft** record from a photo/scanned PDF AST report:

```text
image/PDF -> Gemini extraction -> DRAFT -> human verification -> canonical ingestion
```

Model extraction never becomes a canonical lab fact without verification.

## 27. Evolution Path

```text
v0.1.x
Clean Architecture monorepo
Cloud Run + Firestore + Pub/Sub + GCS
Gemini + ADK
resumable investigation
curated/semantic evidence
real approved action
       ↓
0.2–0.5.x
stronger adapters, governance, observability,
real-world evaluation under approved conditions
       ↓
0.9.x / 1.0.0
production-candidate/production-ready hardening
       ↓
research/deeptech extensions
pathogen genomics + AMRFinderPlus
phylogenetics
phenotype/genotype fusion
validated surveillance models
```
