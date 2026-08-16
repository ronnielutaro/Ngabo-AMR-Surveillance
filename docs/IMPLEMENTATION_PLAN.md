# Ngabo — Implementation Plan

**Version:** 0.6  
**Created:** 2026-08-16  
**Official hackathon deadline:** 2026-08-31, 5:00 PM Pacific Time

---

## 1. Principle

> **Do not spend the final 48 hours implementing core architecture.**

Feature-complete several days early. Reserve the end for measured evaluation, deployment proof, UI polish, submission evidence, public build content, optional bonus integrations, demo rehearsal, and Devpost submission.

All implementation must preserve:

- Clean Architecture dependency boundaries;
- monorepo structure;
- deterministic scientific logic;
- graph-first hybrid orchestration;
- bounded agentic autonomy;
- long-running truth/context/freshness rules;
- human consequential-action governance;
- third-party/data/pre-existing-work provenance;
- measured operational-utility evaluation;
- Gitflow / SemVer / Conventional Commits;
- truthful hackathon claims and proof.

Required source contracts before runtime/submission work:

- `docs/HACKATHON_ALIGNMENT.md`
- `docs/CLEAN_ARCHITECTURE.md`
- `docs/ADK_RUNTIME.md`
- `docs/ORCHESTRATION_PATTERNS.md`
- `docs/LONG_RUNNING_AGENT.md`
- `docs/DATA_SAFETY_EVALUATION.md`
- `docs/OPERATIONAL_UTILITY_EVALUATION.md`
- `docs/UI_UX_SPEC.md`
- `docs/UI_UX_HACKATHON_ADDENDUM.md`
- `docs/THIRD_PARTY_PROVENANCE.md`
- `docs/SUBMISSION_EVIDENCE.md`
- ADR 0005 and ADR 0006.

---

## 2. Critical Path

```text
Clean Architecture monorepo scaffold
   ↓
domain entities + ports + state machine
   ↓
synthetic data + schema + provenance
   ↓
deterministic parser / normalizer
   ↓
deterministic surveillance detector
   ↓
application workflows + infrastructure adapters
   ↓
deterministic investigation capabilities
   ↓
ADK graph: context -> parallel function nodes -> join
   ↓
Gemini triage/synthesis agent nodes
   ↓
resumable long-running graph + current-context rebuild
   ↓
targeted clarification + same-incident resume
   ↓
deterministically validated incident package
   ↓
human consequential-action approval
   ↓
deterministic pre-action freshness barrier
   ↓
real outbound action + acknowledgement
   ↓
Next.js incident console + graph/freshness timeline
   ↓
Cloud deployment + observability + cost/security
   ↓
deterministic/ADK/E2E/freshness/operational evaluation
   ↓
EmbeddingGemma retrieval integration if core green
   ↓
provenance + submission evidence freeze
   ↓
demo + article + social + Devpost
```

---

## Aug 16 — Freeze Design, Architecture & Hackathon Contract

Completed design/governance work includes:

- [x] Lean Canvas
- [x] Devpost pitch
- [x] LinkedIn article strategy
- [x] PRD
- [x] Tech stack
- [x] System design
- [x] Agent design
- [x] Data/safety/evaluation design
- [x] UI/UX specification
- [x] release roadmap
- [x] Gitflow / SemVer / Conventional Commits governance
- [x] Clean Architecture + monorepo decision
- [x] `docs/HACKATHON_ALIGNMENT.md`
- [x] `docs/ADK_RUNTIME.md`
- [x] `docs/ORCHESTRATION_PATTERNS.md`
- [x] ADR 0005 — graph-first orchestration
- [x] `docs/LONG_RUNNING_AGENT.md`
- [x] ADR 0006 — long-running state/freshness/memory
- [x] `docs/OPERATIONAL_UTILITY_EVALUATION.md`
- [x] `docs/THIRD_PARTY_PROVENANCE.md`
- [x] `docs/SUBMISSION_EVIDENCE.md`
- [x] `CLAUDE.md` implementation contract
- [x] `AGENTS.md` coding-agent rules
- [x] GitHub repository + `develop`
- [x] LICENSE + SECURITY.md

**Exit:** implementation can begin without guessing the product, scoring strategy, architecture, long-running semantics, human boundary, provenance obligations, evaluation method, or submission proof requirements.

---

## Aug 17 — Clean Architecture Monorepo Scaffold + Domain Core

### Repository / workspaces

- [ ] create `apps/web`
- [ ] create `services/core`
- [ ] create `data/{synthetic,schemas,guidance}`
- [ ] create/verify `infra`
- [ ] pnpm workspace configuration
- [ ] uv Python project under `services/core`
- [ ] lint/type/test scripts
- [ ] `.env.example`

