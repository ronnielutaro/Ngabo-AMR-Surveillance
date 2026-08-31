# Ngabo — Value Proposition Canvases

**Product:** Ngabo — Always-On Antimicrobial Resistance Surveillance & Coordination<br>
**Positioning:** Product direction: Connect → Watch → Investigate → Coordinate; v0.1 target: synthetic source → proof-verified A1 action → acknowledgement<br>
**Version:** 0.1  
**Date:** 2026-08-29  
**Status:** Product hypothesis and validation guide; not evidence of clinical validation, adoption, or customer demand

---

## Executive Decision

Ngabo has one product-direction value proposition, expressed differently for three participants in the adoption system:

> **Ngabo is designed to remove recurring human glue from governed laboratory data acquisition through deterministic surveillance, automatic investigation, and permitted coordination without replacing the systems that produce or govern the data.**

The current v0.1 target is narrower:

> **The v0.1 target is for a committed synthetic WHONET-style source to produce a deterministic surveillance signal that Ngabo turns into a proof-verified investigation package and one authorized, acknowledged safe-coordination action. Delivery must be supported by runtime evidence; no production laboratory-system connector is claimed.**

The three canvases are:

1. **Primary user:** the microbiology or AMR surveillance professional who repeatedly prepares or reviews surveillance data, translates meaningful signals into investigation-ready packages, and coordinates the next safe step.
2. **Institutional adopter and governor:** the laboratory, hospital, surveillance-programme, research, or public-health leader responsible for workflow performance, safety, accountability, and deployment.
3. **Platform or implementation partner:** the owner or implementer of WHONET, LIMS, ALIS, LDR, NIAMR, or another governed data platform that may provide authorized exports, records, or signals to Ngabo or receive its verified outputs.

These are related but not interchangeable. A practitioner may use the output, an institution may authorize and fund the deployment, and a platform owner may control integration. Treating them as one generic “AMR user” would hide different jobs, risks, and adoption barriers.

The builder's repeated AMR research and coordination workflow remains the **v0.1 BYOF evaluation reference**. It supports the hackathon utility claim but does not prove that practitioners or institutions have validated these canvases.

---

## 1. Evidence and Claim Discipline

### Evidence labels

| Label | Meaning |
|---|---|
| **Supported** | Grounded in repository contracts, documented research, public practitioner evidence, or implemented and measured behaviour |
| **Partially supported** | Direction is supported, but prevalence, importance, workflow detail, or solution fit remains uncertain |
| **Hypothesis** | Plausible proposition that requires interviews, observation, prototype testing, integration discovery, or a controlled pilot |

### Current evidence base

These canvases synthesize:

- [Lean Canvas](LEAN_CANVAS.md);
- [Competitor and Alternatives Analysis](COMPETITOR_ANALYSIS.md);
- [User Personas](USER_PERSONAS.md);
- [BYOF Friction](BYOF_FRICTION.md);
- [Operational Utility Evaluation](OPERATIONAL_UTILITY_EVALUATION.md);
- [Product Requirements](PRD.md);
- [Taskmaster Zero-Human Autonomy Contract](TASKMASTER_ZERO_HUMAN_AUTONOMY.md);
- [Proof-Carrying Reasoning](PROOF_CARRYING_REASONING.md);
- [Autonomous Effect Outbox](AUTONOMOUS_EFFECT_OUTBOX.md).

The competitor research intentionally included complaint-oriented public discussions. Those comments reveal possible pains and useful language, but they are not representative sentiment measurement. No segment below should be described as validated until direct research supports it.

---

## 2. Shared Product Boundary

### Product direction and v0.1 proof boundary

```text
PRODUCT DIRECTION
ALIS / WHONET / LIS/LIMS / governed export
→ governed source adapter
→ canonical surveillance state
→ deterministic watch / signal
→ proof-verified investigation
→ permitted coordination
→ machine acknowledgement

CURRENT v0.1 CERTIFIED SLICE
committed synthetic WHONET-style source
→ deterministic ingestion / surveillance signal
→ event-driven investigation
→ proof verification / A1 policy
→ authorized safe coordination
→ machine acknowledgement
```

