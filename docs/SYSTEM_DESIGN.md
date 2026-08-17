# Ngabo — System Design

**Version:** 0.6  
**Date:** 2026-08-17  
**Status:** Hackathon MVP system design  
**Architecture:** Clean Architecture in a monorepo

---

## 1. Design Objective

Build the smallest production-minded architecture that demonstrates:

- event-driven AMR surveillance;
- deterministic scientific detection;
- Google ADK graph/workflow execution;
- bounded Gemini reasoning;
- **Proof-Carrying Autonomy**: action-relevant model claims carry machine-checkable references;
- deterministic claim/evidence verification before autonomous action;
- zero-human completion of the canonical Taskmaster coordination workflow;
- safe autonomous action through a constrained A1 action envelope;
- real external action + machine acknowledgement;
- durable state, freshness, transactional ActionIntent/outbox, idempotency and observability;
- clear separation between AI reasoning and scientific/business truth.

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
Gemini proof-carrying synthesis
        ↓
deterministic claim/evidence verifier
  ├─ invalid → structured errors → bounded repair → verify again
  └─ exhausted → autonomous abstention
        ↓
package/schema validation
        ↓
deterministic A0/A1/A2/A3 policy
        ↓
A1 safe coordination eligible
        ↓
freshness revalidation
        ↓
transactional ActionIntent + idempotency
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
- evidence + proof-carrying claim view;
- deterministic claim-verification status;
- autonomy-policy/freshness state;
- external action/ack status;
- technical/evaluation proof drawer.

### `ngabo-core`

Cloud Run service providing:

- API/event interfaces;
- application workflows;
- deterministic surveillance core;
- deterministic claim/policy verification core;
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

### Domain/application own

- canonical entities/value objects;
- deterministic surveillance;
- incident state policy;
- claim taxonomy/reference rules;
- deterministic claim verification contracts/services;
- package validation rules/contracts;
- A0/A1/A2/A3 action policy;
- material-change/freshness policy;
- ActionIntent/idempotency policy;
- workflows and ports.

### Infrastructure owns

- FastAPI;
- Firestore;
- Pub/Sub;
- Cloud Storage;
- Google ADK/Gemini;
- EmbeddingGemma/MedGemma adapters if implemented;
- external notification/action provider;
- Cloud logging/tracing.

Gemini/ADK must not own claim validity, action authority, canonical truth, or external side effects.

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
- deterministic findings + algorithm/config versions;
- incidents;
- packages/versions;
- typed reasoning claims;
- claim-verification reports/error codes;
- evidence references/manifests;
- graph/agent execution references;
- autonomy decisions;
- source watermarks;
- ActionIntents/delivery records;
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
- algorithm/config version;
- stable deterministic finding IDs that model claims can reference.

Signal means **investigation candidate**, not confirmed outbreak.

---

## 7. Proof-Carrying Reasoning Boundary

Gemini may interpret/hypothesize/synthesize, but action-relevant output must be structured claims equivalent to:

```text
claim_id
claim_type
statement
supporting_record_ids[]
supporting_finding_ids[]
supporting_source_ids[]
contradicting_claim_ids[]
uncertainties[]
requested_action_class
confidence_label
```

Supported claim types:

```text
OBSERVED_FACT
DERIVED_FINDING
EVIDENCE_STATEMENT
HYPOTHESIS
ACTION_JUSTIFICATION
```

`ACTION_JUSTIFICATION` does not authorize an action.

Forbidden v0.1 autonomous claim types include diagnosis, prescription, outbreak confirmation, mandatory containment authority, and official public-health declaration.

See `docs/PROOF_CARRYING_REASONING.md`.

---

## 8. Deterministic Claim Verification

After Gemini synthesis, application/domain logic verifies:

- referenced canonical records exist/current;
- referenced deterministic findings exist/current and belong to the incident/run;
- referenced evidence was actually retrieved and approved;
- observed facts do not rely solely on model inference;
- derived claims map to deterministic outputs;
- hypotheses stay labelled as hypotheses;
- unsupported/forbidden claim types/wording are rejected;
- required uncertainty/limitations are present where policy requires them;
- package/source/finding versions are not stale.

Unknown references fail deterministically.

Verifier output is a structured `ClaimVerificationReport` with stable error codes suitable for routing/evaluation.

---

