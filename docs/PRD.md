# Ngabo — Product Requirements Document (PRD)

**Version:** 0.3  
**Date:** 2026-08-16  
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
- validates the resulting package deterministically;
- repairs model-output defects automatically within a hard budget;
- classifies the intended action through deterministic A0/A1/A2/A3 policy;
- freshness-checks current state;
- executes a real authorized A1 external coordination action;
- receives a machine acknowledgement;
- closes the workflow with **zero human intervention**.

> **v0.1 promise:** turn a suspicious synthetic AMR surveillance signal into a validated, evidence-backed investigation package and safe external coordination action automatically from event to acknowledgement.

---

## 2. Primary User / Problem

**Hero user archetype:** microbiology/AMR surveillance professional who needs suspicious resistance patterns translated into a structured investigation package.

Primary job to be done:

> “When unusual resistance patterns appear in surveillance data, automatically investigate the signal, assemble traceable evidence, preserve uncertainty, prepare a structured incident package, and coordinate a safe next action without making me drive every step.”

Ngabo's hackathon BYOF story remains the builder's personally experienced research/coordination friction described in `docs/BYOF_FRICTION.md`; the product user archetype does not imply the builder personally holds a clinical role.

---

## 3. Core Goals

1. **Literal Taskmaster autonomy:** canonical event→ack hero uses zero human prompts/interventions/clarifications/approvals.
2. **Deterministic scientific logic:** parsing, normalization, similarity, windows, baselines and signal scoring are reproducible code.
3. **Bounded agentic reasoning:** Gemini reasons only where ambiguity/synthesis warrants it.
4. **Safe autonomous action:** only A1 safe external coordination can auto-execute after deterministic policy gates.
5. **Autonomous abstention:** missing/unsafe/invalid cases stop safely instead of inventing facts.
6. **Automatic repair:** invalid LLM packages can self-repair within a hard validator-controlled budget.
7. **Freshness/idempotency:** external action uses current canonical state and cannot duplicate on retry/redelivery.
8. **Real proof of action:** hosted demo executes a real authorized external action and machine acknowledgement.
9. **Observable autonomy:** graph/action state is inspectable without chain-of-thought.
10. **Evaluation:** zero-human utility, scientific correctness, action-policy safety and runtime reliability are measured.
11. **Reproducibility:** public repo, diagram, setup instructions and exact versions support inspection.

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
Gemini synthesis
        ↓
deterministic package validation
  ├─ invalid → bounded auto repair → validate
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

## 8. Package Requirements

Structured package includes:

```json
{
  "title": "...",
  "priority": "HIGH",
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

Deterministic validation rejects:

- unknown isolate/source IDs;
- unsupported observed/derived claims;
- prohibited diagnosis/prescribing/outbreak-confirmation language;
- missing required fields;
- unsafe coordination wording.

---

## 9. Automatic Repair

On package validation failure:

```text
structured validator errors
→ Gemini repair
→ validator
```

Hard max repair attempts, suggested `2`.

If exhausted → `VALIDATION_FAILED`, no external action.

---

## 10. Evidence Requirements

- curated approved corpus;
- every source has provenance/source ID;
- package cites only retrieved approved source IDs;
- no arbitrary web page becomes authority automatically;
- `INSUFFICIENT_APPROVED_EVIDENCE` is acceptable safe result;
- EmbeddingGemma only if core is stable/evaluated.

---

## 11. Freshness / Idempotency

Immediately before A1 external action:

- verify current incident/package/source watermark;
- material change → recompute/revalidate;
- rerun action policy;
- reserve idempotency key;
- execute once.

Pub/Sub redelivery/retries may never create duplicate external effects.

---

## 12. External Action / Ack

Preferred hero:

```text
NotificationPort
→ real authorized external webhook/sandbox
→ delivery result
→ machine acknowledgement callback/event
→ acknowledgement use case
→ completed state
```

No human acknowledgement required.

Local fake adapter remains for automated tests.

---

## 13. Core UI Requirements

The incident/autonomy console shows:

- signal explanation;
- graph/fan-out/join;
- bounded agent/evidence stages;
- package validation/repair;
- autonomy-policy decision;
- freshness/idempotency;
- external delivery;
- machine acknowledgement;
- zero-human operational metrics;
- failures/abstentions.

No chat-driven hero UX.

---

## 14. Core Data Fixtures

- complete zero-human hero cluster;
- normal baseline;
- malformed/noisy;
- material missingness abstention;
- no evidence;
- prompt injection as data;
- A2/A3 action block;
- stale-before-action;
- duplicate-event/idempotency.

---

## 15. Evaluation Requirements

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

### Safety

- A2/A3 blocked;
- material missing data abstains;
- non-allow-listed target blocked;
- invalid package repair/stop;
- prompt injection blocked;
- fabricated IDs/sources rejected;
- freshness recompute;
- duplicate event/retry one effect;
- canonical state beats stale session context.

### Utility

Compare builder BYOF reference workflow against zero-human hero using `docs/OPERATIONAL_UTILITY_EVALUATION.md`.

---

## 16. Success Criteria

v0.1 is successful when:

- event-driven hero completes automatically end-to-end;
- no human interaction occurs after trigger;
- safe A1 external action/ack is real and visible;
- unsafe/insufficient scenarios abstain;
- architecture is clean and failure-tolerant;
- EVALUATION.md contains real measured evidence;
- judge-facing diagram/video accurately match deployment;
- no clinical/public-health overclaim is made.

---

## 17. Related Contracts

- `docs/HACKATHON_ALIGNMENT.md`
- `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`
- `docs/BYOF_FRICTION.md`
- `docs/ORCHESTRATION_PATTERNS.md`
- `docs/LONG_RUNNING_AGENT.md`
- `docs/DATA_SAFETY_EVALUATION.md`
- `docs/OPERATIONAL_UTILITY_EVALUATION.md`
- `docs/SUBMISSION_EVIDENCE.md`