Ngabo does not need to replace laboratory data entry, breakpoint management, national aggregation, or existing reporting systems to create value. Its product direction is the recurring surveillance-to-coordination operating loop. The v0.1 hackathon target uses a synthetic source to demonstrate a bounded complete slice; completion must not be claimed without the required runtime evidence, and no production ALIS, WHONET, LIS/LIMS, instrument, or hospital connector is claimed.

In these canvases, **always-on** means automatically responding to authorized data arrival or scheduled ingestion. It does not imply permanently running compute.

### Ngabo's value is constrained autonomy

Ngabo does not promise unrestricted autonomous response. It promises that a narrow safe workflow can proceed automatically while consequential authority remains governed:

| Action class | Meaning | Public v0.1 behaviour |
|---|---|---|
| A0 | Internal state and audit work | Autonomous |
| A1 | Safe, authorized external coordination | Autonomous after deterministic gates |
| A2 | Real operational escalation | Not autonomous by default |
| A3 | Clinical or official public-health decision | Never autonomous |

This boundary is part of the value proposition. It is not merely a compliance disclaimer.

---

## 3. Canvas A — Primary Surveillance Practitioner

### Segment definition

> **A microbiology or AMR surveillance professional responsible for translating structured AST data or an existing surveillance signal into an investigation-ready package and coordinating the next safe step.**

Likely roles include an AMR surveillance analyst, AMR focal person, microbiology data manager, clinical laboratory scientist with surveillance responsibilities, hospital epidemiology analyst, or public-health laboratory analyst.

The first user is assumed to work where structured or exportable microbiology data exists but investigation and coordination still require repeated manual work. This is a hypothesis to validate, not a statement about every Ugandan facility.

### Customer jobs

#### Functional jobs

| Priority | Job to be done | Evidence status |
|---|---|---|
| 1 | Determine whether a suspicious resistance signal is based on valid, current, sufficiently complete data | Partially supported |
| 2 | Identify the implicated isolates, resistance profiles, locations, dates, specimen context, and relevant baseline | Supported as a required reference workflow |
| 3 | Distinguish observed facts and deterministic findings from hypotheses or interpretation | Supported as a safety and communication need |
| 4 | Locate trusted guidance or evidence relevant to the signal | Supported as workflow friction; exact sources vary |
| 5 | Assemble a concise, review-ready investigation package | Supported as the core proposed output |
| 6 | Route the package to an authorized recipient or coordination system | Partially supported; actual routes vary by institution |
| 7 | Know whether the coordination action was delivered and acknowledged | Partially supported; acknowledgement expectations require validation |
| 8 | Preserve an auditable record that another person can understand and reproduce | Partially supported |

#### Emotional jobs

- Feel confident that an important signal was not missed or overstated.
- Avoid being personally responsible for an unsupported or poorly sourced escalation.
- Reduce uncertainty about what work remains after an alert appears.
- Trust that automation will stop when evidence or authorization is insufficient.

#### Social and professional jobs

- Communicate a defensible package to colleagues, supervisors, IPC, AMS, research, or public-health stakeholders.
- Demonstrate that conclusions came from traceable records and governed analysis.
- Maintain continuity when responsibility changes or specialist expertise is limited.
- Avoid appearing to substitute software confidence for professional authority.

### Pains

| Priority | Pain | Evidence status |
|---|---|---|
| 1 | Data inspection, comparison, evidence lookup, writing, validation, routing, and follow-up are spread across tools and people | Supported directionally |
| 2 | Alerts and dashboards can identify something unusual without assembling the context needed for the next action | Partially supported |
| 3 | Manual consolidation, duplicate entry, configuration, mapping, and data cleaning consume attention | Supported by research and practitioner comments |
| 4 | Workflow knowledge can be fragile when trained staff leave or responsibility changes | Supported by qualitative evidence |
| 5 | Noisy, robotic, or poorly explained alerts encourage dismissal and alert fatigue | Supported directionally; Ngabo-specific severity unknown |
| 6 | General-purpose AI may produce fluent but fabricated, stale, overconfident, or incorrectly classified claims | Supported as a technical risk; user-perceived importance unvalidated |
| 7 | A message may be sent without reliable confirmation that the intended system received it | Hypothesis |
| 8 | Low connectivity, power instability, limited support, and uneven infrastructure can undermine otherwise capable tools | Supported as an adoption constraint |

