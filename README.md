# Ngabo

**Autonomous AMR Surveillance & Incident Response**

Ngabo is an **open-source, event-driven antimicrobial resistance surveillance and incident-response system** that transforms AMR surveillance signals into structured, evidence-backed investigations and coordinated **human-reviewed** response workflows.

> **Current release status:** `v0.1.0` hackathon MVP in development.  
> **Data:** Synthetic demonstration data only in the public v0.1 release.  
> **Safety:** Ngabo is not a clinical diagnostic or prescribing system and does not autonomously confirm outbreaks.

The word **MVP** describes the maturity of the current release—not Ngabo's product identity. See [`ROADMAP.md`](./ROADMAP.md) for the path from the hackathon release through research evaluation, shadow-mode pilots, validation, production-candidate hardening, and `1.0.0`.

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

Dependencies point inward. AMR/domain/scientific policy does **not** depend directly on FastAPI, Firestore, Pub/Sub, Cloud Storage, Google ADK, Gemini, or frontend frameworks.

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
Google ADK + Gemini investigation
        ↓
evidence + targeted clarification
        ↓
structured incident package
        ↓
human review
        ↓
notification + acknowledgement
        ↓
audit trail
```

## Planned Stack

- **Architecture:** Clean Architecture
- **Repository:** GitHub monorepo
- **Frontend:** Next.js, TypeScript, Tailwind CSS, shadcn/ui
- **Backend:** Python, FastAPI, Pydantic v2
- **Agent:** Google ADK (Python), Gemini 3.6 Flash
- **Analytics:** pandas, NumPy, SciPy
- **State:** Firestore
- **Files/evidence:** Cloud Storage
- **Events:** Pub/Sub
- **Compute:** Cloud Run
- **Testing:** pytest, ADK evals, Playwright

## Clean Architecture Boundaries

Backend target:

```text
services/core/ngabo/
├── domain/           # AMR entities, value objects, deterministic rules
├── application/      # use cases, workflows, ports/contracts
├── interfaces/       # FastAPI + event adapters
├── infrastructure/   # Firestore/GCS/PubSub/ADK/Gemini/notifications
└── bootstrap/        # composition root / dependency wiring
```

Google ADK and Gemini are outer infrastructure. Deterministic AMR/surveillance calculations live inward and must be testable without model/cloud access.

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
- [`docs/CLEAN_ARCHITECTURE.md`](./docs/CLEAN_ARCHITECTURE.md) — dependency/layer/monorepo implementation contract
- [`docs/SYSTEM_DESIGN.md`](./docs/SYSTEM_DESIGN.md) — system/event/state design
- [`docs/AGENT_ARCHITECTURE.md`](./docs/AGENT_ARCHITECTURE.md) — runtime agent design
- [`docs/DATA_SAFETY_EVALUATION.md`](./docs/DATA_SAFETY_EVALUATION.md) — data, safety and evaluation contracts
- [`docs/UI_UX_SPEC.md`](./docs/UI_UX_SPEC.md) — frontend implementation contract
- [`docs/IMPLEMENTATION_PLAN.md`](./docs/IMPLEMENTATION_PLAN.md) — milestone plan
- [`docs/adr/0001-hackathon-mvp-architecture.md`](./docs/adr/0001-hackathon-mvp-architecture.md) — MVP architecture baseline
- [`docs/adr/0002-release-governance.md`](./docs/adr/0002-release-governance.md) — release governance decision
- [`docs/adr/0003-clean-architecture-monorepo.md`](./docs/adr/0003-clean-architecture-monorepo.md) — Clean Architecture + monorepo decision

## Current Repository State

The repository is being initialized from design-first specifications. Application scaffolding and complete local/cloud spin-up instructions will be added as implementation begins.

## License

See [`LICENSE`](./LICENSE).
