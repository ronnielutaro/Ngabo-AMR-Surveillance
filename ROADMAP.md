# Ngabo Product & Release Roadmap

Ngabo is an **open-source, event-driven antimicrobial resistance surveillance and incident-response system** that transforms AMR surveillance signals into structured, evidence-backed investigations and coordinated response workflows.

Release labels describe maturity, not permanent product identity.

> Roadmap stages are not claims of clinical validation, regulatory approval, or suitability for patient-care decisions.

---

## 1. Release Ladder

```text
0.1.x  Hackathon MVP
       synthetic data
       zero-human safe coordination hero
       complete event→action→ack workflow

0.2.x  Technical Prototype
       reliability/evaluation hardening
       broader failure scenarios
       domain-expert feedback

0.3.x  Research Prototype
       approved retrospective real-world datasets
       stronger surveillance research evaluation
       reproducibility

0.4.x  Shadow-Mode Pilot
       facility workflow integration
       no autonomous clinical/official authority
       prospective shadow evaluation

0.5.x  Validation & Pilot Hardening
       prospective evaluation
       governance/security/interoperability
       explicit operational action policies

0.9.x  Production Candidate
       stable interfaces
       deployment/security hardening
       documented governance model

1.0.0  Production-Ready Release
       validated intended-use boundaries
       stable public contracts
       security/governance/integration baseline
```

---

## 2. v0.1.x — Hackathon MVP

### Goal

Prove:

> **A suspicious synthetic AMR surveillance signal can trigger an autonomous evidence-backed investigation and safe external coordination workflow that completes from event to machine acknowledgement with zero human intervention.**

### Required capabilities

- synthetic WHONET-style ingestion;
- deterministic schema validation/normalization;
- deterministic resistance-pattern surveillance;
- persisted incident/canonical state;
- Pub/Sub trigger;
- Google ADK + Gemini bounded workflow;
- deterministic parallel profile/baseline/missingness analysis;
- approved evidence retrieval;
- structured incident package;
- deterministic package validation;
- bounded automatic model-output repair;
- deterministic A0/A1/A2/A3 action policy;
- autonomous A1 safe external coordination;
- pre-action freshness;
- idempotent external delivery;
- machine acknowledgement;
- audit/observability;
- Next.js incident/autonomy console;
- Google Cloud deployment;
- public evaluation/operational utility evidence.

### Hero requirements

```text
0 prompts
0 human interventions
0 clarifications
0 approval clicks
1 real authorized A1 external effect
1 machine acknowledgement
```

### Safety exclusions

v0.1 does not autonomously:

- diagnose;
- prescribe/start/stop treatment;
- confirm/declare an outbreak;
- execute A2 real operational escalation by default;
- execute A3 clinical/official public-health decisions;
- contact real hospitals/patients/persons without explicit authorization.

Material missing data or unsafe action class causes autonomous abstention.

### Optional post-core

- EmbeddingGemma semantic approved-corpus retrieval;
- MedGemma only if evaluation proves benefit;
- multimodal AST/PDF extraction as human-verified draft;
- scheduled follow-up.

### Initial release

Target: **`v0.1.0`**

---

## 3. v0.2.x — Technical Prototype

Focus:

- expand scenario/evaluation suite;
- stronger fault injection/recovery;
- domain-expert workflow feedback;
- operational policy configuration;
- richer source/evidence governance;
- performance/cost tuning;
- optional specialist capabilities only if evaluation warrants.

Still no production clinical authority.

---

## 4. v0.3.x — Research Prototype

Potential:

- approved retrospective datasets;
- compare detector/incident workflow against research baselines;
- domain-expert review of packages;
- publish reproducible evaluation;
- deepen phenotype/genotype architecture planning;
- introduce genomics only with validated bioinformatics tooling.

Do not label as clinically validated merely because real datasets are used.

---

## 5. v0.4.x — Shadow-Mode Pilot

Potential partner/facility deployment where Ngabo observes real workflows **without autonomous operational authority**.

Goals:

- integration with real systems where authorized;
- RBAC/tenancy/data governance;
- measure alert/package quality;
- compare timing/workflow friction;
- capture human review outcomes;
- no patient-care or official outbreak action directly controlled by Ngabo.

---

## 6. v0.5.x — Validation & Pilot Hardening

Focus:

- prospective evaluation;
- institution-owned action policy;
- governance/approval/audit controls;
- security testing;
- interoperability;
- retention/data residency;
- operational SLOs;
- failure/recovery drills.

Any expansion beyond A1 autonomy requires evidence and institutional authorization.

---

## 7. v0.9.x — Production Candidate

Requirements include:

- stable APIs/contracts;
- migration strategy;
- mature observability/security;
- explicit intended-use/action boundaries;
- deployment runbooks;
- validated integrations;
- governance ownership;
- release rollback/recovery.

---

## 8. v1.0.0 — Production-Ready

`1.0.0` is earned only when the intended deployment context has sufficient validation, security, governance and operational maturity.

It is not automatically created because the hackathon ends or a demo succeeds.

---

## 9. Long-Term DeepTech Direction

Possible research progression:

```text
phenotypic AMR surveillance
→ stronger epidemiological models
→ pathogen genomic analysis
→ resistance-gene/mutation detection via validated bioinformatics tools
→ phenotype/genotype fusion
→ outbreak-risk/pattern models
→ African AMR dataset research
→ prospective validation
```

Potential tools such as AMRFinderPlus/CARD/ResFinder remain future validated bioinformatics capabilities; raw sequence should not be handed to a general LLM as the source of genomic truth.

---

## 10. Governance Principle

Autonomy expands by **action class and evidence**, not by model confidence alone.

The hackathon proves a zero-human **safe coordination** lane. It does not establish that unrestricted clinical/public-health decisions should be autonomous.
