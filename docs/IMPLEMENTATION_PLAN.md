# Ngabo — Implementation Plan

**Version:** 0.5  
**Created:** 2026-08-16  
**Official hackathon deadline:** 2026-08-31, 5:00 PM Pacific Time

## 1. Principle

> **Do not spend the final 48 hours implementing core architecture.**

Feature-complete several days early; reserve the end for evaluation, deployment proof, UI polish, public build content, bonus integrations, demo, and submission.

All implementation must preserve:

- **Clean Architecture** dependency boundaries;
- the **monorepo** structure;
- deterministic scientific logic;
- the **graph-first hybrid orchestration** contract;
- bounded agentic autonomy;
- Gitflow / SemVer / Conventional Commits governance;
- the hackathon alignment requirements in `docs/HACKATHON_ALIGNMENT.md`;
- the ADK runtime contract in `docs/ADK_RUNTIME.md`;
- the orchestration rules in `docs/ORCHESTRATION_PATTERNS.md` and ADR 0005.

## 2. Critical Path

```text
Clean Architecture monorepo scaffold
   ↓
domain entities + ports + state machine
   ↓
synthetic data + schema
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
resumable graph investigation
   ↓
targeted clarification + resume
   ↓
deterministically validated incident package
   ↓
human approval
   ↓
real outbound action + acknowledgement
   ↓
Next.js incident console + graph timeline
   ↓
Cloud deployment + observability
   ↓
ADK/scientific/E2E evaluation + model-call budget
   ↓
EmbeddingGemma retrieval integration
   ↓
demo + article + social + Devpost
```

## Aug 16 — Freeze Design, Architecture & Hackathon Contract

- [x] Lean Canvas
- [x] Devpost pitch
- [x] LinkedIn article strategy
- [x] PRD
- [x] Tech stack
- [x] System design
- [x] Agent design
- [x] Data/safety/evaluation design
- [x] UI/UX implementation specification
- [x] Product/release roadmap
- [x] Gitflow / SemVer / Conventional Commits governance
- [x] Clean Architecture + monorepo decision
- [x] `docs/CLEAN_ARCHITECTURE.md`
- [x] ADR 0003 — Clean Architecture in a monorepo
- [x] `docs/HACKATHON_ALIGNMENT.md`
- [x] `docs/ADK_RUNTIME.md`
- [x] ADR 0004 — hackathon runtime + bonus-model strategy
- [x] `docs/ORCHESTRATION_PATTERNS.md`
- [x] ADR 0005 — graph-first hybrid ADK orchestration
- [x] `CLAUDE.md` implementation contract
- [x] `AGENTS.md` coding-agent rules
- [x] GitHub repository + `develop` branch
- [x] README/document map
- [x] LICENSE + SECURITY.md
- [x] implementation design docs in repository

**Exit:** Claude Code can begin Milestone 1 without guessing product behavior, UI, safety model, graph/agent boundary, runtime strategy, hackathon obligations, release workflow, repository shape, or dependency direction.

## Aug 17 — Clean Architecture Monorepo Scaffold + Domain Core

### Repository/workspaces

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

- [ ] `domain/entities`
- [ ] `domain/value_objects`
- [ ] `domain/events`
- [ ] `domain/services/surveillance`
- [ ] `application/use_cases`
- [ ] `application/ports`
- [ ] `application/workflows`
- [ ] `interfaces/api`
- [ ] `interfaces/events`
- [ ] infrastructure adapter folders including `infrastructure/ai/adk`
- [ ] composition root / dependency wiring skeleton

### Domain model

- [ ] ImportBatch
- [ ] Isolate
- [ ] ASTResult
- [ ] SurveillanceSignal
- [ ] Incident
- [ ] IncidentEvent
- [ ] Clarification
- [ ] Notification state
- [ ] agent-execution reference value/object at application boundary
- [ ] incident state machine
- [ ] state-transition tests

### Architecture acceptance

- [ ] domain imports no FastAPI/GCP/ADK/Gemini SDKs
- [ ] application imports no concrete cloud/model SDKs
- [ ] framework adapters remain thin
- [ ] domain tests run without network/cloud/model access

Optional implementation aid:

- [ ] run `uvx google-agents-cli setup` if useful; generated scaffolding must not replace Ngabo's monorepo/Clean Architecture/orchestration contracts.

