# AGENTS.md — Ngabo Coding-Agent Rules

This file applies to AI coding agents working anywhere in this repository.

Read `CLAUDE.md` first. It is the root implementation contract.

---

## 1. Mission

Build Ngabo as a safe, event-driven AMR surveillance and incident-response system whose **canonical Taskmaster hero workflow completes with zero human intervention** while keeping clinical/official public-health decisions outside the autonomous v0.1 action envelope.

Optimize for:

- asynchronous event-driven autonomy;
- zero-human hero completion;
- deterministic scientific logic;
- graph-first hybrid orchestration;
- safe A1 external coordination;
- deterministic action policy;
- bounded automatic repair;
- freshness/idempotency;
- safe abstention;
- canonical state discipline;
- observability/evaluation;
- Clean Architecture;
- monorepo discipline;
- BYOF operational utility;
- truthful submission evidence.

---

## 2. Required Read Order

1. `CLAUDE.md`
2. `ROADMAP.md`
3. `CONTRIBUTING.md`
4. `docs/PRD.md`
5. `docs/TECH_STACK.md`
6. `docs/CLEAN_ARCHITECTURE.md`
7. `docs/HACKATHON_ALIGNMENT.md`
8. `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`
9. `docs/BYOF_FRICTION.md`
10. `docs/ADK_CAPABILITY_SPIKE.md`
11. `docs/ADK_RUNTIME.md`
12. `docs/ORCHESTRATION_PATTERNS.md`
13. `docs/LONG_RUNNING_AGENT.md`
14. `docs/SYSTEM_DESIGN.md`
15. `docs/AGENT_ARCHITECTURE.md`
16. `docs/DATA_SAFETY_EVALUATION.md`
17. `docs/OPERATIONAL_UTILITY_EVALUATION.md`
18. `docs/UI_UX_SPEC.md`
19. `docs/UI_UX_HACKATHON_ADDENDUM.md`
20. `docs/ARCHITECTURE_DIAGRAM.md`
21. `docs/THIRD_PARTY_PROVENANCE.md`
22. `docs/SUBMISSION_EVIDENCE.md`
23. `docs/SUBMISSION_FREEZE.md`
24. `docs/HACKATHON_RISK_REGISTER.md`
25. `docs/IMPLEMENTATION_PLAN.md`
26. relevant ADRs, especially 0005 and 0006.

If older documents still mention mandatory human approval/clarification in the v0.1 hero, `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md` and `CLAUDE.md` supersede that wording for the safe A1 hero lane.

---

## 3. Hero Invariant

Required canonical flow:

```text
signal
→ Pub/Sub
→ ADK workflow
→ deterministic fan-out/join
→ bounded Gemini reasoning
→ approved evidence
→ synthesis
→ deterministic validation / bounded repair
→ deterministic A1 autonomy policy
→ freshness
→ idempotency
→ real external action
→ machine acknowledgement
```

Required counters:

```text
manual_prompt_count_to_start = 0
human_intervention_count = 0
human_active_steps = 0
clarification_count = 0
approval_click_count = 0
```

Do not implement the hero as an interactive chat or human-guided workflow.

---

## 4. Safety Envelope

Action classes:

```text
A0 INTERNAL_STATE                autonomous
A1 SAFE_EXTERNAL_COORDINATION    autonomous after gates
A2 REAL_OPERATIONAL_ESCALATION   not autonomous public-v0.1 by default
A3 CLINICAL/OFFICIAL DECISION    never autonomous v0.1
```

Rules:

- action class is deterministic application/domain policy;
- Gemini cannot promote A2/A3 to A1;
- hero target must be allow-listed and authorized;
- hero payload is an investigation candidate/synthetic demonstration;
- no prescribing, diagnosis or autonomous outbreak confirmation;
- no real hospital/person contact without explicit authorization.

---

## 5. Missing Data

Do not use a human question to keep the hero moving.

```text
material fact absent → NEEDS_INFORMATION → no action
optional fact absent → UNKNOWN; continue only if policy permits
recoverable fact → fetch automatically only from authorized canonical source
```

Never invent a clinical fact for zero-human completion.

The hero fixture must be complete enough to finish safely.

---

## 6. Clean Architecture

```text
Frameworks / Infrastructure
          ↓
Interfaces / Adapters
          ↓
Application / Use Cases / Ports
          ↓
Domain
```

Inner layers must not import FastAPI/GCP/ADK/Gemini/Next.js.

ADK nodes/tools call inward application contracts.

Forbidden:

```text
ADK node -> raw Firestore + business logic
Gemini -> direct external action
route -> scientific calculation
application -> concrete cloud/model SDK
React -> cloud/model SDK
```

---

## 7. Deterministic vs Agentic

Deterministic owns:

- parsing/validation/normalization;
- AST/profile/baseline/window/scoring;
- structural missingness;
- fixed routing;
- join/failure semantics;
- package validation;
- action classification;
- allow-list authorization;
- freshness;
- idempotency;
- acknowledgement state.

Gemini owns only bounded ambiguity:

- reasoning over joined findings;
- evidence intent when not deterministic;
- source-grounded synthesis;
- labelled hypotheses;
- bounded repair from validator errors;
- stopping with uncertainty.

No model call for ordinary fixed policy.

---

## 8. ADK Capability Spike

Before production orchestration code:

- run `docs/ADK_CAPABILITY_SPIKE.md`;
- pin exact ADK version;
- verify event/backend invocation;
- verify supported parallel/join path;
- verify structured output;
- verify session/resume/eval/trace path;
- choose documented fallback if workshop API differs.

Do not guess APIs and do not add another orchestration framework to compensate.

---

## 9. Automatic Repair

Package validation is deterministic.

If invalid:

```text
structured errors → Gemini repair → validator
```

Hard max attempts. Suggested `2`.

If budget exhausted: `VALIDATION_FAILED`; no action.

---

## 10. External Action

Hero uses a real A1 integration through `NotificationPort`.

Preferred:

```text
authorized test/sandbox webhook
→ delivery ID
→ machine acknowledgement callback/event
```

Keep fake adapter for tests.

No person should need to acknowledge the hero action.

---

## 11. State / Retry / Freshness

- Firestore/application state is canonical truth;
- ADK session is execution continuity only;
- Pub/Sub may redeliver;
- read-only work is repeatable;
- side effects are idempotent;
- freshness runs immediately before external action;
- changed canonical data triggers recompute/revalidation;
- stale session/context never authorizes action.

---

## 12. Failure / Abstention

Legitimate states:

```text
NEEDS_INFORMATION
INSUFFICIENT_APPROVED_EVIDENCE
VALIDATION_FAILED
POLICY_BLOCKED
STALE_RECOMPUTE_REQUIRED
ACTION_FAILED_RETRYABLE
ACTION_FAILED_TERMINAL
```

Do not fake completion.

---

## 13. UI

Hero UI shows:

- event start;
- deterministic fan-out/join;
- bounded Gemini/evidence stages;
- validation/repair;
- A1 autonomy-policy result;
- freshness/idempotency;
- external delivery;
- machine acknowledgement;
- zero-human metrics.

No clarification card or approval click in canonical hero.

---

## 14. Evaluation

Hero assertions:

```text
0 prompts
0 interventions
0 human steps
0 clarifications
0 approvals
1 external effect
1 machine acknowledgement
```

Also test:

- A2/A3 blocked;
- material missing fact abstains;
- non-allow-listed target blocked;
- prompt injection;
- fabricated citation/isolate;
- repair success/exhaustion;
- branch failure;
- freshness recompute;
- duplicate event/retry idempotency;
- canonical state beats session text;
- restart/recovery.

Run three consecutive deployed hero E2Es before demo freeze.

---

## 15. BYOF

The personal friction is the builder's own repeated AMR research/coordination workflow described in `docs/BYOF_FRICTION.md`.

Do not borrow clinical identity.

Operational benchmark compares builder reference human steps against zero-human Ngabo hero.

---

## 16. Git / Release Governance

Feature work:

```text
feature/<name> from develop → PR to develop
```

Release:

```text
release/vX.Y.Z → main → tag → reconcile develop
```

Use SemVer + Conventional Commits.

For hackathon release, follow `docs/SUBMISSION_FREEZE.md`: preserve judged main/tag/Cloud Run revisions/video through judging.

---

## 17. Scope Freeze

Until zero-human deployed hero and core evals are green, do not add:

- MedGemma;
- multi-agent specialist fleet;
- dynamic topology;
- multimodal ingestion;
- genomics;
- vector DB;
- LangGraph;
- GKE/Redis/Kafka;
- real patient data;
- real hospital connector;
- A2/A3 autonomous actions.

EmbeddingGemma begins only after core green.

---

## 18. Stop Conditions

Stop rather than guess if:

- official rules changed;
- exact ADK API is unknown;
- hero requires human input;
- zero-human completion would require inventing clinical data;
- action is not A1/authorized/allow-listed;
- model is being asked to own deterministic safety policy;
- external side effect lacks idempotency;
- package can bypass validator;
- dependency direction is inverted;
- claim lacks real evidence;
- bonus work threatens hero reliability.

---

## 19. Definition of Done

A milestone is done only when relevant tests are green, architecture boundaries hold, safety policy holds, docs/evidence are updated, and the change does not weaken the zero-human Taskmaster hero.

The final release is not complete until a deployed scenario proves event→action→machine-ack completion with **zero human intervention** and the safety eval proves A2/A3 clinical/official actions remain blocked.
