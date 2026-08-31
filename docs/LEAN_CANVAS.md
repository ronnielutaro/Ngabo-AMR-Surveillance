# Ngabo — Lean Canvas

**Project:** Ngabo — Always-On Antimicrobial Resistance Surveillance & Coordination  
**Positioning:** Open-source, always-on AMR surveillance and coordination layer with proof-verified autonomy  
**Initial context:** Uganda and African health systems  
**Version:** 0.3  
**Date:** 2026-08-31

---

## 1. Problem

### Core problems

1. **Routine microbiology data exists, but people remain the integration layer.** Laboratory and antimicrobial-susceptibility testing (AST) results may live in ALIS, WHONET, LIMS/LIS platforms, instrument exports, spreadsheets, or paper-assisted workflows. Surveillance teams still spend recurring effort extracting, transcribing, converting, cleaning, reconciling, deduplicating, and preparing data before useful surveillance work can begin.
2. **Surveillance is often periodic and operator-driven instead of continuously maintained.** Even where structured data exists, someone must remember to import it, refresh analyses, inspect trends, construct line lists or antibiograms, and notice when a resistance pattern deserves attention.
3. **A suspicious signal is only the beginning of the work.** Once something unusual appears, professionals still have to identify implicated isolates, compare resistance profiles, inspect temporal/location/baseline context, assess missingness, retrieve trusted guidance, distinguish facts from hypotheses, assemble an investigation-ready brief, route it, and follow up.
4. **Coordination is fragmented across tools and people.** Investigation outputs may move through Excel, WHONET reports, email, paper, messaging groups, committee materials, and national reporting channels with limited end-to-end acknowledgement or audit continuity.
5. **General-purpose AI cannot safely bridge this workflow by itself.** Fluent model output is not canonical truth. Action-relevant claims must remain grounded in laboratory records, deterministic findings, or approved retrieved evidence and must pass deterministic verification and policy before autonomous action.

### Existing alternatives

- WHONET analysis, alerts, antibiograms, line lists, and reporting
- ALIS, LIMS/LIS platforms, laboratory instruments, and national/interoperable surveillance systems
- BacLink and other export/conversion workflows
- Spreadsheets and custom analytical scripts
- Manual extraction, transcription, mapping, cleaning, deduplication, and periodic analysis
- Email, paper reports, phone calls, and messaging groups
- Manual investigation and coordination by microbiologists, AMR surveillance officers, IPC/AMS teams, epidemiologists, biostatisticians, and AMR focal persons

### Ngabo's wedge

Ngabo does **not** aim to replace microbiology instruments, ALIS, WHONET, LIMS/LIS platforms, or national surveillance infrastructure. It aims to remove the human glue between those systems and the recurring surveillance-to-coordination job.

> **Ngabo is an always-on AMR surveillance and coordination layer that connects to the laboratory systems you already use, continuously turns microbiology data into surveillance intelligence, automatically investigates meaningful signals, and completes the next permitted coordination step with machine-verifiable proof.**

The product loop is:

```text
CONNECT
routine microbiology / AST data
        ↓
WATCH
continuous deterministic surveillance
        ↓
INVESTIGATE
bounded reasoning + proof verification
        ↓
COORDINATE
deterministic policy + safe action + acknowledgement
```

### Current implementation boundary versus product direction

The v0.1 hackathon release does **not** yet claim a production ALIS, WHONET, LIS, instrument, or hospital connector. Its certified source is a committed synthetic WHONET-style dataset that exercises the deterministic ingestion and surveillance contracts.

The product direction is to replace that fixture boundary with governed source adapters while preserving the same canonical import, provenance, deduplication, surveillance, proof, and safety contracts.

---

## 2. Customer Segments

### Primary user

> **A microbiology or AMR surveillance professional responsible for keeping facility surveillance current and ensuring meaningful resistance signals become defensible, coordinated investigations.**

Likely first users include:

