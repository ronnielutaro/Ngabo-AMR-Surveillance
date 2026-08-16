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
9. `docs/SYSTEM_DESIGN.md`
10. `docs/AGENT_ARCHITECTURE.md`
11. `docs/DATA_SAFETY_EVALUATION.md`
12. `docs/UI_UX_SPEC.md`
13. `docs/UI_UX_HACKATHON_ADDENDUM.md`
14. `docs/IMPLEMENTATION_PLAN.md`
15. relevant ADRs under `docs/adr/`, including ADR 0005 for agent-orchestration work

Also read `AGENTS.md` and consult `CHANGELOG.md` before release-oriented work.

If documents conflict, use this precedence:

```text
Official hackathon rules (for contest requirements)
        ↓
Safety / data constraints
        ↓
CLAUDE.md invariants
        ↓
PRD
        ↓
Clean Architecture contract
        ↓
Hackathon / ADK runtime / orchestration contracts
        ↓
System Design / Agent Architecture
        ↓
UI/UX specifications
        ↓
Tech Stack
        ↓
ROADMAP
        ↓
Implementation Plan
```

Do not silently resolve material conflicts. Surface them and create an ADR when appropriate.

---

## 2. Product Definition

Ngabo is an **open-source, event-driven antimicrobial-resistance surveillance and incident-response system**.

Do not make “prototype” part of the permanent product identity. State maturity separately, for example:

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
deterministic function-node fan-out + join
        ↓
Gemini 3.6 Flash reasoning where ambiguity exists
        ↓
approved evidence + targeted clarification if required
        ↓
resumed investigation
        ↓
deterministically validated incident package
        ↓
human approval
        ↓
real authorized external action
        ↓
acknowledgement + audit trail
```

Ngabo is **not a chatbot product**. The web application is an incident-response console.

---

## 3. Hackathon Technology Contract — Non-Negotiable

The v0.1 implementation must actually use and visibly demonstrate:

- **Gemini 3.6 Flash** through Gemini API (eligible 3.5+ model);
- **Google ADK Python** as the graph/agent runtime;
- **Cloud Run** for `ngabo-web` and `ngabo-core`;
- **Firestore** for durable workflow state;
- **Pub/Sub** for asynchronous event-triggered work;
- **Cloud Storage** for raw/evidence artifacts;
- **Cloud Logging / supported tracing** for inspectable execution.

Primary category is **The Taskmaster**.

The workflow must start from an event such as:

```text
surveillance.signal.detected
```

Do not require a user to type “investigate this” to begin the workflow.

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

Target backend shape:

```text
services/core/ngabo/
├── domain/
├── application/
├── interfaces/
├── infrastructure/
└── bootstrap/
```

### Domain

Owns:

- AMR entities/value objects;
- incident state policy;
- deterministic surveillance rules;
- domain events/exceptions.

Must not import FastAPI, Google Cloud SDKs, ADK, Gemini, Gemma-family models, notification SDKs, or transport/framework models.

### Application

Owns:

- use cases;
- commands/queries;
- workflows;
- ports/contracts;
- application DTOs;
- agent-facing contracts;
- review/notification gating;
- retry/resume policy.

May depend on domain. Must not instantiate outer clients directly.

### Interfaces

Own HTTP/event translation only. FastAPI routes and Pub/Sub handlers must not contain AMR/scientific/business policy.

### Infrastructure

Implements ports for:

- Firestore;
- GCS;
- Pub/Sub;
- Google ADK graph/function/agent nodes;
- Gemini;
- EmbeddingGemma;
- optional MedGemma;
- evidence retrieval;
- notification providers;
- logging/tracing.

### Bootstrap

Composition root. Prefer explicit dependency injection.

Reject architecture smells such as:

```text
domain -> FastAPI
application -> Firestore SDK
application -> Gemini/ADK SDK
route -> signal scoring
ADK function node -> raw database + business logic
ADK agent tool -> direct external notification
React component -> Firestore / PubSub / Gemini / ADK
```

ADK function nodes are orchestration adapters; they do not become a new domain/business layer.

---

## 5. Monorepo — Non-Negotiable

One repository:

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

Do not split the repository or create a new deployable service without an ADR.

---

## 6. Scientific, Orchestration, and Safety Invariants

The governing orchestration rule is:

> **Deterministic when the workflow is known; agentic when the decision is ambiguous; dynamic only when the workflow itself cannot reasonably be known in advance.**

### Deterministic code/function nodes own

- CSV parsing;
- schema validation;
- organism/antibiotic normalization;
- AST calculations;
- time windows;
- resistance-profile similarity;
- baseline calculations;
- signal scoring;
- structural missing-field extraction;
- fixed routing/state-transition validation;
- idempotency policy;
- package post-generation validation;
- joining typed deterministic results.

### Gemini agent nodes own

- reasoning across joined findings;
- deciding whether a missing value is materially blocking;
- bounded optional capability/evidence-topic selection;
- contextual evidence intent;
- targeted clarification;
- evidence synthesis;
- labelled hypotheses;
- incident-package drafting;
- bounded resumable reasoning execution;
- stopping when evidence is insufficient.

### Humans own

- material missing context when requested;
- consequential public-health/clinical escalation approval;
- outbreak confirmation through appropriate process;
- treatment decisions.

Never blur these boundaries.

Never implement:

```text
CSV -> LLM -> “outbreak detected”
```

Correct boundary:

```text
CSV -> deterministic detector -> investigation candidate -> ADK graph -> bounded Gemini reasoning
```

Source laboratory facts are immutable. Human clarification is persisted separately with provenance.

---

## 7. Google ADK Graph Runtime — Required

ADK is a real runtime capability, not a compliance badge.

Core v0.1 graph:

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
Gemini triage agent node
   ↓
evidence / clarification
   ↓
Gemini synthesis agent node
   ↓
deterministic package validation
   ↓
human review
```

