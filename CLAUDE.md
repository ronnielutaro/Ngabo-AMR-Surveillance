# CLAUDE.md — Ngabo Implementation Contract

This file is the root implementation contract for Claude Code working on Ngabo.

**Project:** Ngabo — Autonomous AMR Surveillance & Incident Response  
**Competition:** All Things Agentic Hackathon 2026 — Taskmaster  
**Architecture:** Clean Architecture in a monorepo  
**Primary stack:** Next.js + TypeScript; Python + FastAPI; Google ADK; Gemini 3.6 Flash; Firestore; Cloud Storage; Pub/Sub; Cloud Run  
**Current release target:** `v0.1.0`  
**MVP deadline:** 2026-08-31, 5:00 PM Pacific Time

---

## 1. Read Before Editing Code

Before implementation or architecture changes, read in this order:

1. `ROADMAP.md`
2. `CONTRIBUTING.md`
3. `docs/PRD.md`
4. `docs/TECH_STACK.md`
5. `docs/CLEAN_ARCHITECTURE.md`
6. `docs/SYSTEM_DESIGN.md`
7. `docs/AGENT_ARCHITECTURE.md`
8. `docs/DATA_SAFETY_EVALUATION.md`
9. `docs/UI_UX_SPEC.md`
10. `docs/IMPLEMENTATION_PLAN.md`
11. `docs/adr/0001-hackathon-mvp-architecture.md`
12. `docs/adr/0002-release-governance.md`
13. `docs/adr/0003-clean-architecture-monorepo.md`

Also read:

- `AGENTS.md` for coding-agent execution rules;
- `CHANGELOG.md` before release work;
- product/evidence docs under `docs/product/` when present.

If documents conflict, use this precedence:

```text
Safety / data constraints
        ↓
CLAUDE.md invariants
        ↓
PRD
        ↓
Clean Architecture contract
        ↓
System Design / Agent Architecture
        ↓
UI/UX Spec
        ↓
Tech Stack
        ↓
ROADMAP release-stage constraints
        ↓
Implementation Plan
```

Git/release mechanics are governed by `CONTRIBUTING.md` plus the rules below.

Do not resolve material conflicts silently. Surface them and create an ADR when appropriate.

---

## 2. Product Definition

Ngabo is an **open-source, event-driven AMR surveillance and incident-response system**.

Do not make “prototype” part of the permanent product identity. Communicate maturity separately.

Example:

> **Product:** Ngabo — AMR Surveillance & Incident Response  
> **Current status:** `v0.1.0` hackathon MVP in development.

The v0.1 proof is:

```text
synthetic WHONET-style input
        ↓
deterministic validation + normalization
        ↓
deterministic surveillance signal
        ↓
Pub/Sub event
        ↓
ADK agent investigation
        ↓
evidence + clarification when needed
        ↓
structured incident package
        ↓
human approval
        ↓
notification / acknowledgement
        ↓
audit trail
```

Ngabo is **not a chatbot product**. The web application is an incident-response console that makes the autonomous workflow visible and auditable.

---

## 3. Architectural Style — Non-Negotiable

Ngabo uses **Clean Architecture inside a monorepo**.

This is a frozen architecture decision recorded in ADR 0003.

### Dependency rule

```text
Frameworks / Infrastructure
          ↓
Interfaces / Adapters
          ↓
Application / Use Cases / Ports
          ↓
Domain / Entities / Value Objects / Domain Services
```

**Source-code dependencies point inward. Inner layers must not depend on outer framework/vendor implementations.**

### Backend package target

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

### Layer rules

**Domain** contains pure AMR/surveillance concepts and policy. It must not import FastAPI, Google Cloud SDKs, ADK, Gemini, notification providers, or transport models.

**Application** contains use cases/workflows/ports and may depend on domain. It must not instantiate Firestore, Pub/Sub, GCS, Gemini, ADK, or HTTP framework clients.

**Interfaces** adapt HTTP/events to application commands/use cases. Routes and event handlers must not own scientific/domain logic.

