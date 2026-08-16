# Ngabo — UI/UX Hackathon Addendum

**Status:** Required extension to `docs/UI_UX_SPEC.md` for v0.1  
**Version:** 0.3  
**Date:** 2026-08-16

---

## 1. Hero Demo Principle

The judge must visually understand that Ngabo completes the canonical Taskmaster workflow **without human intervention**.

Hero flow:

```text
AMR data/signal arrives
  ↓
Pub/Sub triggers ADK workflow automatically
  ↓
deterministic function nodes fan out
  ↓
parallel branches complete + join
  ↓
Gemini bounded triage
  ↓
approved evidence retrieval
  ↓
Gemini synthesis
  ↓
deterministic validation / automatic repair if needed
  ↓
autonomy policy: A1 SAFE EXTERNAL COORDINATION
  ↓
freshness + idempotency
  ↓
real external action
  ↓
machine acknowledgement
```

Required hero counters:

```text
Prompts required        0
Human interventions     0
Clarifications          0
Approval clicks         0
```

Do not place a required clarification or approval click inside the canonical filmed path.

---

## 2. Canonical Timeline Events

Support public-safe events such as:

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
PACKAGE_VALIDATION_STARTED
PACKAGE_VALIDATION_FAILED
PACKAGE_REPAIR_STARTED
PACKAGE_REPAIR_COMPLETED
PACKAGE_VALIDATION_COMPLETED
AUTONOMY_POLICY_EVALUATED
FRESHNESS_CHECK_STARTED
FRESHNESS_CHECK_PASSED
FRESHNESS_CHECK_FAILED
IDEMPOTENCY_RESERVED
NOTIFICATION_SENT
NOTIFICATION_ACKNOWLEDGED
WORKFLOW_COMPLETED
WORKFLOW_ABSTAINED
```

Secondary/evaluation scenarios may also expose:

```text
AGENT_RUN_PAUSED
AGENT_RUN_RESUMED
CONTEXT_REBUILT
NEEDS_INFORMATION
POLICY_BLOCKED
```

Do not expose private chain-of-thought.

---

## 3. Fan-Out / Join Visualization

Make the deterministic parallel work obvious:

```text
Parallel investigation
  ✓ Resistance profile comparison    420 ms
  ✓ Baseline summary                 610 ms
  ✓ Missing-field assessment         180 ms

