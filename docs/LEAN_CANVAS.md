# Ngabo — Lean Canvas

**Project:** Ngabo — Autonomous Antimicrobial Resistance Surveillance & Incident Response  
**Positioning:** Open-source, event-driven AMR investigation and safe-coordination layer with proof-verified autonomy  
**Initial context:** Uganda and African health systems  
**Version:** 0.2  
**Date:** 2026-08-29

---

## 1. Problem

### Core problems

1. **AMR surveillance signals do not reliably become coordinated action.** Microbiology and antimicrobial-susceptibility testing (AST) data may already exist in WHONET, laboratory information systems, spreadsheets, or national surveillance infrastructure. Turning a suspicious signal into an investigation-ready package and a coordinated next step still requires many disconnected activities across people and systems.
2. **Suspicious resistance patterns are difficult to triage consistently.** Surveillance professionals must compare organisms, resistance phenotypes, locations, dates, specimen sources, historical baselines, missingness, and guidance before deciding whether a signal warrants further investigation.
3. **Evidence assembly and coordination are fragmented.** Teams must gather context, retrieve approved guidance, distinguish observations from hypotheses, prepare a brief, route it appropriately, track acknowledgement, and preserve an auditable record.
4. **General-purpose AI cannot safely bridge this gap by itself.** Fluent output is not enough. Action-relevant claims must be grounded in canonical records, deterministic findings, or approved retrieved evidence and must be verified before they can influence an autonomous action.

### Existing alternatives

- WHONET analysis, alerts, and reporting
- Laboratory information systems and national or interoperable surveillance platforms
- Spreadsheets and custom analytical scripts
- Email, paper reports, phone calls, and messaging groups
- Manual review and coordination by microbiologists, AMR surveillance officers, IPC teams, epidemiologists, and AMR focal persons

### Ngabo's wedge

Ngabo does **not** aim to replace WHONET, laboratory systems, or national surveillance infrastructure. It focuses on the workflow after structured data and surveillance signals exist:

> **Turning a suspicious AMR signal into a proof-verified investigation package and an authorized, acknowledged safe-coordination action.**

---

## 2. Customer Segments

### Primary user

> **A microbiology or AMR surveillance professional responsible for translating structured AST data into an investigation-ready package and coordinating the next safe step.**

The initial user is most likely an AMR surveillance analyst, AMR focal person, or microbiology data manager in a facility that already produces structured microbiology data but still performs substantial manual investigation and coordination.

### Workflow stakeholders and information recipients

- Hospital microbiologists and clinical laboratory scientists
- Infection Prevention and Control (IPC) teams
- Hospital epidemiologists and surveillance officers
- Antimicrobial Stewardship (AMS) teams and clinical pharmacists
- Regional and national AMR surveillance teams
- Public-health and reference laboratories
- AMR researchers and epidemiologists

These stakeholders may review, receive, govern, or act on Ngabo's outputs. They are not all assumed to be the first daily operator.

### Potential institutional adopters, buyers, or funders

- Hospitals and hospital networks
- Ministries of Health and public-health agencies
- Universities and research programmes
- Global-health NGOs and implementing partners
- Donor-funded AMR and digital-health programmes
- Innovation and public-sector technology funders

These are **market hypotheses**, not confirmed customers or partners.

### Early-adopter conditions

- Structured or exportable microbiology/AST data already exists
- Investigation and escalation still involve repeated manual work
- An active AMR, IPC, microbiology, or stewardship function exists
- The institution can begin with synthetic, de-identified, or controlled data
- A domain professional can critique the investigation logic and workflow fit
- The institution is willing to evaluate an open, auditable coordination layer rather than replace its surveillance system

---

## 3. Unique Value Proposition

> **From AMR signal to proof-verified investigation and safe coordination automatically, without replacing existing surveillance systems.**

Ngabo detects a suspicious AMR signal, performs deterministic investigation stages, uses Gemini only for bounded evidence-grounded synthesis, verifies every material action-relevant claim, and executes one authorized safe-coordination action with machine acknowledgement.

### High-level concept

**An autonomous AMR investigation and safe-coordination agent with machine-verifiable claims.**

### Differentiating principle

> **LLM proposes; deterministic machinery verifies whatever can be verified before a claim may influence autonomous action.**

