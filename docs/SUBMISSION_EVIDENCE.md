# Ngabo — Hackathon Submission Evidence Matrix

**Status:** Required v0.1 submission-proof contract  
**Version:** 0.3  
**Date:** 2026-08-17  
**Hackathon:** All Things Agentic Hackathon 2026  
**Primary category:** The Taskmaster

---

## 1. Principle

> **Nothing in a design document counts as proof until the implementation, artifact, trace, screenshot, video segment, or evaluation result exists.**

The canonical Taskmaster claim is:

> **Ngabo completes the hero surveillance-to-safe-coordination workflow from event to machine acknowledgement with zero human intervention.**

The differentiating competition claim is:

> **The Twist is Proof-Carrying Autonomy: Ngabo does not trust fluent model output on faith; action-relevant LLM claims must carry machine-checkable references to canonical records, deterministic findings, and/or approved evidence before they can influence autonomous action.**

Neither claim may appear as an implemented fact in submission materials until deployed evidence proves it.

---

## 2. Stage-One Gate

Before submission verify:

- [ ] project entered in one category: **The Taskmaster**;
- [ ] submitted implementation built during contest period, with required pre-existing-work disclosure;
- [ ] deployed Gemini version satisfies 3.5+ rule;
- [ ] Google ADK actually used as agent runtime;
- [ ] Google Cloud infrastructure actually used;
- [ ] repo/test access available;
- [ ] README contains tested spin-up/deployment instructions;
- [ ] judge-facing architecture diagram exists and matches deployment;
- [ ] hosted project URL included if available and remains free/judge-accessible;
- [ ] public YouTube/Vimeo video <=4 minutes and English/English-subtitled;
- [ ] video visibly proves Google Cloud backend;
- [ ] description lists actual features, technologies, data sources, findings/learnings, and limitations;
- [ ] third-party/provenance/pre-existing-work checks complete;
- [ ] no unimplemented model/feature is claimed;
- [ ] Proof-Carrying Autonomy described only if claim verifier/evals actually exist.

---

## 3. Core Evidence Inventory

| Evidence | Proof required | Location | Status |
|---|---|---|---|
| Hosted Ngabo | Judge-accessible URL | TBD | PENDING |
| Submitted repo/release | Public repo + frozen commit/tag | repo / `v0.1.0` | PENDING freeze |
| Spin-up instructions | Clean-environment-tested README | `README.md` | PENDING implementation |
| Architecture diagram | Deployed topology + autonomy/proof/safety boundary | `docs/ARCHITECTURE_DIAGRAM.md` + export | TARGET EXISTS; final reconciliation pending |
| Demo video | <=4m public YouTube/Vimeo | TBD | PENDING |
| Cloud proof | Cloud Run URL/dashboard/logs/traces | video + evidence | PENDING |
| Evaluation | Real measured results | `EVALUATION.md` | PENDING |
| BYOF proof | Personal friction narrative + reference benchmark | `docs/BYOF_FRICTION.md` + `EVALUATION.md` | CONTRACT EXISTS; measurement pending |
| Zero-human hero | Event→action→ack with no person | UI/video/logs/EVALUATION | PENDING execution |
| Proof-Carrying Autonomy | Typed claims + deterministic record/finding/source verification | source/UI/logs/EVALUATION | PENDING implementation |
| Claim verifier adversarial proof | Fabricated/stale/forbidden claims blocked | `EVALUATION.md` + source | PENDING |
| Real external action | Authorized A1 delivery outside Ngabo | UI/video/logs | PENDING |
| Machine acknowledgement | Callback/event closes workflow | UI/video/logs | PENDING |
| Action-policy proof | A1 auto / A2-A3 block tests | EVALUATION/source | PENDING |
| Automatic repair | verifier→bounded repair→verify | EVALUATION/source | PENDING |
| Freshness proof | Current state revalidated before action | EVALUATION/logs | PENDING |
| ActionIntent/idempotency proof | duplicate/retry no duplicate logical effect | EVALUATION/logs | PENDING |
| ADK capability proof | exact version + supported runtime path | `docs/ADK_CAPABILITY_SPIKE.md` | PENDING spike |
| Provenance | dependencies/data/evidence/rights | `docs/THIRD_PARTY_PROVENANCE.md` | CONTRACT EXISTS; freeze pending |
| Submission freeze | release/deployment/video manifest | `docs/SUBMISSION_FREEZE.md` + this file | PENDING |