### Desired gains

| Priority | Gain | Evidence status |
|---|---|---|
| 1 | A review-ready package appears automatically after a qualifying signal | Hypothesis to validate with practitioners |
| 2 | Every material claim shows the record, deterministic finding, or approved source that supports it | Strong product hypothesis; user value unvalidated |
| 3 | Facts, findings, evidence statements, hypotheses, and action justification are visibly separated | Strong product hypothesis |
| 4 | Unsafe, stale, unsupported, or unauthorized work stops without silently creating an effect | Supported safety requirement |
| 5 | The next permitted coordination action completes once and returns acknowledgement | Hypothesis to validate against real workflows |
| 6 | Repeated investigation steps become consistent and reproducible across runs | Supported technical objective |
| 7 | Existing WHONET, LIMS, or national-platform work is preserved rather than replaced | Supported by competitor landscape |
| 8 | The user can understand what the agent did without reading private model reasoning or raw infrastructure logs | Supported UI objective |

### Ngabo products and services

- Governed ingestion of synthetic or authorized structured AMR data and signals.
- Deterministic validation, normalization, similarity, temporal/location, baseline, and missingness analysis.
- Event-triggered ADK investigation workflow.
- Approved-evidence retrieval with provenance and integrity checks.
- Typed proof-carrying incident packages.
- Deterministic claim and reference verification.
- Bounded automatic repair or safe abstention.
- Deterministic action classification, authorization, and freshness checks.
- Durable ActionIntent, idempotent external delivery, and machine acknowledgement.
- Incident/autonomy console showing canonical evidence and state.

### Pain relievers

| Pain | Ngabo response | v0.1 proof required |
|---|---|---|
| Fragmented repeated work | Orchestrate the qualifying surveillance event through acknowledgement in v0.1 | Three deployed event-to-ack runs |
| Manual comparison and context assembly | Run deterministic investigation capabilities and join their typed findings | Value-level detector and graph evidence |
| Unclear support for conclusions | Attach machine-checkable record, finding, and evidence references | Claim/reference verification suite |
| Unsafe or fabricated AI output | Fail closed, repair within a fixed budget, or abstain | Adversarial fabricated/forbidden claim tests |
| Noisy unexplained alerts | Show why the signal matters, what is known, what remains uncertain, and what policy permits | Browser-tested proof and policy views |
| Duplicate or stale coordination | Recheck freshness and reuse a stable idempotency key | Redelivery, crash, race, and stale-state tests |
| Lost handoff state | Persist canonical incident, intent, delivery, and acknowledgement truth | Restart/recovery evidence |

### Gain creators

- A single timeline connects signal, investigation, evidence, verification, authorization, delivery, and acknowledgement.
- Typed claim cards make evidence inspection faster than reconstructing support from prose.
- Explicit uncertainty allows useful investigation candidates without pretending to confirm an outbreak.
- Deterministic gates make the agent's permitted action envelope inspectable.
- Open architecture and adapters create a future path to coexist with existing surveillance systems.
- Zero-human metrics make the reduction in builder-reference workflow steps measurable.

### Fit statement

> **For AMR surveillance professionals who repeatedly prepare or review structured laboratory surveillance data, Ngabo is designed to keep the surveillance-to-coordination loop moving automatically. The v0.1 target assembles a traceable investigation package after a deterministic signal and completes the next authorized coordination step, while machine-verifying action-relevant claims and applying deterministic safety, freshness, and idempotency gates before acting.**

### Current alternatives

- Manually inspect data, calculate or obtain comparisons, search guidance, write a brief, email or message it, and follow up.
- Use WHONET, AMASS, LIMS, commercial surveillance, or national-platform reports and then coordinate outside the system.
- Build local spreadsheets, scripts, dashboards, and notification rules.
- Use a general-purpose AI assistant for drafting, followed by manual checking.