Ngabo calls this design **Proof-Carrying Autonomy**. Model fluency, confidence, hidden reasoning, or consensus never substitutes for canonical evidence or deterministic authorization.

---

## 4. Solution

### Canonical v0.1 workflow

1. **Ingest and normalize**
   - Parse representative synthetic WHONET-style microbiology/AST data
   - Validate and normalize organism, specimen, location, date, and AST fields deterministically
   - Reject malformed records and represent missingness explicitly

2. **Detect**
   - Run transparent statistical and rule-based surveillance logic
   - Compare resistance profiles, time windows, locations, and historical baselines
   - Emit a suspicious investigation-candidate event when governed criteria pass

3. **Start automatically**
   - Publish the signal through Pub/Sub
   - Start the Google ADK workflow without a manual prompt
   - Load current canonical incident context

4. **Investigate through deterministic fan-out and join**
   - Run resistance-profile comparison, baseline analysis, and missing-field assessment in parallel
   - Use deterministic routing, branch requirements, failure semantics, and join behaviour
   - Treat canonical application state as truth; use ADK session state only for execution continuity

5. **Reason with approved evidence**
   - Use Gemini only for bounded ambiguity, evidence-grounded synthesis, labelled hypotheses, and drafting
   - Retrieve from an approved, provenance-carrying evidence corpus
   - Separate observed facts, derived findings, evidence statements, hypotheses, uncertainties, and action justification

6. **Verify and repair**
   - Require material model claims to reference canonical records, deterministic findings, or retrieved approved sources
   - Verify claim types, references, prohibited semantics, package structure, and evidence integrity deterministically
   - Return structured errors for bounded automatic repair
   - Abstain if verification cannot pass within the repair budget

7. **Authorize only safe coordination**
   - Apply deterministic A0/A1/A2/A3 action policy
   - Permit only authorized, allow-listed A1 safe external coordination in the v0.1 autonomous hero
   - Block A2 operational escalation and A3 clinical or official public-health decisions from autonomous execution
   - Recheck freshness immediately before action

8. **Execute and close the loop**
   - Commit one durable `ActionIntent` with a stable idempotency key
   - Send the investigation-candidate payload through a real authorized test, sandbox, or internal integration
   - Receive a machine acknowledgement
   - Preserve a complete auditable incident and effect timeline

### Missing-data behaviour

Ngabo does not ask a human a question merely to keep the canonical hero moving:

```text
material fact missing    → NEEDS_INFORMATION → no external action
optional fact missing    → preserve UNKNOWN; continue only if policy permits
recoverable fact missing → fetch from an authorized canonical source when deterministically linked
```

The complete synthetic hero fixture contains the material facts required for safe A1 completion. Ngabo never invents a clinical fact to preserve autonomy.

### Action envelope

| Class | Meaning | Public v0.1 behaviour |
|---|---|---|
| A0 | Internal state and audit effects | Autonomous |
| A1 | Safe, allow-listed external coordination | Autonomous after all deterministic gates pass |
| A2 | Real operational escalation | Not autonomous by default |
| A3 | Clinical or official public-health decision | Never autonomous |

Ngabo does not diagnose, prescribe, confirm an outbreak, or claim official authority. Future consequential workflows require appropriate institutional governance and human authority.

### Stretch capabilities after the core hero is reliable

- Standards-based LIMS, DHIS2, and national-platform connectors
- Facility-specific baselines informed by validated outcomes
- Embedding-based evidence retrieval when it demonstrates measured value
- Genomic AMR evidence and genotype–phenotype concordance
- Cross-facility and One Health intelligence

These capabilities are outside the v0.1 core unless implemented and evaluated without threatening hero reliability.

---

## 5. Channels

### Initial discovery and validation channels

- Direct workflow interviews and controlled demonstrations with microbiology and AMR surveillance professionals
- University and research collaborations
- AMR, IPC, microbiology, and public-health professional networks
- Open-source GitHub distribution and technical documentation
- Hackathons, research showcases, and responsible public demonstrations

### Potential adoption channels

- Controlled pilots with research laboratories, university hospitals, or referral hospitals
- Ministry of Health and public-health partnerships
- Digital-health and AMR implementing partners
- Donor-funded AMR and surveillance programmes
- Standards-based integration partners

