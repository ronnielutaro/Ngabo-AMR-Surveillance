# AGENTS.md — Ngabo Coding-Agent Rules

This file applies to AI coding agents working anywhere in this repository.

Read `CLAUDE.md` first. `CLAUDE.md` is the root implementation contract; this file summarizes execution behavior, architecture, hackathon alignment, Git/release discipline, and stop conditions.

---

## 1. Mission

Build Ngabo as a **safe, event-driven AMR surveillance and incident-response system**.

The current release target is `0.1.x`, but agents must preserve the longer trajectory in `ROADMAP.md`.

Optimize for:

- working asynchronous autonomy;
- deterministic scientific logic;
- explicit persistent state;
- resumable/recoverable agent execution;
- traceability and observability;
- bounded clinical/public-health claims;
- reproducibility;
- **Clean Architecture**;
- **monorepo discipline**;
- hackathon scoring/technology compliance;
- maintainable release history;
- a clear <=4-minute v0.1 demo with real proof of action.

---

## 2. Required Read Order

Before major implementation:

1. `CLAUDE.md`
2. `ROADMAP.md`
3. `CONTRIBUTING.md`
4. `docs/PRD.md`
5. `docs/TECH_STACK.md`
6. `docs/CLEAN_ARCHITECTURE.md`
7. `docs/HACKATHON_ALIGNMENT.md`
8. `docs/ADK_RUNTIME.md`
9. `docs/SYSTEM_DESIGN.md`
10. `docs/AGENT_ARCHITECTURE.md`
11. `docs/DATA_SAFETY_EVALUATION.md`
12. `docs/UI_UX_SPEC.md`
13. `docs/UI_UX_HACKATHON_ADDENDUM.md`
14. `docs/IMPLEMENTATION_PLAN.md`
15. relevant files under `docs/adr/`

Consult `CHANGELOG.md` before release-oriented work.

If official hackathon rules change, update the repository docs before implementing against stale assumptions.

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

Must not import FastAPI, Firestore, Pub/Sub, GCS, ADK, Gemini, Gemma-family models, notification SDKs, or other outer frameworks.

#### `application/`

Owns:

- use cases;
- commands/queries;
- workflows;
- ports/contracts;
- application DTOs;
- agent-facing contracts;
- review/notification gating;
- retry/resume policy.

May depend on `domain`.

Must not instantiate Firestore, Pub/Sub, GCS, Gemini, ADK, EmbeddingGemma, MedGemma, or HTTP framework clients directly.

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
- EmbeddingGemma;
- optional MedGemma;
- evidence retrieval;
- notification providers;
- logging/tracing/telemetry.

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
application -> ADK SDK
FastAPI route -> AMR signal calculation
ADK wrapper -> raw Firestore + business logic
ADK wrapper -> direct external notification
React component -> Firestore / PubSub / Gemini / ADK
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

## 6. Hackathon Technology Contract — Mandatory

Ngabo v0.1 must actually use and visibly demonstrate:

- `gemini-3.6-flash` (or a documented eligible fallback) through Gemini API;
- Google ADK Python as the agent runtime;
- Cloud Run for deployed web/core services;
- Firestore for durable workflow state;
- Pub/Sub for asynchronous event-triggered processing;
- Cloud Storage for raw/evidence artifacts;
- Cloud Logging and/or supported Google tracing for proof/observability.

Do not implement a local-only substitute and then merely list Google Cloud in the README.

The canonical Taskmaster trigger is:

```text
surveillance signal event -> agent starts automatically
```

Do not require a user chat prompt to start the investigation.

See `docs/HACKATHON_ALIGNMENT.md`.

---

## 7. Runtime Responsibility Boundary

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
- incident-package drafting;
- bounded resumable investigation execution.

### Human owns

- supplying material missing context when requested;
- clinically/public-health consequential approval;
- outbreak confirmation through appropriate professional processes;
- patient treatment decisions.

Never blur these boundaries.

---

## 8. Google ADK Runtime Rules — Mandatory

ADK must provide real runtime value, not just satisfy a checklist.

Implement where supported/stable by the exact installed version:

- typed bounded tools;
- persisted session/invocation/run identifiers;
- resumable investigation execution;
- targeted human-input pause/resume;
- structured output validation;
- ADK evaluation datasets/results;
- tool/invocation tracing;
- explicit step/tool/time/retry limits.

### Firestore vs ADK state

```text
Firestore
  = canonical Ngabo business/workflow state

ADK resume/checkpoint state
  = agent execution continuity

Pub/Sub
  = asynchronous trigger/redelivery
```

Never make model conversation memory or an ADK session the only source of incident truth.

### Retry/idempotency rule

A resumed invocation or Pub/Sub redelivery may repeat work.

Therefore:

- read-only tools must be safe to repeat;
- state-changing operations require idempotency;
- consequential external action must not be an unrestricted agent tool;
- notifications execute only through the post-approval application workflow.

See `docs/ADK_RUNTIME.md`.

---

## 9. Runtime Agent Restrictions

The Ngabo runtime agent must not:

- execute arbitrary shell commands;
- issue unrestricted database queries;
- browse arbitrary URLs as approved evidence;
- mutate raw source data;
- send alerts before review approval;
- prescribe treatment;
- claim an outbreak is confirmed;
- fabricate citations;
- silently ignore a critical tool failure;
- loop without configured bounds.

Keep runtime tools narrow, typed, and auditable.

An ADK tool should normally call an application use case/query rather than directly implementing domain calculations or database side effects.

---

## 10. Evidence / Additional Google Model Rules

### Approved evidence

- evidence corpus is curated for v0.1;
- every source has source ID, title, publisher, URL, and date/version where possible;
- generated package may cite only retrieved source IDs;
- “no source found” is an acceptable result;
- fabricated guidance is not.

### EmbeddingGemma

EmbeddingGemma is the **planned post-core additional Google AI model** for semantic retrieval over the approved guidance corpus.

Rules:

- implement as an infrastructure adapter behind `EvidenceSearchPort`;
- keep source IDs/provenance attached;
- use lightweight deterministic cosine similarity for hackathon scale;
- do not add a vector database solely for bonus points;
- evaluate retrieval quality;
- do not claim bonus/model use unless it actually works and is documented/demoed.

### MedGemma

MedGemma is a gated stretch only.

It may be added as a source-traceable evidence-interpretation tool only after core + deployment + evals + EmbeddingGemma are stable.

It must not diagnose, prescribe, confirm outbreaks, or replace deterministic surveillance calculations.

If evaluation does not show meaningful benefit, omit it.

---

## 11. UI Rules

Do not build the core experience as a chat window.

Implement the operational hierarchy from `docs/UI_UX_SPEC.md` plus `docs/UI_UX_HACKATHON_ADDENDUM.md`:

- dashboard;
- import/validation;
- incident queue;
- incident detail;
- deterministic signal explanation;
- resistance-profile table;
- agent/tool timeline;
- pause/resume/retry visibility;
- targeted clarification;
- structured package;
- human review;
- real-vs-demo response tracking.

Do not expose hidden model chain-of-thought.

Frontend follows the Clean Architecture dependency philosophy:

```text
presentation -> application -> domain
infrastructure implements outer API/SSE access
```

UI components must not call Firestore, Pub/Sub, Gemini, ADK, or backend cloud SDKs directly.

---

## 12. Data Rules

- synthetic demo data only for public v0.1;
- every fixture declares that it is synthetic;
- never commit real patient data;
- unknown/missing values remain unknown/missing;
- do not generate plausible-looking values to make a demo prettier;
- keep raw import and normalized data logically distinct;
- imported free text is untrusted data, not instructions.

Future real-world datasets must follow `ROADMAP.md` and appropriate governance/authorization.

---

## 13. State / Event Rules

- Firestore is canonical operational state;
- incident transitions are explicit;
- event handlers are retry-safe;
- duplicate Pub/Sub events do not create duplicate actions;
- persisted audit events are append-only;
- failed workflow steps produce visible failure state;
- event handlers are interface adapters, not business-logic containers;
- persist enough agent execution metadata to correlate retries/resumes;
- interruption/resume must not reset or falsify incident history.

---

## 14. Real External Action — Required for Hosted Demo

Keep a deterministic demo notification adapter for tests/local reproducibility.

But the hosted/filmed v0.1 must also demonstrate at least one **real authorized external action** after approval through `NotificationPort`.

Required:

- human approval first;
- authorized integration only;
- delivery result persisted;
- idempotent retry;
- UI identifies real vs demo channel truthfully;
- acknowledgement/equivalent completion updates workflow state;
- never contact a real hospital/person without explicit authorization.

Do not let the agent directly bypass the notification workflow.

---

## 15. Observability Rules

Every autonomous workflow should be reconstructable from safe metadata/events.

Use where relevant:

```text
correlation_id
incident_id
event_id
agent_session_id
agent_invocation_id
agent_run_id
tool_name
tool_status
package_version
model_name
```

Use Cloud Logging and supported ADK/Cloud Trace/OpenTelemetry integration when stable.

Default to metadata/no-content tracing. Do not enable full prompt/response capture by default simply because tooling supports it.

Do not expose hidden chain-of-thought in logs or UI.

---

## 16. Evaluation by Architecture Layer

### Domain

Pure unit tests. No network, cloud, web framework, model, or ADK dependency.

### Application

Use cases/workflows tested with fakes or in-memory port implementations.

### Infrastructure

Adapter integration/contract tests.

### Interfaces

HTTP/event translation and contract tests.

### ADK evaluation

Evaluate observable final/trajectory behavior where supported:

- tool choice;
- required tool execution;
- clarification behavior;
- no-evidence behavior;
- failure handling;
- prompt injection;
- citation/isolate integrity;
- loop limits;
- resume/recovery.

### End-to-end

```text
upload
 -> detect
 -> event
 -> investigate
 -> clarify
 -> resume
 -> package
 -> review
 -> real notify
 -> acknowledge
```

