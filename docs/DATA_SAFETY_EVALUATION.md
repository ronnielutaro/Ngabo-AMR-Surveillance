# Ngabo — Data, Safety & Evaluation Design

**Version:** 0.4  
**Date:** 2026-08-16

---

## 1. Purpose

Keep Ngabo v0.1:

- scientifically interpretable;
- auditable;
- reproducible;
- honest about uncertainty;
- safe for a synthetic-data demonstration;
- fully autonomous on the canonical Taskmaster hero path;
- resilient under asynchronous/retry execution;
- measurable through deterministic, agent, operational and end-to-end evaluation.

This is **not clinical validation**.

Required companion contracts:

- `docs/HACKATHON_ALIGNMENT.md`
- `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`
- `docs/ORCHESTRATION_PATTERNS.md`
- `docs/LONG_RUNNING_AGENT.md`
- `docs/OPERATIONAL_UTILITY_EVALUATION.md`

---

# Part A — Data

## 2. Canonical Isolate Boundary

Illustrative canonical fields:

```python
class Isolate:
    isolate_id: str
    collection_date: date
    organism_code: str
    organism_name: str
    ward: str | None
    specimen_type: str | None
    patient_token: str | None  # synthetic/demo only
    ast_results: dict[str, ASTResult]
    source_import_id: str

class ASTResult:
    antibiotic_code: str
    interpretation: Literal["S", "I", "R", "UNKNOWN"]
    mic: float | None
    zone_mm: float | None
    raw_value: str | None
```

MVP signal logic primarily uses normalized S/I/R interpretation.

## 3. Synthetic Data Policy

Public v0.1 uses Ngabo-authored synthetic representative data.

Rules:

- no real patient names/MRNs;
- no named-hospital patient/lab rows;
- no reconstruction of identifiable real records;
- all screenshots/logs/eval fixtures remain synthetic;
- every public fixture declares synthetic status;
- synthetic compatibility does not imply WHO/WHONET sponsorship.

Required disclaimer:

> This dataset is synthetic and intended solely for software demonstration/evaluation. It does not represent real patient records and is not suitable for clinical inference.

## 4. Hero Dataset Contract

The Taskmaster hero fixture must intentionally contain all **material canonical information** required for the safe A1 external coordination action.

Hero purpose:

```text
complete material data
→ suspicious deterministic signal
→ zero-human investigation
→ safe A1 action
→ machine acknowledgement
```

Do not create a hero fixture that forces clarification merely to demonstrate pause/resume.

Pause/resume belongs in separate engineering/eval scenarios.

## 5. Scenario Set

At minimum:

### Hero complete cluster

- suspicious seeded cluster;
- material fields present;
- approved evidence available;
- A1 action eligible;
- expected zero-human completion.

### Normal baseline

Routine variation; no suspicious signal/action.

### Noise

Missing/irregular values that do not justify fabricated completion.

### Material missing data

Expected autonomous abstention: `NEEDS_INFORMATION`.

### No approved evidence

Expected bounded no-evidence result/abstention when evidence is required.

### Prompt injection as data

Free text contains instruction-like content; must remain data.

### A2/A3 action request

Expected deterministic policy block.

### Stale-before-action

Canonical source changes after package synthesis; must recompute/revalidate before any external action.

---

## 6. Deterministic Surveillance

Resistance representation and signal calculations remain deterministic.

Possible S/I/R mapping:

```text
S -> 0
I -> 1
R -> 2
UNKNOWN -> excluded where appropriate
```

Possible prototype score:

```text
signal_score =
    w1 * temporal_concentration
  + w2 * location_concentration
  + w3 * phenotype_similarity
  + w4 * baseline_excess
```

Persist score components.

Weights/thresholds are prototype configuration, not validated clinical outbreak criteria.

---

# Part B — Safety

## 7. Claims Boundary

Allowed:

- `suspicious signal`;
- `possible cluster`;
- `investigation candidate`;
- `pattern warrants investigation`;
- `similar resistance profiles`;
- `synthetic demonstration`.

Forbidden autonomous claims:

- `confirmed outbreak`;
- patient-to-patient transmission claim;
- diagnosis;
- prescribe/start/stop antimicrobial;
- unsupported resistance-gene claim;
- official public-health declaration.

## 8. Safety Through Action Envelope

The Taskmaster hero has zero human intervention because Ngabo autonomously executes only **safe coordination actions**.

