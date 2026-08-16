# Ngabo — All Things Agentic Hackathon Alignment

**Status:** Required v0.1 implementation and submission contract  
**Hackathon:** All Things Agentic Hackathon 2026  
**Primary category:** The Taskmaster  
**Submission deadline:** 2026-08-31 17:00 PT

---

## 1. Purpose

This document converts the hackathon rules, resources, judging criteria, and organizer guidance into explicit Ngabo implementation requirements.

Ngabo should not merely satisfy the minimum technology checklist. The v0.1 build should visibly exploit the hackathon's strongest signals:

- asynchronous background execution;
- event-driven autonomous routing;
- multi-step tool use;
- persistent/resumable workflows;
- human approval at meaningful boundaries;
- failure tolerance and idempotency;
- strong observability and evaluation;
- undeniable proof of action;
- Google Cloud deployment;
- meaningful use of additional Google AI models where they improve the product;
- public build content and social distribution.

This document extends the PRD, Tech Stack, System Design, Agent Architecture, Data/Safety/Evaluation, UI/UX Spec, and Implementation Plan. If implementation choices conflict, preserve the safety and Clean Architecture rules first.

---

## 2. Official Mandatory Technology Requirements

All categories require:

1. **Gemini 3.5 or newer**, accessed through Gemini API or Vertex AI;
2. at least one supported Google Agent Framework:
   - Google ADK;
   - GenAI SDK;
   - Antigravity SDK;
   - Genkit;
3. at least one Google Cloud infrastructure service such as:
   - Cloud Run;
   - Cloud SQL;
   - Firestore;
   - GKE;
   - Pub/Sub.

### Ngabo compliance

| Requirement | Ngabo decision | Status |
|---|---|---|
| Gemini 3.5+ | `gemini-3.6-flash` | Required |
| Model transport | Gemini API | Required |
| Agent framework | Google ADK Python | Required |
| Agent deployment | `ngabo-core` on Cloud Run | Required |
| Web deployment | `ngabo-web` on Cloud Run | Required |
| Persistent workflow state | Firestore | Required |
| Event-driven triggers | Pub/Sub | Required |
| Object storage | Cloud Storage | Required |
| Structured logging | Cloud Logging | Required |

The application must make this technology use obvious in code, architecture diagrams, documentation, and the demo. Do not technically include Google Cloud while hiding it behind a local-only demo.

---

## 3. Category Decision — The Taskmaster

The Taskmaster focuses on an event-driven workflow with autonomous routing: the system watches for a change, decides what must happen, interacts with tools, and completes a multi-step workflow without the user guiding each step.

Ngabo's canonical flow is therefore:

```text
new AMR data arrives
        ↓
deterministic ingestion + validation
        ↓
deterministic surveillance detector
        ↓
suspicious AMR signal
        ↓
Pub/Sub event
        ↓
Ngabo starts investigation automatically
        ↓
agent chooses bounded tools
        ↓
evidence/context gathered
        ↓
clarification only if materially necessary
        ↓
structured incident package
        ↓
human safety gate
        ↓
real outbound action
        ↓
acknowledgement + audit trail
```

### Demo rule

The demo must never depend on a user typing:

> “Please investigate these isolates.”

The event should wake the workflow automatically.

---

## 4. Judging Strategy

Official Stage Two weighting:

- **Innovation & Operational Utility — 40%**
- **Architectural Discipline & Tech Stack — 30%**
- **Demo & Production Readiness — 30%**

Ngabo optimizes explicitly for all three.

### 4.1 Innovation & Operational Utility

Prove that Ngabo reduces the friction between surveillance and response.

The system should visibly:

- ingest messy laboratory surveillance data;
- detect an investigation candidate deterministically;
- launch an investigation without prompting;
- gather evidence/context autonomously;
- pause only when information truly requires a human;
- resume automatically;
- produce a structured incident package;
- route approved action;
- track acknowledgement.

Do not present Ngabo as “an LLM that summarizes AMR data.”

### 4.2 Architectural Discipline & Tech Stack

Prove:

- Clean Architecture dependency boundaries;
- scoped tools;
- persistent workflow state;
- resumability;
- idempotent side effects;
- explicit state machine;
- deterministic scientific calculations;
- failure-visible behavior;
- credential isolation;
- structured logging/tracing;
- agent evaluation;
- human review boundaries.

