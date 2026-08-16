# Ngabo — Implementation Plan

**Version:** 0.7  
**Created:** 2026-08-16  
**Official hackathon deadline:** 2026-08-31, 5:00 PM Pacific Time

---

## 1. Principle

> **Build the zero-human Taskmaster hero first. Everything else is secondary.**

The canonical hero must complete:

```text
surveillance event
→ autonomous investigation
→ validated package
→ safe A1 external action
→ machine acknowledgement
```

with:

```text
human_intervention_count == 0
manual_prompt_count_to_start == 0
clarification_count == 0
approval_click_count == 0
```

All implementation preserves:

- Clean Architecture;
- monorepo boundaries;
- deterministic scientific logic;
- graph-first hybrid orchestration;
- zero-human A1 safe action policy;
- bounded agentic reasoning;
- freshness/idempotency;
- safe abstention;
- Gitflow/SemVer/Conventional Commits;
- submission evidence and freeze discipline.

Required read set includes:

- `docs/HACKATHON_ALIGNMENT.md`
- `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`
- `docs/BYOF_FRICTION.md`
- `docs/ADK_CAPABILITY_SPIKE.md`
- `docs/HACKATHON_RISK_REGISTER.md`
- `docs/ORCHESTRATION_PATTERNS.md`
- `docs/LONG_RUNNING_AGENT.md`
- `docs/DATA_SAFETY_EVALUATION.md`
- `docs/OPERATIONAL_UTILITY_EVALUATION.md`
- `docs/SUBMISSION_EVIDENCE.md`
- `docs/SUBMISSION_FREEZE.md`

---

## 2. Critical Path

```text
Clean Architecture scaffold
   ↓
domain/state/action-policy core
   ↓
synthetic data + complete hero fixture
   ↓
deterministic ingestion
   ↓
deterministic surveillance detector
   ↓
ADK capability spike + version pin
   ↓
deterministic investigation capabilities
   ↓
ADK workflow: context → parallel fan-out → join
   ↓
Gemini triage + evidence + synthesis
   ↓
deterministic package validator + bounded auto repair
   ↓
A0/A1/A2/A3 autonomous action policy
   ↓
freshness + idempotency
   ↓
real A1 external integration
   ↓
machine acknowledgement
   ↓
zero-human deployed E2E
   ↓
Next.js autonomy/graph proof UI
   ↓
GCP deployment + observability
   ↓
scientific/agent/safety/utility evaluation
   ↓
EmbeddingGemma if core green
   ↓
diagram + article + video + submission freeze
```

---

## Aug 16 — Freeze Competition Architecture

Completed design controls should include:

- [x] product/PRD/tech/system/agent/UI specifications;
- [x] Clean Architecture + monorepo ADR;
- [x] hackathon alignment;
- [x] graph-first orchestration;
- [x] long-running state/freshness contract;
- [x] zero-human Taskmaster autonomy contract;
- [x] BYOF friction contract;
- [x] operational-utility benchmark contract;
- [x] provenance/submission evidence contracts;
- [x] ADK capability-spike contract;
- [x] submission-freeze contract;
- [x] hackathon risk register;
- [x] judge-facing target architecture diagram.

**Exit:** implementation can start without guessing Taskmaster autonomy or safety boundaries.

---

## Aug 17 — Monorepo Scaffold + Domain Core + Action Policy

### Repository

- [ ] `apps/web`;
- [ ] `services/core`;
- [ ] `data/{synthetic,schemas,guidance}`;
- [ ] `infra`;
- [ ] pnpm workspace;
- [ ] uv Python project;
- [ ] lint/type/test scripts;
- [ ] `.env.example`.

### Backend layers

```text
services/core/ngabo/
├── domain/
├── application/
├── interfaces/
├── infrastructure/
└── bootstrap/
```

### Domain/application model

- [ ] ImportBatch;
- [ ] Isolate;
- [ ] ASTResult;
- [ ] SurveillanceSignal;
- [ ] Incident;
- [ ] IncidentEvent;
- [ ] package/version metadata;
- [ ] action classes `A0/A1/A2/A3`;
- [ ] `AutonomyDecision` value object;
- [ ] incident state machine;
- [ ] state-transition tests;
- [ ] action-class policy tests;
- [ ] A2/A3 cannot auto-execute.