Implement where supported/stable by the exact installed ADK version:

- explicit graph/workflow orchestration;
- deterministic function nodes;
- parallel fan-out/join for independent read-only work;
- deterministic routers for exhaustive rules;
- bounded Gemini agent nodes for ambiguity;
- persisted session/invocation/run references;
- resumable investigation execution;
- targeted human-input pause/resume;
- schema-constrained output;
- ADK evaluations;
- graph/node/invocation traces;
- explicit model/tool/time/retry limits.

State model:

```text
Firestore
  = canonical Ngabo workflow/business state

ADK resume/checkpoint
  = graph/agent execution continuity

Pub/Sub
  = asynchronous trigger/redelivery
```

Do not make model conversation memory or ADK session state the only incident record.

A resumed graph may repeat work. Read-only nodes/tools must be repeatable; state-changing operations must be idempotent.

See `docs/ADK_RUNTIME.md` and `docs/ORCHESTRATION_PATTERNS.md`.

---

## 8. Routing, Capabilities, and Restrictions

Core application-facing capabilities:

- `get_incident_context()`
- `compare_resistance_profiles()`
- `get_baseline_summary()`
- `get_missing_fields()`
- `search_approved_guidance()`
- `request_clarification()`
- `prepare_incident_package()`

Do not assume every capability is an agent-chosen tool.

Known mandatory reproducible steps should be graph/function nodes. Agent-driven invocation is reserved for genuinely optional/ambiguous capabilities.

### Deterministic routing

Use ordinary code for exhaustive rules such as:

```text
event type -> handler
state -> legal transition
duplicate -> idempotency path
validation -> pass/fail path
approval -> notification
rejection -> stop
```

### Agentic routing

Use Gemini only for bounded ambiguous choices such as evidence topic, materiality of missing context, optional specialist use, or evidence sufficiency.

Runtime agent must not:

- execute arbitrary shell commands;
- run unrestricted database queries;
- treat arbitrary web URLs as approved evidence;
- mutate source facts;
- send alerts before review approval;
- prescribe treatment;
- confirm outbreaks;
- fabricate citations;
- loop without bounds.

Preferred node/tool flow:

```text
ADK node/tool wrapper
      ↓
application query/use case/port
      ↓
domain calculation or infrastructure adapter
      ↓
typed validated result
```

---

## 9. Truth and Incident Package Contract

Truth hierarchy:

1. canonical source data;
2. deterministic graph/tool output;
3. approved retrieved evidence;
4. explicitly labelled hypothesis;
5. unknown / insufficient evidence.

Final package must remain structured:

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

Post-generation deterministic validation must reject unknown isolate IDs, unknown source IDs, unsupported observed/derived claims, prohibited prescribing/outbreak-confirmation language, or missing required fields.

A required graph branch failure must not be hidden by later model synthesis.

---

## 10. Evidence and Additional Google Models

### EmbeddingGemma — planned after core green

Use for semantic retrieval over the **approved guidance corpus** only.

Architecture:

```text
EvidenceSearchPort
        ↑
EmbeddingGemmaEvidenceAdapter
        ↓
precomputed approved embeddings + lightweight cosine similarity
```

For hackathon scale, do not add a vector database solely for bonus points.

Claim the model bonus only if the integration works, is evaluated, appears in code/docs, and is truthfully represented in the submission.

### MedGemma — gated stretch

Only after core + deployment + evals + EmbeddingGemma are stable.

Permitted bounded role: source-traceable interpretation of already retrieved approved medical/AMR evidence.

Prefer a bounded/stateless specialist capability before creating an autonomous MedGemma sub-agent.

It must not diagnose, prescribe, confirm outbreaks, replace deterministic surveillance, or create uncited authority.

If evaluation does not show material benefit, omit it.

### Collaborative specialist pattern

Do not introduce multiple specialist agents by default. Add them only if evaluation shows capability/traceability/reliability benefit. A future coordinator may select only the relevant subset of specialists.

### Dynamic workflow pattern

Deferred from core v0.1. Use only if a later investigation's execution topology genuinely cannot be known ahead of runtime.

### Multimodal stretch

Only after core freeze, Gemini may extract a **draft** from an image/scanned-PDF AST report:

```text
image/PDF -> AI draft -> human verification -> canonical deterministic ingestion
```

Unverified extraction must never enter the detector.

---

## 11. Human Clarification and Final Approval

The deterministic missing-field node detects missingness. Gemini decides whether a missing value is materially important enough to pause the investigation.

Clarification flow:

```text
INVESTIGATING
  ↓
WAITING_FOR_CLARIFICATION
  ↓ human answer
INVESTIGATING / RESUME
```

Questions must be targeted and materially necessary.

Final consequential approval remains an application/domain state-machine gate:

```text
WAITING_FOR_REVIEW
  ↓
APPROVED / REJECTED / NEEDS_MORE_INFO
```

Do not make a framework confirmation primitive the sole safety mechanism.

---

## 12. Real External Action — Required for Hosted Demo

Keep a deterministic demo notification adapter for tests/local reproducibility.

The hosted/filmed v0.1 must also perform at least one **real authorized external action** after human approval through `NotificationPort`.

Required:

- authorization;
- human approval first;
- idempotency key;
- persisted delivery attempt/result;
- visible external result;
- acknowledgement or equivalent completion signal;
- UI truthfully distinguishes real integration from demo simulation.

The runtime agent must not send the final notification directly.

---

## 13. Observability — Required

Capture safe structured execution metadata such as:

```text
correlation_id
incident_id
event_id
agent_session_id
agent_invocation_id
agent_run_id
graph_run_id
node_name
node_type
branch_id
join_id
model_name
package_version
```

Expose graph facts such as fan-out, branch completion, join, agent-node start, clarification/resume, and package validation.

Use Cloud Logging plus supported ADK/Cloud Trace/OpenTelemetry integration where stable.

Do not expose private chain-of-thought. Default to metadata/no-content traces rather than full prompt/response capture.

Observability failure must not change domain behavior.

---

## 14. Evaluation — Required

Test by layer:

### Domain
Pure unit tests without cloud/model/network.

### Application
Use cases/workflows with fakes/in-memory ports.

