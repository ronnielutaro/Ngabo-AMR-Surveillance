# Ngabo — Data, Safety & Evaluation Design

**Version:** 0.2  
**Date:** 2026-08-16

## 1. Purpose

Keep Ngabo v0.1:

- scientifically interpretable;
- auditable;
- reproducible;
- honest about uncertainty;
- safe for a synthetic-data demonstration;
- resilient under asynchronous/resumable agent execution;
- measurable through deterministic, agent, and end-to-end evaluation.

This is **not clinical validation**.

See also:

- `docs/HACKATHON_ALIGNMENT.md`
- `docs/ADK_RUNTIME.md`

# Part A — Data

## 2. Canonical Isolate Schema

Illustrative:

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

## 3. Synthetic Dataset Policy

Public v0.1 data is representative and synthetic.

Rules:

- no real patient names;
- no real MRNs;
- no claim that rows came from a named hospital;
- published distributions may inspire scenarios, but real patient rows are not reconstructed;
- all screenshots, logs, demo artifacts, and committed eval fixtures use synthetic content.

Dataset disclaimer:

> “This dataset is synthetic and intended solely for software demonstration/evaluation. It does not represent real patient records and is not suitable for clinical inference.”

## 4. Scenario Dataset

Create:

### Normal baseline
Routine variation.

### Noise
Missing values, duplicates, unusual but isolated resistance.

### Seeded suspicious cluster
For example:

- *Klebsiella pneumoniae*;
- same neonatal unit;
- narrow time window;
- highly similar resistance phenotype;
- one intentionally missing specimen field.

### Adversarial/untrusted-data case
A free-text field contains instruction-like text intended to manipulate an LLM.

Expected behavior: data remains data; no system/tool instructions are overridden.

## 5. Resistance Representation

For overlapping antibiotics:

```text
S -> 0
I -> 1
R -> 2
UNKNOWN -> excluded from pairwise comparison
```

Preferred MVP similarity:

- exact-category agreement; or
- Jaccard similarity of resistant-antibiotic sets.

Pick one primary method and document it.

## 6. Prototype Signal Score

Possible transparent score:

```text
signal_score =
    w1 * temporal_concentration
  + w2 * location_concentration
  + w3 * phenotype_similarity
  + w4 * baseline_excess
```

Weights are prototype configuration—not clinically validated parameters.

Persist component values with every signal.

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
- “prescribe X”;
- “start/stop this antibiotic”;
- “gene X is present” without validated genomic evidence.

## 8. Human Authority

```text
machine:
ingest
validate
calculate
detect
retrieve
organize
draft
coordinate

human:
provide missing context where needed
approve consequential escalation
confirm outbreak under appropriate process
make clinical decisions
```

Clarification may be agent-orchestrated. Consequential approval remains an authoritative application/domain gate.

## 9. Prompt-Injection Boundary

Uploaded lab data is **untrusted data**.

Mitigations:

- no raw CSV concatenated directly into system instructions;
- agent receives canonical structured fields;
- free text remains data;
- evidence corpus is curated;
- arbitrary external URLs are not followed as approved evidence during v0.1;
- imported instruction-like text is included in adversarial eval cases;
- tool access remains narrowly scoped.

## 10. Source Integrity

Approved evidence records include:

- source ID;
- publisher;
- title;
- URL;
- version/date;
- stored excerpt/reference.

Generated package may cite only source IDs retrieved during the investigation.

Application validation rejects unknown source IDs before a package enters review.

## 11. EmbeddingGemma Evidence Safety

EmbeddingGemma may rank/retrieve only within the approved guidance corpus.

Rules:

- embedding similarity is a retrieval aid, not evidence authority;
- returned chunks preserve source IDs and metadata;
- similarity score is not a clinical confidence score;
- the LLM may summarize only retrieved approved content;
- no arbitrary web corpus is silently mixed into the approved evidence index;
- retrieval quality is evaluated before the bonus integration is claimed.

