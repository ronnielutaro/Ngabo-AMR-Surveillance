# Ngabo — All Things Agentic Hackathon Alignment

**Status:** Required v0.1 implementation and submission contract  
**Version:** 0.2  
**Hackathon:** All Things Agentic Hackathon 2026  
**Primary category:** The Taskmaster  
**Submission deadline:** 2026-08-31 17:00 PT

---

## 1. Purpose

This document converts the current official hackathon rules, judging criteria, prize structure, resources, and Ngabo architecture decisions into one implementation/submission contract.

Ngabo must not merely satisfy a technology checklist. The submitted system should visibly demonstrate:

- event-driven asynchronous autonomy;
- a complete background workflow rather than a chat loop;
- deterministic scientific work where ordinary code is more reliable;
- bounded Gemini reasoning where ambiguity exists;
- graph-first Google ADK orchestration;
- durable state, resumability, idempotency, and failure visibility;
- explicit context/memory/freshness boundaries for long-running work;
- human authority only at meaningful high-stakes boundaries;
- real authorized external action and acknowledgement;
- strong evaluation and operational-utility evidence;
- inspectable Google Cloud execution;
- reproducible documentation;
- truthful third-party/data/pre-existing-work disclosure;
- selective bonus-model/content work only after the core is stable.

This document extends the PRD, Clean Architecture, ADK runtime, orchestration, long-running-agent, system, agent, data/safety/evaluation, UI/UX, implementation, provenance, operational-utility, and submission-evidence contracts.

If official rules change, the official rules win and this file must be updated before implementation/submission proceeds.

---

## 2. Official Mandatory Technology Requirements

All categories require:

1. **Gemini 3.5 or newer** via Gemini API or Vertex AI;
2. at least one supported Google Agent Framework, including Google ADK;
3. at least one Google Cloud infrastructure service such as Cloud Run, Firestore or Pub/Sub.

### Ngabo technology contract

| Requirement | Ngabo decision | v0.1 status |
|---|---|---|
| Gemini 3.5+ | `gemini-3.6-flash` | REQUIRED |
| Model transport | Gemini API | REQUIRED |
| Agent framework | Google ADK Python | REQUIRED |
| Agent deployment | `ngabo-core` on Cloud Run | REQUIRED |
| Web deployment | `ngabo-web` on Cloud Run | REQUIRED |
| Canonical workflow persistence | Firestore | REQUIRED |
| Event transport | Pub/Sub | REQUIRED |
| File/artifact storage | Cloud Storage | REQUIRED |
| Operational proof | Cloud Logging + supported tracing | REQUIRED |
| Semantic evidence retrieval | EmbeddingGemma | PLANNED after core green |
| Medical evidence interpretation | MedGemma | OPTIONAL gated stretch |

Google services/models must be visible in real code, deployment, diagram, evaluation and/or demo according to their claimed role. Do not list infrastructure or models that are not actually part of the submitted system.

---

## 3. Category Decision — The Taskmaster

The Taskmaster asks for a **complete workflow, not just a chatbot**: a system that takes action, handles a messy multi-step chore, sends the right information to the right places, and proves it performs the heavy lifting.

Ngabo's canonical Taskmaster flow is:

```text
new synthetic AMR data arrives
        ↓
deterministic ingestion + validation
        ↓
deterministic surveillance detector
        ↓
suspicious AMR investigation candidate
        ↓
Pub/Sub event
        ↓
Google ADK graph starts automatically
        ↓
load canonical incident context
        ↓
parallel deterministic fan-out
  ├─ resistance-profile comparison
  ├─ baseline summary
  └─ structural missing-field assessment
        ↓
join typed results
        ↓
Gemini triage only where ambiguity exists
        ↓
approved evidence retrieval
        ↓
targeted clarification only if materially required
        ↓
pause / resume same incident
        ↓
Gemini evidence-grounded synthesis
        ↓
deterministic package validation
        ↓
WAITING_FOR_REVIEW
        ↓
professional consequential-action approval
        ↓
deterministic pre-action freshness barrier
   ├─ stale → invalidate approval / re-review
   └─ fresh → continue
        ↓
real authorized outbound action
        ↓
acknowledgement + audit trail
```