**Infrastructure** implements ports for Firestore, GCS, Pub/Sub, Gemini, ADK, evidence, notifications, telemetry, etc.

**Bootstrap** is the composition root where concrete implementations are wired.

Prefer explicit constructor dependency injection. Do not hide dependencies in global service locators.

### Architecture smells that must be rejected

```text
domain -> FastAPI
domain -> Firestore
application -> google.cloud.firestore
application -> Gemini SDK
FastAPI route -> signal-scoring logic
Pub/Sub handler -> AMR business rules
ADK tool wrapper -> raw database + ad hoc business logic
React component -> Firestore/PubSub/Gemini
```

When a vendor capability is needed from an inner layer, define a port inward and implement it outward.

---

## 4. Monorepo — Non-Negotiable

Ngabo uses **one Git repository** for the product.

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
├── README.md
├── LICENSE
└── SECURITY.md
```

**Monorepo does not mean monolith.**

Primary runtime deployables remain:

```text
Cloud Run: ngabo-web
Cloud Run: ngabo-core
```

Do not split frontend/backend into separate repositories, or create new runtime services that change system boundaries, without an ADR.

---

## 5. Non-Negotiable Scientific / Safety Invariants

### A. Scientific calculations are deterministic

The LLM must not own:

- CSV parsing;
- schema validation;
- organism/antibiotic normalization;
- date-window calculations;
- resistance-profile similarity;
- baseline calculations;
- signal scoring;
- state-transition validation;
- idempotency decisions.

If a calculation can be reproduced in ordinary code, implement it in ordinary code.

### B. The agent receives a signal; it does not invent one

Never implement:

```text
CSV -> LLM -> “this is an outbreak”
```

Required boundary:

```text
CSV -> deterministic detector -> investigation candidate -> agent
```

### C. Source facts are immutable

The agent may never rewrite canonical isolate/laboratory facts. Human clarification is persisted separately with provenance.

### D. Firestore is operational source of truth

Model conversation state is not the canonical workflow state.

### E. Side effects are idempotent

Pub/Sub is at-least-once delivery. No duplicate incidents, notifications, or acknowledgements.

### F. Human review is a real gate

No consequential escalation is sent before professional review approval.

### G. Evidence is traceable

External guidance claims use source IDs/URLs returned by approved evidence tools. Never fabricate citations.

### H. No autonomous prescribing

Never implement autonomous treatment/antibiotic recommendations.

### I. Synthetic public v0.1 data only

Do not commit real patient records to fixtures, screenshots, logs, or Git history.

### J. No hidden chain-of-thought UI

Show observable workflow actions, tool results, concise source-backed rationale, and state—not private model reasoning tokens.

---

## 6. Agent Architecture Under Clean Architecture

The runtime agent operates through narrowly scoped typed tools such as:

- `get_incident_context()`
- `compare_resistance_profiles()`
- `get_baseline_summary()`
- `get_missing_fields()`
- `search_approved_guidance()`
- `request_clarification()`
- `prepare_incident_package()`

Google ADK and Gemini are **outer infrastructure**.

Recommended runtime boundary:

```text
ADK/Gemini adapter
        ↓
application agent contract / use case
        ↓
domain calculation or inward-defined port
        ↓
infrastructure adapter when required
```

Do not create an unrestricted runtime database tool or shell tool.

An ADK wrapper must not become an alternate business layer containing raw Firestore access plus scientific calculations plus side effects.

---

## 7. Runtime Agent Truth Hierarchy

Generated outputs respect:

1. canonical source data;
2. deterministic tool output;
3. retrieved approved guidance;
4. explicitly labelled hypothesis;
5. unknown / insufficient evidence.

Never invent missing facts.

---

## 8. Incident Package Contract

Final output is schema validated and keeps separate categories:

```json
{
  "title": "...",
  "priority": "HIGH",
  "observed_evidence": [],
  "derived_findings": [],
  "hypotheses": [],
  "uncertainties": [],
  "missing_information": [],
  "guidance": [],
  "investigation_checklist": [],
  "draft_escalation": "...",
  "limitations": []
}
```

Do not collapse all categories into one prose blob.

---

## 9. UI Contract

Read `docs/UI_UX_SPEC.md` before frontend work.

Core principle:

> **Incident-response console, not ChatGPT for AMR.**

Required operational UI:

```text
Dashboard
  ↓
