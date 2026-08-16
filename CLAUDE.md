# CLAUDE.md — Ngabo Implementation Contract

This is the root implementation contract for Claude Code working on Ngabo.

**Project:** Ngabo — Autonomous AMR Surveillance & Incident Response  
**Competition:** All Things Agentic Hackathon 2026 — The Taskmaster  
**Architecture:** Clean Architecture in a monorepo  
**Agent orchestration:** graph-first hybrid Google ADK workflow  
**Primary stack:** Next.js + TypeScript; Python + FastAPI; Google ADK; Gemini 3.6 Flash; Firestore; Cloud Storage; Pub/Sub; Cloud Run  
**Current release target:** `v0.1.0`  
**Deadline:** 2026-08-31 17:00 PT

---

## 1. Read Before Editing Code

Read in this order:

1. `ROADMAP.md`
2. `CONTRIBUTING.md`
3. `docs/PRD.md`
4. `docs/TECH_STACK.md`
5. `docs/CLEAN_ARCHITECTURE.md`
6. `docs/HACKATHON_ALIGNMENT.md`
7. `docs/ADK_RUNTIME.md`
8. `docs/ORCHESTRATION_PATTERNS.md`
9. `docs/LONG_RUNNING_AGENT.md`
10. `docs/SYSTEM_DESIGN.md`
11. `docs/AGENT_ARCHITECTURE.md`
12. `docs/DATA_SAFETY_EVALUATION.md`
13. `docs/OPERATIONAL_UTILITY_EVALUATION.md`
14. `docs/UI_UX_SPEC.md`
15. `docs/UI_UX_HACKATHON_ADDENDUM.md`
16. `docs/THIRD_PARTY_PROVENANCE.md`
17. `docs/SUBMISSION_EVIDENCE.md`
18. `docs/IMPLEMENTATION_PLAN.md`
19. relevant ADRs under `docs/adr/`, especially ADR 0005 and ADR 0006 for runtime/orchestration work.

Also read `AGENTS.md` and consult `CHANGELOG.md` before release-oriented work.

If official hackathon rules change, update repository contracts before implementing against stale assumptions.

Precedence for material conflicts:

```text
Official hackathon rules (contest requirements)
        ↓
Safety / data / provenance constraints
        ↓
CLAUDE.md invariants
        ↓
PRD
        ↓
Clean Architecture contract
        ↓
Hackathon / ADK / orchestration / long-running contracts
        ↓
Data/safety/evaluation + operational-utility contracts
        ↓
System Design / Agent Architecture
        ↓
UI/UX specifications
        ↓
Tech Stack / Roadmap / Implementation Plan
```

Do not silently resolve material conflicts. Surface them and create/update an ADR when appropriate.

---

## 2. Product Definition

Ngabo is an **open-source, event-driven antimicrobial-resistance surveillance and incident-response system**.

Do not make “prototype” part of permanent product identity. State maturity separately, for example:

> **Current status:** `v0.1.0` hackathon MVP in development.

Canonical v0.1 flow:

```text
synthetic WHONET-style data
        ↓
deterministic validation + normalization
        ↓
deterministic surveillance signal
        ↓
Pub/Sub event
        ↓
Google ADK investigation graph
        ↓
load canonical incident context
        ↓
parallel deterministic fan-out
  ├─ profile comparison
  ├─ baseline summary
  └─ structural missing-field assessment
        ↓
join typed findings
        ↓
Gemini 3.6 Flash reasoning where ambiguity exists
        ↓
approved evidence + targeted clarification if required
        ↓
pause / resume same incident
        ↓
Gemini evidence-grounded synthesis
        ↓
deterministic package validation
        ↓
human consequential-action approval
        ↓
deterministic pre-action freshness barrier
   ├─ stale → invalidate approval / re-review
   └─ fresh → continue
        ↓
real authorized external action
        ↓
acknowledgement + audit/trace trail
```

Ngabo is **not a chatbot product**. The web application is an incident-response console.

---

## 3. Hackathon Technology Contract — Non-Negotiable

The submitted v0.1 must actually use and visibly demonstrate:

- **Gemini 3.6 Flash** through Gemini API (eligible 3.5+ model);
- **Google ADK Python** as the graph/agent runtime;
- **Cloud Run** for `ngabo-web` and `ngabo-core`;
- **Firestore** for canonical durable workflow state;
- **Pub/Sub** for asynchronous event-triggered work;
- **Cloud Storage** for raw/evidence artifacts;
- **Cloud Logging / supported tracing** for inspectable execution.

