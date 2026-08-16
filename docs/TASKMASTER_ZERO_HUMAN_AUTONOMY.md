# Ngabo — Zero-Human Taskmaster Autonomy & Safety Policy

**Status:** Required v0.1 hackathon runtime and demo contract  
**Date:** 2026-08-16  
**Primary category:** The Taskmaster

---

## 1. Decision

Ngabo's **canonical hackathon hero workflow must complete end-to-end with zero human intervention after the synthetic surveillance event is emitted**.

For the hero path:

```text
human_intervention_count == 0
manual_prompt_count_to_start == 0
clarification_count == 0
```

This does **not** mean Ngabo autonomously makes unrestricted clinical or official public-health decisions.

Ngabo achieves literal Taskmaster autonomy by separating:

1. **safe autonomous coordination actions** that are permitted to execute automatically; and
2. **consequential clinical/public-health actions** that remain outside the autonomous v0.1 action envelope.

The governing principle is:

> **Automate the complete coordination workflow; constrain the action envelope instead of weakening safety.**

---

## 2. Why This Exists

The official Taskmaster judging language asks whether the agent can intercept and complete a multi-step background workflow **without human intervention**.

Earlier Ngabo designs intentionally used clarification and human approval inside the canonical demo. Those are valuable production-safety patterns, but making them mandatory in the hero path creates unnecessary judging ambiguity.

The revised design therefore makes the hero scenario fully autonomous while preserving strong safety boundaries through deterministic policy, allow-listed action classes, abstention, validation, freshness checks, and idempotency.

---

## 3. Dual-Lane Action Architecture

### Lane A — Autonomous Coordination Lane (v0.1 hero path)

Ngabo may autonomously execute actions that are:

- non-diagnostic;
- non-prescribing;
- non-outbreak-confirming;
- reversible or low-consequence;
- sent only to an explicitly configured, authorized test/sandbox or internal coordination target;
- clearly labelled as a surveillance **investigation candidate**, not a confirmed clinical/public-health determination.

Examples:

- create/update the Ngabo incident record;
- persist the validated evidence-backed incident package;
- create a test incident/ticket through an authorized webhook;
- send an AMR investigation-candidate notification to an authorized test inbox/webhook;
- publish a structured machine-readable incident payload to a sandbox integration;
- request and receive an automated acknowledgement callback;
- schedule deterministic follow-up checks.

This lane is the **Taskmaster hero lane**.

### Lane B — Consequential Decision Lane

Actions that could directly alter clinical treatment, formally declare/confirm an outbreak, contact real patients, initiate real facility-wide containment, or represent an official public-health escalation remain outside the zero-human autonomous envelope.

Examples:

- prescribing or changing antimicrobials;
- official outbreak confirmation;
- patient-specific clinical instructions;
- irreversible real-world interventions;
- official regulator/public-health declarations;
- contacting a real hospital/person without explicit authorization.

For future real-world deployments these actions require appropriate institutional governance and human authority.

The hackathon does **not** need to use a high-risk action to prove autonomous execution.

---

## 4. Action Risk Classes

Every external action must be assigned a deterministic class before execution.

```text
A0 — INTERNAL_STATE
     incident state, audit event, package persistence
     → autonomous

A1 — SAFE_EXTERNAL_COORDINATION
     allow-listed test/sandbox/internal coordination action
     → autonomous if all policy gates pass

A2 — REAL_OPERATIONAL_ESCALATION
     real stakeholder/facility escalation with meaningful operational consequence
     → not autonomous in public v0.1 unless separately approved by policy/authorization

A3 — CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION
     prescribing, treatment, diagnosis, official outbreak confirmation/declaration
     → forbidden as autonomous v0.1 action
```

Gemini does **not** assign the final executable action class. The application policy engine owns this classification and authorization.

---

## 5. Autonomous Action Gate

Before any A1 external action, Ngabo must pass all deterministic gates:

```text
canonical input valid
        ↓
surveillance signal valid
        ↓
mandatory graph branches succeeded
        ↓
no unresolved material-data blocker for this safe action class
        ↓
evidence/source integrity valid
        ↓
incident package schema valid
        ↓
no prohibited clinical/outbreak claims
        ↓
action class == A1
        ↓
destination allow-listed
        ↓
authorization configuration valid
        ↓
pre-action freshness check passes
        ↓
idempotency reservation acquired
        ↓
EXECUTE
```

