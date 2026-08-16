# Ngabo — Long-Running Agent State, Freshness & Recovery Contract

**Status:** Required v0.1 runtime contract  
**Date:** 2026-08-16  
**Applies to:** `ngabo-core`, Google ADK runtime integration, incident workflow, review/action workflow, observability, and deployment

---

## 1. Purpose

Ngabo is designed to run asynchronously, pause for humans or external work, survive process restarts, and resume later without losing the meaning or safety of an AMR incident.

A workflow is not correct merely because it can resume. A resumed workflow must also:

- restore the right execution state;
- rebuild current authoritative context;
- avoid replaying unsafe side effects;
- detect whether information changed while it was waiting;
- require re-review when a previous approval no longer applies;
- avoid treating stale model/session memory as epidemiological truth.

This document is a companion to:

- `docs/ADK_RUNTIME.md`
- `docs/ORCHESTRATION_PATTERNS.md`
- `docs/SYSTEM_DESIGN.md`
- `docs/AGENT_ARCHITECTURE.md`

The governing rule is:

> **Resume execution, but revalidate truth.**

---

## 2. Long-Running State Model

Ngabo deliberately separates business truth from agent execution context.

```text
FIRESTORE — CANONICAL BUSINESS / WORKFLOW STATE
───────────────────────────────────────────────
incident
surveillance signal
canonical isolates / AST facts
clarifications + provenance
incident package versions
review decisions
notification state
acknowledgements
audit events
source-data/version watermarks

ADK SESSION / EXECUTION STATE
─────────────────────────────
current investigation execution
agent/node event continuity
resume/checkpoint identifiers
bounded working context needed by the current run

TRANSIENT / TEMP STATE
──────────────────────
small intermediate values
routing decisions
query fragments
recomputable branch outputs

ARTIFACTS / CLOUD STORAGE
─────────────────────────
large evidence snapshots
large intermediate JSON
exported reports
future PDF/image drafts
future genomic/bioinformatics artifacts

LONG-TERM MODEL/AGENT MEMORY
────────────────────────────
disabled by default for v0.1 factual incident reasoning
```

No outer-runtime state replaces the canonical application/domain record.

---

## 3. Canonical Truth Rule

The model must never be asked to remember canonical AMR facts from conversation history when Ngabo can load them from authoritative state.

Before reasoning or resuming, construct a fresh bounded context from:

1. canonical incident/source records;
2. current deterministic surveillance outputs;
3. current human clarifications;
4. current approved evidence retrieval results;
5. only then, relevant compacted execution context.

Correct:

```text
Firestore + deterministic outputs
          ↓
fresh incident context
          +
compacted ADK execution context
          ↓
Gemini
```

Incorrect:

```text
old conversation transcript
        ↓
Gemini guesses what the incident currently looks like
```

---

## 4. Pre-Action Freshness Barrier — Required

Human approval is scoped to a specific reviewed package and source-data state. It is not permanent authorization for whatever the incident becomes later.

Immediately before any consequential external action, Ngabo must execute a deterministic application-level freshness check.

Suggested use case:

```text
RevalidateIncidentBeforeAction
```

Suggested input:

```json
{
  "incident_id": "INC-001",
  "approved_package_version": 3,
  "approved_incident_version": 12,
  "approved_source_watermark": "...",
  "review_id": "REV-009"
}
```

The check should compare at least:

- current incident version;
- current package version;
- current source-data watermark/revision;
- whether new isolates or AST facts materially entered the incident scope;
- whether clarification or evidence changed after review;
- whether the review decision still refers to the current package;
- whether incident state still legally permits the action.

### Fresh case

```text
APPROVED
   ↓
pre-action freshness check
   ↓
UNCHANGED / VALID
   ↓
notification/action workflow
```

### Stale case

```text
APPROVED
   ↓
pre-action freshness check
   ↓
MATERIAL CHANGE DETECTED
   ↓
DO NOT ACT
   ↓
mark approval stale
   ↓
regenerate/revalidate package if needed
   ↓
WAITING_FOR_REVIEW
```

