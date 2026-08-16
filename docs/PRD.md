# Ngabo — Product Requirements Document (PRD)

**Version:** 0.2  
**Date:** 2026-08-16  
**Status:** Hackathon MVP baseline  
**Primary track:** All Things Agentic Hackathon — The Taskmaster

## 1. Product Summary

Ngabo is an open-source, agentic antimicrobial-resistance (AMR) surveillance and incident-response system.

It ingests representative WHONET-style microbiology and antimicrobial-susceptibility data, validates and normalizes it deterministically, detects suspicious resistance patterns using transparent statistical/rule-based logic, and launches an autonomous investigation workflow.

The agent gathers context and approved evidence, identifies missing information, asks a targeted clarification question when necessary, resumes the same incident, prepares an evidence-backed incident-response package, routes it through a human safety gate, executes an authorized external action, and tracks acknowledgement/follow-up.

> **v0.1 promise:** turn a suspicious AMR surveillance signal into an evidence-backed, human-reviewable incident package and coordinated action through a safe, event-driven, resumable workflow.

## 2. Primary User

**Hero user:** hospital microbiologist / AMR surveillance officer.

Job to be done:

> “When unusual resistance patterns appear in our laboratory data, help me determine what deserves investigation, assemble the evidence, identify what is missing, and prepare a structured incident package for the team.”

Secondary users:

- Infection Prevention & Control (IPC)
- antimicrobial-stewardship leads
- hospital epidemiologists
- AMR focal persons

## 3. Goals

1. **Event-driven autonomy:** new lab data triggers the workflow without manually prompting a chatbot through each step.
2. **Deterministic scientific logic:** parsing, validation, AST normalization, time windows, similarity calculations, and trigger logic remain reproducible code.
3. **Agentic investigation:** once a signal exists, Ngabo decides which bounded tools/evidence it needs and synthesizes an investigation.
4. **Resumable/recoverable execution:** interruptions, retries, and clarification pauses do not destroy the canonical incident workflow or duplicate consequential actions.
5. **Bounded autonomy:** qualified humans approve clinically consequential actions.
6. **Proof of action:** the hosted/demo path performs at least one real authorized outbound action after approval and records the result.
7. **Observable autonomy:** tool execution, state changes, retries/resumes, evidence, and action are inspectable without exposing hidden chain-of-thought.
8. **Evaluated behavior:** deterministic, ADK-agent, safety, resumability, and end-to-end scenarios are measured and documented.
9. **Reproducibility:** GitHub, architecture diagrams, tests/evals, and setup instructions make the project inspectable and runnable.

## 4. Non-Goals for Core v0.1

Ngabo will not:

- diagnose patients;
- prescribe antibiotics;
- autonomously confirm an outbreak;
- replace WHONET or NIAMR;
- use real identifiable patient data in the public demo;
- claim clinical validation or regulatory approval;
- require genomics, a vector DB, BigQuery, Kubernetes, or a microservice fleet;
- depend on MedGemma or multimodal AST extraction for the core demo.

EmbeddingGemma semantic evidence retrieval is a planned post-core v0.1 enhancement. MedGemma and multimodal ingestion are gated stretch features.

## 5. Primary Workflow

```text
Upload / receive WHONET-style CSV
        ↓
Deterministic validation + normalization
        ↓
Statistical surveillance detector
        ↓
Suspicious signal?
   no ↙        ↘ yes
summary      incident
                ↓
         Pub/Sub event
                ↓
       autonomous ADK investigation
                ↓
       missing context?
         yes ↙   ↘ no
   targeted clarification
         ↓
     resume same incident
                ↓
     validated incident package
                ↓
      human safety gate
        reject / approve
                ↓
   real authorized notification/action
                ↓
        acknowledgement
                ↓
             closed
```

## 6. Functional Requirements

### FR-001 — Import data

User can upload a CSV representing WHONET-style isolate/AST data.

