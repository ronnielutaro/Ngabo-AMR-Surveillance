# Changelog

All notable changes to Ngabo will be documented in this file.

The project uses Semantic Versioning and Conventional Commits.

## [Unreleased]

### Added

- `docs/LEAN_CANVAS.md`, `docs/COMPETITOR_ANALYSIS.md` and `docs/VALUE_PROPOSITION_CANVAS.md` for evidence-disciplined product strategy, competitive positioning, segment-specific value propositions and post-hackathon validation priorities.
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
- `docs/PROOF_CARRYING_REASONING.md` defining typed model claims, deterministic evidence/reference verification, bounded automatic repair and abstention before autonomous action.
- ADR 0009 adopting proof-carrying reasoning as the model-to-action safety boundary.
- Explicit competition framing of **The Twist: Proof-Carrying Autonomy** across README, hackathon alignment, UI/demo, evidence and implementation contracts.

### Changed

- The canonical v0.1 Taskmaster hero now completes from surveillance event to real external coordination action and machine acknowledgement with **zero human intervention**.
- Hero requirements are `0` prompts, `0` human interventions, `0` active human steps, `0` clarifications and `0` approval clicks after the event trigger.
- Ngabo no longer relies on human approval to make the hackathon hero safe. Instead the autonomous action envelope is deterministically constrained: A1 safe external coordination may auto-execute; A2 real operational escalation is outside the public-v0.1 auto lane by default; A3 clinical/official public-health decisions are never autonomous in v0.1.
- Missing material data causes autonomous abstention rather than mandatory clarification or fabricated completion.
- Model-output defects use deterministic verification plus a bounded automatic repair loop; exhausted repair budgets stop safely.
- Model-generated factual/evidentiary/action-relevant claims must carry canonical record, deterministic finding and/or approved evidence references and pass deterministic verification before entering the A1 action path.
- Chain-of-thought/model confidence is explicitly non-authoritative; reasoning quality techniques never bypass machine verification.
- Pre-action freshness protects every autonomous A1 external action.
- Autonomous side effects use a transactional `ActionIntent`/outbox with stable idempotency semantics and machine acknowledgement.
- The BYOF benchmark explicitly compares the builder's manual AMR research/coordination workflow against the zero-human Ngabo hero.
- The canonical demo storyboard prioritizes zero-human execution and Proof-Carrying Autonomy rather than clarification/resume/human approval.
- ADK implementation requires a pinned-version capability spike with a documented fallback ladder if workshop terminology differs from supported Python APIs.
- README, Hackathon Alignment, ADK Runtime, System Design, Implementation Plan, UI/UX Hackathon Addendum, Submission Evidence and Risk Register were synchronized to the Proof-Carrying Autonomy pipeline.
- The risk register now explicitly covers competition-Twist visibility, fabricated/stale proof references, hypothesis/forbidden-claim escalation, cross-document drift, premature proof-carrying claims, and misrepresentation of software safety metrics.

## [0.1.0] — Planned

### Goal

First working hackathon MVP demonstrating:

```text
synthetic AMR data
→ deterministic validation / surveillance signal
→ Pub/Sub-triggered Google ADK workflow
→ deterministic parallel investigation + join
→ bounded Gemini reasoning + approved evidence
→ proof-carrying structured claims
→ deterministic claim/evidence verification
→ bounded automatic repair or safe abstention
→ deterministic A1 autonomy policy
→ freshness + transactional ActionIntent/idempotency
→ real authorized external coordination action
→ machine acknowledgement
→ complete audit/observability trail
```

The canonical hero must complete with zero human intervention while A2/A3 clinical/official actions remain deterministically blocked from autonomous v0.1 execution.

`v0.1.0` has not yet been released.