Action classes:

```text
A0 INTERNAL_STATE
A1 SAFE_EXTERNAL_COORDINATION
A2 REAL_OPERATIONAL_ESCALATION
A3 CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION
```

Policy:

- A0: autonomous;
- A1: autonomous only after deterministic gates;
- A2: outside autonomous public-v0.1 envelope unless separately authorized;
- A3: forbidden as autonomous v0.1 action.

Gemini cannot promote A2/A3 into A1.

See `docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`.

## 9. A1 Safety Gates

Before A1 external action:

- canonical data valid;
- signal/required graph outputs valid;
- no material blocker;
- evidence/source integrity valid;
- package valid;
- prohibited-claim validator passes;
- destination allow-listed;
- action classifier returns A1;
- freshness passes;
- idempotency reservation acquired.

Failure means autonomous abstention, not human bypass or model override.

## 10. Missing Data Rule

Ngabo does not hallucinate missing facts to preserve zero-human completion.

```text
material fact unavailable
→ NEEDS_INFORMATION
→ no unsafe action
```

Optional/non-material fields may remain explicitly unknown when policy allows continuation.

Automatically retrieve only from authorized canonical sources with defensible linkage.

## 11. Prompt Injection Boundary

Uploaded lab data is untrusted.

Mitigations:

- raw CSV/free text not concatenated as system instructions;
- agent receives normalized structured fields;
- free text remains data;
- tools/capabilities are allow-listed and typed;
- approved evidence corpus only;
- arbitrary URL browsing is not evidence authority;
- adversarial injection fixtures required.

## 12. Evidence Integrity

Approved evidence records include:

- source ID;
- publisher;
- title;
- URL;
- version/date;
- permitted stored excerpt/reference;
- provenance/usage status.

Generated packages may cite only retrieved/approved source IDs.

Unknown/fabricated source IDs fail deterministic validation.

## 13. EmbeddingGemma Safety

If integrated:

- searches approved corpus only;
- source IDs/provenance remain attached;
- similarity is retrieval ranking, not medical confidence;
- no arbitrary public web corpus is mixed silently;
- retrieval quality must be evaluated before claiming bonus.

## 14. MedGemma Safety

If integrated after core:

- bounded interpretation of already retrieved approved evidence;
- may not diagnose/prescribe/confirm outbreak;
- may not replace deterministic surveillance;
- may not create uncited authority;
- keep only if comparative eval shows clear benefit.

## 15. Multimodal Safety

Optional stretch:

```text
image/PDF AST
→ AI-extracted DRAFT
→ human verification
→ canonical ingestion
```

This optional input path can have human verification because it is not the canonical zero-human hero workflow.

Unverified extraction never reaches detector.

## 16. Privacy / Telemetry

- synthetic public data only;
- metadata-first logs/traces;
- no secrets/tokens;
- no unbounded raw data logging;
- no private chain-of-thought;
- full prompt/response logging disabled by default;
- observability failure cannot change domain behavior.

---

# Part C — Autonomous Repair & Abstention

## 17. Package Validator

Post-generation deterministic validation must reject:

- unknown isolate IDs;
- unknown source IDs;
- unsupported observed/derived claims;
- prohibited diagnosis/prescribing/outbreak confirmation;
- missing required schema fields;
- action payload not compatible with safe label requirements.

## 18. Bounded Repair

On validation failure:

```text
validator errors
→ Gemini repair
→ validator
```

Rules:

- max attempts configured (suggested `2`);
- model cannot override validator;
- validation budget exhaustion → `VALIDATION_FAILED`;
- no invalid package reaches action policy.

## 19. Safe Abstention

Expected legitimate outcomes:

```text
NEEDS_INFORMATION
INSUFFICIENT_APPROVED_EVIDENCE
VALIDATION_FAILED
POLICY_BLOCKED
STALE_RECOMPUTE_REQUIRED
ACTION_FAILED_RETRYABLE
ACTION_FAILED_TERMINAL
```

Autonomous completion is not required when safety facts are unavailable.

---

# Part D — Evaluation Layers

## 20. Layer 1 — Domain / Deterministic

Test:

- parser/normalizer;
- AST mappings;
- resistance similarity;
- baseline/windows/scoring;
- state transitions;
- action classification;
- material-change/freshness policy;
- prohibited-claim validation;
- idempotency policy.

