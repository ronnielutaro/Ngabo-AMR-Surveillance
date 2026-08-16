# Ngabo — Hackathon Submission Evidence Matrix

**Status:** Required v0.1 submission-proof contract  
**Date:** 2026-08-16  
**Hackathon:** All Things Agentic Hackathon 2026  
**Primary category:** The Taskmaster

---

## 1. Purpose

Architecture documents describe intent. Judges score the submitted project, repository, text, images, video, and any working build they inspect.

This document converts every important contest claim into a required piece of evidence.

> **Nothing in a design document counts as proof until the implementation, artifact, trace, screenshot, video segment, or evaluation result exists.**

---

## 2. Stage-One Submission Gate

Before final submission, verify:

- [ ] project is entered in one category: **The Taskmaster**;
- [ ] submitted implementation was created during the contest period, with any non-standard pre-existing work disclosed;
- [ ] Gemini 3.5+ requirement is satisfied by the actually deployed model;
- [ ] Google Agent Framework requirement is satisfied by the actually running Google ADK integration;
- [ ] Google Cloud infrastructure requirement is visibly satisfied;
- [ ] repository URL is public or required judge access is configured;
- [ ] README contains reproducible local/deployment spin-up instructions;
- [ ] architecture diagram exists and matches the deployed system;
- [ ] hosted URL is included if available and remains judge-accessible through the judging period;
- [ ] demo video is public on YouTube/Vimeo, English or English-subtitled, and <=4 minutes;
- [ ] video demonstrates the backend running on Google Cloud;
- [ ] project description lists features, technologies, data sources, findings/learnings, and limitations truthfully;
- [ ] third-party usage and pre-existing-work disclosure are complete;
- [ ] no unimplemented feature/model/deployment appears in submission claims.

---

## 3. Core Evidence Inventory

| Evidence item | Required proof | Location / URL | Status |
|---|---|---|---|
| Hosted Ngabo app | Working judge-accessible URL | `TBD` | PENDING |
| Public repository | GitHub repo URL | repository root | EXISTS |
| Spin-up instructions | Reproducible README section | `README.md` | PENDING final implementation update |
| Architecture diagram | Deployed runtime + Clean Architecture + human boundary | `TBD` | PENDING |
| Demo video | <=4 min public YouTube/Vimeo | `TBD` | PENDING |
| Cloud proof | Cloud Run URL/dashboard/logs/traces visible in video | `TBD` | PENDING |
| Evaluation artifact | Real measured results | `EVALUATION.md` | PENDING |
| Operational utility evidence | Before-vs-after scripted benchmark | `EVALUATION.md` + `docs/OPERATIONAL_UTILITY_EVALUATION.md` | PENDING execution |
| Third-party provenance | Dependency/data/source/usage register | `docs/THIRD_PARTY_PROVENANCE.md` | CONTRACT EXISTS; verification pending |
| Pre-existing work disclosure | Submission-period provenance | `docs/THIRD_PARTY_PROVENANCE.md` + Devpost text | PENDING freeze |
| Real action proof | Authorized external delivery + persisted result | UI/video/logs | PENDING |
| Acknowledgement proof | External completion/ack state returns to Ngabo | UI/video/logs | PENDING |
| Resume proof | Same incident pauses/resumes or controlled recovery evidence | UI/eval/logs | PENDING |
| Freshness proof | Pre-action revalidation passes or stale approval blocks correctly | eval/logs; optional video | PENDING |

Statuses must be updated from actual artifacts only.

---

## 4. Innovation & Operational Utility (40%) Evidence

The submission must prove the system removes workflow friction rather than merely generating text.

### Required demonstration

```text
surveillance signal
→ automatic Pub/Sub trigger
→ ADK graph starts without user prompt
→ deterministic investigation work executes
→ bounded Gemini reasoning
→ evidence retrieval
→ targeted clarification only if needed
→ same incident resumes
→ validated review-ready package
→ professional review
→ freshness revalidation
→ authorized external action
→ acknowledgement
```

### Required measured evidence

From `docs/OPERATIONAL_UTILITY_EVALUATION.md`:

- [ ] zero manual prompts required to start investigation;
- [ ] human intervention count measured;
- [ ] human active steps measured against scripted reference workflow;
- [ ] signal-to-review-ready latency measured on deployed runs;
- [ ] clarification count measured;
- [ ] model/function/tool trajectory counts measured;
- [ ] no hospital/clinical time-saving claim made without real evidence.