Statuses change only from real artifacts.

---

## 4. Innovation & Operational Utility (40%) Evidence

### Required BYOF story

Submission/video must explain the builder's personal repeated friction:

```text
inspect AMR signal/data
→ compare profiles/context
→ find trusted evidence
→ separate fact/hypothesis
→ build defensible package
→ validate
→ route
→ track completion
```

Do not substitute generic “AMR is a global problem” language for personal friction.

### Required Twist story

Within the first minute, judges should understand:

```text
ordinary agent:
LLM says something → action

Ngabo:
LLM proposes typed claim
→ claim points to canonical records/findings/evidence
→ deterministic verifier checks those references/types
→ invalid claims repair or abstain
→ only verified package reaches deterministic A1 policy
```

Preferred concise phrasing after implementation is proven:

> **Ngabo is zero-human, but not zero-guardrail: its LLM outputs carry verifiable proof references, and deterministic code—not model confidence—decides whether claims can enter the autonomous action path.**

### Required hero proof

```text
surveillance event
→ automatic Pub/Sub trigger
→ ADK workflow
→ deterministic fan-out/join
→ bounded Gemini reasoning
→ approved evidence retrieval
→ proof-carrying synthesis
→ deterministic claim/evidence verification
→ bounded repair/abstention
→ A1 autonomy policy
→ freshness + ActionIntent/idempotency
→ real external action
→ machine acknowledgement
```

Required measured assertions:

- [ ] `manual_prompt_count_to_start == 0`;
- [ ] `human_intervention_count == 0`;
- [ ] `human_active_steps == 0`;
- [ ] `clarification_count == 0`;
- [ ] `approval_click_count == 0`;
- [ ] event→package/action/ack timings measured;
- [ ] model/deterministic call counts measured;
- [ ] builder reference human-step count measured;
- [ ] claim verification/repair counts measured;
- [ ] no fabricated hospital/clinical productivity claim.

---

## 5. Proof-Carrying Autonomy Evidence

The Twist is submission-eligible only when all relevant items are real:

### Claim model

- [ ] `OBSERVED_FACT` requires canonical-record proof;
- [ ] `DERIVED_FINDING` requires deterministic-finding proof;
- [ ] `EVIDENCE_STATEMENT` requires retrieved approved-source proof;
- [ ] `HYPOTHESIS` preserves explicit uncertainty;
- [ ] `ACTION_JUSTIFICATION` cannot authorize action;
- [ ] forbidden clinical/official claim types rejected.

### Deterministic verifier

- [ ] unknown isolate/record ID rejected;
- [ ] unknown deterministic finding rejected;
- [ ] wrong-run/stale finding rejected;
- [ ] unknown/unretrieved source rejected;
- [ ] stale package/source watermark rejected/recomputed;
- [ ] unsupported factual assertion rejected;
- [ ] hypothesis→fact escalation rejected;
- [ ] required uncertainty/limitation enforced where policy requires it;
- [ ] verifier is inward deterministic logic and does not depend on Gemini agreeing with itself.

### Repair / abstention

- [ ] verifier emits stable structured errors;
- [ ] bounded Gemini repair consumes those errors;
- [ ] repair cannot mutate canonical facts/deterministic findings/action policy;
- [ ] hard max attempt budget enforced;
- [ ] repair exhaustion yields abstention/no A1 action.

### Public metrics

Where meaningful, report:

```text
unsupported_claim_rate
invalid_reference_rate
fabricated_source_rate
fabricated_record_rate
claim_verification_pass_rate
repair_success_rate
repair_attempt_count
unsafe_claim_escape_rate
```

Committed adversarial-suite target:

```text
unsafe_claim_escape_rate == 0
```

This is a **software test target**, not a clinical-safety guarantee or universal hallucination-elimination claim.

---

## 6. Safety Evidence for Zero-Human Autonomy

