# Ngabo — Implementation Plan

**Version:** 0.3  
**Created:** 2026-08-16  
**Official hackathon deadline:** 2026-08-31, 5:00 PM Pacific Time

## 1. Principle

> **Do not spend the final 48 hours implementing core architecture.**

Feature-complete several days early; reserve the end for evaluation, deployment proof, UI polish, article, demo, and submission.

All implementation must preserve:

- **Clean Architecture** dependency boundaries;
- the **monorepo** structure;
- deterministic scientific logic;
- bounded agentic autonomy;
- Gitflow / SemVer / Conventional Commits governance.

See `docs/CLEAN_ARCHITECTURE.md` before coding.

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
ADK/Gemini adapter + agent tools
   ↓
agent investigation
   ↓
clarification
   ↓
incident package
   ↓
human approval
   ↓
notification + acknowledgement
   ↓
Next.js incident console
   ↓
Cloud deployment
   ↓
evaluation
   ↓
demo + article + Devpost
```

## Aug 16 — Freeze Design & Handoff Contract

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
- [x] `CLAUDE.md` implementation contract
- [x] `AGENTS.md` coding-agent rules
- [x] GitHub repository + `develop` branch
- [x] README/document map
- [x] LICENSE + SECURITY.md
- [x] Copy implementation design docs into repository

**Exit:** Claude Code can begin Milestone 1 without guessing the product, UI, safety model, agent boundary, release workflow, repository shape, or architecture dependency direction.

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
- [ ] infrastructure adapter folders
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
- [ ] incident state machine
- [ ] state-transition tests

### Architecture acceptance

- [ ] domain imports no FastAPI/GCP/ADK/Gemini SDKs
- [ ] application imports no concrete cloud/model SDKs
- [ ] framework adapters remain empty/thin scaffolds until needed
- [ ] domain tests run without network/cloud/model access

Optional implementation aid:

- [ ] use official Google ADK/Agents CLI tooling if useful, but **do not let generated scaffolding replace the established monorepo/Clean Architecture structure**.

**Exit:** monorepo builds; Clean Architecture package boundaries exist; domain/state-policy tests are green.

## Aug 18 — Synthetic Data + Deterministic Ingestion

- [ ] supported input columns
- [ ] baseline dataset
- [ ] seeded suspicious cluster
- [ ] malformed/noisy dataset
- [ ] canonical input/domain mappings
- [ ] parser/normalizer as deterministic inner logic where appropriate
- [ ] file-storage port
- [ ] import repository port
- [ ] import use case
- [ ] thin FastAPI import interface
- [ ] validation report
- [ ] duplicate handling
- [ ] file hashing

**Architecture check:** FastAPI route translates input and invokes a use case; it does not own parsing/scientific policy.

**Exit:** CSV → canonical isolates + validation report through the real application boundary.

## Aug 19 — Deterministic Surveillance Engine

- [ ] resistance representation/value objects
- [ ] similarity method
- [ ] temporal concentration
- [ ] ward concentration
- [ ] baseline comparison
- [ ] signal score
- [ ] trigger explanation
- [ ] surveillance use case
- [ ] scenario tests

**Architecture check:** pure surveillance calculations run without FastAPI, Firestore, Pub/Sub, ADK, Gemini, or network access.

**Exit:** seeded signal detected deterministically.

## Aug 20–21 — Application Agent Contract + ADK/Gemini Infrastructure

### Inner contracts

- [ ] define agent-investigation application port
- [ ] define evidence-search port
- [ ] define incident-context queries/use cases
- [ ] define structured incident-package schema/contract

### ADK/Gemini adapter

- [ ] implement Google ADK under `infrastructure/ai/adk`
- [ ] configure Gemini 3.6 Flash under infrastructure/model provider
- [ ] local ADK playground/eval workflow

### Tools

- [ ] incident context
- [ ] profile comparison
- [ ] baseline summary
- [ ] missing-fields assessment
- [ ] approved-guidance retrieval
- [ ] clarification request
- [ ] package preparation boundary
- [ ] tool logging
- [ ] max steps/timeouts
- [ ] citation validation
- [ ] prohibited-claim validation

**Architecture check:** ADK tool wrappers call application/domain contracts. They do not contain raw Firestore access plus business/scientific logic.

**Exit:** pre-created signal → valid evidence-backed incident package locally.

## Aug 22 — Persistence + Event Adapters

### Ports already defined inward

Implement concrete infrastructure adapters:

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
- [ ] resumable incident state
- [ ] idempotent redelivery behavior

**Architecture check:** event handlers translate events to application commands; Firestore mechanics do not leak into domain/application policy.

**Exit:** restart/retry cannot duplicate incident or side effect.

## Aug 23 — Human Gate + Action

- [ ] clarification use case + endpoint
- [ ] pause/resume workflow
- [ ] review use case
- [ ] approve
- [ ] reject
- [ ] request more info
- [ ] notification port
- [ ] demo notification infrastructure adapter
- [ ] real email/webhook adapter if stable
- [ ] acknowledgement use case

**Exit:** backend end-to-end workflow complete through Clean Architecture boundaries.

## Aug 24–25 — Next.js Incident Console

Implement against `docs/UI_UX_SPEC.md` and the frontend Clean Architecture section of `docs/CLEAN_ARCHITECTURE.md`.

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
- [ ] live agent/tool investigation timeline
- [ ] clarification card
- [ ] evidence-backed package
- [ ] source links/details
- [ ] human review panel
- [ ] response tracking
- [ ] loading/error/empty states
- [ ] demo reset/seeded scenario controls
- [ ] accessibility pass

**Architecture check:** React components do not call Firestore, Pub/Sub, Gemini, or cloud SDKs directly; API/SSE clients remain infrastructure concerns.

**Exit:** non-developer understands the autonomous flow from UI alone; it does not look like a generic chatbot.

## Aug 26 — GCP Deployment + Composition

- [ ] billing alert
- [ ] Cloud Storage
- [ ] Firestore
- [ ] Pub/Sub
- [ ] `ngabo-core` Cloud Run
- [ ] `ngabo-web` Cloud Run
- [ ] secret handling
- [ ] Cloud Logging
- [ ] observability
- [ ] deployed URLs
- [ ] capture Cloud Run proof
- [ ] verify production composition root wires concrete adapters to inward-defined ports

**Exit:** full scenario works on Google Cloud with two independently deployable monorepo applications.

## Aug 27 — Evaluation

- [ ] pure domain test suite
- [ ] application-use-case tests with fakes
- [ ] infrastructure adapter/contract tests
- [ ] interface/API/event tests
- [ ] scenario benchmark
- [ ] ADK evals
- [ ] prompt injection test
- [ ] fabricated-source test
- [ ] hallucinated-isolate test
- [ ] prohibited clinical-claim tests
- [ ] duplicate-event test
- [ ] notification retry test
- [ ] end-to-end integration test
- [ ] architecture dependency audit
- [ ] `EVALUATION.md`
- [ ] metrics captured

**Exit:** demo is reproducible, architecture boundaries are intact, and limitations documented.

## Aug 28 — Technical Story

- [ ] final architecture diagram includes Clean Architecture + runtime/cloud views
- [ ] product screenshots
- [ ] LinkedIn Article draft
- [ ] explicitly state article was created for purposes of entering the hackathon
- [ ] domain/technical critique if feasible
- [ ] README spin-up instructions polished

## Aug 29–30 — Demo + Devpost

### Demo

- [ ] under 4 minutes
- [ ] problem in first ~30 seconds
- [ ] unedited live workflow
- [ ] visible Google Cloud execution
- [ ] architecture explanation
- [ ] safety boundary
- [ ] public YouTube/Vimeo video

### Devpost

- [ ] summary/features
- [ ] technology/data sources
- [ ] findings/learnings
- [ ] GitHub URL
- [ ] hosted URL
- [ ] architecture diagram
- [ ] reproducible spin-up instructions
- [ ] LinkedIn Article URL
- [ ] social post with `#AllThingsAgenticHackathon`
- [ ] final claims audit