### Backend Clean Architecture

Create:

```text
services/core/ngabo/
├── domain/
├── application/
├── interfaces/
├── infrastructure/
└── bootstrap/
```

- [ ] domain entities/value objects/events/services
- [ ] application use cases/ports/workflows
- [ ] interfaces API/events
- [ ] infrastructure adapter packages including `infrastructure/ai/adk`
- [ ] composition root/dependency wiring

### Domain model

- [ ] ImportBatch
- [ ] Isolate
- [ ] ASTResult
- [ ] SurveillanceSignal
- [ ] Incident
- [ ] IncidentEvent
- [ ] Clarification
- [ ] Review decision/version reference
- [ ] Notification state
- [ ] Agent/graph execution reference at application boundary
- [ ] Incident/package/source watermark/version values
- [ ] Incident state machine
- [ ] State-transition tests

### Architecture acceptance

- [ ] domain imports no FastAPI/GCP/ADK/Gemini SDKs
- [ ] application imports no concrete cloud/model SDKs
- [ ] framework adapters remain thin
- [ ] domain tests run without network/cloud/model access

**Exit:** monorepo builds; domain/state/version policy is explicit; architecture tests pass.

---

## Aug 18 — Synthetic Data + Deterministic Ingestion + Provenance Baseline

- [ ] supported input columns
- [ ] baseline synthetic dataset
- [ ] seeded suspicious cluster
- [ ] malformed/noisy dataset
- [ ] prompt-injection-as-data fixture
- [ ] freshness/material-change fixture
- [ ] canonical input/domain mappings
- [ ] deterministic parser/normalizer
- [ ] file-storage port
- [ ] import repository port
- [ ] import use case
- [ ] thin FastAPI import interface
- [ ] validation report
- [ ] duplicate handling
- [ ] file hashing/source watermarking
- [ ] every public fixture labelled synthetic
- [ ] confirm no real WHONET/hospital row is committed
- [ ] begin `docs/THIRD_PARTY_PROVENANCE.md` evidence/data register

**Architecture check:** FastAPI translates input and invokes a use case; it does not own parsing/scientific policy.

**Exit:** CSV → canonical isolates + validation report through real application boundary; dataset provenance is clean.

---

## Aug 19 — Deterministic Surveillance Engine

- [ ] resistance representation/value objects
- [ ] similarity method
- [ ] temporal concentration
- [ ] ward/location concentration
- [ ] baseline comparison
- [ ] prototype signal score
- [ ] trigger explanation
- [ ] surveillance use case
- [ ] scenario tests
- [ ] source/material-change watermark inputs defined

**Architecture check:** surveillance calculations run without FastAPI, Firestore, Pub/Sub, ADK, Gemini or network access.

**Exit:** seeded investigation candidate detected deterministically and reproducibly.

---

## Aug 20–21 — Investigation Capabilities + ADK Graph + Gemini Reasoning

Read before implementation:

- `docs/ADK_RUNTIME.md`
- `docs/ORCHESTRATION_PATTERNS.md`
- `docs/LONG_RUNNING_AGENT.md`
- `docs/AGENT_ARCHITECTURE.md`
- ADR 0005 / ADR 0006.

### Inner contracts

- [ ] investigation application port
- [ ] evidence-search port
- [ ] incident-context query/use case
- [ ] profile-comparison query wrapping deterministic domain logic
- [ ] baseline-summary query wrapping deterministic domain logic
- [ ] missing-fields query
- [ ] structured incident-package schema
- [ ] deterministic package validator
- [ ] graph/agent execution metadata contract
- [ ] context-rebuild application query

### ADK infrastructure

- [ ] Google ADK under `infrastructure/ai/adk`
- [ ] graph/workflow boundary
- [ ] function-node adapter boundary
- [ ] Gemini 3.6 Flash agent-node adapter/config
- [ ] local-only ADK development workflow
- [ ] persist/correlate session/invocation/run IDs
- [ ] verify exact installed ADK graph/resume/human-input APIs
- [ ] bounded max model steps/calls/tools/timeouts/retries

### Core deterministic graph

```text
incident context
      ↓
parallel fan-out
  ├─ profile comparison
  ├─ baseline summary
  └─ missing-field assessment
      ↓
join
```

- [ ] context node calls inward application contract
- [ ] deterministic branch nodes
- [ ] parallel fan-out
- [ ] typed join result
- [ ] required branch failure semantics
- [ ] timeout/retry semantics
- [ ] no unsafe shared-state mutation