**Exit:** domain/application build without FastAPI/GCP/ADK/Gemini and action policy is deterministic.

---

## Aug 18 — Synthetic Data + Deterministic Ingestion

Create fixtures:

- [ ] complete zero-human hero dataset;
- [ ] normal baseline;
- [ ] noisy/malformed dataset;
- [ ] material-missing-data abstention fixture;
- [ ] prompt-injection-as-data fixture;
- [ ] stale-before-action fixture;
- [ ] A2/A3 policy-block fixtures.

Implement:

- [ ] canonical schema;
- [ ] parser/normalizer;
- [ ] duplicate handling;
- [ ] file hashing;
- [ ] file storage port;
- [ ] import use case;
- [ ] thin FastAPI import adapter;
- [ ] validation report.

**Hero rule:** no intentionally missing material field.

**Exit:** hero CSV → complete canonical isolates without human repair.

---

## Aug 19 — Deterministic Surveillance Engine

- [ ] resistance representation;
- [ ] similarity method;
- [ ] temporal concentration;
- [ ] ward/location concentration;
- [ ] baseline comparison;
- [ ] prototype signal score;
- [ ] trigger explanation;
- [ ] surveillance use case;
- [ ] scenario tests;
- [ ] signal event contract.

**Exit:** hero dataset creates expected suspicious investigation candidate deterministically.

---

## Aug 20 Morning — ADK Capability Spike

Before production graph code, complete `docs/ADK_CAPABILITY_SPIKE.md`.

- [ ] pin exact Python version;
- [ ] pin exact `google-adk` version;
- [ ] verify backend invocation without chat;
- [ ] verify sequential/parallel supported path;
- [ ] verify join/failure semantics;
- [ ] verify structured Gemini output;
- [ ] verify callback/session/eval/trace capabilities;
- [ ] choose documented fallback if workshop graph API differs;
- [ ] record result;
- [ ] commit lockfile.

**Stop condition:** do not build runtime against guessed workshop APIs.

---

## Aug 20–21 — Investigation Capabilities + ADK Workflow

### Inner contracts

- [ ] incident-context query;
- [ ] profile-comparison query;
- [ ] baseline-summary query;
- [ ] missing-fields query;
- [ ] evidence-search port;
- [ ] incident-package schema;
- [ ] package validator;
- [ ] autonomy-policy use case;
- [ ] freshness use case;
- [ ] agent execution metadata contract.

### ADK infrastructure

- [ ] ADK outer adapter under `infrastructure/ai/adk`;
- [ ] context stage;
- [ ] parallel deterministic profile/baseline/missingness stages;
- [ ] join;
- [ ] Gemini 3.6 Flash triage;
- [ ] approved evidence retrieval;
- [ ] Gemini synthesis;
- [ ] bounded model/tool/time budgets;
- [ ] structured telemetry IDs.

### No-human hero behavior

- [ ] no clarification tool in required hero route;
- [ ] material missingness causes autonomous abstention;
- [ ] fixed routing does not call Gemini;
- [ ] hero complete fixture proceeds automatically.

**Exit:** pre-created hero signal → valid evidence-backed package without user input.

---

## Aug 22 — Deterministic Validation + Automatic Repair + Event Persistence

### Package validation

Reject:

- unknown isolate/source IDs;
- unsupported observed/derived claims;
- prohibited prescribing/diagnosis/outbreak confirmation;
- malformed/missing required schema;
- unsafe action wording.

### Bounded repair

- [ ] structured validator errors;
- [ ] Gemini repair attempt;
- [ ] hard max attempts (target `2`);
- [ ] exhausted budget → `VALIDATION_FAILED`;
- [ ] invalid package can never reach action policy.

### Persistence/events

- [ ] Firestore repositories;
- [ ] GCS store;
- [ ] Pub/Sub publisher/consumer;
- [ ] processed-event/idempotency persistence;
- [ ] append-only timeline;
- [ ] graph/session/run correlation;
- [ ] restart/redelivery tests.

