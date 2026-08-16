# Architecture Decision Records

Architecture Decision Records (ADRs) capture material technical or engineering-governance decisions that should not be changed silently.

Current ADRs:

- `0001-hackathon-mvp-architecture.md` — MVP architecture baseline
- `0002-release-governance.md` — Semantic Versioning, Conventional Commits, and Gitflow

## When to create an ADR

Create an ADR when a change materially affects:

- core architecture;
- persistence/event model;
- AI orchestration framework;
- deterministic vs agentic responsibility boundaries;
- human-review/safety boundary;
- major infrastructure selection;
- release/versioning governance.

Routine refactors that preserve existing contracts do not need an ADR.