**Exit:** monorepo builds; Clean Architecture boundaries exist; domain/state-policy tests are green.

## Aug 18 — Synthetic Data + Deterministic Ingestion

- [ ] supported input columns
- [ ] baseline dataset
- [ ] seeded suspicious cluster
- [ ] malformed/noisy dataset
- [ ] prompt-injection-as-data fixture
- [ ] canonical input/domain mappings
- [ ] deterministic parser/normalizer
- [ ] file-storage port
- [ ] import repository port
- [ ] import use case
- [ ] thin FastAPI import interface
- [ ] validation report
- [ ] duplicate handling
- [ ] file hashing

**Architecture check:** FastAPI translates input and invokes a use case; it does not own parsing/scientific policy.

**Exit:** CSV → canonical isolates + validation report through the real application boundary.

## Aug 19 — Deterministic Surveillance Engine

- [ ] resistance representation/value objects
- [ ] similarity method
- [ ] temporal concentration
- [ ] ward concentration
- [ ] baseline comparison
- [ ] prototype signal score
- [ ] trigger explanation
- [ ] surveillance use case
- [ ] scenario tests

**Architecture check:** pure surveillance calculations run without FastAPI, Firestore, Pub/Sub, ADK, Gemini, or network access.

**Exit:** seeded investigation candidate detected deterministically.

## Aug 20–21 — Investigation Capabilities + ADK Graph + Gemini Reasoning

Read before implementation:

- `docs/ADK_RUNTIME.md`
- `docs/ORCHESTRATION_PATTERNS.md`
- `docs/AGENT_ARCHITECTURE.md`
- ADR 0005

### Inner contracts

- [ ] agent-investigation application port
- [ ] evidence-search port
- [ ] incident-context query/use case
- [ ] profile-comparison application query wrapping deterministic domain logic
- [ ] baseline-summary application query wrapping deterministic domain logic
- [ ] missing-fields application query
- [ ] structured incident-package schema
- [ ] deterministic package-validator contract
- [ ] agent execution metadata application contract

### ADK infrastructure scaffold

- [ ] Google ADK under `infrastructure/ai/adk`
- [ ] graph/workflow package boundary
- [ ] function-node adapter boundary
- [ ] Gemini 3.6 Flash agent-node adapter/configuration
- [ ] local ADK playground/run workflow
- [ ] persist/correlate session/invocation/run IDs
- [ ] investigate exact installed ADK graph/resume APIs before coding against workshop terminology
- [ ] bounded max model steps/calls/tool calls/timeouts/retries

### Core graph — deterministic first

Implement the canonical graph:

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

- [ ] context function node calls inward application contract
- [ ] profile-comparison function node
- [ ] baseline-summary function node
- [ ] missing-field function node
- [ ] parallel fan-out
- [ ] typed join result
- [ ] required-branch failure semantics
- [ ] branch timeout/retry semantics
- [ ] no unsafe shared-state mutation from parallel branches

### Routing

- [ ] deterministic event/state/validation routing remains ordinary code
- [ ] table-driven tests for deterministic routing
- [ ] no Gemini call for fixed routing decisions

### Gemini reasoning nodes

- [ ] triage agent node consumes joined deterministic findings
- [ ] agent decides whether detected missingness is materially blocking
- [ ] agent formulates bounded evidence-search intent where needed
- [ ] source-grounded synthesis agent node
- [ ] package preparation boundary
- [ ] citation validation
- [ ] prohibited-claim validation
- [ ] deterministic package post-validation

### Evidence

- [ ] approved-guidance retrieval through `EvidenceSearchPort`
- [ ] curated/tag fallback initially
- [ ] evidence query may run in initial parallel graph only if intent can be formed deterministically

### Resumability

- [ ] implement resumable graph/agent execution if stable in exact installed ADK version
- [ ] application-level safe restart fallback
- [ ] verified completed deterministic results are reused only when trustworthy
- [ ] repeated nodes remain idempotent/read-only where possible

### ADK eval foundation

- [ ] committed eval dataset location
- [ ] happy-path graph case
- [ ] clarification case
- [ ] no-evidence case
- [ ] required-branch failure case
- [ ] fan-out completion-order case
- [ ] fixed-routing-no-model-call case
- [ ] prompt-injection case

