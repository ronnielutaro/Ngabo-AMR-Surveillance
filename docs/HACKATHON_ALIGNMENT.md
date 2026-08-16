# Ngabo — All Things Agentic Hackathon Alignment

**Status:** Required v0.1 implementation and submission contract  
**Version:** 0.3  
**Hackathon:** All Things Agentic Hackathon 2026  
**Primary category:** The Taskmaster  
**Submission deadline:** 2026-08-31 17:00 PT

---

## 1. Competition Objective

Ngabo is designed to maximize the published judging criteria while remaining truthful, safe and technically defensible.

Official Stage Two weighting:

- **Innovation & Operational Utility — 40%**
- **Architectural Discipline & Tech Stack — 30%**
- **Demo & Production Readiness — 30%**

Official Taskmaster emphasis:

- complete workflow, not just a chatbot;
- event-driven/background execution;
- autonomous routing/action;
- high-value real-world friction;
- multi-step workflow completed without human intervention;
- Bring Your Own Friction (BYOF): solve a unique, personal problem.

Official Stage Three bonus paths:

- public build content: up to `+0.2`;
- qualifying social post: up to `+0.2`;
- additional successfully integrated Google AI models: `+0.2` each, up to `+0.6`.

Official sources:

- https://allthingsagentichackathon.devpost.com/rules
- https://allthingsagentichackathon.devpost.com/resources

If official rules change, they override this document.

---

## 2. Mandatory Technology Contract

The submitted v0.1 must actually use and visibly prove:

| Requirement | Ngabo decision |
|---|---|
| Gemini 3.5+ | `gemini-3.6-flash` via Gemini API |
| Google Agent Framework | Google ADK Python |
| Google Cloud infrastructure | Cloud Run + Firestore + Pub/Sub + Cloud Storage |
| Agent deployment | `ngabo-core` on Cloud Run |
| Web deployment | `ngabo-web` on Cloud Run |
| Canonical workflow state | Firestore |
| Async event transport | Pub/Sub |
| Files/artifacts | Cloud Storage |
| Observability proof | Cloud Logging + supported Trace/OpenTelemetry path |
| Planned additional model | EmbeddingGemma after core green |
| Gated additional model | MedGemma only if evaluation proves benefit |

Technology listed in Devpost/video/diagram must be real in the submitted release.

---

## 3. Canonical Taskmaster Hero — Zero Human Intervention

The **hero workflow must complete from surveillance event to external acknowledgement with no human input**.

Required hero metrics:

```text
manual_prompt_count_to_start == 0
human_intervention_count == 0
human_active_steps == 0
clarification_count == 0
approval_click_count == 0
```

Canonical flow:

```text
synthetic AMR data arrives
        ↓
deterministic validation + normalization
        ↓
deterministic surveillance signal
        ↓
Pub/Sub event
        ↓
Google ADK workflow starts automatically
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
Gemini bounded triage
        ↓
approved evidence retrieval
        ↓
Gemini evidence-grounded synthesis
        ↓
deterministic package validation
   └─ bounded automatic repair if necessary
        ↓
deterministic autonomous-action policy
        ↓
pre-action freshness barrier
        ↓
idempotency reservation
        ↓
real authorized safe external action
        ↓
machine acknowledgement callback/event
        ↓
audit + completion
```

No chat prompt, clarification answer, approval click or manual routing action occurs after the trigger.

See `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`.

---

## 4. Safety Without Mandatory Human Intervention

Ngabo does **not** solve the Taskmaster requirement by allowing unrestricted clinical autonomy.

Instead it constrains the autonomous action envelope.

### Autonomous action classes

```text
A0 INTERNAL_STATE
→ autonomous

A1 SAFE_EXTERNAL_COORDINATION
→ autonomous after policy + freshness + idempotency gates

A2 REAL_OPERATIONAL_ESCALATION
→ outside autonomous public-v0.1 envelope unless separately authorized

A3 CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION
→ forbidden as autonomous v0.1 action
```

