# Ngabo — Tech Stack & Architecture Decisions

**Version:** 0.2  
**Date:** 2026-08-16  
**Status:** Frozen hackathon-MVP architecture baseline

## 1. Architecture Style

Ngabo will be implemented using **Clean Architecture inside a monorepo**.

This is a required architectural decision, not a stylistic preference.

The dependency rule is:

```text
Frameworks / Infrastructure
          ↓
Interfaces / Adapters
          ↓
Application / Use Cases / Ports
          ↓
Domain / Entities / Value Objects / Domain Services
```

**Dependencies point inward.** The domain/application core must not depend directly on FastAPI, Firestore, Pub/Sub, Cloud Storage, Google ADK, Gemini, or other vendor/framework SDKs.

See:

- `docs/CLEAN_ARCHITECTURE.md`
- `docs/adr/0003-clean-architecture-monorepo.md`

## 2. Stack Decision

| Layer | Decision | Why |
|---|---|---|
| Architecture | **Clean Architecture** | Protect domain/scientific logic from frameworks/vendors |
| Repository | **GitHub monorepo** | One product/release history with independently deployable apps/services |
| Web UI | **Next.js + TypeScript** | Fast polished incident-response console |
| UI | **Tailwind CSS + shadcn/ui** | Rapid consistent components |
| Core API | **Python + FastAPI** | Strong fit for scientific processing + ADK |
| Schemas | **Pydantic v2** | Typed boundaries and output validation |
| Agent framework | **Google ADK (Python)** | Native fit for hackathon and agent workflows |
| Primary model | **Gemini 3.6 Flash** | Stable 3.5+ model optimized for agentic workflows |
| Fallback model | **Gemini 3.5 Flash** | Compatibility fallback if required |
| Analytics | **pandas + NumPy + SciPy** | Reproducible AST/surveillance calculations |
| State | **Firestore** | Persistent incident/workflow state |
| Raw files/evidence | **Cloud Storage** | Durable object storage |
| Event bus | **Pub/Sub** | Event-driven asynchronous workflow |
| Compute | **Cloud Run** | Serverless, scales to zero |
| Secrets | **Secret Manager / environment-bound secrets** | No committed credentials |
| Logging | **Cloud Logging + structured logs** | Debugging and demo proof |
| Tests | **pytest + ADK evals + Playwright** | Domain, agent, and UI coverage |
| Packages | **uv + pnpm** | Fast deterministic environments |

## 3. Monorepo Contract

Ngabo uses one repository for the full product:

```text
ngabo/
├── apps/
│   └── web/                         # Next.js Cloud Run deployable
├── services/
│   └── core/                        # FastAPI/ADK Cloud Run deployable
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

**Monorepo does not mean monolith.** `ngabo-web` and `ngabo-core` remain independently deployable Cloud Run services.

Do not split them into separate repositories without an ADR.

## 4. Backend Clean Architecture

Target Python package:

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
    ├── settings.py
    └── container.py
```

### Dependency rules

- `domain` depends on no outer Ngabo layer;
- `application` may depend on `domain`;
- `interfaces` may depend on `application` and domain-facing contracts;
- `infrastructure` implements ports/contracts defined inward;
- `bootstrap` wires concrete dependencies.

The exact file names may evolve. The dependency direction may not be silently inverted.

## 5. Core Language Decision

Use Python for the scientific/agentic core because Ngabo combines:

```text
tabular microbiology data
+ statistics
+ agent tools
+ evaluation
+ future bioinformatics
```

FastAPI is an **outer delivery mechanism**. It must not own domain or scientific logic.

Pydantic is used at typed boundaries, but domain concepts should not be unnecessarily coupled to HTTP transport models.

## 6. Frontend Clean Architecture

Next.js + TypeScript powers the incident-response console.

Target shape:

```text
apps/web/src/
├── domain/
├── application/
├── infrastructure/
│   ├── api/
│   └── streaming/
├── presentation/
│   ├── components/
│   ├── features/
│   └── layouts/
└── app/                             # Next.js routes/composition
```

Rules:

- UI does not call Firestore/Pub/Sub/Gemini directly;
- API/SSE clients live in infrastructure;
- behavioral application logic is separable from React rendering;
- presentation renders explicit backend/domain state rather than reinterpreting medical meaning from prose;
- do not over-engineer trivial presentational components merely for architectural ceremony.

> **UI principle:** Ngabo is an incident-response console. Chat exists only for targeted clarification.

## 7. Gemini Decision

For v0.1, use the **Gemini API** from the ADK-based backend.

Primary model:

`gemini-3.6-flash`

Use for:

- investigation planning;
- tool selection;
- contextual synthesis;
- clarification formulation;
- incident-package narrative.

Keep model access behind an inward-defined port/contract so future Vertex AI or model changes do not rewrite application/domain logic.