Joined findings
Gemini triage started
```

Rules:

- branch order does not imply semantic priority;
- deterministic calculations must not be visually attributed to Gemini;
- required branch failure must visibly block downstream success;
- tool-level details can live in a developer/details drawer.

---

## 4. Bounded Agent Visibility

Allowed labels:

- `Assessing joined findings`;
- `Selecting approved evidence topic`;
- `Synthesizing source-grounded incident package`;
- `Repairing package from validator feedback`;
- `Insufficient approved evidence — abstaining`.

Show observable stages/results, not hidden reasoning traces.

---

## 5. Autonomy Policy Card — Required

Before external action, show a compact deterministic policy result.

Hero example:

```text
Autonomy policy
Action class        A1 — Safe external coordination
Destination         Authorized test webhook
Package validation  Passed
Evidence integrity  Passed
Freshness           Passed
Idempotency         Reserved
Decision            AUTO-EXECUTE
```

Blocked example:

```text
Action class        A3 — Clinical/official decision
Decision            BLOCKED FROM AUTONOMOUS EXECUTION
Reason              Outside v0.1 autonomous action envelope
```

Never suggest Gemini granted itself permission to act.

---

## 6. Zero-Human Hero Data Contract

The hero fixture contains all material facts required for A1 completion.

Therefore the hero UI must **not** display a clarification card.

Missing-data behavior belongs in secondary/evaluation scenarios:

```text
Material information unavailable
→ Ngabo abstained safely
→ No external action sent
```

Optional/unknown data may remain visibly `UNKNOWN` when policy permits continuation.

---

## 7. Automatic Repair UI

If synthesis fails deterministic validation, timeline may show:

```text
Package validation failed
2 structured issues returned
Automatic repair attempt 1/2
Package validation passed
```

Do not expose raw private reasoning.

If repair budget is exhausted:

```text
Workflow abstained
Reason: package could not satisfy deterministic validation
External action: not sent
```

---

## 8. Freshness UI

Freshness remains mandatory even without human approval.

Hero:

```text
Current incident state verified
Freshness check passed
```

Changed-state scenario:

```text
New canonical data arrived before action
Package marked stale
Recomputing investigation before external action
```

No external action may be shown as sent until current-state revalidation passes.

---

## 9. Real External Action + Machine Acknowledgement

The hosted/filmed path should truthfully display:

```text
Channel        Authorized test webhook
Mode           Real integration
Action class    A1
Delivery ID     ...
Status          Sent
Acknowledgement ...
Completed at    ...
```

Local automated tests use a separate clearly labelled simulation adapter.

The acknowledgement must be machine-driven for the hero flow; no person should click “acknowledge.”

---

## 10. BYOF / Operational Utility Proof

A compact card can show generated benchmark facts:

```text
Builder reference workflow   X active human steps
Ngabo hero                   0 human steps after event
Prompts to start             0
Median event→action          X s
Median action→ack            X ms
```

Only show values generated in `EVALUATION.md`.

See `docs/BYOF_FRICTION.md` and `docs/OPERATIONAL_UTILITY_EVALUATION.md`.

---

## 11. Technical Proof Drawer

May expose safe metadata:

- incident/correlation/event IDs;
- graph run ID;
- node/branch/join IDs;
- agent run/session/invocation ID;
- model name;
- package/incident version;
- action class;
- freshness result;
- idempotency key reference;
- delivery/ack IDs;
- retry/repair counts.

This supports architecture judging but must not overwhelm the operational UI.

---

## 12. Failure / Abstention UX

Autonomous safety requires visible non-success states:

- `NEEDS_INFORMATION`;
- `INSUFFICIENT_APPROVED_EVIDENCE`;
- `VALIDATION_FAILED`;
- `POLICY_BLOCKED`;
- `STALE_RECOMPUTE_REQUIRED`;
- `ACTION_FAILED_RETRYABLE`;
- `ACTION_FAILED_TERMINAL`.

Never turn a safe abstention into a green success state for demo aesthetics.

---

## 13. Resume / Recovery Proof

Pause/resume remains a secondary engineering feature.

If exercised in evaluation/technical proof:

```text
Investigation interrupted
Recovery in progress
Context rebuilt from canonical state
Investigation resumed
```

The hero demo should prioritize uninterrupted zero-human completion unless a restart demonstration can be shown without confusing the core story.

---

## 14. Evidence Provenance

Evidence details show:

- source ID;
- publisher/title;
- official URL;
- version/date where available;
- retrieval method;
- excerpt/chunk provenance.

If EmbeddingGemma is active, label it truthfully. Similarity score is not medical confidence.

---

## 15. Four-Minute Demo UX Budget

Target:

1. **0:00–0:25** — personal BYOF friction + value proposition;
2. **0:25–0:45** — synthetic signal/data arrives;
3. **0:45–1:45** — automatic graph + fan-out/join + Gemini/evidence;
4. **1:45–2:20** — package validation + autonomy policy + freshness;
5. **2:20–2:45** — real external action + machine ack;
6. **2:45–3:10** — zero-human operational benchmark;
7. **3:10–3:40** — architecture diagram + Cloud Run/log proof;
8. **3:40–4:00** — evaluation/limitations/closing.

Exact timing may change, but hero execution must get most of the screen time.

---

## 16. Multimodal Stretch

Only after core freeze:

```text
image/PDF AST report
→ AI-EXTRACTED UNVERIFIED DRAFT
→ human verification
→ canonical deterministic ingestion
```

This optional input workflow may contain human verification because it is **not the canonical Taskmaster hero path**.

The detector must never consume unverified extraction.

---

## 17. Acceptance Criteria

- [ ] hero path begins automatically from an event;
- [ ] no chat prompt starts it;
- [ ] no clarification occurs in hero flow;
- [ ] no approval click occurs in hero flow;
- [ ] fan-out/join is legible;
- [ ] deterministic vs agentic work is distinguishable;
- [ ] validation/repair behavior is visible when exercised;
- [ ] autonomy policy proves A1 authorization deterministically;
- [ ] freshness/idempotency are visible before action;
- [ ] real external action leaves Ngabo;
- [ ] machine acknowledgement closes loop;
- [ ] zero-human benchmark uses measured values only;
- [ ] blocked/unsafe scenarios visibly abstain;
- [ ] no optional model/feature is implied unless implemented;
- [ ] complete story remains understandable within four minutes.