- AMR surveillance analysts and AMR focal persons
- Microbiology data managers
- Clinical laboratory scientists or microbiologists with surveillance responsibilities
- Hospital biostatisticians/data officers supporting AMR surveillance
- Hospital epidemiology analysts

The strongest user is not someone looking for another dashboard. It is someone already performing recurring data preparation, surveillance refresh, investigation assembly, reporting, or coordination work across several systems.

### Workflow stakeholders and information recipients

- Infection Prevention and Control (IPC) teams
- Antimicrobial Stewardship (AMS) teams and clinical pharmacists
- Medicines and Therapeutics Committees
- Hospital epidemiologists and surveillance officers
- Laboratory directors and microbiology leads
- Regional and national AMR surveillance teams
- Public-health and reference laboratories
- AMR researchers and epidemiologists

These stakeholders may govern, review, receive, or act on Ngabo's outputs. They are not all assumed to be daily operators.

### Potential institutional adopters, buyers, or funders

- National and regional referral hospitals
- AMR sentinel surveillance sites and hospital networks
- Ministries of Health and public-health agencies
- National/reference laboratory networks and AMR programmes
- Universities and research programmes
- Global-health NGOs and implementing partners
- Donor-funded AMR and digital-health programmes
- Innovation and public-sector technology funders

These remain **market hypotheses**, not confirmed customers or partnerships.

### Early-adopter conditions

The strongest initial environment should have:

- routine bacterial culture and AST;
- structured or exportable microbiology data;
- recurring ALIS/WHONET/LIS/Excel surveillance work;
- an active microbiology, AMR, IPC, or stewardship function;
- enough testing volume for surveillance state to require regular maintenance;
- a willingness to begin with synthetic, de-identified, controlled, or shadow-mode evaluation;
- a domain professional able to challenge Ngabo's assumptions and outputs;
- an authorized low-consequence coordination target for testing the A1 lane.

Small facilities with very low microbiology volume, no structured data, or no surveillance function may experience Ngabo as a vitamin rather than a painkiller and are not the preferred first segment.

---

## 3. Unique Value Proposition

> **Your laboratory keeps doing its normal work. Ngabo keeps the AMR surveillance job done.**

Ngabo continuously receives or consumes authorized microbiology data, validates and normalizes it, updates surveillance state, detects meaningful investigation-priority signals, automatically assembles the investigation, retrieves approved evidence, separates facts from hypotheses, verifies model-supported claims, applies deterministic action policy, and tracks permitted coordination through machine acknowledgement.

### Product promise

> **From routine lab data to safe surveillance action without somebody repeatedly extracting, cleaning, analyzing, assembling, sending, and chasing the workflow.**

### High-level concept

**An always-on AMR surveillance operating loop: Connect → Watch → Investigate → Coordinate.**

### Differentiating principle

> **High system autonomy, low model authority. LLM proposes; deterministic machinery verifies; deterministic policy authorizes; the system executes; external acknowledgement confirms completion.**

Ngabo calls this design **Proof-Carrying Autonomy**. Gemini contributes bounded intelligence, but model fluency, confidence, hidden reasoning, or self-assessment never creates canonical facts, verification, policy eligibility, authorization, delivery, or acknowledgement.

---

## 4. Solution

### Product operating loop

#### 1. Connect — governed data acquisition

Target production behaviour:

- Meet the data where the laboratory already produces it rather than requiring a new parallel workflow.
- Support governed adapters for sources such as ALIS, WHONET/BacLink outputs, LIMS/LIS exports, watched folders, scheduled files, instrument exports, and future standards-based interfaces.
- Preserve source identity, provenance, authorization, and replay semantics.
- Keep manual file upload as a fallback, not the ideal primary experience.

**v0.1 truth:** the hackathon hero currently uses a committed synthetic WHONET-style source; live production connectors remain a deployment frontier, not a shipped claim.

#### 2. Watch — continuous deterministic surveillance