## 21. Layer 2 — Application Workflow

With fakes/in-memory ports:

- incident start;
- zero-human hero progression;
- package validation/repair orchestration;
- A1 policy gate;
- A2/A3 blocking;
- freshness/recompute;
- notification/action gating;
- retry/redelivery behavior;
- machine acknowledgement closure.

## 22. Layer 3 — Graph / Function Nodes

Test:

- context node;
- profile/baseline/missingness nodes;
- parallel completion-order independence;
- typed join;
- required branch failure;
- no Gemini call for fixed routing/calculation;
- branch retries are safe.

## 23. Layer 4 — ADK / Agent Evaluation

Evaluate observable result and trajectory:

- bounded triage;
- evidence query selection where agentic;
- no-evidence handling;
- source-grounded synthesis;
- structured output;
- repair behavior;
- tool/model budgets;
- prompt injection resistance;
- fabricated source/isolate rejection;
- prohibited clinical claim avoidance.

Do not evaluate private chain-of-thought.

## 24. Layer 5 — Infrastructure / Contract

- Firestore;
- Pub/Sub;
- Cloud Storage;
- Gemini/ADK boundary;
- evidence retrieval;
- real A1 action adapter;
- acknowledgement callback/event;
- Cloud logging/tracing.

## 25. Layer 6 — Deployed E2E Hero

```text
signal
→ Pub/Sub
→ ADK graph
→ fan-out/join
→ Gemini/evidence
→ synthesis
→ validate/repair
→ A1 policy
→ freshness
→ idempotency
→ real external action
→ machine acknowledgement
```

Assertions:

```text
manual_prompt_count_to_start == 0
human_intervention_count == 0
human_active_steps == 0
clarification_count == 0
approval_click_count == 0
external_effect_count == 1
acknowledgement_count == 1
```

Run successfully at least three consecutive times before demo freeze.

---

## 26. Critical Safety Evaluations

### Action policy

- A1 eligible payload → may execute;
- A2 payload → blocked;
- A3 payload → blocked;
- Gemini text claiming A1 cannot override deterministic classification;
- non-allow-listed destination → blocked.

### Missing data

- material missing fact → abstain;
- optional missing fact → unknown preserved;
- no generated fake canonical value.

### Repair

- recoverable invalid output → repaired within budget;
- repeatedly invalid output → safe stop;
- invalid output never externally acts.

### Freshness

- no material change → action permitted;
- material source change → recompute/revalidate;
- stale cached/session context cannot authorize action.

### Idempotency

- duplicate Pub/Sub event → one incident/effect;
- retry after transient send failure → no ambiguous duplicate;
- acknowledgement replay → idempotent.

### Context truth

- old ADK/session text conflicts with Firestore → canonical Firestore/application state wins;
- compacted context cannot redefine isolate/AST facts.

---

## 27. Operational Utility

Use `docs/OPERATIONAL_UTILITY_EVALUATION.md` and `docs/BYOF_FRICTION.md`.

Report:

- reference human steps;
- zero-human hero counters;
- event→package/action/ack timings;
- model/deterministic call counts;
- retries/repair attempts;
- limitations.

---

## 28. `EVALUATION.md` Submission Artifact

Before submission publish real measured results including:

- synthetic dataset/scenario description;
- detector configuration/results;
- graph tests;
- ADK trajectory methodology;
- safety/adversarial tests;
- action-policy tests;
- autonomous repair tests;
- freshness/idempotency tests;
- operational utility/BYOF benchmark;
- three deployed hero runs;
- real external action + ack evidence IDs;
- EmbeddingGemma/MedGemma results only if implemented;
- exact model/framework versions;
- limitations;
- explicit statement: not clinical validation.

---

## 29. Definition of Done

- [ ] hero dataset supports zero-human A1 completion;
- [ ] zero-human E2E succeeds three consecutive deployed runs;
- [ ] A2/A3 are deterministically blocked;
- [ ] missing material information causes abstention, not fabrication;
- [ ] validator + bounded repair are implemented/tested;
- [ ] freshness/idempotency protect autonomous action;
- [ ] real external A1 action + machine acknowledgement work;
- [ ] prompt injection/source integrity tests pass;
- [ ] canonical truth beats model/session memory;
- [ ] `EVALUATION.md` contains actual results;
- [ ] no clinical validation or real-hospital-use claim is made.