Primary category: **The Taskmaster**.

The investigation must begin from an event such as `surveillance.signal.detected`, not a user chat prompt.

See `docs/HACKATHON_ALIGNMENT.md`.

---

## 4. Clean Architecture — Non-Negotiable

Dependencies point inward:

```text
Frameworks / Infrastructure
          ↓
Interfaces / Adapters
          ↓
Application / Use Cases / Ports
          ↓
Domain / Entities / Value Objects / Domain Services
```

Target backend:

```text
services/core/ngabo/
├── domain/
├── application/
├── interfaces/
├── infrastructure/
└── bootstrap/
```

### Domain

Owns AMR entities/value objects, incident state policy, deterministic surveillance rules and domain events/exceptions.

Must not import FastAPI, Google Cloud SDKs, ADK, Gemini, Gemma-family models, notification SDKs or transport/framework models.

### Application

Owns use cases, commands/queries, workflows, ports/contracts, DTOs, review/action gating, freshness/retry/resume policy and agent-facing contracts.

May depend on domain. Must not instantiate outer clients directly.

### Interfaces

Own HTTP/event translation only. FastAPI routes and Pub/Sub handlers must not contain scientific/business policy.

### Infrastructure

Implements Firestore, GCS, Pub/Sub, ADK graph/function/agent nodes, Gemini, EmbeddingGemma, optional MedGemma, evidence retrieval, notifications and telemetry behind inward-defined ports.

### Bootstrap

Composition root. Prefer explicit dependency injection.

Reject smells such as:

```text
domain -> FastAPI
application -> Firestore/Gemini/ADK SDK
route -> signal scoring
ADK function node -> raw database + business logic
ADK agent -> direct notification provider
React component -> Firestore / PubSub / Gemini / ADK
```

ADK function nodes are orchestration adapters, not a new business layer.

---

## 5. Monorepo — Non-Negotiable

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

Do not split the repo or create another deployable service without an ADR.

---

## 6. Scientific / Orchestration / Human Boundary

Governing orchestration rule:

> **Deterministic when the workflow is known; agentic when the decision is ambiguous; dynamic only when the workflow itself cannot reasonably be known in advance.**

### Deterministic code/function nodes own

- parsing/schema validation/normalization;
- AST calculations;
- time/location windows;
- profile similarity;
- baseline calculations;
- signal scoring;
- structural missing-field extraction;
- fixed routing/state-transition validation;
- idempotency;
- joining typed results;
- package validation;
- incident/package/source-version freshness comparison.

### Gemini agent nodes own

- reasoning across joined findings;
- deciding whether missing context is materially blocking;
- bounded evidence intent / optional capability selection;
- targeted clarification;
- source-grounded synthesis;
- labelled hypotheses;
- incident-package drafting;
- stopping with uncertainty when evidence is insufficient.

### Humans own

- materially missing context when requested;
- consequential public-health/clinical action approval;
- outbreak confirmation through appropriate professional process;
- patient treatment decisions.

The human does **not** manually sequence the normal investigation workflow.

Never implement:

```text
CSV -> LLM -> “outbreak detected”
```

Correct boundary:

```text
CSV -> deterministic detector -> investigation candidate -> ADK graph -> bounded Gemini reasoning
```

---

## 7. Google ADK Graph Runtime — Required

Core graph:

```text
signal event
   ↓
context function node
   ↓
parallel deterministic fan-out
   ├── profile comparison
   ├── baseline summary
   └── missing-field assessment
   ↓
join
   ↓
Gemini triage
   ↓
evidence / clarification
   ↓
Gemini synthesis
   ↓
deterministic package validation
   ↓
human review
```

Implement where supported/stable by the exact installed ADK release:

- graph/workflow orchestration;
- deterministic function nodes;
- fan-out/join for independent read-only work;
- deterministic routers for exhaustive rules;
- bounded Gemini nodes for ambiguity;
- persisted execution/session/run references;
- pause/resume/recovery;
- targeted human input;
- schema-constrained outputs;
- evals covering final result and observable trajectory;
- safe tracing/telemetry;
- explicit model/tool/time/retry budgets.

State model:

```text
Firestore/application persistence = canonical truth
ADK checkpoint/session           = execution continuity only
Pub/Sub                          = event transport/redelivery
```

See `docs/ADK_RUNTIME.md`, `docs/ORCHESTRATION_PATTERNS.md` and `docs/LONG_RUNNING_AGENT.md`.

---

## 8. Long-Running Agent Invariants — Required

Governing rule:

