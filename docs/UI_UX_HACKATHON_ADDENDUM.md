# Ngabo — UI/UX Hackathon Addendum

**Status:** Required extension to `docs/UI_UX_SPEC.md` for v0.1  
**Version:** 0.4  
**Date:** 2026-08-17

---

## 1. Hero Demo Principle

The judge must visually understand two things immediately:

1. Ngabo completes the canonical Taskmaster workflow **without human intervention**; and
2. Ngabo's **Twist is Proof-Carrying Autonomy** — the system does not trust fluent LLM output on faith.

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
Gemini proof-carrying synthesis
  ↓
deterministic claim/evidence verification
  ├─ invalid → bounded automatic repair → verify again
  └─ exhausted → autonomous abstention
  ↓
autonomy policy: A1 SAFE EXTERNAL COORDINATION
  ↓
freshness + ActionIntent/idempotency
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

## 2. The Twist Must Be Visible

The UI must make **Proof-Carrying Autonomy** understandable without exposing private chain-of-thought.

Recommended judge-facing explanation:

> **Gemini can interpret and hypothesize, but Ngabo does not trust free-form model prose. Every action-relevant claim must point back to canonical records, deterministic calculations, or approved evidence and pass machine verification before it can enter the autonomous action path.**

A compact visual should show:

```text
Model claim
  ↓
Record refs      ✓
Finding refs     ✓
Evidence refs    ✓
Claim type       HYPOTHESIS
Uncertainty      Present
Verification     PASSED
```

Avoid marketing language suggesting mathematical proof of medical truth.

---

## 3. Canonical Timeline Events

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
REASONING_PACKAGE_GENERATED
CLAIM_VERIFICATION_STARTED
CLAIM_VERIFICATION_FAILED
CLAIM_VERIFICATION_PASSED
REASONING_REPAIR_STARTED
REASONING_REPAIR_COMPLETED
REASONING_REPAIR_EXHAUSTED
AUTONOMY_POLICY_EVALUATED
FRESHNESS_CHECK_STARTED
FRESHNESS_CHECK_PASSED
FRESHNESS_CHECK_FAILED
ACTION_INTENT_PREPARED
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

## 4. Fan-Out / Join Visualization

Make deterministic parallel work obvious:

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

## 5. Bounded Agent Visibility

Allowed labels:

- `Assessing joined findings`;
- `Selecting approved evidence topic`;
- `Synthesizing proof-carrying incident claims`;
- `Repairing claims from deterministic verifier feedback`;
- `Insufficient approved evidence — abstaining`.

Show observable stages/results, not hidden reasoning traces.

---

## 6. Proof-Carrying Claims Card — Required

The incident package view must distinguish claim classes and show support references.

Example:

```text
Claim type       HYPOTHESIS
Statement        Closely matching resistance phenotypes may indicate a shared epidemiologic process.
Records          ISO-031 · ISO-034 · ISO-039
Finding          profile-comparison-17
Evidence         GUIDANCE-004
Uncertainty      Genomic relatedness unavailable
Verification     PASSED
```

For `OBSERVED_FACT`, show canonical-record support.

For `DERIVED_FINDING`, show deterministic finding ID/version.

For `EVIDENCE_STATEMENT`, show retrieved approved source/chunk/reference.

For `ACTION_JUSTIFICATION`, visibly distinguish **justification** from **authorization**.

---

## 7. Claim Verification UI

Hero pass state:

```text
Proof verification
Claims checked        7
Unknown record refs   0
Unknown finding refs  0
Unknown source refs   0
Unsupported claims    0
Forbidden claims      0
Result                PASSED
```

Failure example:

```text
Proof verification failed
Claim claim-03 references unknown finding baseline-999
Action path blocked
Automatic repair attempt 1/2
```

If repair succeeds, show re-verification. If exhausted:

```text
Workflow abstained
Reason: proof-carrying claims could not satisfy deterministic verification
External action: not sent
```

Never expose raw private CoT as “proof.”

---

## 8. Autonomy Policy Card — Required

Before external action, show a compact deterministic policy result.

Hero example:

```text
Autonomy policy
Action class          A1 — Safe external coordination
Destination           Authorized test webhook
Proof verification    Passed
Evidence integrity    Passed
Freshness             Passed
ActionIntent           Prepared
Idempotency           Reserved
Decision              AUTO-EXECUTE
```

Blocked example:

```text
Action class          A3 — Clinical/official decision
Decision              BLOCKED FROM AUTONOMOUS EXECUTION
Reason                Outside v0.1 autonomous action envelope
```

Never suggest Gemini granted itself permission to act.

---

## 9. Zero-Human Hero Data Contract

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

## 10. Bounded Repair UI

If proof/package verification fails:

```text
Claim verification failed
2 structured issues returned
Automatic repair attempt 1/2
Claim verification passed
```

Do not expose raw private reasoning.

Repair metadata belongs in technical view:

- attempt number;
- stable error codes;
- whether new approved evidence retrieval was explicitly routed;
- final verification status.

---

## 11. Freshness UI

Freshness remains mandatory even without human approval.

Hero:

```text
Current incident state verified
Source watermark unchanged
Freshness check passed
```

Changed-state scenario:

```text
New canonical data arrived before action
Previous package/proof status marked stale
Recomputing + re-verifying before external action
```

No external action may be shown as sent until current-state revalidation passes.

---

## 12. Real External Action + Machine Acknowledgement

The hosted/filmed path should truthfully display:

```text
Channel          Authorized test webhook
Mode             Real integration
Action class      A1
ActionIntent      ...
Delivery ID       ...
Status            Sent
Acknowledgement   ...
Completed at      ...
```

Local automated tests use a separate clearly labelled simulation adapter.

The acknowledgement must be machine-driven for the hero flow; no person should click “acknowledge.”

---

## 13. BYOF / Operational Utility Proof

A compact card can show generated benchmark facts:

```text
Builder reference workflow   X active human steps
Ngabo hero                    0 human steps after event
Prompts to start              0
Median event→action           X s
Median action→ack             X ms
Claims machine-verified       X
Repair attempts               X
```

Only show values generated in `EVALUATION.md`.

See `docs/BYOF_FRICTION.md` and `docs/OPERATIONAL_UTILITY_EVALUATION.md`.

---

## 14. Technical Proof Drawer

May expose safe metadata:

- incident/correlation/event IDs;
- graph run ID;
- node/branch/join IDs;
- agent run/session/invocation ID;
- model name;
- package/incident version;
- claim count/type counts;
- claim verification status/error codes;
- source/finding/record reference counts;
- repair attempt count;
- action class;
- freshness result;
- ActionIntent/idempotency reference;
- delivery/ack IDs;
- retry counts.

This supports architecture judging but must not overwhelm operational UI.

---

## 15. Failure / Abstention UX

Autonomous safety requires visible non-success states:

- `NEEDS_INFORMATION`;
- `INSUFFICIENT_APPROVED_EVIDENCE`;
- `CLAIM_VERIFICATION_FAILED`;
- `VALIDATION_FAILED`;
- `POLICY_BLOCKED`;
- `STALE_RECOMPUTE_REQUIRED`;
- `ACTION_FAILED_RETRYABLE`;
- `ACTION_FAILED_TERMINAL`.

Never turn a safe abstention into a green success state for demo aesthetics.

---

## 16. Resume / Recovery Proof

Pause/resume remains a secondary engineering feature.

If exercised:

```text
Investigation interrupted
Recovery in progress
Context rebuilt from canonical state
Proof references revalidated if state changed
Investigation resumed
```

The hero demo should prioritize uninterrupted zero-human completion unless a restart demonstration can be shown without confusing the core story.

---

## 17. Evidence Provenance

Evidence details show:

- source ID;
- publisher/title;
- official URL;
- version/date where available;
- retrieval method;
- excerpt/chunk provenance.

If EmbeddingGemma is active, label it truthfully. Similarity score is not medical confidence.

---

## 18. Four-Minute Demo UX Budget

Target:

1. **0:00–0:25** — personal BYOF friction + value proposition;
2. **0:25–0:45** — synthetic signal/data arrives;
3. **0:45–1:30** — automatic graph + fan-out/join + Gemini/evidence;
4. **1:30–2:00** — **The Twist: Proof-Carrying Autonomy** — show typed claims + deterministic verification;
5. **2:00–2:20** — autonomy policy + freshness + ActionIntent/idempotency;
6. **2:20–2:45** — real external action + machine ack;
7. **2:45–3:10** — zero-human operational benchmark;
8. **3:10–3:40** — architecture diagram + Cloud Run/log proof;
9. **3:40–4:00** — evaluation/limitations/closing.

Exact timing may change, but hero execution must get most screen time.

---

## 19. Multimodal Stretch

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

## 20. Acceptance Criteria

- [ ] hero path begins automatically from an event;
- [ ] no chat prompt starts it;
- [ ] no clarification occurs in hero flow;
- [ ] no approval click occurs in hero flow;
- [ ] fan-out/join is legible;
- [ ] deterministic vs agentic work distinguishable;
- [ ] Proof-Carrying Autonomy visible and understandable;
- [ ] claim types + record/finding/source references visible;
- [ ] deterministic proof verification visible;
- [ ] repair/abstention behavior visible when exercised;
- [ ] autonomy policy proves A1 authorization deterministically;
- [ ] freshness + ActionIntent/idempotency visible before action;
- [ ] real external action leaves Ngabo;
- [ ] machine acknowledgement closes loop;
- [ ] zero-human benchmark uses measured values only;
- [ ] blocked/unsafe scenarios visibly abstain;
- [ ] no optional model/feature implied unless implemented;
- [ ] complete story remains understandable within four minutes.