- Parse, validate, normalize, hash, deduplicate, and reconcile incoming microbiology/AST data deterministically.
- Update canonical surveillance state whenever authorized data changes.
- Recompute relevant resistance-profile, temporal/location, concentration, and baseline findings through deterministic scientific owners.
- Stay quiet when there is no meaningful signal.
- Emit a referenceable investigation-priority event when governed criteria pass.

#### 3. Investigate — autonomous evidence-grounded workflow

- Start the workflow from the surveillance event without chat, clarification, approval, or manual continuation.
- Run mandatory deterministic investigation branches such as resistance-profile comparison, baseline analysis, and material-missingness assessment.
- Use Gemini only where bounded judgment is useful.
- Retrieve only approved provenance-carrying evidence.
- Generate typed proposals that distinguish observed facts, deterministic findings, evidence statements, hypotheses, uncertainty, and action justification.
- Require material claims to carry machine-checkable support.
- Verify claims and package boundaries deterministically.
- Allow bounded model repair only under verifier control; otherwise abstain.

#### 4. Coordinate — deterministic safe action and closure

- Require current verified-package eligibility before action policy.
- Apply deterministic A0/A1/A2/A3 classification and authorization.
- Permit only authorized, allow-listed A1 coordination in the public v0.1 autonomous lane.
- Recheck freshness immediately before action.
- Commit one durable `ActionIntent` with a stable idempotency key.
- Execute one authorized external effect.
- Receive and preserve machine acknowledgement.

### Three nested autonomous loops

```text
DATA READINESS LOOP
new authorized lab data
→ acquire
→ validate
→ normalize
→ deduplicate
→ canonical state

SURVEILLANCE LOOP
canonical state change
→ update findings/baseline
→ evaluate signal
→ quiet OR incident

INVESTIGATION / RESPONSE LOOP
incident
→ investigate
→ evidence
→ Gemini proposal
→ deterministic verification
→ deterministic policy
→ effect
→ acknowledgement
```

### Missing-data behaviour

Ngabo does not ask a human a question merely to keep the canonical hero moving:

```text
material fact missing    → NEEDS_INFORMATION / BLOCK → no external action
optional fact missing    → preserve UNKNOWN; continue only if policy permits
recoverable fact missing → fetch only from an authorized deterministically linked source
```

Ngabo never invents a clinical or laboratory fact to preserve autonomy.

### Action envelope

| Class | Meaning | Public v0.1 behaviour |
|---|---|---|
| A0 | Internal state and audit effects | Autonomous |
| A1 | Safe, allow-listed external coordination | Autonomous after deterministic gates |
| A2 | Real operational escalation | Not autonomous by default |
| A3 | Clinical or official public-health decision | Never autonomous |

Ngabo does not diagnose, prescribe, confirm an outbreak, or claim official authority.

---

## 5. Channels

### Initial discovery and validation channels

- Direct workflow interviews and controlled demonstrations with microbiology and AMR surveillance professionals
- Referral hospitals and established AMR sentinel sites
- University and research collaborations
- AMR, IPC, microbiology, stewardship, biostatistics, and public-health professional networks
- Open-source GitHub distribution and technical documentation
- Hackathons, research showcases, and responsible public demonstrations

### Potential adoption channels

- Controlled shadow-mode pilots with referral hospitals or research laboratories
- Ministry of Health and national AMR surveillance programmes
- Public-health/reference laboratory networks
- Digital-health and AMR implementing partners
- Donor-funded AMR and surveillance programmes
- ALIS/LIMS/WHONET/interoperability implementation partners

### Trust-building channels

- Transparent software benchmarks and reproducible evaluations
- Public architecture, safety contracts, and limitations
- Auditable data provenance, evidence, verification, policy, delivery, and acknowledgement trails
- Domain-expert workflow review
- Clean integration contracts that complement rather than replace upstream systems
- Peer-reviewed or preprint validation studies when sufficient evidence exists

---

## 6. Revenue and Support Streams

Ngabo can remain open source at its core while sustainable deployment, integration, validation, and support are funded separately.

### Near-term hypotheses

- Research and innovation grants
- Public-health R&D funding
- Sponsored workflow-validation studies or controlled pilots
- University and research collaborations
- Hackathon or innovation awards

