# Ngabo

**Autonomous AMR Surveillance & Incident Response**

Ngabo is an **open-source, event-driven antimicrobial resistance surveillance and incident-response system** that transforms AMR surveillance signals into structured, evidence-backed investigations and coordinated **human-reviewed** response workflows.

> **Current release status:** `v0.1.0` hackathon MVP in development.  
> **Data:** Synthetic demonstration data only in the public v0.1 release.  
> **Safety:** Ngabo is not a clinical diagnostic or prescribing system and does not autonomously confirm outbreaks.

The word **MVP** describes the maturity of the current release—not Ngabo's product identity. See [`ROADMAP.md`](./ROADMAP.md) for the path from hackathon release through research evaluation, shadow-mode pilots, validation, production-candidate hardening, and `1.0.0`.

## Hackathon Target

Ngabo is being built for the **All Things Agentic Hackathon 2026** in **The Taskmaster** category.

The v0.1 design deliberately targets the hackathon's event-driven/autonomous workflow requirements:

```text
AMR data arrives
        ↓
deterministic surveillance signal
        ↓
Pub/Sub event
        ↓
Google ADK investigation graph starts automatically
        ↓
deterministic function-node fan-out + join
        ↓
Gemini 3.6 Flash reasons where ambiguity exists
        ↓
approved evidence + targeted clarification if needed
        ↓
resume same incident
        ↓
deterministically validated incident package
        ↓
human approval
        ↓
real authorized external action
        ↓
acknowledgement + audit/trace proof
```

Read [`docs/HACKATHON_ALIGNMENT.md`](./docs/HACKATHON_ALIGNMENT.md) for the formal compliance/scoring/bonus strategy, [`docs/ADK_RUNTIME.md`](./docs/ADK_RUNTIME.md) for the runtime contract, and [`docs/ORCHESTRATION_PATTERNS.md`](./docs/ORCHESTRATION_PATTERNS.md) for the graph/function/agent pattern-selection rules.

## Architecture

Ngabo is implemented using **Clean Architecture inside a monorepo**.

The dependency rule is:

```text
Frameworks / Infrastructure
          ↓
Interfaces / Adapters
          ↓
Application / Use Cases / Ports
          ↓
Domain / Entities / Value Objects / Domain Services
```

Dependencies point inward. AMR/domain/scientific policy does **not** depend directly on FastAPI, Firestore, Pub/Sub, Cloud Storage, Google ADK, Gemini, Gemma-family models, or frontend frameworks.

Repository shape:

```text
ngabo/
├── apps/
│   └── web/                  # Next.js incident-response console
├── services/
│   └── core/                 # FastAPI + deterministic core + ADK integration
├── data/                     # synthetic data, schemas, guidance
├── docs/                     # product, architecture, ADR, release docs
├── infra/                    # deployment/configuration
└── .github/                  # CI/repository automation
```

> **Monorepo does not mean monolith.** `ngabo-web` and `ngabo-core` remain independently deployable Cloud Run services.

Read [`docs/CLEAN_ARCHITECTURE.md`](./docs/CLEAN_ARCHITECTURE.md) and [`docs/adr/0003-clean-architecture-monorepo.md`](./docs/adr/0003-clean-architecture-monorepo.md) for the full implementation contract.

## Graph-First Agent Orchestration

Ngabo's v0.1 ADK runtime follows one rule:

> **Deterministic when the workflow is known; agentic when the decision is ambiguous; dynamic only when the workflow itself cannot reasonably be known in advance.**

Core investigation shape:

```text
incident context
      ↓
parallel deterministic fan-out
  ├── resistance-profile comparison
  ├── baseline summary
  └── missing-field assessment
      ↓
join
      ↓
Gemini triage
      ↓
evidence / targeted clarification
      ↓
Gemini evidence-grounded synthesis
      ↓
deterministic package validation
```

Fixed routing rules do not consume Gemini calls. Collaborative specialist agents are introduced only if evaluation shows a real benefit. Runtime-generated dynamic topology is deferred from the core v0.1 flow.

See [`docs/ORCHESTRATION_PATTERNS.md`](./docs/ORCHESTRATION_PATTERNS.md) and [`docs/adr/0005-adk-graph-first-orchestration.md`](./docs/adr/0005-adk-graph-first-orchestration.md).

## MVP Flow

