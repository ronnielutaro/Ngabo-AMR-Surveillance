# Ngabo — Product Requirements Document (PRD)

**Version:** 0.4  
**Date:** 2026-08-17  
**Status:** Hackathon MVP baseline  
**Primary track:** All Things Agentic Hackathon — The Taskmaster

---

## 1. Product Summary

Ngabo is an open-source, event-driven antimicrobial-resistance (AMR) surveillance and incident-response system.

It ingests representative synthetic WHONET-style microbiology/AST data, validates and normalizes it deterministically, detects suspicious resistance patterns using transparent statistical/rule-based logic, and launches an autonomous Google ADK investigation workflow.

The canonical v0.1 hero automatically:

- loads current incident context;
- performs deterministic resistance-profile, baseline and missingness analysis in parallel;
- uses Gemini only for bounded investigation/evidence/synthesis reasoning;
- requires Gemini's material claims to carry machine-checkable references to canonical records, deterministic findings and/or approved evidence;
- verifies those claims deterministically before action eligibility;
- repairs invalid model output automatically within a hard budget or safely abstains;
- classifies the intended action through deterministic A0/A1/A2/A3 policy;
- freshness-checks current state;
- executes a real authorized A1 external coordination action;
- receives a machine acknowledgement;
- closes the workflow with **zero human intervention**.

> **v0.1 promise:** turn a suspicious synthetic AMR surveillance signal into a machine-verified, evidence-backed investigation package and safe external coordination action automatically from event to acknowledgement.

---

## 2. Primary User / Problem

**Hero user archetype:** microbiology/AMR surveillance professional who needs suspicious resistance patterns translated into a structured investigation package.

Primary job to be done:

> “When unusual resistance patterns appear in surveillance data, automatically investigate the signal, assemble traceable evidence, preserve uncertainty, verify the model's claims, prepare a structured incident package, and coordinate a safe next action without making me drive every step.”

Ngabo's hackathon BYOF story remains the builder's personally experienced research/coordination friction described in `docs/BYOF_FRICTION.md`; the product user archetype does not imply the builder personally holds a clinical role.

---

## 3. Core Goals

1. **Literal Taskmaster autonomy:** canonical event→ack hero uses zero human prompts/interventions/clarifications/approvals.
2. **Deterministic scientific logic:** parsing, normalization, similarity, windows, baselines and signal scoring are reproducible code.
3. **Bounded agentic reasoning:** Gemini reasons only where ambiguity/synthesis warrants it.
4. **Proof-carrying reasoning:** action-relevant model claims must reference canonical records, deterministic findings and/or approved evidence and pass machine verification.
5. **Safe autonomous action:** only A1 safe external coordination can auto-execute after deterministic policy gates.
6. **Autonomous abstention:** missing/unsafe/invalid cases stop safely instead of inventing facts.
7. **Automatic repair:** invalid LLM packages can self-repair within a hard verifier-controlled budget.
8. **Freshness/idempotency:** external action uses current canonical state and cannot duplicate on retry/redelivery.
9. **Real proof of action:** hosted demo executes a real authorized external action and machine acknowledgement.
10. **Observable autonomy:** graph/action/claim-verification state is inspectable without chain-of-thought.
11. **Evaluation:** zero-human utility, scientific correctness, claim-reference integrity, action-policy safety and runtime reliability are measured.
12. **Reproducibility:** public repo, diagram, setup instructions and exact versions support inspection.

---

## 4. Safety / Non-Goals

Ngabo v0.1 will not:

- diagnose patients;
- prescribe/start/stop antibiotics;
- autonomously confirm or officially declare an outbreak;
- autonomously execute A2/A3 clinical/official public-health actions;
- contact real hospitals/patients/persons without explicit authorization;
- replace WHONET or Uganda's broader AMR surveillance infrastructure;
- use real identifiable patient data in public demo;
- claim clinical validation/regulatory approval;
- treat model chain-of-thought, confidence or model consensus as evidence/authority;
- require genomics, vector DB, GKE, BigQuery or microservice fleet;
- require MedGemma/multimodal/genomics for core hero.

EmbeddingGemma is optional post-core. MedGemma and multimodal remain gated stretch.

---

## 5. Canonical Hero Workflow