**Exit:** event processing is durable/idempotent and model errors can self-repair or stop safely.

---

## Aug 23 — Zero-Human Autonomous Action + Machine Ack

### Policy engine

- [ ] deterministic A0/A1/A2/A3 classification;
- [ ] allow-listed target policy;
- [ ] authorization config;
- [ ] A2/A3 hard block;
- [ ] safe abstention states.

### Freshness

- [ ] incident/package/source watermark;
- [ ] pre-action deterministic revalidation;
- [ ] material change → recompute/revalidate;
- [ ] no stale external action.

### Idempotency

- [ ] action idempotency key/reservation;
- [ ] delivery attempt/result persistence;
- [ ] retry behavior;
- [ ] duplicate event cannot duplicate action.

### Real external integration

Preferred:

```text
NotificationPort
→ authorized external test/sandbox webhook
→ delivery result
→ machine acknowledgement callback/event
```

- [ ] real adapter;
- [ ] local fake adapter kept for tests;
- [ ] external delivery ID;
- [ ] automated acknowledgement;
- [ ] acknowledgement updates incident;
- [ ] hero E2E requires no person.

**Exit:** backend hero flow completes event→ack with zero human intervention.

---

## Aug 24–25 — Next.js Incident / Autonomy Console

Required views:

- [ ] synthetic-data banner;
- [ ] dashboard/import/signal;
- [ ] incident detail;
- [ ] deterministic why-flagged card;
- [ ] resistance comparison;
- [ ] graph timeline;
- [ ] fan-out/branch/join visibility;
- [ ] bounded Gemini/evidence stages;
- [ ] package validation/repair state;
- [ ] autonomy-policy card;
- [ ] A1 vs blocked A2/A3 state;
- [ ] freshness/idempotency state;
- [ ] real action + delivery ID;
- [ ] machine acknowledgement;
- [ ] zero-human operational metrics card;
- [ ] developer/details drawer;
- [ ] failure/abstention states;
- [ ] demo reset/seed control.

Do not make chat or human approval the hero interaction model.

**Exit:** judge can understand the zero-human workflow from UI alone.

---

## Aug 26 — GCP Deployment + Observability + Security/Cost

- [ ] Cloud Run `ngabo-core`;
- [ ] Cloud Run `ngabo-web`;
- [ ] Firestore;
- [ ] Pub/Sub;
- [ ] GCS;
- [ ] Secret Manager/injected secrets;
- [ ] protected event/callback endpoints;
- [ ] allow-listed external target config;
- [ ] min instances `0` unless justified;
- [ ] max instance caps;
- [ ] budget + email alert;
- [ ] structured Cloud Logging;
- [ ] graph/node/model/action/freshness/ack telemetry;
- [ ] supported Trace/OpenTelemetry path if stable;
- [ ] metadata-first content policy.

**Exit:** full hero works on GCP and provides visible proof.

---

## Aug 27 — Evaluation + Operational Utility + EmbeddingGemma Gate

### Hero E2E

Run three consecutive deployed hero scenarios.

Required:

```text
manual_prompt_count_to_start = 0
human_intervention_count = 0
human_active_steps = 0
clarification_count = 0
approval_click_count = 0
external_effect_count = 1
acknowledgement_count = 1
```

### Safety/architecture eval

- [ ] deterministic node tests;
- [ ] fan-out order independence;
- [ ] required branch failure;
- [ ] zero model calls for fixed routing;
- [ ] prompt injection;
- [ ] fabricated source/isolate;
- [ ] package auto-repair;
- [ ] repair budget exhaustion;
- [ ] material missingness abstention;
- [ ] A2/A3 blocks;
- [ ] non-allow-listed target block;
- [ ] freshness recompute;
- [ ] duplicate/redelivery idempotency;
- [ ] session/canonical truth conflict;
- [ ] restart/recovery.

### Operational utility / BYOF

- [ ] freeze reference builder workflow;
- [ ] measure human active steps;
- [ ] capture event→package/action/ack timings;
- [ ] model/node/repair/retry counts;
- [ ] write public `EVALUATION.md`.