Store credentials through Secret Manager / Cloud Run secret injection.

Determinism belongs in code and schemas—not sampling tricks.

## 8. Google ADK Decision

Use Google ADK Python.

ADK is an **infrastructure/framework concern**.

Recommended boundary:

```text
ADK tool wrapper
      ↓
application use case/query
      ↓
domain calculation or inward-defined port
      ↓
infrastructure adapter when required
```

Do not turn deterministic functions into agents, and do not let ADK tool wrappers become an alternate service layer with raw database access and ad hoc business logic.

## 9. Deployment Shape

Hackathon MVP uses two Cloud Run services:

```text
ngabo-web
  Next.js
     |
     v
ngabo-core
  FastAPI + Clean Architecture core + ADK adapter
```

The backend is **logically modular before physically distributed**. Split into additional deployables later only when scale/fault isolation or product boundaries justify it through an ADR.

## 10. Event Architecture

Three Pub/Sub topics:

### `ngabo-import-events`
- `lab.import.received`
- `lab.batch.normalized`
- `lab.import.failed`

### `ngabo-surveillance-events`
- `surveillance.signal.detected`

### `ngabo-incident-events`
- `incident.investigation.requested`
- `incident.clarification.received`
- `incident.review.approved`
- `incident.review.rejected`
- `incident.notification.requested`
- `incident.acknowledged`

Event envelope:

```json
{
  "event_id": "uuid",
  "event_type": "surveillance.signal.detected",
  "occurred_at": "ISO-8601",
  "correlation_id": "uuid",
  "entity_id": "uuid",
  "schema_version": 1
}
```

Pub/Sub handlers are interface adapters: they validate/translate events and invoke application use cases. They must not duplicate workflow/domain logic.

## 11. Firestore Role

Firestore stores **operational workflow state**, not long-term scientific analytics.

Collections:

```text
imports/
isolates/
signals/
incidents/
incident_events/
clarifications/
notifications/
guidance_sources/
processed_events/
```

Firestore-specific repository implementations live in `infrastructure/persistence/firestore` and implement inward-defined repository ports.

Future high-scale analytics can move to BigQuery or another analytical store without changing core domain behavior.

## 12. Cloud Storage Role

Prefixes:

```text
raw-imports/
approved-guidance/
normalized-exports/
demo-artifacts/
```

Cloud Storage is accessed through an infrastructure adapter/port boundary. Raw uploaded files are immutable and hashed.

## 13. Evidence Retrieval

v0.1 uses a curated, versioned evidence library with:

- source ID;
- title;
- publisher;
- official URL;
- date/version;
- tags;
- approved content/chunks.

Evidence search is exposed to the application/agent through a port. Do not add a vector database unless the corpus actually requires one.

## 14. Notification Boundary

Define an inward-facing port such as:

```python
class NotificationPort(Protocol):
    async def send_incident_alert(...): ...
```

Infrastructure adapters:

1. deterministic demo adapter;
2. optional real email/webhook adapter.

## 15. Surveillance Engine

Deterministic surveillance is core domain/application logic.

Modules/concepts include:

- schema/AST normalization policies;
- resistance-vector construction;
- profile similarity;
- temporal concentration;
- ward concentration;
- baseline comparison;
- signal scoring.

Pure calculations must be testable without FastAPI, Firestore, Pub/Sub, ADK, Gemini, or network access.

The signal score is an **investigation-priority score**, not an outbreak probability.

## 16. Architecture Rules

1. **Clean Architecture dependency rule is mandatory.**
2. **Monorepo is mandatory unless changed by ADR.**
3. If a task can be deterministic, make it deterministic.
4. Domain/application layers do not directly depend on vendor/cloud/AI SDKs.
5. Agents may request tool results; they may not rewrite source facts.
6. Every side effect needs an idempotency strategy.
7. Every meaningful claim is observed data, deterministic calculation, cited guidance, or labelled hypothesis.
8. Infrastructure implementations are wired at the outer composition root.
9. Do not add infrastructure merely to make the architecture diagram look impressive.

## 17. Deferred Technology

Not before the core demo works:

- GKE;
- Cloud SQL;
- BigQuery;
- vector DB;
- Redis/Kafka;
- LangGraph;
- additional LLM vendors;
- full RBAC platform;
- genomic pipeline;
- AMRFinderPlus;
- live hospital connectors.

## 18. References

- Hackathon rules: https://allthingsagentichackathon.devpost.com/rules
- Hackathon resources: https://allthingsagentichackathon.devpost.com/resources
- Gemini 3.6 Flash: https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash
- Google ADK: https://google.github.io/adk-docs/
- Cloud Run: https://cloud.google.com/run/docs
- Firestore: https://cloud.google.com/firestore/docs
- Pub/Sub: https://cloud.google.com/pubsub/docs