```text
receive synthetic WHONET-style data
        ↓
deterministic validation + normalization
        ↓
deterministic surveillance detector
        ↓
suspicious investigation candidate
        ↓
Pub/Sub event
        ↓
ADK workflow starts automatically
        ↓
context
        ↓
parallel deterministic investigation
  ├─ resistance-profile comparison
  ├─ baseline summary
  └─ missing-field assessment
        ↓
join
        ↓
Gemini triage
        ↓
approved evidence retrieval
        ↓
Gemini proof-carrying synthesis
        ↓
deterministic claim/evidence verification
  ├─ invalid → bounded auto repair → verify
  ├─ exhausted → autonomous abstention
  └─ valid
        ↓
deterministic autonomy policy
  ├─ A1 → continue
  └─ blocked/insufficient → autonomous abstention
        ↓
freshness check
        ↓
idempotency reservation
        ↓
real authorized external A1 action
        ↓
machine acknowledgement
        ↓
completed/audited incident
```

Hero metrics:

```text
manual_prompt_count_to_start = 0
human_intervention_count = 0
human_active_steps = 0
clarification_count = 0
approval_click_count = 0
```

---

## 6. Action Policy

Action classes:

```text
A0 INTERNAL_STATE                auto
A1 SAFE_EXTERNAL_COORDINATION    auto after gates
A2 REAL_OPERATIONAL_ESCALATION   blocked from public-v0.1 auto lane by default
A3 CLINICAL/OFFICIAL DECISION    always blocked from autonomous v0.1
```

Hero action must be A1 and sent only to an authorized allow-listed test/sandbox/internal target.

Example payload label:

> **AMR surveillance investigation candidate — synthetic demonstration. Not a confirmed outbreak, diagnosis or treatment recommendation.**

Gemini may request/justify an A1 candidate in structured output, but only deterministic policy can authorize the executable action class.

---

## 7. Missing-Data Requirements

Hero fixture includes all material information needed for A1 completion.

For other scenarios:

- material missing fact → `NEEDS_INFORMATION`, no external action;
- optional missing fact → preserve `UNKNOWN`, continue only if policy permits;
- deterministic linked-source lookup may recover facts from already-authorized canonical sources;
- never hallucinate a clinical fact to avoid a human question.

No mandatory clarification is part of hero flow.

---

## 8. Proof-Carrying Claim Requirements

Read `docs/PROOF_CARRYING_REASONING.md` and ADR 0009.

Every material model-generated claim must be typed. Minimum claim classes:

```text
OBSERVED_FACT
DERIVED_FINDING
EVIDENCE_STATEMENT
HYPOTHESIS
ACTION_JUSTIFICATION
```

Required semantics:

- `OBSERVED_FACT` references canonical source records;
- `DERIVED_FINDING` references deterministic Ngabo result IDs;
- `EVIDENCE_STATEMENT` references actually retrieved approved evidence IDs;
- `HYPOTHESIS` remains explicitly labelled and carries supporting references plus uncertainty;
- `ACTION_JUSTIFICATION` may explain an A1 candidate but does not authorize execution.

The public v0.1 verifier rejects attempted claim types or semantics equivalent to:

- diagnosis;
- prescription;
- outbreak confirmation;
- mandatory containment authority;
- official public-health declaration.

Unknown/stale references fail verification.

---

## 9. Package Requirements

Structured package includes both human-readable sections and machine-verifiable claims.

```json
{
  "title": "...",
  "priority": "HIGH",
  "claims": [
    {
      "claim_id": "claim-01",
      "claim_type": "HYPOTHESIS",
      "statement": "...",
      "supporting_record_ids": [],
      "supporting_finding_ids": [],
      "supporting_source_ids": [],
      "contradicting_claim_ids": [],
      "uncertainties": []
    }
  ],
  "observed_evidence": [],
  "derived_findings": [],
  "hypotheses": [],
  "uncertainties": [],
  "missing_information": [],
  "guidance": [],
  "investigation_checklist": [],
  "draft_coordination_message": "...",
  "limitations": []
}
```

Deterministic verification rejects:

- unknown canonical record/isolate IDs;
- unknown/stale deterministic finding IDs;
- unknown/unretrieved/unapproved source IDs;
- unsupported observed/derived claims;
- hypothesis→fact escalation;
- prohibited diagnosis/prescribing/outbreak-confirmation language;
- missing required fields/uncertainties;
- unsafe coordination wording.

---

## 10. Automatic Repair

On claim/package verification failure:

```text
structured verifier errors
→ Gemini repair
→ deterministic verifier
```