### 4.3 Demo & Production Readiness

The 4-minute video should provide undeniable proof of action through UI state, logs, database/state transitions, and an external action.

Required visible proof:

- application running from a hosted URL;
- Google Cloud deployment proof (`.run.app`, Cloud Run dashboard/logs, or equivalent);
- autonomous signal-triggered investigation;
- actual tool execution;
- state persistence;
- clarification pause/resume;
- human review;
- real notification/action;
- acknowledgement/state update;
- concise architecture diagram.

---

## 5. ADK Must Be Used as a Runtime Capability, Not a Badge

Google's hackathon resources emphasize long-running agents, crash recovery, human approval, and idempotency. Ngabo should therefore exploit ADK-specific runtime capabilities deliberately.

Required ADK usage for v0.1:

1. bounded tool calling;
2. persistent session/run identifiers;
3. resumable investigation execution where supported and stable;
4. targeted human input for clarification;
5. ADK evaluations;
6. trace/observability integration;
7. structured model outputs validated by Pydantic.

See `docs/ADK_RUNTIME.md` for the detailed contract.

---

## 6. Resumability Model

Ngabo uses two complementary forms of persistence.

### Firestore — application/workflow truth

Firestore owns durable Ngabo state:

- incident state;
- package versions;
- clarification requests/answers;
- review decisions;
- notification state;
- event audit history;
- agent execution references.

### ADK resumability — agent execution continuity

Where supported by the chosen ADK release, persist agent execution identifiers/checkpoint metadata so interrupted investigations can continue rather than restart from zero.

Suggested incident execution fields:

```text
agent_session_id
agent_invocation_id
agent_run_status
agent_started_at
agent_updated_at
last_agent_checkpoint
agent_attempt
```

### Pub/Sub — asynchronous trigger and redelivery

Pub/Sub is the event transport, not the workflow database.

Because delivery is at least once, every state-changing consumer must remain idempotent.

---

## 7. Human Input and Approval

Ngabo has two different human interaction boundaries.

### 7.1 Investigation clarification — ADK workflow input

Use structured human input for missing information that blocks a valid assessment.

Example:

```text
WAITING_FOR_CLARIFICATION
  question: specimen type for isolate UGA-039
        ↓
human answers: blood
        ↓
INVESTIGATING
        ↓
agent resumes existing incident
```

The question must be targeted. Do not turn clarification into open-ended chat.

### 7.2 Consequential response approval — application/domain gate

Final approval remains owned by the Ngabo application state machine, not delegated solely to an experimental model/tool confirmation primitive.

The reviewer can:

- approve the incident package/escalation;
- reject;
- request more information.

The agent may prepare an action, but it cannot bypass this gate.

---

## 8. ADK Evaluation Is a Deliverable

Evaluation is not just internal testing. It is part of Ngabo's technical story.

Required v0.1 evaluation cases include:

| Scenario | Expected behavior |
|---|---|
| clear seeded cluster | investigate and prepare valid package |
| missing specimen/source metadata | ask one targeted clarification |
| weak/noisy signal | preserve uncertainty; avoid overclaiming |
| no matching approved evidence | explicitly state evidence unavailable |
| tool failure | bounded visible failure / retry behavior |
| prompt injection text inside CSV | treat as untrusted data, not instruction |
| fabricated source attempt | reject output |
| hallucinated isolate ID | reject output |
| prescribing request | preserve clinical boundary |
| outbreak-confirmation language | do not claim confirmation |
| duplicate event | no duplicate incident/action |
| notification retry | no duplicate delivery ambiguity |

Evaluation should cover both:

- final structured outcome;
- tool/trajectory behavior where ADK evaluation supports it.

Produce a public `EVALUATION.md` before submission containing methodology, scenarios, pass/fail results, known limitations, and model/version details.

---

## 9. Observability Is a Product Feature

Ngabo's autonomous behavior must be inspectable.

Required telemetry dimensions:

```text
correlation_id
incident_id
event_id
agent_session_id
agent_invocation_id
agent_run_id
tool_name
tool_status
model_name
package_version
```

Required signals:

- import processing duration;
- detector duration;
- agent invocation duration;
- tool latency/error;
- clarification count;
- package-generation time;
- notification latency;
- retries/resumes;
- token/model usage when available.

