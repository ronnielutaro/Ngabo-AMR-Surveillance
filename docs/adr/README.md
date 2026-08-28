# Architecture Decision Records

Architecture Decision Records (ADRs) capture material technical or engineering-governance decisions that should not be changed silently.

Current ADRs:

- `0001-hackathon-mvp-architecture.md` — MVP architecture baseline
- `0002-release-governance.md` — Semantic Versioning, Conventional Commits, and Gitflow
- `0003-clean-architecture-monorepo.md` — Clean Architecture and monorepo implementation model
- `0004-hackathon-agent-runtime-and-bonus-models.md` — hackathon agent-runtime, proof-of-action, and bonus-model strategy
- `0005-adk-graph-first-orchestration.md` — graph-first hybrid ADK orchestration and deterministic-vs-agentic routing
- `0006-long-running-agent-state-and-freshness.md` — long-running state, context/memory boundaries, pre-action freshness, and recovery
- `0007-zero-human-safe-coordination.md` — zero-human Taskmaster hero via bounded A1 safe coordination rather than autonomous clinical/official action
- `0008-autonomous-action-outbox.md` — transactional action-intent/outbox and idempotent external-effect execution
- `0009-proof-carrying-reasoning.md` — machine-verifiable evidence/reference contracts for model-generated claims before autonomous action
- `0010-v0.1-resistance-profile-similarity-policy.md` — v0.1 maintainer-approved resistance-profile similarity policy and non-clinical prototype boundaries
- `0011-v0.1-temporal-location-concentration-policy.md` — v0.1 maintainer-approved temporal and location concentration policy and descriptive measurement boundaries
- `0012-v0.1-investigation-priority-signal-policy.md` — v0.1 maintainer-approved investigation-priority signal policy, composite scoring, and triage boundaries

## Supersession Note

ADR 0007 supersedes older v0.1 wording that required human clarification or approval inside the **canonical hackathon hero path**.

Human-governed consequential patterns remain valid for future A2/A3 real-world workflows and secondary evaluation scenarios.

For the current hero, read ADRs 0007–0009 together with:

- `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`
- `docs/AUTONOMOUS_EFFECT_OUTBOX.md`
- `docs/PROOF_CARRYING_REASONING.md`
- `docs/HACKATHON_ALIGNMENT.md`
- `docs/LONG_RUNNING_AGENT.md`

## When to Create an ADR

Create an ADR when a change materially affects:

- core architecture;
- persistence/event model;
- AI orchestration framework;
- deterministic vs agentic responsibility boundaries;
- long-running execution or memory/context policy;
- autonomous/human safety boundary;
- action authorization/effect semantics;
- model-claim verification / evidence authority;
- major infrastructure selection;
- release/versioning governance.

Routine refactors preserving existing contracts do not need an ADR.