## 9. ADK Workflow Boundary

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
6. Gemini proof-carrying synthesis;
7. deterministic claim/evidence verification;
8. bounded repair/abstention;
9. package/schema validation;
10. autonomy policy;
11. freshness + ActionIntent/idempotency;
12. external action;
13. machine acknowledgement.

Exact framework implementation follows `docs/ADK_CAPABILITY_SPIKE.md`.

---

## 10. Action Safety Architecture

```text
A0 internal state              → autonomous
A1 safe external coordination  → autonomous after gates
A2 operational escalation      → blocked from public-v0.1 auto lane by default
A3 clinical/official decision  → always blocked from autonomous v0.1
```

Policy engine is deterministic application/domain logic.

A1 requires:

- valid current package;
- claim verification passed;
- evidence/source integrity;
- no material blocker;
- allow-listed authorized destination;
- safe claim boundary;
- freshness;
- durable ActionIntent + idempotency.

Gemini has no direct notification capability.

---

## 11. Missing Information

Hero fixture contains all material fields.

Other scenarios:

```text
material missing → NEEDS_INFORMATION / no action
optional missing → UNKNOWN; continue only if A1 policy permits
```

No mandatory human clarification is part of v0.1 hero.

---

## 12. Bounded Proof/Package Repair

```text
Gemini proof-carrying package
→ deterministic verifier
   ├─ pass → package/action policy
   └─ fail → structured errors → Gemini repair → verifier
```

Controls:

- hard repair budget (target `2`);
- repair cannot mutate canonical facts/deterministic findings/action policy;
- new evidence only through explicit approved retrieval path;
- no valid verified package → no action.

---

## 13. Evidence

Core can use deterministic/tag retrieval first.

Post-core optional:

```text
EvidenceSearchPort
→ EmbeddingGemma adapter
→ approved corpus only
→ source IDs/chunks/scores
```

Every evidence statement must reference actually retrieved approved evidence. A URL generated by the model is never authority.

MedGemma remains bounded/gated.

---

## 14. Freshness

Immediately before every A1 action:

- compare current incident/package/source versions/watermark;
- detect material change;
- if changed, recompute/reverify/revalidate affected stages;
- rerun autonomy policy;
- act only on current state.

Freshness is autonomous safety, not merely review protection.

---

## 15. ActionIntent / Outbox / Idempotency

Before every autonomous external effect, persist a durable immutable `ActionIntent` bound to:

- incident/package/source versions;
- action class/policy version;
- target;
- payload hash;
- stable idempotency key.

Dispatcher/receiver semantics follow `docs/AUTONOMOUS_EFFECT_OUTBOX.md`.

Claim accurately as **exactly-once Ngabo intent plus idempotent external execution**, not universal exactly-once network delivery.

---

## 16. External Action / Ack

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

## 17. Failure / Retry

Handle:

- Pub/Sub redelivery;
- required graph branch failure;
- model timeout/error;
- evidence failure;
- malformed/unsupported proof references;
- proof/repair exhaustion;
- stale data;
- external send failure;
- ambiguous crash window around external side effect;
- acknowledgement timeout/replay;
- process restart.

State-changing operations idempotent; failures visible.

---

## 18. Observability

Correlate:

```text
correlation_id
incident_id
event_id
graph_run_id
node/branch/join IDs
agent session/invocation/run IDs
package_version
claim_count
claim type counts
claim verification status/error codes
reasoning repair count
action_class
autonomy decision
freshness result
action_intent_id
idempotency reference
delivery/ack IDs
retry counts
```

No private chain-of-thought.

---

## 19. Security / Cost

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

## 20. Hero E2E Acceptance

```text
manual prompts             = 0
human interventions        = 0
human steps                = 0
clarifications             = 0
approval clicks            = 0
claim verification         = passed
logical ActionIntents      = 1
external effects           = 1
machine acknowledgements   = 1
```

Also prove:

- fabricated record/finding/source references are rejected;
- hypothesis/forbidden-claim escalation is blocked;
- failed claim verification never reaches A1 action;
- A2/A3 actions are blocked;
- unsafe/missing-data scenarios abstain;
- freshness/idempotency protect external action.

---

## 21. Diagram

See `docs/ARCHITECTURE_DIAGRAM.md` for the judge-facing visual. Update it to match final deployment before submission.
