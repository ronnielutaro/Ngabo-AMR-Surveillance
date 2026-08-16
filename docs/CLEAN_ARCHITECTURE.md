# Ngabo — Clean Architecture & Monorepo Implementation Guide

**Status:** Required implementation architecture  
**Applies from:** `v0.1.0` onward  
**Repository model:** Monorepo

---

## 1. Decision

Ngabo will be implemented using **Clean Architecture** inside a **single monorepo**.

“Clean Architecture” means the codebase follows an explicit dependency rule: **source-code dependencies point inward toward stable business/domain policy**. Frameworks, cloud SDKs, databases, web transport, Google ADK, Gemini, and UI technologies remain implementation details at the outer layers.

The monorepo means the web application, backend/core service, shared project data, infrastructure configuration, tests, documentation, and release governance live in one Git repository while remaining cleanly separated into independently understandable modules and deployables.

> **Monorepo does not mean monolith.** Ngabo v0.1 still deploys `ngabo-web` and `ngabo-core` independently to Cloud Run.

---

## 2. Why This Matters for Ngabo

Ngabo is expected to evolve from a hackathon MVP into research, pilot, validation, and production-oriented release stages. The architecture must therefore allow us to change:

- Firestore without rewriting AMR domain rules;
- Pub/Sub without rewriting incident workflows;
- Gemini/ADK without rewriting deterministic surveillance logic;
- FastAPI without rewriting use cases;
- notification providers without changing incident policy;
- UI technology without changing backend domain behavior;
- future bioinformatics/genomics adapters without contaminating the current phenotype-surveillance core.

Clean Architecture gives us this separation by treating frameworks and vendors as replaceable outer details.

---

## 3. The Dependency Rule

Allowed dependency direction:

```text
OUTER LAYERS                                      INNER LAYERS

Frameworks / Drivers
FastAPI · Firestore · Pub/Sub · GCS · ADK · Gemini
                 │
                 ▼
Interface Adapters / Infrastructure
                 │
                 ▼
Application / Use Cases / Ports
                 │
                 ▼
Domain / Entities / Value Objects / Domain Services
```

**Dependencies may point inward. Inner layers must never import outer layers.**

Examples:

```text
✓ FastAPI route -> application use case
✓ Firestore repository -> application/domain port
✓ ADK tool adapter -> application service
✓ application use case -> domain entity

✗ domain entity -> FastAPI
✗ domain service -> Firestore SDK
✗ application use case -> google.cloud.firestore
✗ surveillance calculation -> Gemini API
✗ domain model -> Next.js/HTTP DTO
```

---

## 4. Backend Layer Model

Target backend package:

```text
services/core/ngabo/
├── domain/
│   ├── entities/
│   ├── value_objects/
│   ├── enums/
│   ├── events/
│   ├── exceptions/
│   └── services/
│       └── surveillance/
│
├── application/
│   ├── use_cases/
│   ├── workflows/
│   ├── commands/
│   ├── queries/
│   ├── dto/
│   ├── ports/
│   └── agent_contracts/
│
├── interfaces/
│   ├── api/
│   └── events/
│
├── infrastructure/
│   ├── persistence/
│   │   └── firestore/
│   ├── storage/
│   │   └── gcs/
│   ├── messaging/
│   │   └── pubsub/
│   ├── ai/
│   │   ├── gemini/
│   │   └── adk/
│   ├── evidence/
│   └── notifications/
│
└── bootstrap/
    ├── settings.py
    └── container.py
```

The exact filenames can evolve, but these dependency boundaries may not be silently collapsed.

---

## 5. Domain Layer

The **domain** is the most stable inner layer.

It contains business/scientific concepts that should make sense without knowing Ngabo uses Google Cloud, FastAPI, or Gemini.

Examples:

- `ImportBatch`
- `Isolate`
- `ASTResult`
- `SurveillanceSignal`
- `Incident`
- `IncidentEvent`
- `Clarification`
- `Notification` domain state
- incident states and valid state-transition rules
- resistance-profile value objects
- deterministic surveillance domain services
- domain exceptions