```text
WHONET-style synthetic data
        ↓
deterministic validation + normalization
        ↓
deterministic surveillance detector
        ↓
suspicious AMR signal
        ↓
Pub/Sub event
        ↓
Google ADK graph
        ↓
parallel deterministic investigation + join
        ↓
Gemini 3.6 Flash triage / evidence reasoning
        ↓
targeted clarification when material
        ↓
resumable/recoverable investigation
        ↓
Gemini source-grounded synthesis
        ↓
deterministic package validation
        ↓
human review
        ↓
real authorized notification/action
        ↓
acknowledgement
        ↓
audit + observability trail
```

## Planned Stack

- **Architecture:** Clean Architecture
- **Repository:** GitHub monorepo
- **Frontend:** Next.js, TypeScript, Tailwind CSS, shadcn/ui
- **Backend:** Python, FastAPI, Pydantic v2
- **Agent runtime:** Google ADK (Python), graph-first hybrid orchestration
- **Primary model:** Gemini 3.6 Flash via Gemini API
- **Planned evidence retrieval model:** EmbeddingGemma, after core E2E is stable
- **Gated stretch model:** MedGemma, only if evaluation shows meaningful value
- **Analytics:** pandas, NumPy, SciPy
- **State:** Firestore
- **Files/evidence:** Cloud Storage
- **Events:** Pub/Sub
- **Compute:** Cloud Run
- **Observability:** Cloud Logging + supported ADK/Cloud Trace/OpenTelemetry integration
- **Testing:** pytest, ADK evaluations, Playwright

## Agent Runtime Discipline

Google ADK is not included merely to satisfy the hackathon checklist.

The v0.1 runtime is designed for:

- deterministic function/workflow nodes for known work;
- parallel fan-out/join for independent read-only calculations;
- deterministic routers for exhaustive rules;
- Gemini agent nodes only for bounded ambiguity/reasoning/synthesis;
- persisted agent session/invocation/run references;
- resumable investigation where supported/stable;
- targeted human-input pause/resume;
- deterministic package validation;
- ADK graph/trajectory evaluations;
- node/branch/join observability;
- explicit model/tool/time/retry limits.

Firestore remains Ngabo's canonical workflow/business state. ADK execution state complements it.

## Clean Architecture Boundaries

Backend target:

```text
services/core/ngabo/
├── domain/           # AMR entities, value objects, deterministic rules
├── application/      # use cases, workflows, ports/contracts
├── interfaces/       # FastAPI + event adapters
├── infrastructure/   # Firestore/GCS/PubSub/ADK/Gemini/Gemma/notifications
└── bootstrap/        # composition root / dependency wiring
```

Google ADK, Gemini, EmbeddingGemma, Firestore, Pub/Sub, Cloud Storage, and notification providers are outer infrastructure. Deterministic AMR/surveillance calculations live inward and must be testable without model/cloud access.

## Evidence Strategy

The approved evidence corpus is curated and source-traceable.

Core implementation can begin with deterministic/tag retrieval. After the deployed core workflow is stable, Ngabo plans to integrate **EmbeddingGemma** for semantic retrieval:

```text
approved guidance
      ↓
EmbeddingGemma embeddings
      ↓
lightweight cosine similarity
      ↓
source IDs + approved chunks
      ↓
Gemini reasoning/synthesis
```

No vector database is required merely for the hackathon bonus.

**MedGemma is optional** and will be included only if a bounded source-traceable role improves measured evaluation without weakening safety or demo reliability. Prefer it as a bounded specialist capability before considering a separate autonomous agent.

## Evaluation & Proof of Action

Before submission Ngabo will publish `EVALUATION.md` covering:

- deterministic detector/scenario tests;
- deterministic graph/function-node tests;
- fan-out/join and fixed-routing tests;
- ADK agentic-routing/trajectory evaluations where supported;
- model-call budget for the canonical scenario;
- prompt-injection and hallucination safety tests;
- clarification behavior;
- resumability/idempotency tests;
- deployed E2E runs;
- EmbeddingGemma retrieval evaluation if integrated;
- known limitations.

The hosted/filmed v0.1 is also required to perform at least one **real authorized external action after human approval**. A deterministic demo notification adapter remains available for tests/local reproducibility.

## Cloud Deployment Discipline

The hackathon deployment plan includes:

- Cloud Run minimum instances `0` unless justified;
- explicit max-instance caps;
- right-sized CPU/RAM;
- Google Cloud budget + email alert;
- Secret Manager/injected secrets;
- protected internal event endpoints;
- lightweight artifact/log retention;
- judge-accessible hosted deployment through the required judging window.