Use:

- Cloud Logging for structured application logs;
- ADK/Google tracing capability where practical;
- Cloud Trace/OpenTelemetry if the selected ADK/Agents CLI path supports it cleanly.

### Sensitive-content rule

Do not enable prompt/response content capture blindly. The public v0.1 dataset is synthetic, but the architecture must still assume future health data is sensitive. Default to metadata/no-content traces unless explicit synthetic-demo observability requires more.

Do not add BigQuery merely for observability unless the implementation demonstrably needs it; Cloud Trace/Logging are sufficient for v0.1 unless evaluation proves otherwise.

---

## 10. Proof of Action — Real Outbound Action Required

A deterministic demo adapter remains required for tests, but the filmed/hosted v0.1 should execute at least one real, authorized external action after human approval.

The architecture remains:

```text
application use case
      ↓
NotificationPort
      ↓
real authorized adapter
```

Acceptable examples include an authorized email or webhook integration.

### Acceptance criteria

- action is triggered only after approval;
- action occurs outside the Ngabo UI;
- delivery attempt/result is persisted;
- retries are idempotent;
- the demo shows the external result;
- acknowledgement or equivalent completion signal updates Ngabo state;
- no real hospital/person is contacted without explicit authorization.

The demo adapter must remain available for automated tests and local reproducibility.

---

## 11. Additional Google AI Model Strategy

The official rules award **0.2 bonus points per successfully integrated additional Google AI model**, up to **0.6**.

Ngabo should pursue bonus models only when they improve the architecture.

### 11.1 EmbeddingGemma — planned v0.1 integration

**Status:** planned after core surveillance-to-action flow is green.

Use case:

```text
approved guidance corpus
       ↓
EmbeddingGemma document embeddings
       ↓
small local/in-process vector index
       ↓
semantic retrieval
       ↓
source IDs + approved chunks
       ↓
Gemini orchestrator
```

Why it is useful:

- semantic retrieval over a curated corpus;
- lightweight model;
- no always-on vector database required;
- maintains source-traceability;
- provides a meaningful additional Google model integration.

For the hackathon-scale corpus, prefer NumPy cosine similarity or another lightweight deterministic index. Do not introduce a vector database solely for the bonus.

### 11.2 MedGemma — gated stretch integration

**Status:** optional, only after core workflow + EmbeddingGemma + evals are stable.

Potential bounded role:

```text
retrieved approved medical/AMR evidence
       ↓
MedGemma structured interpretation tool
       ↓
Gemini orchestrator synthesis
```

MedGemma must not:

- diagnose;
- prescribe;
- confirm outbreaks;
- replace deterministic AST/surveillance calculations;
- transform uncited knowledge into authoritative guidance.

Claim a bonus only if the integration is real, documented, evaluated, and shown in the project.

### 11.3 Bonus discipline

Do not add a third model by default. A third model is acceptable only if it has a genuine bounded role and does not compromise the core demo or architecture score.

---

## 12. Multimodal Stretch — Best Multimodal UX Opportunity

The rules include a Best Multimodal UX prize. This is a stretch objective, not core v0.1 scope.

Potential feature:

```text
photo / scanned PDF of AST report
       ↓
Gemini multimodal extraction
       ↓
structured DRAFT record
       ↓
human verification
       ↓
canonical deterministic ingestion
```

Safety boundary:

```text
multimodal model output != canonical lab fact
```

The extracted record remains a draft until human verification.

Do not implement this before the CSV-based end-to-end workflow is deployed and stable.

---

## 13. Public Build Content Bonus

The hackathon grants up to:

- **+0.2** for qualifying public build content;
- **+0.2** for a qualifying social post.

### LinkedIn Article

Ngabo will publish the planned LinkedIn Article.

It must include explicit language such as:

> “This article was created for the purposes of entering the All Things Agentic Hackathon 2026.”

The article should cover actual implementation, architecture, evaluation, trade-offs, screenshots, and lessons—not just product marketing.

### Social post

Publish a LinkedIn launch/build post using the exact official hashtag:

`#AllThingsAgenticHackathon`

Do not rely on transcript/OCR variants of the hashtag.

---

## 14. Cloud Cost, Security, and Demo Acceptance Criteria

The Resources page explicitly recommends scale-to-zero, max instance caps, budget alerts, light storage, endpoint protection, and shutting down unused infrastructure after proof is captured.