### Function nodes
Verify deterministic behavior and typed failures without Gemini.

### Fan-out / join
Verify branch-order independence, required-branch failure semantics, and retry/idempotency behavior.

### Deterministic routers
Table-driven tests cover all fixed branches.

### ADK / agentic routing
Evaluate final result and observable trajectory where supported:

- mandatory graph-node execution;
- correct bounded optional capability choice;
- clarification when required;
- no unnecessary clarification;
- empty evidence;
- required branch/tool failure;
- prompt injection;
- fabricated citation/isolate reference;
- clinical overclaiming;
- model/tool budget;
- resume/recovery;
- zero unnecessary model call for fixed routing decisions.

### E2E

```text
upload -> signal -> event -> graph fan-out/join -> Gemini triage -> clarify -> resume -> evidence -> synthesis -> validate -> review -> real notify -> acknowledge
```

Create public `EVALUATION.md` before submission.

For the canonical scenario record model-call count, function/tool calls, retries, clarification count, branch timings, and total investigation duration as engineering regression metrics.

---

## 15. UI Contract

Read both:

- `docs/UI_UX_SPEC.md`
- `docs/UI_UX_HACKATHON_ADDENDUM.md`

Core principle:

> **Incident-response console, not ChatGPT for AMR.**

UI must visibly show:

- deterministic signal explanation;
- graph/node timeline;
- parallel fan-out and join where legible;
- agent reasoning stages as observable actions, not chain-of-thought;
- interruption/retry/resume when relevant;
- targeted clarification;
- evidence and source provenance;
- structured package;
- human gate;
- real-vs-demo action channel;
- response/acknowledgement.

Never expose hidden chain-of-thought.

---

## 16. Cloud Deployment / Cost / Security Contract

Required for v0.1 deployment:

- `ngabo-web` on Cloud Run;
- `ngabo-core` on Cloud Run;
- minimum instances `0` unless documented exception;
- explicit max-instance caps;
- right-sized resources;
- Google Cloud budget + email alert;
- Secret Manager/injected secrets;
- protected internal/PubSub endpoints;
- protection/rate limiting for expensive public endpoints where practical;
- least-privilege service accounts where practical;
- lightweight storage/log retention;
- hosted judge access preserved through required judging period.

Do not delete the judge-accessible hosted project immediately after recording proof.

---

## 17. Tech Stack — Do Not Substitute Casually

Frontend:

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- pnpm

Backend:

- Python 3.11+
- FastAPI
- Pydantic v2
- uv

AI:

- Google ADK Python
- Gemini API
- `gemini-3.6-flash`
- planned EmbeddingGemma after core
- optional MedGemma only if gated criteria pass

Cloud:

- Cloud Run
- Firestore
- Pub/Sub
- Cloud Storage
- Secret Manager/injected secrets
- Cloud Logging / supported tracing

Testing:

- pytest
- ADK evaluation tooling
- Playwright

Do not add without a documented need/ADR:

- LangGraph;
- GKE;
- Redis;
- Kafka;
- Cloud SQL;
- BigQuery as core state/analytics for v0.1;
- vector database;
- second non-Google LLM provider;
- genomics toolchain.

---

## 18. Implementation Order

Follow `docs/IMPLEMENTATION_PLAN.md` exactly enough to preserve the critical path.

Core order:

1. Clean Architecture monorepo scaffold;
2. domain/state model;
3. synthetic data/schema;
4. deterministic ingestion;
5. deterministic surveillance;
6. application ports/workflows;
7. deterministic investigation capabilities;
8. ADK graph scaffold: context -> parallel function nodes -> join;
9. Gemini triage/synthesis agent nodes + bounded agentic routing;
10. persistent event workflow + resume safety;
11. clarification + human gate;
12. real action;
13. incident console + graph timeline;
14. GCP deploy + observability/cost/security;
15. evaluation including trajectory/model-call budget;
16. EmbeddingGemma;
17. public content/demo/submission;
18. MedGemma/collaborative agents/multimodal only if core is frozen and stable.

