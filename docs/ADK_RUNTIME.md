# Ngabo — Google ADK Runtime, Resumability & Evaluation Contract

**Status:** Required v0.1 agent-runtime contract  
**Version:** 0.4  
**Applies to:** `services/core/ngabo/infrastructure/ai/adk` and application workflows it coordinates

---

## 1. Objective

Ngabo uses Google ADK as a real runtime capability, not a badge.

The v0.1 hero is a graph-first hybrid workflow in which:

- known scientific/policy work stays deterministic;
- independent deterministic work fans out and joins;
- Gemini handles bounded ambiguity/synthesis;
- invalid model output can be repaired automatically within a hard budget;
- final A1 action authorization remains deterministic application policy;
- the event→action→ack hero requires zero human intervention.

Governing rule:

> **Deterministic when the workflow is known; agentic when the decision is ambiguous; dynamic only when the workflow itself cannot reasonably be known in advance.**

ADK remains outer infrastructure under Clean Architecture.

---

## 2. Mandatory Pre-Implementation Spike

Before production runtime code, complete `docs/ADK_CAPABILITY_SPIKE.md` against the exact pinned `google-adk` version.

Verify:

- backend/event invocation without interactive chat;
- supported sequential/parallel workflow primitives;
- join/failure semantics;
- structured Gemini output;
- session/run identifiers;
- resume/recovery capabilities;
- callbacks;
- eval/observability path.

If workshop class names differ from shipping Python APIs, preserve architecture using the documented fallback ladder. Do not invent APIs.

---

## 3. Clean Architecture Boundary

```text
Google ADK / Gemini
        ↓
infrastructure orchestration adapter
        ↓
application workflow / ports
        ↓
domain + deterministic policy
```

Forbidden:

```text
domain -> google.adk
application -> concrete Gemini/ADK SDK
ADK stage -> raw Firestore business mutation
ADK stage -> direct notification provider
Gemini -> action authorization
ADK stage -> duplicated scientific/domain calculation
```

---

## 4. Canonical Hero Runtime

```text
surveillance.signal.detected
          ↓
create/load incident
          ↓
FUNCTION: get_incident_context
          ↓
      FAN OUT
  ├─ FUNCTION: compare_resistance_profiles
  ├─ FUNCTION: get_baseline_summary
  └─ FUNCTION: get_missing_fields
          ↓
         JOIN
          ↓
AGENT: bounded investigation triage
          ↓
EvidenceSearchPort
          ↓
AGENT: evidence-grounded synthesis
          ↓
FUNCTION: package validation
   ├─ invalid → AGENT: bounded repair → validation
   └─ valid
          ↓
FUNCTION: autonomy/action policy
   ├─ A1 eligible → continue
   └─ blocked/insufficient → abstain
          ↓
FUNCTION: freshness revalidation
          ↓
FUNCTION: idempotency reservation
          ↓
APPLICATION/ADAPTER: real A1 external action
          ↓
EVENT/CALLBACK: machine acknowledgement
          ↓
FUNCTION: completion state transition
```

The hero path has **no clarification or human approval stage**.

---

## 5. Function / Deterministic Stages

Known mandatory work must not be agent-selected optional tools.

Deterministic stages include:

- context load;
- profile comparison;
- baseline summary;
- structural missingness;
- fixed state/event routing;
- package validation;
- action class A0/A1/A2/A3;
- allow-list/authorization checks;
- freshness/material-change check;
- idempotency;
- acknowledgement transition.

Gemini must not be called merely to execute fixed policy.

---

## 6. Gemini Agent Stages

Gemini may:

- reason across joined findings;
- select bounded approved-evidence intent when ambiguous;
- produce labelled hypotheses;
- synthesize structured evidence-backed package;
- repair package from structured validator errors;
- stop with uncertainty when evidence is insufficient.

Gemini may not:

- calculate surveillance facts that ordinary code owns;
- fabricate missing canonical data;
- decide final action class/authorization;
- send external action directly;
- diagnose/prescribe/confirm outbreak.

---

## 7. Hero Missing-Data Behavior

The hero fixture is complete enough for A1 completion.

Outside the hero:

```text
material missing data
→ NEEDS_INFORMATION
→ autonomous abstention
```

No required human-input primitive belongs in the hero runtime.

Human pause/resume may remain a secondary/future evaluation capability if needed, but must not weaken the Taskmaster proof.

---

## 8. Automatic Repair Loop

Package validation returns structured errors.

```text
invalid package
→ structured validation errors
→ Gemini repair
→ validator
```

Requirements:

- hard `max_package_repair_attempts` (target `2`);
- each attempt traceable;
- model cannot waive validator;
- exhausted budget → `VALIDATION_FAILED`;
- invalid package never reaches autonomy policy/action.

---