Hard max repair attempts, suggested `2`.

Repair may not invent source records/findings/evidence, mutate action policy or bypass verification.

If exhausted → `VALIDATION_FAILED`, no external action.

---

## 11. Evidence Requirements

- curated approved corpus;
- every source has provenance/source ID;
- package cites only retrieved approved source IDs;
- no arbitrary web page becomes authority automatically;
- `INSUFFICIENT_APPROVED_EVIDENCE` is acceptable safe result;
- EmbeddingGemma only if core is stable/evaluated.

---

## 12. Freshness / Idempotency

Immediately before A1 external action:

- verify current incident/package/source watermark;
- verify current package still carries a passing claim-verification report;
- material change → recompute/revalidate;
- rerun action policy;
- reserve idempotency key;
- execute once.

Pub/Sub redelivery/retries may never create duplicate logical external effects.

---

## 13. External Action / Ack

Preferred hero:

```text
verified package
→ NotificationPort
→ real authorized external webhook/sandbox
→ delivery result
→ machine acknowledgement callback/event
→ acknowledgement use case
→ completed state
```

No human acknowledgement required.

Local fake adapter remains for automated tests.

---

## 14. Core UI Requirements

The incident/autonomy console shows:

- signal explanation;
- graph/fan-out/join;
- bounded agent/evidence stages;
- claim types and supporting record/finding/source references;
- proof-verification status;
- package validation/repair;
- autonomy-policy decision;
- freshness/idempotency;
- external delivery;
- machine acknowledgement;
- zero-human operational metrics;
- failures/abstentions.

No chat-driven hero UX.

Do not expose private chain-of-thought. Expose checkable claims, references, uncertainty and verification state.

---

## 15. Core Data Fixtures

- complete zero-human hero cluster;
- normal baseline;
- malformed/noisy;
- material missingness abstention;
- no evidence;
- prompt injection as data;
- fabricated canonical-record reference;
- fabricated deterministic-finding reference;
- fabricated/unretrieved source reference;
- hypothesis promoted to fact;
- forbidden claim-type escalation;
- A2/A3 action block;
- stale-before-action;
- duplicate-event/idempotency.

---

## 16. Evaluation Requirements

### Hero

At least three consecutive deployed runs with:

```text
0 prompts
0 interventions
0 human steps
0 clarifications
0 approvals
1 external effect
1 machine acknowledgement
```

### Safety / proof integrity

- A2/A3 blocked;
- material missing data abstains;
- non-allow-listed target blocked;
- invalid package repair/stop;
- prompt injection blocked;
- fabricated record/finding/source IDs rejected;
- unsupported factual claim rejected;
- claim-type escalation rejected;
- unverified package cannot enter A1 policy;
- repair budget exhaustion abstains;
- freshness recompute;
- duplicate event/retry one effect;
- canonical state beats stale session context.

Track at least where meaningful:

```text
unsupported_claim_rate
invalid_reference_rate
fabricated_source_rate
fabricated_record_rate
claim_verification_pass_rate
repair_success_rate
unsafe_claim_escape_rate
```

Target `unsafe_claim_escape_rate == 0` on the committed software adversarial suite. This is not a clinical safety guarantee.

### Utility

Compare builder BYOF reference workflow against zero-human hero using `docs/OPERATIONAL_UTILITY_EVALUATION.md`.

---

## 17. Success Criteria

v0.1 is successful when:

- event-driven hero completes automatically end-to-end;
- no human interaction occurs after trigger;
- every material action-relevant model claim is proof-carrying and machine-verified;
- safe A1 external action/ack is real and visible;
- unsafe/insufficient/unverifiable scenarios abstain;
- architecture is clean and failure-tolerant;
- EVALUATION.md contains real measured evidence;
- judge-facing diagram/video accurately match deployment;
- no clinical/public-health overclaim is made.

---

## 18. Related Contracts

- `docs/HACKATHON_ALIGNMENT.md`
- `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`
- `docs/BYOF_FRICTION.md`
- `docs/ORCHESTRATION_PATTERNS.md`
- `docs/PROOF_CARRYING_REASONING.md`
- `docs/LONG_RUNNING_AGENT.md`
- `docs/DATA_SAFETY_EVALUATION.md`
- `docs/OPERATIONAL_UTILITY_EVALUATION.md`
- `docs/SUBMISSION_EVIDENCE.md`