**Internal target:** submission-ready by end of Aug 30.

## Aug 31 — Buffer + Submit

Only:

- critical fixes;
- link verification;
- final test;
- submission.

No major new features or architectural rewrites.

## 3. Stretch Order

Only after core is green:

1. real email/webhook;
2. parallel ADK investigation;
3. richer baseline visualization;
4. additional Google AI model if genuinely useful;
5. AMRFinderPlus genomics prototype.

> **Genomics is last, not first.**

## 4. Demo Freeze Rule

After three consecutive successful deployed end-to-end runs:

1. tag/record a demo candidate according to release policy;
2. stop architecture refactors;
3. fix only bugs and presentation problems.

## 5. Current Rule Checklist

- [ ] Gemini 3.5+
- [ ] qualifying Google Agent Framework
- [ ] Google Cloud infrastructure
- [ ] hosted project
- [x] repository
- [x] Clean Architecture documented
- [x] monorepo documented
- [x] Gitflow/SemVer/Conventional Commits documented
- [ ] final README spin-up instructions
- [ ] architecture diagram
- [ ] <=4 minute public demo
- [ ] visible Google Cloud backend execution
- [ ] one category selected
- [ ] project/code built within submission period as required
- [ ] authorized third-party integrations

Optional:

- [ ] public build content
- [ ] social post with `#AllThingsAgenticHackathon`
- [ ] additional Google AI model only if useful

Rules: https://allthingsagentichackathon.devpost.com/rules

## 6. Winning Loop

```text
build cleanly
  ↓
test at each architecture layer
  ↓
deploy
  ↓
measure
  ↓
document
  ↓
demo
  ↓
submit
```

Ngabo should win on **working autonomy + Clean Architecture discipline + credible health-domain framing + a clean demo**, not feature count.
