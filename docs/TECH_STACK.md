# Ngabo — Tech Stack & Architecture Decisions

**Version:** 0.3  
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

**Dependencies point inward.** The domain/application core must not depend directly on FastAPI, Firestore, Pub/Sub, Cloud Storage, Google ADK, Gemini, Gemma-family models, or other vendor/framework SDKs.

See:

- `docs/CLEAN_ARCHITECTURE.md`
- `docs/HACKATHON_ALIGNMENT.md`
- `docs/ADK_RUNTIME.md`
- `docs/adr/0003-clean-architecture-monorepo.md`
- `docs/adr/0004-hackathon-agent-runtime-and-bonus-models.md`

## 2. Stack Decision

| Layer | Decision | Why |
|---|---|---|
| Architecture | **Clean Architecture** | Protect domain/scientific logic from frameworks/vendors |
| Repository | **GitHub monorepo** | One product/release history with independently deployable apps/services |
| Web UI | **Next.js + TypeScript** | Polished incident-response console |
| UI | **Tailwind CSS + shadcn/ui** | Rapid consistent components |
| Core API | **Python + FastAPI** | Strong fit for scientific processing + ADK |
| Schemas | **Pydantic v2** | Typed boundaries and output validation |
| Agent framework | **Google ADK (Python)** | Required/strong fit for asynchronous agent workflows |
| Primary orchestrator model | **Gemini 3.6 Flash** | Stable 3.5+ model optimized for agentic workflows |
| Fallback model | **Gemini 3.5 Flash** | Compatibility fallback if required |
| Planned retrieval model | **EmbeddingGemma** | Lightweight semantic retrieval over approved guidance |
| Gated medical model | **MedGemma** | Optional bounded evidence interpretation after core stability/evaluation |
| Analytics | **pandas + NumPy + SciPy** | Reproducible AST/surveillance calculations |
| State | **Firestore** | Persistent incident/workflow state |
| Raw files/evidence | **Cloud Storage** | Durable object storage |
| Event bus | **Pub/Sub** | Event-driven asynchronous workflow |
| Compute | **Cloud Run** | Serverless, scales to zero |
| Secrets | **Secret Manager / environment-bound secrets** | No committed credentials |
| Logging | **Cloud Logging + structured logs** | Debugging and demo proof |
| Tracing | **ADK/Cloud Trace/OpenTelemetry where stable** | Inspect agent/tool execution without exposing hidden reasoning |
| Tests | **pytest + ADK evals + Playwright** | Domain, agent, and UI coverage |
| Packages | **uv + pnpm** | Fast deterministic environments |

EmbeddingGemma is a planned post-core v0.1 integration. MedGemma is a gated stretch. Neither is allowed to delay the required Gemini + ADK + Cloud Run + Firestore + Pub/Sub core.

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
│   ├── ai/embedding_gemma/
│   ├── ai/medgemma/                 # only if stretch is accepted
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

- UI does not call Firestore/Pub/Sub/Gemini/ADK directly;
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

Use Flash first. Do not introduce an expensive model escalation path until evaluation proves a narrow step needs it.

Keep model access behind an inward-defined port/contract so future Vertex AI or model changes do not rewrite application/domain logic.

Store credentials through Secret Manager / Cloud Run secret injection.

Determinism belongs in code and schemas—not sampling tricks.

## 8. Google ADK Decision

Use Google ADK Python as the actual agent runtime.

ADK is an **infrastructure/framework concern** but must provide real runtime value rather than existing only to satisfy the rules.

Required v0.1 usage:

- bounded typed tools;
- persisted session/invocation/run references;
- resumable investigation execution where supported and stable by the installed ADK version;
- targeted human input for clarification;
- structured outputs;
- ADK evaluation;
- tracing/observability integration;
- explicit loop/time/retry limits.

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

See `docs/ADK_RUNTIME.md`.

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

### Hackathon deployment controls

Required:

- Cloud Run minimum instances `0` unless documented exception;
- explicit maximum-instance caps;
- right-sized CPU/RAM;
- Google Cloud budget + email alert;
- secrets injected, never committed;
- internal/event endpoints protected;
- expensive public endpoints protected/rate-limited where practical;
- judge-accessible hosted service retained through the judging period.

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

At-least-once delivery means all state-changing consumers must be idempotent.

## 11. Firestore Role

Firestore stores **operational workflow state**, not long-term scientific analytics.

Collections may include:

```text
imports/
isolates/
signals/
incidents/
incident_events/
agent_runs/
clarifications/
notifications/
guidance_sources/
processed_events/
```

Persist agent session/invocation/run references without making ADK state the authoritative business state.

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

Keep storage footprints light; do not retain large temporary execution artifacts indefinitely.

