# Ngabo

**Autonomous AMR Surveillance & Incident Response**

Ngabo is an **open-source, event-driven antimicrobial resistance surveillance and incident-response system** that transforms AMR surveillance signals into structured, evidence-backed investigations and coordinated **human-reviewed** response workflows.

> **Current release status:** `v0.1.0` hackathon MVP in development.  
> **Data:** Synthetic demonstration data only in the public v0.1 release.  
> **Safety:** Ngabo is not a clinical diagnostic or prescribing system and does not autonomously confirm outbreaks.

The word **MVP** describes the maturity of the current release—not Ngabo's product identity. See [`ROADMAP.md`](./ROADMAP.md) for the path from hackathon release through research evaluation, shadow-mode pilots, validation, production-candidate hardening, and `1.0.0`.

## Hackathon Target

Ngabo is being built for the **All Things Agentic Hackathon 2026** in **The Taskmaster** category.

The v0.1 design deliberately targets a complete event-driven autonomous workflow rather than a chat loop:

```text
AMR data arrives
        ↓
deterministic surveillance signal
        ↓
Pub/Sub event
        ↓
Google ADK investigation graph starts automatically
        ↓
load canonical incident context
        ↓
deterministic function-node fan-out + join
        ↓
Gemini 3.6 Flash reasons where ambiguity exists
        ↓
approved evidence + targeted clarification if needed
        ↓
resume same incident using current canonical state
        ↓
deterministically validated incident package
        ↓
human consequential-action approval
        ↓
deterministic pre-action freshness barrier
   ├─ stale → invalidate approval / re-review
   └─ fresh → continue
        ↓
real authorized external action
        ↓
acknowledgement + audit/trace proof
```

The human does not manually drive the investigation. Human input is reserved for a materially missing fact when required and the consequential public-health action boundary.

Read [`docs/HACKATHON_ALIGNMENT.md`](./docs/HACKATHON_ALIGNMENT.md) for the formal scoring/prize/submission strategy, [`docs/ADK_RUNTIME.md`](./docs/ADK_RUNTIME.md) for runtime details, [`docs/ORCHESTRATION_PATTERNS.md`](./docs/ORCHESTRATION_PATTERNS.md) for pattern selection, and [`docs/LONG_RUNNING_AGENT.md`](./docs/LONG_RUNNING_AGENT.md) for long-running state/freshness rules.

## Architecture

Ngabo is implemented using **Clean Architecture inside a monorepo**.

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

Read [`docs/CLEAN_ARCHITECTURE.md`](./docs/CLEAN_ARCHITECTURE.md) and [`docs/adr/0003-clean-architecture-monorepo.md`](./docs/adr/0003-clean-architecture-monorepo.md).

## Graph-First Agent Orchestration

Ngabo's v0.1 runtime follows one rule:

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

## Long-Running State & Freshness

Ngabo treats workflow continuity and incident truth as different concerns:

```text
Firestore/application state = canonical incident/workflow truth
ADK session/checkpoint       = execution continuity only
transient state              = recomputable working values
Cloud Storage artifacts      = file-like outputs
long-term model memory       = non-authoritative for v0.1 incident facts
```

The governing rule is:

> **Resume execution, but revalidate truth.**

After a long wait or restart, Ngabo rebuilds current context from canonical state rather than trusting an old conversation/session summary.

Human approval is version-scoped. Before consequential external action, Ngabo executes a deterministic freshness check. If incident/package/source data changed materially after review, the old approval becomes stale and the incident returns to review instead of acting on outdated information.

See [`docs/LONG_RUNNING_AGENT.md`](./docs/LONG_RUNNING_AGENT.md) and [`docs/adr/0006-long-running-agent-state-and-freshness.md`](./docs/adr/0006-long-running-agent-state-and-freshness.md).

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
resumable/recoverable investigation using current canonical state
        ↓
Gemini source-grounded synthesis
        ↓
deterministic package validation
        ↓
human review
        ↓
deterministic freshness validation
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
- current-context reconstruction after waits/restarts;
- targeted human-input pause/resume;
- deterministic package and freshness validation;
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

The approved evidence corpus is curated, source-traceable, and subject to provenance/usage-right review.

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

**MedGemma is optional** and will be included only if a bounded source-traceable role improves measured evaluation without weakening safety or demo reliability.

See [`docs/THIRD_PARTY_PROVENANCE.md`](./docs/THIRD_PARTY_PROVENANCE.md) for dependency/data/evidence provenance and pre-existing-work disclosure rules.

## Evaluation, Operational Utility & Proof of Action

Before submission Ngabo will publish `EVALUATION.md` covering:

- deterministic detector/scenario tests;
- deterministic graph/function-node tests;
- fan-out/join and fixed-routing tests;
- ADK observable trajectory evaluations where supported;
- model-call budget for canonical scenario;
- prompt-injection and hallucination safety tests;
- clarification behavior;
- resumability/idempotency/context-rebuild tests;
- stale-approval/freshness tests;
- deployed E2E runs;
- operational-utility before-vs-after workflow benchmark;
- EmbeddingGemma retrieval evaluation if integrated;
- known limitations.

