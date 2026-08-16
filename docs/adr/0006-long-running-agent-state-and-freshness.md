# ADR 0006 — Long-Running Agent State, Freshness, and Memory Boundaries

**Status:** Accepted  
**Date:** 2026-08-16

## Context

Ngabo is an asynchronous AMR surveillance and incident-response system. Investigations may pause for human clarification, survive process restarts, resume after delays, and wait for review before taking a consequential external action.

The official All Things Agentic webinar **“Build a Long-Running Agent — Persistent Workflows with Google ADK”** highlights several production concerns that materially affect Ngabo:

- long-running agents need durable session/execution state;
- context can degrade as sessions grow and therefore needs compaction/bounded context;
- external waits and process restarts require resumability;
- information may become stale while an agent is waiting;
- callbacks/interceptors can refresh or validate context before a model/tool/action boundary;
- artifacts are distinct from working/session memory;
- distributed A2A communication is unnecessary when capabilities share one runtime;
- developer agent UIs should not be exposed publicly in production.

Ngabo already uses Firestore as canonical workflow state and Google ADK as an outer runtime. We need an explicit rule for how long-running execution state, model context, memory, and post-wait freshness interact with the clinical/public-health safety boundary.

## Decision

Ngabo adopts the long-running-agent contract in `docs/LONG_RUNNING_AGENT.md`.

The central rule is:

> **Resume execution, but revalidate truth.**

### 1. Canonical state

Firestore/application persistence remains authoritative for incidents, isolates, AST facts, deterministic surveillance outputs, clarifications, package versions, reviews, notifications, acknowledgements, and audit history.

ADK session/checkpoint state exists only to support execution continuity.

### 2. Freshness barrier before action

Every consequential outbound action must pass a deterministic pre-action freshness check tied to the exact incident/package/source-data state that was reviewed.

If material data or package state changed after review, the old approval becomes stale and no action is executed until the updated package is reviewed again.

### 3. Context compaction

ADK context compaction/bounded history may be used to control token cost and context degradation, but compacted summaries never become authoritative representations of canonical AMR facts.

Fresh authoritative context is reconstructed from persisted application state after resume or long waits.

### 4. Long-term model memory

Unreviewed long-term model/agent memory is disabled as a factual input to v0.1 incident reasoning. Cross-incident memory requires a future ADR covering provenance, retention, facility/user boundaries, correction/deletion, contamination risk, and evaluation.

### 5. Artifacts

Large/file-like intermediate outputs belong in artifacts/Cloud Storage with explicit provenance/versioning. Artifact existence does not make content canonical.

### 6. ADK long-running primitives

Use stable ADK resumability, human-input, callbacks/interceptors, and long-running-function primitives only where they solve a real execution/wait boundary. Implementation must target the exact installed ADK API rather than blindly copying workshop code.

### 7. A2A

Do not introduce distributed Agent-to-Agent infrastructure in v0.1. Same-runtime graph/function/agent capabilities remain inside `ngabo-core`. A2A requires a future ADR and an actual distributed-agent need.

### 8. ADK Web

ADK Web/debug UI is local-development only and must not be exposed as the public/judge-facing production UI.

### 9. Scheduled follow-up

Cloud Scheduler → Pub/Sub may be added after the core E2E path is stable for bounded follow-up/acknowledgement/stale-review checks. It remains optional and deterministic-first.

## Consequences

### Positive

- stale human approvals cannot trigger action after material incident changes;
- resumability does not create hidden reliance on old model context;
- long-running sessions remain more cost- and context-efficient;
- canonical AMR facts stay source-traceable and testable;
- agent-memory contamination across incidents is prevented in v0.1;
- unnecessary A2A/distributed-systems complexity is avoided;
- production exposure of development agent internals is explicitly prohibited;
- the Taskmaster story becomes more credible because background workflows can pause, resume, revalidate, and continue safely.

### Trade-offs

- additional version/watermark metadata and tests are required;
- stale approval handling can send an incident back to review;
- context must be reconstructed deliberately rather than relying on conversation history;
- some ADK convenience features are intentionally constrained by application/domain policy;
- scheduled follow-up is deferred until the core system is stable.

## Rejected Alternatives

### Treat an approval as valid indefinitely

Rejected because the incident or source data may materially change during a long wait.

### Use ADK/model memory as the incident source of truth

Rejected because session/memory state is not an authoritative clinical/public-health record and may be stale, compacted, or model-generated.

### Add A2A to make the architecture look more agentic

Rejected because v0.1 capabilities share one runtime and do not justify distributed-agent complexity.

### Keep ADK Web exposed for judges

Rejected because it is a development/debugging surface rather than Ngabo's product UI and exposes unnecessary runtime details.

### Poll with Gemini on a schedule

Rejected as the default. Scheduled work should first use deterministic state checks and invoke model reasoning only when there is an actual ambiguous task.

## Implementation Notes

At minimum, implementation should introduce or represent:

```text
incident_version
package_version
reviewed_package_version
reviewed_incident_version
source_watermark
reviewed_source_watermark
last_material_change_at
```

and a deterministic application use case such as:

```text
RevalidateIncidentBeforeAction
```

The review/action workflow must fail closed when the reviewed version cannot be proven current.

## References

- `docs/LONG_RUNNING_AGENT.md`
- `docs/ADK_RUNTIME.md`
- `docs/ORCHESTRATION_PATTERNS.md`
- `docs/SYSTEM_DESIGN.md`
- `docs/AGENT_ARCHITECTURE.md`
- Official All Things Agentic resource webinar: “Build a Long-Running Agent — Persistent Workflows with Google ADK”
