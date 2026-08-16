# AGENTS.md — Ngabo Coding-Agent Rules

This file applies to AI coding agents working anywhere in this repository.

Read `CLAUDE.md` first. `CLAUDE.md` is the root implementation contract; this file summarizes execution behavior, architecture, orchestration, long-running safety, hackathon evidence, Git/release discipline, and stop conditions.

---

## 1. Mission

Build Ngabo as a **safe, event-driven AMR surveillance and incident-response system**.

The current release target is `0.1.x`. Preserve the longer trajectory in `ROADMAP.md`.

Optimize for:

- working asynchronous autonomy;
- deterministic scientific logic;
- graph-first hybrid orchestration;
- explicit persistent state;
- resumable/recoverable long-running execution;
- current-context reconstruction;
- pre-action freshness protection;
- traceability/observability;
- bounded clinical/public-health claims;
- reproducibility;
- Clean Architecture;
- monorepo discipline;
- measured operational utility;
- third-party/data provenance;
- hackathon scoring/technology compliance;
- truthful proof of execution;
- maintainable release history;
- a clear <=4-minute demo.

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
9. `docs/ORCHESTRATION_PATTERNS.md`
10. `docs/LONG_RUNNING_AGENT.md`
11. `docs/SYSTEM_DESIGN.md`
12. `docs/AGENT_ARCHITECTURE.md`
13. `docs/DATA_SAFETY_EVALUATION.md`
14. `docs/OPERATIONAL_UTILITY_EVALUATION.md`
15. `docs/UI_UX_SPEC.md`
16. `docs/UI_UX_HACKATHON_ADDENDUM.md`
17. `docs/THIRD_PARTY_PROVENANCE.md`
18. `docs/SUBMISSION_EVIDENCE.md`
19. `docs/IMPLEMENTATION_PLAN.md`
20. relevant ADRs, especially ADR 0005 and ADR 0006 for runtime work.

Consult `CHANGELOG.md` before release-oriented work.

If official hackathon rules change, update repository contracts before implementing against stale assumptions.

---

## 3. Product Identity / Maturity

Preferred permanent identity:

> **Ngabo is an open-source AMR surveillance and incident-response system.**

State maturity separately:

> `v0.1.0` hackathon MVP in development.

Do not overclaim hospital use, clinical validation or production readiness.

---

## 4. Clean Architecture — Mandatory

```text
Frameworks / Infrastructure
          ↓
Interfaces / Adapters
          ↓
Application / Use Cases / Ports
          ↓
Domain / Entities / Value Objects / Domain Services
```

### Backend shape

```text
services/core/ngabo/
├── domain/
├── application/
├── interfaces/
├── infrastructure/
└── bootstrap/
```

### Rules

- domain owns deterministic AMR/scientific policy and imports no outer frameworks;
- application owns use cases/workflows/ports and imports no concrete cloud/model SDKs;
- interfaces translate HTTP/events only;
- infrastructure implements Firestore/GCS/PubSub/ADK/Gemini/evidence/notification/telemetry ports;
- bootstrap owns dependency wiring;
- React UI calls backend/application abstractions, not cloud/model SDKs directly.

Stop and fix:

```text
domain -> FastAPI
application -> google.cloud.firestore
application -> Gemini SDK
application -> ADK SDK
route -> AMR calculation
ADK function node -> raw Firestore + business logic
ADK agent -> direct notification provider
React component -> Firestore / PubSub / Gemini / ADK
```

ADK function nodes are orchestration adapters, not a new business layer.

---

## 5. Monorepo — Mandatory

```text
ngabo/
├── apps/web/
├── services/core/
├── data/
├── docs/
├── infra/
└── .github/
```

`ngabo-web` and `ngabo-core` remain independently deployable Cloud Run services.

Do not split repos or add deployables without an ADR.

---

## 6. Hackathon Technology Contract

The submitted v0.1 must actually use and visibly demonstrate:

- Gemini 3.6 Flash (or documented eligible fallback) through Gemini API;
- Google ADK Python as graph/agent runtime;
- Cloud Run for web/core;
- Firestore for canonical durable workflow state;
- Pub/Sub for asynchronous trigger/redelivery;
- Cloud Storage for artifacts/raw files;
- Cloud Logging/supported tracing for proof.

Primary category: **The Taskmaster**.

Canonical trigger:

```text
surveillance signal event -> ADK graph starts automatically
```

Never require a user chat prompt to start the normal investigation.

---

## 7. Runtime Responsibility Boundary

Governing rule:

> **Deterministic when the workflow is known; agentic when the decision is ambiguous; dynamic only when the workflow itself cannot reasonably be known in advance.**

### Deterministic layer/function nodes

