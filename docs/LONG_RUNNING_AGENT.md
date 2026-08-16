# Ngabo — Long-Running Agent State, Freshness & Recovery Contract

**Status:** Required v0.1 runtime contract  
**Version:** 0.2  
**Date:** 2026-08-16

---

## 1. Principle

> **Resume execution, but revalidate truth.**

Ngabo may run asynchronously, survive retries/restarts, and continue work later. A resumed workflow must restore execution safely **and rebuild current canonical context before reasoning or external action**.

For the canonical Taskmaster hero, no human wait is required. Long-running/recovery mechanisms still matter for process failures, Pub/Sub redelivery, external retries and secondary evaluation scenarios.

`docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md` is the source of truth for the zero-human A1 hero action lane.

---

## 2. State Model

```text
FIRESTORE / APPLICATION PERSISTENCE
= canonical incident/workflow truth
  isolates / AST facts
  surveillance signal
  package versions
  action policy result
  freshness watermarks
  delivery / acknowledgement state
  audit events

ADK SESSION / EXECUTION STATE
= execution continuity only
  run/session/invocation identifiers
  node/checkpoint references where supported
  bounded working context

TRANSIENT STATE
= recomputable intermediate values

CLOUD STORAGE ARTIFACTS
= raw files, large evidence/report/intermediate artifacts

LONG-TERM MODEL MEMORY
= not authoritative factual input for v0.1
```

No ADK/session/model state replaces the canonical application record.

---

## 3. Context Reconstruction

Before model reasoning after a retry/restart/long wait:

1. load current incident/source state;
2. load current deterministic findings or recompute them where required;
3. load current approved evidence;
4. load current action/policy state;
5. only then add bounded relevant execution context.

Correct:

```text
canonical state + deterministic outputs + approved evidence
                  ↓
          fresh bounded context
                  ↓
                Gemini
```

Incorrect:

```text
old conversation/session text
→ model guesses current AMR truth
```

---

## 4. Freshness Barrier — Required Before Every External A1 Action

Freshness is no longer tied only to a human approval workflow.

Immediately before any autonomous A1 external action, deterministic application logic must verify that the package/action is still based on current canonical state.

Suggested use case:

```text
RevalidateIncidentBeforeAction
```

Compare at least:

- current incident version;
- current package version;
- source-data watermark;
- material isolate/AST changes;
- material context changes;
- evidence version where relevant;
- current action-policy classification;
- current incident state eligibility.

### Fresh

```text
A1 policy eligible
→ freshness passes
→ idempotency
→ external action
```

### Stale

```text
material source change
→ DO NOT ACT
→ recompute/re-run affected investigation stages
→ regenerate/revalidate package
→ re-run autonomy policy
→ freshness again
```

No stale package may act merely because an earlier run reached the action stage.

---

## 5. Human-Governed Lanes

Future/secondary A2 workflows may still contain human review. If such a workflow is implemented, the review must remain version-scoped and freshness must still run before action.

This does not change the v0.1 hero requirement:

```text
A1 hero → zero human intervention
```

---

## 6. Pub/Sub / Retry / Idempotency

Pub/Sub is at-least-once transport, not workflow truth.

Requirements:

- duplicate event → same logical incident/effect;
- read-only stages safe to repeat;
- state mutations use optimistic/version checks where appropriate;
- external action uses idempotency key/reservation;
- delivery result persisted;
- acknowledgement replay idempotent;
- retry cannot reuse stale action authorization.

---

## 7. External Operation State

Persist enough to recover:

```text
incident_id
event_id
graph_run_id
agent_session_id
agent_invocation_id
agent_run_id
attempt
current_stage/checkpoint where useful
completed deterministic stage refs
package_version
source_watermark
action_class
action_policy_result
idempotency_key/reference
delivery_id
delivery_status
acknowledgement_id
last_error
updated_at
```

Exact ADK fields depend on the pinned supported version.

---

## 8. Resumability

Where stable in the selected ADK version, use supported resumability/session mechanisms.

Required interruption classes:

- Cloud Run/process restart;
- retryable Gemini failure;
- retryable evidence/tool failure;
- Pub/Sub redelivery;
- external action retry;
- machine-ack timeout;
- optional secondary human-input wait if implemented outside hero.

Resume sequence:

```text
load canonical incident
→ determine legal resumable state
→ restore ADK execution metadata if useful
→ rebuild current context
→ re-run only safe/necessary stages
→ append recovery audit event
→ freshness before any external action
```