These channels require validation. Participation in an ecosystem does not itself prove access, partnership, or adoption.

### Trust-building channels

- Transparent software benchmarks and reproducible evaluations
- Public architecture, safety contracts, and limitations
- Auditable evidence and claim-verification trails
- Domain-expert review of scenarios and outputs
- Peer-reviewed or preprint validation studies when sufficient evidence exists

---

## 6. Revenue and Support Streams

Ngabo can remain open source at its core while sustainable deployment, validation, integration, and support are funded separately.

### Near-term hypotheses

- Research and innovation grants
- Public-health R&D funding
- Sponsored validation studies or controlled pilots
- University and research collaborations
- Hackathon or innovation awards

### Longer-term hypotheses

- Managed or hosted deployments
- Paid implementation and systems integration
- Custom connectors and institutional configuration
- Enterprise support, maintenance, security, and governance services
- Training and institutional capacity building

The immediate goal is to validate the problem and workflow, not to imply that these revenue streams or customers already exist.

---

## 7. Cost Structure

### Product and engineering

- Google Cloud compute, storage, networking, and event infrastructure
- Gemini inference and approved-evidence retrieval
- External notification or coordination integrations
- Observability, security, backups, and audit logging
- Data engineering and interoperability work

### Domain and evaluation

- Microbiology, epidemiology, IPC, and AMS expert review
- Synthetic dataset design and scenario curation
- Deterministic detector and proof-verifier evaluation
- User workflow research and controlled usability testing
- Future clinical, operational, or implementation research

### Deployment and governance

- Institutional integration and configuration
- Training and change management
- Security, privacy, and data-protection assessment
- Field testing and implementation support
- Ongoing maintenance and open-source governance
- Potential regulatory or clinical-safety work if future product claims require it

---

## 8. Key Metrics

### Canonical hero autonomy

```text
manual_prompt_count_to_start  = 0
human_intervention_count      = 0
human_active_steps            = 0
clarification_count           = 0
approval_click_count          = 0
external_effect_count         = 1
machine_acknowledgement_count = 1
```

- Three consecutive successful deployed hero runs before submission freeze
- Event-to-signal, signal-to-package, package-to-action, and action-to-acknowledgement latency
- Successful recovery from restart or redelivery without human intervention

### Proof and safety integrity

- Claim-verification pass rate
- Invalid-reference and fabricated-reference rejection rate
- Unsupported-claim rate
- Repair success and repair-budget exhaustion rate
- Percentage of unverified packages reaching A1 policy: target `0`
- A2/A3 autonomous execution count: target `0`
- Non-allow-listed action execution count: target `0`
- `unsafe_claim_escape_rate`: target `0` on the committed adversarial software suite

The `unsafe_claim_escape_rate` target is a software-suite result, not clinical validation or a universal guarantee that hallucinations are eliminated.

### Deterministic surveillance performance

- Time from data arrival to suspicious signal
- Detector precision or positive predictive value on seeded scenarios
- False-positive rate on committed normal/noisy scenarios
- Sensitivity on committed seeded suspicious scenarios
- Deterministic result reproducibility across repeated runs

These are offline software-evaluation metrics until validated with appropriate real-world study design. They must not be presented as clinical performance.

### Workflow utility

- Reference human steps compared with Ngabo hero steps
- Reference human elapsed time compared with automated elapsed time
- Manual data-gathering and coordination steps eliminated
- Percentage of incidents with complete traceable evidence packages
- Percentage of external effects with durable intent, delivery result, and machine acknowledgement

### Adoption and ecosystem, when pilots begin

- Qualified workflow interviews and demonstrations completed
- Domain-professional contradictions and workflow gaps documented
- Controlled pilots or research collaborations established
- Repeated usage in an approved evaluation environment
- Validated integrations and external open-source contributions

---

## 9. Advantage

Ngabo's defensibility should come from verifiable architecture, workflow depth, evaluation evidence, and trusted integration rather than merely wrapping an LLM.

### Tangible advantages being built