## 9. Tool / Capability Boundary

Application-facing capabilities may include:

```text
get_incident_context
compare_resistance_profiles
get_baseline_summary
get_missing_fields
search_approved_guidance
synthesize_incident_package / agent contract
validate_incident_package
classify_autonomous_action
revalidate_incident_before_action
```

Not every capability is an agent tool. Most mandatory deterministic capabilities are workflow/function stages.

No arbitrary shell, unrestricted DB, arbitrary URL evidence or direct notification tool.

---

## 10. External Action Boundary

The model/ADK agent does not own external side effects.

```text
application workflow
→ NotificationPort
→ authorized A1 infrastructure adapter
→ external target
```

Machine acknowledgement returns through a protected interface/event adapter into an application acknowledgement use case.

---

## 11. State / Execution Identity

Persist/correlate where useful:

```text
incident_id
event_id
correlation_id
graph_run_id
agent_session_id
agent_invocation_id
agent_run_id
attempt
package_version
source_watermark
action_class
autonomy_policy_result
idempotency_reference
delivery_id
acknowledgement_id
```

Firestore/application persistence remains canonical workflow truth.

ADK session/checkpoint is execution continuity only.

---

## 12. Resumability

Use stable supported ADK resume/session primitives where they help.

Recover from:

- process restart;
- model/evidence transient failure;
- Pub/Sub redelivery;
- external send/ack transient failure.

On recovery:

1. load canonical state;
2. rebuild current context;
3. restore execution refs if useful;
4. rerun safe/idempotent stages as required;
5. freshness before external action.

No checkpoint bypasses freshness/idempotency.

---

## 13. Context Compaction / Memory

May compact non-authoritative execution narration.

Canonical facts, deterministic outputs, source IDs, package/action versions, delivery/ack state remain in application persistence and are reconstructed.

Long-term model memory is not factual AMR authority for v0.1.

---

## 14. Callbacks

Callbacks/interceptors may support:

- telemetry;
- context preparation;
- execution budgets;
- redaction;
- invoking application freshness checks.

Callbacks do not own hidden business/action policy.

---

## 15. Model / Tool / Time Budgets

Configure explicit limits:

- model-call count;
- tool/capability count;
- repair attempts;
- retries;
- wall-clock timeout.

A failure to complete within budget should result in a visible bounded failure/abstention.

---

## 16. Evaluation

### Hero trajectory

Assert:

```text
0 user prompts
0 human interventions
0 clarifications
0 approvals
required deterministic stages executed
bounded Gemini stages executed
valid package
A1 policy accepted
freshness passed
idempotency reserved
1 external effect
1 machine acknowledgement
```

### Runtime/safety

Evaluate:

- required branch failure;
- branch-order independence;
- fixed router zero model call;
- prompt injection;
- fabricated source/isolate;
- no-evidence behavior;
- repair success/exhaustion;
- A2/A3 block;
- non-allow-listed target block;
- stale recompute;
- duplicate event/side-effect suppression;
- restart/recovery;
- session context conflict loses to canonical state.

---

## 17. Observability

Emit safe execution facts:

```text
INVESTIGATION_GRAPH_STARTED
FUNCTION_NODE_STARTED/COMPLETED
PARALLEL_FANOUT_STARTED
PARALLEL_BRANCH_COMPLETED
PARALLEL_JOIN_COMPLETED
AGENT_NODE_STARTED/COMPLETED
EVIDENCE_SEARCH_COMPLETED
PACKAGE_VALIDATION_FAILED/COMPLETED
PACKAGE_REPAIR_STARTED/COMPLETED
AUTONOMY_POLICY_EVALUATED
FRESHNESS_CHECK_STARTED/PASSED/FAILED
IDEMPOTENCY_RESERVED
NOTIFICATION_SENT
NOTIFICATION_ACKNOWLEDGED
WORKFLOW_COMPLETED/ABSTAINED
```

No private chain-of-thought.

---

## 18. Production Rules

- ADK Web local-only;
- production event entrypoints protected;
- external ack endpoint protected/authenticated as appropriate;
- secrets injected;
- Cloud Run min/max/cost controls;
- hosted/judged release stable;
- exact versions recorded.

---

## 19. Definition of Done

- [ ] capability spike passed;
- [ ] exact ADK version pinned;
- [ ] event starts workflow without chat;
- [ ] deterministic stages are mandatory and model-free;
- [ ] parallel/join semantics proven;
- [ ] hero has no human interaction;
- [ ] validation/repair bounded;
- [ ] A1 policy deterministic;
- [ ] A2/A3 blocked;
- [ ] freshness/idempotency mandatory;
- [ ] real external action outside model tool access;
- [ ] machine acknowledgement closes flow;
- [ ] resume/context/eval/observability behavior proven.
