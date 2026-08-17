# Ngabo — Hackathon Risk Register

**Status:** Required competition/release control  
**Date:** 2026-08-17

This register tracks risks that could reduce judging score, create submission ineligibility, weaken the Taskmaster story, or create a safety/architecture contradiction.

| ID | Risk | Impact | Mitigation / design control | Closure evidence |
|---|---|---:|---|---|
| R01 | Taskmaster hero requires human intervention | Critical | Zero-human A1 safe coordination lane; hero has no prompt, clarification or approval click | Deployed E2E + video + EVALUATION |
| R02 | Removing humans causes unsafe clinical/public-health autonomy | Critical | Deterministic A0–A3 action classes; only A1 allow-listed safe coordination auto-executes; A2/A3 blocked | Policy tests + source + diagram |
| R03 | BYOF feels generic/borrowed rather than personal | High | Ground friction in builder's own repeated AMR research/coordination workflow; measure exact reference workflow | `BYOF_FRICTION.md` + Devpost/video + benchmark |
| R04 | Hero data requires clarification | High | Complete material hero fixture; missing-data policy abstains rather than asks/fabricates | Fixture tests + `clarification_count=0` |
| R05 | Gemini produces invalid package and needs human repair | High | Proof-carrying typed claims + deterministic verifier + bounded automatic repair loop + safe abort | Claim-verification + repair evals |
| R06 | Evidence lookup fails and requires human search | High | Approved retrieval chain + bounded query reformulation + autonomous abstention | Evidence evals |
| R07 | External action is too consequential to automate | Critical | Use real authorized test/sandbox/internal A1 endpoint; no patient/treatment/outbreak action | Action-class tests + demo target config |
| R08 | External action requires human acknowledgement | Medium | Machine acknowledgement callback/event | E2E proof |
| R09 | Stale data causes wrong autonomous action | Critical | Deterministic pre-action freshness barrier and recomputation | Freshness tests |
| R10 | Duplicate Pub/Sub/retry causes duplicate action | Critical | Idempotency reservation/key + persisted delivery state | Redelivery/retry tests |
| R11 | ADK workshop graph API differs from installed Python API | High | Mandatory capability spike, version pin, fallback ladder | `ADK_CAPABILITY_SPIKE.md` result |
| R12 | Architecture diagram absent or mismatched | High | Judge-facing Mermaid diagram now exists; freeze update must match deployed runtime | final diagram + submitted image |
| R13 | Demo is architecture-heavy but friction/value unclear | High | BYOF opening + operational benchmark + hero autonomy counters | storyboard/video review |
| R14 | Demo spends time on clarification/resume instead of autonomy | High | Hero demo contains zero clarification; resume shown in eval/technical proof only | final storyboard |
| R15 | Design docs are mistaken for proof | Critical | Submission evidence matrix; claims require artifact/trace/result | claim ledger |
| R16 | Repo/deployment changes after deadline confuse judging | High | Freeze main/tag/revisions/video and keep judged URLs stable | submission manifest |
| R17 | Third-party data/content creates eligibility/IP risk | Critical | provenance/licensing register; synthetic authored fixtures; approved corpus verification | provenance freeze |
| R18 | Optional bonus model destabilizes core | High | EmbeddingGemma only after core; MedGemma/multimodal gated | scope freeze + eval |
| R19 | Agent performs fixed logic through LLM calls | Medium | graph-first deterministic/agentic rule; model-call regression tests | trajectory eval |
| R20 | Agent loops/self-repair runs forever | High | max step/tool/repair budgets + timeouts | budget tests |
| R21 | Prompt injection in imported data controls agent | Critical | canonical structured parsing, untrusted free text, scoped tools, adversarial eval | safety eval |
| R22 | Model/session memory overrides current AMR facts | Critical | Firestore/application canonical truth + context rebuild + no v0.1 factual long-term memory | context conflict tests |
| R23 | Submission claims clinical validation/real hospital use | Critical | claim boundaries + synthetic-data banner + final claim ledger | submission review |
| R24 | Hosted app unavailable during judging | High | scale-to-zero + max caps + budget, availability smoke tests, frozen revisions | monitoring checklist |
| R25 | Video fails proof-of-action criterion | Critical | continuous unedited event→action→ack segment with UI/log changes | final video review |
| R26 | Required GCP/model/framework use is hidden | High | architecture diagram + technical drawer + Cloud Console/Run proof | video timestamps |
| R27 | Operational utility score is subjective/unmeasured | High | before-vs-after builder friction benchmark + deployed timing/step metrics | EVALUATION |
| R28 | Autonomous completion hides uncertainty/failure | High | explicit safe abstention states; no fake success | failure scenario evals |
| R29 | Action-policy decision is delegated to Gemini | Critical | deterministic policy engine owns action class/authorization | unit tests |
| R30 | Hero action is dismissed as simulation | High | real outbound authorized integration outside Ngabo plus real machine acknowledgement; UI distinguishes simulation tests from real demo integration | delivery ID/log/callback proof |
| R31 | Fluent model hallucination survives into autonomous action | Critical | Proof-carrying structured claims; canonical record/finding/source references; deterministic claim verifier; bounded repair; invalid/exhausted packages abstain; action policy runs only on verified packages | `PROOF_CARRYING_REASONING.md` + fabricated-reference/claim-escalation tests + `unsafe_claim_escape_rate` |
| R32 | Chain-of-thought is mistaken for evidence or exposed as product truth | High | Hidden CoT is non-authoritative/non-persisted/non-displayed; expose claim type, evidence references, uncertainty and verification result instead | UI/log review + tests |

## Review Cadence

Review this register at:

- end of each implementation milestone;
- before Cloud deployment;
- before bonus-model integration;
- before demo freeze;
- before release `v0.1.0`;
- immediately before Devpost submission.

A Critical or High risk may be marked closed only when the required implementation/evidence exists—not because the design document exists.