> **Resume execution, but revalidate truth.**

After a wait/restart/resume:

1. load canonical incident/workflow state;
2. restore runtime execution state where safe;
3. rebuild current bounded context;
4. re-run only safe/idempotent work;
5. append visible retry/resume audit state;
6. never let old session text/compaction/model memory override current facts;
7. run freshness validation again before consequential action.

### State/memory tiers

- Firestore/application state = canonical;
- ADK session/checkpoint = non-authoritative continuity;
- transient values = recomputable;
- Cloud Storage/artifacts = file-like outputs with provenance;
- cross-incident long-term model memory = disabled as factual input in v0.1.

### Pre-action freshness barrier

Approval is scoped to the exact reviewed package/incident/source-data state.

```text
APPROVED
  ↓
deterministic freshness check
  ├─ fresh → action may proceed
  └─ material change → approval stale → re-review
```

Do not let Gemini decide whether a version mismatch exists.

ADK Web is local-development only. Do not add A2A infrastructure in v0.1 without a new ADR.

---

## 9. Routing / Capability Restrictions

Known mandatory reproducible steps are graph/function nodes, not model-selected tools.

Use ordinary code for exhaustive routing:

```text
event type -> handler
state -> legal transition
duplicate -> idempotency path
validation -> pass/fail
approval -> freshness/action workflow
rejection -> stop
```

Use Gemini only for bounded ambiguous routing such as evidence intent, materiality of missing context, optional specialist use or evidence sufficiency.

Runtime capabilities must not:

- execute arbitrary shell commands;
- issue unrestricted database queries;
- browse arbitrary URLs as approved evidence;
- mutate source lab facts;
- send consequential alerts before approval/freshness;
- prescribe treatment;
- confirm outbreaks;
- fabricate citations;
- loop without bounds.

Preferred path:

```text
ADK node/tool wrapper
      ↓
application use case/query/port
      ↓
domain calculation or infrastructure adapter
      ↓
typed validated result
```

---

## 10. Truth / Package Contract

Truth hierarchy:

1. canonical source/application data;
2. deterministic calculations/results;
3. approved retrieved evidence;
4. explicitly labelled hypothesis;
5. unknown / insufficient evidence.

Final package must remain structured and include observed evidence, derived findings, hypotheses, uncertainties, missing information, guidance, investigation checklist, draft escalation/action and limitations.

Deterministic validation rejects unknown isolate/source IDs, unsupported factual claims, prohibited prescribing/outbreak-confirmation language or missing required structure.

A required graph branch failure must never be hidden by model synthesis.

---

## 11. Evidence / Optional Google Models

### EmbeddingGemma — planned after core green

Use only for semantic retrieval over the approved provenance-recorded guidance corpus behind `EvidenceSearchPort`.

Use a lightweight index appropriate to hackathon scale. Do not add a vector DB solely for bonus points.

Claim no bonus until integration is real, evaluated and shown truthfully.

### MedGemma — gated stretch

Only after core + deployment + evals + EmbeddingGemma are stable.

Permitted role: bounded source-traceable interpretation of already retrieved approved evidence.

Must not diagnose, prescribe, confirm outbreaks, replace deterministic calculations or introduce uncited authority.

Omit if measured value is not clear.

### Multimodal stretch

Only after core freeze:

```text
image/PDF -> UNVERIFIED AI DRAFT -> human verification -> canonical deterministic ingestion
```

Unverified extraction never enters surveillance calculations.

### Collaborative / dynamic patterns

Do not create specialist-agent fleets by default. Collaborative agents require measured benefit. Runtime-generated dynamic topology is deferred from core v0.1.

---

## 12. Human Clarification / Approval / Real Action

Clarification:

```text
INVESTIGATING
  ↓
WAITING_FOR_CLARIFICATION
  ↓ targeted answer
RESUME SAME INCIDENT
```

Final consequential review:

```text
WAITING_FOR_REVIEW
  ↓
APPROVED / REJECTED / NEEDS_MORE_INFO
```

Then:

```text
APPROVED
  ↓
FRESHNESS CHECK
  ↓ if current
NotificationPort
  ↓
real authorized adapter
  ↓
acknowledgement
```

Keep a deterministic demo adapter for tests, but the hosted/filmed v0.1 should perform at least one real authorized external action.

Use idempotency keys and persist delivery/ack state. Runtime agent may not bypass this workflow.

---

## 13. Observability — Required

Capture public-safe execution metadata where relevant:

```text
correlation_id
incident_id
event_id
graph_run_id
node_name
node_type
branch_id
join_id
agent_session_id
agent_invocation_id
agent_run_id
model_name
incident_version
package_version
review_id
source_watermark
freshness_result
```

Expose workflow facts such as graph start, fan-out, branch completion, join, agent stage, clarification, pause/resume, context rebuild, package validation, review, freshness and action/ack.

Do not expose private chain-of-thought. Default to metadata/no-sensitive-content tracing.

---

## 14. Evaluation — Required

Test by layer:

- domain deterministic unit tests;
- application workflow tests with fakes/in-memory ports;
- function-node tests;
- fan-out/join ordering/failure tests;
- deterministic router table tests;
- ADK final-result + observable-trajectory evals;
- infrastructure adapter/contract tests;
- deployed E2E tests;
- operational-utility benchmark;
- long-running context/resume/idempotency/freshness tests.

Canonical E2E:

```text
upload/data arrival
→ signal
→ Pub/Sub
→ graph
→ deterministic fan-out/join
→ Gemini triage
→ evidence
→ clarify
→ resume
→ synthesis
→ validate
→ review
→ freshness
→ real notify
→ acknowledge
```

Create public `EVALUATION.md` before submission.

Required operational metrics come from `docs/OPERATIONAL_UTILITY_EVALUATION.md`; do not fabricate time-saved percentages.

---

## 15. UI Contract

Read:

- `docs/UI_UX_SPEC.md`
- `docs/UI_UX_HACKATHON_ADDENDUM.md`

Core principle:

> **Incident-response console, not ChatGPT for AMR.**

UI must make visible:

- deterministic signal explanation;
- graph/function-node timeline;
- fan-out/join;
- bounded agent stages without chain-of-thought;
- pause/resume/recovery;
- evidence provenance;
- structured package;
- professional review boundary;
- freshness pass/failure/stale-approval state;
- real-vs-demo action channel;
- acknowledgement.

---

## 16. Operational Utility / Prize Evidence — Required

The highest-weighted judging criterion is operational utility.

Before submission, generate measured evidence for:

- zero user prompts required to start canonical investigation;
- human intervention/active-step count;
- signal-to-review-ready timing;
- clarification count;
- model/function/tool trajectory;
- real action/ack completion;
- comparison to a documented scripted reference workflow.

Use `docs/OPERATIONAL_UTILITY_EVALUATION.md`.

Use `docs/SUBMISSION_EVIDENCE.md` to map every Taskmaster, architecture, demo and bonus claim to an actual artifact/log/video/evaluation location.

Do not treat design documentation itself as execution proof.

---

## 17. Third-Party / Provenance / Ownership — Required

Use `docs/THIRD_PARTY_PROVENANCE.md`.

Before merging/submitting third-party code, model, data, evidence source or media:

- record source and applicable terms/license/usage basis;
- satisfy attribution/notices;
- ensure intended public-repo/submission use is permitted;
- do not redistribute real lab/patient data;
- use Ngabo-authored synthetic demo fixtures unless another data source is explicitly authorized;
- disclose non-standard pre-existing work if incorporated;
- do not imply third-party sponsorship/endorsement;
- do not claim optional model integration before exact terms + working implementation are verified.

Stop if ownership/authorization is unclear.

---

## 18. Cloud Deployment / Cost / Security

Required:

- `ngabo-web` + `ngabo-core` on Cloud Run;
- min instances `0` unless documented exception;
- explicit max-instance caps;
- right-sized resources;
- Google Cloud budget + alert;
- Secret Manager/injected secrets;
- protected Pub/Sub/internal endpoints;
- least-privilege identities where practical;
- bounded log/artifact retention;
- judge-accessible hosted project maintained through judging;
- no production exposure of ADK Web.

Do not delete judge-required resources immediately after recording the video.

---

## 19. Tech Stack — Do Not Substitute Casually

Frontend: Next.js, TypeScript, Tailwind CSS, shadcn/ui, pnpm.  
Backend: Python 3.11+, FastAPI, Pydantic v2, uv.  
AI: Google ADK Python, Gemini API, `gemini-3.6-flash`, planned EmbeddingGemma, gated MedGemma.  
Cloud: Cloud Run, Firestore, Pub/Sub, Cloud Storage, Secret Manager/injected secrets, Cloud Logging/supported tracing.  
Testing: pytest, ADK evaluation tooling, Playwright.

Do not add without documented need/ADR:

- LangGraph;
- GKE;
- Redis/Kafka;
- Cloud SQL;
- BigQuery as core v0.1 state/analytics;
- vector database;
- second non-Google LLM provider;
- genomics toolchain.