### Routing

- [ ] fixed event/state/validation routing remains code
- [ ] table-driven deterministic routing tests
- [ ] verify zero Gemini calls for fixed routing

### Gemini reasoning

- [ ] triage consumes joined deterministic findings
- [ ] materiality decision for missing context
- [ ] bounded evidence intent
- [ ] evidence-grounded synthesis
- [ ] citation/source ID validation
- [ ] prohibited-claim validation
- [ ] deterministic package post-validation

### ADK eval foundation

- [ ] committed eval dataset location
- [ ] happy-path graph
- [ ] clarification case
- [ ] no-evidence case
- [ ] required-branch failure
- [ ] fan-out completion-order
- [ ] fixed-routing-no-model-call
- [ ] prompt injection

**Exit:** pre-created signal → deterministic graph fan-out/join → bounded Gemini reasoning → valid evidence-backed package locally.

---

## Aug 22 — Persistent Event Workflow + Resume / Context Safety

### Infrastructure adapters

- [ ] Firestore repositories
- [ ] GCS raw/artifact store
- [ ] Pub/Sub publisher/consumer adapters
- [ ] processed-event/idempotency persistence

### Workflow

- [ ] incident persistence
- [ ] append-only event timeline
- [ ] persist graph/agent session/invocation/run refs
- [ ] incident/package/source versions + watermarks
- [ ] resumable incident state
- [ ] restart/retry path
- [ ] idempotent redelivery
- [ ] resume/retry audit events
- [ ] context rebuild from canonical current state
- [ ] old session text cannot override current Firestore state
- [ ] context compaction/bounding only if stable/useful
- [ ] ADK Web excluded from public deployment
- [ ] no A2A runtime/service in v0.1

**Exit:** interruption/restart/redelivery cannot duplicate incident/effect; resumed reasoning uses current canonical truth.

---

## Aug 23 — Clarification + Human Safety Gate + Freshness + Real Action

### Clarification

- [ ] clarification use case/endpoint
- [ ] stable ADK human-input integration where useful
- [ ] deterministic missing-field node identifies missingness
- [ ] Gemini triage decides materiality
- [ ] `WAITING_FOR_CLARIFICATION`
- [ ] resume same incident after answer

### Human review

- [ ] review use case
- [ ] approve
- [ ] reject
- [ ] request more info
- [ ] persist reviewed package/incident/source watermark references
- [ ] final authority remains in application/domain state machine

### Pre-action freshness barrier

- [ ] `RevalidateIncidentBeforeAction` (or equivalent) application use case
- [ ] compare current vs reviewed incident/package/source versions
- [ ] deterministic material-change policy
- [ ] unchanged state → action allowed
- [ ] material new isolate → approval stale
- [ ] changed AST → approval stale
- [ ] regenerated package → approval stale
- [ ] material clarification/evidence change → approval stale where policy requires
- [ ] telemetry-only change does not invalidate approval
- [ ] stale path returns visibly to review
- [ ] stale approval cannot be replayed on retry/redelivery

### Real action

- [ ] NotificationPort
- [ ] deterministic demo adapter
- [ ] **real authorized outbound notification adapter**
- [ ] idempotency key
- [ ] delivery attempt/result persistence
- [ ] acknowledgement use case
- [ ] demo-visible external result

**Exit:** backend E2E completes real approved action only when current reviewed state remains valid.

---

## Aug 24–25 — Next.js Incident Console

Implement against the UI/UX contracts.

### Frontend structure

- [ ] `src/domain`
- [ ] `src/application`
- [ ] `src/infrastructure/api`
- [ ] `src/infrastructure/streaming`
- [ ] `src/presentation`
- [ ] Next.js `app/` composition/routes

### Required screens/components

- [ ] app shell + synthetic-data banner
- [ ] dashboard
- [ ] import/validation
- [ ] incident queue/detail
- [ ] deterministic “why flagged” card
- [ ] resistance-profile comparison
- [ ] live graph timeline
- [ ] visible function-node fan-out/branch completion/join
- [ ] bounded agent-stage visibility without chain-of-thought
- [ ] interruption/retry/resume/context-rebuilt visibility
- [ ] targeted clarification card
- [ ] evidence-backed package + source provenance
- [ ] professional review panel
- [ ] freshness check state
- [ ] stale-approval / re-review state
- [ ] real-vs-demo response tracking
- [ ] acknowledgement state
- [ ] demo reset/seed controls
- [ ] accessibility/loading/error/empty states

**Exit:** non-developer can understand autonomy, deterministic vs agentic work, safety boundary, freshness and real action from UI alone.

---

