# CLAUDE.md — Ngabo Implementation Contract

This file is the root implementation contract for Claude Code working on Ngabo.

**Project:** Ngabo — Autonomous AMR Surveillance & Incident Response  
**Competition:** All Things Agentic Hackathon 2026 — Taskmaster  
**Primary stack:** Next.js + TypeScript; Python + FastAPI; Google ADK; Gemini 3.6 Flash; Firestore; Cloud Storage; Pub/Sub; Cloud Run  
**MVP deadline:** 2026-08-31, 5:00 PM Pacific Time

---

## 1. Read Before Editing Code

Before implementing or changing architecture, read these files in order:

1. `docs/PRD.md`
2. `docs/TECH_STACK.md`
3. `docs/SYSTEM_DESIGN.md`
4. `docs/AGENT_ARCHITECTURE.md`
5. `docs/DATA_SAFETY_EVALUATION.md`
6. `docs/UI_UX_SPEC.md`
7. `docs/IMPLEMENTATION_PLAN.md`
8. `docs/adr/0001-hackathon-mvp-architecture.md`

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
Implementation Plan
```

Do not resolve material conflicts silently. Document them and propose an ADR.

---

## 2. Product Definition

Ngabo is an **event-driven AMR surveillance-to-action system**.

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

Google's current Agents CLI can install coding-agent skills for ADK development and explicitly supports Claude Code.

If available in the development environment, initial setup may use:

```bash
uvx google-agents-cli setup
```

Then use the official ADK/Agents CLI workflow skills where they help with scaffolding, evaluation, deployment, and observability.

Important:

- do not let a scaffold overwrite Ngabo's established monorepo/product architecture;
- use generated templates as implementation aids, not as product requirements;
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
├── README.md
├── LICENSE
└── SECURITY.md
```

Do not reorganize top-level structure casually once implementation begins.

---

## 11. Implementation Order

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

Do not start genomics before the core flow is green.

---

## 12. Definition of Done Per Milestone

Before marking a milestone complete:

- tests for changed deterministic behavior pass;
- schemas are explicit;
- errors are not silently swallowed;
- no architectural invariant was violated;
- docs are updated if contracts changed;
- relevant lint/type checks pass;
- code is committed in a coherent state.

Do not declare success merely because the happy-path UI renders.

---

## 13. Test Requirements

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

## 14. Failure Handling

A failed step must leave a persisted, inspectable state.

Never catch an exception and proceed as if successful.

Examples:

- malformed import -> validation failure;
- Gemini timeout -> retryable investigation failure;
- malformed package -> schema rejection;
- notification failure -> retryable notification state;
- duplicate event -> no duplicate side effect.

---

## 15. Scope Control

When tempted to add a feature, ask:

> “Does this strengthen the v0.1 promise: suspicious AMR signal -> evidence-backed, human-reviewable incident package -> coordinated action?”

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

## 16. Architecture Changes

If implementation reveals that a frozen decision is wrong:

1. do not silently substitute technology;
2. create a new file under `docs/adr/`;
3. state context, decision, alternatives, consequences;
4. update relevant source-of-truth docs;
5. only then implement the change.

Small refactors that preserve public contracts do not require an ADR.

---

## 17. Hackathon Constraints

Keep the public project consistent with the current official requirements:

- Gemini 3.5 or newer;
- qualifying Google Agent Framework;
- at least one Google Cloud infrastructure service;
- repository + spin-up instructions;
- architecture diagram;
- <=4-minute public demo;
- demo visibly proves Google Cloud backend execution;
- project behaves as shown in the demo.

Do not implement shortcuts that make the demo fake or non-reproducible.

---

## 18. Working Style for Claude Code

- inspect before editing;
- make focused changes;
- do not rewrite unrelated files;
- preserve user-authored documentation unless a contract change requires an update;
- prefer typed interfaces over loose dictionaries at boundaries;
- prefer boring, testable code over clever abstractions;
- avoid premature microservices;
- avoid premature generic frameworks;
- report discovered contradictions rather than guessing.

When asked to implement a milestone, stay inside that milestone unless a prerequisite must be fixed.

---

## 19. Final Product Standard

A judge should be able to see:

> **new AMR data arrived -> Ngabo detected a signal -> the agent investigated autonomously -> asked for one necessary clarification -> assembled evidence -> a professional approved the package -> Ngabo routed the action -> the audit trail recorded everything.**

If the code cannot demonstrate that truthfully, the MVP is not complete.
