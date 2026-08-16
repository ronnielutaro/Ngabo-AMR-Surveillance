# Ngabo — System Design

**Version:** 0.2  
**Date:** 2026-08-16  
**Status:** Hackathon MVP system design  
**Architecture:** Clean Architecture in a monorepo

## 1. Design Objective

Build the smallest architecture that convincingly demonstrates:

> **event-driven AMR surveillance → autonomous investigation → human-reviewed response → observable action**

while preserving deterministic scientific logic, an auditable workflow, and strict Clean Architecture dependency boundaries.

See `docs/CLEAN_ARCHITECTURE.md` for the implementation-level dependency contract.

## 2. Architectural Principles

Ngabo follows these system-wide rules:

1. **Clean Architecture:** dependencies point inward toward domain/application policy.
2. **Monorepo:** frontend, backend, data, infra, docs, tests, and release governance share one repository.
3. **Independent deployables:** monorepo does not collapse `ngabo-web` and `ngabo-core` into one runtime.
4. **Deterministic scientific core:** surveillance calculations remain ordinary reproducible code.
5. **Agentic ambiguity only:** Gemini/ADK handle investigation planning, context, clarification, evidence synthesis, and coordination.
6. **Ports/adapters:** Firestore, Pub/Sub, GCS, ADK, Gemini, and notifications are outer implementations.
7. **Persisted workflow:** Firestore is canonical operational state.
8. **Bounded autonomy:** human approval gates consequential escalation.

## 3. System Context

```mermaid
flowchart LR
    U[Microbiologist / AMR Officer]
    W[Ngabo Web Console]
    C[Ngabo Core]
    G[Gemini + Google ADK]
    F[(Firestore)]
    S[(Cloud Storage)]
    P[Pub/Sub]
    N[Notification Adapter]
    E[Approved Evidence Library]

    U --> W
    W --> C
    C --> S
    C --> F
    C --> P
    P --> C
    C --> G
    G --> C
    C --> E
    C --> N
```

## 4. Clean Architecture View

```mermaid
flowchart TB
    subgraph Outer[Frameworks / Infrastructure]
        FastAPI[FastAPI]
        Firestore[Firestore]
        PubSub[Pub/Sub]
        GCS[Cloud Storage]
        ADK[Google ADK / Gemini]
        Notify[Notification Providers]
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
    Notify --> InfraAdapters

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
    Core --> Gemini[Gemini API / Google ADK]
    Core --> Logs[Cloud Logging]
    Core --> Notify[Email/Webhook/Demo Adapter]
```

### MVP deployment principle

Use one backend deployment with clean internal layers. Split services later only when real scale, fault isolation, or product boundaries justify the operational cost.

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
│   ├── evidence/
│   └── notifications/
└── bootstrap/
```

### Layer responsibilities

**Domain** — AMR/surveillance entities, value objects, rules, state policy, pure deterministic services.  
**Application** — use cases, workflows, commands/queries, ports, agent-facing contracts.  
**Interfaces** — HTTP and event translation into application commands.  
**Infrastructure** — Firestore/GCS/PubSub/Gemini/ADK/notification implementations.  
**Bootstrap** — composition root and dependency wiring.

## 8. Core Domain Entities

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

### EvidenceSource
Approved guidance/reference metadata.

### Clarification
Question + human answer/provenance.

### Notification
Outbound action + delivery/ack state.

These domain concepts must remain meaningful without knowing which database, web framework, or LLM provider is used.

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
    App->>Domain: Parse/validate/normalize through deterministic services
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
    participant Tools as Application/Domain Tools
    participant Repo as Repository Ports
    participant UI

    Bus->>Handler: surveillance.signal.detected
    Handler->>App: StartInvestigation command
    App->>Repo: Create Incident
    App->>Agent: Investigate incident
    Agent->>Tools: get_incident_context
    Agent->>Tools: compare_resistance_profiles
    Agent->>Tools: get_baseline_summary
    Agent->>Tools: search_approved_guidance
    Agent->>Tools: get_missing_fields

    alt clarification needed
        Agent->>App: Request clarification
        App->>Repo: WAITING_FOR_CLARIFICATION
        UI->>App: Submit clarification
        App->>Agent: Resume investigation
    end

    Agent->>App: Structured incident package
    App->>Repo: WAITING_FOR_REVIEW
```

