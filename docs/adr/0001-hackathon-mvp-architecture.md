# ADR 0001 — Hackathon MVP Architecture Baseline

**Status:** Accepted  
**Date:** 2026-08-16

## Context

Ngabo must demonstrate a credible, event-driven AMR surveillance-to-action workflow during a short hackathon implementation window.

The project requires:

- deterministic microbiology/surveillance processing;
- agentic investigation and evidence synthesis;
- persistent asynchronous workflow state;
- human approval at consequential decision boundaries;
- a polished web console;
- Google agent/model/cloud technology required by the competition;
- a reproducible public implementation.

The architecture must be technically disciplined without introducing infrastructure that cannot be completed and demonstrated reliably before the deadline.

## Decision

Use:

### Frontend

- Next.js + TypeScript
- Tailwind CSS + shadcn/ui

### Backend / scientific core

- Python 3.11+
- FastAPI
- Pydantic v2
- pandas / NumPy / SciPy

### Agentic layer

- Google ADK (Python)
- Gemini API
- `gemini-3.6-flash`

### Google Cloud

- two Cloud Run deployables: `ngabo-web` and `ngabo-core`;
- Firestore for operational state;
- Cloud Storage for raw imports/evidence artifacts;
- Pub/Sub for event-driven workflow;
- Cloud Logging;
- secret injection / Secret Manager where needed.

### Architecture style

Use a modular monorepo with **logical separation before physical microservice separation**.

The core backend keeps deterministic surveillance, domain logic, agent workflow, and infrastructure adapters separate inside one deployable for the MVP.

### Evidence

Use a small curated evidence corpus for v0.1 rather than prematurely introducing vector infrastructure.

### UI

Build an incident-response console rather than a chat-first product.

## Key Invariants

- LLM does not own scientific calculations.
- surveillance detector creates investigation candidates before agent involvement.
- source laboratory facts are immutable.
- Firestore is workflow source of truth.
- Pub/Sub side effects are idempotent.
- incident package separates facts, derived findings, hypotheses, uncertainty, and guidance.
- human approval is required before consequential external escalation.
- public prototype uses synthetic data.

## Alternatives Considered

### All-TypeScript backend

Rejected for MVP because Python provides a stronger unified ecosystem for scientific/statistical processing, ADK, evaluation, and future bioinformatics.

### LangGraph in addition to ADK

Rejected because ADK already satisfies the project/hackathon agent framework needs; adding a second orchestrator increases complexity without a clear v0.1 benefit.

### Kubernetes / GKE

Rejected as unnecessary operational overhead for hackathon scale.

### Cloud SQL

Deferred. Firestore better matches current operational state needs and reduces setup burden.

### BigQuery

Deferred until surveillance scale requires an analytical warehouse.

### Vector database / managed RAG

Deferred because the v0.1 approved guidance corpus is deliberately small and curated.

### Genomics / AMRFinderPlus

Deferred until the phenotype-based core workflow is complete and stable.

## Consequences

### Positive

- small number of deployables;
- strong deterministic/agent separation;
- clear event-driven Taskmaster story;
- easy Google Cloud proof in demo;
- Python-compatible future genomics path;
- frontend can be polished independently.

### Negative / Trade-offs

- Firestore is not intended to become the final large-scale analytical warehouse;
- evidence retrieval is intentionally limited in v0.1;
- full hospital identity/RBAC is deferred;
- deployment is logically modular but not fully microservice-isolated.

## Change Policy

Material substitutions to this architecture require a new ADR that explains:

- the implementation problem;
- alternatives considered;
- why this ADR no longer serves the MVP;
- migration/testing impact;
- deadline risk.