---

## 20. Implementation Order

Follow `docs/IMPLEMENTATION_PLAN.md` while preserving this critical order:

1. monorepo + Clean Architecture scaffold;
2. domain/state model;
3. synthetic data/schema;
4. deterministic ingestion/surveillance;
5. application ports/workflows;
6. deterministic investigation capabilities;
7. ADK graph + fan-out/join;
8. Gemini triage/synthesis;
9. persistent event workflow + long-running resume/context safety;
10. clarification + review + freshness barrier;
11. real action + acknowledgement;
12. incident console + graph/freshness timeline;
13. GCP deploy + observability/cost/security;
14. deterministic/agent/E2E/operational-utility evaluation;
15. EmbeddingGemma;
16. architecture/submission evidence + article/social/demo;
17. MedGemma/multimodal/collaborative agents only if core is frozen and stable.

---

## 21. Git / Release Governance — Mandatory

Use Semantic Versioning, Conventional Commits and Gitflow-style `main` + `develop`.

Feature work:

```text
feature/<short-name> from develop → PR to develop
```

Release:

```text
release/vX.Y.Z from develop → main → tag → reconcile back to develop
```

Hotfix:

```text
hotfix/vX.Y.Z from main → merge to main + develop
```

Do not create `1.0.0` automatically; maturity is governed by `ROADMAP.md`.

---

## 22. Bonus / Submission Discipline

Planned:

- public LinkedIn build article with required hackathon-purpose statement;
- public social post with exact hashtag `#AllThingsAgenticHackathon`;
- EmbeddingGemma after core green.

Gated:

- MedGemma only if useful/evaluated/stable;
- collaborative specialists only if evaluation justifies them;
- multimodal flow only after core freeze.

Never claim a model, feature, deployment, prize bonus or evaluation result that exists only in documentation.

Before Devpost freeze, reconcile every claim against `docs/SUBMISSION_EVIDENCE.md`.

---

## 23. Definition of Done Per Milestone

Before declaring a milestone complete:

- appropriate tests/evals pass;
- contracts/schemas are explicit;
- errors/failures are visible;
- Clean Architecture dependency direction holds;
- function nodes call inward contracts rather than duplicate policy;
- fixed routing uses no Gemini call;
- state/memory/freshness invariants hold;
- side effects remain idempotent;
- human consequential-action boundary holds;
- provenance/disclosure requirements are satisfied for new third-party material;
- docs/ADR are updated when contracts change;
- Gitflow/Conventional Commits are followed;
- competitive behavior/evidence is not weakened.

---

## 24. Stop Conditions

Stop and surface the issue rather than guessing when:

- official hackathon rules conflict with repository assumptions;
- safety/data/provenance docs conflict;
- a dependency would invert Clean Architecture;
- ADK node/tool would bypass application/domain contracts;
- deterministic logic is being moved into a prompt without justification;
- external action lacks authorization;
- current canonical data conflicts with stale session/model context;
- an old approval would act on materially changed incident state;
- model output cannot be validated;
- third-party rights/ownership are unclear;
- bonus integration threatens core reliability;
- collaborative/dynamic complexity lacks demonstrated need;
- release/Git operations violate governance.

---

## 25. Scope Freeze

Until deployed core E2E is green, do not add:

- MedGemma;
- collaborative specialist-agent topology;
- runtime-generated dynamic workflow topology;
- multimodal AST/PDF ingestion;
- pathogen genomics / AMRFinderPlus;
- vector database;
- GKE;
- Redis/Kafka;
- LangGraph;
- BigQuery agent analytics without explicit justification;
- mobile app;
- real patient data;
- production hospital connector.

EmbeddingGemma starts only after the required core graph works reliably.

---

## 26. Final Product Standard

A judge should be able to see, truthfully:

> **new AMR data arrived → deterministic Ngabo logic detected a signal → Pub/Sub triggered the ADK graph automatically → independent deterministic investigation steps fanned out and joined → Gemini reasoned only where ambiguity existed → the workflow paused for one necessary clarification → resumed safely using current canonical state → assembled traceable evidence → deterministic validation protected the package → a professional approved it → Ngabo revalidated freshness → executed one real authorized external action → acknowledgement plus audit/log/trace state proved completion.**

The repository should also prove why each architectural boundary exists, how operational friction is reduced, what third-party/data provenance applies, and where every submitted competitive claim is evidenced.

If we cannot demonstrate the behavior and architecture truthfully, the MVP is not complete.
