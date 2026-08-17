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
| R05 | Gemini produces invalid/unreliable package and needs human repair | High | Proof-carrying structured claims + deterministic verifier + bounded automatic repair + safe abort | Proof/repair evals |
| R06 | Evidence lookup fails and requires human search | High | Approved retrieval chain + bounded query reformulation + autonomous abstention | Evidence evals |
| R07 | External action is too consequential to automate | Critical | Use real authorized test/sandbox/internal A1 endpoint; no patient/treatment/outbreak action | Action-class tests + demo target config |
| R08 | External action requires human acknowledgement | Medium | Machine acknowledgement callback/event | E2E proof |
| R09 | Stale data causes wrong autonomous action | Critical | Deterministic pre-action freshness barrier and recomputation/re-verification | Freshness tests |
| R10 | Duplicate Pub/Sub/retry causes duplicate action | Critical | Transactional ActionIntent/outbox + stable idempotency key + delivery reconciliation | Redelivery/retry/crash-window tests |
| R11 | ADK workshop graph API differs from installed Python API | High | Mandatory capability spike, version pin, fallback ladder | `ADK_CAPABILITY_SPIKE.md` result |
| R12 | Architecture diagram absent or mismatched | High | Judge-facing Mermaid diagram exists; freeze update must match deployed runtime | Final diagram + submitted image |
| R13 | Demo is architecture-heavy but friction/value unclear | High | BYOF opening + operational benchmark + hero autonomy counters | Storyboard/video review |
| R14 | Demo spends time on clarification/resume instead of autonomy | High | Hero demo contains zero clarification; resume shown in eval/technical proof only | Final storyboard |
| R15 | Design docs are mistaken for proof | Critical | Submission evidence matrix; claims require artifact/trace/result | Claim ledger |
| R16 | Repo/deployment changes after deadline confuse judging | High | Freeze main/tag/revisions/video and keep judged URLs stable | Submission manifest |
| R17 | Third-party data/content creates eligibility/IP risk | Critical | Provenance/licensing register; synthetic authored fixtures; approved corpus verification | Provenance freeze |
| R18 | Optional bonus model destabilizes core | High | EmbeddingGemma only after core; MedGemma/multimodal gated | Scope freeze + eval |
| R19 | Agent performs fixed logic through LLM calls | Medium | Graph-first deterministic/agentic rule; model-call regression tests | Trajectory eval |
| R20 | Agent loops/self-repair runs forever | High | Max step/tool/repair budgets + timeouts | Budget tests |
| R21 | Prompt injection in imported data controls agent | Critical | Canonical structured parsing, untrusted free text, scoped tools, adversarial eval | Safety eval |
| R22 | Model/session memory overrides current AMR facts | Critical | Firestore/application canonical truth + context rebuild + no v0.1 factual long-term memory | Context conflict tests |
| R23 | Submission claims clinical validation/real hospital use | Critical | Claim boundaries + synthetic-data banner + final claim ledger | Submission review |
| R24 | Hosted app unavailable during judging | High | Cloud Run reliability controls, smoke tests, frozen revisions | Monitoring checklist |
| R25 | Video fails proof-of-action criterion | Critical | Continuous unedited event→action→ack segment with UI/log changes | Final video review |
| R26 | Required GCP/model/framework use is hidden | High | Architecture diagram + technical drawer + Cloud Console/Run proof | Video timestamps |
| R27 | Operational utility score is subjective/unmeasured | High | Before-vs-after builder friction benchmark + deployed timing/step metrics | EVALUATION |
| R28 | Autonomous completion hides uncertainty/failure | High | Explicit abstention/failure states; no fake success | Failure scenario evals |
| R29 | Action-policy decision is delegated to Gemini | Critical | Deterministic policy engine owns action class/authorization | Unit tests |
| R30 | Hero action is dismissed as simulation | High | Real outbound authorized integration outside Ngabo plus real machine acknowledgement; UI distinguishes simulation tests from real demo integration | Delivery ID/log/callback proof |
| R31 | Competition “Twist” is not explicit/memorable | High | Define and repeat **The Twist: Proof-Carrying Autonomy** in README, alignment, UI, Devpost/video plan | Final README/Devpost/video review |
| R32 | Gemini fabricates record/finding/source references | Critical | Typed proof-carrying claims + deterministic referential verifier | Adversarial verifier tests |
| R33 | Gemini promotes hypothesis to fact or forbidden clinical claim | Critical | Deterministic claim-type policy; forbidden claim classes/wording; repair/abstention | Claim-escalation tests |
| R34 | Proof-Carrying Reasoning docs drift from runtime/submission docs | High | Synchronize README, alignment, runtime, system design, implementation plan, UI, evidence matrix | Cross-doc audit before implementation/freeze |
| R35 | Proof-Carrying Autonomy is claimed before implementation/evaluation | Critical | Submission evidence matrix keeps claim PENDING until source + E2E + adversarial metrics exist | Claim ledger + EVALUATION |
| R36 | `unsafe_claim_escape_rate == 0` is misrepresented as clinical safety | Critical | Scope metric explicitly to committed software adversarial suite; never call clinical validation/universal hallucination elimination | EVALUATION wording review |

## Review Cadence

Review this register at:

- end of each implementation milestone;
- before Cloud deployment;
- before bonus-model integration;
- before demo freeze;
- before release `v0.1.0`;
- immediately before Devpost submission.

A Critical or High risk may be marked closed only when the required implementation/evidence exists—not because the design document exists.