Acceptance:

- unique import ID;
- immutable raw file stored;
- SHA-256 recorded;
- malformed input fails visibly;
- LLM never silently guesses malformed schema.

### FR-002 — Normalize records

Canonical fields include:

- isolate ID;
- collection date;
- organism;
- ward/location;
- specimen type where present;
- antibiotic result fields;
- normalized S/I/R interpretation.

Acceptance:

- deterministic mappings;
- unknown values flagged, never invented.

### FR-003 — Detect suspicious AMR patterns

MVP dimensions:

- organism;
- ward;
- time window;
- resistance-profile similarity;
- representative baseline frequency.

Acceptance:

- seeded demo signal is reproducible;
- trigger explanation persisted;
- output is an **investigation candidate**, not a confirmed outbreak.

### FR-004 — Create incident

Incident stores/references:

- signal;
- related isolates;
- priority;
- trigger explanation;
- state;
- evidence;
- timestamps;
- agent execution references;
- package versions;
- audit timeline.

### FR-005 — Autonomous ADK investigation

Approved tools:

- `get_incident_context`
- `compare_resistance_profiles`
- `get_baseline_summary`
- `get_missing_fields`
- `search_approved_guidance`
- `request_clarification`
- `prepare_incident_package`

Acceptance:

- Pub/Sub signal launches investigation automatically;
- every tool call is observable/auditable;
- deterministic calculations come from deterministic tools/services;
- agent cannot rewrite source facts;
- agent has configured step/tool/time/retry bounds;
- session/invocation/run references are persisted where available.

### FR-006 — Clarification + resume

Agent can pause at `WAITING_FOR_CLARIFICATION`, ask one targeted materially relevant question, persist the answer, then resume the same incident.

Acceptance:

- question is constrained where possible;
- missing values are never guessed;
- answer provenance is retained;
- resume/retry does not duplicate consequential side effects;
- interruption/recovery is visible in audit/telemetry.

### FR-007 — Incident package

Package includes:

- observed evidence;
- derived findings;
- hypotheses;
- uncertainty;
- missing information;
- source-linked guidance;
- investigation checklist;
- draft escalation message;
- limitations.

Acceptance:

- schema validation passes;
- isolate IDs exist;
- cited source IDs were actually retrieved;
- prohibited clinical overclaims are rejected;
- package cannot enter review after critical agent/tool failure.

### FR-008 — Human safety gate

Reviewer options:

- approve;
- reject;
- request more information.

Acceptance:

- consequential external action cannot bypass this state transition;
- final approval authority remains in application/domain workflow.

### FR-009 — Real action + demo action

Ngabo has a `NotificationPort` with:

1. deterministic demo adapter for tests/local reproducibility;
2. at least one real authorized external adapter for the hosted/filmed v0.1 path.

Acceptance:

- real action occurs only after approval;
- delivery attempt/result is persisted;
- retries are idempotent;
- UI identifies real vs demo channel truthfully;
- acknowledgement/equivalent completion is persisted;
- no real hospital/person is contacted without explicit authorization.

### FR-010 — Audit trail

Append-only timeline records every major:

- import;
- signal;
- agent start;
- tool action;
- retry/resume;
- clarification;
- package validation;
- review;
- notification;
- acknowledgement;
- error.

Do not store private chain-of-thought as an audit artifact.

### FR-011 — Observability

System emits structured safe metadata including where relevant:

- correlation ID;
- incident ID;
- event ID;
- agent session/invocation/run ID;
- tool name/status;
- model name;
- package version;
- latency/retry information.

Use Cloud Logging plus supported ADK/Cloud Trace/OpenTelemetry integration where stable.

### FR-012 — Evaluation artifact

Before submission, publish `EVALUATION.md` covering:

- detector benchmark;
- ADK agent eval cases;
- safety/adversarial tests;
- resumability/idempotency tests;
- end-to-end deployed tests;
- EmbeddingGemma retrieval evaluation if integrated;
- model/framework versions;
- limitations.