Dynamic workflow topology and genomics remain post-core unless a new requirement is accepted through architecture review.

---

## 19. Git / Release Governance — Mandatory

Use:

- Semantic Versioning 2.0.0;
- Conventional Commits 1.0.0;
- Gitflow-style `main` + `develop`;
- `CHANGELOG.md`;
- tags `vX.Y.Z`.

Feature work:

```text
feature/<short-name>
```

from `develop`, merged through PR into `develop`.

Release:

```text
release/vX.Y.Z -> main -> tag -> reconcile to develop
```

Hotfix:

```text
hotfix/vX.Y.Z
```

from `main`, merged to both `main` and `develop`.

Conventional commit format:

```text
<type>[optional scope]: <description>
```

Recommended scopes include:

```text
web core surveillance agent evidence events data eval infra docs release architecture hackathon
```

Do not create `1.0.0` automatically; production readiness is governed by `ROADMAP.md`.

---

## 20. Bonus / Submission Discipline

Planned bonus paths:

- public LinkedIn build article with required hackathon-purpose statement;
- social post with exact hashtag `#AllThingsAgenticHackathon`;
- EmbeddingGemma if successfully integrated.

Gated:

- MedGemma only if real, useful, evaluated, and stable;
- collaborative specialist agents only if evaluation justifies them;
- multimodal AST/PDF draft flow only after core freeze.

Never claim a model, feature, bonus, deployment, or evaluation result that exists only in documentation.

Bonus points never outrank architecture quality or demo reliability.

---

## 21. Definition of Done Per Milestone

Before declaring a milestone complete:

- tests/evals appropriate to the changed surface pass;
- schemas/contracts are explicit;
- errors are visible, not swallowed;
- Clean Architecture dependency rule holds;
- graph/function nodes call inward contracts rather than duplicating business logic;
- fixed routing decisions do not invoke Gemini;
- monorepo/deployable boundaries hold;
- safety/human gate holds;
- docs/ADR updated if contracts changed;
- branch follows Gitflow;
- commits follow Conventional Commits;
- changelog/release impact considered;
- hackathon behavior is not weakened.

---

## 22. Stop Conditions

Stop and surface the issue rather than guessing when:

- official hackathon rules conflict with repository assumptions;
- docs materially contradict;
- a requested change violates safety;
- a dependency would invert Clean Architecture;
- an ADK node would need to bypass application/domain contracts;
- a known deterministic rule is being moved into an LLM prompt without justification;
- a new deployable/repo is required without an ADR;
- available data cannot support a claimed calculation;
- model output cannot be validated;
- an external action lacks authorization;
- a bonus integration threatens the core path;
- collaborative/dynamic complexity is being added without a demonstrated product need;
- a Git/release operation violates documented governance.

---

## 23. Scope Freeze

Until the deployed core E2E graph is green, do not add:

- MedGemma;
- collaborative specialist-agent topology;
- runtime-generated dynamic workflow topology;
- multimodal AST/PDF ingestion;
- pathogen genomics;
- AMRFinderPlus;
- vector database;
- GKE;
- Redis/Kafka;
- LangGraph;
- BigQuery agent analytics unless explicitly justified;
- mobile app;
- real patient data;
- production hospital connector.

EmbeddingGemma starts only after the required core graph works reliably.

---

## 24. Final Product Standard

A judge should be able to see, truthfully:

> **new AMR data arrived → deterministic Ngabo logic detected a signal → Pub/Sub triggered the ADK graph automatically → independent deterministic investigation steps fanned out and joined → Gemini reasoned only where ambiguity existed → the workflow paused for one necessary clarification → resumed safely → assembled traceable evidence → deterministic validation protected the package → a professional approved it → Ngabo executed a real authorized external action → acknowledgement and audit/trace state proved completion.**

The code should also make it obvious that the AMR domain/application core is independent of FastAPI, Firestore, Pub/Sub, ADK, Gemini, Gemma-family models, and Next.js.

If we cannot demonstrate both the product behavior and the architectural discipline truthfully, the MVP is not complete.