**Architecture check:** ADK graph/function/agent wrappers invoke application/domain contracts. No raw Firestore + business logic inside nodes. Known mandatory reproducible steps are not delegated to Gemini.

**Exit:** pre-created signal → deterministic graph fan-out/join → bounded Gemini reasoning → schema-valid evidence-backed incident package locally.

## Aug 22 — Persistent Event Workflow + Resume Safety

### Infrastructure adapters

- [ ] Firestore repositories
- [ ] GCS raw-file store
- [ ] Pub/Sub event publisher
- [ ] processed-event/idempotency persistence

### Interface adapters

- [ ] import event handler
- [ ] surveillance-signal event handler
- [ ] incident event handler

### Workflow

- [ ] incident persistence
- [ ] append-only event timeline
- [ ] persist agent session/invocation/run references
- [ ] graph/node execution correlation metadata where useful
- [ ] resumable incident state
- [ ] restart/retry path
- [ ] idempotent redelivery behavior
- [ ] resume/retry audit events
- [ ] deterministic branch results remain traceable/reusable only when valid

**Architecture check:** Pub/Sub handlers translate events to application commands; framework state is not the business source of truth.

**Exit:** interruption/restart/redelivery cannot duplicate incident or side effect; graph investigation can recover safely.

## Aug 23 — Human Input, Safety Gate + Real Action

### Clarification

- [ ] clarification use case + endpoint
- [ ] ADK-targeted human-input integration where stable
- [ ] deterministic missing-field node identifies missingness
- [ ] Gemini triage decides materiality before asking
- [ ] `WAITING_FOR_CLARIFICATION`
- [ ] resume same incident after answer

### Human review

- [ ] review use case
- [ ] approve
- [ ] reject
- [ ] request more info
- [ ] keep final authority in application/domain state machine

### Action

- [ ] notification port
- [ ] deterministic demo notification adapter
- [ ] **real authorized outbound notification adapter**
- [ ] persist delivery attempt/result
- [ ] idempotent retry
- [ ] acknowledgement use case
- [ ] demo-visible external result

**Exit:** backend end-to-end workflow is complete and a real approved external action can be demonstrated.

## Aug 24–25 — Next.js Incident Console

Implement against `docs/UI_UX_SPEC.md`, `docs/UI_UX_HACKATHON_ADDENDUM.md`, and `docs/CLEAN_ARCHITECTURE.md`.

### Frontend structure

- [ ] `src/domain`
- [ ] `src/application`
- [ ] `src/infrastructure/api`
- [ ] `src/infrastructure/streaming`
- [ ] `src/presentation`
- [ ] Next.js `app/` route/composition wiring

### Screens/components

- [ ] app shell + synthetic-data banner
- [ ] dashboard
- [ ] import UI
- [ ] validation report
- [ ] incident queue
- [ ] incident header
- [ ] deterministic “why flagged” card
- [ ] resistance-profile comparison
- [ ] live graph/agent investigation timeline
- [ ] visible parallel fan-out + branch completion + join without exposing chain-of-thought
- [ ] pause/resume/retry state visibility
- [ ] clarification card
- [ ] evidence-backed package
- [ ] source links/details
- [ ] human review panel
- [ ] response tracking
- [ ] real-vs-demo notification channel label
- [ ] loading/error/empty states
- [ ] demo reset/seeded scenario controls
- [ ] accessibility pass

**Architecture check:** React components do not call Firestore, Pub/Sub, Gemini, ADK, or cloud SDKs directly.

**Exit:** a non-developer can understand deterministic work, agentic reasoning stages, autonomy, safety boundaries, and action from the UI alone.

## Aug 26 — GCP Deployment + Observability + Cost/Security Controls

### Infrastructure

- [ ] Cloud Storage
- [ ] Firestore
- [ ] Pub/Sub
- [ ] `ngabo-core` Cloud Run
- [ ] `ngabo-web` Cloud Run
- [ ] production composition root

### Cost controls

- [ ] Cloud Run minimum instances = `0` unless documented exception
- [ ] explicit max-instance caps
- [ ] right-sized CPU/RAM
- [ ] Google Cloud budget
- [ ] email budget alert
- [ ] lightweight artifact retention/cleanup plan

### Security

