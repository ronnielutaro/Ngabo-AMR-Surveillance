# Ngabo — UI/UX Hackathon Addendum

**Status:** Required extension to `docs/UI_UX_SPEC.md` for v0.1  
**Version:** 0.2  
**Date:** 2026-08-16

---

## 1. Demo Principle

The UI must make autonomous execution **undeniable** within the four-minute demo.

A judge should visually understand:

```text
AMR data arrives
  ↓
deterministic signal appears
  ↓
Pub/Sub triggers ADK graph automatically
  ↓
deterministic function nodes fan out
  ↓
parallel branches complete + join
  ↓
Gemini reasons where ambiguity exists
  ↓
approved evidence arrives
  ↓
clarification pause only if needed
  ↓
same incident resumes
  ↓
package is deterministically validated
  ↓
human reviews consequential action
  ↓
freshness check protects the approval
  ↓
real external action
  ↓
acknowledgement
```

No chat prompt should be needed to begin the investigation.

---

## 2. Investigation Timeline — Canonical Event Vocabulary

The primary timeline should use graph/runtime facts, not the older generic “agent tool” vocabulary where a more specific event exists.

Supported public-safe events include:

```text
SIGNAL_DETECTED
INVESTIGATION_GRAPH_STARTED
FUNCTION_NODE_STARTED
FUNCTION_NODE_COMPLETED
PARALLEL_FANOUT_STARTED
PARALLEL_BRANCH_COMPLETED
PARALLEL_JOIN_COMPLETED
AGENT_NODE_STARTED
EVIDENCE_SEARCH_COMPLETED
CLARIFICATION_REQUESTED
AGENT_RUN_PAUSED
CLARIFICATION_RECEIVED
AGENT_RUN_RESUMED
CONTEXT_REBUILT
PACKAGE_VALIDATION_COMPLETED
PACKAGE_READY_FOR_REVIEW
REVIEW_APPROVED
REVIEW_REJECTED
FRESHNESS_CHECK_STARTED
FRESHNESS_CHECK_PASSED
FRESHNESS_CHECK_FAILED
APPROVAL_MARKED_STALE
NOTIFICATION_SENT
NOTIFICATION_ACKNOWLEDGED
```

Tool-level details may still appear inside a developer/details view where useful, but the product narrative should expose the graph structure: deterministic nodes, fan-out, join, bounded agent reasoning, pause/resume and action.

Do not expose private chain-of-thought.

---

## 3. Fan-Out / Join Visualization

The incident timeline should make parallel deterministic work legible without becoming a developer-only graph editor.

Suggested presentation:

```text
Investigation context loaded

Parallel investigation
  ✓ Resistance profile comparison    420 ms
  ✓ Baseline summary                 610 ms
  ✓ Missing-field assessment         180 ms

Joined investigation context
Gemini triage started
```

Requirements:

- branch completion order must not imply semantic priority;
- required branch failures must be visibly different from optional unavailable work;
- a failed required branch must not be visually followed by a false “successful synthesis” state;
- do not present deterministic nodes as if Gemini performed the calculations.

---

## 4. Agent Reasoning Visibility Without Chain-of-Thought

The UI may show bounded stage labels such as:

- `Assessing whether missing context is material`;
- `Selecting approved evidence topic`;
- `Synthesizing source-grounded incident package`;
- `Insufficient evidence — stopping with uncertainty`.

Do not show hidden reasoning traces or fabricate explanations of private model thought.

Show **what capability ran and what observable result it produced**, not chain-of-thought.

---

## 5. Resume / Recovery UI

If an investigation is interrupted or retried, show a bounded operational state such as:

```text
Investigation interrupted
Recovery / retry in progress
```

After recovery:

```text
Investigation resumed
Current incident context rebuilt from canonical state
```

Where useful, developer/details views may show:

- graph run ID;
- agent run/session/invocation ID;
- attempt number;
- correlation ID;
- resume reason.

The UI must never silently reset the timeline and pretend the interruption did not occur.

---

## 6. Long-Running Context / Truth UI

The product should not expose ADK session memory as if it were incident truth.

When a long-running workflow resumes, the UI may communicate:

> **Investigation resumed using current incident data.**

If current canonical data changed materially during the wait, reflect the updated incident/package state rather than replaying stale text from the previous session.

---

## 7. Freshness Barrier / Stale Approval UI

This is a required v0.1 operational state.

After human approval but before consequential external action, Ngabo performs deterministic freshness validation.

### Fresh approval

```text
Review approved
Freshness check passed
Authorized action sent
```

### Stale approval

If relevant source/incident/package data changed after review, show a clear blocking state:

> **New incident data arrived after this package was reviewed. The previous approval no longer authorizes notification. Review the updated package before action.**

Display where useful:

- reviewed package version;
- current package version;
- reviewed/current incident version;
- last material data change;
- reason approval became stale;
- re-review required state.

Do not ask the reviewer to infer staleness from timestamps alone.

Do not display `NOTIFICATION_SENT` when the freshness barrier blocked the action.

---

## 8. Evidence Retrieval Provenance

Evidence-source details should show:

- source ID;
- publisher/title;
- official URL;
- version/date where available;
- retrieval method;
- excerpt/chunk provenance where appropriate.

If EmbeddingGemma is integrated, label the method truthfully, e.g.:

```text
Retrieval: EmbeddingGemma semantic retrieval
```

A retrieval similarity score must never be labelled medical confidence.

If deterministic/tag retrieval is active, label it accurately. Do not imply EmbeddingGemma is running when it is not.

---

## 9. Human Safety Boundary Must Look Like Governance, Not Manual Orchestration

The UI should make clear that the human is not driving every investigation step.

Before review, Ngabo should already have completed the autonomous investigation package.

The review panel should focus on:

- observed/derived evidence;
- hypotheses and uncertainty;
- missing information;
- approved-source guidance;
- draft escalation/action;
- limitations;
- approve / reject / request more information.

Avoid UI patterns that make the user choose the next graph node/tool manually during the normal Taskmaster path.

---

## 10. Real External Action

The hosted/demo flow should use a real authorized action adapter after approval **and freshness validation**.

Response Tracking must identify channel truthfully, for example:

```text
Channel        Authorized test webhook
Mode           Real integration
Freshness      Passed
Status         Sent
Delivery ID    ...
Sent at        ...
Acknowledged   ...
```

For automated/local tests:

```text
Channel        Demo notification adapter
Mode           Simulation
```

Never imply a real hospital/person was contacted unless explicitly authorized and true.

---

## 11. Observability / Technical Proof View

A compact developer/details drawer or demo-only technical panel may expose safe execution metadata:

- incident ID;
- correlation/event ID;
- graph run ID;
- node/branch/join IDs;
- agent run/session/invocation ID;
- current model name;
- retry/resume count;
- package/incident version;
- freshness result;
- latest delivery ID/status.

This view supplements the operational UI; it should not dominate it.

The demo may pair this panel with a brief Cloud Run/Cloud Logging/Trace view to prove Google Cloud execution.

---

## 12. Operational Utility Proof

The application does not need a full analytics product for v0.1.

A compact Technical/About/Evaluation section may show measured benchmark facts from `EVALUATION.md`, such as:

- zero prompts required to start canonical investigation;
- human intervention count;
- signal-to-review-ready timing;
- deterministic/model call counts;
- number of committed synthetic scenarios;
- last evaluated commit/deployment.

Never display estimated or unmeasured productivity percentages.

See `docs/OPERATIONAL_UTILITY_EVALUATION.md`.

---

## 13. Evaluation Proof

A compact section may link to public `EVALUATION.md` and summarize only generated facts, including:

- detector/scenario benchmark results;
- safety/adversarial tests;
- graph trajectory tests;
- resume/idempotency tests;
- freshness-barrier tests;
- retrieval evaluation if EmbeddingGemma is active;
- hosted E2E run status.

Never show evaluation metrics that have not actually been produced.

---

## 14. Multimodal Stretch UI

Only if implemented after core freeze, the import screen may offer:

```text
Upload CSV
or
Extract draft from image/PDF
```

Required flow:

```text
AI-EXTRACTED DRAFT
       ↓
Human verify/edit
       ↓
Confirm canonical record
       ↓
Deterministic ingestion
```

Use a prominent badge such as:

`UNVERIFIED AI EXTRACTION`

until verification occurs.

The detector must not consume unverified extraction output.

---

## 15. Four-Minute Demo UX Budget

Target visible sequence:

1. import/trigger synthetic scenario;
2. dashboard signal appears;
3. incident opens / graph starts automatically;
4. timeline shows deterministic fan-out + branch completion + join;
5. Gemini/evidence stage appears;
6. clarification card appears;
7. answer once and show resume;
8. validated package becomes ready;
9. approve;
10. freshness check passes;
11. real external action appears;
12. acknowledgement closes loop;
13. quick technical/GCP/evaluation proof.

Avoid decorative transitions or extra screens that consume demo time.

---

## 16. Submission-Proof Rules

Before demo freeze, cross-check `docs/SUBMISSION_EVIDENCE.md`.

The UI/video must not imply that any of these are active unless actually implemented:

- EmbeddingGemma;
- MedGemma;
- multimodal extraction;
- real hospital integration;
- clinical validation;
- production deployment beyond the actual hackathon environment.

---

## 17. Acceptance Criteria

- [ ] autonomous event-triggered start is visible;
- [ ] deterministic function nodes are distinguishable from agent/model work;
- [ ] fan-out/join is visible where useful;
- [ ] bounded agent stages are visible without chain-of-thought;
- [ ] pause/resume/recovery is visible;
- [ ] failures/retries cannot masquerade as success;
- [ ] evidence provenance is visible;
- [ ] human review looks like a consequential safety gate rather than step-by-step orchestration;
- [ ] freshness check is represented before real action;
- [ ] stale approval produces a clear re-review state;
- [ ] real vs demo notification channels are distinguishable;
- [ ] real action + acknowledgement are visible in hosted/demo path;
- [ ] operational/evaluation proof uses measured results only;
- [ ] optional model/multimodal features are labelled only if actually integrated;
- [ ] the complete product story remains understandable in <4 minutes.
