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
- proof-carrying model claims;
- deterministic claim/evidence verification;
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

## 2. Issue-Driven Execution

Work is driven by GitHub issues. The active issue is the **task-specific implementation contract** for the current change.

- `CLAUDE.md`, `AGENTS.md`, architecture docs, ADRs, safety/data contracts and hackathon invariants remain governing constraints.
- An issue may **narrow scope** but may not override those governing constraints.
- If an issue conflicts with a governing contract, stop and report the conflict; do not silently choose one side.
- Do not implement later milestones merely because the next work is obvious.
- Stop when the current issue's acceptance criteria are satisfied.
- Keep each PR limited to the issue it closes.
- Do not merge the PR yourself unless explicitly instructed by the human maintainer.

---

## 3. Required Read Order

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
13. `docs/PROOF_CARRYING_REASONING.md`
14. `docs/LONG_RUNNING_AGENT.md`
15. `docs/AUTONOMOUS_EFFECT_OUTBOX.md`
16. `docs/SYSTEM_DESIGN.md`
17. `docs/AGENT_ARCHITECTURE.md`
18. `docs/DATA_SAFETY_EVALUATION.md`
19. `docs/OPERATIONAL_UTILITY_EVALUATION.md`
20. `docs/UI_UX_SPEC.md`
21. `docs/UI_UX_HACKATHON_ADDENDUM.md`
22. `docs/ARCHITECTURE_DIAGRAM.md`
23. `docs/THIRD_PARTY_PROVENANCE.md`
24. `docs/SUBMISSION_EVIDENCE.md`
25. `docs/SUBMISSION_FREEZE.md`
26. `docs/HACKATHON_RISK_REGISTER.md`
27. `docs/IMPLEMENTATION_PLAN.md`
28. relevant ADRs, especially 0005–0009.

If older documents still mention mandatory human approval/clarification in the v0.1 hero, `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md` and `CLAUDE.md` supersede that wording for the safe A1 hero lane.

---

## 4. Hero Invariant

Required canonical flow:

```text
signal
→ Pub/Sub
→ ADK workflow
→ deterministic fan-out/join
→ bounded Gemini reasoning
→ approved evidence
→ proof-carrying synthesis
→ deterministic claim/evidence verification
→ bounded repair or abstention
→ deterministic A1 autonomy policy
→ freshness
→ transactional ActionIntent / outbox / stable idempotency key
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

## 5. Safety Envelope

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

## 6. Missing Data

Do not use a human question to keep the hero moving.

```text
material fact absent → NEEDS_INFORMATION → no action
optional fact absent → UNKNOWN; continue only if policy permits
recoverable fact → fetch automatically only from authorized canonical source
```

Never invent a clinical fact for zero-human completion.

The hero fixture must be complete enough to finish safely.

---

## 7. Clean Architecture

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
Gemini -> verifier/policy override
route -> scientific calculation
application -> concrete cloud/model SDK
React -> cloud/model SDK
```

---

## 8. Deterministic vs Agentic

Deterministic owns:

- parsing/validation/normalization;
- AST/profile/baseline/window/scoring;
- structural missingness;
- fixed routing;
- join/failure semantics;
- canonical record/finding/source reference verification;
- claim-type/policy validation;
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
- typed proof-carrying claim drafting;
- bounded repair from verifier errors;
- stopping with uncertainty.

No model call for ordinary fixed policy.

---

## 9. Proof-Carrying Reasoning

Ngabo's hackathon **Twist** is **Proof-Carrying Autonomy**. The governing principle:

> **LLM proposes; deterministic machinery verifies whatever can be verified before the claim may influence autonomous action.**

Read `docs/PROOF_CARRYING_REASONING.md` and ADR 0009.

Every material action-relevant model claim must be typed and machine-checkable against canonical data, deterministic findings and/or approved retrieved evidence.

Required claim families include:

```text
OBSERVED_FACT
DERIVED_FINDING
EVIDENCE_STATEMENT
HYPOTHESIS
ACTION_JUSTIFICATION
```

Rules:

- observed facts reference canonical records;
- derived findings reference deterministic result IDs;
- evidence statements reference actually retrieved approved source IDs;
- hypotheses remain labelled hypotheses and carry supporting evidence/uncertainty;
- action justifications do not authorize actions;
- forbidden diagnosis/prescription/outbreak-confirmation/official-authority claims fail verification;
- unknown references fail verification;
- unverified packages never reach A1 action policy.

Private/hidden chain-of-thought is not evidence, is not canonical incident truth and must not be exposed. Self-consistency/multiple-candidate reasoning may improve quality but never bypasses deterministic verification.

---

## 10. ADK Capability Spike

Before production orchestration code:

- run `docs/ADK_CAPABILITY_SPIKE.md`;
- pin exact ADK version;
- verify event/backend invocation;
- verify supported parallel/join path;
- verify structured output;
- verify session/resume/eval/trace path;
- choose documented fallback if workshop API differs.