The hero action is A1: a real authorized external coordination action to an allow-listed test/sandbox/internal endpoint, clearly labelled as an **investigation candidate**, not a diagnosis, confirmed outbreak or treatment instruction.

Clinical/official public-health authority remains out of scope for the autonomous hero lane.

This policy supersedes earlier v0.1 wording that made human approval mandatory for every external action. Human-governed consequential lanes remain valid future/real-world architecture, but they are **not** the Taskmaster hero path.

---

## 5. Autonomous Safety Gates

Before A1 execution, deterministic application logic must confirm:

- canonical input valid;
- surveillance signal valid;
- required graph branches successful;
- no unresolved material blocker for A1 action;
- evidence/source integrity valid;
- package schema valid;
- no prohibited diagnosis/prescribing/outbreak-confirmation claim;
- action is classified A1;
- destination is allow-listed and authorized;
- current incident/package/source state passes freshness validation;
- idempotency reservation is acquired.

Any failed gate produces **autonomous abstention**, not unsafe completion.

Valid bounded outcomes include:

```text
NEEDS_INFORMATION
INSUFFICIENT_APPROVED_EVIDENCE
VALIDATION_FAILED
POLICY_BLOCKED
STALE_RECOMPUTE_REQUIRED
ACTION_FAILED_RETRYABLE
ACTION_FAILED_TERMINAL
```

---

## 6. No Clarification on the Hero Path

The canonical hero fixture must contain all material data required for A1 completion.

For other scenarios:

- material missing fact → abstain safely;
- optional missing fact → preserve `UNKNOWN` and continue only if policy permits;
- recoverable canonical fact → retrieve automatically from an already-authorized linked source;
- never invent clinical facts to avoid asking a person.

Long-running pause/resume remains an important engineering/evaluation capability, but it is **not required inside the hero demo**.

---

## 7. Autonomous Repair

A deterministic validator may return structured errors to a bounded Gemini repair loop.

```text
synthesis
→ validator
   ├─ valid → continue
   └─ invalid → structured errors → repair → validator
```

Rules:

- maximum repair attempts configured (suggested `2`);
- model cannot override validator;
- exhausted repair budget → safe stop;
- invalid package can never reach external action.

This replaces human correction for normal model-format/claim errors.

---

## 8. BYOF — Personal Friction

Ngabo's Taskmaster story is not merely “AMR is important.”

The builder's personal friction is the repeated manual workflow encountered while researching/building AMR intelligence:

```text
inspect signal/data
→ inspect isolates
→ compare resistance profiles
→ inspect baseline/context
→ identify missingness
→ find trusted guidance
→ separate facts/hypotheses
→ assemble structured incident brief
→ validate sources/claims
→ route result
→ track completion
```

Ngabo is the agent built to automate that personally experienced coordination workflow.

Use `docs/BYOF_FRICTION.md` as the source of truth. Do not imply the builder is a hospital microbiologist or claim practitioner validation unless it actually occurs.

Optional practitioner conversations can strengthen relevance, but they are not fabricated prerequisites for the BYOF claim.

---

## 9. Innovation & Operational Utility — 40%

The strongest scoring story must be measurable.

Required evidence from deployed synthetic runs:

```text
manual_prompt_count_to_start
human_intervention_count
human_active_steps
clarification_count
signal_to_review_ready_ms
signal_to_autonomous_action_ms
action_to_ack_ms
evidence_searches_completed_by_system
model_call_count
deterministic_node_count
retry_count
abstention_count/reason where applicable
```

Compare Ngabo against the frozen builder reference workflow in `docs/BYOF_FRICTION.md` and `docs/OPERATIONAL_UTILITY_EVALUATION.md`.

Do not manufacture hospital productivity percentages or clinical outcome claims.

Hero requirement:

```text
human_intervention_count == 0
```

---

## 10. Architectural Discipline & Tech Stack — 30%

Ngabo deliberately targets this prize/criterion.

### Clean Architecture