Ngabo must outperform these alternatives on workflow completion and inspectability, not merely produce a more attractive summary.

---

## 4. Canvas B — Institutional Adopter and Governor

### Segment definition

> **A leader accountable for AMR surveillance workflow performance, deployment risk, governance, auditability, and resourcing within a laboratory, hospital, network, research programme, implementing organization, or public-health institution.**

Possible roles include a laboratory director, AMR programme lead, IPC or AMS lead, surveillance manager, digital-health lead, research principal investigator, or technical programme manager. The economic buyer, policy owner, system owner, and daily user may be different people.

### Customer jobs

#### Functional jobs

- Improve the reliability and timeliness of signal-to-investigation coordination.
- Define which data, recipients, actions, and systems are authorized.
- Preserve institutional authority over clinical and official public-health decisions.
- Integrate new capability without discarding existing laboratory or national systems.
- Monitor whether automation is current, safe, reproducible, and recoverable.
- Control infrastructure cost, access, secrets, retention, and operational risk.
- Produce evidence for technical review, research evaluation, funders, governance, or audit.

#### Emotional and social jobs

- Avoid reputational or operational harm from unsafe AI claims or unauthorized actions.
- Demonstrate responsible innovation without overstating clinical readiness.
- Maintain confidence that failures become visible abstentions rather than hidden success states.
- Show that scarce technical and domain capacity is being used on review and governance rather than repetitive assembly.

### Pains

| Priority | Pain | Evidence status |
|---|---|---|
| 1 | AI systems can obscure why a claim was produced and who authorized an effect | Strong governance concern; customer priority unvalidated |
| 2 | Existing data investments may be threatened by replacement-oriented products or vendor lock-in | Partially supported |
| 3 | Integration, configuration, training, turnover, and technical support determine whether tools remain usable | Supported by adoption research |
| 4 | Alerts without ownership, context, or actionability can add workload instead of reducing it | Partially supported |
| 5 | Cloud cost, identity, secrets, deployment drift, and rollback create operational risk | Supported implementation concern |
| 6 | Synthetic demonstrations can be mistaken for clinical or national evidence | Supported claim-governance risk |
| 7 | A failed or retried effect can create duplicate coordination or inconsistent institutional records | Supported distributed-system risk |

### Desired gains

- A bounded automation policy that the institution owns rather than the model.
- Auditable evidence linking each material model claim to canonical support.
- Open, inspectable architecture with replaceable adapters and no forced surveillance-system replacement.
- Reproducible deployment from reviewed commit to immutable artifact and Cloud Run revision.
- Clear separation between synthetic software evidence, shadow-mode research, and validated operational use.
- Measured workflow utility, failure rates, unsafe-claim escapes, latency, cost, and recovery behaviour.
- A safe path from technical prototype to retrospective evaluation and shadow-mode pilot.

### Ngabo products and services

- Configurable deterministic action-class and allow-list policy.
- Approved source and evidence governance.
- Canonical audit trail and correlated event-to-ack telemetry.
- Fail-closed verifier, bounded repair, abstention, freshness, and idempotency controls.
- Keyless, least-privilege GCP deployment and reproducible release evidence.
- Open-source core with future integration, configuration, validation, hosting, and support options.
- Evaluation contracts that explicitly prevent clinical or public-health overclaiming.

### Pain relievers

| Institutional pain | Ngabo response |
|---|---|
| Model output treated as authority | Model proposes; deterministic verifier and policy decide eligibility |
| Uncontrolled action scope | A0/A1/A2/A3 policy keeps A2/A3 outside autonomous v0.1 |
| Opaque claims | Typed references and verification reports expose support and failure reasons |
| Duplicate external effects | Durable intent plus idempotent execution and acknowledgement |
| Replacement risk | Governed adapter and canonical-boundary design complement upstream systems |
| Demo-to-production confusion | Explicit release ladder from synthetic MVP to shadow-mode and validation |
| Cloud governance risk | Keyless identity, bounded spend, immutable artifacts, promotion, and rollback |

