# Ngabo — System Design

**Version:** 0.5  
**Date:** 2026-08-16  
**Status:** Hackathon MVP system design  
**Architecture:** Clean Architecture in a monorepo

---

## 1. Design Objective

Build the smallest production-minded architecture that demonstrates:

- event-driven AMR surveillance;
- deterministic scientific detection;
- Google ADK graph/workflow execution;
- bounded Gemini reasoning;
- zero-human completion of the canonical Taskmaster coordination workflow;
- safe autonomous action through a constrained A1 action envelope;
- real external action + machine acknowledgement;
- durable state, idempotency, freshness and observability;
- clear separation between AI orchestration and scientific/business truth.

---

## 2. Canonical Hero Flow

```text
synthetic WHONET-style data
        ↓
deterministic parser/normalizer
        ↓
Firestore canonical isolates
        ↓
deterministic surveillance detector
        ↓
surveillance.signal.detected
        ↓
Pub/Sub
        ↓
ngabo-core Cloud Run
        ↓
Google ADK workflow
        ↓
canonical context
        ↓
parallel deterministic fan-out
  ├─ resistance profile
  ├─ baseline summary
  └─ missing-field assessment
        ↓
join
        ↓
Gemini triage
        ↓
approved evidence retrieval
        ↓
Gemini synthesis
        ↓
deterministic package validation
  └─ bounded automatic repair if needed
        ↓
deterministic A0/A1/A2/A3 policy
        ↓
A1 safe coordination eligible
        ↓
freshness revalidation
        ↓
idempotency reservation
        ↓
NotificationPort
        ↓
real authorized external test/sandbox endpoint
        ↓
machine acknowledgement callback/event
        ↓
Firestore completion + audit
```

No human prompt/clarification/approval occurs in the hero flow.

---

## 3. Deployables

### `ngabo-web`

Cloud Run service providing:

- dashboard;
- import/demo controls;
- incident/autonomy timeline;
- graph/fan-out/join proof;
- package/evidence view;
- autonomy-policy/freshness state;
- external action/ack status;
- technical/evaluation proof drawer.

### `ngabo-core`

Cloud Run service providing:

- API/event interfaces;
- application workflows;
- deterministic surveillance core;
- Google ADK infrastructure;
- evidence/action adapters;
- persistence/event integration.

Monorepo does not imply monolith; these are independently deployable.

---

## 4. Clean Architecture

```text
Infrastructure / Frameworks
          ↓
Interfaces / Adapters
          ↓
Application / Use Cases / Ports
          ↓
Domain
```

### Domain/application

Own:

- canonical entities/value objects;
- deterministic surveillance;
- incident state policy;
- package validation rules/contracts;
- A0/A1/A2/A3 action policy;
- material-change/freshness policy;
- idempotency policy;
- workflows and ports.

### Infrastructure

Own:

- FastAPI;
- Firestore;
- Pub/Sub;
- Cloud Storage;
- Google ADK/Gemini;
- EmbeddingGemma/MedGemma adapters if implemented;
- external notification/action provider;
- Cloud logging/tracing.

---

## 5. Data / State Ownership

```text
Firestore
= canonical incident/workflow state

Cloud Storage
= raw immutable imports + large/file artifacts

ADK session/checkpoint
= execution continuity only

Pub/Sub
= event delivery, not workflow truth
```

Suggested canonical records:

- imports;
- isolates/AST results;
- surveillance signals;
- incidents;
- packages/versions;
- evidence references;
- graph/agent execution references;
- autonomy decisions;
- source watermarks;
- action/delivery records;
- acknowledgements;
- audit events;
- processed-event/idempotency records.

---

## 6. Deterministic Surveillance

Scientific calculations remain independent of model/cloud frameworks.

Persist:

- signal score/components;
- time/location concentration;
- phenotype similarity;
- baseline comparison;
- trigger explanation;
- algorithm/config version.

Signal means **investigation candidate**, not confirmed outbreak.