```text
frameworks / cloud / ADK / models
              ↓
infrastructure + interface adapters
              ↓
application use cases / ports
              ↓
domain policy + deterministic science
```

### Graph-first rule

> **Deterministic when the workflow is known; agentic when the decision is ambiguous; dynamic only when the workflow itself cannot reasonably be known in advance.**

### State truth

```text
Firestore/application persistence = canonical truth
ADK session/checkpoint            = execution continuity
transient state                   = recomputable work
Cloud Storage                     = file/large artifacts
model memory                      = not authoritative AMR truth
```

### Reliability

Prove:

- at-least-once event redelivery is idempotent;
- required branch failure is visible;
- process/model/tool retry is bounded;
- old session context cannot override current facts;
- freshness protects autonomous action;
- repair loops are bounded;
- A2/A3 action requests cannot be escalated into A1 by Gemini;
- scoped capabilities cannot run arbitrary shell/DB/web actions.

See:

- `docs/CLEAN_ARCHITECTURE.md`
- `docs/ORCHESTRATION_PATTERNS.md`
- `docs/LONG_RUNNING_AGENT.md`
- `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`
- `docs/HACKATHON_RISK_REGISTER.md`

---

## 11. ADK API Risk Must Be Eliminated Early

Before implementing the production graph runtime, complete `docs/ADK_CAPABILITY_SPIKE.md` against the exact pinned ADK Python version.

The spike must prove:

- backend/event invocation without interactive chat;
- supported deterministic/sequential/parallel orchestration path;
- join/failure semantics;
- structured Gemini output;
- validator boundary;
- session/resume approach;
- eval/observability path.

If workshop API names differ from the shipping package, preserve the architecture using supported ADK workflow primitives/application orchestration. Do not introduce another agent framework merely to match workshop terminology.

---

## 12. Demo & Production Readiness — 30%

The 4-minute video must show **undeniable live execution**, not a slide deck of intentions.

### Hero video sequence

1. In 20–30 seconds explain the BYOF friction.
2. Show synthetic signal/data arrival.
3. Show Pub/Sub-triggered workflow start automatically.
4. Show deterministic fan-out/branch completion/join.
5. Show bounded Gemini/evidence stage.
6. Show validated package.
7. Show autonomy-policy result: `A1 SAFE EXTERNAL COORDINATION`.
8. Show freshness + idempotency gate.
9. Show real authorized external action outside Ngabo.
10. Show machine acknowledgement returning to Ngabo.
11. Show `human interventions: 0` / operational benchmark briefly.
12. Show Cloud Run/log proof + architecture diagram.

Do **not** put a clarification or approval click in the hero flow.

Resume/recovery, stale-approval/action blocking and other safety scenarios belong in `EVALUATION.md`/technical proof unless they fit without obscuring the zero-human story.

---

## 13. Real External Action

The hero action must leave Ngabo and execute against a real authorized external service/endpoint.

Preferred:

```text
NotificationPort
→ authorized test/sandbox webhook
→ external delivery ID/state
→ automated acknowledgement callback/event
→ Ngabo incident update
```

A local fake is still required for tests, but it does not count as filmed proof of external action.

Never contact a real hospital/person without explicit authorization.

---

## 14. Judge-Facing Architecture Diagram

`docs/ARCHITECTURE_DIAGRAM.md` is the canonical judge-facing architecture visual.

Before submission it must be reconciled to the deployed release and exported as needed.

It must make these concepts obvious in seconds:

- Cloud Run web/core;
- Pub/Sub autonomous trigger;
- Firestore canonical state;
- ADK graph;
- deterministic fan-out/join;
- Gemini bounded agent nodes;
- evidence adapter / optional EmbeddingGemma;
- autonomous A1 policy gate;
- freshness/idempotency;
- external action + acknowledgement;
- A2/A3 safety boundary.

---

## 15. Evaluation Requirements

Public `EVALUATION.md` must report real results for:

### Zero-human hero

