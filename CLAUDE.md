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
7. `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`
8. `docs/BYOF_FRICTION.md`
9. `docs/ADK_CAPABILITY_SPIKE.md`
10. `docs/ADK_RUNTIME.md`
11. `docs/ORCHESTRATION_PATTERNS.md`
12. `docs/LONG_RUNNING_AGENT.md`
13. `docs/SYSTEM_DESIGN.md`
14. `docs/AGENT_ARCHITECTURE.md`
15. `docs/DATA_SAFETY_EVALUATION.md`
16. `docs/OPERATIONAL_UTILITY_EVALUATION.md`
17. `docs/UI_UX_SPEC.md`
18. `docs/UI_UX_HACKATHON_ADDENDUM.md`
19. `docs/ARCHITECTURE_DIAGRAM.md`
20. `docs/THIRD_PARTY_PROVENANCE.md`
21. `docs/SUBMISSION_EVIDENCE.md`
22. `docs/SUBMISSION_FREEZE.md`
23. `docs/HACKATHON_RISK_REGISTER.md`
24. `docs/IMPLEMENTATION_PLAN.md`
25. relevant ADRs, especially ADR 0005 and ADR 0006.

Also read `AGENTS.md` and `CHANGELOG.md` before release-oriented work.

### Conflict precedence

```text
Official hackathon rules
        ↓
Safety / data / provenance constraints
        ↓
THIS FILE + TASKMASTER_ZERO_HUMAN_AUTONOMY
        ↓
PRD / Clean Architecture
        ↓
Hackathon / ADK / orchestration / long-running contracts
        ↓
Evaluation / UI / implementation documents
```

**Important amendment:** `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md` supersedes older v0.1 wording that required human approval or clarification inside the canonical hackathon hero flow. Human-governed consequential clinical/public-health lanes remain valid future/real-world architecture, but the hero A1 coordination workflow is zero-human.

---

## 2. Product Definition

Ngabo is an **open-source, event-driven antimicrobial-resistance surveillance and incident-response system**.

Current maturity:

> `v0.1.0` hackathon MVP in development.

Do not define the permanent product identity as “a prototype.”

Ngabo is not a chatbot. The web application is an incident/autonomy console.

---

## 3. Canonical Taskmaster Hero — Non-Negotiable

The submitted hero must complete:

```text
synthetic AMR signal
→ Pub/Sub event
→ Google ADK workflow
→ deterministic fan-out/join
→ bounded Gemini triage
→ approved evidence retrieval
→ Gemini synthesis
→ deterministic validation / bounded auto repair
→ deterministic A1 autonomy policy
→ freshness
→ idempotency
→ real authorized external action
→ machine acknowledgement
```

with:

```text
manual_prompt_count_to_start == 0
human_intervention_count == 0
human_active_steps == 0
clarification_count == 0
approval_click_count == 0
```

Do not reintroduce mandatory human input into the hero path merely because ADK supports human-in-the-loop patterns.

---

## 4. Safety Through Constrained Autonomy — Non-Negotiable

Zero-human hero autonomy does **not** authorize autonomous diagnosis, prescribing, official outbreak confirmation or irreversible real-world clinical/public-health intervention.

Action classes:

```text
A0 INTERNAL_STATE
→ autonomous

A1 SAFE_EXTERNAL_COORDINATION
→ autonomous after deterministic gates

A2 REAL_OPERATIONAL_ESCALATION
→ outside autonomous public-v0.1 envelope unless separately authorized

A3 CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION
→ forbidden as autonomous v0.1 action
```

The hero uses A1 only.

Examples of acceptable A1 hero action:

- authorized test/sandbox webhook;
- authorized internal/test inbox;
- external sandbox incident/ticket creation;
- machine-readable coordination payload.

Payload must clearly say investigation candidate/synthetic demo and must not claim diagnosis, treatment or confirmed outbreak.

**Gemini may not decide the final executable action class or waive policy.**

---

## 5. Autonomous Safety Gate

Before A1 execution, deterministic application logic must verify:

1. canonical data valid;
2. signal valid;
3. required graph branches succeeded;
4. no material A1 blocker;
5. approved evidence/source integrity valid;
6. package schema/claim validation passed;
7. action class is A1;
8. destination allow-listed/authorized;
9. current state passes freshness validation;
10. idempotency reservation acquired.

Any failure → safe abstention/recompute. Never ask Gemini to “decide it is safe enough.”

---

## 6. Missing Data / No Clarification Hero Rule

The hero fixture contains all material fields needed for A1 completion.

For other scenarios:

```text
material fact missing → NEEDS_INFORMATION → no external action
optional fact missing → keep UNKNOWN; continue only if policy permits
recoverable canonical fact → retrieve from authorized source if deterministic linkage exists
```