Required v0.1 deployment configuration:

### Cloud Run

- minimum instances: `0` unless a demonstrated technical reason requires otherwise;
- explicit maximum instance cap;
- right-sized CPU/memory;
- separate `ngabo-web` and `ngabo-core` services;
- avoid accidental public administrative/internal endpoints.

### Budget

- configure a Google Cloud budget;
- configure at least one email threshold alert;
- document expected low-volume demo cost assumptions.

### Security

- secrets injected from Secret Manager/environment, never committed;
- protect internal event endpoints;
- validate Pub/Sub-originated requests where applicable;
- rate-limit or otherwise protect externally exposed expensive endpoints;
- least-privilege service accounts where practical;
- synthetic demo data only.

### Storage

- retain essential demo/audit artifacts only;
- avoid large unnecessary prompt/log payloads;
- document cleanup procedure.

### After demo/judging

Do not delete services required for judge testing before the judging period ends. After the required availability window, disable/delete unused paid resources.

---

## 15. Required Architecture Diagram Content

The submission diagram must visibly show:

```text
Browser
   ↓
Cloud Run: ngabo-web
   ↓
Cloud Run: ngabo-core
   │
   ├── deterministic surveillance core
   ├── Google ADK orchestrator
   ├── Gemini 3.6 Flash
   ├── EmbeddingGemma (if completed)
   ├── MedGemma (only if completed)
   └── notification port
   │
   ├── Firestore
   ├── Pub/Sub
   ├── Cloud Storage
   ├── Cloud Logging / tracing
   └── real authorized action target
```

It should also mark the **human approval boundary** explicitly.

---

## 16. Four-Minute Demo Storyboard Constraint

The product must be designed so the following can be shown clearly in under four minutes:

1. problem/value proposition;
2. upload/arrival of synthetic AMR data;
3. deterministic signal detection;
4. Pub/Sub-triggered investigation without prompt;
5. visible tool/evidence timeline;
6. clarification pause + answer + resume;
7. evidence-backed incident package;
8. human approval;
9. real external action;
10. acknowledgement/state update;
11. quick architecture/GCP proof;
12. evaluation/observability proof.

Do not add features that make this story harder to understand.

---

## 17. Definition of Hackathon-Ready

Ngabo is not submission-ready until all core items below are true:

- [ ] Gemini 3.6 Flash actually runs the agent workflow;
- [ ] Google ADK actually orchestrates tool use;
- [ ] Cloud Run hosts the working services;
- [ ] Firestore persists incident/workflow state;
- [ ] Pub/Sub triggers asynchronous processing;
- [ ] Cloud Storage stores the required files/evidence artifacts;
- [ ] agent investigation is resumable/recoverable to the extent supported by the selected ADK version;
- [ ] clarification pauses and resumes the same incident;
- [ ] all side effects are idempotent;
- [ ] ADK evaluation suite is run and documented;
- [ ] Cloud Logging/tracing provides inspectable proof;
- [ ] one real authorized outbound action works;
- [ ] full seeded E2E scenario succeeds repeatedly on GCP;
- [ ] architecture diagram exists;
- [ ] README contains local/deployment spin-up instructions;
- [ ] hosted project remains available for judging;
- [ ] public demo video is <=4 minutes;
- [ ] LinkedIn Article satisfies hackathon language requirement;
- [ ] social post uses `#AllThingsAgenticHackathon`;
- [ ] EmbeddingGemma bonus is claimed only if successfully integrated;
- [ ] MedGemma bonus is claimed only if successfully integrated and evaluated;
- [ ] no unimplemented capability appears in the Devpost claims or demo.

---

## 18. Official Sources

- Rules: https://allthingsagentichackathon.devpost.com/rules
- Resources: https://allthingsagentichackathon.devpost.com/resources
- Google ADK / Agents tooling: https://google.github.io/adk-docs/ and https://google.github.io/agents-cli/
- Gemini API: https://ai.google.dev/gemini-api/docs
- EmbeddingGemma: https://ai.google.dev/gemma/docs/embeddinggemma
- MedGemma: https://developers.google.com/health-ai-developer-foundations/medgemma

Re-check the official rules before final submission. If this document and the official rules diverge, the official rules win and this document must be updated.
