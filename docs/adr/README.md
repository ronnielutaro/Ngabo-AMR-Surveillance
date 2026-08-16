# Architecture Decision Records

Architecture Decision Records (ADRs) capture material technical or engineering-governance decisions that should not be changed silently.

Current ADRs:

- `0001-hackathon-mvp-architecture.md` — MVP architecture baseline
- `0002-release-governance.md` — Semantic Versioning, Conventional Commits, and Gitflow
- `0003-clean-architecture-monorepo.md` — Clean Architecture and monorepo implementation model
- `0004-hackathon-agent-runtime-and-bonus-models.md` — hackathon agent-runtime, proof-of-action, and bonus-model strategy
- `0005-adk-graph-first-orchestration.md` — graph-first hybrid ADK orchestration and deterministic-vs-agentic routing
- `0006-long-running-agent-state-and-freshness.md` — long-running state, context/memory boundaries, pre-action freshness, and recovery

For long-running-agent, resumability, memory/context, review/action, or scheduled-follow-up work, read ADR 0006 together with `docs/LONG_RUNNING_AGENT.md`.

## When to create an ADR

Create an ADR when a change materially affects:

- core architecture;
- persistence/event model;
- AI orchestration framework;
- deterministic vs agentic responsibility boundaries;
- long-running execution or memory/context policy;
- human-review/safety boundary;
- major infrastructure selection;
- release/versioning governance.

Routine refactors that preserve existing contracts do not need an ADR.
