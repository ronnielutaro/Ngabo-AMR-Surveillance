# Ngabo — Data, Safety & Evaluation Design

**Version:** 0.3  
**Date:** 2026-08-16

---

## 1. Purpose

Keep Ngabo v0.1:

- scientifically interpretable;
- auditable and reproducible;
- honest about uncertainty;
- safe for a synthetic-data demonstration;
- resilient under asynchronous/resumable graph execution;
- explicit about human authority;
- protected against stale approvals and replayed side effects;
- measurable through deterministic, graph, agent, operational-utility and end-to-end evaluation.

This is **not clinical validation**.

Required companion contracts:

- `docs/HACKATHON_ALIGNMENT.md`
- `docs/ADK_RUNTIME.md`
- `docs/ORCHESTRATION_PATTERNS.md`
- `docs/LONG_RUNNING_AGENT.md`
- `docs/OPERATIONAL_UTILITY_EVALUATION.md`
- `docs/THIRD_PARTY_PROVENANCE.md`

---

# Part A — Data

## 2. Canonical Isolate Schema

Illustrative domain shape:

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

MVP detection primarily uses normalized S/I/R interpretation.

---

## 3. Synthetic Dataset Policy

Public v0.1 data is representative and synthetic.

Rules:

- no real patient names/MRNs;
- no claim rows came from a named hospital;
- no real laboratory export committed or shown in public demo/logs;
- published aggregate patterns may inspire scenarios, but real patient rows are not reconstructed;
- screenshots, logs and committed eval fixtures use synthetic content;
- every fixture is explicitly labelled synthetic;
- third-party sample files are not copied unless usage rights/provenance are recorded.

Dataset disclaimer:

> “This dataset is synthetic and intended solely for software demonstration/evaluation. It does not represent real patient records and is not suitable for clinical inference.”

See `docs/THIRD_PARTY_PROVENANCE.md`.

---

## 4. Required Scenario Fixtures

Create at least:

### Normal baseline
Routine variation without the seeded suspicious pattern.

### Noise
Missing values, duplicates and unusual-but-isolated resistance.

### Seeded suspicious cluster
For example:

- *Klebsiella pneumoniae*;
- same neonatal unit;
- narrow time window;
- highly similar resistance phenotype;
- one intentionally missing specimen field for clarification testing.

### Prompt-injection-as-data
A free-text field contains instruction-like text intended to manipulate an LLM.

Expected: data remains data; no system/tool instructions are overridden.

### Long-running/freshness fixture
A deterministic material change is introduced after package review so the stale approval path can be tested.

---

## 5. Resistance Representation

For overlapping antibiotics:

```text
S -> 0
I -> 1
R -> 2
UNKNOWN -> excluded from pairwise comparison
```

Preferred MVP similarity is one documented deterministic method such as exact-category agreement or Jaccard similarity of resistant-antibiotic sets.

Persist method/configuration and component outputs.

---

## 6. Prototype Signal Score

Illustrative transparent form:

```text
signal_score =
    w1 * temporal_concentration
  + w2 * location_concentration
  + w3 * phenotype_similarity
  + w4 * baseline_excess
```

Weights/thresholds are prototype configuration, not clinically validated outbreak parameters.

Persist component values and trigger explanation for every signal.

---

# Part B — Safety

## 7. Claims Boundary

Ngabo may say:

- “suspicious signal”;
- “possible cluster”;
- “pattern warrants investigation”;
- “high-priority investigation candidate”;
- “these isolates have similar resistance profiles.”

Ngabo must not autonomously state:

- “confirmed outbreak”;
- “these patients infected one another”;
- “prescribe/start/stop antibiotic X”;
- “gene X is present” without validated genomic evidence.

---

## 8. Deterministic / Agentic / Human Authority Boundary

```text
DETERMINISTIC CODE/FUNCTION NODES
parse
validate
normalize
calculate AST/profile/baseline/window/score
extract structural missingness
fixed routing/state validation
idempotency
join required findings
package validation
freshness/version comparison

GEMINI AGENT NODES
reason across joined findings
assess materiality of missing context
choose bounded evidence intent/optional capability
ask one targeted clarification
synthesize retrieved evidence
produce labelled hypotheses / draft package
stop with uncertainty when evidence is insufficient

HUMAN
provide materially missing context when asked
approve/reject/request more information at consequential boundary
confirm outbreak through appropriate professional process
make patient treatment decisions
```