## Aug 26 — GCP Deployment + Observability + Cost / Security

### Infrastructure

- [ ] Cloud Storage
- [ ] Firestore
- [ ] Pub/Sub
- [ ] `ngabo-core` Cloud Run
- [ ] `ngabo-web` Cloud Run
- [ ] production composition root

### Cost

- [ ] Cloud Run min instances `0` unless documented exception
- [ ] max-instance caps
- [ ] right-sized CPU/RAM
- [ ] Google Cloud budget
- [ ] budget email alert
- [ ] artifact/log cleanup policy

### Security

- [ ] Secret Manager/injected secrets
- [ ] no committed credentials
- [ ] protected event/internal endpoints
- [ ] Pub/Sub origin/auth validation where applicable
- [ ] expensive public endpoint protection/rate limits where practical
- [ ] least-privilege service accounts where practical
- [ ] ADK Web not publicly deployed

### Observability

- [ ] correlation/event/incident IDs
- [ ] graph run/node/branch/join telemetry
- [ ] agent session/invocation/run telemetry
- [ ] model-call count/latency
- [ ] pause/resume/context-rebuild events
- [ ] review/freshness events
- [ ] action/ack events
- [ ] Cloud Trace/OpenTelemetry path if stable
- [ ] metadata-first/no-sensitive-content traces
- [ ] deployed URLs + commit recorded
- [ ] Cloud Run/log/trace proof captured

**Exit:** full scenario works on Google Cloud with inspectable proof and controlled cost/security.

---

## Aug 27 — Evaluation + Operational Utility + EmbeddingGemma

### Deterministic/application

- [ ] pure domain suite
- [ ] application use-case tests
- [ ] infrastructure contract tests
- [ ] interface/API/event tests

### Graph/orchestration

- [ ] deterministic function-node tests
- [ ] branch completion-order test
- [ ] required branch failure
- [ ] join semantics
- [ ] deterministic router table tests
- [ ] zero model call for fixed routing
- [ ] canonical graph trajectory captured

### Long-running/freshness

- [ ] process restart/recovery
- [ ] same-incident clarification resume
- [ ] canonical context rebuild
- [ ] old session vs current Firestore conflict
- [ ] approval + no material change → action
- [ ] approval + new isolate → block
- [ ] approval + changed AST → block
- [ ] stale approval replay → block
- [ ] notification retry/idempotency

### ADK/safety

- [ ] clarification behavior
- [ ] empty evidence
- [ ] bounded capability failure
- [ ] fabricated source
- [ ] hallucinated isolate
- [ ] prohibited clinical claims
- [ ] prompt injection
- [ ] model/tool budget

### Operational utility

Follow `docs/OPERATIONAL_UTILITY_EVALUATION.md`:

- [ ] document scripted reference workflow
- [ ] measure reference human active steps
- [ ] measure Ngabo human interventions/active steps
- [ ] verify zero prompts to start investigation
- [ ] capture `signal_to_review_ready_ms`
- [ ] capture clarification count
- [ ] capture model/function/tool counts
- [ ] capture action-to-ack timing where available
- [ ] report median/range across deployed runs
- [ ] do not invent hospital productivity percentages

### Deployed E2E

- [ ] full deployed integration test
- [ ] run canonical hosted scenario three consecutive times
- [ ] record failures/retries rather than deleting them
- [ ] architecture dependency audit
- [ ] create public `EVALUATION.md`

### EmbeddingGemma — only after core E2E green

- [ ] verify exact model usage terms/provenance
- [ ] precompute approved guidance embeddings
- [ ] implement `EmbeddingGemmaEvidenceAdapter`
- [ ] lightweight cosine similarity retrieval
- [ ] preserve source IDs/chunks/scores
- [ ] retrieval tests/eval
- [ ] record actual integration in provenance + submission evidence

**Exit:** measured evidence exists for architecture, reliability, safety and highest-weighted operational utility; EmbeddingGemma claimed only if real.

---

## Aug 28 — Technical Story + Provenance + Submission Evidence + Bonus Readiness

### Architecture / reproducibility

- [ ] final architecture diagram matches deployed runtime
- [ ] diagram shows Pub/Sub → ADK graph → deterministic fan-out/join → Gemini → evidence → human boundary → freshness → real action
- [ ] diagram shows Firestore/GCS/Cloud Run/observability
- [ ] optional models shown only if implemented
- [ ] README spin-up/deploy instructions tested and polished
- [ ] product screenshots captured

### Provenance / ownership

