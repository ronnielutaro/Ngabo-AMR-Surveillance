# Changelog

All notable changes to Ngabo will be documented in this file.

The project uses [Semantic Versioning](https://semver.org/) and [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

## [Unreleased]

### Added

- Product and release roadmap.
- Claude Code and coding-agent implementation contracts.
- Product, system, agent, data/safety/evaluation, UI/UX, and implementation design documents.
- Release governance based on Semantic Versioning, Conventional Commits, and a Gitflow-style branch model.
- Clean Architecture + monorepo implementation contract and ADR.
- Hackathon alignment contract mapping the official Taskmaster requirements, judging criteria, proof-of-action expectations, bonus strategy, and GCP deployment controls.
- Google ADK runtime contract covering bounded tools, execution identity, resumability, human clarification, evaluation, observability, loop controls, and failure semantics.
- Hackathon UI/UX addendum for visible pause/resume, real-vs-demo actions, technical proof, and optional multimodal draft handling.
- ADR 0004 covering ADK runtime advantages, real external action, EmbeddingGemma, gated MedGemma, and post-core multimodal strategy.
- `docs/ORCHESTRATION_PATTERNS.md` defining Ngabo's graph-first hybrid ADK orchestration model, deterministic/agentic routing rules, parallel fan-out/join, selective collaborative agents, and deferred dynamic topology.
- ADR 0005 adopting graph-first hybrid orchestration for the v0.1 investigation path.

### Changed

- Product identity language now describes Ngabo as an AMR surveillance and incident-response **system**; maturity is communicated separately through release status.
- `v0.1.0` Definition of Done now requires a Pub/Sub-triggered ADK investigation, safe clarification/resume, documented agent evaluation, observability, and at least one real authorized external action after human approval.
- The ADK investigation is now explicitly graph-first: known reproducible steps use deterministic function nodes, independent calculations fan out and join, fixed routing avoids Gemini calls, and Gemini is reserved for genuinely ambiguous triage/evidence/synthesis decisions.
- Required deterministic investigation branches now include incident context, resistance-profile comparison, baseline summary, and missing-field assessment, with typed failure/join semantics.
- Collaborative specialist agents are gated by evaluation rather than used by default; runtime-generated dynamic workflow topology is deferred from the core v0.1 path.
- EmbeddingGemma remains the planned post-core semantic retrieval model over the approved evidence corpus; MedGemma remains a gated bounded specialist capability.
- Cloud deployment acceptance explicitly includes scale-to-zero, max-instance caps, budget alerts, secret isolation, protected event endpoints, and judge-accessible hosting.

## [0.1.0] — Planned

### Goal

First working hackathon MVP demonstrating:

```text
synthetic AMR data
→ deterministic validation
→ surveillance signal
→ Pub/Sub-triggered ADK graph
→ deterministic parallel investigation fan-out
→ join
→ bounded Gemini triage/evidence reasoning
→ clarification
→ safe resume
→ evidence-grounded synthesis
→ deterministic package validation
→ human approval
→ real authorized notification/action
→ acknowledgement
→ audit/observability trail
```

`v0.1.0` has not yet been released.