Google ADK/Gemini are concrete infrastructure implementations behind the agent/application contract. They do not become the source of domain truth.

## 12. Human Review + Action Sequence

```mermaid
sequenceDiagram
    actor Reviewer
    participant UI
    participant API as HTTP Interface
    participant App as Review Use Case
    participant Repo as Repository Port
    participant Events as EventPublisher Port
    participant Notify as Notification Port

    Reviewer->>UI: Review package
    UI->>API: Approve / Reject / More Info
    API->>App: ReviewIncident command

    alt approved
        App->>Repo: Record approval
        App->>Events: incident.notification.requested
        App->>Notify: via later event workflow
    else rejected
        App->>Repo: Record rejection
    end
```

The concrete notification provider is an infrastructure adapter.

## 13. Incident State Machine

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

The state-transition policy belongs in the domain/application core, not in FastAPI routes, React components, or Firestore adapters.

## 14. Idempotency

Pub/Sub may redeliver events.

Every event has a unique `event_id`.

Before a state-changing side effect:

1. application workflow checks/uses the idempotency contract;
2. infrastructure persistence performs the required transactional operation where possible;
3. processed-event state is persisted;
4. side effect is not repeated on redelivery.

Notifications use an idempotency key such as:

```text
incident_id + action_type + package_version
```

Idempotency policy belongs inward; Firestore transaction mechanics are infrastructure details.

## 15. Concurrency

Incident has numeric `version`.

Updates require expected version and valid state transition. Conflicts return `409` at the HTTP boundary.

This prevents a reviewer approval racing against a still-changing package.

## 16. Data Integrity

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
- acknowledgement.

The agent cannot mutate immutable source facts.

## 17. API Surface

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

Routes/controllers should remain thin transport adapters.

## 18. Frontend Architecture

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

See `docs/UI_UX_SPEC.md` for the product/UI contract.

## 19. Live UI

Preferred: Server-Sent Events for incident state/tool events.

Fallback: short polling if SSE threatens implementation stability.

Live-update infrastructure remains replaceable and does not change incident domain state semantics.

## 20. Required Failure Behaviors

| Failure | Behavior |
|---|---|
| invalid CSV | visible validation failure |
| unknown organism | flag unknown; never invent mapping |
| missing ward/specimen | persist missingness |
| duplicate Pub/Sub event | no duplicate incident/action |
| Gemini timeout | bounded retry + visible error |
| tool failure | visible failed investigation state |
| no guidance result | say evidence unavailable |
| malformed model package | reject with schema validation |
| reviewer rejection | stop action and persist reason |
| notification failure | retryable state |
| app restart | resume from persisted state |

Errors are translated at outer interfaces; inner layers use domain/application error types rather than framework-specific HTTP exceptions.

## 21. Observability

Every log/event carries where relevant:

- correlation ID;
- incident ID;
- event ID;
- agent run ID;
- tool name.

Track:

- import time;
- normalization time;
- detector time;
- agent/tool latency;
- clarification count;
- package generation time;
- notification latency.

Observability is infrastructure. Domain behavior must not depend on Cloud Logging being available.

## 22. Testing Strategy by Layer

### Domain

Pure unit tests without cloud, HTTP, model, or network access.

### Application

Use-case/workflow tests using fakes/in-memory port implementations.

### Infrastructure

Adapter integration/contract tests using emulators/test doubles or controlled integration environments.

### Interfaces

API/event contract tests.

### End-to-end

Full seeded workflow:

```text
upload -> signal -> investigate -> clarify -> package -> review -> notify -> acknowledge
```

## 23. Architecture Enforcement

Before completing a change, verify:

- domain imports no FastAPI/GCP/ADK/Gemini SDK;
- application does not instantiate Firestore/PubSub/GCS/Gemini clients;
- routes/event handlers contain no scientific/business rules;
- ADK wrappers call inward use cases/contracts rather than becoming a parallel business layer;
- deterministic surveillance tests run without external services;
- concrete adapters are wired at composition roots;
- monorepo boundaries remain intact;
- new deployables/repositories require an ADR.

## 24. Evolution Path

```text
v0.1.x
Clean Architecture monorepo
Cloud Run + Firestore + Pub/Sub + GCS
curated evidence
phenotype surveillance
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