### Taskmaster autonomy rule

The demo must never depend on a user typing:

> “Please investigate these isolates.”

The surveillance event wakes the workflow.

### Human-boundary narrative

The human does **not** manually drive the investigation.

The human may:

- provide a materially missing fact when specifically asked;
- approve/reject/request more information at the consequential response boundary;
- retain outbreak-confirmation and patient-treatment authority.

The human does **not**:

- choose mandatory calculations;
- sequence graph nodes;
- decide fixed routing branches;
- assemble the incident package manually;
- manually send the approved notification.

This safety boundary preserves Taskmaster autonomy rather than weakening it.

---

## 4. Official Judging Strategy

Stage Two weighting:

- **Innovation & Operational Utility — 40%**
- **Architectural Discipline & Tech Stack — 30%**
- **Demo & Production Readiness — 30%**

Ngabo explicitly optimizes for all three.

---

## 5. Innovation & Operational Utility — 40%

The submission must prove that Ngabo removes coordination friction between a surveillance signal and a response-ready investigation.

### Product proof

Show that Ngabo:

- accepts messy/realistic synthetic microbiology surveillance data;
- detects an investigation candidate deterministically;
- starts automatically from an event;
- performs required investigation work without user prompting;
- retrieves approved evidence;
- interrupts the human only for materially missing context;
- resumes the same incident;
- produces a structured, validated review-ready package;
- routes approved action automatically after freshness revalidation;
- tracks acknowledgement/completion.

Never present the product as merely “an LLM that summarizes AMR data.”

### Required operational-utility measurement

Use `docs/OPERATIONAL_UTILITY_EVALUATION.md` and report from real synthetic/deployed runs:

```text
signal_to_review_ready_ms
human_intervention_count
human_active_steps
clarification_count
manual_prompt_count_to_start
evidence_searches_completed_by_system
signal_to_action_ready_ms
action_to_ack_ms
model_call_count
deterministic_node_count
```

Compare against a documented scripted reference workflow using the same synthetic information.

Do not invent hospital time-saved percentages. If credible manual timing cannot be collected, report step/handoff reduction rather than fabricated time savings.

### Core Taskmaster acceptance

- `manual_prompt_count_to_start == 0`;
- mandatory deterministic work executes automatically;
- final human interaction is governance/safety, not step-by-step workflow guidance;
- real authorized action occurs outside the UI after approval if freshness passes;
- acknowledgement closes the loop.

---

## 6. Architectural Discipline & Tech Stack — 30%

The architecture must make deliberate engineering decisions visible.

### 6.1 Clean Architecture

Dependencies point inward:

```text
frameworks/cloud/ADK/models
        ↓
infrastructure/interface adapters
        ↓
application use cases / ports
        ↓
domain policy / deterministic scientific logic
```

ADK, Gemini, Firestore, Pub/Sub, GCS, FastAPI and Next.js remain outer implementation details.

### 6.2 Graph-first hybrid orchestration

Governing rule:

> **Deterministic when the workflow is known; agentic when the decision is ambiguous; dynamic only when the workflow itself cannot reasonably be known in advance.**

Known mandatory investigation work uses function nodes/code. Fixed exhaustive routing does not consume Gemini calls.

Gemini is reserved for bounded ambiguity such as:

- materiality of missing context;
- evidence-search intent when not deterministic;
- optional specialist capability selection;
- evidence sufficiency;
- evidence-grounded hypothesis/synthesis.

See `docs/ORCHESTRATION_PATTERNS.md` and ADR 0005.

### 6.3 Parallel fan-out / join

Independent read-only deterministic work should fan out and join when it improves latency/clarity without unsafe shared mutation.

Required branch failures remain explicit. Later model synthesis may not hide them.

### 6.4 State architecture

```text
Firestore/application persistence
  = canonical incident/workflow truth

ADK session/checkpoint state
  = execution continuity only

transient runtime state
  = recomputable working values

Cloud Storage artifacts
  = large/file-like outputs

long-term model/agent memory
  = not authoritative factual input for v0.1
```

See `docs/LONG_RUNNING_AGENT.md` and ADR 0006.

### 6.5 Long-running correctness

Required principle:

> **Resume execution, but revalidate truth.**

A resumed workflow reconstructs current canonical context. Context compaction/session summaries cannot replace isolate/AST facts, human decisions, citations, package versions or audit history.

### 6.6 Pre-action freshness barrier

Human approval is version-scoped.

Immediately before consequential external action, deterministic application logic compares the reviewed incident/package/source-watermark state with current state.

```text
APPROVED
  ↓
freshness check
  ├─ unchanged → action allowed
  └─ material change → approval stale → WAITING_FOR_REVIEW
```

Gemini does not decide whether a version mismatch exists.

### 6.7 Failure tolerance / idempotency

Prove:

- duplicate Pub/Sub delivery does not duplicate incidents/effects;
- retries/restarts are safe;
- side-effect tools/actions use idempotency keys;
- required branch failures are visible;
- model/tool/graph execution has bounded budgets;
- notification retries do not create ambiguous duplicates;
- stale approvals cannot be replayed after retry/redelivery.

### 6.8 Scoped capabilities

No arbitrary shell, unrestricted DB, unrestricted web browsing as approved evidence, direct agent notification bypass, source-data mutation, prescribing or autonomous outbreak confirmation.

ADK nodes/tools call inward application contracts.

### 6.9 Cost and context discipline

Track model-call count in the canonical scenario. Do not use Gemini for fixed routing, similarity, baselines, schema validation, joins or structural missing-field extraction.

Use bounded/reconstructed context and compaction where supported without redefining factual truth.

---

## 7. Demo & Production Readiness — 30%

Design intent does not earn these points by itself. The submission must show live proof.

### Required visible proof

- working hosted application if available;
- Google Cloud deployment proof (`.run.app`, Cloud Run dashboard/logs/traces or equivalent);
- autonomous Pub/Sub-triggered graph start;
- deterministic graph/node activity including fan-out/join;
- state persistence;
- evidence retrieval;
- clarification pause/resume of the same incident;
- validated incident package;
- professional review;
- freshness revalidation where legible;
- real authorized outbound action;
- acknowledgement/state update;
- concise architecture diagram;
- public evaluation artifact.

### Proof-of-action rule

Show at least one continuous, live, unedited execution segment where UI/log/database state changes prove the agent performed the work.

Do not replace live proof with only a slide, pre-recorded animation or screenshots of completed state.

### Reproducibility

Before submission:

- README spin-up instructions must match implementation;
- exact model/framework versions must be recorded;
- a synthetic seed/reset path should be available;
- hosted build should remain free/judge-accessible through judging;
- architecture diagram must match deployed runtime;
- full hosted scenario should pass repeatedly before freeze.

See `docs/SUBMISSION_EVIDENCE.md`.

---

## 8. ADK Runtime Must Be Real

Google ADK is a runtime capability, not a badge.

Required where supported/stable by the exact installed release:

- explicit workflow/graph orchestration;
- deterministic function nodes;
- parallel fan-out/join;
- bounded Gemini agent nodes;
- typed/validated outputs;
- execution/session/run identifiers;
- resumability/recovery;
- targeted human-input pause/resume;
- evaluations covering final result and observable trajectory;
- tracing/structured telemetry;
- model/tool/time/retry budgets.

Do not copy workshop API names blindly; verify exact installed ADK APIs during implementation.

---

## 9. Human Clarification vs Consequential Approval

These are different boundaries.

### Investigation clarification

```text
WAITING_FOR_CLARIFICATION
  ↓ targeted human answer
INVESTIGATING / RESUME SAME INCIDENT
```

Use only when a missing fact materially blocks a defensible assessment.

### Consequential approval

```text
WAITING_FOR_REVIEW
  ↓
APPROVED / REJECTED / NEEDS_MORE_INFO
```

This remains an application/domain safety gate, not merely an experimental framework confirmation primitive.

After approval, action still requires the deterministic freshness barrier.

---

## 10. Evaluation Is a Submission Artifact

Evaluation must cover:

### Deterministic/scientific

- parser/normalizer;
- AST mappings;
- profile similarity;
- baseline/window/scoring;
- state transitions;
- fixed routers;
- package validation;
- freshness-material-change policy.

### Graph/runtime