## 13. Evidence Retrieval

v0.1 uses a curated, versioned evidence library with:

- source ID;
- title;
- publisher;
- official URL;
- date/version;
- tags;
- approved content/chunks.

Evidence search is exposed through an inward-defined `EvidenceSearchPort`.

### Initial fallback

A simple deterministic/tag/keyword implementation is acceptable while the core workflow is being built.

### Planned EmbeddingGemma adapter

After the deployed core flow is stable:

```text
approved guidance corpus
       ↓
EmbeddingGemma embeddings
       ↓
lightweight deterministic similarity index
       ↓
source IDs + approved chunks
```

For hackathon scale, prefer a small in-process NumPy/cosine implementation. Do not add a vector database solely to earn a bonus.

## 14. Optional MedGemma Boundary

MedGemma is **not** core v0.1 infrastructure.

It may be added only as a bounded evidence-interpretation adapter after the core, EmbeddingGemma, deployment, and evaluations are stable.

It may not:

- prescribe;
- diagnose;
- confirm an outbreak;
- own deterministic surveillance logic;
- create uncited guidance.

If it does not materially improve evaluation, omit it.

## 15. Notification Boundary

Define an inward-facing port such as:

```python
class NotificationPort(Protocol):
    async def send_incident_alert(...): ...
```

Infrastructure adapters:

1. deterministic demo adapter for tests/local reproducibility;
2. **at least one real authorized external adapter for the hosted/demo v0.1 path**.

The real adapter must execute only after human approval, persist delivery result, and support idempotent retry.

## 16. Surveillance Engine

Deterministic surveillance is core domain/application logic.

Modules/concepts include:

- schema/AST normalization policies;
- resistance-vector construction;
- profile similarity;
- temporal concentration;
- ward concentration;
- baseline comparison;
- signal scoring.

Pure calculations must be testable without FastAPI, Firestore, Pub/Sub, ADK, Gemini, Gemma models, or network access.

The signal score is an **investigation-priority score**, not an outbreak probability.

## 17. Observability

Ngabo uses structured application logs plus ADK/runtime tracing where stable.

Required correlation fields include:

```text
correlation_id
incident_id
event_id
agent_session_id
agent_invocation_id
agent_run_id
tool_name
package_version
```

Prefer metadata-first/no-content traces. Do not enable broad prompt-response content capture by default, even though v0.1 uses synthetic data.

BigQuery agent analytics remains deferred unless it produces clear v0.1 value; do not add it simply because tooling supports it.

## 18. Testing & Evaluation

Required layers:

- pure domain/unit tests;
- application use-case tests with fakes;
- infrastructure adapter/contract tests;
- API/event interface tests;
- ADK trajectory/output evaluations;
- Playwright E2E;
- deployed seeded scenario.

A public `EVALUATION.md` is a submission deliverable.

## 19. Architecture Rules

1. **Clean Architecture dependency rule is mandatory.**
2. **Monorepo is mandatory unless changed by ADR.**
3. If a task can be deterministic, make it deterministic.
4. Domain/application layers do not directly depend on vendor/cloud/AI SDKs.
5. Agents may request tool results; they may not rewrite source facts.
6. Every side effect needs an idempotency strategy.
7. Every meaningful claim is observed data, deterministic calculation, cited guidance, or labelled hypothesis.
8. Infrastructure implementations are wired at the outer composition root.
9. Firestore owns workflow truth; ADK resumability complements it.
10. Bonus models may not weaken the core architecture or demo reliability.
11. Do not add infrastructure merely to make the architecture diagram look impressive.

## 20. Deferred Technology / Features

Not before the core demo works:

- GKE;
- Cloud SQL;
- BigQuery;
- vector DB;
- Redis/Kafka;
- LangGraph;
- additional non-Google LLM vendors;
- full RBAC platform;
- genomic pipeline;
- AMRFinderPlus;
- live hospital connectors;
- MedGemma unless gated criteria pass;
- multimodal AST/PDF ingestion until the core is frozen.

## 21. References

- Hackathon rules: https://allthingsagentichackathon.devpost.com/rules
- Hackathon resources: https://allthingsagentichackathon.devpost.com/resources
- Google ADK: https://google.github.io/adk-docs/
- Google Agents CLI: https://google.github.io/agents-cli/
- Gemini API: https://ai.google.dev/gemini-api/docs
- EmbeddingGemma: https://ai.google.dev/gemma/docs/embeddinggemma
- MedGemma: https://developers.google.com/health-ai-developer-foundations/medgemma
- Cloud Run: https://cloud.google.com/run/docs
- Firestore: https://cloud.google.com/firestore/docs
- Pub/Sub: https://cloud.google.com/pubsub/docs
