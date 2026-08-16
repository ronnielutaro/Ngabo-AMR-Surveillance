# Ngabo — UI/UX Hackathon Addendum

**Status:** Required extension to `docs/UI_UX_SPEC.md` for v0.1  
**Date:** 2026-08-16

This document adds hackathon-specific UI requirements without replacing the core UI/UX specification.

## 1. Demo Principle

The UI must make autonomous execution **undeniable** within the four-minute demo.

A judge should visually see:

```text
AMR data arrives
  ↓
deterministic signal
  ↓
agent starts automatically
  ↓
tools execute
  ↓
evidence arrives
  ↓
clarification pause
  ↓
resume
  ↓
package ready
  ↓
human approves
  ↓
real external action
  ↓
acknowledgement
```

No chat prompt should be needed to begin the investigation.

## 2. Investigation Timeline Additions

The timeline must support these public-safe events when they occur:

- `AGENT_INVESTIGATION_STARTED`
- `AGENT_TOOL_STARTED`
- `AGENT_TOOL_COMPLETED`
- `EVIDENCE_RETRIEVED`
- `AGENT_INTERRUPTED` / retryable failure where relevant
- `AGENT_INVESTIGATION_RESUMED`
- `CLARIFICATION_REQUESTED`
- `CLARIFICATION_RECEIVED`
- `INCIDENT_PACKAGE_VALIDATED`
- `REVIEW_APPROVED`
- `NOTIFICATION_SENT`
- `NOTIFICATION_ACKNOWLEDGED`

Do not display private chain-of-thought. Show observable workflow facts only.

## 3. Resume / Recovery UI

If an investigation is interrupted or retried, show a bounded status such as:

```text
Investigation interrupted
Retry scheduled / Resume in progress
```

After recovery:

```text
Investigation resumed
Previous completed steps preserved where supported
```

The UI must never silently reset the timeline and pretend the interruption did not occur.

Developer/details views may show safe identifiers such as:

- agent run ID;
- invocation ID;
- attempt number;
- correlation ID.

Do not expose secrets, prompts, or hidden model reasoning.

## 4. Evidence Retrieval Provenance

If EmbeddingGemma is integrated, evidence-source details may show:

- retrieval method: `EmbeddingGemma semantic retrieval`;
- source ID;
- publisher/title;
- official URL;
- retrieval score/rank where helpful.

A retrieval score must never be labelled medical confidence.

If a deterministic/tag fallback is used, label it accurately. Do not imply EmbeddingGemma is active when it is not.

## 5. Real External Action

The v0.1 hosted/demo flow should use a real authorized action adapter after approval.

Response Tracking must identify the channel truthfully, for example:

```text
Channel        Authorized test webhook
Mode           Real integration
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

The interface must make the difference obvious.

Never imply a real hospital/person was contacted unless that is actually authorized and true.

## 6. Observability / Technical Proof View

A small developer/details drawer or demo-only technical panel may expose safe execution metadata:

- incident ID;
- correlation ID;
- event ID;
- agent run/invocation ID;
- current model name;
- latest tool;
- retry count;
- package version.

This is supplemental to the human-facing UI and should not clutter the primary clinical-operational console.

The demo may pair this panel with a quick Cloud Run/Cloud Logging/Trace view to prove the backend is on Google Cloud.

## 7. Evaluation Proof

The application does not need a full evaluation dashboard for v0.1.

A compact About/Technical section may link to `EVALUATION.md` and summarize verified facts such as:

- number of committed synthetic scenarios;
- last evaluation version/commit;
- safety tests passed;
- last deployed E2E status.

Never show evaluation metrics that have not actually been generated.

## 8. Multimodal Stretch UI

Only if the stretch feature is implemented after core freeze, the import screen may offer:

```text
Upload CSV
or
Extract draft from image/PDF
```

Multimodal flow must visually enforce:

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

until the human verifies the record.

The detector must not consume unverified extraction output.

## 9. Four-Minute Demo UX Budget

The seeded scenario should minimize unnecessary clicks.

Target visible sequence:

1. import/trigger;
2. dashboard signal appears;
3. automatically open or navigate to incident;
4. timeline shows investigation/tool activity;
5. clarification card appears;
6. answer once;
7. package becomes ready;
8. approve;
9. external action result appears;
10. acknowledgement closes loop.

Avoid decorative transitions that consume demo time.

## 10. Acceptance Criteria

- [ ] autonomous start is visible;
- [ ] tool/evidence activity is visible;
- [ ] pause/resume is visible;
- [ ] failures/retries do not masquerade as success;
- [ ] EmbeddingGemma is labelled only if actually integrated;
- [ ] real and demo notification channels are distinguishable;
- [ ] real external action is visible in the hosted/demo path;
- [ ] technical proof is available without exposing chain-of-thought;
- [ ] multimodal extraction, if present, remains an unverified draft until human confirmation;
- [ ] the full product story remains understandable in <4 minutes.
