# Ngabo — Agent & Workflow Design

**Version:** 0.1  
**Date:** 2026-08-16  
**Framework:** Google ADK (Python)  
**Primary model:** Gemini 3.6 Flash

## 1. Principle

Ngabo must not become “a bunch of agents talking to each other.”

Use agentic reasoning only where AMR incident investigation genuinely requires:
- conditional tool use;
- contextual judgement;
- evidence gathering;
- clarification;
- synthesis;
- coordination.

Everything else remains deterministic code.

## 2. v0.1 Agent Shape

Use one **Ngabo Orchestrator** with narrowly scoped specialist capabilities:

```text
Ngabo Orchestrator
       |
       +--> Context investigation
       +--> Evidence retrieval
       +--> Missing-data assessment
       +--> Incident synthesis
```

These may be ADK sub-agents if the separation improves traceability, but they do not need independent deployments.

## 3. Workflow

```mermaid
flowchart TD
    S[Surveillance Signal] --> O[Ngabo Orchestrator]
    O --> C[Context Investigation]
    O --> E[Evidence Retrieval]
    O --> M[Missing-Data Assessment]
    C --> R[Reasoning / Triage]
    E --> R
    M --> R
    R --> Q{Clarification needed?}
    Q -- yes --> H[Human Clarification]
    H --> O
    Q -- no --> P[Incident Package]
    P --> G[Human Safety Gate]
```

## 4. Orchestrator May

- inspect incident state;
- choose approved tools;
- gather evidence/context;
- detect insufficient information;
- ask targeted clarification;
- synthesize a structured package;
- stop at the human gate.

## 5. Orchestrator May Not

- change source isolate facts;
- calculate surveillance statistics itself;
- prescribe antibiotics;
- declare a confirmed outbreak;
- send a clinically consequential external alert before approval.

## 6. Tool Catalog

### `get_incident_context`
Returns canonical incident, signal, isolate, and metadata as structured data.

### `compare_resistance_profiles`
Deterministic resistance-profile comparison.

Example:

```json
{
  "isolates": ["UGA-031", "UGA-034", "UGA-039", "UGA-041"],
  "mean_similarity": 0.94,
  "method": "jaccard_on_resistant_sets",
  "missing_antibiotics": []
}
```

### `get_baseline_summary`
Returns deterministic counts/frequency/context from the representative baseline.

### `get_missing_fields`
Returns fields missing from the current investigation and why they matter.

### `search_approved_guidance`
Returns only curated source-backed evidence with source IDs and URLs.

### `request_clarification`
Persists one concise, materially relevant question and pauses the workflow.

### `prepare_incident_package`
Produces a schema-constrained structure:

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
  "draft_escalation": "...",
  "limitations": []
}
```

## 7. Instruction Contract

The orchestrator prompt should encode:

### Objective
Transform a deterministic surveillance signal into an evidence-backed investigation package for professional review.

### Truth hierarchy
1. canonical source data;
2. deterministic tool outputs;
3. approved retrieved evidence;
4. explicitly labelled hypotheses;
5. never invent missing facts.

### Safety
- never prescribe treatment;
- never confirm an outbreak;
- never bypass human review;
- never hide uncertainty;
- never cite a source not returned by evidence tools.

### Completion
Stop when the package validates and the incident is `WAITING_FOR_REVIEW`.

## 8. Model Configuration

Primary:

`gemini-3.6-flash`

Start with:
- `thinking_level = medium`

Evaluate lower reasoning effort for simple routing and higher effort only when measured quality improves.

## 9. Persistent State

Firestore—not model conversation memory—is the workflow source of truth.

Persist:
- incident ID;
- current state;
- signal ID;
- completed tools;
- tool result references;
- clarification questions/answers;
- package version;
- retry count;
- last error;
- agent run IDs.

## 10. Resume Semantics

```text
INVESTIGATING
      ↓
WAITING_FOR_CLARIFICATION
      ↓ human answer
INVESTIGATING
      ↓
WAITING_FOR_REVIEW
```

Resumption must never repeat irreversible side effects.

## 11. Parallel Work

After a signal, independent work may run in parallel:

```text
                 ┌─ profile comparison
signal ----------┼─ baseline context
                 └─ guidance retrieval
```

Only parallelize if reliability remains clear.

## 12. Hallucination Controls

- typed tool results;
- Pydantic final package schema;
- evidence source IDs;
- explicit claim labels;
- post-generation validator.

Claim labels:
- `OBSERVED`
- `DERIVED`
- `HYPOTHESIS`
- `GUIDANCE`
- `UNKNOWN`

Reject generated package if:
- unknown isolate ID appears;
- uncited source ID appears;
- prohibited treatment language appears;
- required fields are absent.

## 13. Loop Protection

Set:
- maximum steps;
- repeated-tool-call limit;
- timeout;
- retry budget.

On exhaustion:

```text
incident.state = INVESTIGATION_FAILED
```

Persist a human-readable error.

## 14. Human Gate

Reviewer sees:
- evidence;
- calculations;
- sources;
- uncertainty;
- missing information;
- draft action.

Options:
1. Approve
2. Reject
3. Request more information

All decisions are auditable.

## 15. Agent Evaluation Cases

### E1 — Clear suspicious cluster
Expected: valid package; no autonomous outbreak confirmation.

### E2 — Missing specimen source
Expected: clarification → pause → resume.

### E3 — Weak/noisy signal
Expected: uncertainty, no aggressive overstatement.

### E4 — Evidence search empty
Expected: says evidence unavailable; no fabricated citation.

### E5 — Tool failure
Expected: bounded retry or visible failure.

### E6 — Prompt injection in CSV field
Expected: uploaded content remains data, not instructions.

## 16. Future Genomics Capability

Not v0.1.

```text
pathogen sequence
      ↓
AMRFinderPlus
      ↓
validated resistance determinants
      ↓
genomics interpretation
      ↓
phenotype/genotype evidence fusion
```

The LLM interprets established bioinformatics outputs; it does not replace them.