Operational-utility evidence will measure real synthetic/deployed execution facts such as zero prompts required to start, human intervention/active-step counts, signal-to-review-ready latency, clarification count and model/function/tool trajectory. It will not invent hospital time-saved percentages.

See [`docs/OPERATIONAL_UTILITY_EVALUATION.md`](./docs/OPERATIONAL_UTILITY_EVALUATION.md).

The hosted/filmed v0.1 is also required to perform at least one **real authorized external action after human approval and freshness validation**. A deterministic demo notification adapter remains available for tests/local reproducibility.

## Cloud Deployment Discipline

The hackathon deployment plan includes:

- Cloud Run minimum instances `0` unless justified;
- explicit max-instance caps;
- right-sized CPU/RAM;
- Google Cloud budget + email alert;
- Secret Manager/injected secrets;
- protected internal event endpoints;
- lightweight artifact/log retention;
- ADK Web local-development only;
- judge-accessible hosted deployment through the required judging window.

## Submission Evidence

Ngabo maintains a submission proof ledger in [`docs/SUBMISSION_EVIDENCE.md`](./docs/SUBMISSION_EVIDENCE.md).

It maps every competitive claim to an actual artifact, including:

- hosted URL;
- repository/spin-up instructions;
- architecture diagram;
- <=4-minute demo video;
- Google Cloud proof;
- live Proof of Action;
- evaluation results;
- operational-utility results;
- real action/acknowledgement;
- resume/freshness proof;
- third-party/pre-existing-work disclosure;
- bonus-model/content evidence.

**Architecture intent is not treated as execution proof.** Anything unimplemented at submission freeze must be removed from competitive claims or clearly labelled future work.

## Bonus Strategy

Planned only when real and demonstrable:

- public LinkedIn build article satisfying the hackathon-purpose-language requirement;
- LinkedIn/social post using `#AllThingsAgenticHackathon`;
- EmbeddingGemma successful integration.

Gated stretch:

- MedGemma if it adds evaluated value;
- collaborative specialist agents only if evaluation demonstrates real benefit;
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

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) and [`ROADMAP.md`](./ROADMAP.md).

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
- [`docs/HACKATHON_ALIGNMENT.md`](./docs/HACKATHON_ALIGNMENT.md) — hackathon judging/prize/submission strategy
- [`docs/ADK_RUNTIME.md`](./docs/ADK_RUNTIME.md) — ADK runtime/resumability/evaluation contract
- [`docs/ORCHESTRATION_PATTERNS.md`](./docs/ORCHESTRATION_PATTERNS.md) — graph/function/agent/routing contract
- [`docs/LONG_RUNNING_AGENT.md`](./docs/LONG_RUNNING_AGENT.md) — state/context/memory/freshness/recovery contract
- [`docs/SYSTEM_DESIGN.md`](./docs/SYSTEM_DESIGN.md) — system/event/state/graph design
- [`docs/AGENT_ARCHITECTURE.md`](./docs/AGENT_ARCHITECTURE.md) — runtime agent and graph design
- [`docs/DATA_SAFETY_EVALUATION.md`](./docs/DATA_SAFETY_EVALUATION.md) — data, safety and multi-layer evaluation
- [`docs/OPERATIONAL_UTILITY_EVALUATION.md`](./docs/OPERATIONAL_UTILITY_EVALUATION.md) — workflow-friction benchmark contract
- [`docs/UI_UX_SPEC.md`](./docs/UI_UX_SPEC.md) — frontend implementation contract
- [`docs/UI_UX_HACKATHON_ADDENDUM.md`](./docs/UI_UX_HACKATHON_ADDENDUM.md) — demo/graph/resume/freshness/action UI requirements
- [`docs/THIRD_PARTY_PROVENANCE.md`](./docs/THIRD_PARTY_PROVENANCE.md) — dependency/data/evidence licensing/provenance + pre-existing work register
- [`docs/SUBMISSION_EVIDENCE.md`](./docs/SUBMISSION_EVIDENCE.md) — competitive claim/proof ledger
- [`docs/IMPLEMENTATION_PLAN.md`](./docs/IMPLEMENTATION_PLAN.md) — milestone plan
- [`docs/adr/0001-hackathon-mvp-architecture.md`](./docs/adr/0001-hackathon-mvp-architecture.md) — MVP architecture baseline
- [`docs/adr/0002-release-governance.md`](./docs/adr/0002-release-governance.md) — release governance decision
- [`docs/adr/0003-clean-architecture-monorepo.md`](./docs/adr/0003-clean-architecture-monorepo.md) — Clean Architecture + monorepo decision
- [`docs/adr/0004-hackathon-agent-runtime-and-bonus-models.md`](./docs/adr/0004-hackathon-agent-runtime-and-bonus-models.md) — runtime/bonus architecture decision
- [`docs/adr/0005-adk-graph-first-orchestration.md`](./docs/adr/0005-adk-graph-first-orchestration.md) — graph-first hybrid orchestration decision
- [`docs/adr/0006-long-running-agent-state-and-freshness.md`](./docs/adr/0006-long-running-agent-state-and-freshness.md) — long-running state/freshness/memory decision

## Current Repository State

The repository is being initialized from design-first specifications. Application scaffolding and complete local/cloud spin-up instructions will be added as implementation begins.

## License

See [`LICENSE`](./LICENSE).
