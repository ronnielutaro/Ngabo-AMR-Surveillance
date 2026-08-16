# AGENTS.md — Ngabo Coding-Agent Rules

This file applies to AI coding agents working anywhere in this repository.

Read `CLAUDE.md` first. `CLAUDE.md` is the root implementation contract; this file summarizes execution behavior, architecture, Git/release discipline, and stop conditions.

---

## 1. Mission

Build Ngabo as a **safe, event-driven AMR surveillance and incident-response system**.

The current release target is `0.1.x`, but agents must preserve the longer trajectory in `ROADMAP.md`.

Optimize for:

- working autonomy;
- deterministic scientific logic;
- explicit state;
- traceability;
- bounded clinical/public-health claims;
- reproducibility;
- **Clean Architecture**;
- **monorepo discipline**;
- maintainable release history;
- a clear 4-minute v0.1 demo.

---

## 2. Required Read Order

Before major implementation:

1. `CLAUDE.md`
2. `ROADMAP.md`
3. `CONTRIBUTING.md`
4. `docs/PRD.md`
5. `docs/TECH_STACK.md`
6. `docs/CLEAN_ARCHITECTURE.md`
7. `docs/SYSTEM_DESIGN.md`
8. `docs/AGENT_ARCHITECTURE.md`
9. `docs/DATA_SAFETY_EVALUATION.md`
10. `docs/UI_UX_SPEC.md`
11. `docs/IMPLEMENTATION_PLAN.md`
12. relevant files under `docs/adr/`

Consult `CHANGELOG.md` before release-oriented work.

---

## 3. Product Identity vs Release Maturity

Do not describe Ngabo itself as merely “the prototype” in permanent product identity copy.

Preferred:

> **Ngabo is an open-source AMR surveillance and incident-response system.**

Then state maturity separately:

> `v0.1.0` hackathon MVP in development.

Use `ROADMAP.md` as the source of truth for maturity stages.

---

## 4. Clean Architecture — Mandatory

Ngabo uses **Clean Architecture**.

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

**Dependencies point inward. Inner layers must not depend on outer framework/vendor implementations.**

### Backend boundaries

Target package shape:

```text
services/core/ngabo/
├── domain/
├── application/
├── interfaces/
├── infrastructure/
└── bootstrap/
```

#### `domain/`

Owns:

- entities;
- value objects;
- domain events;
- incident state policy;
- deterministic AMR/surveillance rules;
- domain exceptions.

Must not import FastAPI, Firestore, Pub/Sub, GCS, ADK, Gemini, notification SDKs, or other outer frameworks.

#### `application/`

Owns:

- use cases;
- commands/queries;
- workflows;
- ports/contracts;
- application DTOs;
- agent-facing contracts.

May depend on `domain`.

Must not instantiate Firestore, Pub/Sub, GCS, Gemini, ADK, or HTTP framework clients directly.

#### `interfaces/`

Owns:

- FastAPI request/response adaptation;
- Pub/Sub/event-handler adaptation.

Routes/handlers translate external input into application commands. They must not contain scientific/business logic.

#### `infrastructure/`

Owns concrete adapters for:

- Firestore;
- GCS;
- Pub/Sub;
- Google ADK;
- Gemini;
- evidence retrieval;
- notification providers;
- logging/telemetry.

Infrastructure implements ports defined inward.

#### `bootstrap/`

Owns composition/dependency wiring.

Prefer explicit constructor dependency injection. Avoid hidden service-locator/global-singleton dependencies.

### Architecture smell checks

Stop and fix the design if you find:

```text
domain -> FastAPI
application -> google.cloud.firestore
application -> Gemini SDK
FastAPI route -> AMR signal calculation
ADK wrapper -> raw Firestore + business logic
React component -> Firestore / PubSub / Gemini
```

See `docs/CLEAN_ARCHITECTURE.md` and ADR 0003.

---

## 5. Monorepo — Mandatory

Ngabo is implemented in **one repository**.

```text
ngabo/
├── apps/web/               # Next.js deployable
├── services/core/          # FastAPI/ADK deployable
├── data/
├── docs/
├── infra/
└── .github/
```

**Monorepo does not mean monolith.** `ngabo-web` and `ngabo-core` are independently deployable Cloud Run services.

Rules:

- do not split frontend/backend into separate repos without an ADR;
- do not create a new deployable service casually;
- Python dependencies stay scoped to `services/core`;
- JS/TS workspace uses pnpm;
- cross-package imports must respect Clean Architecture;
- shared contracts need an explicit owner and dependency direction.

---

## 6. Runtime Responsibility Boundary

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
- idempotency policy.

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

## 7. Runtime Agent Restrictions

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

ADK/Gemini are infrastructure concerns. An ADK tool should normally call an application use case/query rather than directly implementing domain calculations or database side effects.

---

## 8. UI Rules

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

Frontend follows the Clean Architecture dependency philosophy:

```text
presentation -> application -> domain
infrastructure implements outer API/SSE access
```

UI components must not call Firestore, Pub/Sub, Gemini, or backend cloud SDKs directly.

---

## 9. Data Rules

- synthetic demo data only for public v0.1;
- every fixture declares that it is synthetic;
- never commit real patient data;
- unknown/missing values remain unknown/missing;
- do not generate plausible-looking values to make a demo prettier;
- keep raw import and normalized data logically distinct.

Future real-world datasets must follow `ROADMAP.md` and appropriate governance/authorization.

---