### Longer-term hypotheses

- Managed or hosted deployments
- Paid source-system integration and connector implementation
- Institutional configuration and surveillance-policy setup
- Enterprise support, maintenance, security, and governance services
- Multi-site/network deployment support
- Training and institutional capacity building

The immediate objective is to prove workflow utility and integration fit, not to imply established willingness to pay.

---

## 7. Cost Structure

### Product and engineering

- Google Cloud compute, storage, networking, event infrastructure, and observability
- Gemini inference and approved-evidence retrieval
- Source adapters, interoperability, watched-folder/scheduled ingestion, and mapping maintenance
- External notification/coordination integrations
- Security, backups, audit logging, and reliability engineering

### Domain and evaluation

- Microbiology, epidemiology, IPC, AMS, and surveillance expert review
- Representative synthetic and controlled datasets
- Deterministic ingestion/detector and proof-verifier evaluation
- Workflow research and usability testing
- Future retrospective/shadow-mode validation

### Deployment and governance

- Institutional integration and configuration
- Security, privacy, retention, and data-protection assessment
- Data-source authorization and mapping
- Training and change management
- Field testing and implementation support
- Ongoing maintenance and open-source governance
- Potential regulatory/clinical-safety work if future product claims require it

---

## 8. Key Metrics

### Data-loop utility

- `manual_export_steps_eliminated`
- `manual_transcription_steps_eliminated`
- `manual_file_uploads_required`
- `source_to_canonical_latency`
- `source_replay_dedup_accuracy`
- percentage of accepted imports requiring manual correction
- percentage of source updates automatically incorporated into surveillance state
- data-freshness age by facility/source

For the mature production direction, the target user experience is that routine data arrival does not require a human to initiate surveillance processing.

### Surveillance utility

- time from authorized data arrival to updated surveillance state
- time from data arrival to investigation-priority signal
- percentage of surveillance refreshes requiring human initiation
- detector reproducibility across equivalent runs
- false-positive rate on committed normal/noisy scenarios
- sensitivity on committed seeded suspicious scenarios

These remain software-evaluation metrics until validated under an appropriate real-world study design.

### Canonical hero autonomy

```text
manual_prompt_count_to_start  = 0
human_intervention_count      = 0
human_active_steps            = 0
clarification_count           = 0
approval_click_count          = 0
manual_continuation_count     = 0
external_effect_count         = 1
machine_acknowledgement_count = 1
```

- Three consecutive successful deployed hero runs before submission freeze
- Signal-to-package, package-to-action, and action-to-acknowledgement latency
- Successful recovery from restart/redelivery without human intervention

### Proof and safety integrity

- Claim-verification pass rate
- Invalid/fabricated-reference rejection rate
- Unsupported-claim rate
- Repair success and repair-budget exhaustion rate
- Percentage of unverified packages reaching A1 policy: target `0`
- A2/A3 autonomous execution count: target `0`
- Non-allow-listed action execution count: target `0`
- `unsafe_claim_escape_rate`: target `0` on the committed adversarial software suite

### Workflow utility

- Reference human active steps versus Ngabo active human steps
- Reference human elapsed time versus automated elapsed time
- Manual extraction, cleaning, investigation, drafting, routing, and follow-up steps eliminated
- Result-to-surveillance latency reduction
- Signal-to-investigation latency reduction
- Signal-to-coordination latency reduction
- Percentage of incidents with complete traceable evidence packages
- Percentage of external effects with durable intent, delivery result, and machine acknowledgement

### Adoption and ecosystem, when pilots begin

- Qualified workflow interviews and demonstrations
- Number and type of source systems successfully mapped in controlled environments
- Domain-professional contradictions and workflow gaps documented
- Controlled pilots/research collaborations established
- Repeated usage in an approved evaluation environment
- Validated integrations and external open-source contributions

---

## 9. Advantage

Ngabo's defensibility should come from owning the end-to-end surveillance operating loop while preserving existing laboratory infrastructure, not from merely wrapping an LLM or cloning an established AMR dashboard.