### Domain rules

The domain layer must not import:

- FastAPI;
- Firestore;
- Pub/Sub;
- Cloud Storage;
- Google ADK;
- Gemini SDKs;
- email/webhook SDKs;
- HTTP clients for infrastructure concerns.

Prefer plain Python and domain-specific types.

---

## 6. Application Layer

The **application** layer expresses Ngabo use cases and workflow policy.

Examples:

- import laboratory data;
- normalize a batch through defined ports/services;
- analyze an import;
- create an incident from a surveillance signal;
- start/resume an investigation;
- request clarification;
- prepare an incident package;
- record human review;
- request notification;
- acknowledge an incident.

The application layer may depend on `domain`.

It defines **ports/interfaces** for capabilities supplied by outer layers, for example:

```python
class IncidentRepository(Protocol): ...
class RawFileStore(Protocol): ...
class EventPublisher(Protocol): ...
class EvidenceSearchPort(Protocol): ...
class AgentInvestigationPort(Protocol): ...
class NotificationPort(Protocol): ...
```

Application code calls these abstractions. Infrastructure implements them.

The application layer must not directly instantiate Firestore clients, Pub/Sub clients, Gemini clients, or web framework objects.

---

## 7. Interface Layer

The **interfaces** layer adapts external inputs into application commands/use cases.

### HTTP/API

FastAPI routes should:

1. validate transport-level input;
2. translate request DTOs to application commands;
3. invoke a use case;
4. translate the result to an HTTP response.

Routes must not contain scientific/domain logic.

### Event consumers

Pub/Sub handlers should:

1. validate the event envelope;
2. establish correlation/idempotency context;
3. translate the event to an application command;
4. invoke the appropriate use case;
5. return acknowledgement/failure according to event semantics.

Pub/Sub handlers must not duplicate application workflow rules.

---

## 8. Infrastructure Layer

The **infrastructure** layer contains replaceable technical implementations.

Examples:

- Firestore repositories;
- Cloud Storage raw-file adapter;
- Pub/Sub publisher/subscriber adapters;
- Gemini model provider;
- Google ADK agent runtime adapter;
- approved-guidance persistence/search adapter;
- email/webhook/demo notification adapters;
- Cloud Logging / telemetry adapters.

Infrastructure depends on the ports/contracts defined inward. The inner layers do not depend on infrastructure implementations.

---

## 9. Agentic Architecture Under Clean Architecture

Google ADK is an **outer framework**, not the domain.

The runtime agent must preserve the existing deterministic/agent boundary.

Recommended split:

```text
domain/
  deterministic AMR/surveillance rules

application/
  investigation workflow
  agent contracts
  tool/use-case boundaries
  incident-package contract

infrastructure/ai/adk/
  ADK Agent definitions
  ADK tool wrappers
  Gemini configuration
  ADK session/runtime integration
```

A Google ADK tool should normally call an application service/use case rather than reaching straight into Firestore or embedding scientific calculations in the tool wrapper.

Example:

```text
ADK tool
   ↓
application query/use case
   ↓
domain calculation or port
   ↓
infrastructure adapter when required
```

Never:

```text
ADK tool
   ↓
raw Firestore + ad hoc calculations + side effects
```

---

## 10. Deterministic Surveillance Under Clean Architecture

Deterministic surveillance logic belongs in the domain/application core, not infrastructure and not the LLM.

Pure calculations should be testable without:

- network access;
- Google Cloud credentials;
- Firestore emulator;
- Gemini API;
- ADK runtime;
- FastAPI test client.

This includes, where appropriate:

- AST normalization policies;
- resistance-vector construction;
- profile similarity;
- temporal concentration;
- ward/location concentration;
- baseline comparison;
- prototype signal scoring.

Data loading/persistence remains an outer concern.

---

## 11. Frontend Clean Architecture

The Next.js application should use the same dependency philosophy without creating unnecessary ceremony.

Target shape:

```text
apps/web/src/
├── domain/
│   ├── models/
│   └── value-objects/
├── application/
│   ├── use-cases/
│   ├── ports/
│   └── state/
├── infrastructure/
│   ├── api/
│   └── streaming/
├── presentation/
│   ├── components/
│   ├── features/
│   └── layouts/
└── app/
    └── Next.js routes/composition
```

Rules:

- presentation renders explicit domain/application state;
- presentation does not reinterpret scientific meaning from prose;
- API/SSE clients live in infrastructure;
- application logic should be testable without rendering React components;
- UI components do not directly call Firestore, Pub/Sub, Gemini, or other backend/cloud SDKs;
- `app/` acts mainly as route/composition wiring.

Do not over-engineer trivial display-only components merely to force every component through four layers.

---

## 12. Composition Root / Dependency Injection

Concrete infrastructure should be wired at the outermost composition root.

Backend example:

```text
bootstrap/container.py
  ├─ FirestoreIncidentRepository -> IncidentRepository
  ├─ GCSRawFileStore -> RawFileStore
  ├─ PubSubEventPublisher -> EventPublisher
  ├─ ADKInvestigationAdapter -> AgentInvestigationPort
  └─ NotificationAdapter -> NotificationPort
```

Use explicit constructor dependency injection wherever practical.

Avoid service-locator/global-singleton patterns that hide dependencies.

---

## 13. Monorepo Contract

Ngabo uses **one repository** for the product.

Target top-level structure:

```text
ngabo/
├── apps/
│   └── web/                  # Next.js deployable
├── services/
│   └── core/                 # FastAPI/ADK deployable
├── data/
│   ├── synthetic/
│   ├── schemas/
│   └── guidance/
├── docs/
│   ├── adr/
│   ├── product/
│   └── release/
├── infra/
├── .github/
├── CLAUDE.md
├── AGENTS.md
├── ROADMAP.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── README.md
```

### Monorepo rules

- do not split frontend/backend into separate repositories without an ADR;
- deployables may have independent Dockerfiles and Cloud Run services;
- Python dependencies remain scoped to `services/core`;
- JS/TS workspace is managed through pnpm;
- shared contracts must have an explicit owner and direction of dependency;
- cross-package imports must not bypass Clean Architecture boundaries;
- CI should eventually run only relevant jobs where practical, but correctness beats optimization.

---

## 14. Testing by Layer

### Domain tests

Fast, pure unit tests. No network/cloud/model dependency.

### Application tests

Use fakes/in-memory implementations of ports to test use cases and workflows.

### Infrastructure tests

Verify adapters against emulators/test doubles or controlled integration environments.

### Interface/API tests

Verify HTTP/event translation and contract behavior.

### End-to-end tests

Verify the complete seeded workflow through real application boundaries.

A passing end-to-end test does not replace unit tests for domain/application policy.

---

## 15. Enforcement Rules for Coding Agents

Coding agents must treat the dependency rule as an architectural invariant.

Before completing a change, check:

- [ ] Does `domain` import any framework/cloud/AI SDK? If yes, fix it.
- [ ] Does `application` directly use Firestore/Pub/Sub/GCS/Gemini SDKs? If yes, introduce/use a port.
- [ ] Is scientific logic hidden inside FastAPI routes, event handlers, React components, or ADK wrappers? If yes, move it inward.
- [ ] Are infrastructure implementations injected from the composition root?
- [ ] Can core deterministic calculations run without external services?
- [ ] Does the monorepo still preserve independent deployable boundaries?
- [ ] Did a change introduce a new repo/service boundary without an ADR?

---

## 16. Change Policy

Clean Architecture and the monorepo are **frozen architectural decisions**.

Material changes require an ADR before implementation, including:

- splitting Ngabo into multiple repositories;
- moving domain logic into framework-specific layers;
- replacing the layer model with another architectural style;
- allowing application/domain layers to depend directly on vendor SDKs;
- creating a new independently deployed service that changes system boundaries.

Small internal refactors that preserve the dependency rule do not require an ADR.