Own parsing, validation, normalization, AST calculations, similarity, temporal/location windows, baselines, signal scoring, structural missingness, fixed routing/state policy, idempotency, typed joins, package validation and freshness/version comparison.

### Gemini agent nodes

Own reasoning across joined findings, materiality assessment, bounded evidence intent/optional capability choice, targeted clarification, evidence synthesis, labelled hypotheses, package drafting and stopping with uncertainty.

### Humans

Own materially missing context when asked, consequential response approval, outbreak confirmation under appropriate process and patient treatment decisions.

The human does not manually sequence the normal graph.

---

## 8. Google ADK Graph Runtime

Core target:

```text
signal
 ↓
context function
 ↓
parallel deterministic fan-out
 ├─ profile comparison
 ├─ baseline summary
 └─ missing-field assessment
 ↓
join
 ↓
Gemini triage
 ↓
evidence / clarification
 ↓
Gemini synthesis
 ↓
deterministic validation
 ↓
review
```

Implement where supported/stable:

- graph/workflow orchestration;
- deterministic function nodes;
- fan-out/join;
- deterministic routers;
- bounded agent nodes;
- persisted run/session/invocation refs;
- pause/resume/recovery;
- typed outputs;
- evals;
- tracing;
- model/tool/time/retry budgets.

Required deterministic branch failure must remain visible; later model output cannot paper it over.

---

## 9. Long-Running State / Memory / Freshness — Mandatory

Governing rule:

> **Resume execution, but revalidate truth.**

```text
Firestore/application state = canonical truth
ADK session/checkpoint       = execution continuity
transient state              = recomputable
Cloud Storage artifacts      = file-like outputs
long-term model memory       = non-authoritative / disabled for v0.1 factual incident reasoning
```

After resume:

- reload current incident data;
- rebuild bounded current context;
- repeat only safe/idempotent work;
- preserve audit history;
- never let old session text override canonical facts;
- re-run freshness before consequential action.

### Freshness barrier

```text
APPROVED
  ↓
current incident/package/source comparison
  ├─ fresh → action
  └─ material change → approval stale → re-review
```

Stale approval may never be replayed by retry/redelivery.

ADK Web is local-only. Do not add A2A infrastructure in v0.1 without an ADR.

---

## 10. Runtime Restrictions

No arbitrary shell, unrestricted DB access, arbitrary web evidence, source-fact mutation, pre-review consequential alerting, prescribing, outbreak confirmation, fabricated citations or unbounded loops.

Known fixed routing is code, not prompt text.

Preferred flow:

```text
ADK node/tool
  ↓
application query/use case
  ↓
domain calculation or port
  ↓
typed result
```

---

## 11. Evidence / Models

Approved evidence corpus must be curated, provenance-recorded and source-ID traceable.

### EmbeddingGemma

Post-core only. Use behind `EvidenceSearchPort` for semantic retrieval over approved sources. Preserve source IDs and evaluate retrieval. No vector DB solely for bonus points.

### MedGemma

Gated stretch only. Bounded interpretation of already retrieved evidence. No diagnose/prescribe/outbreak authority/deterministic replacement.

### Multimodal

Post-core only:

```text
image/PDF -> UNVERIFIED AI DRAFT -> human verification -> canonical ingestion
```

### Collaborative/dynamic

Do not add agent teams or dynamic topology for aesthetics. Require measurable value/ADR where specified.

---

## 12. Human Review / Action

Clarification may pause/resume the same incident.

Final consequential review remains an application/domain state gate.

Real hosted-demo action path:

```text
professional approval
→ freshness validation
→ NotificationPort
→ authorized real adapter
→ delivery persisted
→ acknowledgement
```

Use idempotency. Keep a deterministic demo adapter for tests. Do not contact real institutions/people without explicit authorization.

---

## 13. UI Rules

Build an incident-response console, not a chat app.

Show:

- why signal was flagged;
- deterministic function-node timeline;
- fan-out/join;
- bounded agent stages without chain-of-thought;
- evidence provenance;
- clarification pause/resume;
- recovery/context rebuild where relevant;
- structured package;
- professional review;
- freshness pass/failure and stale-approval re-review;
- real-vs-demo action truthfully;
- acknowledgement.

Do not expose hidden chain-of-thought.

---

## 14. Data / Provenance Rules

- synthetic demo data only;
- every fixture labelled synthetic;
- never commit real patient/lab data;
- missing values stay missing;
- imported free text is untrusted data;
- raw import and normalized data remain distinct;
- approved evidence sources require provenance/usage records;
- third-party data/model/dependency rights/terms must be recorded;
- non-standard pre-existing work must be disclosed if reused.

See `docs/THIRD_PARTY_PROVENANCE.md`.