### Tangible advantages being built

- **Continuous-loop architecture:** ingestion, surveillance, investigation, proof, policy, effect, and acknowledgement are designed as one traceable workflow rather than disconnected tools.
- **Proof-Carrying Autonomy:** material model claims carry machine-checkable references and must pass deterministic verification before influencing action.
- **High system autonomy / low model authority:** Ngabo owns workflow progression; Gemini contributes bounded proposals but cannot create canonical truth or action authority.
- **Deterministic/agentic separation:** code owns scientific calculations, mandatory routing, verification, authorization, freshness, and idempotency.
- **Replay-safe ingestion foundation:** source identity, hashing, deterministic normalization, deduplication, and canonical provenance reduce the risk that always-on ingestion creates duplicate or inconsistent work.
- **Closed-loop autonomy:** the target proof covers event, investigation, safe external effect, and machine acknowledgement with zero human continuation.
- **Safe abstention:** incomplete, stale, unauthorized, or unverifiable cases stop instead of fabricating completion.
- **Non-replacement integration strategy:** Ngabo is intended to complement ALIS, WHONET, LIS/LIMS, and national platforms rather than force wholesale replacement.

### Advantages to validate or develop

- Production-grade governed adapters for ALIS, WHONET/BacLink, LIS/LIMS, watched-folder, instrument-export, and standards-based sources
- Uganda- and Africa-specific workflow knowledge grounded in direct practitioner validation
- Institutional trust and integration relationships
- Facility/network-specific operational knowledge learned under governance
- Multi-site surveillance operations without creating ungoverned cross-facility claims
- Published evidence that Ngabo reduces recurring surveillance labor and latency

Future advantages remain hypotheses until supported by implementation, evaluation, partnerships, or measured deployment evidence.

---

## 10. Early-Adopter Hypothesis

The strongest first user is likely:

> **An AMR surveillance focal person, microbiology data manager, microbiologist, or hospital data professional at a referral/sentinel facility that already generates routine AST data but still relies on recurring extraction, conversion, Excel/WHONET preparation, manual surveillance refresh, investigation assembly, and coordination.**

The strongest first institutional environment should have:

- routine bacterial culture and AST;
- ALIS, WHONET, LIS/LIMS, BacLink-compatible export, or another structured data source;
- enough microbiology volume for recurring surveillance work;
- an active AMR, IPC, AMS, microbiology, or surveillance function;
- repeated reporting/committee/coordination obligations;
- a willingness to evaluate an integration layer rather than replace existing systems;
- controlled/de-identified/shadow-mode data available for validation;
- an authorized low-consequence coordination target.

A second high-value institutional hypothesis is the **AMR surveillance network/programme** rather than one hospital: multi-site data collection compounds extraction, reconciliation, quality, surveillance, and coordination workload and may therefore increase Ngabo's operating frequency and value.

This remains a hypothesis until direct workflow research and controlled evaluation confirm it.

---

## 11. Critical Risks and Assumptions

### Product assumptions to validate

- Recurring data acquisition/preparation is a meaningful operational burden at target facilities or surveillance programmes.
- Users prefer an always-on integration/surveillance layer to another dashboard they must operate.
- Existing ALIS/WHONET/LIS/export workflows provide a practical governed source seam.
- Continuous surveillance reduces work without creating unacceptable alert fatigue.
- Enough laboratory context exists for useful automated investigation or safe abstention.
- Proof-verified packages are understandable and useful to surveillance professionals.
- Safe A1 automation removes meaningful coordination friction without crossing clinical or official authority boundaries.
- Institutions are willing to authorize background ingestion and automation under explicit governance.

### Major risks