- required function-node execution;
- fan-out completion-order independence;
- join semantics;
- required branch failure;
- timeouts/retries;
- zero Gemini call for fixed routing;
- model/function/tool call trajectory;
- resume/recovery;
- canonical-context rebuild.

### Agent/safety

- clarification when required and not otherwise;
- empty/no evidence;
- prompt injection as data;
- fabricated source/isolate rejection;
- unsupported/prohibited clinical claims;
- bounded agent/tool loops;
- citation/source integrity.

### Long-running/action

- stale approval blocks action;
- unchanged approved state permits action;
- retry/redelivery cannot reuse stale approval;
- notification idempotency;
- acknowledgement closure;
- context/session memory never overrides canonical truth.

### Operational utility

- reference workflow;
- human active-step comparison;
- human intervention count;
- signal-to-review-ready timing;
- zero-prompt autonomous start;
- limitations.

Produce a public `EVALUATION.md` containing real results before submission.

---

## 11. Observability Is Product Proof

Capture safe structured metadata such as:

```text
correlation_id
incident_id
event_id
graph_run_id
node_name
node_type
branch_id
join_id
agent_session_id
agent_invocation_id
agent_run_id
model_name
incident_version
package_version
review_id
source_watermark
freshness_result
```

Useful public-safe workflow events include:

```text
INVESTIGATION_GRAPH_STARTED
FUNCTION_NODE_STARTED
FUNCTION_NODE_COMPLETED
PARALLEL_FANOUT_STARTED
PARALLEL_BRANCH_COMPLETED
PARALLEL_JOIN_COMPLETED
AGENT_NODE_STARTED
EVIDENCE_SEARCH_COMPLETED
CLARIFICATION_REQUESTED
AGENT_RUN_PAUSED
AGENT_RUN_RESUMED
CONTEXT_REBUILT
PACKAGE_VALIDATION_COMPLETED
REVIEW_APPROVED
FRESHNESS_CHECK_STARTED
FRESHNESS_CHECK_PASSED
FRESHNESS_CHECK_FAILED
APPROVAL_MARKED_STALE
NOTIFICATION_SENT
NOTIFICATION_ACKNOWLEDGED
```

Do not expose hidden chain-of-thought.

Default to metadata/no-sensitive-content tracing even though the public v0.1 dataset is synthetic.

---

## 12. Real External Action — Required

Keep a deterministic local/test notification adapter.

The hosted/filmed submission should perform at least one **real authorized external action** after approval and freshness validation through:

```text
application use case
      ↓
NotificationPort
      ↓
real authorized adapter
```

Acceptance:

- authorized target only;
- approval first;
- freshness check passes;
- idempotency key used;
- delivery attempt/result persisted;
- external result visible;
- acknowledgement/equivalent completion updates Ngabo;
- UI labels real vs demo channel truthfully.

---

## 13. Additional Google AI Model Strategy

Official rules award **+0.2 per successfully integrated additional Google AI model**, up to **+0.6** from models.

### EmbeddingGemma — planned

After core deployed E2E is green:

```text
approved guidance corpus
→ EmbeddingGemma embeddings
→ lightweight in-process similarity index
→ approved source IDs/chunks
→ Gemini reasoning
```

Evaluate retrieval quality and provenance. Do not add a vector database solely for bonus points.

### MedGemma — gated stretch

Potential bounded role:

```text
retrieved approved medical/AMR evidence
→ MedGemma structured interpretation
→ Gemini synthesis
```

It must not diagnose, prescribe, confirm outbreaks, replace deterministic surveillance calculations or introduce uncited authority.

Only keep it if evaluation demonstrates meaningful value without harming safety, latency or reliability.

### Bonus discipline

Do not add a third model merely for points. Claim no model bonus until integration is real, documented, evaluated and demonstrable.

---

## 14. Multimodal Stretch — Best Multimodal UX

Optional after core freeze:

```text
photo / scanned PDF AST report
→ Gemini multimodal extraction
→ UNVERIFIED AI DRAFT
→ human verification/edit
→ canonical deterministic ingestion
```

The detector must never consume unverified model extraction.

Multimodal work must not jeopardize Taskmaster/architecture/demo reliability.