The human safety gate is not manual orchestration of the investigation.

---

## 9. Prompt-Injection Boundary

Uploaded lab data is **untrusted data**.

Mitigations:

- no raw CSV concatenated into system instructions;
- agent receives canonical structured fields;
- free text remains explicitly data;
- approved evidence corpus is curated;
- arbitrary external URLs are not treated as approved evidence;
- instruction-like imported text is part of adversarial evals;
- tool/capability access is allow-listed and typed;
- fixed routing is ordinary code, not prompt text.

---

## 10. Source / Citation Integrity

Approved evidence records include:

- source ID;
- publisher;
- title;
- official URL;
- version/date where possible;
- stored excerpt/reference and provenance/usage basis.

Generated package may cite only source IDs retrieved during that investigation.

Application validation rejects unknown source IDs before review.

Corpus rights/provenance must pass `docs/THIRD_PARTY_PROVENANCE.md`.

---

## 11. EmbeddingGemma Evidence Safety

EmbeddingGemma may rank/retrieve only within the approved corpus.

Rules:

- embedding similarity is retrieval, not evidence authority;
- returned chunks preserve source IDs/metadata;
- similarity score is not clinical confidence;
- no arbitrary web corpus is mixed silently into the index;
- retrieval quality is measured before the integration/bonus is claimed;
- exact model/license/terms are recorded before release.

---

## 12. Optional MedGemma Safety Gate

If MedGemma is added, it remains a bounded source-traceable interpretation capability over already approved/retrieved material.

It may not:

- diagnose;
- prescribe;
- confirm outbreaks;
- replace deterministic surveillance/AST calculations;
- introduce uncited authoritative claims;
- bypass final human review.

Compare against the simpler Gemini+retrieval baseline. Omit if benefit is not measurable or safety/reliability worsens.

---

## 13. Multimodal Draft Boundary

If implemented after core freeze:

```text
image/scanned PDF AST report
        ↓
Gemini extraction
        ↓
UNVERIFIED DRAFT
        ↓
human verification
        ↓
canonical deterministic ingestion
```

The detector cannot consume unverified extraction output.

Evaluation includes ambiguous/incorrect extraction cases.

---

## 14. Long-Running Canonical Truth

Firestore/application state is authoritative for:

- incident/source facts;
- isolate/AST data;
- clarifications/provenance;
- package versions;
- review decisions;
- action/acknowledgement state;
- audit history;
- source-data/version watermarks.

ADK session/checkpoint state and compacted context are **execution continuity**, not factual authority.

After resume/long wait:

1. restore/recover execution state where safe;
2. reload current canonical incident state;
3. rebuild bounded reasoning context;
4. resume only safe/idempotent work.

Old session text conflicting with current canonical state must lose to canonical state.

---

## 15. Pre-Action Freshness Safety Barrier

Human approval applies to the reviewed package/incident/source-data version.

Immediately before external action, deterministic application logic checks at least:

- current incident version;
- current package version;
- source-data watermark/revision;
- material new/changed isolate or AST facts;
- material clarification/evidence changes;
- legal action state;
- review references to current package/state.

```text
APPROVED
   ↓
freshness check
   ├─ PASS → authorized action
   └─ MATERIAL CHANGE → do not act → mark approval stale → re-review
```

Gemini may contextualize a detected change later; it does not decide whether the version mismatch exists.

---

## 16. Privacy / Telemetry

Hackathon v0.1 uses synthetic data only, but telemetry should model future health-data sensitivity.

Rules:

- metadata-first structured logs/traces;
- no secrets/tokens in logs;
- no unbounded raw upload logging;
- no default full prompt/response capture;
- no hidden chain-of-thought in logs/UI;
- tracing failure must not alter domain behavior;
- document any synthetic-content tracing enabled solely for demo debugging.

Future real deployment requires separate identity/RBAC, tenancy, retention, encryption, residency, legal/regulatory and clinical-governance work.