### Gain creators

- Institution-owned policy can expand only when authorization and evidence justify it.
- Adversarial evaluation creates a concrete safety conversation instead of vague “responsible AI” language.
- Open documentation supports technical, domain, governance, and funder review.
- The same canonical evidence powers runtime state, UI, evaluation, and release claims.
- Integration can start with a narrow authorized signal and coordination target rather than a full digital transformation.

### Fit statement

> **For institutions that want to test an always-on AMR surveillance and coordination loop without surrendering clinical or public-health authority, Ngabo provides an open, auditable architecture whose model claims, action eligibility, freshness, and external effects are deterministically governed. Its v0.1 evaluation begins with a bounded synthetic target and can mature toward governed source adapters only through evidence-gated evaluation.**

### Adoption conditions

Ngabo is not ready for institutional operational use merely because v0.1 succeeds. Adoption requires at least:

- an institution-owned intended use and action policy;
- authorized data and integration agreements;
- security, privacy, retention, and data-residency review;
- named operational and clinical/public-health accountability;
- retrospective and shadow-mode evaluation;
- local workflow and usability validation;
- incident response, rollback, support, and change-management processes.

---

## 5. Canvas C — Platform and Implementation Partner

### Segment definition

> **A team responsible for an upstream laboratory, surveillance, interoperability, or national data platform that needs downstream signals to become trustworthy, governed, and traceable coordination workflows.**

Potential contexts include WHONET-based programmes, LIMS or ALIS implementers, Uganda's Laboratory Data Repository, the NIAMR programme, research data platforms, and digital-health implementing partners. These are ecosystem hypotheses, not claimed partnerships.

### Partner jobs

- Capture, standardize, exchange, aggregate, or analyze AMR data reliably.
- Preserve the platform as canonical source for the data it owns.
- Expose governed events, APIs, exports, or reports to authorized downstream users.
- Make platform outputs more actionable without duplicating every downstream workflow.
- Prevent third-party AI from bypassing data governance, provenance, or institutional policy.
- Demonstrate how a signal led to a coordination outcome and acknowledgement.
- Extend capability through modular integrations rather than brittle one-off scripts.

### Pains

| Priority | Pain | Evidence status |
|---|---|---|
| 1 | Dashboards and reports may be informative without owning the final investigation and coordination workflow | Supported directionally |
| 2 | A downstream tool may duplicate ingestion, create conflicting truth, or imply that the upstream platform is obsolete | Strong strategic risk |
| 3 | Arbitrary AI access can create untraceable claims or weaken source governance | Supported architecture concern |
| 4 | Custom integrations can become brittle, unaudited, and difficult to support | General integration hypothesis |
| 5 | External actions may not return durable acknowledgement to the originating workflow | Hypothesis |
| 6 | Platform roadmaps may already include alerts, AI, or decision support, creating overlap and ownership ambiguity | Supported by competitor landscape |

### Desired gains

- A complementary surveillance-to-coordination component rather than a replacement data platform.
- Explicit contracts for canonical records, findings, approved evidence, packages, events, and acknowledgements.
- Traceable provenance from upstream source through downstream claim and action.
- Deterministic policy preventing a model from converting platform data into unauthorized authority.
- A narrow integration that can be evaluated before broader rollout.
- Clear attribution of which platform supplied data and which system verified or executed each step.

### Ngabo products and services

- Inbound signal and canonical-record adapter contracts.
- Versioned proof references back to upstream records and findings.
- Approved-evidence manifest and retrieval boundary.
- Event-driven investigation orchestration.
- Deterministic verification and action-policy services.
- Outbound coordination and acknowledgement ports.
- Correlated telemetry and audit exports.
- Future standards-based connectors, subject to governance and validation.

### Pain relievers