The spike must prove the chosen ADK version supports:

```text
structured proof-carrying DTOs
→ deterministic verifier routing
→ bounded automatic repair
```

Verification and authorization policy must not be moved into prompts or model behavior.

Do not guess APIs and do not add another orchestration framework to compensate.

---

## 11. Automatic Repair

Claim/package verification is deterministic.

If invalid:

```text
structured errors → Gemini repair → deterministic verifier
```

Hard max attempts. Suggested `2`.

Repair may not invent canonical records/findings/sources, mutate action policy or bypass verification.

If budget exhausted: `VALIDATION_FAILED`; no action.

---

## 12. External Action

Hero uses a real A1 integration through `NotificationPort`.

Governing rule:

> **exactly-once Ngabo intent + idempotent external execution**

Applied to every autonomous external effect (see `docs/AUTONOMOUS_EFFECT_OUTBOX.md` for the full lifecycle):

- external effects must not bypass the durable `ActionIntent`/outbox path;
- retries reuse the stable idempotency key;
- verification, policy and freshness remain prerequisites to action;
- a crash/retry must not create a second Ngabo intent for the same authorized effect.

Preferred:

```text
verified package
→ ActionIntent / outbox
→ authorized test/sandbox webhook
→ delivery ID
→ machine acknowledgement callback/event
```

Keep fake adapter for tests.

No person should need to acknowledge the hero action.

---

## 13. State / Retry / Freshness

- Firestore/application state is canonical truth;
- ADK session is execution continuity only;
- Pub/Sub may redeliver;
- read-only work is repeatable;
- side effects are idempotent;
- claim verification is package/version scoped;
- freshness runs immediately before external action;
- changed canonical data triggers recompute/revalidation;
- stale session/context never authorizes action.

---

## 14. Failure / Abstention

Legitimate states:

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

Do not fake completion.

---

## 15. UI

Hero UI shows:

- event start;
- deterministic fan-out/join;
- bounded Gemini/evidence stages;
- claim types + supporting references;
- deterministic verification result;
- validation/repair;
- A1 autonomy-policy result;
- freshness/idempotency;
- external delivery;
- machine acknowledgement;
- zero-human metrics.

No clarification card or approval click in canonical hero.

Never expose chain-of-thought; expose evidence references, uncertainty and verification state instead.

---

## 16. Evaluation

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
- fabricated isolate/record reference;
- fabricated deterministic finding reference;
- fabricated/unretrieved source;
- hypothesis promoted to observed fact;
- forbidden claim-type escalation;
- proof-verification repair success/exhaustion;
- no A1 action from an unverified package;
- branch failure;
- freshness recompute;
- duplicate event/retry idempotency;
- canonical state beats session text;
- restart/recovery.

Track `unsafe_claim_escape_rate` on the committed adversarial software suite and target `0`; never present that as clinical validation or a universal hallucination guarantee.

Run three consecutive deployed hero E2Es before demo freeze.

---

## 17. BYOF

The personal friction is the builder's own repeated AMR research/coordination workflow described in `docs/BYOF_FRICTION.md`.

Do not borrow clinical identity.

Operational benchmark compares builder reference human steps against zero-human Ngabo hero.

---

## 18. Git / Release Governance

Feature work:

```text
feature/<name> from develop → PR to develop
```

Release:

```text
release/vX.Y.Z → main → tag → reconcile develop
```

Use SemVer + Conventional Commits.

Commit messages must not credit AI tooling. Do not add `Co-Authored-By: Claude` (or similar AI-attribution trailers) to commit messages; commit authorship belongs to the human contributor.

PR descriptions must not carry AI-generation footers such as "🤖 Generated with Claude Code" (or similar AI-attribution lines).

For hackathon release, follow `docs/SUBMISSION_FREEZE.md`: preserve judged main/tag/Cloud Run revisions/video through judging.

---

## 19. Scope Freeze

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

## 20. Stop Conditions

Stop rather than guess if:

- official rules changed;
- exact ADK API is unknown;
- hero requires human input;
- zero-human completion would require inventing clinical data;
- action is not A1/authorized/allow-listed;
- model is being asked to own deterministic safety policy;
- model output can bypass proof/reference verification;
- chain-of-thought is being persisted/exposed as authority;
- model consensus is being treated as proof;
- external side effect lacks idempotency;
- dependency direction is inverted;
- claim lacks real evidence;
- bonus work threatens hero reliability.

---

## 21. Definition of Done

A milestone is done only when relevant tests are green, architecture boundaries hold, proof-carrying claim verification holds, safety policy holds, docs/evidence are updated, and the change does not weaken the zero-human Taskmaster hero.

The final release is not complete until a deployed scenario proves event→proof-verified package→action→machine-ack completion with **zero human intervention** and the safety eval proves fabricated/forbidden claims cannot escape verification into A1 action while A2/A3 clinical/official actions remain blocked.