Any failed gate causes **autonomous abstention**, not unsafe improvisation.

---

## 6. No-Human Clarification Policy for the Hero Path

The hero scenario must contain all material canonical fields needed for the intended A1 action.

Ngabo must not ask the user a question during the hero path.

Missing-data policy:

### Required material fact unavailable

```text
missing material fact
→ deterministic/agentic materiality assessment
→ autonomous abstention / NEEDS_INFORMATION state
→ no fabricated value
→ no unsafe action
```

### Optional/non-material field unavailable

```text
field remains UNKNOWN
→ package records uncertainty
→ workflow may continue if policy permits A1 action
```

### Recoverable information

Ngabo may retrieve information automatically from already-authorized canonical sources/adapters when a deterministic linkage exists.

Ngabo must not hallucinate specimen type, ward, AST result, patient fact, resistance mechanism, or other canonical clinical fact merely to avoid a clarification.

The hero dataset is intentionally complete enough that the workflow completes without entering the abstention path.

---

## 7. Autonomous Repair Instead of Human Repair

Where a model-generated artifact fails a deterministic validator, Ngabo should attempt a bounded automatic repair loop rather than asking the user to fix it.

Example:

```text
Gemini synthesis
   ↓
PackageValidator
   ├─ valid → continue
   └─ invalid
        ↓
structured validation errors
        ↓
Gemini repair attempt
        ↓
PackageValidator
```

Requirements:

- maximum repair attempts configured;
- validator errors are structured and do not reveal private chain-of-thought;
- model cannot override the validator;
- after the limit, Ngabo autonomously stops safely;
- no consequential action occurs from an invalid package.

Suggested v0.1 default:

```text
max_package_repair_attempts = 2
```

---

## 8. Evidence Failure Strategy

No human lookup is required in the hero path.

Evidence strategy:

1. deterministic/tag retrieval where sufficient;
2. EmbeddingGemma semantic retrieval after the core is green, if integrated;
3. bounded alternate query formulation when Gemini is legitimately needed;
4. source-integrity validation;
5. if adequate approved evidence still cannot be retrieved, state `INSUFFICIENT_APPROVED_EVIDENCE` and abstain from any action whose policy requires evidence.

The agent may not browse arbitrary URLs and convert them into approved authority during v0.1.

---

## 9. Zero-Human Hero Workflow

Canonical hackathon demonstration:

```text
synthetic AMR import/event
        ↓
deterministic validation + normalization
        ↓
deterministic surveillance signal
        ↓
Pub/Sub
        ↓
Google ADK graph starts automatically
        ↓
canonical context load
        ↓
parallel deterministic fan-out
  ├─ resistance-profile comparison
  ├─ baseline summary
  └─ missing-field assessment
        ↓
join
        ↓
Gemini bounded triage
        ↓
approved evidence retrieval
        ↓
Gemini evidence-grounded synthesis
        ↓
deterministic package validation
   └─ bounded automatic repair if needed
        ↓
autonomous action-policy gate
        ↓
deterministic freshness barrier
        ↓
idempotency reservation
        ↓
real authorized A1 external action
        ↓
automated acknowledgement callback
        ↓
incident closes / follow-up scheduled
```

**No prompt, clarification, approval click, or human routing action occurs between the trigger and acknowledgement.**

---

## 10. Action Payload Safety

The hero action should use language such as:

> **AMR surveillance investigation candidate — synthetic demonstration. This is not a confirmed outbreak, diagnosis, or treatment recommendation.**

Payloads may include:

- incident ID;
- organism;
- time/location pattern;
- deterministic resistance-profile findings;
- evidence source IDs;
- uncertainties;
- investigation checklist;
- link back to Ngabo incident;
- synthetic-data marker.

Payloads must not include autonomous prescribing or outbreak-confirmation language.

---

## 11. Automated Acknowledgement

To close the Taskmaster loop without a person clicking anything, use a real authorized integration capable of machine acknowledgement.

Preferred demo shape:

```text
Ngabo NotificationPort
        ↓
authorized test webhook / sandbox endpoint
        ↓
external delivery recorded
        ↓
automated acknowledgement callback/event
        ↓
Ngabo updates incident state
```

The external action must be real in the sense that it leaves Ngabo and is observed by another authorized endpoint/service. It does not need to contact a real hospital or clinician.

---

## 12. Freshness Still Applies

Removing mandatory human approval from the hero lane does not remove freshness protection.

Immediately before external A1 action:

- compare current incident/package/source watermark;
- ensure no material canonical change occurred after synthesis;
- regenerate/revalidate if necessary;
- only act on current state.

The freshness barrier therefore becomes an **autonomous safety mechanism** rather than merely an approval-protection mechanism.

---

## 13. Autonomous Abstention Is a Feature

A safe autonomous agent must know when not to act.

Valid terminal/degraded states include:

```text
NEEDS_INFORMATION
INSUFFICIENT_APPROVED_EVIDENCE
VALIDATION_FAILED
POLICY_BLOCKED
STALE_RECOMPUTE_REQUIRED
EXTERNAL_ACTION_FAILED_RETRYABLE
EXTERNAL_ACTION_FAILED_TERMINAL
```

These states should be visible and evaluated.

Do not convert uncertainty into fake completion merely to satisfy the demo.

---

## 14. Hero Scenario Contract

The seeded hero scenario must be engineered to exercise the complete autonomous path truthfully:

- material canonical fields present;
- deterministic suspicious signal detected;
- all required graph branches succeed;
- approved evidence exists;
- synthesis can produce a valid package;
- action payload is A1-safe;
- target is allow-listed and authorized;
- freshness check passes;
- external action succeeds;
- automated acknowledgement succeeds.

The demo may separately show or cite evaluation scenarios where Ngabo abstains safely.

---

## 15. Evaluation Requirements

Required assertions:

- `manual_prompt_count_to_start == 0`;
- `human_intervention_count == 0` on hero path;
- `clarification_count == 0` on hero path;
- no human approval is required for A1 hero action;
- action classifier never upgrades A2/A3 into A1;
- missing material fact causes abstention, not hallucination;
- invalid synthesis enters bounded repair and never bypasses validation;
- failed repair causes safe stop;
- stale source state forces recomputation before action;
- duplicate/redelivered event produces at most one external effect;
- A1 action destination must be allow-listed;
- A3 action request is always rejected by v0.1 policy;
- automated acknowledgement closes the hero workflow.

---

## 16. UI / Demo Requirements

The hero video should visually prove:

```text
0 human prompts
0 clarification answers
0 approval clicks
1 autonomous event trigger
1 autonomous graph execution
1 validated package
1 safe external action
1 automated acknowledgement
```

The UI should display a compact label such as:

`Autonomy policy: SAFE COORDINATION — eligible for automatic action`

For blocked cases:

`Autonomy policy: BLOCKED — clinical/official decision requires external governance`

---

## 17. Real-World Deployment Boundary

The hackathon's zero-human hero lane is deliberately restricted to safe coordination actions.

Future hospital/public-health deployment requires separate validation and governance for any wider action envelope, including:

- institutional authorization;
- identity/RBAC;
- policy ownership;
- audit/compliance;
- clinical/public-health validation;
- escalation rules;
- data protection;
- local regulatory review.

Do not use hackathon autonomy as evidence that clinical/public-health decisions should be fully autonomous.

---

## 18. Definition of Done

The zero-human Taskmaster contract is satisfied when:

- [ ] hero workflow completes from event to acknowledgement with no human input;
- [ ] hero external action is real, authorized, safe and outside the Ngabo UI;
- [ ] action classification is deterministic and tested;
- [ ] A2/A3 actions cannot enter the autonomous lane;
- [ ] missing/uncertain data can cause autonomous abstention;
- [ ] bounded automatic synthesis repair exists;
- [ ] freshness and idempotency gates remain mandatory;
- [ ] acknowledgement is machine-driven;
- [ ] `EVALUATION.md` reports the zero-human result from deployed runs;
- [ ] submission/video clearly distinguish safe coordination autonomy from clinical/public-health authority.