## Bonus Strategy

Planned only when real and demonstrable:

- public LinkedIn build article satisfying the hackathon-purpose-language requirement;
- LinkedIn/social post using `#AllThingsAgenticHackathon`;
- EmbeddingGemma successful integration.

Gated stretch:

- MedGemma if it adds evaluated value;
- collaborative specialist agents only if evaluation demonstrates a real benefit;
- multimodal AST/PDF extraction only as a **human-verified draft** after core freeze.

No bonus model or feature will be claimed if it exists only in documentation.

## Release & Engineering Governance

Ngabo uses:

- **Semantic Versioning 2.0.0** for releases;
- **Conventional Commits 1.0.0** for commit history;
- a **Gitflow-style workflow** adapted to `main` + `develop`;
- release tags `vMAJOR.MINOR.PATCH`;
- `CHANGELOG.md` for meaningful release history.

Primary branches:

```text
main       released / release-ready history
develop    integration for the next release
```

Supporting branches:

```text
feature/<name>
release/vX.Y.Z
hotfix/vX.Y.Z
```

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the workflow and [`ROADMAP.md`](./ROADMAP.md) for release maturity.

## Documentation

Implementation source-of-truth:

- [`CLAUDE.md`](./CLAUDE.md) — Claude Code implementation contract
- [`AGENTS.md`](./AGENTS.md) — coding-agent execution rules
- [`ROADMAP.md`](./ROADMAP.md) — product/release maturity roadmap
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — Gitflow, commits, PRs and releases
- [`CHANGELOG.md`](./CHANGELOG.md) — release history
- [`docs/PRD.md`](./docs/PRD.md) — product requirements
- [`docs/TECH_STACK.md`](./docs/TECH_STACK.md) — stack and architecture decisions
- [`docs/CLEAN_ARCHITECTURE.md`](./docs/CLEAN_ARCHITECTURE.md) — dependency/layer/monorepo contract
- [`docs/HACKATHON_ALIGNMENT.md`](./docs/HACKATHON_ALIGNMENT.md) — hackathon requirements, scoring and bonus strategy
- [`docs/ADK_RUNTIME.md`](./docs/ADK_RUNTIME.md) — ADK graph runtime, resumability and evaluation contract
- [`docs/ORCHESTRATION_PATTERNS.md`](./docs/ORCHESTRATION_PATTERNS.md) — graph/function/agent/routing pattern-selection contract
- [`docs/SYSTEM_DESIGN.md`](./docs/SYSTEM_DESIGN.md) — system/event/state/graph design
- [`docs/AGENT_ARCHITECTURE.md`](./docs/AGENT_ARCHITECTURE.md) — runtime agent and graph design
- [`docs/DATA_SAFETY_EVALUATION.md`](./docs/DATA_SAFETY_EVALUATION.md) — data, safety and evaluation contracts
- [`docs/UI_UX_SPEC.md`](./docs/UI_UX_SPEC.md) — frontend implementation contract
- [`docs/UI_UX_HACKATHON_ADDENDUM.md`](./docs/UI_UX_HACKATHON_ADDENDUM.md) — demo/resume/action UI requirements
- [`docs/IMPLEMENTATION_PLAN.md`](./docs/IMPLEMENTATION_PLAN.md) — milestone plan
- [`docs/adr/0001-hackathon-mvp-architecture.md`](./docs/adr/0001-hackathon-mvp-architecture.md) — MVP architecture baseline
- [`docs/adr/0002-release-governance.md`](./docs/adr/0002-release-governance.md) — release governance decision
- [`docs/adr/0003-clean-architecture-monorepo.md`](./docs/adr/0003-clean-architecture-monorepo.md) — Clean Architecture + monorepo decision
- [`docs/adr/0004-hackathon-agent-runtime-and-bonus-models.md`](./docs/adr/0004-hackathon-agent-runtime-and-bonus-models.md) — hackathon runtime/bonus architecture decision
- [`docs/adr/0005-adk-graph-first-orchestration.md`](./docs/adr/0005-adk-graph-first-orchestration.md) — graph-first hybrid orchestration decision

## Current Repository State

The repository is being initialized from design-first specifications. Application scaffolding and complete local/cloud spin-up instructions will be added as implementation begins.

## License

See [`LICENSE`](./LICENSE).
