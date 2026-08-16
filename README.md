# Ngabo

**Autonomous AMR Surveillance & Incident Response**

Ngabo is an **open-source, event-driven antimicrobial resistance surveillance and incident-response system** that transforms AMR surveillance signals into structured, evidence-backed investigations and coordinated **human-reviewed** response workflows.

> **Current release status:** `v0.1.0` hackathon MVP in development.  
> **Data:** Synthetic demonstration data only in the public v0.1 release.  
> **Safety:** Ngabo is not a clinical diagnostic or prescribing system and does not autonomously confirm outbreaks.

The word **MVP** describes the maturity of the current release—not Ngabo's product identity. See [`ROADMAP.md`](./ROADMAP.md) for the path from the hackathon release through research evaluation, shadow-mode pilots, validation, production-candidate hardening, and `1.0.0`.

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

- **Frontend:** Next.js, TypeScript, Tailwind CSS, shadcn/ui
- **Backend:** Python, FastAPI, Pydantic v2
- **Agent:** Google ADK (Python), Gemini 3.6 Flash
- **Analytics:** pandas, NumPy, SciPy
- **State:** Firestore
- **Files/evidence:** Cloud Storage
- **Events:** Pub/Sub
- **Compute:** Cloud Run
- **Testing:** pytest, ADK evals, Playwright

## Release & Engineering Governance

Ngabo uses:

- **Semantic Versioning 2.0.0** for releases;
- **Conventional Commits 1.0.0** for commit history;
- a **Gitflow-style workflow** adapted to `main` + `develop`;
- release tags in the form `vMAJOR.MINOR.PATCH`;
- `CHANGELOG.md` for user/operator-visible release history.

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

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the contribution/release workflow and [`ROADMAP.md`](./ROADMAP.md) for release maturity.

## Documentation

Implementation source-of-truth:

- [`CLAUDE.md`](./CLAUDE.md) — Claude Code implementation contract
- [`AGENTS.md`](./AGENTS.md) — coding-agent execution rules
- [`ROADMAP.md`](./ROADMAP.md) — product maturity and release roadmap
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — Gitflow, SemVer, Conventional Commits, PR and release rules
- [`CHANGELOG.md`](./CHANGELOG.md) — release history
- [`docs/PRD.md`](./docs/PRD.md) — product requirements
- [`docs/TECH_STACK.md`](./docs/TECH_STACK.md) — stack decisions
- [`docs/SYSTEM_DESIGN.md`](./docs/SYSTEM_DESIGN.md) — architecture and event/state design
- [`docs/AGENT_ARCHITECTURE.md`](./docs/AGENT_ARCHITECTURE.md) — runtime agent design
- [`docs/DATA_SAFETY_EVALUATION.md`](./docs/DATA_SAFETY_EVALUATION.md) — data, safety and evaluation contracts
- [`docs/UI_UX_SPEC.md`](./docs/UI_UX_SPEC.md) — frontend implementation contract
- [`docs/IMPLEMENTATION_PLAN.md`](./docs/IMPLEMENTATION_PLAN.md) — milestone plan
- [`docs/adr/0001-hackathon-mvp-architecture.md`](./docs/adr/0001-hackathon-mvp-architecture.md) — frozen MVP architecture baseline

## Release Path

```text
0.1.x  Hackathon MVP
  ↓
0.2.x  Technical Prototype
  ↓
0.3.x  Research Prototype
  ↓
0.4.x  Shadow-Mode Pilot
  ↓
0.5.x  Validation & Pilot Hardening
  ↓
0.9.x  Production Candidate
  ↓
1.0.0  Production-Ready Release
```

Release numbers communicate software maturity and compatibility. They do **not** replace scientific, clinical, regulatory, security, or governance evidence required for the intended use.

## Current Repository State

The repository is being initialized from design-first specifications. Application scaffolding and complete spin-up instructions will be added as implementation begins.

The final hackathon README must include complete local/cloud setup steps before submission.

## License

See [`LICENSE`](./LICENSE).