---

## 15. Public Build / Social Bonus

### Public content (+0.2 max)

Publish real build content and include explicit language that it was created for the purposes of entering the All Things Agentic Hackathon 2026.

### Social (+0.2 max)

Use the exact hashtag:

`#AllThingsAgenticHackathon`

Capture public URLs in `docs/SUBMISSION_EVIDENCE.md` before claiming bonus points.

---

## 16. Third-Party, Data, Ownership & Pre-Existing Work Compliance

Official rules require authorization for third-party SDKs, APIs, data and other information, and disclosure of non-standard pre-existing code/work incorporated into the project.

Ngabo therefore requires `docs/THIRD_PARTY_PROVENANCE.md`.

Before submission:

- exact direct dependency/model/service versions and usage basis are recorded;
- approved AMR guidance corpus sources have provenance/usage records;
- public demo fixtures are Ngabo-authored synthetic data unless another source is explicitly authorized;
- real patient/lab data is absent;
- any non-standard pre-existing work actually reused is disclosed;
- third-party logos/media do not imply unauthorized sponsorship/endorsement;
- optional models are not included/claimed until their exact terms and actual integration are verified.

---

## 17. Cloud Cost, Security & Judge Availability

Required deployment controls:

### Cloud Run

- minimum instances `0` unless documented technical reason;
- explicit max-instance cap;
- right-sized CPU/memory;
- separate `ngabo-web` and `ngabo-core`;
- no accidental public admin/developer endpoints.

### Cost

- Google Cloud budget;
- at least one budget alert;
- lightweight artifact/log retention;
- avoid always-on infrastructure not required by the demo.

### Security

- Secret Manager/injected secrets;
- no committed credentials;
- protected internal event endpoints;
- validate Pub/Sub origin/auth where applicable;
- protect/rate-limit expensive public endpoints where practical;
- least-privilege service accounts where practical;
- ADK Web remains local-development only;
- no A2A service in v0.1 without a new ADR.

Do not remove the hosted service required for judging before the judging period ends.

---

## 18. Required Architecture Diagram

The final diagram must show the actual deployed runtime:

```text
Browser
  ↓
Cloud Run: ngabo-web
  ↓
Cloud Run: ngabo-core
  ├─ Clean Architecture application/domain core
  ├─ deterministic surveillance core
  ├─ Google ADK graph runtime
  │    ├─ deterministic function nodes
  │    ├─ parallel fan-out/join
  │    └─ Gemini agent nodes
  ├─ EvidenceSearchPort → EmbeddingGemma only if implemented
  ├─ optional MedGemma only if implemented
  └─ NotificationPort → authorized external target

Pub/Sub → event interface
Firestore ↔ canonical application persistence
Cloud Storage ↔ artifacts/raw imports
Cloud Logging / Trace ← public-safe execution telemetry

WAITING_FOR_REVIEW
      ↓ HUMAN AUTHORITY BOUNDARY
APPROVED
      ↓ PRE-ACTION FRESHNESS BARRIER
AUTHORIZED ACTION
```

Do not show optional technologies as active if they are not implemented.

---

## 19. Four-Minute Demo Storyboard

The UI/product must support a concise sequence:

1. problem + friction + value proposition;
2. synthetic data arrival/import;
3. deterministic signal detection;
4. Pub/Sub-triggered graph without prompt;
5. visible function-node fan-out/join;
6. bounded Gemini/evidence activity;
7. targeted clarification + answer + same-incident resume;
8. validated evidence-backed package;
9. professional approval;
10. freshness check;
11. real external action;
12. acknowledgement;
13. fast Google Cloud/architecture/evaluation proof.

The video must remain <=4 minutes. Optimize for clarity, not feature count.

---

## 20. Prize Positioning

### The Taskmaster — primary target

Ngabo is deliberately shaped around complete event-driven autonomous workflow execution.

### Best Architectural Design — deliberate secondary target

The submission should explicitly explain and prove:

- Clean Architecture;
- state ownership;
- graph-first orchestration;
- deterministic/agentic separation;
- scoped capabilities;
- idempotency/failure semantics;
- resume/recovery;
- context/memory discipline;
- freshness barrier;
- observability/evaluation.

