# Ngabo — Data, Safety & Evaluation Design

**Version:** 0.1  
**Date:** 2026-08-16

## 1. Purpose

Keep the prototype:
- scientifically interpretable;
- auditable;
- reproducible;
- honest about uncertainty;
- safe for a synthetic-data demonstration.

This is **not clinical validation**.

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

Public prototype data is representative and synthetic.

Rules:
- no real patient names;
- no real MRNs;
- no claim that rows came from a named hospital;
- published distributions may inspire scenarios, but real patient rows are not reconstructed.

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
approve consequential escalation
confirm outbreak under appropriate process
make clinical decisions
```

## 9. Prompt-Injection Boundary

Uploaded lab data is **untrusted data**.

Mitigations:
- no raw CSV concatenated directly into system instructions;
- agent receives canonical structured fields;
- free text remains data;
- evidence corpus is curated;
- external arbitrary URLs are not followed during v0.1.

## 10. Source Integrity

Approved evidence records include:
- source ID;
- publisher;
- title;
- URL;
- version/date;
- stored excerpt/reference.

Generated package may cite only source IDs retrieved during the investigation.

## 11. Privacy

Hackathon:
- synthetic data only;
- no real clinical deployment claim.

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

## 12. Four Evaluation Layers

### Layer 1 — Unit tests
- parser;
- normalizer;
- AST mappings;
- similarity;
- baseline;
- time windows;
- scoring;
- state transitions;
- idempotency.

### Layer 2 — Scenario benchmark
Synthetic full-dataset cases with expected detector outcomes.

### Layer 3 — Agent evaluations
ADK eval cases and structured assertions.

### Layer 4 — End-to-end
Upload → signal → agent → clarification → package → approval → notification.

## 13. Detector Metrics

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

## 14. Agent Metrics

### Citation integrity
Retrieved source IDs used correctly / all cited source IDs.

Target: 100%.

### Unsupported claims
Target: zero prohibited unsupported clinical claims in the demo benchmark.

### Clarification quality
Question asks for genuinely missing, relevant information.

### Package completeness
Schema passes validation.

## 15. Safety Tests

Explicit tests for:
- autonomous prescribing language;
- autonomous outbreak-confirmation language;
- fabricated source;
- hallucinated isolate ID;
- CSV prompt injection;
- empty evidence result;
- malformed tool result;
- duplicate event;
- repeated notification.

## 16. End-to-End Acceptance Test

Given seeded demo CSV:

1. import succeeds;
2. expected row count normalizes;
3. one expected suspicious signal appears;
4. incident is created exactly once;
5. agent launches automatically;
6. required tools run;
7. intended clarification is requested;
8. answer resumes workflow;
9. package validates;
10. package has source-backed evidence;
11. human review is required;
12. approval causes one notification;
13. acknowledgement closes loop;
14. audit timeline shows all major steps.

## 17. Devpost Evaluation Artifact

Before submission create `EVALUATION.md` containing:
- dataset description;
- detector method;
- scenario count;
- results;
- safety tests;
- known limitations.

## 18. Public Limitations

State explicitly:
- synthetic data;
- prototype trigger configuration;
- not clinically validated;
- no proof of transmission;
- no genomic relatedness in v0.1;
- evidence corpus may be incomplete;
- real-world interoperability varies by facility.