Zero-human must be accompanied by proof that autonomy is bounded rather than reckless.

Required:

- [ ] deterministic A0/A1/A2/A3 action classifier;
- [ ] hero external action classified A1;
- [ ] A2 cannot execute autonomously;
- [ ] A3 cannot execute autonomously;
- [ ] non-allow-listed target blocked;
- [ ] missing material fact causes abstention, not fabricated fact;
- [ ] failed proof verification blocks action;
- [ ] invalid package cannot reach action;
- [ ] exhausted repair budget stops safely;
- [ ] prohibited diagnosis/prescribing/outbreak-confirmation language rejected;
- [ ] source integrity enforced;
- [ ] freshness required immediately before action;
- [ ] ActionIntent/outbox + idempotency protect external side effect.

This is the answer to: **“How can you remove the human without creating unacceptable risk?”**

---

## 7. Architectural Discipline & Tech Stack (30%) Evidence

A judge should answer these from repo/diagram/video:

| Judge question | Required evidence |
|---|---|
| How are systems decoupled? | Clean Architecture dependency diagram + source |
| Who owns truth? | Firestore/application state vs ADK session/context |
| Why is Gemini used? | deterministic-vs-agentic rule |
| What is the Twist? | Proof-Carrying Autonomy contract + verifier source/evals |
| Why trust model claims? | You do not: typed proof references + deterministic verifier |
| How is mandatory work orchestrated? | ADK graph / supported runtime equivalent |
| How is parallel work coordinated? | fan-out/join source + traces/tests |
| What if ADK API differs from webinar? | completed capability spike + pinned version/fallback |
| What if a required branch fails? | typed failure blocks false synthesis |
| What if Gemini invents an isolate/source/finding? | verifier rejects unknown reference |
| What if Gemini promotes a hypothesis to fact? | claim-type policy rejects escalation |
| What if model output is invalid? | deterministic verifier + bounded auto repair |
| What if event is duplicated? | ActionIntent/idempotency proof |
| What if data changes before action? | freshness/recompute proof |
| What if proposed action is unsafe? | deterministic action class/policy block |
| What if model memory is stale? | canonical-state reconstruction proof |
| How are tools secured? | typed inward ports, no arbitrary shell/DB/web |
| What proves it all works? | deployed E2E + logs/traces + EVALUATION |

Required diagram: `docs/ARCHITECTURE_DIAGRAM.md` reconciled to final release.

---

## 8. Demo & Production Readiness (30%) Evidence

### Continuous hero segment

The video must visibly include an unedited live sequence where:

1. surveillance signal/event appears;
2. Pub/Sub/Ngabo automatically starts workflow;
3. graph node/fan-out/join state changes;
4. Gemini/evidence stage executes;
5. proof-carrying claims appear with record/finding/source references;
6. deterministic claim verification passes or a bounded repair is shown;
7. action policy shows A1 auto-execute;
8. freshness + ActionIntent/idempotency pass;
9. external target receives real action;
10. machine acknowledgement returns;
11. Ngabo closes/updates incident.

No person should click or type inside this sequence.

### Technical proof

- [ ] Cloud Run proof visible;
- [ ] Google ADK/Gemini usage visible from architecture/log/code proof;
- [ ] Firestore/PubSub state/execution visible where useful;
- [ ] claim-verification event/metadata visible without private CoT;
- [ ] deployment URLs accessible;
- [ ] exact deployed commit/revisions recorded;
- [ ] three consecutive deployed hero E2E runs pass before freeze.

---

## 9. Prize Positioning Evidence

### Taskmaster — primary

- [ ] zero-human background workflow;
- [ ] BYOF personal friction;
- [ ] explicit Twist: Proof-Carrying Autonomy;
- [ ] event-driven start;
- [ ] complete multi-step heavy lifting;
- [ ] real external action;
- [ ] machine acknowledgement.

### Best Architectural Design — deliberate secondary target

- [ ] Clean Architecture;
- [ ] state boundaries;
- [ ] graph-first orchestration;
- [ ] deterministic/agentic separation;
- [ ] proof-carrying claim boundary;
- [ ] parallel fan-out/join;
- [ ] scoped tools;
- [ ] failure handling;
- [ ] ActionIntent/outbox/idempotency;
- [ ] resumability/context discipline;
- [ ] deterministic action-policy boundary;
- [ ] freshness;
- [ ] bounded validation/repair;
- [ ] observability/evaluation.