## 10. Evidence Rules

- evidence corpus is curated for v0.1;
- every source has source ID, title, publisher, URL, and date/version where possible;
- generated package may cite only retrieved source IDs;
- “no source found” is an acceptable result;
- fabricated guidance is not.

---

## 11. State / Event Rules

- Firestore is canonical operational state;
- incident transitions are explicit;
- event handlers are retry-safe;
- duplicate Pub/Sub events do not create duplicate actions;
- persisted audit events are append-only;
- failed workflow steps produce visible failure state;
- event handlers are interface adapters, not business-logic containers.

---

## 12. Coding Standards

### Python

- Python 3.11+
- FastAPI
- Pydantic v2
- type annotations on public interfaces
- pytest
- domain/application code independent of HTTP/cloud/AI SDKs
- ports defined inward, adapters implemented outward

### TypeScript

- strict TypeScript
- typed API models
- shadcn/ui primitives where appropriate
- avoid client-side reinterpretation of medical/scientific strings
- Playwright for critical user journeys
- behavioral client logic separated from presentation when meaningful

### General

- small modules;
- explicit dependencies;
- constructor injection where practical;
- no magic global state;
- no swallowed exceptions;
- structured logs;
- configuration through settings/environment objects;
- no secrets in code/docs;
- boring/testable abstractions preferred over clever frameworks.

---

## 13. Testing by Architecture Layer

### Domain

Pure unit tests. No network, cloud, web framework, model, or ADK dependency.

### Application

Use cases/workflows tested with fakes or in-memory port implementations.

### Infrastructure

Adapter integration/contract tests.

### Interfaces

HTTP/event translation and contract tests.

### End-to-end

```text
upload
 -> detect
 -> investigate
 -> clarify
 -> package
 -> review
 -> notify
 -> acknowledge
```

A passing end-to-end test does not replace domain/application tests.

---

## 14. Gitflow — Mandatory Branch Discipline

Long-lived branches:

```text
main       released / release-ready history
develop    integration for the next release
```

Feature work:

```text
feature/<short-name>
```

Create from `develop`, merge through PR into `develop`.

Release branches:

```text
release/vX.Y.Z
```

Create from `develop`; use for final fixes, version metadata, changelog, docs, evaluation/hardening. Do not add new product scope.

Completed release:

```text
release/vX.Y.Z -> main -> tag vX.Y.Z
                         ↓
                 reconcile to develop
```

Urgent release fixes:

```text
hotfix/vX.Y.Z
```

Create from `main`; merge to both `main` and `develop`.

Do not commit feature work directly to `main`.

---

## 15. Semantic Versioning — Mandatory

Ngabo uses Semantic Versioning 2.0.0:

```text
MAJOR.MINOR.PATCH
```

Tags:

```text
vMAJOR.MINOR.PATCH
```

During `0.y.z`:

- bug fix → normally PATCH;
- backward-compatible feature/release milestone → normally MINOR;
- breaking change → explicitly marked and normally MINOR while pre-1.0;
- never automatically create `1.0.0` because a breaking commit exists.

`1.0.0` is the deliberate production-readiness milestone defined in `ROADMAP.md`.

---

## 16. Conventional Commits — Mandatory

All commits use:

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
test(eval): add prompt injection scenario
docs(architecture): define clean architecture boundaries
```

Breaking change:

```text
feat(events)!: revise surveillance signal schema
```

Do not leave vague merge history such as `update stuff`, `wip`, or `changes`.

---

## 17. PR / Changelog Discipline

Substantive work should merge through PRs.

A PR should state:

- scope;
- reason;
- tests run;
- API/schema/event impact;
- safety/human-review impact;
- architecture/dependency impact;
- docs/changelog impact;
- ADR requirement if applicable.

Do not merge knowingly failing required tests.

Maintain `CHANGELOG.md`; summarize meaningful user/operator-visible changes under `Unreleased` during development.

---

## 18. Before Completing Any Task

Run checks appropriate to the changed surface. Expected eventual commands include:

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

Also verify:

- branch follows Gitflow;
- commit follows Conventional Commits;
- SemVer/release impact considered;
- changelog/docs updated when required;
- Clean Architecture dependency rule preserved;
- monorepo/deployable boundaries preserved.

---

## 19. Product Vocabulary

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

## 20. Primary Demo Scenario

The canonical v0.1 demo is a synthetic neonatal-unit *Klebsiella pneumoniae* resistance-pattern cluster with one intentionally missing metadata field.

It must demonstrate:

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

Do not replace the real path with canned final-state UI.

---

## 21. Stop Conditions

Stop and surface the issue instead of guessing when:

- docs materially contradict each other;
- a requested feature violates the safety boundary;
- a dependency requires replacing a frozen architecture decision;
- domain/application code would need to depend directly on an outer vendor SDK;
- a change would split the monorepo or create a new deployable without an ADR;
- available data cannot support a claimed calculation;
- model output cannot be validated;
- third-party integration requires unavailable credentials/permissions;
- release/version action conflicts with `ROADMAP.md` or SemVer;
- branch/merge action violates Gitflow without explicit authorization.

---

## 22. Scope Freeze

Until the end-to-end v0.1 core works and passes acceptance tests, do not add:

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

## 23. Success Criterion

The coding agent succeeds when the repository truthfully demonstrates the PRD's Definition of Done **while preserving Clean Architecture, monorepo boundaries, safety, and coherent versioned release history**—not when it generates the largest amount of code.