Never hallucinate a clinical fact to avoid a human question.

Pause/resume remains an eval/engineering capability, not a required hero interaction.

---

## 7. Clean Architecture — Non-Negotiable

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

### Domain/application own

- AMR entities/value objects;
- deterministic surveillance;
- incident state policy;
- action-class policy;
- freshness/material-change policy;
- package/claim validation contracts;
- idempotency policy;
- application workflows/ports.

### Infrastructure owns

- FastAPI adapters;
- Firestore/GCS/PubSub adapters;
- Google ADK;
- Gemini;
- EmbeddingGemma/optional MedGemma;
- external action adapters;
- tracing/logging.

Forbidden dependency smells:

```text
domain -> FastAPI/GCP/ADK/Gemini
application -> concrete Firestore/Gemini/ADK SDK
ADK node -> raw DB + duplicated business logic
Gemini -> direct external action
React -> Firestore/PubSub/Gemini/ADK
```

---

## 8. Monorepo — Non-Negotiable

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

Do not split repos/create extra services casually.

---

## 9. Deterministic vs Agentic Responsibility

Governing rule:

> **Deterministic when the workflow is known; agentic when the decision is ambiguous; dynamic only when the workflow itself cannot reasonably be known in advance.**

### Deterministic

- parsing/schema/normalization;
- AST calculations;
- similarity;
- temporal/location windows;
- baseline/scoring;
- structural missingness;
- fixed routing/state transitions;
- fan-out/join semantics;
- package validation;
- action classification;
- allow-list authorization;
- freshness;
- idempotency;
- acknowledgement state transition.

### Gemini

- reason across joined findings;
- bounded evidence intent where ambiguous;
- source-grounded hypothesis/synthesis;
- structured package drafting;
- bounded repair from deterministic validator errors;
- stop with uncertainty when evidence insufficient.

Gemini must not own fixed policy merely to make the workflow look agentic.

---

## 10. Google ADK Runtime

Before production ADK implementation, complete `docs/ADK_CAPABILITY_SPIKE.md`.

Pin exact dependency and verify supported APIs.

Preferred conceptual flow:

```text
signal event
→ context
→ parallel deterministic profile/baseline/missingness
→ join
→ Gemini triage
→ evidence
→ Gemini synthesis
→ deterministic validation
```

If workshop first-class graph/function/join terminology differs from the exact package, use the documented fallback ladder:

1. supported first-class ADK workflow/graph primitives;
2. supported Sequential/Parallel/workflow agents + deterministic adapters;
3. application-owned deterministic workflow invoking bounded ADK model-agent boundaries.

Do **not** add LangGraph merely to match a workshop abstraction.

ADK remains outer infrastructure.

---

## 11. Automatic Package Repair

On deterministic validation failure:

```text
validator errors
→ bounded Gemini repair
→ validator
```

Suggested max attempts: `2`.

Rules:

- model cannot override validator;
- invalid package never reaches action;
- exhausted budget → `VALIDATION_FAILED`;
- repair telemetry is visible.

---

## 12. Evidence

Evidence corpus is curated/provenance-recorded.

Generated package may cite only retrieved approved source IDs.

No arbitrary URL becomes authority automatically.

EmbeddingGemma is planned only after core hero is green and must remain behind `EvidenceSearchPort`.

MedGemma is gated stretch; keep only if evaluation proves value.

---

## 13. Long-Running State / Truth

```text
Firestore/application state = canonical incident truth
ADK session/checkpoint      = execution continuity
transient context           = recomputable working values
Cloud Storage               = file/large artifacts
model memory                = not authoritative v0.1 AMR truth
```

After restart/resume, rebuild current context from canonical state.

Compaction/session history cannot redefine isolate/AST facts, source IDs, package versions or policy.

Freshness protection applies to **all external A1 action**, not only human-approved actions.

---

## 14. Real External Action / Ack

Hosted/filmed hero must perform a real authorized A1 action outside Ngabo.

Preferred:

```text
NotificationPort
→ external test/sandbox endpoint
→ delivery ID/result
→ machine acknowledgement callback/event
→ Ngabo state update
```

Keep local fake adapter for automated tests.

Never contact real hospital/person without explicit authorization.

---

## 15. Observability

Capture safe metadata:

```text
correlation_id
incident_id
event_id
graph_run_id
node_name/node_type
branch_id/join_id
agent_session_id/invocation_id/run_id
model_name
incident_version/package_version
action_class
autonomy_policy_result
freshness_result
idempotency_reference
delivery_id
acknowledgement_id
retry_count
repair_attempt_count
```

No private chain-of-thought.