The stale transition must be explicit and auditable. Do not silently reinterpret an old approval as applying to a new package.

---

## 5. Freshness Watermarks

The exact implementation may evolve, but v0.1 should persist enough information to detect whether a reviewed package is still current.

Possible fields:

```text
incident.version
package.version
package.generated_at
package.source_watermark
review.reviewed_package_version
review.reviewed_incident_version
review.reviewed_source_watermark
review.created_at
last_source_change_at
last_material_change_at
```

A deterministic material-change policy should define which updates invalidate approval.

Examples likely to invalidate review:

- a new isolate joins the investigated cluster;
- an existing isolate's canonical AST data changes;
- a corrected specimen/ward field changes the investigation context;
- deterministic profile/baseline output changes materially;
- the incident package is regenerated to a new version;
- material human clarification changes.

Examples that normally should not invalidate review:

- telemetry-only updates;
- log delivery;
- non-semantic UI metadata;
- acknowledgement display formatting.

Do not let Gemini decide whether a version mismatch exists. Gemini may help contextualize a material change only after deterministic change detection.

---

## 6. ADK Callbacks / Interceptors

ADK lifecycle/tool/model callbacks may be used for cross-cutting runtime behavior where supported by the selected ADK version.

Suitable callback concerns include:

- safe telemetry enrichment;
- context preparation;
- invoking a deterministic freshness/revalidation use case before a consequential boundary;
- ensuring current data is loaded before an agent/tool step;
- enforcing execution budgets;
- redacting sensitive trace content.

Clean Architecture still applies:

```text
ADK callback / interceptor
        ↓
application use case / port
        ↓
domain policy / current data
```

Forbidden:

```text
ADK callback
  ├── hidden AMR business rules
  ├── direct Firestore mutation
  ├── direct notification bypass
  └── model-authored approval semantics
```

A callback is an orchestration hook, not a new policy layer.

---

## 7. Resumability

Where stable in the exact installed ADK version, configure resumability for the investigation workflow.

Ngabo should support at least these interruption classes:

```text
Cloud Run process restart
retryable model failure
retryable tool failure
human clarification wait
external long-running wait if introduced
Pub/Sub redelivery
```

Resume sequence:

1. load the canonical incident;
2. verify the incident is still resumable;
3. restore/recover ADK execution state where available;
4. rebuild authoritative current context;
5. re-run only safe/idempotent steps as required;
6. append a resume/retry audit event;
7. continue toward clarification/package/review;
8. execute the freshness barrier again before any consequential action.

A successful checkpoint restoration does not waive freshness checks.

---

## 8. Long-Running Function Tools

If the exact ADK version provides a stable long-running function/tool primitive, Ngabo may use it only for work that genuinely spans an external wait boundary.

Potential future examples:

- waiting for an external acknowledgement;
- waiting for a scheduled follow-up condition;
- waiting for an external analysis job;
- a future approved bioinformatics job.

Do not wrap ordinary synchronous work in a long-running tool merely to appear agentic.

The long-running tool should represent/coordinate the external operation, not keep a Cloud Run request alive while sleeping for minutes.

For human clarification, prefer the most appropriate stable ADK human-input/resume primitive. Do not force clarification into a long-running function if the framework's human-input workflow is cleaner.

Implementation must be verified against the exact installed ADK API; do not copy workshop API names blindly.

---

## 9. Context Compaction

Long-running agent sessions can accumulate unnecessary context. Where supported and stable, Ngabo should use ADK context compaction or equivalent bounded-context strategies.

### Context that may be compacted

- prior conversational narration;
- repetitive tool-event descriptions;
- old non-authoritative agent explanations;
- historical routing narration;
- earlier working summaries that can be reconstructed.

### Facts that must never rely on compaction as their authoritative representation

- isolate IDs and canonical isolate fields;
- AST results;
- detector outputs;
- deterministic similarity/baseline values;
- human clarifications;
- review decisions;
- evidence source IDs/citations;
- package versions;
- notification decisions;
- audit history.

