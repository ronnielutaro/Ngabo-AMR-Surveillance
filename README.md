# Ngabo

**Autonomous AMR Surveillance & Incident Response**

Ngabo is an open-source, event-driven prototype exploring how antimicrobial-resistance surveillance signals can be transformed into structured, evidence-backed investigations and coordinated **human-reviewed** response workflows.

> **Status:** All Things Agentic Hackathon 2026 MVP in development.  
> **Data:** Synthetic demonstration data only.  
> **Safety:** Ngabo is not a clinical diagnostic or prescribing system and does not autonomously confirm outbreaks.

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

## Documentation

Implementation source-of-truth:

- [`CLAUDE.md`](./CLAUDE.md) — Claude Code implementation contract
- [`AGENTS.md`](./AGENTS.md) — coding-agent execution rules
- [`docs/PRD.md`](./docs/PRD.md) — product requirements
- [`docs/TECH_STACK.md`](./docs/TECH_STACK.md) — stack decisions
- [`docs/SYSTEM_DESIGN.md`](./docs/SYSTEM_DESIGN.md) — architecture and event/state design
- [`docs/AGENT_ARCHITECTURE.md`](./docs/AGENT_ARCHITECTURE.md) — runtime agent design
- [`docs/DATA_SAFETY_EVALUATION.md`](./docs/DATA_SAFETY_EVALUATION.md) — data, safety and evaluation contracts
- [`docs/UI_UX_SPEC.md`](./docs/UI_UX_SPEC.md) — frontend implementation contract
- [`docs/IMPLEMENTATION_PLAN.md`](./docs/IMPLEMENTATION_PLAN.md) — milestone plan
- [`docs/adr/0001-hackathon-mvp-architecture.md`](./docs/adr/0001-hackathon-mvp-architecture.md) — frozen MVP architecture baseline

## Current Repository State

The repository is being initialized from design-first specifications. Application scaffolding and spin-up instructions will be added as implementation begins.

The final hackathon README must include complete local/cloud setup steps before submission.

## License

See [`LICENSE`](./LICENSE).
