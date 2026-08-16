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
- `docs/LONG_RUNNING_AGENT.md` defining canonical-vs-session state, context compaction boundaries, long-running resume semantics, artifact policy, local-only ADK Web, no-A2A-v0.1, optional Scheduler→Pub/Sub follow-up, and a deterministic pre-action freshness barrier.
- ADR 0006 adopting long-running state, memory/context, freshness, and recovery boundaries.
- `docs/OPERATIONAL_UTILITY_EVALUATION.md` defining the before-vs-after workflow-friction benchmark for the hackathon's highest-weighted judging criterion.
- `docs/THIRD_PARTY_PROVENANCE.md` providing a submission-time register for dependencies, evidence/data sources, licensing/usage basis, attribution, and pre-existing-work disclosure.
- `docs/SUBMISSION_EVIDENCE.md` mapping Taskmaster, architectural-design, demo/production, prize, bonus, ownership, and compliance claims to required proof artifacts.

### Changed

- Product identity language now describes Ngabo as an AMR surveillance and incident-response **system**; maturity is communicated separately through release status.
- `v0.1.0` Definition of Done now requires a Pub/Sub-triggered ADK investigation, safe clarification/resume, documented agent evaluation, observability, and at least one real authorized external action after human approval.
- The ADK investigation is now explicitly graph-first: known reproducible steps use deterministic function nodes, independent calculations fan out and join, fixed routing avoids Gemini calls, and Gemini is reserved for genuinely ambiguous triage/evidence/synthesis decisions.
- Required deterministic investigation branches now include incident context, resistance-profile comparison, baseline summary, and missing-field assessment, with typed failure/join semantics.
- Collaborative specialist agents are gated by evaluation rather than used by default; runtime-generated dynamic workflow topology is deferred from the core v0.1 path.
- EmbeddingGemma remains the planned post-core semantic retrieval model over the approved evidence corpus; MedGemma remains a gated bounded specialist capability.
- Cloud deployment acceptance explicitly includes scale-to-zero, max-instance caps, budget alerts, secret isolation, protected event endpoints, and judge-accessible hosting.
- Human approval is now version-scoped: immediately before consequential external action, Ngabo must deterministically revalidate the incident/package/source-data state and return stale approvals to review instead of acting on changed information.
- ADK session/checkpoint state and compacted execution context are explicitly non-authoritative; canonical AMR facts are rebuilt from application state after resume or long waits.
- Unreviewed cross-incident agent memory is disabled as factual input to v0.1 investigations, and ADK Web is explicitly local-development only.
- Hackathon alignment, UI/UX, data/safety/evaluation, and Claude implementation contracts are synchronized around the graph-first runtime, freshness barrier, long-running truth model, and human-governance boundary.
- Operational utility is now a measured deliverable: zero-prompt start, human-touch reduction, signal-to-review-ready timing, and related metrics must be reported from real synthetic/deployed runs rather than estimated.
- Third-party SDK/model/data/evidence provenance and non-standard pre-existing-work disclosure are now explicit submission gates.
- Submission readiness now requires an evidence ledger that distinguishes architectural intent from actual hosted execution proof, measured evaluation, Google Cloud proof, and truthful bonus claims.

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
→ safe resume using current canonical state
→ evidence-grounded synthesis
→ deterministic package validation
→ human approval
→ deterministic pre-action freshness check
→ real authorized notification/action only if approval is still current
→ acknowledgement
→ audit/observability trail
→ measured operational-utility evidence
```

`v0.1.0` has not yet been released.