Stop if ownership/authorization is unclear.

---

## 15. State / Event / Idempotency Rules

- Firestore is canonical operational state;
- transitions are explicit;
- event handlers are retry-safe thin adapters;
- duplicate Pub/Sub delivery does not duplicate incidents/actions;
- audit events are append-only;
- failed graph steps are visible;
- graph/agent execution metadata correlates retries/resumes;
- required deterministic branch failure cannot be hidden;
- stale approval cannot execute after redelivery;
- consequential side effects use idempotency keys.

---

## 16. Observability

Use safe metadata such as:

```text
correlation_id
incident_id
event_id
graph_run_id
node/branch/join IDs
agent session/invocation/run IDs
model_name
incident_version
package_version
review_id
source_watermark
freshness_result
```

Expose graph start, fan-out/join, agent stage, evidence, clarification, pause/resume, context rebuild, package validation, review, freshness, action and acknowledgement.

Metadata-first traces; no chain-of-thought.

---

## 17. Evaluation

Required layers:

- pure domain tests;
- application workflow tests;
- function-node tests;
- fan-out/join ordering/failure tests;
- deterministic-router table tests;
- ADK final-result/trajectory evals;
- prompt-injection/source/isolate/clinical-claim adversarial tests;
- resume/context/idempotency tests;
- freshness/stale-approval tests;
- deployed E2E;
- operational-utility benchmark;
- EmbeddingGemma/MedGemma evaluation only if integrated.

Canonical E2E:

```text
upload/data arrival
→ signal
→ Pub/Sub
→ graph
→ deterministic fan-out/join
→ Gemini triage
→ evidence
→ clarification
→ resume
→ synthesis
→ validation
→ review
→ freshness
→ real action
→ acknowledgement
```

Create public `EVALUATION.md` before submission.

---

## 18. Operational Utility / Submission Evidence

Use `docs/OPERATIONAL_UTILITY_EVALUATION.md` to measure:

- zero user prompts to start canonical investigation;
- human intervention/active-step count;
- signal-to-review-ready timing;
- clarification count;
- model/function/tool counts;
- action-to-ack timing where available;
- comparison with documented scripted reference workflow.

Do not invent hospital productivity percentages.

Use `docs/SUBMISSION_EVIDENCE.md` to map every competitive claim to real proof: URL, trace, screenshot, eval result, video segment or external action.

Documentation intent is not execution proof.

---

## 19. Cloud / Security / Cost

Required:

- web/core on Cloud Run;
- min instances 0 unless justified;
- max caps/right-sized resources;
- budget + alert;
- secrets injected, not committed;
- protected Pub/Sub/internal endpoints;
- least privilege where practical;
- judge access kept through judging;
- no public ADK Web.

---

## 20. Implementation / Scope Freeze

Follow `docs/IMPLEMENTATION_PLAN.md`.

Until deployed core E2E is green, do not add:

- MedGemma;
- collaborative specialist topology;
- dynamic workflow topology;
- multimodal ingestion;
- genomics/AMRFinderPlus;
- vector database;
- GKE;
- Redis/Kafka;
- LangGraph;
- mobile app;
- real patient data;
- production hospital connector.

EmbeddingGemma begins only after core works reliably.

---

## 21. Git / Release Discipline

Use SemVer, Conventional Commits and Gitflow-style branches.

Feature:

```text
feature/<short-name> from develop -> PR to develop
```

Release:

```text
release/vX.Y.Z from develop -> main -> tag -> reconcile to develop
```

Hotfix from `main`, merged to both `main` and `develop`.

Do not direct-commit feature work to `main`.

---

## 22. Stop Conditions

Stop and surface when:

- official rules conflict with docs;
- safety/provenance is unclear;
- dependency direction would invert Clean Architecture;
- deterministic logic is being delegated to an LLM without reason;
- ADK node would bypass application/domain contracts;
- model output cannot be validated;
- external action lacks authorization;
- old context conflicts with current canonical state;
- stale approval would execute;
- third-party rights are unclear;
- bonus work threatens core reliability;
- Git/release operation violates governance.

---

## 23. Final Standard

A judge should be able to see truthfully:

> **AMR data arrived → deterministic Ngabo logic detected a signal → Pub/Sub triggered an ADK graph → deterministic investigation work fanned out and joined → Gemini reasoned only where ambiguity existed → the workflow asked one necessary clarification and resumed the same incident using current canonical truth → traceable evidence was synthesized → deterministic validation protected the package → a professional approved consequential action → Ngabo revalidated freshness → executed one authorized real-world action → acknowledgement plus logs/state proved completion.**

The repository must also show measured operational utility, reproducible setup, third-party/data provenance, and proof locations for every submitted competitive claim.