### Taskmaster wording rule

Preferred submission framing:

> Ngabo autonomously performs the surveillance-to-investigation coordination work. A human supplies a material missing fact only when necessary and retains authority at the consequential public-health action boundary; the human does not manually drive the investigation.

Avoid framing the safety gate as evidence that the workflow is manually guided.

---

## 5. Architectural Discipline & Tech Stack (30%) Evidence

Judges should be able to answer these questions from the repository/diagram/demo.

| Judge question | Ngabo evidence |
|---|---|
| How are systems decoupled? | Clean Architecture dependency diagram + ports/adapters |
| Who owns truth? | Firestore/application state vs non-authoritative ADK session/context |
| Why use an LLM here? | Deterministic-vs-agentic orchestration rule |
| How are fixed workflows handled? | ADK graph with deterministic function nodes and routers |
| How is parallel work coordinated? | Fan-out/join graph + branch telemetry/tests |
| What happens on duplicate events? | Idempotency persistence/test |
| What happens if process/model/tool fails? | Resume/recovery + visible typed failure semantics |
| What happens if a required branch fails? | Join rejects/degrades visibly; Gemini cannot hide failure |
| How are model/tool loops bounded? | Model/tool/time/retry budgets + ADK evals |
| How are tools scoped? | Inward application ports, no arbitrary DB/shell/web access |
| How is long-running context controlled? | Context reconstruction/compaction policy |
| What if model memory conflicts with current data? | Canonical Firestore/application truth wins |
| What if data changes after approval? | Deterministic pre-action freshness barrier |
| What prevents unsafe notification? | Human application/domain gate + freshness check + NotificationPort |
| What proves the architecture works? | Deployed E2E, logs/traces, public evaluation |

### Required architecture diagram layers

The final visual must show at minimum:

```text
Browser
  ↓
Cloud Run: ngabo-web
  ↓
Cloud Run: ngabo-core
  ├─ deterministic AMR/domain/application core
  ├─ Google ADK graph runtime
  │    ├─ deterministic function nodes
  │    ├─ parallel fan-out/join
  │    └─ Gemini agent nodes
  ├─ EvidenceSearchPort → EmbeddingGemma only if implemented
  ├─ optional MedGemma only if implemented
  └─ NotificationPort → authorized external target

Pub/Sub → ngabo-core event interface
Firestore ↔ application persistence
Cloud Storage ↔ artifact adapters
Cloud Logging/Trace ← safe telemetry

WAITING_FOR_REVIEW
      ↓ HUMAN AUTHORITY BOUNDARY
APPROVED
      ↓ deterministic freshness barrier
AUTHORIZED ACTION
```

---

## 6. Demo & Production Readiness (30%) Evidence

The demo must show live state change rather than only slides/mockups.

### Required proof sequence

1. show working Ngabo UI;
2. introduce synthetic data/signal;
3. show automatic event-triggered investigation;
4. show graph/node activity including fan-out/join;
5. show evidence/clarification;
6. answer clarification and show same incident resume;
7. show validated package;
8. approve through the professional safety gate;
9. show freshness check in UI/logs if legible;
10. show real authorized action outside Ngabo;
11. show acknowledgement/state update;
12. show Cloud Run / Google Cloud proof;
13. show architecture/evaluation proof briefly.

### Proof-of-action rule

At least one key workflow should be shown in a continuous, unedited live execution segment. Do not rely only on screenshots of a previously completed run.

### Reproducibility rule

Before submission:

- [ ] README commands tested from a clean environment where practical;
- [ ] required environment variables documented without secrets;
- [ ] synthetic seed/reset path documented;
- [ ] exact model/framework versions recorded;
- [ ] three consecutive hosted E2E runs completed successfully before demo freeze;
- [ ] deployed commit SHA recorded.

---

## 7. Prize Positioning Evidence

### Taskmaster — primary

Must prove:

- [ ] event-driven autonomous start;
- [ ] complete multi-step workflow;
- [ ] system performs heavy lifting without step-by-step human guidance;
- [ ] action occurs outside the UI after approval;
- [ ] acknowledgement closes loop.

### Best Architectural Design — deliberate secondary target

Must make visible:

- [ ] decoupling;
- [ ] state boundaries;
- [ ] deterministic/agentic separation;
- [ ] graph orchestration;
- [ ] scoped tools;
- [ ] failure handling;
- [ ] idempotency;
- [ ] resumability;
- [ ] context/memory discipline;
- [ ] freshness barrier;
- [ ] observability/evaluation.

### Individual/Hobbyist

Eligibility depends on final entrant/team structure. No architecture change is required; ensure Devpost participant structure is accurate.

### Startup Excellence

Only pursue if the final submission is made on behalf of an eligible incorporated organization and the required corporate email/other eligibility conditions are satisfied. Do not alter the technical narrative merely to chase this prize.

### Best Multimodal UX — optional stretch

Claim only if implemented and polished:

```text
image/PDF AST report
→ AI-extracted UNVERIFIED DRAFT
→ human verification
→ canonical deterministic ingestion
```

Do not allow unverified extraction into surveillance calculations.

---

## 8. Bonus Evidence

### Public build content (+0.2 max)

- [ ] public article/content exists;
- [ ] contains required statement that it was created for purposes of entering the hackathon;
- [ ] explains real implementation, trade-offs, evaluation, and learnings;
- [ ] URL entered in submission where appropriate.

### Social post (+0.2 max)

- [ ] public post exists;
- [ ] uses exact hashtag `#AllThingsAgenticHackathon`;
- [ ] URL captured.

### Additional Google AI models (+0.2 each, max +0.6)

For each claimed model:

- [ ] real code integration exists;
- [ ] model executes in tested/submitted path;
- [ ] role materially contributes to product;
- [ ] evaluation exists;
- [ ] architecture diagram/doc reflects it;
- [ ] video/submission claim is truthful;
- [ ] usage terms/license recorded in provenance register.

EmbeddingGemma is planned after core green. MedGemma remains gated. Do not add a third model solely for points.

---

## 9. Human Safety Gate Narrative

This distinction must be consistent across README, Devpost text, diagram and video:

```text
HUMAN DOES NOT:
- prompt the investigation to start
- select mandatory calculations
- manually route every workflow step
- write the incident package
- send the approved notification manually

HUMAN DOES:
- provide a materially missing fact when asked
- review consequential escalation/action
- retain outbreak-confirmation and treatment authority
```

Therefore the safety boundary does not weaken the Taskmaster claim. It defines where autonomy should stop.

---

## 10. Submission-Period / Ownership Evidence

Before final submission:

- [ ] verify commit history supports the contest-period build claim;
- [ ] list any pre-existing non-standard work actually incorporated;
- [ ] list third-party SDKs/APIs/data/information and usage basis;
- [ ] verify synthetic data ownership/provenance;
- [ ] verify approved evidence-corpus rights/provenance;
- [ ] ensure no real patient/laboratory data appears in repo/video/logs;
- [ ] ensure third-party logos/media do not imply sponsorship or violate rights.

See `docs/THIRD_PARTY_PROVENANCE.md`.

---

## 11. Final Claim Ledger

Before locking Devpost copy, create a final table in this file or `EVALUATION.md`:

| Claim | Implemented? | Evidence location | Allowed in submission? |
|---|---|---|---|
| Event-triggered autonomous start | TBD | TBD | only if yes |
| Graph fan-out/join | TBD | TBD | only if yes |
| Resume same incident | TBD | TBD | only if yes |
| Real authorized action | TBD | TBD | only if yes |
| Freshness barrier | TBD | TBD | only if yes |
| EmbeddingGemma | TBD | TBD | only if yes |
| MedGemma | TBD | TBD | only if yes |
| Multimodal AST draft | TBD | TBD | only if yes |
| Operational utility result | TBD | TBD | only after measured |

Anything marked `no` or `TBD` at submission freeze must be removed from competitive claims unless clearly labelled future work.

---

## 12. Freeze Checklist

Submission evidence is ready only when:

- [ ] Stage-One gate is complete;
- [ ] every implemented competitive claim has a proof location;
- [ ] every unimplemented claim is removed/labelled future;
- [ ] hosted project works from judge-accessible environment;
- [ ] architecture diagram matches deployed runtime;
- [ ] `EVALUATION.md` reports measured results;
- [ ] provenance/disclosure register is complete;
- [ ] public content/social/model bonuses have actual URLs/evidence if claimed;
- [ ] demo remains <=4 minutes;
- [ ] judge availability remains enabled through judging period.