---

## 7. ADK Workflow Boundary

ADK lives in infrastructure and orchestrates inward application contracts.

```text
ADK workflow stage
→ application query/use case
→ domain calculation or port
→ typed result
```

Core stages:

1. context;
2. parallel deterministic investigation;
3. join;
4. Gemini triage;
5. evidence;
6. Gemini synthesis;
7. deterministic validation/repair;
8. autonomy policy;
9. freshness/idempotency;
10. external action;
11. machine acknowledgement.

Exact framework implementation must follow `docs/ADK_CAPABILITY_SPIKE.md`.

---

## 8. Action Safety Architecture

```text
A0 internal state              → autonomous
A1 safe external coordination  → autonomous after gates
A2 operational escalation      → blocked from public-v0.1 auto lane by default
A3 clinical/official decision  → always blocked from autonomous v0.1
```

Policy engine is deterministic application/domain logic.

A1 requires:

- valid package;
- evidence/source integrity;
- no material blocker;
- allow-listed authorized destination;
- safe claim boundary;
- freshness;
- idempotency.

Gemini has no direct notification capability.

---

## 9. Missing Information

Hero fixture contains all material fields.

Other scenarios:

```text
material missing → NEEDS_INFORMATION / no action
optional missing → UNKNOWN; continue only if A1 policy permits
```

No mandatory human clarification is part of v0.1 hero.

---

## 10. Automatic Package Repair

```text
Gemini package
→ deterministic validator
   ├─ pass → autonomy policy
   └─ fail → structured errors → Gemini repair → validator
```

Hard repair budget. No valid package → no action.

---

## 11. Evidence

Core can use deterministic/tag retrieval first.

Post-core optional:

```text
EvidenceSearchPort
→ EmbeddingGemma adapter
→ approved corpus only
→ source IDs/chunks/scores
```

MedGemma remains bounded/gated.

No arbitrary web page automatically becomes approved authority.

---

## 12. Freshness

Immediately before every A1 action:

- compare current incident/package/source version;
- detect material change;
- if changed, recompute/revalidate affected stages;
- rerun autonomy policy;
- act only on current state.

Freshness is autonomous safety, not merely review protection.

---

## 13. External Action / Ack

Preferred hero integration:

```text
NotificationPort
→ authorized external webhook/sandbox
→ delivery ID
→ machine acknowledgement callback/event
→ acknowledgement use case
→ incident completed
```

Callbacks/event endpoints must be authenticated/protected as appropriate.

Keep fake adapter for tests.

---

## 14. Failure / Retry

Handle:

- Pub/Sub redelivery;
- required graph branch failure;
- model timeout/error;
- evidence failure;
- package repair exhaustion;
- stale data;
- external send failure;
- acknowledgement timeout/replay;
- process restart.

State-changing operations idempotent; failures visible.

---

## 15. Observability

Correlate:

```text
correlation_id
incident_id
event_id
graph_run_id
node/branch/join IDs
agent session/invocation/run IDs
package_version
action_class
autonomy decision
freshness result
idempotency reference
delivery/ack IDs
retry/repair counts
```

No private chain-of-thought.

---

## 16. Security / Cost

- synthetic public data only;
- secrets via injected config/Secret Manager;
- internal/event/callback endpoints protected;
- action target allow-listed;
- no ADK Web in production;
- least privilege where practical;
- Cloud Run min `0` unless justified;
- max instance caps;
- budget alerts;
- bounded model/tool/repair attempts.

---

## 17. Hero E2E Acceptance

```text
manual prompts       = 0
human interventions  = 0
human steps          = 0
clarifications       = 0
approval clicks      = 0
external effects     = 1
machine acknowledgements = 1
```

Also prove A2/A3 actions are blocked and unsafe/missing-data scenarios abstain.

---

## 18. Diagram

See `docs/ARCHITECTURE_DIAGRAM.md` for the judge-facing visual. Update it to match final deployment before submission.
