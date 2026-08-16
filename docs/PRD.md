# Ngabo — Product Requirements Document (PRD)

**Version:** 0.1  
**Date:** 2026-08-16  
**Status:** Hackathon MVP baseline  
**Primary track:** All Things Agentic Hackathon — The Taskmaster

## 1. Product Summary

Ngabo is an open-source, agentic antimicrobial-resistance (AMR) incident-response system.

It ingests representative WHONET-style microbiology and antimicrobial-susceptibility data, validates and normalizes it deterministically, detects suspicious resistance patterns using transparent statistical/rule-based logic, and launches an autonomous investigation workflow.

The agent gathers context and approved evidence, identifies missing information, asks a targeted clarification question when necessary, prepares an evidence-backed incident-response package, routes it through a human safety gate, and coordinates an alert/follow-up workflow.

> **v0.1 promise:** turn a suspicious AMR surveillance signal into an evidence-backed, human-reviewable incident package through a safe, event-driven workflow.

## 2. Primary User

**Hero user:** hospital microbiologist / AMR surveillance officer.

Job to be done:

> “When unusual resistance patterns appear in our laboratory data, help me determine what deserves investigation, assemble the evidence, identify what is missing, and prepare a structured incident package for the team.”

Secondary users:

- Infection Prevention & Control (IPC)
- antimicrobial-stewardship leads
- hospital epidemiologists
- AMR focal persons

## 3. Goals

1. **Event-driven autonomy:** new lab data triggers the workflow without manually prompting a chatbot through each step.
2. **Deterministic scientific logic:** parsing, validation, AST normalization, time windows, similarity calculations, and trigger logic remain reproducible code.
3. **Agentic investigation:** once a signal exists, Ngabo decides which tools/evidence it needs and synthesizes an investigation.
4. **Bounded autonomy:** qualified humans approve clinically consequential actions.
5. **Observable action:** the workflow ends with a package, approval, notification, acknowledgement/follow-up, and audit trail.
6. **Reproducibility:** GitHub, architecture diagram, tests, and setup instructions make the project inspectable and runnable.

## 4. Non-Goals for v0.1

Ngabo will not:

- diagnose patients;
- prescribe antibiotics;
- autonomously confirm an outbreak;
- replace WHONET or NIAMR;
- use real identifiable patient data in the public demo;
- claim clinical validation or regulatory approval;
- require genomics, a vector DB, BigQuery, Kubernetes, or a microservice fleet.

## 5. Primary Workflow

```text
Upload WHONET-style CSV
        ↓
Deterministic validation + normalization
        ↓
Statistical surveillance detector
        ↓
Suspicious signal?
   no ↙        ↘ yes
summary      incident
                ↓
       autonomous investigation
                ↓
       missing context?
         yes ↙   ↘ no
   clarification
         ↓
     resume agent
                ↓
     incident package
                ↓
      human safety gate
        reject / approve
                ↓
       route notification
                ↓
        acknowledgement
                ↓
             closed
```

## 6. Functional Requirements

### FR-001 — Import data
User can upload a CSV representing WHONET-style isolate/AST data.

Acceptance:
- unique import ID;
- immutable raw file stored;
- SHA-256 recorded;
- malformed input fails visibly;
- LLM never silently guesses malformed schema.

### FR-002 — Normalize records
Canonical fields include:
- isolate ID;
- collection date;
- organism;
- ward/location;
- specimen type where present;
- antibiotic result fields;
- normalized S/I/R interpretation.

Acceptance:
- deterministic mappings;
- unknown values flagged, never invented.

### FR-003 — Detect suspicious AMR patterns
MVP dimensions:
- organism;
- ward;
- time window;
- resistance-profile similarity;
- representative baseline frequency.

Acceptance:
- seeded demo signal is reproducible;
- trigger explanation persisted;
- output is an **investigation candidate**, not a confirmed outbreak.

### FR-004 — Create incident
Incident stores:
- signal;
- related isolates;
- priority;
- trigger explanation;
- state;
- evidence;
- timestamps.

### FR-005 — Autonomous investigation
Approved tools:
- `get_incident_context`
- `compare_resistance_profiles`
- `get_baseline_summary`
- `get_missing_fields`
- `search_approved_guidance`
- `request_clarification`
- `prepare_incident_package`

Acceptance:
- every tool call logged;
- deterministic calculations come from tools;
- agent cannot rewrite source facts.

### FR-006 — Clarification loop
Agent can pause at `WAITING_FOR_CLARIFICATION`, ask one targeted question, persist the answer, then resume.

### FR-007 — Incident package
Package includes:
- observed evidence;
- derived findings;
- hypotheses;
- uncertainty;
- missing information;
- source-linked guidance;
- investigation checklist;
- draft escalation message.

### FR-008 — Human safety gate
Reviewer options:
- approve;
- reject;
- request more information.

### FR-009 — Action
After approval, route a real email/webhook if stable; otherwise use an observable deterministic demo notification adapter.

### FR-010 — Audit trail
Append-only timeline records every major import, signal, agent, clarification, review, notification, acknowledgement, error, and retry event.

## 7. Non-Functional Requirements

- **Reproducibility:** same data + detector config → same surveillance result.
- **Traceability:** guidance claims must link to a known source.
- **Failure visibility:** failed tool/agent steps never masquerade as success.
- **Idempotency:** Pub/Sub retries cannot create duplicate incidents/actions.
- **Privacy:** synthetic demo data only.
- **Performance:** 250–1,000 isolate rows process comfortably within demo time.
- **Cost:** serverless components scale to zero where possible.

## 8. UX Requirements

The MVP should feel like an **incident-response console**, not a chatbot.

Core screens/states:

1. Import
2. Surveillance overview
3. Incident timeline
4. Clarification request
5. Evidence-backed incident package
6. Human review
7. Notification/acknowledgement

See `docs/UI_UX_SPEC.md` for the frontend implementation contract.

## 9. Demo Scenario

Representative neonatal-unit data contains several *Klebsiella pneumoniae* isolates with unusually similar resistance phenotypes over a short period. One isolate intentionally lacks a relevant metadata field.

Ngabo should:

1. ingest;
2. normalize;
3. detect;
4. explain signal;
5. launch investigation automatically;
6. retrieve context/evidence;
7. notice missing field;
8. ask one clarification;
9. resume;
10. create incident package;
11. wait for approval;
12. route action;
13. record acknowledgement.

## 10. Definition of Done

Ngabo v0.1 is done when a reviewer can watch a single unedited workflow:

> **synthetic WHONET-style input → detected signal → autonomous investigation → evidence-backed package → human approval → routed action → persisted audit trail**

and every stage is visible in the UI, logs, or database state.