Compaction may improve LLM context efficiency. It may not redefine the source of truth.

### Context reconstruction rule

After a long wait or resume, prefer rebuilding a compact current incident summary from canonical state over replaying an unbounded old conversation.

---

## 10. Long-Term Memory Policy

Ngabo v0.1 must not use unreviewed long-term model/agent memory as factual input to AMR incident reasoning.

Do not implement behavior such as:

```text
"A previous incident looked similar, so I remember this is probably an outbreak."
```

If future cross-incident memory is introduced, it requires a separate architecture/safety decision defining:

- what may be remembered;
- provenance;
- retention;
- facility/user boundaries;
- retrieval controls;
- deletion/correction;
- whether the memory is advisory or authoritative;
- evaluation for contamination and stale knowledge.

Until then, historical comparisons must come from explicit approved datasets/queries, not hidden agent memory.

---

## 11. Artifact Policy

Use artifacts/Cloud Storage for large or file-like intermediate outputs instead of bloating model/session state.

Examples:

- raw immutable import files;
- evidence snapshots where appropriate;
- generated reports;
- large structured intermediate outputs;
- future multimodal extraction drafts;
- future genomic analysis outputs.

Artifacts require:

- stable IDs/URIs;
- incident/run association;
- version/provenance where relevant;
- appropriate retention;
- no patient data in public v0.1;
- no assumption that an artifact is canonical merely because it exists.

Canonical structured facts still live through the application persistence model.

---

## 12. Scheduled Follow-Up — Optional Post-Core Enhancement

Cloud Scheduler may be added after the core deployed flow is green to emit bounded follow-up events through Pub/Sub.

Possible events:

```text
incident.followup.tick
incident.acknowledgement.check
incident.stale_review.check
```

Example:

```text
Cloud Scheduler
      ↓
Pub/Sub
      ↓
ngabo-core event interface
      ↓
application follow-up use case
      ↓
deterministic state check
      ↓
optional bounded agent reasoning only if needed
```

Rules:

- Scheduler does not become a second workflow engine;
- event handlers remain thin adapters;
- follow-up events are idempotent;
- no periodic Gemini call when ordinary state checks can decide there is nothing to do;
- explicit max frequency/cost limits;
- optional for v0.1, not a dependency of the core submission.

---

## 13. A2A Policy

Do **not** add Agent-to-Agent (A2A) distributed-agent infrastructure for v0.1.

Ngabo's v0.1 graph/functions/agent capabilities run inside the same `ngabo-core` deployable. A distributed agent protocol would add deployment, authentication, networking, observability, and failure complexity without solving a current product need.

A2A may be reconsidered only if a future specialist capability:

- is separately deployed;
- has an independent ownership/security boundary;
- requires standardized remote-agent interoperability;
- and provides measurable value that justifies distributed-systems complexity.

Same-runtime specialist capabilities do not require A2A merely because they are called agents.

---

## 14. ADK Web Security Rule

ADK Web / developer debugging UI is **local-development only** for Ngabo v0.1.

Allowed:

- local agent inspection;
- development traces;
- prompt/tool debugging;
- developer-only evaluation work.

Forbidden:

- public production exposure;
- judge-facing operational UI;
- production authentication shortcut;
- linking it as the product interface.

The judge-facing product is Ngabo's own incident-response console.

Deployment/CI should not publish an unauthenticated ADK developer UI.

---

## 15. Observability for Long-Running Work

Record public-safe workflow facts such as:

```text
AGENT_RUN_STARTED
AGENT_RUN_PAUSED
AGENT_RUN_RESUMED
CONTEXT_REBUILT
CONTEXT_COMPACTED
FRESHNESS_CHECK_STARTED
FRESHNESS_CHECK_PASSED
FRESHNESS_CHECK_FAILED
APPROVAL_MARKED_STALE
PACKAGE_REVIEW_REQUIRED
LONG_RUNNING_OPERATION_STARTED
LONG_RUNNING_OPERATION_RESUMED
SCHEDULED_FOLLOWUP_RECEIVED
```

