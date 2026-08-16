# Ngabo — Tech Stack & Architecture Decisions

**Version:** 0.1  
**Date:** 2026-08-16  
**Status:** Proposed stack to freeze before implementation

## 1. Stack Decision

| Layer | Decision | Why |
|---|---|---|
| Web UI | **Next.js + TypeScript** | Fast polished incident console |
| UI | **Tailwind CSS + shadcn/ui** | Rapid consistent components |
| Core API | **Python + FastAPI** | Strong fit for scientific processing + ADK |
| Schemas | **Pydantic v2** | Typed boundaries and output validation |
| Agent framework | **Google ADK (Python)** | Native fit for hackathon and agent workflows |
| Primary model | **Gemini 3.6 Flash** | Stable 3.5+ model optimized for agentic workflows |
| Fallback model | **Gemini 3.5 Flash** | Stable compatibility fallback |
| Analytics | **pandas + NumPy + SciPy** | Reproducible AST/surveillance calculations |
| State | **Firestore** | Persistent incident/workflow state |
| Raw files/evidence | **Cloud Storage** | Durable object storage |
| Event bus | **Pub/Sub** | Event-driven asynchronous workflow |
| Compute | **Cloud Run** | Serverless, scales to zero |
| Secrets | **Secret Manager / environment-bound secrets** | No committed credentials |
| Logging | **Cloud Logging + structured logs** | Debugging and demo proof |
| Tests | **pytest + ADK evals + Playwright** | Domain, agent, and UI coverage |
| Packages | **uv + pnpm** | Fast deterministic environments |
| Repo | **GitHub monorepo** | Judge visibility + reproducibility |

## 2. Core Language Decision

Use Python for the scientific/agentic core because Ngabo combines:

```text
tabular microbiology data
+ statistics
+ agent tools
+ evaluation
+ future bioinformatics
```

FastAPI provides the HTTP boundary while allowing the surveillance engine and ADK agent to share typed Python domain models.

## 3. UI Decision

Next.js + TypeScript powers:

- import workflow;
- incident tables;
- status visualizations;
- timelines;
- evidence package;
- human review.

> **UI principle:** Ngabo is an incident-response console. Chat exists only for targeted clarification.

## 4. Gemini Decision

### Model access

For v0.1, use the **Gemini API** from the ADK-based backend.

Why:

- the hackathon explicitly permits Gemini API or Vertex AI;
- `gemini-3.6-flash` is currently a stable Gemini model;
- direct Gemini API access keeps model availability simple while Google Cloud still owns deployment, state, storage, events, logging, and secrets.

Keep model access behind a small `ModelProvider` / configuration boundary so a future Vertex AI switch does not affect domain or agent logic.

Store the Gemini API credential through Secret Manager / Cloud Run secret injection rather than source control.

### Primary model

`gemini-3.6-flash`

Use for:
- investigation planning;
- tool selection;
- contextual synthesis;
- clarification formulation;
- package narrative.

Start with `thinking_level = medium`.

Use lower reasoning effort for simple routing if latency/cost warrants it. Use higher effort only if evaluation shows meaningful gains.

Determinism belongs in code and schemas—not sampling tricks.

## 5. ADK Decision

Use Google ADK Python.

Agents are used only where ambiguity exists.

Do **not** turn deterministic functions into agents.

## 6. Deployment Shape

Hackathon MVP uses two Cloud Run services:

```text
ngabo-web
  Next.js
     |
     v
ngabo-core
  FastAPI + domain modules + surveillance + ADK
```

Logical modules inside `ngabo-core`:

```text
api/
application/
domain/
infrastructure/
agents/
surveillance/
evidence/
notifications/
```

This keeps deployment simple while preserving clean internal boundaries.

## 7. Event Architecture

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

Keep event payloads small; full entity state lives in Firestore.

## 8. Firestore Role

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

Future high-scale analytics can move to BigQuery or another analytical store.

## 9. Cloud Storage Role

Prefixes:

```text
raw-imports/
approved-guidance/
normalized-exports/
demo-artifacts/
```

Raw uploaded files are immutable and hashed.

## 10. Evidence Retrieval

v0.1 uses a curated, versioned evidence library with:

- source ID;
- title;
- publisher;
- official URL;
- date/version;
- tags;
- approved content/chunks.

Do **not** add a vector database unless the corpus actually requires one.

## 11. Notification Boundary

Define a port:

```python
class NotificationPort:
    async def send_incident_alert(...): ...
```

Adapters:
1. deterministic demo adapter;
2. optional real email/webhook adapter.

## 12. Surveillance Engine

Use ordinary code.

Modules:
- schema validation;
- AST normalization;
- resistance-vector construction;
- profile similarity;
- temporal concentration;
- ward concentration;
- baseline comparison;
- signal scoring.

The score is an **investigation-priority score**, not an outbreak probability.

## 13. Repository Layout

```text
ngabo/
├── apps/web/
├── services/core/
│   ├── ngabo/
│   │   ├── api/
│   │   ├── application/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   ├── agents/
│   │   ├── surveillance/
│   │   ├── evidence/
│   │   └── notifications/
│   └── tests/
├── data/
│   ├── synthetic/
│   ├── schemas/
│   └── guidance/
├── docs/
│   ├── architecture/
│   └── adr/
├── infra/
├── .github/workflows/
├── README.md
├── LICENSE
└── SECURITY.md
```

## 14. Architecture Rules

1. If it can be deterministic, make it deterministic.
2. Agents may request tool results; they may not rewrite source facts.
3. Every side effect needs an idempotency key.
4. Every meaningful claim is observed data, deterministic calculation, cited guidance, or labelled hypothesis.
5. Do not add infrastructure merely to make the architecture diagram look impressive.

## 15. Deferred Technology

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

## 16. References

- Hackathon rules: https://allthingsagentichackathon.devpost.com/rules
- Hackathon resources: https://allthingsagentichackathon.devpost.com/resources
- Gemini 3.6 Flash: https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash
- Google ADK: https://google.github.io/adk-docs/
- Cloud Run: https://cloud.google.com/run/docs
- Firestore: https://cloud.google.com/firestore/docs
- Pub/Sub: https://cloud.google.com/pubsub/docs