---

## 16. Evaluation

### Hero assertions

```text
0 prompts
0 human interventions
0 human steps
0 clarifications
0 approval clicks
1 external effect
1 machine acknowledgement
```

Run at least three consecutive successful deployed hero scenarios before freeze.

### Safety

Test:

- material missing fact → abstain;
- A2/A3 → block;
- non-allow-listed target → block;
- prompt injection → no instruction takeover;
- fabricated source/isolate → reject;
- invalid package → repair/stop;
- repair budget exhaustion → stop;
- stale state → recompute;
- duplicate event/retry → one effect;
- stale session conflict → canonical state wins.

Create real public `EVALUATION.md` before submission.

---

## 17. UI Contract

Read `docs/UI_UX_SPEC.md` + `docs/UI_UX_HACKATHON_ADDENDUM.md`.

Hero UI must show:

- autonomous event start;
- deterministic fan-out/join;
- bounded agent/evidence stages;
- validation/repair;
- A1 autonomy-policy card;
- freshness/idempotency;
- real delivery;
- machine acknowledgement;
- zero-human metrics.

Do not put chat, clarification or approval click in the hero sequence.

---

## 18. BYOF / Operational Utility

Use `docs/BYOF_FRICTION.md`.

The first-person friction is the builder's repeated AMR research/coordination workflow—not borrowed clinical identity.

Measure reference human steps against zero-human Ngabo hero in `docs/OPERATIONAL_UTILITY_EVALUATION.md`.

Do not manufacture hospital time-saved or clinical benefit claims.

---

## 19. Cloud / Security / Cost

Required:

- Cloud Run web/core;
- Firestore/PubSub/GCS;
- Secret Manager/injected secrets;
- protected event/ack endpoints;
- allow-listed action target;
- min instances `0` unless justified;
- max caps;
- budget alert;
- least privilege where practical;
- metadata-first logging/tracing;
- judge-accessible hosted release.

---

## 20. Submission Discipline

Required docs:

- `docs/ARCHITECTURE_DIAGRAM.md`;
- `docs/SUBMISSION_EVIDENCE.md`;
- `docs/SUBMISSION_FREEZE.md`;
- `docs/THIRD_PARTY_PROVENANCE.md`;
- `docs/HACKATHON_RISK_REGISTER.md`.

Never claim a feature/model/evaluation/deployment that exists only in docs.

Freeze `main`, tag, Cloud Run revisions, video and claim ledger for judging.

---

## 21. Implementation Order

1. scaffold/domain/state/action policy;
2. complete hero synthetic data;
3. deterministic ingest;
4. deterministic detector;
5. ADK capability spike + version pin;
6. deterministic investigation capabilities;
7. ADK workflow/fan-out/join;
8. Gemini triage/evidence/synthesis;
9. deterministic validation + auto repair;
10. A1 policy + freshness + idempotency;
11. real external action + machine ack;
12. zero-human backend E2E;
13. UI/autonomy proof;
14. GCP deploy/observability;
15. evaluation/BYOF benchmark;
16. EmbeddingGemma if core green;
17. diagram/article/video/submission freeze;
18. only then consider MedGemma/multimodal.

---

## 22. Scope Freeze

Until zero-human deployed hero is green, do not add:

- MedGemma;
- specialist-agent fleet;
- dynamic workflow topology;
- multimodal ingestion;
- genomics;
- vector DB;
- GKE/Redis/Kafka/LangGraph;
- real patient data;
- real hospital integration;
- A2/A3 autonomous action.

---

## 23. Stop Conditions

Stop and surface the issue when:

- official rules conflict with assumptions;
- exact ADK API is unverified;
- dependency direction inverts Clean Architecture;
- Gemini is being asked to own deterministic safety policy;
- hero path requires human clarification/approval;
- someone proposes fabricating missing clinical data to keep zero-human flow;
- action is not A1/allow-listed/authorized;
- external side effect lacks idempotency;
- package can bypass validation;
- a bonus threatens core reliability;
- submission claim lacks evidence.

---

## 24. Final Product Standard

A judge should be able to truthfully see:

> **new AMR data arrived → deterministic logic detected a signal → Pub/Sub started Ngabo automatically → deterministic investigation work ran in parallel and joined → Gemini reasoned only where ambiguity existed → approved evidence was assembled → the package was deterministically validated and automatically repaired if necessary → a deterministic policy classified the action as safe A1 → freshness/idempotency passed → Ngabo executed a real authorized external action → a machine acknowledgement returned → the workflow completed with zero human intervention.**

And the code/evals must make equally obvious that clinical/official A2/A3 actions are not autonomously permitted merely because the hero flow is fully autonomous.
