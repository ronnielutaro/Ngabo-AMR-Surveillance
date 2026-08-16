# CLAUDE.md — Ngabo Implementation Contract

This file is the root implementation contract for Claude Code working on Ngabo.

**Project:** Ngabo — Autonomous AMR Surveillance & Incident Response  
**Competition:** All Things Agentic Hackathon 2026 — Taskmaster  
**Primary stack:** Next.js + TypeScript; Python + FastAPI; Google ADK; Gemini 3.6 Flash; Firestore; Cloud Storage; Pub/Sub; Cloud Run  
**Current release target:** `v0.1.0`  
**MVP deadline:** 2026-08-31, 5:00 PM Pacific Time

---

## 1. Read Before Editing Code

Before implementing or changing architecture, read these files in order:

1. `ROADMAP.md`
2. `CONTRIBUTING.md`
3. `docs/PRD.md`
4. `docs/TECH_STACK.md`
5. `docs/SYSTEM_DESIGN.md`
6. `docs/AGENT_ARCHITECTURE.md`
7. `docs/DATA_SAFETY_EVALUATION.md`
8. `docs/UI_UX_SPEC.md`
9. `docs/IMPLEMENTATION_PLAN.md`
10. `docs/adr/0001-hackathon-mvp-architecture.md`

Also read:

- `AGENTS.md` for coding-agent execution rules;
- `CHANGELOG.md` before release-oriented work.

Product/evidence context:

- `docs/product/LEAN_CANVAS.md` when present
- `docs/product/DEVPOST_PITCH.md` when present

If two documents conflict, use this precedence:

```text
Safety / data constraints
        ↓
CLAUDE.md architectural invariants
        ↓
PRD
        ↓
System Design / Agent Architecture
        ↓
UI/UX Spec
        ↓
Tech Stack
        ↓
ROADMAP release-stage constraints
        ↓
Implementation Plan
```

Git/release mechanics are governed by `CONTRIBUTING.md` and the release sections of this file.

Do not resolve material conflicts silently. Document them and propose an ADR where appropriate.

---

## 2. Product Definition

Ngabo is an **open-source, event-driven AMR surveillance and incident-response system**.

Do not make “prototype” part of Ngabo's permanent product identity. Communicate maturity separately through the current release stage.

For example:

> **Product:** Ngabo — AMR Surveillance & Incident Response  
> **Current status:** `v0.1.0` hackathon MVP in development.

The v0.1 proof is:

```text
synthetic WHONET-style input
        ↓
deterministic validation + normalization
        ↓
deterministic surveillance signal
        ↓
Pub/Sub event
        ↓
ADK agent investigation
        ↓
evidence + clarification when needed
        ↓
structured incident package
        ↓
human approval
        ↓
notification / acknowledgement
        ↓
audit trail
```

Ngabo is **not a chatbot product**.

The web application is an incident-response console that makes this workflow visible.

See `ROADMAP.md` for the intended evolution from hackathon MVP through technical/research prototypes, shadow-mode pilot, validation, production candidate, and `1.0.0`.

---

## 3. Non-Negotiable Architectural Invariants

### A. Scientific calculations are deterministic

The LLM must not own:

- CSV parsing;
- schema validation;
- organism/antibiotic normalization;
- date-window calculations;
- resistance-profile similarity calculations;
- baseline calculations;
- signal scoring;
- state-transition validation;
- idempotency decisions.

If a calculation can be reproduced in ordinary code, implement it in ordinary code.

### B. The agent receives a signal; it does not invent one

Do not implement:

```text
CSV -> LLM -> “this is an outbreak”
```

Correct boundary:

```text
CSV -> deterministic detector -> investigation candidate -> agent
```

### C. Source facts are immutable

The agent may never rewrite canonical isolate/laboratory facts.

Human clarification is persisted separately with provenance.

### D. Firestore is operational source of truth

Do not depend on model conversation memory as the canonical workflow state.