| Partner pain | Ngabo response |
|---|---|
| Conflicting source of truth | Canonical references identify ownership, version, and current state |
| Replacement concern | Ngabo can begin from a governed export or upstream signal and avoids reproducing full LIMS/WHONET/platform scope |
| Uncontrolled AI interpretation | Approved-source boundary and deterministic claim verification |
| Weak downstream traceability | Correlation IDs connect event, package, intent, delivery, and acknowledgement |
| Brittle side effects | Stable ports, durable intent, idempotency, and retry semantics |
| Unclear overlap | Explicit capability and responsibility matrix agreed before integration |

### Gain creators

- Existing surveillance investments gain a visible event-to-action path.
- Platform owners can keep data and official authority while delegating a bounded coordination workflow.
- Machine-verifiable references make cross-system audits and research evaluation more feasible.
- The integration can start with synthetic or sandbox signals before touching operational data.
- Open contracts reduce dependence on a single proprietary workflow engine.

### Fit statement

> **For AMR data and surveillance platforms that expose governed exports, records, or suspicious signals, Ngabo is designed to provide a modular surveillance, investigation, and safe-coordination layer. It preserves upstream data ownership, verifies model claims against governed references, and returns traceable delivery and acknowledgement evidence without asking the platform to become an autonomous agent. Production integration remains a hypothesis beyond the synthetic v0.1 target.**

### Partnership posture

Ngabo should approach WHONET, LDR, NIAMR, LIMS, and similar systems with four questions:

1. Which system owns each canonical record, finding, and policy decision?
2. What authorized event or export should start a downstream investigation?
3. Which coordination action is genuinely safe and useful to automate?
4. What acknowledgement or result should return to the originating system?

Until those questions are answered with a real partner, integration remains a roadmap hypothesis.

---

## 6. BYOF Bridge — What v0.1 Actually Proves

The builder reference workflow is:

```text
inspect surveillance signal and data
→ identify implicated isolates
→ compare resistance profiles
→ inspect temporal, location, and baseline context
→ inspect missing information
→ locate trusted guidance
→ separate facts from hypotheses
→ assemble an incident brief
→ validate claims and sources
→ route the result
→ track completion
```

The v0.1 hero attempts to replace those active steps after an event with:

```text
event
→ deterministic investigation
→ bounded evidence-grounded synthesis
→ proof verification
→ deterministic A1 policy
→ durable external coordination
→ machine acknowledgement
```

The intended measured result is:

```text
manual_prompt_count_to_start = 0
human_intervention_count     = 0
human_active_steps           = 0
clarification_count          = 0
approval_click_count         = 0
external_effect_count        = 1
machine_ack_count            = 1
```

This proves a bounded software workflow over synthetic data. It does not prove that the reference workflow is universal, that professionals would adopt Ngabo, or that it improves clinical or public-health outcomes.

---

## 7. Problem–Solution Fit Assessment

| Proposition | Current confidence | Why | Next evidence needed |
|---|---|---|---|
| The recurring AMR surveillance-to-coordination loop involves fragmented manual work | Medium | Uganda workflow research and wider practitioner evidence support the direction | Observe and map at least five relevant workflows |
| Existing surveillance tools should be complemented rather than replaced | High | Competitor landscape contains mature free, national, and commercial systems | Confirm integration boundaries with platform owners |
| A traceable review-ready package would be useful | Medium-low | Logical response to documented friction, but package shape is unvalidated | Package concept test with practitioners |
| Proof-carrying claims increase trust and actionability | Low-medium | Strong technical rationale; direct user demand is unproven | Compare ordinary AI summary with verified package in interviews/usability tests |
| One safe A1 coordination action can be automated usefully | Low | v0.1 can prove feasibility, not real-workflow desirability | Identify institution-specific action, target, owner, and acknowledgement |
| Zero-human completion is valuable for the bounded workflow | Medium for hackathon; low for practice | Strong competition fit; operational acceptability depends on context | Shadow-mode comparison and policy-owner review |
| Open, auditable architecture matters to institutional adopters | Medium-low | Plausible for public health and research; procurement evidence absent | Buyer and implementer interviews |
| Cloud delivery is acceptable in constrained settings | Low | Competitor research highlights offline and infrastructure constraints | Connectivity, cost, security, and deployment discovery |