- [ ] Secret Manager / injected secrets
- [ ] no committed credentials
- [ ] protect internal event endpoints
- [ ] validate Pub/Sub request origin/auth where applicable
- [ ] protect/rate-limit expensive public endpoints
- [ ] least-privilege service accounts where practical

### Observability

- [ ] Cloud Logging structured fields
- [ ] graph run/node/branch/join telemetry
- [ ] ADK invocation/agent/tool telemetry
- [ ] model-call count/latency
- [ ] Cloud Trace/OpenTelemetry path if stable
- [ ] metadata-first/no-sensitive-content trace configuration
- [ ] deployed URLs
- [ ] capture Cloud Run + logs/traces proof

**Exit:** full scenario works on Google Cloud and provides visible operational proof without uncontrolled cost exposure.

## Aug 27 — Evaluation + EmbeddingGemma

### Scientific/application evaluation

- [ ] pure domain test suite
- [ ] application-use-case tests with fakes
- [ ] infrastructure adapter/contract tests
- [ ] interface/API/event tests
- [ ] scenario benchmark

### Graph/orchestration evaluation

- [ ] deterministic function-node tests
- [ ] parallel branch completion-order test
- [ ] required branch failure test
- [ ] join semantics test
- [ ] deterministic router table tests
- [ ] verify zero model call for fixed routing decisions
- [ ] canonical graph trajectory captured

### ADK evaluation

- [ ] agentic routing/capability-choice evaluations where supported
- [ ] clarification behavior
- [ ] empty-evidence behavior
- [ ] tool/capability failure
- [ ] fabricated-source test
- [ ] hallucinated-isolate test
- [ ] prohibited clinical-claim tests
- [ ] prompt injection test
- [ ] duplicate-event test
- [ ] notification retry test
- [ ] resume/recovery test
- [ ] baseline vs candidate eval comparison for material agent changes

### End-to-end

- [ ] full deployed integration test
- [ ] architecture dependency audit
- [ ] `EVALUATION.md`
- [ ] model-call/function-call/tool-call counts captured
- [ ] branch/join timing captured
- [ ] total investigation duration captured

### Planned bonus model — EmbeddingGemma

Only after the core deployed E2E graph is green:

- [ ] precompute curated guidance embeddings
- [ ] implement `EmbeddingGemmaEvidenceAdapter`
- [ ] lightweight cosine similarity retrieval
- [ ] return approved source IDs/chunks/scores
- [ ] retrieval tests/evaluation
- [ ] demonstrate/document actual integration

**Exit:** demo is reproducible, graph boundaries remain intact, ADK behavior is evaluated, model-call use is disciplined, and EmbeddingGemma is only claimed if it genuinely works.

## Aug 28 — Technical Story + Bonus Readiness

- [ ] final architecture diagram includes Clean Architecture + runtime/cloud views
- [ ] diagram shows Pub/Sub -> ADK graph -> function-node fan-out/join -> Gemini reasoning -> evidence -> human gate -> real action
- [ ] diagram shows Firestore/GCS/Cloud Run/observability
- [ ] include EmbeddingGemma only if implemented
- [ ] product screenshots
- [ ] LinkedIn Article final draft
- [ ] article explicitly states it was created for purposes of entering the hackathon
- [ ] explain why known work is deterministic and ambiguity is agentic
- [ ] README spin-up instructions polished
- [ ] `EVALUATION.md` polished

### Gated stretch decision

If and only if core + EmbeddingGemma + deployment + evals are stable:

- [ ] evaluate whether MedGemma adds measurable value as a bounded evidence-interpretation capability
- [ ] if useful, integrate + test + document
- [ ] consider collaborative specialist agents only if evaluations show a need
- [ ] otherwise omit them and preserve demo stability

Do not count a bonus for an unproven integration.

## Aug 29–30 — Demo + Devpost + Public Content

### Demo

- [ ] <=4 minutes
- [ ] problem/value proposition immediately clear
- [ ] unedited live workflow
- [ ] event-triggered investigation — no manual “investigate” prompt
- [ ] visible deterministic fan-out + join
- [ ] visible Gemini reasoning/tool/evidence stage without chain-of-thought
- [ ] clarification pause + resume
- [ ] deterministic package validation
- [ ] human approval
- [ ] real outbound action
- [ ] acknowledgement/state update
- [ ] visible Google Cloud execution
- [ ] observability/evaluation proof
- [ ] architecture explanation
- [ ] safety boundary
- [ ] public YouTube/Vimeo video