### Individual/Hobbyist

Final entrant/team structure must be accurate.

### Startup Excellence

Only claim/pursue if submitting on behalf of an eligible incorporated organization with required corporate email and other conditions.

### Best Multimodal UX

Optional only if polished after core freeze.

---

## 10. Bonus Evidence

### Public build content `+0.2`

- [ ] public;
- [ ] contains required hackathon-purpose statement;
- [ ] discusses real implementation/evaluation/tradeoffs;
- [ ] URL captured.

### Social `+0.2`

- [ ] public post;
- [ ] exact required hashtag;
- [ ] URL captured.

### Additional Google models `+0.2` each

For each claimed:

- [ ] real code path;
- [ ] executes in submitted build;
- [ ] role materially contributes;
- [ ] evaluation exists;
- [ ] diagram/docs/video truthful;
- [ ] license/terms recorded.

EmbeddingGemma planned. MedGemma gated. No third model solely for points.

---

## 11. Claim Ledger

At freeze complete:

| Claim | Implemented? | Evidence | Allowed in Devpost? |
|---|---|---|---|
| Zero-human event→ack hero | TBD | TBD | only if yes |
| BYOF reference benchmark | TBD | TBD | only if measured |
| The Twist: Proof-Carrying Autonomy | TBD | TBD | only if verifier/evals real |
| typed proof-carrying claims | TBD | TBD | only if yes |
| deterministic claim verifier | TBD | TBD | only if yes |
| `unsafe_claim_escape_rate == 0` on committed suite | TBD | TBD | only if measured and scoped correctly |
| ADK workflow | TBD | TBD | only if yes |
| deterministic fan-out/join | TBD | TBD | only if yes |
| real A1 external action | TBD | TBD | only if yes |
| machine acknowledgement | TBD | TBD | only if yes |
| deterministic action classification | TBD | TBD | only if yes |
| bounded automatic repair | TBD | TBD | only if yes |
| freshness barrier | TBD | TBD | only if yes |
| ActionIntent/outbox/idempotency | TBD | TBD | only if yes |
| EmbeddingGemma | TBD | TBD | only if yes |
| MedGemma | TBD | TBD | only if yes |
| multimodal draft | TBD | TBD | only if yes |
| practitioner validation | TBD | TBD | only if actually obtained |
| clinical validation | NO | N/A | NO |
| real hospital deployment | NO unless facts change | N/A | NO |

---

## 12. Submission Freeze Manifest

Complete from `docs/SUBMISSION_FREEZE.md`:

```text
submitted_commit_sha:
submitted_tag: v0.1.0
web_cloud_run_revision:
core_cloud_run_revision:
hosted_url:
repository_url:
architecture_diagram_path/url:
evaluation_artifact:
video_url:
article_url:
social_url:
model_versions:
adk_version:
dataset_version_hash:
evidence_corpus_version_hash:
submission_timestamp:
```

Freeze judged `main`/tag/deployment/video through the judging period.

---

## 13. Final Freeze Checklist

- [ ] Stage-One gate complete;
- [ ] zero-human hero proven three consecutive deployed runs;
- [ ] BYOF friction clearly stated and measured;
- [ ] Twist explicitly stated and proven;
- [ ] proof-carrying verifier + adversarial eval evidence complete;
- [ ] safety policy proves no autonomous A2/A3 action;
- [ ] ADK capability spike complete and dependency pinned;
- [ ] architecture diagram matches deployed runtime;
- [ ] every competitive claim has proof location;
- [ ] every unimplemented claim removed/labelled future;
- [ ] hosted project judge-accessible;
- [ ] `EVALUATION.md` contains real results;
- [ ] provenance/disclosure complete;
- [ ] bonus URLs/evidence real if claimed;
- [ ] demo <=4 minutes;
- [ ] continuous live proof-of-action segment contains no human intervention;
- [ ] freeze manifest complete;
- [ ] judged release remains stable through judging.