- **Proof-Carrying Autonomy:** material model claims carry machine-checkable references and must pass deterministic verification before influencing action
- **Deterministic/agentic separation:** code owns scientific calculations, routing, verification, authorization, freshness, and idempotency; Gemini handles only bounded ambiguity and synthesis
- **Closed-loop autonomy:** the target proof covers event, investigation, external effect, and machine acknowledgement with zero human intervention
- **Safe abstention:** incomplete, stale, unauthorized, or unverifiable cases stop instead of fabricating completion
- **Open and auditable design:** architecture, safety policy, evaluations, synthetic fixtures, and limitations can be inspected
- **Non-replacement positioning:** Ngabo operates above existing laboratory and surveillance systems rather than demanding wholesale replacement

### Advantages to validate or develop

- Uganda- and Africa-specific workflow knowledge grounded in documented research and partnerships
- Institutional trust and integration relationships
- Validated AMR investigation scenarios and evaluation datasets
- Facility-specific operational knowledge learned under appropriate governance
- Standards-based connectors that lower deployment friction
- Published evidence that Ngabo improves surveillance-to-coordination workflow performance

Future advantages must remain hypotheses until supported by implementation, evaluation, partnerships, or measured deployment evidence.

---

## 10. Early-Adopter Hypothesis

The strongest first user is likely:

> **An AMR surveillance analyst, AMR focal person, or microbiology data manager at a facility that already produces structured AST data but still performs substantial manual work when investigating and coordinating unusual resistance patterns.**

The strongest first institutional environment should have:

- Routine bacterial culture and AST
- WHONET or another exportable structured microbiology dataset
- An active microbiology, AMR, IPC, or stewardship function
- A willingness to begin with synthetic, de-identified, controlled, or shadow-mode evaluation
- A domain professional able to challenge Ngabo's assumptions, investigation logic, and usefulness
- An authorized low-consequence integration target for testing safe coordination

This remains a hypothesis until direct user research and controlled evaluation confirm it.

---

## 11. Critical Risks and Assumptions

### Product assumptions to validate

- Surveillance-to-coordination is a meaningful bottleneck after existing tools surface AMR signals
- Users value an investigation and coordination layer more than another dashboard
- Available laboratory data contains enough context for useful automated investigation or safe abstention
- Proof-verified packages are understandable and useful to surveillance professionals
- A safe A1 autonomous lane removes meaningful manual friction without crossing clinical or official authority boundaries
- Institutions are willing to evaluate an open-source tool alongside existing workflows

### Major risks

- Poor, incomplete, or inconsistent laboratory data
- False-positive signals and alert fatigue
- Fabricated, unsupported, stale, or misclassified model claims
- Confusion between an investigation candidate and a confirmed outbreak
- Integration complexity across heterogeneous systems
- Patient privacy, data-protection, and health-data governance constraints
- Lack of trust or insufficient workflow utility
- Ngabo duplicating established local or national functionality
- Insufficient domain, operational, or clinical validation
- A demo that documents architecture without proving the deployed runtime outcome

### Safety principles

- Deterministic systems own parsing, scientific calculations, routing, verification, action classification, authorization, freshness, and idempotency
- Gemini cannot promote A2/A3 actions into the A1 autonomous lane
- Material model claims remain typed, evidence-linked, uncertainty-aware, and machine-verifiable
- Missing material facts cause safe abstention; they are never invented to preserve autonomy
- Only authorized A1 safe coordination can auto-execute in the public v0.1 hero
- Clinical, treatment, official outbreak, and other consequential decisions remain outside autonomous v0.1
- No real identifiable patient data appears in public repositories, evaluations, or hackathon demonstrations
- Software evaluation is not represented as clinical validation or regulatory approval

---

## 12. Validation Plan

### Phase 0 — Domain and workflow grounding

- Study WHONET workflows, AST interpretation boundaries, AMR surveillance, outbreak investigation, and the relevant Uganda context
- Interview domain professionals about the actual signal-to-investigation-to-coordination workflow
- Document existing-system capabilities to prevent unnecessary duplication
- Separate verified workflow evidence from assumptions and builder interpretations

### Phase 1 — Deterministic signal foundation

- Build representative synthetic WHONET-style fixtures
- Implement deterministic ingestion, normalization, validation, profile comparison, baselines, windows, and signal logic
- Certify normal, noisy, malformed, missing, and suspicious seeded scenarios offline
- Preserve deterministic provenance for every action-relevant finding

### Phase 2 — Proof-carrying autonomous workflow

