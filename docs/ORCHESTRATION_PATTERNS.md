# Ngabo — ADK Orchestration Patterns

**Status:** Required v0.1 orchestration contract  
**Version:** 0.2  
**Date:** 2026-08-16  
**Framework:** Google ADK

---

## 1. Decision

Ngabo uses a **graph-first hybrid orchestration model**.

> **Deterministic when the workflow is known; agentic when the decision is ambiguous; dynamic only when the workflow itself cannot reasonably be known in advance.**

For the Taskmaster hero, the workflow continues beyond package creation through deterministic autonomous-action policy, freshness, idempotency, real A1 external action and machine acknowledgement—without human intervention.

See `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`.

---

## 2. v0.1 Hero Topology

```text
surveillance.signal.detected
          ↓
create/load incident
          ↓
FUNCTION: get_incident_context
          ↓
      FAN OUT
   ┌──────┼──────────┐
   │      │          │
   ▼      ▼          ▼
FUNCTION FUNCTION   FUNCTION
profile  baseline   missing-field
compare  summary    assessment
   │      │          │
   └──────┼──────────┘
          ▼
         JOIN
          ↓
AGENT: bounded investigation triage
          ↓
approved evidence retrieval
          ↓
AGENT: evidence-grounded synthesis
          ↓
FUNCTION: deterministic package validation
          ↓
ROUTE: valid?
   ├─ no → bounded automatic repair → validate
   └─ yes
          ↓
FUNCTION: autonomous action policy
   ├─ A1 eligible → continue
   └─ blocked/insufficient → autonomous abstention
          ↓
FUNCTION: freshness revalidation
          ↓
FUNCTION: idempotency reservation
          ↓
ADAPTER: real authorized A1 external action
          ↓
EVENT/CALLBACK: machine acknowledgement
          ↓
FUNCTION: completion state transition
```

Hero path contains no human clarification/approval node.

---

## 3. Function Nodes / Deterministic Stages

Use ordinary code for same-input/same-policy work:

- canonical context loading via application contract;
- resistance-profile comparison;
- baseline calculation/summary;
- structural missingness;
- fixed routing;
- state-transition legality;
- schema/claim validation;
- source/citation integrity;
- action classification A0/A1/A2/A3;
- destination allow-list authorization;
- material-change/freshness check;
- idempotency reservation;
- join semantics;
- acknowledgement state transition.

Do not call Gemini to implement deterministic safety policy.

---

## 4. Agent Nodes

Use Gemini where reasoning materially adds value:

- interpret joined structured findings;
- judge evidence intent when rules are insufficient;
- formulate bounded hypotheses;
- synthesize approved evidence into a structured package;
- repair a package from structured validator errors;
- stop with uncertainty when approved evidence is insufficient.

Agent nodes must use typed inputs/outputs, bounded tools/steps/time and no direct consequential side effects.

---

## 5. No-Human Missing-Data Routing

The hero fixture contains all material information.

Outside the hero:

```text
material fact missing
→ NEEDS_INFORMATION
→ autonomous abstention
```

Do not route to a human question merely to maintain completion.

Optional facts may remain unknown when the A1 policy allows continuation.

---

## 6. Deterministic Routing

No Gemini for:

```text
event type -> handler
incident state -> legal transition
duplicate event -> idempotency path
schema invalid -> validation failure
required branch failed -> bounded failure
package valid/invalid -> next path
action class A1 -> autonomy gate
action class A2/A3 -> block
non-allow-listed target -> block
fresh/stale -> execute/recompute
ack duplicate -> idempotent success
```

---

## 7. Agentic Routing

Permitted bounded questions:

- Which approved evidence topic is relevant?
- Is there enough evidence to form a labelled hypothesis?
- Which optional bounded capability is useful?
- How should structured findings be synthesized?
- How should a package be repaired given deterministic validator errors?

Gemini may not decide final action authorization.

---

## 8. Parallel Fan-Out / Join

Core independent read-only branches:

```text
compare_resistance_profiles
get_baseline_summary
get_missing_fields
```

Requirements:

- safe concurrent execution;
- immutable typed inputs;
- branch-specific telemetry;
- explicit join;
- completion order does not change semantic joined result;
- required failure blocks downstream synthesis;
- no external side effects inside fan-out.

---

## 9. Automatic Repair Loop

```text
Gemini synthesis
→ deterministic validator
   ├─ valid → autonomy policy
   └─ invalid → structured errors
                  ↓
             Gemini repair
                  ↓
               validator
```

Hard max attempts. Suggested `2`.

This is an intentionally bounded loop, not dynamic open-ended planning.

---

## 10. Autonomy Policy Stage

The deterministic policy engine evaluates:

- action class;
- package validity;
- evidence integrity;
- material blockers;
- target allow-list/authorization;
- required disclaimer/claim boundary.

Outcomes:

```text
AUTO_EXECUTE_A1
POLICY_BLOCKED
NEEDS_INFORMATION
INSUFFICIENT_APPROVED_EVIDENCE
```

The policy stage is application/domain logic exposed to orchestration through a typed contract.

---

## 11. Freshness / Idempotency Stages

Immediately before A1 external action:

```text
freshness
→ idempotency reservation
→ external adapter
```

Material canonical change causes recompute/revalidation; duplicate/retry must not duplicate external effect.

---

## 12. External Action / Ack

External action is **not** an unrestricted Gemini tool.

```text
workflow/application use case
→ NotificationPort
→ authorized A1 adapter
→ external service
→ machine acknowledgement event/callback
→ application acknowledgement use case
```

This preserves Clean Architecture and safety.

---

## 13. Clean Architecture Placement

```text
ADK/workflow primitive
        ↓
infrastructure orchestration adapter
        ↓
application query/use case/port
        ↓
domain/application deterministic policy
```

Forbidden:

```text
ADK node -> raw Firestore business mutation
ADK router -> direct notification
Gemini -> action class authorization
function node -> duplicated domain calculation
```

---

## 14. ADK API Fallback

Before coding, complete `docs/ADK_CAPABILITY_SPIKE.md`.

Preferred implementation:

1. supported first-class ADK workflow/graph primitives;
2. supported Sequential/Parallel/workflow agents + thin deterministic adapters;
3. application-owned graph/state machine invoking bounded ADK model-agent boundaries.

Architecture semantics matter more than copying webinar class names.

---

## 15. Collaborative Pattern

Not default for v0.1.

Potential future specialists only if evaluation shows measurable value:

- epidemiology;
- evidence;
- genomics;
- medical evidence interpretation.

Do not add agents for visual complexity or bonus optics.

---

## 16. Dynamic Pattern

Deferred from core v0.1.

A dynamic topology is for workflows whose structure genuinely cannot be known ahead of time. The hero AMR coordination workflow is known and should remain explicit.

---

## 17. Model-Call Budget

A model call must have a reason.

Do not use Gemini for:

- data fetch;
- fixed routing;
- similarity/baseline;
- missing-field extraction;
- validation;
- join;
- action classification;
- freshness;
- idempotency;
- ack state transition.

Record model-call count as a regression metric.

---

## 18. Failure Semantics

Required typed failure/abstention states include:

```text
REQUIRED_BRANCH_FAILED
NEEDS_INFORMATION
INSUFFICIENT_APPROVED_EVIDENCE
VALIDATION_FAILED
POLICY_BLOCKED
STALE_RECOMPUTE_REQUIRED
ACTION_FAILED_RETRYABLE
ACTION_FAILED_TERMINAL
```

No later Gemini stage may convert a critical deterministic failure into apparent success.

---

## 19. Observability

Useful events:

```text
INVESTIGATION_GRAPH_STARTED
PARALLEL_FANOUT_STARTED
PARALLEL_BRANCH_COMPLETED
PARALLEL_JOIN_COMPLETED
AGENT_NODE_STARTED
EVIDENCE_SEARCH_COMPLETED
PACKAGE_VALIDATION_FAILED
PACKAGE_REPAIR_STARTED
PACKAGE_VALIDATION_COMPLETED
AUTONOMY_POLICY_EVALUATED
FRESHNESS_CHECK_PASSED
IDEMPOTENCY_RESERVED
NOTIFICATION_SENT
NOTIFICATION_ACKNOWLEDGED
WORKFLOW_COMPLETED
WORKFLOW_ABSTAINED
```

No chain-of-thought.

---

## 20. Evaluation

Required:

- deterministic node repeatability;
- fan-out completion-order independence;
- required branch failure;
- fixed-router zero-model-call test;
- auto-repair success/exhaustion;
- A1 policy acceptance;
- A2/A3 policy rejection;
- missing-material-data abstention;
- freshness recompute;
- duplicate external-effect suppression;
- machine acknowledgement idempotency;
- hero zero-human trajectory.

---

## 21. Hero Acceptance

- [ ] surveillance event starts workflow without prompt;
- [ ] deterministic branches fan out/join;
- [ ] Gemini only handles bounded reasoning;
- [ ] approved evidence retrieved automatically;
- [ ] package validates or repairs within budget;
- [ ] no human clarification;
- [ ] no approval click;
- [ ] policy deterministically authorizes only A1;
- [ ] freshness/idempotency pass;
- [ ] real external A1 action occurs;
- [ ] machine acknowledgement returns;
- [ ] `human_intervention_count == 0`.