### FR-013 — EmbeddingGemma evidence retrieval enhancement

After the deployed core path is green, Ngabo should support semantic retrieval over the curated approved evidence corpus through an `EmbeddingGemmaEvidenceAdapter` behind `EvidenceSearchPort`.

Acceptance:

- approved corpus only;
- source IDs/provenance retained;
- lightweight similarity index is sufficient for hackathon scale;
- no vector database required solely for bonus points;
- retrieval is evaluated;
- bonus/model claim made only if successfully integrated.

## 7. Gated Stretch Requirements

### MedGemma

May be added only if core + deployment + evaluation + EmbeddingGemma are stable and comparison shows meaningful benefit.

Potential role: bounded interpretation of already retrieved approved medical/AMR evidence.

Must not diagnose, prescribe, confirm outbreaks, replace deterministic surveillance, or create uncited authority.

### Multimodal AST/PDF draft extraction

May be added only after core freeze.

```text
image/PDF -> Gemini extraction -> UNVERIFIED DRAFT -> human verification -> canonical ingestion
```

Detector cannot consume unverified extraction.

## 8. Non-Functional Requirements

- **Reproducibility:** same data + detector config → same surveillance result.
- **Traceability:** guidance claims link to known retrieved sources.
- **Failure visibility:** failed tool/agent steps never masquerade as success.
- **Idempotency:** Pub/Sub/resume/retries cannot create duplicate consequential actions.
- **Recoverability:** incident business state survives process restart; ADK execution is resumable where supported/stable or safely restartable from persisted state.
- **Privacy:** synthetic demo data only; metadata-first telemetry.
- **Performance:** 250–1,000 isolate rows process comfortably within demo time.
- **Cost:** serverless components scale to zero where possible; agent loops bounded.
- **Security:** secrets injected, internal endpoints protected, expensive public endpoints bounded/protected where practical.
- **Availability for judging:** hosted project remains accessible through the required judging period.

## 9. UX Requirements

The MVP should feel like an **incident-response console**, not a chatbot.

Core screens/states:

1. Import
2. Surveillance overview
3. Incident timeline
4. Agent tool/evidence progression
5. Pause/resume/retry visibility
6. Clarification request
7. Evidence-backed incident package
8. Human review
9. Real/demo notification status
10. Acknowledgement

See:

- `docs/UI_UX_SPEC.md`
- `docs/UI_UX_HACKATHON_ADDENDUM.md`

## 10. Demo Scenario

Representative neonatal-unit data contains several *Klebsiella pneumoniae* isolates with unusually similar resistance phenotypes over a short period. One isolate intentionally lacks a relevant metadata field.

Ngabo should:

1. ingest;
2. normalize;
3. detect;
4. explain signal;
5. publish/consume the event;
6. launch ADK investigation automatically;
7. execute bounded tools;
8. retrieve context/evidence;
9. notice missing field;
10. ask one clarification;
11. resume the same incident;
12. create and validate incident package;
13. wait for approval;
14. execute one real authorized action;
15. persist delivery/acknowledgement;
16. expose audit/log/trace evidence.

## 11. Definition of Done

Ngabo v0.1 is done when a reviewer can watch a single unedited hosted workflow:

> **synthetic WHONET-style input → deterministic detected signal → Pub/Sub-triggered ADK investigation → targeted clarification → safe resume → evidence-backed validated package → human approval → real authorized routed action → acknowledgement → persisted audit/observability trail**

and:

- every scientific calculation is deterministic/testable;
- every major stage is visible in UI/logs/state;
- retries/redelivery do not duplicate consequential effects;
- ADK eval/safety results are documented;
- Google Cloud deployment is visibly proven;
- README has reproducible spin-up/deploy instructions;
- no unimplemented bonus model/feature is claimed.