---

# Part C — Evaluation

## 17. Evaluation Layers

### Layer 1 — Domain/unit

Pure deterministic tests for parser/normalizer, AST mappings, similarity, baseline, windows, scoring, state policy, material-change policy and validation.

### Layer 2 — Application workflow

Use fakes/in-memory ports for investigation startup, review, clarification, freshness, action gating, acknowledgement, retry/resume and duplicate-event policy.

### Layer 3 — Scenario benchmark

Synthetic full-dataset cases with expected detector/workflow outcomes.

### Layer 4 — Function-node / graph tests

Verify deterministic nodes, typed failures, fan-out completion-order independence, join semantics and fixed-router behavior.

### Layer 5 — ADK agent evaluations

Evaluate structured result and **observable trajectory/capability behavior**, never hidden chain-of-thought.

### Layer 6 — Infrastructure/contract tests

Firestore, Pub/Sub, Cloud Storage, notification, evidence retrieval, model/runtime boundaries.

### Layer 7 — Deployed end-to-end

```text
upload/data arrival
→ deterministic signal
→ Pub/Sub
→ ADK graph start
→ deterministic fan-out/join
→ Gemini triage
→ evidence
→ clarification
→ same-incident resume
→ Gemini synthesis
→ deterministic package validation
→ human review
→ deterministic freshness check
→ real authorized action
→ acknowledgement
```

### Layer 8 — Operational utility

Use `docs/OPERATIONAL_UTILITY_EVALUATION.md` to compare human steps/handoffs and deployed latency against a documented scripted reference workflow.

---

## 18. Detector Metrics

Track:

- seeded scenarios detected;
- false alerts on curated baseline scenarios;
- latency;
- deterministic reproducibility.

Any target such as “100% seeded scenarios / 0 baseline false alerts” is a **committed synthetic software benchmark**, not clinical sensitivity/specificity.

---

## 19. Agent Output Metrics

### Citation integrity
All cited source IDs exist in retrieved approved evidence.

### Referential integrity
All isolate IDs/source IDs referenced in output exist in canonical/retrieved data.

### Unsupported/prohibited claims
Target zero prohibited unsupported clinical claims in committed benchmark.

### Clarification quality
Question is genuinely missing, materially relevant and does not guess.

### Package completeness
Final package passes deterministic schema/content validation.

---

## 20. Graph / Trajectory Assertions

Evaluate whether:

- mandatory deterministic nodes execute;
- fixed routing invokes zero Gemini calls;
- parallel branches can complete in any order without semantic change;
- required branch failure remains visible;
- agentic routing selects only allow-listed bounded capabilities;
- clarification is requested only when needed;
- no-evidence state is handled explicitly;
- model/tool loops respect budgets;
- synthesis cannot hide failed required data;
- package validation runs before review.

Record model/function/tool counts as engineering regression metrics.

---

## 21. Resumability / Idempotency Tests

### Process/agent interruption

- interrupt after one or more completed steps;
- recover/resume or safely restart according to supported runtime;
- verify canonical incident state remains correct;
- rebuild current context;
- verify no duplicate consequential effect.

### Pub/Sub redelivery

Deliver same event multiple times; exactly one intended incident/effect is created.

### Notification retry

Retry transient failure with same idempotency key; no ambiguous duplicate delivery record.

### Context truth

Make old ADK/session text conflict with updated canonical state; canonical state must win.

---

## 22. Freshness Tests — Required

- approval + no material change → action permitted;
- approval + new material isolate → action blocked;
- approval + changed AST fact → action blocked;
- approval + regenerated package version → action blocked;
- material human clarification after review → action blocked;
- telemetry-only/non-semantic change → approval remains valid;
- stale approval cannot be replayed after retry/redelivery;
- blocked freshness check creates visible re-review/audit state;
- no `NOTIFICATION_SENT` state is emitted when freshness blocks action.

---

## 23. Evidence Retrieval Metrics

If EmbeddingGemma is implemented:

- committed query set;
- expected relevant source IDs/chunks;
- retrieval recall@k or scenario-level hit rate;
- latency;
- deterministic/repeatable ranking after embeddings are fixed;
- source integrity;
- irrelevant-high-similarity adversarial case.

