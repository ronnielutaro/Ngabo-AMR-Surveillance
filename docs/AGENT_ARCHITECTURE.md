# Ngabo — Agent & Workflow Design

**Version:** 0.5  
**Date:** 2026-08-17  
**Framework:** Google ADK (Python)  
**Primary model:** Gemini 3.6 Flash

---

## 1. Principle

Ngabo is not “a bunch of agents talking to each other.”

The v0.1 runtime uses bounded Gemini reasoning inside an explicit deterministic workflow.

The hero completes without human intervention, but Gemini does not own scientific truth, proof validity, action authorization, freshness, idempotency, or external side effects.

Two governing rules apply:

> **Deterministic when the workflow is known; agentic when the decision is ambiguous; dynamic only when the workflow itself cannot reasonably be known in advance.**

> **LLM proposes; deterministic machinery verifies whatever can be verified before the claim may influence autonomous action.**

---

## 2. Agent Role

Gemini is responsible for:

- reasoning across joined deterministic findings;
- selecting bounded approved-evidence intent when ambiguous;
- forming explicitly labelled hypotheses;
- synthesizing approved evidence into **proof-carrying structured claims**;
- repairing claims/package from structured deterministic verifier feedback;
- stopping with uncertainty when evidence is insufficient.

Gemini is **not** responsible for:

- signal calculation;
- profile/baseline math;
- canonical-record truth;
- deterministic-finding truth;
- source approval/retrieval truth;
- claim verification policy;
- fixed routing;
- action class assignment;
- allow-list authorization;
- freshness/material-change detection;
- ActionIntent/idempotency;
- external action side effects;
- acknowledgement state transitions;
- prescribing/diagnosis/outbreak confirmation.

---

## 3. Canonical Hero Runtime

```text
signal event
  ↓
context function
  ↓
parallel deterministic branches
  ├─ profile comparison
  ├─ baseline summary
  └─ missingness assessment
  ↓
join
  ↓
Gemini triage
  ↓
approved evidence retrieval
  ↓
Gemini proof-carrying synthesis
  ↓
deterministic claim/evidence verifier
  ├─ valid → continue
  └─ invalid → structured errors → bounded Gemini repair → verifier
       └─ exhausted → autonomous abstention
  ↓
package/schema validation
  ↓
deterministic autonomy policy
  ├─ A1 → continue
  └─ blocked/insufficient → abstain
  ↓
freshness
  ↓
transactional ActionIntent / idempotency
  ↓
external A1 action adapter
  ↓
machine acknowledgement
```

No human clarification/approval node is required in hero path.

---

## 4. Hero No-Question Rule

Hero fixture must be complete enough for safe A1 coordination.

If a non-hero incident lacks a material fact:

```text
material missingness
→ NEEDS_INFORMATION
→ autonomous abstention
```

The model must not fabricate the value and should not route to a human merely to preserve “completion.”

---

## 5. Structured Inputs

Gemini should receive bounded structured investigation context such as:

```json
{
  "incident_id": "INC-001",
  "incident_version": 4,
  "source_watermark": "...",
  "signal": {},
  "profile_comparison": {"finding_id": "profile-comparison-17"},
  "baseline_summary": {"finding_id": "baseline-08"},
  "missing_fields": [],
  "approved_evidence": [
    {"source_id": "GUIDANCE-004", "chunk_id": "chunk-12"}
  ],
  "known_uncertainties": []
}
```

Canonical facts are loaded from application state, not remembered from prior model conversation.

---

## 6. Proof-Carrying Structured Output

Final synthesis must use a strict schema equivalent to:

```json
{
  "package_id": "PKG-001",
  "claims": [
    {
      "claim_id": "claim-01",
      "claim_type": "HYPOTHESIS",
      "statement": "The isolates show a closely matching resistance phenotype consistent with a possible shared epidemiologic process.",
      "supporting_record_ids": ["ISO-031", "ISO-034", "ISO-039"],
      "supporting_finding_ids": ["profile-comparison-17"],
      "supporting_source_ids": ["GUIDANCE-004"],
      "contradicting_claim_ids": [],
      "uncertainties": ["Genomic relatedness is unavailable."],
      "requested_action_class": "A1",
      "confidence_label": "BOUNDED_HYPOTHESIS"
    }
  ],
  "draft_coordination_message": "...",
  "limitations": []
}
```

Supported material claim classes:

- `OBSERVED_FACT`;
- `DERIVED_FINDING`;
- `EVIDENCE_STATEMENT`;
- `HYPOTHESIS`;
- `ACTION_JUSTIFICATION`.

The output is a model proposal until deterministic claim verification succeeds.

---

## 7. Deterministic Claim Verification

`VerifyReasoningClaims` checks at minimum:

- record/isolate IDs exist in current incident;
- deterministic finding IDs exist, match current incident/run/version, and support declared value;
- evidence/source IDs were actually retrieved and approved;
- package/finding/source references are not stale;
- observed facts are not model-only inventions;
- hypotheses stay labelled hypotheses;
- forbidden diagnosis/prescription/outbreak/official-authority claim classes or wording are rejected;
- required uncertainties/limitations are present where policy requires them;
- `ACTION_JUSTIFICATION` cannot authorize an action.

Unknown references fail deterministically.

The verifier returns stable structured error codes suitable for routing, repair, telemetry, and evaluation.

---

## 8. Bounded Repair

Repair loop:

```text
claim verification errors
→ Gemini repair using existing permitted facts/findings/evidence
→ deterministic verification
```

Controls:

- hard max attempts, suggested `2`;
- no model override of verifier;
- repair cannot mutate canonical facts/deterministic findings/action policy;
- arbitrary new evidence is forbidden unless workflow explicitly routes through approved retrieval;
- repair exhaustion → `VALIDATION_FAILED` / abstention;
- unverified package never reaches A1 action policy.

---

## 9. Relationship to Chain-of-Thought

Ngabo may use model-native reasoning internally where useful, but:

- private/hidden CoT is not canonical truth;
- CoT is not persisted as evidence;
- CoT is not shown in UI/logs/submission;
- a detailed rationale does not bypass deterministic verification;
- self-consistency/multiple-candidate reasoning, if used, is only a quality technique;
- disagreement should increase uncertainty or abstention;
- model consensus is still not proof.

Judge-facing trust comes from typed claims + machine-checkable references + deterministic verification.

---

## 10. Evidence Capability

Evidence retrieval is behind `EvidenceSearchPort`.

Core may use deterministic/tag retrieval.

Post-core:

```text
EvidenceSearchPort
→ EmbeddingGemma adapter
→ approved corpus only
```

Every `EVIDENCE_STATEMENT` must point to evidence actually returned by the approved retrieval path.

A model-created URL/title/source is never authority.

---

## 11. Action Boundary

Gemini may propose an `ACTION_JUSTIFICATION`, but action authority is separate:

```text
verified package
→ deterministic AutonomousActionPolicy
→ A1 eligible?
→ freshness
→ ActionIntent/outbox/idempotency
→ NotificationPort
```

Gemini cannot:

- convert A2/A3 to A1;
- override target allow-list;
- waive freshness;
- create/send external action directly.

---

## 12. Failure / Abstention

Expected typed outcomes include:

```text
NEEDS_INFORMATION
INSUFFICIENT_APPROVED_EVIDENCE
CLAIM_VERIFICATION_FAILED
VALIDATION_FAILED
POLICY_BLOCKED
STALE_RECOMPUTE_REQUIRED
ACTION_FAILED_RETRYABLE
ACTION_FAILED_TERMINAL
```

No later agent stage may turn deterministic critical failure into apparent success.

---

## 13. Observability

Expose public-safe metadata:

```text
claim_count
claim_type_counts
invalid_reference_count
unsupported_claim_count
verification_error_codes
repair_attempt_count
package_version
source_watermark
```

Useful events:

```text
REASONING_PACKAGE_GENERATED
CLAIM_VERIFICATION_STARTED
CLAIM_VERIFICATION_PASSED
CLAIM_VERIFICATION_FAILED
REASONING_REPAIR_STARTED
REASONING_REPAIR_COMPLETED
REASONING_REPAIR_EXHAUSTED
```

No private chain-of-thought.

---

## 14. Evaluation

Required tests/evals:

- unknown isolate/record ID rejected;
- unknown deterministic finding ID rejected;
- wrong-run/stale finding rejected;
- unknown/unretrieved source rejected;
- fabricated source/title/URL rejected;
- unsupported observed fact rejected;
- hypothesis→fact escalation rejected;
- forbidden claim type rejected;
- failed verification blocks A1;
- bounded repair succeeds/fails correctly;
- repair budget enforced;
- action policy still runs independently after proof passes;
- `unsafe_claim_escape_rate == 0` on committed adversarial software suite.

Do not present that software test metric as clinical validation or universal hallucination elimination.

---

## 15. Hero Acceptance

- [ ] event starts workflow without prompt;
- [ ] deterministic branches fan out/join;
- [ ] Gemini only handles bounded reasoning;
- [ ] approved evidence retrieved automatically;
- [ ] synthesis returns typed proof-carrying claims;
- [ ] deterministic claim/evidence verification passes;
- [ ] no fabricated/stale/forbidden claim reaches action path;
- [ ] invalid claims repair within budget or abstain;
- [ ] no human clarification;
- [ ] no approval click;
- [ ] policy deterministically authorizes only A1;
- [ ] freshness + ActionIntent/idempotency pass;
- [ ] real external A1 action occurs;
- [ ] machine acknowledgement returns;
- [ ] `human_intervention_count == 0`.
