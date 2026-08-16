# ADR 0003 — Adopt Clean Architecture in a Monorepo

**Status:** Accepted  
**Date:** 2026-08-16  
**Applies from:** `v0.1.0`

## Context

Ngabo is intended to evolve through hackathon, technical-prototype, research, pilot, validation, and production-oriented release stages. The codebase will combine deterministic AMR surveillance logic, event-driven workflows, agentic AI, cloud infrastructure, and a web incident-response console.

Without explicit architectural boundaries, vendor/framework details such as FastAPI, Firestore, Pub/Sub, Google ADK, Gemini, and Next.js could leak into business/scientific policy and make later testing, validation, replacement, and research evolution unnecessarily difficult.

At the same time, splitting the project into many repositories or deployables during the hackathon would add coordination and release overhead without improving the core product.

## Decision

Ngabo will use **Clean Architecture** inside a **single monorepo**.

The dependency rule is:

```text
Frameworks / infrastructure
          ↓
Interfaces / adapters
          ↓
Application / use cases / ports
          ↓
Domain / entities / value objects / domain services
```

Dependencies point inward. Inner layers must not depend on outer framework/vendor implementations.

The repository contains both primary deployables:

```text
apps/web        -> Next.js incident-response console
services/core   -> FastAPI + deterministic core + ADK integration
```

These remain independently deployable to Cloud Run even though they share one Git repository.

## Backend Consequences

- domain logic is plain Python and framework-independent;
- deterministic surveillance logic remains testable without cloud/model access;
- application use cases depend on ports/interfaces rather than vendor SDKs;
- Firestore, Pub/Sub, GCS, Gemini, ADK, and notification providers live in infrastructure/adapters;
- FastAPI and Pub/Sub handlers translate external inputs to application commands rather than owning business logic;
- concrete adapters are wired at an outer composition root.

## Frontend Consequences

The Next.js app follows the same dependency philosophy without forcing unnecessary ceremony:

- presentation/UI renders explicit application/domain state;
- application logic is separated from React rendering where it has real behavior;
- API/SSE clients live in infrastructure;
- UI components do not call Firestore, Pub/Sub, Gemini, or backend cloud SDKs directly;
- Next.js routes/composition remain outer framework concerns.

## Monorepo Consequences

The monorepo owns:

- web application;
- backend service;
- synthetic datasets and schemas;
- approved guidance fixtures;
- infrastructure/deployment configuration;
- tests/evaluation assets;
- architecture/product/release documentation.

Splitting frontend/backend into separate repositories requires a future ADR.

## Alternatives Considered

### Framework-centric architecture

Rejected because it would encourage domain/application policy to depend directly on FastAPI, Firestore, ADK, or other technical choices.

### Microservices-first architecture

Rejected for v0.1 because operational boundaries do not yet justify the extra deployment and coordination burden.

### Multiple repositories

Rejected because Ngabo currently benefits from atomic cross-stack changes, shared release governance, unified documentation, and one reproducible hackathon repository.

### Ad hoc folder organization without a dependency rule

Rejected because folder names alone do not prevent architecture erosion, especially when coding agents implement rapidly.

## Enforcement

`docs/CLEAN_ARCHITECTURE.md`, `CLAUDE.md`, and `AGENTS.md` are implementation contracts.

Material deviations require another ADR before implementation.