- Poor, incomplete, delayed, or inconsistent laboratory data
- Source-system heterogeneity and mapping/configuration burden
- Offline or poorly connected facilities
- Manual upstream workflows that cannot yet produce reliable machine-readable data
- False-positive signals and alert fatigue
- Fabricated, unsupported, stale, or misclassified model claims
- Confusion between investigation candidates and confirmed outbreaks
- Patient privacy, data protection, retention, and data-residency constraints
- Integration/security resistance from institutional system owners
- Ngabo duplicating functionality already solved locally
- Lack of measurable labor/latency savings
- Insufficient domain, operational, or clinical validation
- Submission/demo wording that implies live hospital connectors or clinical validation that do not exist

### Safety principles

- Data acquisition must be authorized, source-linked, replay-safe, and privacy governed.
- Deterministic systems own parsing, scientific calculations, mandatory routing, verification, action classification, authorization, freshness, and idempotency.
- Gemini cannot create canonical facts, verify itself, promote A2/A3 actions, or produce terminal success authority.
- Material model claims remain typed, evidence-linked, uncertainty-aware, and machine-verifiable.
- Missing material facts cause safe abstention; they are never invented to preserve autonomy.
- Only authorized A1 safe coordination can auto-execute in the public v0.1 hero.
- Clinical, treatment, official outbreak, and other consequential decisions remain outside autonomous v0.1.
- No real identifiable patient data appears in public repositories, evaluations, or hackathon demonstrations.
- Software evaluation is not represented as clinical validation or regulatory approval.

---

## 12. Validation Plan

### Phase 0 — Workflow and source-system grounding

- Interview microbiology, AMR surveillance, biostatistics/data, IPC, and AMS professionals about the actual data-to-surveillance-to-coordination workflow.
- Observe or document where ALIS, WHONET, LIS/LIMS, BacLink, Excel, paper, email, and committee workflows enter the process.
- Measure recurring extraction, transcription, conversion, cleaning, deduplication, analysis, investigation, and follow-up steps.
- Identify the highest-frequency safe integration seam rather than assuming one universal hospital architecture.
- Keep public claims separated into supported evidence, partial support, and hypotheses.

### Phase 1 — Deterministic ingestion/signal foundation

- Maintain representative synthetic WHONET-style fixtures.
- Preserve deterministic parsing, validation, normalization, hashing, deduplication, canonical import, profile comparison, baselines, windows, and signal logic.
- Certify normal, noisy, malformed, missing, replay, duplicate, changed-source, and suspicious scenarios offline.

### Phase 2 — Production source-adapter discovery and shadow ingestion

After the hackathon core is stable:

- Prototype the smallest real governed adapter path, preferably one that fits existing practice rather than requiring a new hospital workflow.
- Candidate progression: manual governed export → watched-folder ingestion → scheduled source connector → event/API integration.
- Compare source-adapter outputs against the existing canonical import boundary.
- Measure manual steps removed and data-freshness improvement.
- Do not let integration work bypass canonical validation, source-watermark, deduplication, or privacy boundaries.

### Phase 3 — Proof-carrying autonomous workflow

- Implement and certify event-driven deterministic fan-out/join.
- Retrieve only approved provenance-carrying evidence.
- Generate typed model proposals with explicit uncertainty.
- Verify claims deterministically and repair under verifier control or abstain.
- Authorize only A1 action after proof, policy, and freshness gates.
- Execute through durable idempotent intent/outbox and receive machine acknowledgement.

### Phase 4 — Safety, reliability, and operational-utility evaluation

- Test A2/A3 blocking, missing-data abstention, unauthorized targets, prompt injection, fabricated references, stale state, branch failure, restart, duplicate events, source replay, and source change.
- Compare the builder's documented reference workflow with the zero-human hero for hackathon evidence.
- For later pilots, compare existing facility workflow against Ngabo on recurring manual steps, result-to-surveillance latency, signal-to-investigation latency, and coordination completion.

### Phase 5 — Professional validation and controlled pilot pathway

- Demonstrate Ngabo to qualified microbiology/AMR/data/IPC/AMS professionals.
- Validate whether recurring data preparation and surveillance maintenance are painful enough to justify adoption.
- Identify a research/institutional partner willing to evaluate de-identified, controlled, or shadow-mode feeds.
- Define data governance, intended use, authorization, success metrics, and stop conditions before any live integration.