## 12. Optional MedGemma Safety

MedGemma, if added, is a bounded evidence-interpretation tool over already approved/retrieved material.

It may not:

- prescribe;
- diagnose;
- confirm outbreaks;
- replace deterministic calculations;
- introduce authoritative claims that cannot be traced to approved source IDs.

The integration is omitted if evaluation shows no meaningful benefit or introduces unacceptable overclaiming/deployment risk.

## 13. Multimodal Draft Boundary

If the post-core multimodal stretch is implemented:

```text
image/scanned PDF AST report
        ↓
Gemini extraction
        ↓
DRAFT structured record
        ↓
human verification
        ↓
canonical ingestion
```

Model-extracted fields are never canonical laboratory facts before verification.

Evaluation must include incorrect/ambiguous extraction examples and verify that unconfirmed data cannot enter the canonical detector path.

## 14. Privacy & Telemetry

Hackathon:

- synthetic data only;
- no real clinical deployment claim.

Observability must still model future health-data sensitivity.

Rules:

- structured metadata-first logs/traces;
- do not enable full prompt/response content capture by default;
- no secrets/tokens in logs;
- no unbounded raw uploaded-data logging;
- tracing failure must not change domain behavior;
- document any synthetic-content capture enabled specifically for demo debugging.

Future deployment requires separate work on:

- identity/RBAC;
- retention;
- encryption;
- facility tenancy;
- audit;
- data residency;
- Ugandan legal/regulatory review;
- clinical governance.

# Part C — Evaluation

## 15. Evaluation Layers

### Layer 1 — Domain/unit tests

- parser;
- normalizer;
- AST mappings;
- similarity;
- baseline;
- time windows;
- scoring;
- state transitions;
- idempotency policy.

### Layer 2 — Application workflow tests

Use fakes/in-memory ports to test:

- start investigation;
- clarification pause/resume;
- review gate;
- notification gating;
- retry/resume decisions;
- package validation;
- duplicate-event behavior.

### Layer 3 — Scenario benchmark

Synthetic full-dataset cases with expected detector outcomes.

### Layer 4 — ADK agent evaluations

Evaluate structured result **and trajectory/tool behavior** where supported by the selected ADK/evaluation tooling.

### Layer 5 — Infrastructure/contract tests

- Firestore adapter;
- Pub/Sub adapter;
- Cloud Storage adapter;
- evidence retrieval adapter;
- notification adapters;
- model/agent boundary contracts where practical.

### Layer 6 — End-to-end deployed test

```text
upload
 -> deterministic signal
 -> Pub/Sub
 -> agent
 -> clarification
 -> resume
 -> package
 -> approval
 -> real notification
 -> acknowledgement
```

## 16. Detector Metrics

Track:

- seeded scenarios detected;
- false alerts on curated baseline scenarios;
- latency;
- reproducibility.

Example hackathon target:

```text
seeded scenarios detected: 100%
baseline false alerts: 0 in curated demo benchmark
```

This is a software benchmark, not a clinical sensitivity/specificity claim.

## 17. Agent Output Metrics

### Citation integrity

Retrieved source IDs used correctly / all cited source IDs.

Target: 100% in committed demo/eval benchmark.

### Unsupported claims

Target: zero prohibited unsupported clinical claims in committed benchmark.

### Clarification quality

Question asks for genuinely missing, materially relevant information and does not guess.

### Package completeness

Schema passes application validation.

### Referential integrity

All isolate IDs/source IDs in generated output exist in canonical/retrieved data.

Target: 100% in committed benchmark.

## 18. Agent Trajectory Metrics / Assertions

Where supported, evaluate whether the agent:

- invokes required deterministic tools;
- avoids prohibited/unnecessary tools;
- asks clarification when required;
- does not ask clarification when data is sufficient;
- stops after a valid package;
- handles no-evidence state correctly;
- avoids repeated tool loops;
- remains within configured step/tool budgets.