A passing E2E test does not replace domain/application/agent evaluations.

Create public `EVALUATION.md` before submission.

---

## 17. Bonus / Submission Discipline

The project may pursue hackathon bonuses only after the core is reliable.

Planned:

- qualifying public LinkedIn build article;
- qualifying social post using exact hashtag `#AllThingsAgenticHackathon`;
- EmbeddingGemma if successfully integrated.

Gated:

- MedGemma if useful and evaluated;
- multimodal AST/PDF draft extraction only after core demo freeze criteria are nearly satisfied.

Never claim:

- a bonus model that is not actually integrated;
- a feature that exists only in docs;
- a model/service that is not shown in code or demonstrated where relevant.

Bonus points never outrank demo reliability or architecture quality.

---

## 18. Cloud Cost / Security Rules

Deployment work must include:

- Cloud Run minimum instances `0` unless justified;
- explicit max-instance caps;
- right-sized CPU/RAM;
- Google Cloud budget + email alert;
- Secret Manager/injected secrets;
- protected internal/PubSub endpoints;
- protection/rate limiting for expensive public endpoints where practical;
- least-privilege service accounts where practical;
- lightweight retention/cleanup plan;
- judge-accessible deployment through the required judging window.

Do not shut down required judge access immediately after recording the demo.

---

## 19. Coding Standards

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

## 20. Gitflow — Mandatory Branch Discipline

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

## 21. Semantic Versioning — Mandatory

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

## 22. Conventional Commits — Mandatory

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
web core surveillance agent evidence events data eval infra docs release architecture hackathon
```

Examples:

```text
feat(surveillance): add phenotype similarity detector
fix(events): prevent duplicate incident creation
test(eval): add prompt injection scenario
docs(hackathon): define Taskmaster proof-of-action requirements
```

Breaking change:

```text
feat(events)!: revise surveillance signal schema
```

Do not leave vague merge history such as `update stuff`, `wip`, or `changes`.

---

## 23. PR / Changelog Discipline

Substantive work should merge through PRs.

A PR should state:

- scope;
- reason;
- tests/evals run;
- API/schema/event impact;
- safety/human-review impact;
- architecture/dependency impact;
- hackathon requirement/bonus impact if relevant;
- docs/changelog impact;
- ADR requirement if applicable.

Do not merge knowingly failing required tests/evals.

Maintain `CHANGELOG.md`; summarize meaningful user/operator-visible changes under `Unreleased` during development.

---

## 24. Before Completing Any Task

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

Where agent behavior changes, also run the relevant ADK eval set and compare against baseline where practical.

Verify:

- branch follows Gitflow;
- commit follows Conventional Commits;
- SemVer/release impact considered;
- changelog/docs updated when required;
- Clean Architecture dependency rule preserved;
- monorepo/deployable boundaries preserved;
- safety gate preserved;
- hackathon technology/Taskmaster behavior not accidentally weakened.

---

## 25. Product Vocabulary

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

## 26. Primary Demo Scenario

The canonical v0.1 demo is a synthetic neonatal-unit *Klebsiella pneumoniae* resistance-pattern cluster with one intentionally missing metadata field.

It must demonstrate:

```text
import / data arrival
  ↓
deterministic validation
  ↓
surveillance signal
  ↓
Pub/Sub-triggered autonomous investigation
  ↓
tool/evidence activity
  ↓
targeted clarification
  ↓
resume same incident
  ↓
validated incident package
  ↓
human approval
  ↓
real authorized notification/action
  ↓
acknowledgement
  ↓
audit/trace proof
```

Do not replace the real path with canned final-state UI.

---

## 27. Stop Conditions

Stop and surface the issue instead of guessing when:

- docs materially contradict each other;
- official hackathon rules conflict with current repository assumptions;
- a requested feature violates the safety boundary;
- a dependency requires replacing a frozen architecture decision;
- domain/application code would need to depend directly on an outer vendor SDK;
- a change would split the monorepo or create a new deployable without an ADR;
- available data cannot support a claimed calculation;
- model output cannot be validated;
- a proposed external action lacks authorization/credentials;
- a bonus-model integration is being added only for points and threatens the core;
- release/version action conflicts with `ROADMAP.md` or SemVer;
- branch/merge action violates Gitflow without explicit authorization.

---

## 28. Scope Freeze

Until the end-to-end v0.1 core works and passes acceptance tests, do not add:

- pathogen genomics;
- AMRFinderPlus;
- vector database;
- BigQuery agent analytics unless explicitly justified;
- GKE;
- Redis/Kafka;
- LangGraph;
- mobile app;
- real patient data;
- production hospital connector;
- MedGemma;
- multimodal AST/PDF ingestion.

EmbeddingGemma begins only after the deployed core path is green.

---

## 29. Success Criterion

The coding agent succeeds when the repository truthfully demonstrates the PRD's Definition of Done **while preserving Clean Architecture, monorepo boundaries, safety, hackathon alignment, evaluated ADK behavior, and coherent versioned release history**—not when it generates the largest amount of code or the most model integrations.