Import / validation
  ↓
Surveillance signal
  ↓
Incident detail
  ├── Why it was flagged
  ├── Resistance profile comparison
  ├── Agent/tool timeline
  ├── Clarification
  ├── Evidence-backed package
  ├── Human review
  └── Response tracking
```

The only chat-like interaction should be targeted clarification.

### Frontend Clean Architecture

Target philosophy:

```text
presentation -> application -> domain
infrastructure -> API/SSE adapters
app/ -> Next.js route/composition wiring
```

UI components do not call Firestore, Pub/Sub, Gemini, or other backend/cloud SDKs directly.

Do not over-engineer trivial presentational components merely for architectural ceremony.

---

## 10. Tech Stack — Do Not Substitute Without ADR

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- pnpm

### Backend

- Python 3.11+
- FastAPI
- Pydantic v2
- uv

### AI

- Google ADK (Python)
- Gemini API
- `gemini-3.6-flash`

### Data / infrastructure

- Firestore
- Cloud Storage
- Pub/Sub
- Cloud Run
- Secret Manager / Cloud Run secrets
- Cloud Logging

### Testing

- pytest
- ADK evaluation tooling
- Playwright

Do not add without a documented requirement/ADR:

- LangGraph;
- Kubernetes/GKE;
- Redis;
- Kafka;
- Cloud SQL;
- BigQuery;
- vector database;
- second LLM provider;
- genomics toolchain.

---

## 11. Google ADK / Agent Scaffolding

Official Google ADK/Agents CLI tooling may assist scaffolding, evaluation, deployment, and observability if available.

Do not let generated scaffolds redefine Ngabo's monorepo or Clean Architecture boundaries.

Generated templates are implementation aids, not product architecture.

---

## 12. Git & Release Governance — Non-Negotiable

Ngabo uses:

- Semantic Versioning 2.0.0;
- Conventional Commits 1.0.0;
- Gitflow-style branching using `main` + `develop`;
- `CHANGELOG.md`;
- release tags `vX.Y.Z`.

### Branches

```text
main                    released / release-ready history
develop                 next-release integration
feature/<short-name>    feature work from develop
release/vX.Y.Z          release hardening from develop
hotfix/vX.Y.Z           urgent fixes from main
```

Feature work must not go directly to `main`.

### Conventional Commits

```text
<type>[optional scope]: <description>
```

Recommended types:

```text
feat fix docs test refactor perf build ci chore revert
```

Recommended scopes:

```text
web core surveillance agent evidence events data eval infra docs release architecture
```

Examples:

```text
feat(surveillance): add phenotype similarity detector
fix(events): prevent duplicate incident creation
docs(architecture): define clean architecture boundaries
```

### SemVer during 0.x

- fix → normally PATCH;
- backward-compatible feature/release milestone → normally MINOR;
- breaking change → explicitly marked and normally MINOR while pre-1.0;
- never auto-promote to `1.0.0`.

`1.0.0` is governed by `ROADMAP.md` exit criteria.

Update `CHANGELOG.md` for meaningful user/operator-visible behavior.

---

## 13. Implementation Order

Follow `docs/IMPLEMENTATION_PLAN.md`.

High-level milestones:

1. monorepo/workspace scaffold with Clean Architecture package boundaries;
2. domain entities + state machine;
3. synthetic dataset + canonical schema;
4. deterministic parser/normalizer;
5. deterministic surveillance engine;
6. application ports + Firestore/PubSub/GCS adapters;
7. ADK/Gemini infrastructure adapter + agent tools;
8. investigation workflow;
9. clarification/resume;
10. incident package validation;
11. human review;
12. notification/acknowledgement;
13. Next.js incident console;
14. Cloud Run deployment;
15. evaluation and demo hardening.

Do not start genomics before the core v0.1 flow is green.

---

## 14. Definition of Done Per Milestone

Before marking a milestone complete:

- changed deterministic behavior has tests;
- schemas/contracts are explicit;
- errors are not silently swallowed;
- Clean Architecture dependency rule is preserved;
- monorepo/deployable boundaries are preserved;
- domain/application code remains independent of outer vendor SDKs;
- docs/ADR updated if public contracts changed;
- lint/type/tests pass for changed surface;
- branch follows Gitflow;
- commits follow Conventional Commits;
- changelog/release impact considered;
- code is coherent, not merely visually working.

---

## 15. Test Requirements by Layer

### Domain

Pure unit tests, no cloud/network/model/web framework.

### Application

Use cases/workflows with fakes/in-memory port implementations.

### Infrastructure

Adapter contract/integration tests.

### Interfaces

HTTP/event translation tests.

### Agent safety

Cover:

- missing field -> clarification;
- no evidence -> no fabricated source;
- prompt injection in CSV -> data, not instructions;
- hallucinated isolate ID -> rejected;
- autonomous prescribing language -> rejected;
- autonomous outbreak confirmation -> rejected;
- tool failure -> visible bounded failure.

### End-to-end

```text
upload -> detect -> investigate -> clarify -> package -> review -> notify -> acknowledge
```

A passing E2E flow does not replace inner-layer tests.

---

## 16. Failure Handling

A failed step leaves persisted, inspectable state.

Never catch an exception and proceed as if successful.

Examples:

- malformed import -> validation failure;
- Gemini timeout -> retryable investigation failure;
- malformed package -> schema rejection;
- notification failure -> retryable notification state;
- duplicate event -> no duplicate side effect.

Inner layers should use domain/application error types; outer interfaces translate them to transport-specific errors.

---

## 17. Scope Control

For `v0.1.0`, ask:

> “Does this strengthen: suspicious AMR signal -> evidence-backed, human-reviewable incident package -> coordinated action?”

If no, defer it.

Explicitly deferred until core completion:

- AMRFinderPlus;
- pathogen genomics;
- real hospital/LIMS integration;
- nationwide analytics;
- facility tenancy/RBAC platform;
- vector RAG;
- mobile app;
- hardware.

---

## 18. Architecture Changes

Material deviations from the frozen architecture require an ADR **before implementation**.

Examples requiring ADR:

- splitting the monorepo;
- adding a new independently deployed service;
- replacing Clean Architecture with another architectural style;
- moving domain logic into framework-specific code;
- allowing domain/application to depend directly on vendor SDKs;
- changing core technology decisions.

Small refactors that preserve contracts and dependency direction do not require an ADR.

---

## 19. Working Style for Claude Code

- inspect before editing;
- make focused changes;
- do not rewrite unrelated files;
- preserve authored documentation unless a contract change requires an update;
- prefer typed interfaces/ports over loose dictionaries at boundaries;
- prefer boring testable code over clever abstractions;
- avoid premature microservices;
- avoid premature generic frameworks;
- do not create abstractions without a real dependency/use-case boundary;
- report contradictions instead of guessing;
- obey Clean Architecture, monorepo, Gitflow, SemVer, Conventional Commits, and changelog rules;
- do not silently version-bump or create release tags.

When asked to implement a milestone, stay inside that milestone unless a prerequisite must be fixed.

---

## 20. Final Product Standard

A judge should be able to see:

> **new AMR data arrived -> deterministic Ngabo logic detected a signal -> the agent investigated autonomously through bounded tools -> asked for one necessary clarification -> assembled evidence -> a professional approved the package -> Ngabo routed the action -> the audit trail recorded everything.**

The code should also make it obvious that the AMR domain/application core is not coupled to FastAPI, Firestore, Pub/Sub, ADK, Gemini, or the Next.js UI.

If we cannot demonstrate both the product behavior and the architectural discipline truthfully, the MVP is not complete.