### Individual/Hobbyist

Eligibility depends on final entrant/team structure; ensure Devpost participant structure is truthful.

### Startup Excellence

Only pursue if final submission satisfies the official incorporated-organization/corporate-email eligibility requirements.

### Best Multimodal UX

Optional only after the core is frozen and stable.

### Grand Prize

The only credible route is a high-scoring core across all three Stage Two criteria plus truthful bonus execution. Do not optimize one special prize at the expense of the weighted core.

A submission can win at most one prize.

---

## 21. Required Submission Evidence

Use `docs/SUBMISSION_EVIDENCE.md` as the proof ledger.

Before submission, actual evidence must exist for:

- hosted URL if available;
- repository;
- tested spin-up instructions;
- final architecture diagram;
- public <=4-minute video;
- visible Google Cloud proof;
- live Proof of Action;
- public measured `EVALUATION.md`;
- operational-utility results;
- real authorized action/ack;
- third-party/data/pre-existing-work provenance;
- every bonus claimed.

Architecture documentation is not a substitute for these artifacts.

---

## 22. Definition of Hackathon-Ready

Ngabo is not submission-ready until:

- [ ] Gemini 3.6 Flash actually performs the bounded agent reasoning path;
- [ ] Google ADK actually runs the graph/workflow;
- [ ] mandatory deterministic graph nodes fan out/join as designed;
- [ ] fixed routing performs zero unnecessary Gemini calls;
- [ ] Cloud Run hosts the working services;
- [ ] Firestore persists canonical incident/workflow state;
- [ ] Pub/Sub triggers asynchronous processing;
- [ ] Cloud Storage stores required artifacts/files;
- [ ] clarification pauses/resumes the same incident;
- [ ] context is reconstructed safely after resume;
- [ ] side effects are idempotent;
- [ ] stale approvals are blocked by the freshness barrier;
- [ ] one real authorized outbound action works;
- [ ] acknowledgement/completion closes the workflow;
- [ ] graph/agent evaluation suite is run and documented;
- [ ] operational-utility benchmark is measured and documented;
- [ ] Cloud Logging/tracing provides inspectable proof;
- [ ] full seeded E2E succeeds repeatedly on GCP;
- [ ] architecture diagram matches deployed system;
- [ ] README spin-up instructions are tested/polished;
- [ ] third-party/data/pre-existing-work register is complete;
- [ ] hosted project remains available through judging;
- [ ] demo video is <=4 minutes and public;
- [ ] LinkedIn article/social requirements are satisfied if bonuses are claimed;
- [ ] EmbeddingGemma/MedGemma/multimodal are claimed only if actually implemented/evaluated;
- [ ] `docs/SUBMISSION_EVIDENCE.md` contains proof locations for every competitive claim;
- [ ] no unimplemented capability appears in Devpost/video copy.

---

## 23. Required Companion Contracts

Before implementing or changing the hackathon/runtime path, read:

- `docs/CLEAN_ARCHITECTURE.md`
- `docs/ADK_RUNTIME.md`
- `docs/ORCHESTRATION_PATTERNS.md`
- `docs/LONG_RUNNING_AGENT.md`
- `docs/DATA_SAFETY_EVALUATION.md`
- `docs/OPERATIONAL_UTILITY_EVALUATION.md`
- `docs/UI_UX_SPEC.md`
- `docs/UI_UX_HACKATHON_ADDENDUM.md`
- `docs/THIRD_PARTY_PROVENANCE.md`
- `docs/SUBMISSION_EVIDENCE.md`
- `docs/IMPLEMENTATION_PLAN.md`
- ADR 0005 and ADR 0006.

---

## 24. Official Sources

- Rules: https://allthingsagentichackathon.devpost.com/rules
- Resources: https://allthingsagentichackathon.devpost.com/resources
- Google ADK: https://google.github.io/adk-docs/
- Gemini API: https://ai.google.dev/gemini-api/docs
- EmbeddingGemma: https://ai.google.dev/gemma/docs/embeddinggemma
- MedGemma: https://developers.google.com/health-ai-developer-foundations/medgemma

Re-check official rules immediately before final submission. If they diverge from this contract, update this contract first.