- zero prompts;
- zero interventions;
- zero clarifications;
- zero approval clicks;
- full event-to-ack completion.

### Scientific/deterministic

- parsing/normalization;
- resistance profile;
- baseline/window/scoring;
- state transitions;
- package validation;
- action classification;
- freshness policy.

### Graph/runtime

- branch order independence;
- required branch failure;
- zero model call for fixed routing;
- model/tool budgets;
- restart/recovery;
- idempotent redelivery.

### Agent/safety

- prompt injection;
- fabricated isolate/source;
- no evidence;
- bounded repair success/failure;
- prohibited clinical claims;
- A2/A3 auto-action rejection;
- old session conflict loses to canonical state.

### External action

- real A1 delivery;
- retry behavior;
- machine acknowledgement;
- duplicate suppression.

---

## 16. Bonus Strategy

Priority order:

1. excellent zero-human core;
2. reliable deployment/evaluation/video;
3. public build article `+0.2`;
4. social post `+0.2` using exact `#AllThingsAgenticHackathon`;
5. EmbeddingGemma `+0.2` if real/evaluated;
6. MedGemma only if it adds measured value;
7. multimodal only after core freeze.

Do not destabilize the 40/30/30 core to chase bonus points.

---

## 17. Prize Positioning

Deliberate targets:

- **The Taskmaster** — primary category;
- **Grand Prize** — overall score target;
- **Best Architectural Design** — explicit secondary scoring target;
- **Individual/Hobbyist** — if entrant/team structure qualifies;
- **Startup Excellence** — only if final organization/corporate-email eligibility is intentionally satisfied;
- **Best Multimodal UX** — optional stretch only if genuinely polished.

One submission can win at most one prize under the official rules.

---

## 18. Submission/Compliance Gates

Before submission:

- mandatory tech really runs;
- project functions as depicted;
- public repo/testing access available;
- README spin-up instructions tested;
- hosted URL stable if used;
- architecture diagram matches deployment;
- <=4 minute public YouTube/Vimeo demo;
- video visibly proves Google Cloud backend;
- third-party/data/pre-existing work disclosure complete;
- no real patient/lab data;
- every competitive claim has evidence;
- unimplemented model/feature removed from claims.

See `docs/SUBMISSION_EVIDENCE.md` and `docs/THIRD_PARTY_PROVENANCE.md`.

---

## 19. Submission Freeze

Use `docs/SUBMISSION_FREEZE.md`.

At freeze:

```text
release/v0.1.0 → main → tag v0.1.0
```

Record and preserve:

- commit SHA;
- Cloud Run revisions;
- URLs;
- exact model/framework versions;
- dataset/evidence versions;
- evaluation artifact;
- architecture diagram;
- video;
- final claim ledger.

Keep the judged `main`/tag/deployment/video stable throughout the judging period. Future development must not silently alter the judged system.

---

## 20. Risk Register

`docs/HACKATHON_RISK_REGISTER.md` is mandatory competition control.

Critical/high risks can be closed only by implementation/evidence, not by writing a design document.

---

## 21. Definition of Hackathon-Ready

Ngabo is ready only when:

- [ ] hero workflow completes event→external action→ack with zero human intervention;
- [ ] A1 autonomous policy is deterministic and tested;
- [ ] A2/A3 cannot auto-execute;
- [ ] ADK capability spike passed and exact version pinned;
- [ ] Gemini/ADK/GCP are real and visible;
- [ ] deployed E2E passes repeatedly;
- [ ] `EVALUATION.md` contains real measured results;
- [ ] operational utility benchmark proves zero-human replacement of BYOF reference workflow;
- [ ] real authorized external action + machine acknowledgement work;
- [ ] diagram matches deployed release;
- [ ] README spin-up path works;
- [ ] proof-of-action video contains continuous live execution;
- [ ] provenance/disclosure complete;
- [ ] submission freeze manifest complete;
- [ ] all claimed bonuses have actual evidence;
- [ ] final claims remain within synthetic/non-clinically-validated boundaries.