The implementation roadmap and GitHub issues track delivery status. This canvas records the product hypotheses and evidence required to validate them.

---

## 13. MVP Boundary

### Ngabo v0.1 should prove one complete autonomous operating slice

> **A synthetic WHONET-style microbiology source can deterministically produce a surveillance signal that automatically completes event → proof-carrying investigation proposal → deterministic verification → authorized A1 external action → machine acknowledgement with zero human intervention, while unsafe, incomplete, unverifiable, A2, and A3 cases block or safely abstain.**

### In scope for the hackathon release

- Representative synthetic WHONET-style source
- Deterministic parsing, validation, normalization, source hashing, replay/deduplication, surveillance, and missingness assessment
- Event-triggered Google ADK workflow without chat/prompt
- Deterministic parallel investigation and join semantics
- Bounded Gemini reasoning and approved evidence retrieval
- Typed proof-carrying model proposals and deterministic verification
- Bounded automatic repair under verifier control or safe abstention
- Deterministic A1 action policy and allow-list authorization
- Freshness validation
- Durable `ActionIntent`, outbox, and stable idempotency
- Real authorized external test/sandbox/internal coordination action
- Machine acknowledgement
- Incident/autonomy console and zero-human metrics
- Audit trail and safety/reliability evaluation

### Explicitly out of scope for the hackathon release unless separately implemented and certified

- Claiming direct production connection to ALIS, WHONET, a hospital LIS/LIMS, or laboratory instrument
- Real patient/hospital data acquisition
- Nationwide or multi-site operational deployment
- Autonomous diagnosis or treatment selection
- Autonomous outbreak confirmation or official declaration
- Autonomous A2 real operational escalation
- Contacting real patients/hospitals/persons without explicit authorization
- Replacing ALIS, WHONET, LIMS/LIS, or national surveillance infrastructure
- Full genomic, multimodal, or cross-facility epidemiological surveillance
- Dynamic multi-agent specialist fleets or a second orchestration framework
- Clinical-validation, medical-device, or regulatory-approval claims

### Post-v0.1 product hardening frontier

The highest-value next product frontier is the **live acquisition seam**:

```text
CURRENT
synthetic WHONET-style source
→ canonical import
→ surveillance
→ investigation
→ coordination

TARGET
ALIS / WHONET / LIS / BacLink / authorized export
→ governed automatic acquisition
→ canonical import
→ continuously refreshed surveillance
→ automatic investigation
→ safe coordination
```

The connector must adapt to Ngabo's canonical boundary; it must not weaken the deterministic import contract to fit upstream source inconsistencies.

---

## 14. Strategic Thesis

Ngabo is most compelling as **always-on public-health surveillance infrastructure with a DeepTech trajectory**, not as another AMR dashboard, reporting tool, AI assistant, or disposable hackathon agent.

The painkiller thesis is not simply that Ngabo produces better insight. It is that recurring human work disappears:

```text
extract / transcribe / upload
→ clean / map / deduplicate
→ refresh surveillance
→ inspect what matters
→ reconstruct context
→ find evidence
→ draft and validate
→ route
→ follow up
```

becomes:

```text
routine laboratory work
        ↓
authorized data arrives
        ↓
Ngabo keeps surveillance current
        ↓
no material signal → quiet
        ↓
meaningful signal → autonomous investigation
        ↓
proof verification
        ↓
safe coordination
        ↓
acknowledgement
```

The long-term product thesis is:

> **Ngabo keeps the AMR surveillance job done continuously — from routine laboratory data entering the system through detection, investigation, proof verification, safe coordination, and acknowledgement.**

The v0.1 hackathon release proves a narrow but complete autonomous slice using synthetic data. It should be presented truthfully as the architectural and operational proof for this broader direction, not as evidence that production hospital ingestion or clinical effectiveness already exists.

A2 operational escalation and A3 clinical or official decisions remain governed by authorized people and institutions.