- Prove the selected Google ADK version supports the required structured workflow and verifier-repair loop
- Implement event-driven fan-out/join orchestration
- Retrieve only approved provenance-carrying evidence
- Generate typed proof-carrying packages with explicit uncertainty
- Verify claims deterministically and repair within a hard budget or abstain
- Authorize only A1 actions after proof, policy, and freshness gates
- Execute through a durable idempotent outbox and receive machine acknowledgement

### Phase 3 — Safety, reliability, and utility evaluation

- Test A2/A3 blocking, missing-data abstention, unauthorized targets, prompt injection, fabricated references, forbidden claim escalation, stale state, branch failure, restart, and duplicate events
- Target zero unsafe claim escapes on the committed adversarial software suite
- Compare the builder's documented reference workflow with the zero-human hero
- Run three consecutive deployed hero E2Es
- Record measured outcomes, limitations, and failed scenarios without converting them into stronger claims

### Phase 4 — Professional validation

- Demonstrate Ngabo to qualified microbiology, AMR surveillance, epidemiology, IPC, or AMS professionals
- Test whether the problem, investigation package, uncertainty, and coordination workflow reflect real practice
- Document contradictions and workflow gaps instead of defending the prototype
- Refine the product around validated workflow pain and safe institutional boundaries

### Phase 5 — Controlled pilot pathway

- Identify a research or institutional partner willing to evaluate de-identified, controlled, or shadow-mode data
- Define governance, authorization, data protection, success metrics, and stop conditions before integration
- Compare Ngabo's workflow quality, elapsed time, and manual steps with the existing process
- Keep real clinical and official public-health decisions under appropriate human and institutional authority

The implementation roadmap and GitHub issues track delivery status. This canvas records the product hypotheses and evidence required to validate them.

---

## 13. MVP Boundary

### Ngabo v0.1 should prove one thing

> **A suspicious synthetic AMR signal can automatically complete event → proof-verified investigation → authorized A1 external action → machine acknowledgement with zero human intervention, while unsafe, incomplete, unverifiable, A2, and A3 cases are blocked or safely abstain.**

### In scope

- Representative synthetic WHONET-style input
- Deterministic validation, normalization, surveillance, and missingness assessment
- Pub/Sub-triggered Google ADK workflow
- Deterministic parallel investigation and join semantics
- Bounded Gemini reasoning and approved evidence retrieval
- Typed proof-carrying claims and deterministic verification
- Bounded automatic repair or safe abstention
- Deterministic A1 action policy and allow-list authorization
- Freshness validation
- Durable `ActionIntent`, outbox, and stable idempotency key
- Real authorized external test, sandbox, or internal coordination action
- Machine acknowledgement
- Observable UI timeline and zero-human metrics
- Audit trail and committed safety/reliability evaluation

### Explicitly out of scope for v0.1

- Autonomous diagnosis or treatment selection
- Autonomous outbreak confirmation or official declaration
- Autonomous A2 real operational escalation
- Contacting real patients, hospitals, or persons without explicit authorization
- Replacing WHONET, LIMS, or national surveillance infrastructure
- Nationwide deployment
- Real identifiable patient data
- Full genomic, multimodal, or cross-facility surveillance
- Dynamic multi-agent specialist fleets or an additional orchestration framework
- Production medical-device claims, clinical validation claims, or regulatory approval claims

---

## 14. Strategic Thesis

Ngabo is most compelling as **open-source public-health infrastructure with a DeepTech trajectory**, not as a disposable hackathon application.

The near-term project proves a narrow but complete autonomous workflow: a synthetic surveillance signal triggers a bounded investigation, machine-verifiable claims, deterministic safety policy, one safe external coordination effect, and a machine acknowledgement. It demonstrates operational autonomy without claiming clinical or official authority.

The longer-term opportunity is to make the broader AMR surveillance-to-response chain faster, more structured, more auditable, and less dependent on manually joining partially automated activities:

```text
AMR data
→ surveillance signal
→ proof-verified investigation
→ safe coordination
→ appropriately governed human or institutional decision for consequential actions
→ documented response and learning
```

Ngabo v0.1 autonomously proves only the safe A1 coordination lane. A2 operational escalation and A3 clinical or official decisions remain governed by authorized people and institutions.