### Overall fit judgment

Ngabo currently has a **clear problem hypothesis and differentiated solution architecture**, but not validated product–market fit. The strongest v0.1 evidence will establish technical feasibility and operational utility for the builder reference workflow. Practitioner desirability, institutional viability, integration feasibility, and field deployment suitability remain later validation work.

---

## 8. Highest-Risk Assumptions and Tests

### Assumption 1 — The operating loop and package solve a real recurring job

**Risk:** Ngabo may produce a technically impressive artifact that does not match how practitioners decide, communicate, or coordinate.

**Test:** Show a static and interactive package prototype to at least five relevant practitioners. Ask them to reconstruct what happened, identify missing information, state the next safe step, and compare it with their current workflow.

**Success signal:** Participants can use the package without extensive explanation and identify concrete work it replaces or accelerates.

### Assumption 2 — Proof verification is meaningful to users

**Risk:** Deterministic verification may be an excellent safety mechanism but an invisible or low-priority buying criterion.

**Test:** Compare two otherwise similar incident packages: one conventional AI summary and one with typed claims, references, verification, uncertainty, and policy state.

**Success signal:** Users identify fewer trust questions, find support faster, or prefer the verified package for a consequential handoff.

### Assumption 3 — A useful A1 action exists

**Risk:** Real workflows may require professional judgement before every meaningful external step, leaving only trivial automation.

**Test:** Ask practitioners and policy owners to classify candidate actions into A0–A3 and identify at least one useful, reversible, allow-listed A1 action with a machine-readable acknowledgement.

**Success signal:** An institution can name the target, payload boundary, authorization owner, failure policy, and acknowledgement semantics.

### Assumption 4 — Structured signals are accessible

**Risk:** Local data may be paper-based, incomplete, inaccessible, poorly mapped, or controlled by a separate programme.

**Test:** Conduct integration discovery using representative WHONET exports, LIMS schemas, or platform APIs without collecting patient-identifiable data.

**Success signal:** A governed minimum signal and reference contract can be mapped without rebuilding the upstream system.

### Assumption 5 — Institutions can operate the deployment

**Risk:** Cloud cost, connectivity, security, support, and change management may outweigh workflow benefit.

**Test:** Produce a deployment-options assessment covering managed cloud, institution cloud, hybrid, and offline-adjacent patterns.

**Success signal:** A prospective adopter can identify an acceptable ownership, cost, data, support, and recovery model.

---

## 9. Validation Sequence

### Phase 1 — Hackathon technical proof

- Complete the synthetic event-to-action-to-ack hero.
- Run three consecutive deployed scenarios.
- Prove zero-human counters, claim verification, repair/abstention, A1 policy, idempotency, and acknowledgement.
- Demonstrate the proof path clearly in the judge console.

### Phase 2 — Problem and package validation

- Conduct workflow interviews and observation with relevant practitioners.
- Test the incident-package content and visual hierarchy.
- Validate which pains are frequent, costly, risky, and currently underserved.
- Revise the primary-user canvas from actual evidence.

### Phase 3 — Integration and policy discovery

- Interview institutional policy owners and platform implementers.
- Map WHONET/LIMS/LDR/NIAMR-compatible signal and reference boundaries.
- Identify a real A1 action and acknowledgement contract.
- Define local governance, privacy, security, retention, and operating ownership.

### Phase 4 — Retrospective and shadow-mode evaluation

- Use approved retrospective data.
- Compare package quality, workflow steps, latency, false/unsupported claims, abstentions, and reviewer outcomes.
- Run prospectively in shadow mode without autonomous clinical or official authority.
- Expand autonomy only through institution-owned policy and measured evidence.

---

## 10. Messaging by Audience

### Practitioner

> **When a suspicious AMR signal appears, Ngabo assembles the records, deterministic findings, approved evidence, uncertainty, and next safe coordination step into one traceable package—then completes the authorized handoff and records acknowledgement.**

### Institutional leader

> **Ngabo lets an institution evaluate bounded AMR workflow autonomy without allowing the model to own clinical authority, action policy, evidence truth, or external-effect state.**

