# Ngabo — All Things Agentic Hackathon Alignment

**Status:** Required v0.1 implementation and submission contract  
**Version:** 0.4  
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

Taskmaster emphasis:

- complete workflow, not chatbot;
- event-driven/background execution;
- autonomous routing/action;
- high-value real-world friction;
- multi-step workflow completed without human intervention;
- Bring Your Own Friction (BYOF): solve a unique, personal problem;
- make the project’s distinctive **Twist** obvious to judges.

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

The hero workflow must complete from surveillance event to external acknowledgement with no human input.

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
Gemini proof-carrying synthesis
        ↓
deterministic claim/evidence verification
   ├─ invalid → structured errors → bounded repair → verify again
   └─ repair exhausted → autonomous abstention
        ↓
deterministic A1 autonomous-action policy
        ↓
pre-action freshness barrier
        ↓
transactional ActionIntent + idempotency
        ↓
real authorized safe external action
        ↓
machine acknowledgement callback/event
        ↓
audit + completion
```

No chat prompt, clarification answer, approval click or manual routing action occurs after the trigger.

See `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md` and `docs/PROOF_CARRYING_REASONING.md`.

---

## 4. The Twist — Proof-Carrying Autonomy

Ngabo's competition **Twist** is:

> **Proof-Carrying Autonomy: Ngabo completes an AMR investigation-to-coordination workflow with zero human intervention, while refusing to trust fluent LLM output on faith. Every action-relevant model claim must carry machine-checkable references to canonical records, deterministic findings, and/or approved evidence before the claim can influence autonomous action.**

The technical rule is:

> **LLM proposes; deterministic machinery verifies whatever can be verified before the claim may influence autonomous action.**

This is deliberately different from ordinary “agent + prompt + tool” designs.

Proof-carrying claims include:

```text
OBSERVED_FACT       → canonical record references
DERIVED_FINDING     → deterministic result references
EVIDENCE_STATEMENT  → retrieved approved evidence references
HYPOTHESIS          → supporting proof + explicit uncertainty
ACTION_JUSTIFICATION→ verified upstream claims; never action authority
```

The verifier rejects:

- fabricated/unknown record IDs;
- fabricated/unknown deterministic findings;
- unapproved or unretrieved source IDs;
- hypothesis→fact escalation;
- forbidden claim types;
- unsupported factual assertions;
- stale package references;
- attempts by model output to authorize A2/A3 action.

Private chain-of-thought is not evidence, persisted truth, or a judge-facing safety claim.

The Twist must be explicit in:

- README;
- Devpost description;
- architecture diagram;
- first 60 seconds of the demo;
- `EVALUATION.md`.

---

## 5. Safety Without Mandatory Human Intervention

Ngabo does not satisfy Taskmaster by allowing unrestricted clinical autonomy. It constrains the autonomous action envelope.

```text
A0 INTERNAL_STATE
→ autonomous

A1 SAFE_EXTERNAL_COORDINATION
→ autonomous after proof verification + policy + freshness + idempotency gates

A2 REAL_OPERATIONAL_ESCALATION
→ outside autonomous public-v0.1 envelope unless separately authorized

A3 CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION
→ forbidden as autonomous v0.1 action
```

The hero action is A1: a real authorized external coordination action to an allow-listed test/sandbox/internal endpoint, clearly labelled as an **investigation candidate**, not a diagnosis, confirmed outbreak or treatment instruction.

Clinical/official public-health authority remains out of scope for the autonomous hero lane.

---

## 6. Autonomous Safety Gates

Before A1 execution, deterministic application logic must confirm:

1. canonical input valid;
2. surveillance signal valid;
3. required graph branches successful;
4. no unresolved material blocker;
5. approved evidence/source integrity valid;
6. proof-carrying claim verification passed;
7. package schema/claim boundary valid;
8. action classified A1;
9. destination allow-listed/authorized;
10. current incident/package/source state fresh;
11. durable `ActionIntent` prepared with stable idempotency semantics.

Any failed gate produces autonomous abstention/recompute, never model override.

Valid bounded outcomes include:

```text
NEEDS_INFORMATION
INSUFFICIENT_APPROVED_EVIDENCE
CLAIM_VERIFICATION_FAILED
VALIDATION_FAILED
POLICY_BLOCKED
STALE_RECOMPUTE_REQUIRED
ACTION_FAILED_RETRYABLE
ACTION_FAILED_TERMINAL
```

---

## 7. No Clarification on the Hero Path

The canonical hero fixture must contain all material data required for A1 completion.

Other scenarios:

- material missing fact → abstain safely;
- optional missing fact → preserve `UNKNOWN` and continue only if policy permits;
- recoverable canonical fact → retrieve from already-authorized linked source;
- never invent clinical facts to avoid asking a person.

Long-running pause/resume remains an engineering/evaluation capability, not required inside the hero demo.

---

## 8. Proof Verification + Bounded Repair

```text
Gemini proof-carrying synthesis
→ deterministic verifier
   ├─ valid → continue
   └─ invalid → structured verification errors
                  ↓
             bounded Gemini repair
                  ↓
                verifier
                  ↓
          exhausted? → abstain
