# AGENTS.md — Ngabo Coding-Agent Rules

This file applies to AI coding agents working anywhere in this repository.

Read `CLAUDE.md` first. `CLAUDE.md` contains the project-wide implementation contract; this file summarizes execution behavior and local invariants for coding agents.

---

## Mission

Build Ngabo as a **safe, event-driven AMR incident-response system** for the hackathon MVP.

Do not optimize for feature count. Optimize for:

- working autonomy;
- deterministic scientific logic;
- explicit state;
- traceability;
- bounded clinical/public-health claims;
- reproducibility;
- a clear 4-minute demo.

---

## Required Read Order

Before major implementation:

1. `CLAUDE.md`
2. `docs/PRD.md`
3. `docs/SYSTEM_DESIGN.md`
4. `docs/AGENT_ARCHITECTURE.md`
5. `docs/DATA_SAFETY_EVALUATION.md`
6. `docs/UI_UX_SPEC.md`
7. `docs/IMPLEMENTATION_PLAN.md`

---

## Runtime Boundary

### Deterministic layer owns

- ingest;
- parsing;
- schema validation;
- normalization;
- AST calculations;
- resistance-profile similarity;
- temporal/location windows;
- baseline calculations;
- signal scoring;
- state transitions;
- idempotency.

### Agentic layer owns

- investigation planning;
- choosing approved tools;
- gathering contextual evidence;
- identifying missing information;
- asking targeted clarification;
- evidence synthesis;
- hypothesis generation with labels;
- incident-package drafting.

### Human owns

- clinically/public-health consequential approval;
- outbreak confirmation through appropriate professional processes;
- patient treatment decisions.

Never blur these boundaries.

---

## Agent Runtime Restrictions

The Ngabo runtime agent must not:

- execute arbitrary shell commands;
- issue unrestricted database queries;
- browse arbitrary URLs as approved evidence;
- mutate raw source data;
- send alerts before review approval;
- prescribe treatment;
- claim an outbreak is confirmed;
- fabricate citations.

Keep runtime tools narrow, typed, and auditable.

---

## UI Restrictions

Do not build the core experience as a chat window.

Implement the operational hierarchy from `docs/UI_UX_SPEC.md`:

- dashboard;
- import/validation;
- incident queue;
- incident detail;
- deterministic signal explanation;
- resistance-profile table;
- agent/tool timeline;
- targeted clarification;
- structured package;
- human review;
- response tracking.

Do not expose hidden model chain-of-thought.

---

## Data Rules

- synthetic demo data only;
- every fixture declares that it is synthetic;
- never commit real patient data;
- unknown/missing values remain unknown/missing;
- do not generate plausible-looking values to make a demo prettier;
- keep raw import and normalized data logically distinct.

---

## Evidence Rules

- evidence corpus is curated for v0.1;
- each source has source ID, title, publisher, URL, and version/date where possible;
- generated package may cite only retrieved source IDs;
- “no source found” is an acceptable result;
- fabricated guidance is not.

---

## State / Event Rules

- Firestore is canonical operational state;
- incident transitions are explicit;
- event handlers are retry-safe;
- duplicate Pub/Sub events do not create duplicate actions;
- persisted audit events are append-only;
- failed workflow steps produce visible failure state.

---

## Coding Standards

### Python

- Python 3.11+
- FastAPI
- Pydantic v2
- type annotations on public interfaces
- pytest
- keep domain logic independent of HTTP and cloud SDKs

### TypeScript

- strict TypeScript
- typed API models
- shadcn/ui primitives where appropriate
- avoid client-side reinterpretation of medical/scientific strings
- Playwright for critical user journeys

### General

- small modules;
- explicit dependencies;
- no magic global state;
- no swallowed exceptions;
- structured logs;
- configuration through environment/settings objects;
- no secrets in code or docs.

---

## Before Completing Any Task

Run the checks appropriate to the changed surface.

Expected eventual commands may include:

```bash
# Python
uv run pytest
uv run ruff check .
uv run mypy .

# Web
pnpm lint
pnpm typecheck
pnpm test
pnpm exec playwright test
```

If the repository uses different finalized commands after scaffolding, update README/CLAUDE.md rather than silently diverging.

---

## Commit / Change Discipline

For each milestone:

- keep changes focused;
- avoid mass formatting unrelated files;
- do not rename established product concepts casually;
- update docs when public contracts change;
- create ADR for material architecture changes;
- do not introduce stretch features before core acceptance criteria are green.

---

## Product Vocabulary

Preferred:

- surveillance signal;
- investigation candidate;
- possible cluster;
- incident;
- evidence-backed package;
- human review;
- approved escalation;
- prototype signal score.

Avoid autonomous factual use of:

- confirmed outbreak;
- diagnosis;
- treatment recommendation;
- clinical confidence score.

---

## Primary Demo Scenario

The canonical demo scenario is a synthetic neonatal-unit *Klebsiella pneumoniae* resistance-pattern cluster with one intentionally missing metadata field.

The system must demonstrate:

```text
import
  ↓
validation
  ↓
signal
  ↓
autonomous investigation
  ↓
clarification
  ↓
resume
  ↓
incident package
  ↓
human approval
  ↓
notification
  ↓
acknowledgement
```

Do not replace the real path with canned UI state.

---

## Stop Conditions

Stop and surface the issue instead of guessing when:

- docs contradict each other materially;
- a requested feature violates the safety boundary;
- a dependency requires replacing a frozen architecture decision;
- the available data cannot support a claimed calculation;
- a model output cannot be validated;
- a third-party integration would require credentials/permissions not available.

---

## Scope Freeze

Until the end-to-end core works and passes acceptance tests, do not add:

- pathogen genomics;
- AMRFinderPlus;
- vector database;
- BigQuery;
- GKE;
- Redis/Kafka;
- LangGraph;
- mobile app;
- real patient data;
- production hospital connector.

---

## Success Criterion

The coding agent has succeeded when the repository truthfully demonstrates the PRD's Definition of Done, not when it has generated the largest amount of code.