### Platform partner

> **Ngabo is designed to add a governed surveillance, investigation, and coordination layer while preserving the upstream platform as canonical data owner. The v0.1 target uses only a synthetic source.**

### Hackathon judge

> **Ngabo does not merely reason and act. It proves why it is allowed to act.**

---

## 11. Competitive Claim Guardrails

### Defensible positioning

- Ngabo's product direction spans governed connection, deterministic surveillance, investigation, and safe coordination.
- The public v0.1 target remains a synthetic, bounded source-to-signal-to-ack proof with no production source-system connector; completion requires runtime evidence.
- Proof-Carrying Autonomy makes action-relevant model claims explicit and machine-checkable where deterministic support exists.
- Existing laboratory, surveillance, and national platforms are potential upstream systems and partners.
- The public v0.1 hero is synthetic, bounded, non-clinical, and A1-only.

### Do not claim without stronger evidence

- Ngabo is the first or only autonomous AMR system.
- Existing systems cannot detect AMR signals or manage alerts.
- Uganda lacks AMR platforms or digital surveillance infrastructure.
- Practitioners broadly dislike current tools.
- Proof verification establishes medical truth or eliminates hallucination.
- Zero-human completion of the synthetic hero proves hospital productivity or improved outcomes.
- NIAMR, LDR, WHONET, or any institution is a partner unless a partnership exists.

---

## 12. Not Doing in v0.1

- Replacing WHONET, LIMS, ALIS, LDR, NIAMR, GLASS, or institutional governance.
- Performing primary laboratory instrument interpretation or regulated diagnostic work.
- Diagnosing, prescribing, confirming an outbreak, or issuing official public-health decisions.
- Contacting real hospitals, patients, or people without explicit authorization.
- Using arbitrary web pages or model-created citations as action-relevant evidence.
- Adding genomics, vector databases, multimodal ingestion, MedGemma, or a specialist agent fleet before the core hero is reliable.
- Claiming product–market fit from Reddit comments, desk research, architecture, or a hackathon demonstration.

---

## 13. Success Measures

### v0.1 software and hackathon measures

- five zero-human counters equal zero;
- exactly one authorized external effect and one machine acknowledgement per hero run;
- three consecutive deployed hero completions;
- zero unsafe claim escapes on the committed adversarial software suite;
- backend, UI, logs, receiver, and evaluation artifacts agree;
- judge can explain the proof-and-action distinction after the demonstration.

### Product-discovery measures

- percentage of interviewed practitioners who recognize the recurring data-to-surveillance-to-coordination workflow;
- jobs and pains ranked by observed frequency, severity, and risk;
- package comprehension and evidence-finding performance;
- candidate A1 actions accepted or rejected by policy owners;
- integration fields and ownership boundaries confirmed with implementers;
- willingness to participate in retrospective or shadow-mode evaluation.

These discovery measures require an approved research protocol and actual participants. No target percentage should be invented before the sample and method are defined.

---

## 14. Maintenance Rule

Update these canvases when any of the following occurs:

- practitioner interviews materially change the primary workflow;
- an institution identifies a real buyer, user, policy owner, or A1 action;
- a platform integration changes source-of-truth ownership;
- deployed evaluation contradicts an expected gain;
- competitor capabilities materially change Ngabo's position;
- the intended-use or action envelope expands.

When updating, preserve the distinction between:

```text
documented problem evidence
≠ validated customer demand
≠ implemented software
≠ deployed runtime proof
≠ clinical or public-health effectiveness
```

---

## 15. Final Value Proposition

> **Ngabo is designed to complement existing laboratory and AMR surveillance systems with an always-on operating loop: connect through governed adapters, watch deterministic surveillance state, investigate meaningful signals, and complete only permitted coordination with acknowledgement. Its v0.1 target is narrower: a committed synthetic WHONET-style source should drive a transparent, bounded, reproducible source-to-signal-to-action workflow with proof-verified model claims and no autonomous clinical authority. Completion must be supported by runtime evidence.**