```

Rules:

- hard max repair attempts (target `2`);
- repair can use only permitted canonical facts/findings/evidence unless the graph explicitly routes through approved retrieval;
- model cannot mutate source facts/deterministic findings/action policy;
- invalid/unverified package never reaches A1 policy;
- private CoT is irrelevant to verifier authority.

---

## 9. BYOF — Personal Friction

Ngabo's Taskmaster story is not merely “AMR is important.”

Builder friction:

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

Ngabo automates that repeated coordination workflow.

Use `docs/BYOF_FRICTION.md` as source of truth. Do not imply practitioner identity or clinical validation unless actually obtained.

---

## 10. Innovation & Operational Utility — 40%

The strongest scoring story is:

```text
PERSONAL FRICTION
+
ZERO-HUMAN EVENT→ACTION→ACK
+
PROOF-CARRYING AUTONOMY TWIST
+
MEASURED BEFORE/AFTER UTILITY
```

Required deployed evidence:

```text
manual_prompt_count_to_start
human_intervention_count
human_active_steps
clarification_count
signal_to_package_ms
signal_to_autonomous_action_ms
action_to_ack_ms
evidence_searches_completed_by_system
claim_count
claim_verification_failure_count
repair_attempt_count
model_call_count
deterministic_node_count
retry_count
abstention_count/reason
```

Compare Ngabo against the frozen builder reference workflow in `docs/BYOF_FRICTION.md` and `docs/OPERATIONAL_UTILITY_EVALUATION.md`.

Do not manufacture hospital productivity percentages or clinical outcome claims.

---

## 11. Architectural Discipline & Tech Stack — 30%

Ngabo deliberately targets this criterion/prize.

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

### Deterministic/agentic boundary

> **Deterministic when the workflow is known; agentic when the decision is ambiguous; dynamic only when the workflow itself cannot reasonably be known in advance.**

### Truth hierarchy

```text
canonical source facts
→ deterministic scientific calculations
→ approved retrieved evidence
→ verified structured model claims
→ labelled hypotheses/synthesis
→ deterministic action policy
→ freshness/idempotency
→ A1 action
```

### Reliability proof

Show:

- at-least-once event redelivery is idempotent;
- required branch failure is visible;
- process/model/tool retry bounded;
- old session context cannot override current facts;
- proof verifier blocks fabricated/stale references;
- freshness protects autonomous action;
- repair loops bounded;
- A2/A3 cannot be escalated into A1 by Gemini;
- external effects use ActionIntent/outbox/idempotency;
- scoped capabilities cannot run arbitrary shell/DB/web actions.

---

## 12. ADK API Risk Must Be Eliminated Early

Before production runtime implementation, complete `docs/ADK_CAPABILITY_SPIKE.md` against the exact pinned `google-adk` version.

Prove:

- backend/event invocation without interactive chat;
- supported deterministic/sequential/parallel orchestration path;
- join/failure semantics;
- structured Gemini output compatible with proof-carrying DTOs;
- deterministic verifier boundary outside model authority;
- session/resume approach;
- eval/observability path.

If workshop API names differ, preserve architecture with supported ADK/application primitives. Do not add another orchestration framework merely to imitate workshop terminology.

---

## 13. Demo & Production Readiness — 30%

The <=4 minute video must show undeniable live execution.

Recommended sequence:

1. **0:00–0:25** — BYOF friction;
2. **0:25–0:45** — signal/event arrives;
3. **0:45–1:30** — Pub/Sub start + deterministic fan-out/join + Gemini/evidence;
4. **1:30–2:00** — Proof-Carrying Autonomy: show claims linked to records/findings/sources and deterministic verification;
5. **2:00–2:20** — A1 policy + freshness + ActionIntent/idempotency;
6. **2:20–2:45** — real external action + machine acknowledgement;
7. **2:45–3:10** — zero-human/BYOF benchmark;
8. **3:10–3:40** — architecture + Cloud Run/log proof;
9. **3:40–4:00** — evaluation/limitations/close.

No person should type/click to advance the hero sequence after trigger.

---

## 14. Real External Action

Hero action must leave Ngabo and execute against a real authorized external service/endpoint.

```text
ActionIntent
→ NotificationPort
→ authorized test/sandbox endpoint
→ external delivery ID/state
→ automated acknowledgement callback/event
→ Ngabo incident update
```

A local fake remains required for tests but does not count as filmed proof of external action.

---

## 15. Evaluation Requirements

Public `EVALUATION.md` must report real results for:

### Zero-human hero
- zero prompts/interventions/clarifications/approvals;
- full event→action→ack completion;
- three consecutive deployed passes before freeze.

### Scientific/deterministic
- parsing/normalization;
- resistance profile;
- baseline/window/scoring;
- state transitions;
- action classification;
- freshness policy.

### Proof-Carrying Autonomy
- unknown record ID rejected;
- unknown deterministic finding rejected;
- unknown/unretrieved source rejected;
- stale package/finding reference rejected;
- hypothesis→fact escalation rejected;
- forbidden claim types rejected;
- action blocked when proof verification fails;
- repair success/exhaustion measured;
- `unsafe_claim_escape_rate == 0` target on committed adversarial software suite.

Do **not** present that target as clinical validation or universal hallucination elimination.

### Runtime/action
- branch-order independence;
- required branch failure;
- zero model call for fixed routing;
- model/tool budgets;
- restart/recovery;
- idempotent redelivery;
- real A1 delivery;
- machine acknowledgement;
- duplicate suppression.

---

## 16. Bonus Strategy

Priority:

1. excellent zero-human core;
2. proof-carrying verifier + reliable deployment/evaluation/video;
3. public build article `+0.2` if eligible;
4. social post `+0.2` using exact required hashtag;
5. EmbeddingGemma `+0.2` if real/evaluated;
6. MedGemma only if measured value;
7. multimodal only after core freeze.

Do not destabilize the 40/30/30 core for bonus points.

---

## 17. Prize Positioning

Deliberate targets:

- **The Taskmaster** — primary;
- **Grand Prize** — overall-score target;
- **Best Architectural Design** — strong deliberate secondary target;
- **Individual/Hobbyist** — if entrant structure qualifies;
- **Startup Excellence** — only if final organization/corporate eligibility is satisfied;
- **Best Multimodal UX** — optional stretch only if genuinely polished.

One submission may win at most one prize under the official rules.

---

## 18. Submission / Compliance Gates

Before submission:

- mandatory tech really runs;
- project functions as depicted;
- repo/testing access available;
- README spin-up instructions tested;
- hosted URL stable if used;
- architecture diagram matches deployment;
- <=4 minute public demo;
- video visibly proves Google Cloud backend;
- third-party/data/pre-existing-work disclosure complete;
- no real patient/lab data;
- every competitive claim has evidence;
- Proof-Carrying Autonomy claimed only if implemented/evaluated;
- unimplemented model/feature removed from claims.

See `docs/SUBMISSION_EVIDENCE.md` and `docs/THIRD_PARTY_PROVENANCE.md`.

---

## 19. Submission Freeze

Use `docs/SUBMISSION_FREEZE.md`.

At freeze:

```text
release/v0.1.0 → main → tag v0.1.0
```

Record/preserve commit SHA, Cloud Run revisions, URLs, exact model/framework versions, dataset/evidence hashes, evaluation artifact, architecture diagram, video and final claim ledger throughout judging.

---

## 20. Definition of Hackathon-Ready

Ngabo is ready only when:

- [ ] hero completes event→external action→ack with zero human intervention;
- [ ] Proof-Carrying Autonomy is implemented, not merely documented;
- [ ] proof verifier blocks fabricated/stale/forbidden claims;
- [ ] A1 policy deterministic and tested;
- [ ] A2/A3 cannot auto-execute;
- [ ] ADK capability spike passed and exact version pinned;
- [ ] Gemini/ADK/GCP real and visible;
- [ ] deployed E2E passes repeatedly;
- [ ] `EVALUATION.md` contains measured results;
- [ ] BYOF benchmark measured;
- [ ] real authorized external action + machine acknowledgement work;
- [ ] architecture diagram matches deployment;
- [ ] README spin-up path works;
- [ ] proof-of-action video contains continuous live execution;
- [ ] provenance/disclosure complete;
- [ ] submission freeze complete.