Do not score private chain-of-thought. Evaluate observable tool/action trajectory.

## 19. Resumability & Idempotency Tests

Explicitly test:

### Agent interruption

- start investigation;
- interrupt/fail after one or more tool calls;
- resume through the supported ADK/application recovery path;
- verify canonical incident state remains correct;
- verify no duplicate consequential action.

### Pub/Sub redelivery

- deliver same event more than once;
- exactly one incident/effect is created.

### Notification retry

- simulate transient send failure;
- retry with same idempotency key;
- verify no ambiguous duplicate delivery record.

## 20. Evidence Retrieval Metrics

For the EmbeddingGemma adapter:

- committed query set;
- expected relevant source IDs/chunks;
- retrieval recall@k or simple scenario-level hit rate;
- latency;
- deterministic/repeatable post-embedding ranking;
- source integrity.

Do not claim EmbeddingGemma improved the system without measured retrieval evidence.

## 21. MedGemma Evaluation Gate

If MedGemma is considered, compare a baseline (Gemini using retrieved evidence directly) against a candidate pipeline that includes MedGemma.

Accept the stretch integration only if it provides a clear benefit such as:

- better structured interpretation;
- fewer unsupported claims;
- better source-grounding;
- improved domain-expert readability;

without degrading:

- safety;
- latency beyond demo tolerance;
- deployment reliability;
- traceability.

Otherwise omit it.

## 22. Safety Tests

Explicit tests for:

- autonomous prescribing language;
- autonomous outbreak-confirmation language;
- fabricated source;
- hallucinated isolate ID;
- CSV prompt injection;
- empty evidence result;
- malformed tool result;
- duplicate event;
- repeated notification;
- agent timeout/loop exhaustion;
- resume/recovery;
- EmbeddingGemma result with irrelevant-but-high-similarity chunk;
- MedGemma uncited-claim attempt if MedGemma is implemented;
- multimodal unverified-draft leakage if multimodal is implemented.

## 23. End-to-End Acceptance Test

Given seeded demo CSV:

1. import succeeds;
2. expected row count normalizes;
3. one expected suspicious signal appears;
4. incident is created exactly once;
5. agent launches automatically from event flow;
6. required tools run;
7. intended clarification is requested;
8. answer resumes the same incident;
9. package validates;
10. package has source-backed evidence;
11. human review is required;
12. approval causes exactly one real authorized notification/action;
13. delivery result is persisted;
14. acknowledgement closes loop;
15. audit timeline shows all major steps;
16. logs/traces correlate incident/event/agent/tool execution;
17. restart/redelivery does not duplicate side effects.

## 24. Repeated Deployed Demo Test

Before demo freeze, run the full hosted scenario **three consecutive times** with expected outcomes.

Record:

- success/failure;
- total duration;
- agent/tool latency;
- notification result;
- any retries/resumes;
- relevant deployed version/commit.

Only after three consecutive successful runs should the demo candidate be frozen.

## 25. `EVALUATION.md` Submission Artifact

Before submission create public `EVALUATION.md` containing:

- synthetic dataset description;
- detector method/configuration;
- scenario counts;
- detector results;
- ADK agent eval methodology;
- observable trajectory assertions;
- safety/adversarial tests;
- resumability/idempotency tests;
- EmbeddingGemma retrieval evaluation if integrated;
- MedGemma comparison if integrated;
- end-to-end results;
- model/framework versions;
- known limitations.

Never present software benchmark metrics as clinical validation.

## 26. Public Limitations

State explicitly:

- synthetic data;
- prototype trigger configuration;
- not clinically validated;
- no proof of transmission;
- no genomic relatedness in core v0.1;
- evidence corpus may be incomplete;
- EmbeddingGemma ranking is retrieval assistance, not medical authority;
- MedGemma is included only if actually implemented/evaluated;
- multimodal extraction, if present, produces human-verified drafts;
- real-world interoperability varies by facility.