- [ ] complete `docs/THIRD_PARTY_PROVENANCE.md`
- [ ] exact dependency/model/service versions recorded
- [ ] evidence-corpus sources have usage/licensing basis
- [ ] no unauthorized full-text guidance copied
- [ ] no real patient/lab data
- [ ] any non-standard pre-existing work disclosed
- [ ] no third-party media/logo implies endorsement

### Submission evidence

- [ ] update `docs/SUBMISSION_EVIDENCE.md` with actual URLs/artifacts
- [ ] hosted URL
- [ ] deployed commit SHA
- [ ] architecture diagram location
- [ ] `EVALUATION.md`
- [ ] cloud proof location
- [ ] real-action/ack proof
- [ ] resume/freshness proof
- [ ] final claim ledger

### Bonus

- [ ] LinkedIn build article final draft
- [ ] article states it was created for purposes of entering the hackathon
- [ ] exact social hashtag `#AllThingsAgenticHackathon`
- [ ] EmbeddingGemma bonus claimed only if real
- [ ] MedGemma only if core frozen + measured value

**Exit:** every competitive claim has a proof location or is removed/future-labelled.

---

## Aug 29 — Demo Freeze + Rehearsal

- [ ] freeze canonical seeded scenario
- [ ] freeze deployed demo candidate after repeated successful runs
- [ ] no new core architecture changes
- [ ] write <=4-minute storyboard/script
- [ ] rehearse live sequence repeatedly
- [ ] ensure one continuous Proof-of-Action execution segment
- [ ] verify real action target is authorized
- [ ] verify stale-approval/freshness behavior separately even if not fully shown in video
- [ ] verify Google Cloud proof can be shown quickly
- [ ] verify operational utility result can be explained in one concise statement

Suggested demo sequence:

1. friction/problem;
2. synthetic data/signal;
3. automatic Pub/Sub trigger;
4. fan-out/join;
5. Gemini/evidence;
6. clarification + resume;
7. package;
8. human review;
9. freshness pass;
10. real external action;
11. acknowledgement;
12. quick Cloud/architecture/evaluation evidence.

---

## Aug 30 — Submission Assembly

- [ ] Devpost description
- [ ] Taskmaster category selected
- [ ] features/functionality accurate
- [ ] technologies actually used listed
- [ ] data sources/provenance accurate
- [ ] findings/learnings included
- [ ] pre-existing-work disclosure included if applicable
- [ ] repo URL
- [ ] hosted URL
- [ ] testing instructions/credentials if needed
- [ ] architecture diagram
- [ ] <=4-minute public YouTube/Vimeo video
- [ ] English/subtitles verified
- [ ] public article/social/model bonus links
- [ ] compare every claim to `docs/SUBMISSION_EVIDENCE.md`
- [ ] remove all unimplemented claims

---

## Aug 31 — Final Verification + Submit Early

Do not use deadline day for substantial engineering.

- [ ] clean-environment README sanity check
- [ ] hosted app reachable
- [ ] judge access unrestricted/free as required
- [ ] canonical demo flow still passes
- [ ] external action target still authorized
- [ ] secrets absent from repo/video/logs
- [ ] final architecture diagram matches deployment
- [ ] `EVALUATION.md` public and truthful
- [ ] provenance/disclosure complete
- [ ] bonus links public
- [ ] video <=4 minutes
- [ ] submit with buffer before 17:00 PT
- [ ] keep judge-required infrastructure available through judging period

---

## 3. Scope Freeze / Stretch Order

Do not implement before the core deployed E2E is stable:

- MedGemma;
- collaborative specialist-agent topology;
- runtime-generated dynamic topology;
- multimodal AST/PDF ingestion;
- genomics / AMRFinderPlus;
- vector database;
- GKE;
- Redis/Kafka;
- LangGraph;
- mobile app;
- real patient data;
- production hospital connector.

Preferred stretch order after core freeze:

1. EmbeddingGemma retrieval;
2. richer architecture/demo visualization;
3. MedGemma only if evaluation shows value;
4. multimodal AST/PDF draft UX if time permits;
5. genomics last.

---

## 4. Final Definition of Done

The v0.1 submission is complete only when:

```text
working hosted product
+ Taskmaster autonomous workflow
+ graph-first ADK runtime
+ deterministic/agentic separation
+ durable/resumable state
+ current-context reconstruction
+ freshness-protected human approval
+ real idempotent external action
+ acknowledgement
+ measured operational utility
+ public evaluation
+ provenance/disclosure
+ architecture diagram
+ tested reproducibility instructions
+ visible Google Cloud execution
+ truthful <=4-minute demo
+ evidence-backed submission claims
```

If any submitted claim cannot be proven, change the claim or change the product — never fake the proof.