Persist incident state, tool execution references, clarification, package versions, review decisions, notification state, and audit events.

### E. All side effects are idempotent

Pub/Sub is at-least-once delivery.

No duplicate:

- incidents;
- package transitions;
- notifications;
- acknowledgements.

Every side effect needs an idempotency strategy.

### F. Human review is a real workflow gate

The agent must not send clinically consequential escalation before review approval.

The UI must provide:

- Approve;
- Reject;
- Request more information.

Do not rename approval to “Confirm outbreak.”

### G. Evidence is traceable

External guidance claims must use source IDs/URLs returned by approved evidence tools.

Never fabricate citations.

### H. No autonomous clinical prescribing

Never implement autonomous treatment/antibiotic recommendations.

### I. Synthetic data only for public v0.1

Do not add real patient records to fixtures, screenshots, logs, or repository history.

Future stages may introduce governed real-world data only as described in `ROADMAP.md` and under appropriate authorization/security.

### J. No hidden chain-of-thought UI

The UI may show tool actions, workflow status, source-backed findings, and concise rationale. It must not expose private model reasoning tokens.

---

## 4. Required Agent Tool Boundary

The v0.1 agent should operate through narrowly scoped typed tools such as:

- `get_incident_context()`
- `compare_resistance_profiles()`
- `get_baseline_summary()`
- `get_missing_fields()`
- `search_approved_guidance()`
- `request_clarification()`
- `prepare_incident_package()`

Do not create a generic unrestricted database tool or shell tool for the runtime agent.

The coding agent may use the terminal while developing; the **Ngabo runtime agent** should not receive arbitrary code execution merely for convenience.

---

## 5. Runtime Agent Truth Hierarchy

Generated outputs must respect:

1. canonical source data;
2. deterministic tool output;
3. retrieved approved guidance;
4. explicitly labelled hypothesis;
5. unknown / insufficient evidence.

Never invent missing facts.

---

## 6. Incident Package Contract

Final package must be schema validated and maintain separate fields for:

```json
{
  "title": "...",
  "priority": "HIGH",
  "observed_evidence": [],
  "derived_findings": [],
  "hypotheses": [],
  "uncertainties": [],
  "missing_information": [],
  "guidance": [],
  "investigation_checklist": [],
  "draft_escalation": "...",
  "limitations": []
}
```

Do not collapse all categories into one prose blob.

---

## 7. UI Contract

Read `docs/UI_UX_SPEC.md` before frontend work.

Core principle:

> **Incident-response console, not ChatGPT for AMR.**

Required operational UI:

```text
Dashboard
  ↓
Import / validation
  ↓
Surveillance signal
  ↓
Incident detail
  ├── Why it was flagged
  ├── Resistance profile comparison
  ├── Agent/tool timeline
  ├── Clarification
  ├── Evidence-backed package
  ├── Human review
  └── Response tracking
```

The only chat-like interaction should be targeted clarification.

---

## 8. Tech Stack — Do Not Substitute Without ADR

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- pnpm

### Backend

- Python 3.11+
- FastAPI
- Pydantic v2
- uv

### AI

- Google ADK (Python)
- Gemini API
- stable model: `gemini-3.6-flash`

### Data / infrastructure

- Firestore
- Cloud Storage
- Pub/Sub
- Cloud Run
- Secret Manager / Cloud Run secrets
- Cloud Logging

### Testing

- pytest
- ADK evaluation tooling
- Playwright

Do not introduce alternate core frameworks because they are familiar.

Specifically do not add without a documented requirement:

- LangGraph;
- Kubernetes/GKE;
- Redis;
- Kafka;
- Cloud SQL;
- BigQuery;
- vector database;
- second LLM provider;
- genomics toolchain.

---

## 9. Google ADK / Agents CLI Guidance

If available in the development environment, official Google ADK/Agents CLI tooling may be used to assist scaffolding, evaluation, deployment, and observability.

Important:

- do not let a scaffold overwrite Ngabo's established monorepo/product architecture;
- use generated templates as implementation aids, not product requirements;
- preserve the architectural invariants in this file.

---

## 10. Repository Target Structure

```text
ngabo/
├── apps/
│   └── web/
├── services/
│   └── core/
│       ├── ngabo/
│       │   ├── api/
│       │   ├── application/
│       │   ├── domain/
│       │   ├── infrastructure/
│       │   ├── agents/
│       │   ├── surveillance/
│       │   ├── evidence/
│       │   └── notifications/
│       └── tests/
├── data/
│   ├── synthetic/
│   ├── schemas/
│   └── guidance/
├── docs/
│   ├── adr/
│   └── product/
├── infra/
├── .github/
├── CLAUDE.md
├── AGENTS.md
├── ROADMAP.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── README.md
├── LICENSE
└── SECURITY.md
```

Do not reorganize top-level structure casually once implementation begins.

---

## 11. Git & Release Governance — Non-Negotiable

Read `CONTRIBUTING.md` before creating branches, commits, pull requests, tags, or releases.

Ngabo uses:

- **Semantic Versioning 2.0.0**;
- **Conventional Commits 1.0.0**;
- **Gitflow-style branching** adapted to `main` + `develop`;
- `CHANGELOG.md`;
- release tags `vX.Y.Z`.

### Branches

Long-lived:

```text
main
 develop
```

Supporting:

```text
feature/<short-name>
release/vX.Y.Z
hotfix/vX.Y.Z
```

Once Gitflow initialization is complete:

- feature work branches from `develop`;
- features merge into `develop` through PRs;
- release branches originate from `develop`;
- releases merge to `main`, are tagged, then reconcile back to `develop`;
- hotfixes originate from `main` and merge to both `main` and `develop`.

Do not commit feature work directly to `main`.

### Conventional Commits

Every commit must use:

```text
<type>[optional scope]: <description>
```

Preferred types:

```text
feat fix docs test refactor perf build ci chore revert
```

Preferred scopes:

```text
web core surveillance agent evidence events data eval infra docs release
```

Examples:

```text
feat(surveillance): add phenotype similarity detector
fix(events): prevent duplicate incident creation
test(eval): add prompt injection scenario
docs(roadmap): define validation stage
```

Breaking change example:

```text
feat(events)!: revise surveillance signal schema
```

Do not create vague commit messages such as `update`, `fix stuff`, `wip`, or `changes` for repository history intended to be merged.

### Semantic Versioning During 0.x

Ngabo remains in SemVer initial development until the explicit `1.0.0` production-readiness decision.

Project policy:

- fix → normally PATCH;
- feature/release milestone → normally MINOR;
- breaking change → mark explicitly and normally increment MINOR during `0.x`;
- do **not** automatically promote to `1.0.0` because a breaking commit exists.

`1.0.0` is governed by the exit criteria in `ROADMAP.md`.

### Changelog

Update `CHANGELOG.md` for meaningful user/operator-visible behavior.

Use `Unreleased` during development and move entries under the released version during release preparation.

---

## 12. Implementation Order

Follow `docs/IMPLEMENTATION_PLAN.md`.

High-level milestones:

1. repository/workspace scaffold;
2. domain entities + state machine;
3. synthetic dataset + canonical schema;
4. deterministic parser/normalizer;
5. deterministic surveillance engine;
6. Firestore/Pub/Sub persistence/event contracts;
7. ADK tools;
8. Ngabo investigation workflow;
9. clarification/resume;
10. incident package validation;
11. human review;
12. notification/acknowledgement;
13. Next.js incident console;
14. Cloud Run deployment;
15. evaluation and demo hardening.

Do not start genomics before the core v0.1 flow is green.

---

## 13. Definition of Done Per Milestone

Before marking a milestone complete:

- tests for changed deterministic behavior pass;
- schemas are explicit;
- errors are not silently swallowed;
- no architectural invariant was violated;
- docs are updated if contracts changed;
- relevant lint/type checks pass;
- branch follows Gitflow purpose/naming;
- commits follow Conventional Commits;
- changelog/release impact is considered;
- code is committed in a coherent state.

Do not declare success merely because the happy-path UI renders.

---

## 14. Test Requirements

At minimum cover:

### Deterministic

- parser;
- normalizer;
- AST mappings;
- similarity calculation;
- temporal windows;
- baseline logic;
- signal scoring;
- state transitions;
- idempotency.

### Agent safety

- missing field -> clarification;
- no evidence -> no fabricated source;
- prompt injection in CSV -> treated as data;
- hallucinated isolate ID -> rejected;
- autonomous prescribing language -> rejected;
- autonomous outbreak confirmation -> rejected;
- tool failure -> visible bounded failure.

### End-to-end

```text
upload
 -> detect
 -> investigate
 -> clarify
 -> package
 -> review
 -> notify
 -> acknowledge
```

---

## 15. Failure Handling

A failed step must leave a persisted, inspectable state.

Never catch an exception and proceed as if successful.

Examples:

- malformed import -> validation failure;
- Gemini timeout -> retryable investigation failure;
- malformed package -> schema rejection;
- notification failure -> retryable notification state;
- duplicate event -> no duplicate side effect.

---

## 16. Scope Control

When tempted to add a feature, ask:

> “Does this strengthen the current release's stated objective in `ROADMAP.md`?”

For `v0.1.0`, ask specifically:

> “Does this strengthen: suspicious AMR signal -> evidence-backed, human-reviewable incident package -> coordinated action?”

If no, defer it.

Explicitly deferred until core completion:

- AMRFinderPlus;
- pathogen genomics;
- real hospital/LIMS integration;
- nationwide analytics;
- facility tenancy/RBAC platform;
- vector RAG;
- mobile app;
- hardware.

---

## 17. Architecture Changes

If implementation reveals that a frozen decision is wrong:

1. do not silently substitute technology;
2. create a new file under `docs/adr/`;
3. state context, decision, alternatives, consequences;
4. update relevant source-of-truth docs;
5. only then implement the change.

Small refactors that preserve public contracts do not require an ADR.

---

## 18. Hackathon Constraints

Keep the public v0.1 project consistent with current official hackathon requirements and the fact-checked project documentation.

Do not implement shortcuts that make the demo fake or non-reproducible.

The hackathon is the first release cycle, not the final product boundary.

---

## 19. Working Style for Claude Code

- inspect before editing;
- make focused changes;
- do not rewrite unrelated files;
- preserve user-authored documentation unless a contract change requires an update;
- prefer typed interfaces over loose dictionaries at boundaries;
- prefer boring, testable code over clever abstractions;
- avoid premature microservices;
- avoid premature generic frameworks;
- report discovered contradictions rather than guessing;
- obey Gitflow, SemVer, Conventional Commits, and changelog rules;
- do not silently version-bump or create release tags.

When asked to implement a milestone, stay inside that milestone unless a prerequisite must be fixed.

---

## 20. Release Actions Require Deliberate Intent

Coding agents may prepare release metadata when asked, but must not independently decide that Ngabo has earned a new maturity stage.

In particular, do not autonomously declare:

- research validation complete;
- pilot readiness;
- production readiness;
- `1.0.0` readiness.

Those milestones require evidence and explicit project-owner/stakeholder decisions under `ROADMAP.md`.

---

## 21. Final Product Standard

For v0.1, a judge should be able to see:

> **new AMR data arrived -> Ngabo detected a signal -> the agent investigated autonomously -> asked for one necessary clarification -> assembled evidence -> a professional approved the package -> Ngabo routed the action -> the audit trail recorded everything.**

Longer-term releases must progressively earn the stronger technical, scientific, security, governance, and deployment claims documented in `ROADMAP.md`.

If the code cannot demonstrate a claim truthfully, do not make the claim.