### EmbeddingGemma

Only if core hero/evals are green:

- [ ] precompute approved corpus embeddings;
- [ ] adapter behind `EvidenceSearchPort`;
- [ ] lightweight similarity retrieval;
- [ ] retrieval eval/provenance;
- [ ] claim bonus only if real.

---

## Aug 28 — Judge-Facing Technical Story

- [ ] reconcile `docs/ARCHITECTURE_DIAGRAM.md` to deployed runtime;
- [ ] export high-resolution diagram if needed;
- [ ] update README spin-up instructions;
- [ ] record exact ADK/Gemini/GCP versions;
- [ ] complete provenance register;
- [ ] prepare operational benchmark card;
- [ ] draft final Devpost BYOF story;
- [ ] draft LinkedIn article with required hackathon-purpose statement;
- [ ] verify bonus evidence requirements.

---

## Aug 29 — Demo Rehearsal + Risk Closure

Use `docs/HACKATHON_RISK_REGISTER.md`.

- [ ] rehearse <=4 min;
- [ ] continuous unedited hero segment has no human input;
- [ ] external action visible outside Ngabo;
- [ ] machine acknowledgement returns visibly;
- [ ] Cloud Run/log proof legible;
- [ ] architecture diagram readable;
- [ ] BYOF friction clear in first 30 sec;
- [ ] no unimplemented feature/model shown;
- [ ] no clinical overclaiming;
- [ ] fix all Critical/High risks that can be closed before freeze.

Optional MedGemma/multimodal work only if everything above is stable and time remains.

---

## Aug 30 — Release Candidate / Submission Freeze

Follow `docs/SUBMISSION_FREEZE.md`.

```text
develop
→ release/v0.1.0
→ main
→ tag v0.1.0
```

- [ ] record submitted commit SHA;
- [ ] record Cloud Run revisions;
- [ ] pin deployed URLs to tested revisions;
- [ ] final `EVALUATION.md` committed;
- [ ] final diagram committed/exported;
- [ ] final claim ledger complete;
- [ ] third-party/provenance complete;
- [ ] video recorded/uploaded/tested public;
- [ ] hosted reset path tested;
- [ ] judge-access smoke test;
- [ ] article/social URLs captured if published;
- [ ] remove claims for any incomplete optional feature.

---

## Aug 31 — Submit, Verify, Freeze

- [ ] final official-rule re-check;
- [ ] Devpost category Taskmaster;
- [ ] hosted URL/repo/video entered;
- [ ] spin-up instructions visible;
- [ ] architecture diagram included;
- [ ] Google Cloud proof in video;
- [ ] BYOF narrative explicit;
- [ ] zero-human claim matches actual E2E evidence;
- [ ] bonuses claimed only with proof;
- [ ] submit before deadline buffer;
- [ ] verify Devpost submission from clean browser;
- [ ] preserve `main`/tag/deployed revisions/video through judging.

---

## 3. Scope Freeze

Until zero-human deployed hero + evaluation are green, do **not** add:

- MedGemma;
- collaborative specialist-agent topology;
- runtime-generated dynamic topology;
- multimodal ingestion;
- genomics/AMRFinderPlus;
- vector database;
- GKE;
- Redis/Kafka;
- LangGraph;
- mobile app;
- real patient data;
- real hospital connector;
- A2/A3 autonomous action.

EmbeddingGemma is the first optional integration after the core passes.

---

## 4. Final Definition of Done

The hackathon build is complete only when a judge can truthfully observe:

> **AMR data changed → deterministic Ngabo logic detected a signal → Pub/Sub started the Google ADK workflow → deterministic investigation stages ran in parallel and joined → Gemini reasoned only where needed → approved evidence was assembled → the package passed deterministic validation (and repaired itself if needed) → Ngabo's deterministic safety policy classified the action as safe A1 → freshness/idempotency passed → Ngabo executed a real authorized external action → a machine acknowledgement returned → the workflow completed with zero human intervention.**

And the repository proves that A2/A3 clinical/official actions cannot be autonomously executed merely because the hero path is fully autonomous.