Successful checkpoint restoration never waives freshness/idempotency.

---

## 9. Long-Running Function Tools

Use a long-running ADK primitive only when it represents a genuine external asynchronous operation.

Potential future/secondary uses:

- external bioinformatics job;
- scheduled follow-up condition;
- external analysis job.

Do not hold a Cloud Run request open sleeping for minutes.

The hero's external action/ack path should normally use persisted application/integration state and callbacks/events rather than an in-process wait.

---

## 10. Context Compaction

May compact:

- old conversational narration;
- repetitive tool-event text;
- non-authoritative agent explanations;
- reconstructable working summaries.

Never rely on compacted text as authoritative representation of:

- isolate/AST facts;
- signal calculations;
- evidence source IDs;
- package/action versions;
- action class/policy;
- freshness state;
- delivery/ack state;
- audit history.

---

## 11. Long-Term Memory Policy

Unreviewed cross-incident model memory is disabled as factual input to v0.1 incident reasoning.

Historical comparisons must come from explicit approved queries/datasets.

Future memory requires separate governance for provenance, retention, tenancy, correction/deletion and evaluation.

---

## 12. Callbacks / Interceptors

ADK callbacks may support:

- telemetry;
- context preparation;
- execution budgets;
- redaction;
- invoking application-level freshness checks.

They must not become hidden business-policy layers.

```text
ADK callback
→ application use case/port
→ domain/application policy
```

Forbidden:

- direct Firestore business mutation;
- hidden action-class policy;
- direct notification bypass;
- model-authored authorization semantics.

---

## 13. Machine Acknowledgement

Hero completion must not wait for a person.

Preferred:

```text
external A1 endpoint
→ acknowledgement callback/event
→ idempotent Ngabo handler
→ persisted completion state
```

If callback is delayed/fails:

- bounded retry/poll strategy if appropriate;
- no repeated external send without idempotent provider semantics;
- visible timeout/failure state.

---

## 14. Scheduled Follow-Up

Optional post-core Cloud Scheduler → Pub/Sub may emit bounded follow-up events.

Rules:

- Scheduler is not workflow truth;
- state checks deterministic-first;
- no periodic Gemini call if ordinary code can decide nothing is required;
- explicit cost/frequency bounds.

---

## 15. A2A / ADK Web

### A2A

No distributed A2A architecture for core v0.1 unless a separately deployed specialist creates a real need.

### ADK Web

Local development/debugging only. Never judge-facing/public production UI.

---

## 16. Observability

Useful events:

```text
AGENT_RUN_STARTED
AGENT_RUN_RESUMED
CONTEXT_REBUILT
CONTEXT_COMPACTED
FRESHNESS_CHECK_STARTED
FRESHNESS_CHECK_PASSED
FRESHNESS_CHECK_FAILED
STALE_RECOMPUTE_STARTED
AUTONOMY_POLICY_EVALUATED
IDEMPOTENCY_RESERVED
NOTIFICATION_SENT
NOTIFICATION_ACKNOWLEDGED
ACTION_RETRY_SCHEDULED
```

No private chain-of-thought.

---

## 17. Required Tests

### Freshness

- unchanged source → action allowed;
- material new isolate/AST/context → recompute before action;
- telemetry-only change → no unnecessary recompute;
- stale session cannot authorize action.

### Resume

- process restart safely continues/restarts;
- current canonical context is rebuilt;
- repeated read-only work safe;
- external effect not duplicated.

### Action / Ack

- duplicate action request → one external effect;
- retry uses same idempotency semantics;
- acknowledgement replay harmless;
- action policy rechecked after material source change.

### Context

- old session conflicting with Firestore loses to Firestore;
- compaction summary cannot alter canonical facts;
- long-term model memory not queried for v0.1 facts.

---

## 18. Definition of Done

- [ ] Firestore/application state remains canonical truth;
- [ ] ADK state is explicitly non-authoritative;
- [ ] current context rebuilt after recovery;
- [ ] context bounded/compacted where useful;
- [ ] freshness runs before every A1 external action;
- [ ] material changes force recomputation/revalidation;
- [ ] idempotency protects external side effects;
- [ ] machine acknowledgement path is recoverable/idempotent;
- [ ] ADK Web not production-exposed;
- [ ] A2A absent unless justified;
- [ ] tests prove resume/freshness/context/action safety;
- [ ] hero can remain zero-human while long-running correctness is preserved.
