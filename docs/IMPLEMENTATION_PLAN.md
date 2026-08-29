# Ngabo — Implementation Plan

**Version:** 0.8  
**Created:** 2026-08-16  
**Updated:** 2026-08-29  
**Official hackathon deadline:** 2026-08-31, 5:00 PM Pacific Time

---

## 1. Principle

> **Build the zero-human Taskmaster hero first. Everything else is secondary.**

The canonical hero must complete:

```text
surveillance event
→ autonomous investigation
→ proof-carrying synthesis
→ deterministic claim verification
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
- **Proof-Carrying Autonomy**;
- bounded Gemini reasoning;
- deterministic claim/evidence verification;
- bounded repair and safe abstention;
- freshness + ActionIntent/outbox/idempotency;
- Gitflow/SemVer/Conventional Commits;
- submission evidence and freeze discipline.

Required read set includes:

- `docs/LEAN_CANVAS.md`
- `docs/COMPETITOR_ANALYSIS.md`
- `docs/VALUE_PROPOSITION_CANVAS.md`
- `docs/HACKATHON_ALIGNMENT.md`
- `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`
- `docs/PROOF_CARRYING_REASONING.md`
- `docs/BYOF_FRICTION.md`
- `docs/ADK_CAPABILITY_SPIKE.md`
- `docs/HACKATHON_RISK_REGISTER.md`
- `docs/ORCHESTRATION_PATTERNS.md`
- `docs/ADK_RUNTIME.md`
- `docs/LONG_RUNNING_AGENT.md`
- `docs/AUTONOMOUS_EFFECT_OUTBOX.md`
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
proof-carrying claim taxonomy + verifier contracts
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
Gemini triage + approved evidence
   ↓
Gemini proof-carrying synthesis
   ↓
deterministic claim/evidence verifier
   ↓
bounded automatic repair / abstention
   ↓
A0/A1/A2/A3 autonomous action policy
   ↓
freshness + transactional ActionIntent/outbox/idempotency
   ↓
real A1 external integration
   ↓
machine acknowledgement
   ↓
zero-human deployed E2E
   ↓
Next.js autonomy/graph/proof UI
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

## Aug 16–17 — Freeze Competition Architecture

Completed design controls:

- [x] product/PRD/tech/system/agent/UI specifications;
- [x] Clean Architecture + monorepo ADR;
- [x] hackathon alignment;
- [x] graph-first orchestration;
- [x] long-running state/freshness contract;
- [x] zero-human Taskmaster autonomy contract;
- [x] transactional autonomous-effect/outbox contract;
- [x] BYOF friction contract;
- [x] operational-utility benchmark contract;
- [x] provenance/submission evidence contracts;
- [x] ADK capability-spike contract;
- [x] submission-freeze contract;
- [x] hackathon risk register;
- [x] judge-facing target architecture diagram;
- [x] Proof-Carrying Reasoning contract + ADR 0009;
- [x] competition “Twist” explicitly defined as **Proof-Carrying Autonomy**.

**Exit:** implementation can start without guessing Taskmaster autonomy, safety, or model-trust boundaries.

---

## Aug 17 — Monorepo Scaffold + Domain Core + Proof Contracts

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

- [ ] `ImportBatch`;
- [ ] `Isolate`;
- [ ] `ASTResult`;
- [ ] `SurveillanceSignal`;
- [ ] `Incident`;
- [ ] `IncidentEvent`;
- [ ] package/version metadata;
- [ ] action classes `A0/A1/A2/A3`;
- [ ] `AutonomyDecision` value object;
- [ ] incident state machine;
- [ ] proof-carrying `ClaimType` enum/value object;
- [ ] `ReasoningClaim` DTO/value object;
- [ ] `EvidenceReference` / deterministic-finding reference contracts;
- [ ] `ClaimVerificationReport` + stable error codes;
- [ ] `VerifyReasoningClaims` application use-case contract;
- [ ] state-transition tests;
- [ ] action-class policy tests;
- [ ] claim-policy unit tests independent of Gemini/ADK;
- [ ] A2/A3 cannot auto-execute.

**Exit:** domain/application build without FastAPI/GCP/ADK/Gemini; action policy and proof-verification contracts are deterministic and framework-free.

---

## Aug 18 — Synthetic Data + Deterministic Ingestion

Create fixtures:

- [ ] complete zero-human hero dataset;
- [ ] normal baseline;
- [ ] noisy/malformed dataset;
- [ ] material-missing-data abstention fixture;
- [ ] prompt-injection-as-data fixture;
- [ ] stale-before-action fixture;
- [ ] A2/A3 policy-block fixtures;
- [ ] fabricated record/finding/source adversarial fixtures;
- [ ] hypothesis→fact escalation fixture.

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
- [ ] deterministic finding IDs + calculation/config version;
- [ ] surveillance use case;
- [ ] scenario tests;
- [ ] signal event contract.

**Exit:** hero dataset creates expected suspicious investigation candidate deterministically, with referenceable finding IDs suitable for proof-carrying claims.

---

## Aug 20 Morning — ADK Capability Spike

Before production graph code, complete `docs/ADK_CAPABILITY_SPIKE.md`.

- [ ] pin exact Python version;
- [ ] pin exact `google-adk` version;
- [ ] verify backend invocation without chat;
- [ ] verify sequential/parallel supported path;
- [ ] verify join/failure semantics;
- [ ] verify structured Gemini output compatible with proof-carrying DTOs;
- [ ] verify callback/session/eval/trace capabilities;
- [ ] prove deterministic verifier can sit outside model authority;
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
- [ ] approved-evidence manifest contract;
- [ ] incident-package schema;
- [ ] proof-carrying claim schema;
- [ ] claim verifier use case;
- [ ] package verifier/validator;
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
- [ ] Gemini proof-carrying synthesis;
- [ ] typed structured output parser;
- [ ] deterministic claim/evidence verification stage;
- [ ] bounded model/tool/time budgets;
- [ ] structured telemetry IDs.

### No-human hero behavior

- [ ] no clarification tool in required hero route;
- [ ] material missingness causes autonomous abstention;
- [ ] fixed routing does not call Gemini;
- [ ] proof verification failure cannot be waived by Gemini;
- [ ] hero complete fixture proceeds automatically.

**Exit:** pre-created hero signal → proof-carrying, machine-verifiable evidence-backed package without user input.

---

## Aug 22 — Proof Verification + Bounded Repair + Event Persistence

### Deterministic claim/evidence verifier

Reject:

- [ ] unknown canonical record/isolate ID;
- [ ] unknown/wrong-run deterministic finding ID;
- [ ] unknown/unretrieved/unapproved evidence source ID;
- [ ] stale package/finding reference;
- [ ] unsupported `OBSERVED_FACT`;
- [ ] unsupported `DERIVED_FINDING`;
- [ ] hypothesis mislabeled as fact;
- [ ] prohibited `DIAGNOSIS` / `PRESCRIPTION` / `OUTBREAK_CONFIRMATION` / official-authority claim;
- [ ] A1 authorization attempted through model output;
- [ ] missing required uncertainty/limitation when policy requires it.

### Bounded repair

- [ ] stable structured verifier errors;
- [ ] Gemini repair using only existing permitted facts/findings/evidence unless graph explicitly retrieves new approved evidence;
- [ ] hard max attempts (target `2`);
- [ ] exhausted budget → `VALIDATION_FAILED` / abstention;
- [ ] invalid/unverified package can never reach action policy.

### Persistence/events

- [ ] Firestore repositories;
- [ ] GCS store;
- [ ] Pub/Sub publisher/consumer;
- [ ] processed-event/idempotency persistence;
- [ ] append-only timeline;
- [ ] graph/session/run correlation;
- [ ] package/claim verification status persisted as canonical workflow facts;
- [ ] restart/redelivery tests.

**Exit:** event processing is durable/idempotent and model hallucination/reference errors can repair or stop safely without human review.

---

## Aug 23 — Zero-Human Autonomous Action + Machine Ack

### Policy engine

- [ ] deterministic A0/A1/A2/A3 classification;
- [ ] verified-package prerequisite;
- [ ] allow-listed target policy;
- [ ] authorization config;
- [ ] A2/A3 hard block;
- [ ] safe abstention states.

### Freshness

- [ ] incident/package/source watermark;
- [ ] pre-action deterministic revalidation;
- [ ] material change invalidates prior verification where relevant;
- [ ] material change → recompute/reverify/revalidate;
- [ ] no stale external action.

### ActionIntent / outbox / idempotency

- [ ] transactional immutable `ActionIntent`;
- [ ] stable logical idempotency key;
- [ ] payload/version binding;
- [ ] dispatcher lease/CAS semantics;
- [ ] delivery attempt/result persistence;
- [ ] receiver/provider dedupe where supported;
- [ ] stale unsent intent cancellation;
- [ ] duplicate event cannot duplicate logical action.

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

**Exit:** backend hero completes event→proof-verified action→ack with zero human intervention.

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
- [ ] **Proof-Carrying Autonomy card**;
- [ ] typed claim list with record/finding/source references;
- [ ] verification passed/failed state;
- [ ] repair attempt metadata without private CoT;
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

**Exit:** judge can understand zero-human workflow and proof-carrying model-safety boundary from UI alone.

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
- [ ] graph/node/model/claim-verification/action/freshness/ack telemetry;
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

### Proof-Carrying Autonomy eval

- [ ] unknown record/isolate reference rejected;
- [ ] unknown finding reference rejected;
- [ ] wrong-run/stale finding reference rejected;
- [ ] unknown/unretrieved source rejected;
- [ ] fabricated source/title/URL rejected;
- [ ] unsupported observed fact rejected;
- [ ] hypothesis→fact escalation rejected;
- [ ] forbidden clinical/official claim types rejected;
- [ ] failed proof verification blocks A1;
- [ ] repair success measured;
- [ ] repair budget exhaustion stops safely;
- [ ] `unsafe_claim_escape_rate == 0` on committed adversarial software suite.

Do not interpret that software test target as clinical validation.

### Safety/architecture eval

- [ ] deterministic node tests;
- [ ] fan-out order independence;
- [ ] required branch failure;
- [ ] zero model calls for fixed routing;
- [ ] prompt injection;
- [ ] material missingness abstention;
- [ ] A2/A3 blocks;
- [ ] non-allow-listed target block;
- [ ] freshness recompute;
- [ ] duplicate/redelivery idempotency;
- [ ] crash around external action uses same logical intent/key;
- [ ] session/canonical truth conflict;
- [ ] restart/recovery.

### Operational utility / BYOF

- [ ] freeze reference builder workflow;
- [ ] measure human active steps;
- [ ] capture event→package/action/ack timings;
- [ ] capture claim verification/repair metrics;
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
- [ ] make **The Twist: Proof-Carrying Autonomy** explicit in Devpost copy;
- [ ] prepare one 20–30s judge explanation of proof-carrying claims;
- [ ] draft LinkedIn article with required hackathon-purpose statement;
- [ ] verify bonus evidence requirements.

---

## Aug 29 — Demo Rehearsal + Risk Closure

Use `docs/HACKATHON_RISK_REGISTER.md`.

- [ ] rehearse <=4 min;
- [ ] continuous unedited hero segment has no human input;
- [ ] proof-carrying claim references + deterministic verification visible;
- [ ] external action visible outside Ngabo;
- [ ] machine acknowledgement returns visibly;
- [ ] Cloud Run/log proof legible;
- [ ] architecture diagram readable;
- [ ] BYOF friction clear in first 30 sec;
- [ ] Twist clear within first 60 sec;
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
- [ ] **The Twist: Proof-Carrying Autonomy** explicit;
- [ ] zero-human claim matches actual E2E evidence;
- [ ] proof-carrying claim only made if verifier/evals exist;
- [ ] bonuses claimed only with proof;
- [ ] submit before deadline buffer;
- [ ] verify submission from clean browser;
- [ ] preserve `main`/tag/deployed revisions/video through judging.

---

## 3. Scope Freeze

Until zero-human deployed hero + proof/safety evaluation are green, do **not** add:

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

> **AMR data changed → deterministic Ngabo logic detected a signal → Pub/Sub started the Google ADK workflow → deterministic investigation stages ran in parallel and joined → Gemini reasoned only where ambiguity existed → approved evidence was assembled → Gemini emitted proof-carrying structured claims → deterministic code verified every action-relevant record/finding/source reference and claim type → invalid claims repaired within budget or abstained → deterministic policy authorized only safe A1 action → freshness passed → Ngabo committed one durable ActionIntent → a real authorized external effect executed idempotently → a machine acknowledgement returned → the workflow completed with zero human intervention.**