### Devpost

- [ ] select **The Taskmaster**
- [ ] summary/features
- [ ] technology/data sources
- [ ] findings/learnings
- [ ] GitHub URL
- [ ] hosted URL
- [ ] architecture diagram
- [ ] reproducible spin-up instructions
- [ ] LinkedIn Article URL
- [ ] social post URL
- [ ] accurately list each successfully integrated additional Google AI model
- [ ] final claims audit

### Public bonus content

- [ ] publish qualifying LinkedIn Article
- [ ] required hackathon-purpose language included
- [ ] publish LinkedIn/social post
- [ ] exact hashtag `#AllThingsAgenticHackathon`

**Internal target:** submission-ready by end of Aug 30.

## Aug 31 — Buffer + Submit

Only:

- critical fixes;
- link verification;
- final deployed test;
- rules re-check;
- submission.

No major features, model additions, or architectural rewrites.

## 3. Stretch Order

Only after every core submission requirement is green:

1. MedGemma bounded evidence interpretation **if evaluation supports it**;
2. collaborative specialist-agent pattern **only if evaluation demonstrates a real need**;
3. Gemini multimodal AST/PDF extraction into a **human-verified draft**;
4. richer baseline visualization;
5. runtime-dynamic investigation topology only if a concrete post-core use case requires it;
6. AMRFinderPlus/genomics prototype.

> **Bonus points never outrank a reliable core demo. Genomics remains last, not first.**

## 4. Demo Freeze Rule

After three consecutive successful deployed end-to-end runs:

1. record/tag a demo candidate according to release policy;
2. stop architecture refactors;
3. do not add stretch models/features;
4. fix only critical bugs and presentation problems.

## 5. Current Hackathon Checklist

### Mandatory

- [ ] Gemini 3.5+ actually used
- [ ] Google ADK actually orchestrates the graph/agent workflow
- [ ] Google Cloud infrastructure actually used
- [ ] Cloud Run deployed services
- [ ] Firestore persistent state
- [ ] Pub/Sub event-driven trigger
- [ ] Cloud Storage artifacts/evidence
- [ ] hosted project
- [x] repository
- [x] Clean Architecture documented
- [x] monorepo documented
- [x] Gitflow/SemVer/Conventional Commits documented
- [x] hackathon alignment contract documented
- [x] ADK runtime contract documented
- [x] graph-first orchestration contract documented
- [x] ADR 0005 accepted
- [ ] README spin-up instructions
- [ ] architecture diagram finalized from implemented system
- [ ] <=4-minute public demo
- [ ] visible GCP backend proof
- [ ] Taskmaster selected
- [ ] project/code built within contest period
- [ ] authorized third-party integrations

### Score/advantage targets

- [ ] graph-first hybrid ADK workflow implemented
- [ ] deterministic parallel fan-out + join
- [ ] fixed routing avoids unnecessary Gemini calls
- [ ] resumable/recoverable ADK investigation
- [ ] human clarification pause/resume
- [ ] ADK evaluation results
- [ ] graph/node logs/traces proving execution
- [ ] canonical model-call budget documented
- [ ] real authorized outbound action
- [ ] repeated deployed E2E success

### Bonus targets

- [ ] public build content (+up to 0.2)
- [ ] qualifying social post (+up to 0.2)
- [ ] EmbeddingGemma successful integration (+0.2 if accepted/verified)
- [ ] MedGemma only if successful and useful (+0.2 if accepted/verified)

Rules: https://allthingsagentichackathon.devpost.com/rules  
Resources: https://allthingsagentichackathon.devpost.com/resources

## 6. Winning Loop

```text
build cleanly
  ↓
test deterministic layers
  ↓
test graph routing + fan-out/join
  ↓
evaluate Gemini trajectory + output
  ↓
deploy
  ↓
observe
  ↓
prove real action
  ↓
measure model/function/tool calls
  ↓
document
  ↓
demo
  ↓
submit
```

Ngabo should compete on **high-value autonomous execution + disciplined deterministic/agentic separation + architectural clarity + evaluated agent behavior + credible AMR framing + undeniable proof of action**, not agent count or feature count.