Useful fields:

```text
incident_id
incident_version
package_version
review_id
reviewed_package_version
source_watermark
current_source_watermark
agent_session_id
agent_invocation_id
graph_run_id
resume_attempt
freshness_result
material_change_reason
```

Do not emit hidden chain-of-thought.

---

## 16. UI Requirements

The console must make stale/review state understandable.

If an approval becomes stale, show a clear operational message such as:

> **New incident data arrived after this package was reviewed. The previous approval no longer authorizes notification. Review the updated package before action.**

The UI should display where relevant:

- reviewed package version;
- current package version;
- last material data change;
- resume/recovery event;
- stale-approval state;
- reason for re-review;
- no false claim that a notification occurred when it was blocked by freshness validation.

Do not ask the reviewer to infer staleness from timestamps alone.

---

## 17. Required Tests / Evaluations

### Freshness

- approval + no material change → action permitted;
- approval + new material isolate → action blocked;
- approval + changed AST fact → action blocked;
- approval + new package version → action blocked;
- telemetry-only change → approval remains valid;
- stale approval cannot be replayed after retry/redelivery.

### Resume

- process restart resumes or safely restarts investigation;
- human clarification wait resumes the same incident;
- resumed execution rebuilds current canonical context;
- repeated read-only work is safe;
- side effects remain idempotent.

### Context / memory

- compacted agent context cannot replace canonical incident facts;
- old session text conflicting with current Firestore state loses to Firestore;
- long-term model memory is not queried for v0.1 incident facts;
- artifact contents are not treated as canonical without the appropriate application mapping.

### Security

- ADK Web is not exposed by production deployment configuration;
- no A2A service/port is deployed in v0.1;
- callbacks cannot bypass application review/action gates.

### Scheduled follow-up, if implemented

- duplicate scheduler/PubSub events are harmless;
- no model call occurs when deterministic follow-up says no work is needed;
- frequency/cost bounds are enforced.

---

## 18. Demo Opportunity

The hackathon demo should visibly prove at least one long-running property without making the video long.

A compact demonstration can:

1. trigger an investigation;
2. pause for a required human clarification;
3. show that the backend/agent execution can resume the same incident;
4. continue from persisted state rather than restarting the whole story;
5. show the human review/action gate;
6. optionally mention/show the freshness check immediately before action.

A controlled restart can be demonstrated in engineering evidence/evaluation even if it is not shown live in the four-minute product demo.

---

## 19. Definition of Done

Long-running-agent hardening is complete for v0.1 when:

- [ ] Firestore remains canonical business/workflow truth;
- [ ] ADK session/execution state is explicitly non-authoritative;
- [ ] current context is rebuilt after resume;
- [ ] context growth is bounded/compacted where supported;
- [ ] canonical facts never depend on compaction summaries;
- [ ] final external action is protected by a deterministic freshness barrier;
- [ ] stale approvals are invalidated and visibly returned to review;
- [ ] resume/retry is safe and idempotent;
- [ ] long-running ADK primitives are used only where they solve an actual wait boundary;
- [ ] ADK Web is local-only;
- [ ] A2A is absent from v0.1 unless a new ADR explicitly reverses this decision;
- [ ] scheduled follow-up remains optional and deterministic-first;
- [ ] tests cover staleness, resume, context truth, and side-effect replay;
- [ ] observability proves pause/resume/freshness behavior without chain-of-thought.

---

## 20. Source Workshop

This contract incorporates lessons from the official All Things Agentic resource webinar **“Build a Long-Running Agent — Persistent Workflows with Google ADK”** while adapting them to Ngabo's Clean Architecture, AMR safety boundaries, and current v0.1 scope.

Implementation must use the exact stable APIs available in the installed Google ADK version rather than assuming workshop sample APIs remain unchanged.
