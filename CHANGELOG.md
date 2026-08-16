# Changelog

All notable changes to Ngabo will be documented in this file.

The project uses Semantic Versioning and Conventional Commits.

## [Unreleased]

### Added

- Product/release roadmap and release governance.
- Clean Architecture + monorepo contract and ADR.
- Hackathon alignment, ADK runtime, graph-first orchestration, long-running state/freshness, UI/UX, data/safety/evaluation and implementation contracts.
- `docs/OPERATIONAL_UTILITY_EVALUATION.md` for BYOF before-vs-after workflow measurement.
- `docs/THIRD_PARTY_PROVENANCE.md` for dependency/data/evidence/pre-existing-work compliance.
- `docs/SUBMISSION_EVIDENCE.md` for claim-to-proof gating.
- `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md` defining the literal zero-human Taskmaster hero and deterministic A0/A1/A2/A3 action envelope.
- `docs/BYOF_FRICTION.md` grounding the Taskmaster personal-friction story in the builder's repeated AMR research/coordination workflow.
- `docs/ADK_CAPABILITY_SPIKE.md` requiring exact-version runtime/API validation before production agent implementation.
- `docs/SUBMISSION_FREEZE.md` defining immutable judged release/deployment/video evidence.
- `docs/ARCHITECTURE_DIAGRAM.md` with a judge-facing target architecture visual.
- `docs/HACKATHON_RISK_REGISTER.md` mapping competition, safety, API, proof and submission risks to closure evidence.

### Changed

- The canonical v0.1 Taskmaster hero now completes from surveillance event to real external coordination action and machine acknowledgement with **zero human intervention**.
- Hero requirements are now `0` prompts, `0` human interventions, `0` active human steps, `0` clarifications and `0` approval clicks after the event trigger.
- Ngabo no longer relies on human approval to make the hackathon hero safe. Instead the autonomous action envelope is deterministically constrained: A1 safe external coordination may auto-execute; A2 real operational escalation is outside the public-v0.1 auto lane by default; A3 clinical/official public-health decisions are never autonomous in v0.1.
- Missing material data now causes autonomous abstention rather than mandatory clarification or fabricated completion.
- Model-output defects use deterministic validation plus a bounded automatic repair loop; exhausted repair budgets stop safely.
- Pre-action freshness now protects every autonomous A1 external action, not only previously human-approved actions.
- The hero external integration now requires a **machine acknowledgement** so the Taskmaster loop closes without a person clicking acknowledge.
- The BYOF benchmark now explicitly compares the builder's manual AMR research/coordination workflow against the zero-human Ngabo hero.
- The canonical demo storyboard no longer spends the hero path on clarification/resume/human approval; those remain secondary evaluation/engineering scenarios.
- ADK implementation now requires a pinned-version capability spike with a documented fallback ladder if workshop terminology differs from the supported Python APIs.
- README, PRD, System Design, Agent Architecture, orchestration, long-running, UI/UX, safety/evaluation, submission evidence, implementation plan, `CLAUDE.md`, and `AGENTS.md` were synchronized around the safe zero-human design.

## [0.1.0] — Planned

### Goal

First working hackathon MVP demonstrating:

```text
synthetic AMR data
→ deterministic validation / surveillance signal
→ Pub/Sub-triggered Google ADK workflow
→ deterministic parallel investigation + join
→ bounded Gemini reasoning + approved evidence
→ deterministic package validation / bounded automatic repair
→ deterministic A1 autonomy policy
→ freshness + idempotency
→ real authorized external coordination action
→ machine acknowledgement
→ complete audit/observability trail
```

The canonical hero must complete with zero human intervention while A2/A3 clinical/official actions remain deterministically blocked from autonomous v0.1 execution.

`v0.1.0` has not yet been released.