Do not claim improvement without measured retrieval evidence.

---

## 24. MedGemma Evaluation Gate

Compare:

```text
baseline: retrieved evidence → Gemini
candidate: retrieved evidence → MedGemma bounded interpretation → Gemini
```

Keep MedGemma only if measured benefit is clear (e.g. structure/source-grounding/readability) without unacceptable safety, latency, deployment or traceability cost.

---

## 25. Operational Utility Metrics — Required

Report from real runs:

```text
signal_to_review_ready_ms
human_intervention_count
human_active_steps
clarification_count
manual_prompt_count_to_start
evidence_searches_completed_by_system
signal_to_action_ready_ms
action_to_ack_ms
model_call_count
deterministic_node_count
```

The canonical Taskmaster path requires zero user prompts to start.

If manual reference timing is not credible, report step/handoff comparison instead of invented time-saved percentages.

---

## 26. Safety / Adversarial Test Set

Explicit tests include:

- autonomous prescribing request;
- autonomous outbreak-confirmation request;
- fabricated source attempt;
- hallucinated isolate ID;
- CSV prompt injection;
- empty evidence;
- malformed required branch/tool result;
- duplicate event;
- repeated notification;
- model timeout/loop exhaustion;
- resume/recovery;
- old session context conflicting with current Firestore state;
- stale approval replay;
- EmbeddingGemma irrelevant-high-similarity result if implemented;
- MedGemma uncited-claim attempt if implemented;
- multimodal unverified-draft leakage if implemented.

---

## 27. End-to-End Acceptance Test

Given the seeded synthetic scenario:

1. import/arrival succeeds;
2. expected rows normalize;
3. expected suspicious signal appears;
4. incident is created exactly once;
5. Pub/Sub starts the ADK graph without user prompt;
6. context function node loads canonical data;
7. required deterministic branches fan out and join;
8. fixed routing uses no Gemini call;
9. Gemini triage uses joined findings;
10. intended clarification is requested;
11. answer resumes the same incident;
12. approved evidence is retrieved;
13. synthesis returns a structured package;
14. deterministic package validation passes;
15. human review is required;
16. approval is version-scoped;
17. freshness check passes for unchanged canonical demo path;
18. exactly one real authorized action occurs;
19. delivery result is persisted;
20. acknowledgement closes the loop;
21. audit/log/trace state correlates major steps;
22. restart/redelivery cannot duplicate side effects.

Also run a variant where data changes after review and prove the old approval is blocked.

---

## 28. Repeated Hosted Demo Test

Before demo freeze, run the full hosted canonical scenario **three consecutive times**.

Record:

- success/failure;
- deployed commit/version;
- total duration;
- signal-to-review-ready time;
- graph branch/join timing;
- model/function/tool counts;
- clarification count;
- notification result;
- acknowledgement;
- retries/resumes;
- freshness result.

Do not discard failed runs from the engineering record.

---

## 29. `EVALUATION.md` Submission Artifact

Before submission create public `EVALUATION.md` containing:

- synthetic dataset/scenario description;
- detector method/configuration;
- scenario counts/results;
- graph/function-node evaluation;
- ADK observable trajectory methodology;
- safety/adversarial tests;
- resumability/idempotency/context tests;
- freshness-barrier tests;
- operational-utility before-vs-after methodology/results;
- EmbeddingGemma retrieval evaluation if integrated;
- MedGemma comparison if integrated;
- deployed E2E results including three consecutive runs;
- exact model/framework versions;
- deployed commit/version;
- known limitations;
- explicit non-clinical-validation statement.

---

## 30. Claim Discipline

Allowed only when measured:

- software benchmark results on committed synthetic scenarios;
- operational step/time results from documented protocol;
- model/retrieval/eval results actually executed;
- hosted reliability results actually observed.

Never convert these into unsupported claims about hospital outcomes, clinical sensitivity/specificity, Uganda-wide impact or patient benefit.

Cross-check final claims against `docs/SUBMISSION_EVIDENCE.md` before Devpost freeze.
