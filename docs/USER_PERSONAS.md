# Ngabo — User Personas

**Product:** Ngabo — Always-On Antimicrobial Resistance Surveillance & Coordination  
**Positioning:** Connect → Watch → Investigate → Coordinate  
**Initial context:** Uganda and African health systems  
**Version:** 0.1  
**Date:** 2026-08-31  
**Status:** Product hypothesis and validation guide; not evidence of adoption, willingness to pay, clinical validation, or a confirmed institutional workflow

---

## 1. Purpose

This document defines the user and institutional personas most likely to feel the recurring workflow pain Ngabo is designed to remove.

Ngabo should not optimize for a generic "AMR user." Different participants experience different parts of the workflow:

- one person may manually prepare and reconcile laboratory surveillance data;
- another may be responsible for interpreting unusual resistance patterns;
- another may prepare committee analytics and reports;
- another may need reliable IPC/AMS coordination;
- a national programme may receive data and quality problems from many facilities at once.

The central product thesis is:

> **Your laboratory keeps doing its normal work. Ngabo keeps the AMR surveillance job done.**

Ngabo aims to reduce recurring human glue across four stages:

```text
CONNECT
routine microbiology / AST data
        ↓
WATCH
continuous deterministic surveillance
        ↓
INVESTIGATE
automatic evidence-grounded investigation
        ↓
COORDINATE
safe authorized action + acknowledgement
```

The strongest personas are therefore those who already spend meaningful time moving, cleaning, inspecting, interpreting, packaging, routing, or following up on AMR surveillance work.

---

## 2. Evidence and Persona Discipline

These personas are **working product archetypes**, not invented named people and not validated customer segments.

Use these evidence labels:

| Label | Meaning |
|---|---|
| **Supported directionally** | Consistent with repository research, public workflow evidence, current product contracts, or the documented builder reference workflow |
| **Partially supported** | Plausible and directionally supported, but prevalence, frequency, ownership, or importance still requires direct practitioner validation |
| **Hypothesis** | Requires interviews, workflow observation, integration discovery, or controlled pilot evidence |

Related repository sources include:

- [Lean Canvas](LEAN_CANVAS.md)
- [Value Proposition Canvases](VALUE_PROPOSITION_CANVAS.md)
- [BYOF Friction](BYOF_FRICTION.md)
- [Competitor and Alternatives Analysis](COMPETITOR_ANALYSIS.md)
- [Product Requirements](PRD.md)
- [Operational Utility Evaluation](OPERATIONAL_UTILITY_EVALUATION.md)

Do not describe any persona below as a confirmed customer, buyer, partner, or validated user until direct evidence supports that claim.

---

## 3. Persona Priority Map

### Initial ranking by likely pain intensity

| Rank | Persona | Why the pain may be high | Likely Ngabo role |
|---|---|---|---|
| **1** | AMR surveillance focal person / microbiology data manager | Directly owns recurring surveillance preparation, data quality, investigation context, reporting, or coordination work | Primary daily/weekly operational user |
| **2** | Microbiologist with surveillance responsibilities | Surveillance work competes with laboratory/scientific responsibilities; repeated data stitching consumes scarce specialist attention | Primary user / expert reviewer |
| **3** | Hospital biostatistician or data officer supporting AMR | Often helps consolidate, clean, analyze, prepare, and disseminate surveillance outputs across systems and committees | Primary/secondary operational user |
| **4** | IPC / AMS programme lead | Depends on timely, contextualized, defensible surveillance outputs but may not prepare the raw data personally | Downstream user / policy stakeholder |
| **5** | National AMR programme / NCC / NMRL / surveillance network team | Receives repeated submissions, quality issues, analyses, and signals across multiple facilities; workflow frequency compounds at network scale | Institutional/network user, buyer, governor, or operator |

This order is a **product hypothesis**. Persona #5 may ultimately represent the largest institutional opportunity even if personas #1–#3 feel the day-to-day pain more directly.

---

# Persona 1 — AMR Surveillance Focal Person / Microbiology Data Manager

## 4. Persona summary

> **The person responsible for keeping AMR surveillance current and turning routine laboratory data into usable surveillance information.**

Possible role labels include:

- AMR focal person;
- AMR surveillance officer;
- microbiology data manager;
- surveillance analyst;
- laboratory surveillance focal person.

This is Ngabo's strongest initial primary-user hypothesis.

### Core job to be done

> **When routine microbiology and AST results accumulate, keep surveillance data current, identify what deserves attention, and make sure meaningful resistance signals become defensible, coordinated investigations without repeatedly reconstructing the workflow by hand.**

### Likely workflow frequency

| Work | Likely cadence |
|---|---|
| New microbiology/AST results become available | Daily / continuous in active laboratories |
| Data import, entry, extraction, reconciliation, or preparation | Daily to weekly depending on digitization |
| Surveillance refresh / review | Daily, weekly, or periodic depending on facility workflow |
| Line lists / antibiograms / routine analytics | Weekly, monthly, quarterly, or on demand |
| Investigation of meaningful signal | Event-driven |
| Committee / programme coordination | Event-driven plus scheduled meetings/reporting |

The key product insight is that the **data and surveillance-maintenance job may be high frequency even when meaningful incidents are relatively infrequent**.

## 5. Current workflow without Ngabo

A representative workflow may look like:

```text
routine lab results
        ↓
ALIS / WHONET / LIS / Excel / instrument export
        ↓
extract / transcribe / convert
        ↓
check headers / codes / dates / organism / AST fields
        ↓
clean / reconcile / deduplicate
        ↓
refresh surveillance analysis
        ↓
construct line list / antibiogram / trend view
        ↓
notice something unusual
        ↓
identify implicated isolates
        ↓
compare resistance patterns
        ↓
inspect ward / location / time / specimen / baseline
        ↓
check what is missing
        ↓
search trusted guidance
        ↓
assemble brief / report
        ↓
share with IPC / AMS / microbiology / management / programme team
        ↓
follow up
```

Not every institution follows this exact sequence. The important pattern is that **the user often acts as the integration layer between data systems, surveillance analysis, investigation, and coordination**.

## 6. Highest-friction tasks

### Data readiness

- exporting or receiving repeated files;
- manual transcription or duplicate entry where systems do not integrate;
- converting between ALIS, WHONET/BacLink, Excel, LIS, or instrument-export formats;
- checking required fields;
- resolving duplicates and replayed submissions;
- maintaining data freshness;
- remembering to refresh surveillance analysis.

### Investigation

- reconstructing which isolates generated the signal;
- comparing phenotypes and resistance profiles;
- checking temporal and location concentration;
- comparing against baseline;
- identifying missing material context;
- separating what is known from what is hypothesized.

### Coordination

- preparing a concise review-ready package;
- explaining why something was flagged;
- attaching evidence and limitations;
- sending it to the correct recipient;
- tracking whether it was received;
- preserving an audit trail.

## 7. Emotional and professional pains

- Fear of overlooking a meaningful resistance pattern.
- Fear of overstating a weak or incomplete signal.
- Frustration when surveillance work repeatedly depends on manual exports and spreadsheets.
- Context switching between laboratory systems, Excel, WHONET, email, guidance, and committee preparation.
- Reliance on tacit workflow knowledge that may disappear when trained staff move or leave.
- Responsibility for explaining where a conclusion came from.

## 8. What Ngabo should remove

```text
BEFORE
manual acquisition / preparation
→ manual surveillance refresh
→ manual context reconstruction
→ manual evidence assembly
→ manual routing / follow-up

AFTER
routine lab data
→ Ngabo continuously maintains the surveillance loop
→ user sees only meaningful, traceable exceptions and outcomes
```

The ideal user experience is **not spending more time inside Ngabo**. It is having less surveillance workflow to operate manually.

## 9. Painkiller features for this persona

- governed source adapters;
- watched-folder or scheduled automatic ingestion;
- deterministic validation and normalization;
- source hashing and replay-safe deduplication;
- freshness and completeness status;
- continuous surveillance refresh;
- automatic incident creation when criteria pass;
- automatic deterministic investigation;
- evidence-grounded proof-carrying package;
- safe A1 coordination and acknowledgement;
- incident/autonomy console showing what happened without requiring chat.

## 10. Success metrics

- manual exports per reporting period;
- manual transcription steps;
- manual file uploads;
- time from source arrival to canonical surveillance state;
- surveillance refreshes requiring human initiation;
- time from signal to investigation-ready package;
- active human steps per incident;
- percentage of meaningful incidents with traceable investigation packages;
- delivery and acknowledgement completeness.

## 11. Adoption blockers

- no structured/exportable data;
- very low microbiology volume;
- unclear responsibility for surveillance;
- weak connectivity/infrastructure;
- lack of institutional authorization for data integration;
- distrust of automation in surveillance;
- existing workflow already sufficiently automated.

---

# Persona 2 — Microbiologist / Clinical Laboratory Scientist with Surveillance Responsibilities

## 12. Persona summary

> **A laboratory professional whose primary expertise is microbiology but who also carries surveillance, interpretation, quality, or reporting responsibilities.**

This persona matters because their surveillance work competes directly with scarce laboratory and scientific capacity.

### Core job to be done

> **Help the hospital understand important resistance patterns without spending disproportionate specialist time moving data, rebuilding surveillance context, or repeatedly preparing the same analytical material.**

## 13. Current workflow without Ngabo

```text
perform / oversee diagnostic microbiology
        ↓
review organism identification and AST quality
        ↓
ensure results enter ALIS / WHONET / LIS / registers
        ↓
help correct mapping / coding / interpretation problems
        ↓
review surveillance outputs
        ↓
investigate unusual resistance patterns
        ↓
explain biological / laboratory significance
        ↓
prepare or contribute to reports / line lists / committee material
        ↓
support IPC / AMS / clinicians / surveillance programme
```

## 14. Pain profile

The pain is not simply "analysis is hard." It is **opportunity cost**.

Every hour spent:

- converting files;
- fixing data formatting;
- maintaining spreadsheets;
- reconstructing line lists;
- searching historical context;
- preparing repeated reports;

is time not spent on:

- laboratory quality;
- difficult isolates;
- diagnostic interpretation;
- mentorship/training;
- infection-control support;
- scientific review.

## 15. What Ngabo should do for this persona

Ngabo should behave like a **surveillance operations layer**, not a replacement microbiologist.

It should:

- keep data current automatically;
- surface only meaningful issues;
- show why something was flagged;
- preserve the exact isolate/finding provenance;
- distinguish deterministic findings from Gemini hypotheses;
- expose missingness and limitations;
- produce review-ready context before the microbiologist needs to intervene;
- never claim clinical or outbreak authority on the microbiologist's behalf.

## 16. Painkiller moment

The strongest experience is:

> **"I did not spend the morning rebuilding the data trail. Ngabo already assembled the records, comparisons, baseline, missingness, evidence, and audit trail. I can spend my time judging the microbiological significance instead."**

## 17. Success metrics

- specialist hours spent on surveillance data preparation;
- repeated manual calculations eliminated;
- percentage of incidents arriving with complete provenance;
- time required for expert review;
- false/noisy alert burden;
- percentage of outputs requiring major context reconstruction before use.

---

# Persona 3 — Hospital Biostatistician / Data Officer Supporting AMR

## 18. Persona summary

> **A hospital data professional responsible for cleaning, consolidating, analyzing, preparing, or disseminating AMR surveillance information.**

Possible role labels include:

- biostatistician;
- data officer;
- health information officer;
- surveillance data analyst;
- records/data-management staff supporting microbiology or AMR.

### Core job to be done

> **Keep the AMR dataset usable and turn raw facility data into timely, reproducible analytics and reporting products without constantly rebuilding manual Excel workflows.**

## 19. Current workflow without Ngabo

A likely pattern is:

```text
receive / extract ALIS, WHONET, LIS, or spreadsheet data
        ↓
combine sources
        ↓
quality checks
        ↓
clean / normalize
        ↓
resolve duplicates / missing values
        ↓
filter by facility / ward / organism / antibiotic / period
        ↓
prepare tables / line lists / charts / antibiogram inputs
        ↓
share outputs with microbiology / AMR / IPC / AMS teams
        ↓
repeat for next period
```

The recurring problem is that analysis logic and data preparation can become embedded in fragile spreadsheets, local scripts, undocumented steps, or one person's memory.

## 20. Highest-friction tasks

- repeated extraction;
- reconciling inconsistent columns or coding;
- cleaning and mapping;
- checking duplicates;
- keeping longitudinal data current;
- recreating reports for different committees/time windows;
- tracing where a value came from;
- explaining changes after a source file is updated;
- repeated ad hoc requests for "just one more cut" of the same data.

## 21. Ngabo value

Ngabo can move this persona from:

```text
spreadsheet operator
```

toward:

```text
data-quality governor / analyst / exception reviewer
```

Ngabo should automate the deterministic repetition while keeping mapping, provenance, and validation inspectable.

## 22. Painkiller features

- adapter-based acquisition;
- source identity and replay protection;
- canonical schema;
- structured validation reports;
- deterministic deduplication;
- automatic surveillance refresh;
- immutable provenance;
- reproducible finding IDs and versions;
- machine-readable export/audit evidence;
- clear failure states instead of silent row loss.

## 23. Success metrics

- recurring spreadsheet steps eliminated;
- percentage of source imports handled automatically;
- number of manual data transformations per cycle;
- reconciliation errors;
- time spent producing recurring surveillance products;
- reproducibility of the same result from the same source;
- time required to explain or audit a published value.

---

# Persona 4 — IPC / AMS Programme Lead

## 24. Persona summary

> **A downstream programme leader who needs timely, trustworthy surveillance information to coordinate infection-prevention or antimicrobial-stewardship work.**

This person may not touch WHONET or ALIS every day. Their pain begins when surveillance information is late, weakly contextualized, difficult to defend, or disconnected from coordination.

Possible roles include:

- IPC lead;
- IPC focal person;
- antimicrobial stewardship lead;
- clinical pharmacist with stewardship responsibilities;
- hospital epidemiology lead;
- Medicines and Therapeutics Committee participant.

### Core job to be done

> **Know when a resistance signal deserves attention, understand why, and receive a concise evidence-backed package early enough to coordinate the next appropriate step.**

## 25. Current workflow without Ngabo

```text
wait for surveillance report / microbiology communication
        ↓
receive line list / antibiogram / email / verbal update / committee paper
        ↓
ask for additional context
        ↓
clarify affected isolates / wards / dates / resistance pattern
        ↓
assess whether the issue is credible/actionable
        ↓
coordinate discussion / review / follow-up
        ↓
track whether requested work happened
```

## 26. Pains

- Information arrives after substantial delay.
- Alerts may lack enough context to support action.
- It may be unclear which statements are facts versus interpretation.
- Different teams may work from different versions of the same data.
- Important limitations may be buried in prose.
- Coordination can disappear into email/message threads.
- There may be no reliable acknowledgement trail.

## 27. Ngabo value

This persona benefits most from the **Investigate → Coordinate** half of Ngabo.

The ideal package answers:

- What happened?
- Why was it flagged?
- Which isolates/records support it?
- What deterministic findings support it?
- What remains uncertain?
- Which approved evidence is relevant?
- What action class is permitted?
- What was sent?
- Was it acknowledged?

## 28. Important authority boundary

Ngabo must **not** turn IPC/AMS programme leads into passive recipients of model authority.

The system can automate safe A1 coordination, but:

- Gemini cannot declare an outbreak;
- Gemini cannot prescribe treatment;
- Gemini cannot authorize A2/A3 action;
- consequential institutional decisions remain governed by authorized people and policy.

## 29. Success metrics

- signal-to-coordination latency;
- number of clarification loops needed before review;
- percentage of packages with explicit provenance and uncertainty;
- acknowledgement completion;
- percentage of unsafe/incomplete situations correctly blocked;
- time from receiving a package to understanding why the signal matters.

---

# Persona 5 — National AMR Programme / NCC / NMRL / Surveillance Network Team

## 30. Persona summary

> **A programme or reference-laboratory team responsible for receiving, validating, aggregating, analyzing, monitoring, and coordinating AMR surveillance across multiple facilities.**

This persona may include:

- national AMR coordination staff;
- national surveillance analysts;
- national/reference laboratory teams;
- programme data managers;
- public-health surveillance officers;
- implementing-partner technical teams supporting national AMR surveillance.

This may become Ngabo's most important **institutional-scale opportunity**, because workflow frequency compounds across sites.

### Core job to be done

> **Keep a multi-facility AMR surveillance network current, identify which data or signals require attention, and coordinate consistent follow-up without manually stitching together every site's submissions and analyses.**

## 31. Why frequency compounds

At one hospital:

```text
routine lab data
→ recurring surveillance maintenance
→ occasional meaningful incident
```

Across many hospitals:

```text
Site A ─┐
Site B ─┤
Site C ─┤
...     ├─→ continuous incoming submissions
Site N ─┘
             ↓
      many data-quality states
             ↓
      many surveillance refreshes
             ↓
      many possible signals
             ↓
      many follow-up pathways
```

Even if a single facility produces meaningful investigation signals only occasionally, a network may face **continuous operational surveillance work**.

## 32. Current workflow without Ngabo

A representative network workflow may include:

```text
receive files / exports / submissions from facilities
        ↓
verify completeness / timeliness
        ↓
map and reconcile heterogeneous source formats
        ↓
clean / deduplicate / resolve anomalies
        ↓
aggregate / analyze
        ↓
identify facility-level or network-level issues
        ↓
contact facility for clarification / correction
        ↓
prepare national outputs / reports
        ↓
route feedback / guidance
        ↓
track follow-up
```

This exact division of responsibility varies by programme. The product hypothesis is that **network scale amplifies integration, quality, freshness, and coordination burden**.

## 33. Highest-friction tasks

- heterogeneous source systems;
- repeated facility submissions;
- late or missing data;
- changed/replayed files;
- inconsistent mappings;
- cross-site data quality;
- preserving source provenance;
- identifying which issues deserve human attention;
- repeated communication back to facilities;
- maintaining an auditable longitudinal view of what changed and what was done.

## 34. Ngabo network value

Longer-term, Ngabo could act as a **surveillance operations layer across participating sites**:

```text
Facility source adapters
        ↓
governed ingestion
        ↓
source identity + provenance
        ↓
automatic QC / normalization / dedup
        ↓
facility surveillance state
        ↓
priority signals
        ↓
automatic investigation
        ↓
proof-verified coordination workflow
```

This is a strategic direction, not a v0.1 implementation claim.

## 35. Painkiller features

- multi-source adapter framework;
- facility/source-level provenance;
- freshness monitoring;
- deterministic QC outcomes;
- replay and duplicate protection;
- facility-specific canonical state;
- automatic surveillance refresh;
- priority-based exception queues;
- traceable incident packages;
- authorized coordination routes;
- acknowledgement tracking;
- network-level operational metrics.

## 36. Institutional success metrics

- facilities requiring manual file handling;
- submission-to-canonical latency;
- unresolved data-quality issues;
- repeated/replayed source handling;
- percentage of facilities current within policy-defined freshness window;
- number of manual follow-up contacts per reporting period;
- time from significant facility signal to national/programme visibility;
- percentage of coordinated actions with acknowledgement;
- analyst hours spent on recurring preparation versus exception review.

## 37. Adoption blockers

- governance and data-sharing authority;
- data residency/privacy constraints;
- heterogeneous source systems;
- inconsistent local data maturity;
- institution-specific workflow variation;
- network connectivity;
- integration ownership and support;
- public-health authority boundaries;
- need for retrospective and shadow-mode validation before operational use.

---

# 38. Cross-Persona Job Map

| Workflow stage | AMR focal/data manager | Microbiologist | Biostatistician/data officer | IPC/AMS lead | National programme |
|---|---|---|---|---|---|
| **Connect** | High pain | Medium | High pain | Low | Very high at network scale |
| **Validate / clean** | High | Medium/high | Very high | Low | Very high |
| **Watch / refresh surveillance** | Very high | Medium/high | High | Medium | Very high |
| **Interpret signal** | High | Very high | Medium | High | High |
| **Assemble evidence/context** | Very high | High | Medium | High | High |
| **Verify claims / limitations** | High | Very high | Medium | High | High |
| **Coordinate** | High | Medium | Medium | Very high | Very high |
| **Track acknowledgement** | Medium/high | Low/medium | Low/medium | High | High |

This table is a hypothesis map for research prioritization, not a measured burden score.

---

# 39. User vs Buyer vs Governor vs Integration Owner

Ngabo adoption is likely multi-party.

| Role in adoption | Likely participants |
|---|---|
| **Daily/weekly user** | AMR focal person, microbiology data manager, biostatistician/data officer, microbiologist |
| **Expert reviewer** | Microbiologist, epidemiologist, IPC/AMS lead |
| **Workflow beneficiary** | IPC, AMS, Medicines and Therapeutics Committee, surveillance leadership |
| **Institutional buyer/funder** | Hospital leadership, research programme, public-health agency, donor/implementing partner |
| **Policy/governance owner** | Hospital/health-system leadership, AMR programme, IPC/AMS governance, public-health authority |
| **Integration owner** | Laboratory IT, ALIS/LIS implementation team, digital-health unit, WHONET/LIMS platform team, national programme infrastructure team |

A product that delights the AMR focal person but cannot satisfy governance and integration requirements will not deploy. Conversely, an institution may fund the system while daily users determine whether it actually removes work.

---

# 40. Preferred Early-Adopter Environment

The strongest first deployment hypothesis is not "any hospital."

Prefer an environment with:

- routine bacterial culture and AST;
- structured or exportable microbiology data;
- an established WHONET, ALIS, LIS/LIMS, BacLink, spreadsheet, or similar surveillance workflow;
- enough sample volume that data freshness and surveillance refresh are recurring jobs;
- an AMR focal person, microbiologist, data officer, IPC, or AMS function;
- recurring surveillance reporting or committee obligations;
- visible manual extraction/cleaning/reporting/coordination burden;
- willingness to begin with de-identified, retrospective, synthetic, or shadow-mode evaluation;
- an authorized low-consequence integration target for safe A1 coordination.

### Strong painkiller signal

A prospective site says something equivalent to:

> "We already have the microbiology data. The problem is getting it out, keeping it clean/current, rerunning the surveillance work, figuring out which signals matter, preparing the context, and getting it to the right people."

### Weak painkiller signal

A site has:

- little or no routine culture/AST;
- no structured data;
- no active surveillance process;
- no one accountable for AMR surveillance;
- very low volume;
- no recurring data/reporting burden.

Ngabo may be a vitamin in that environment until the upstream surveillance capability itself exists.

---

# 41. Anti-Personas / Not the Initial User

Ngabo should not initially optimize for:

### Individual clinician seeking treatment advice

Ngabo is not a prescribing or diagnosis assistant.

### Patient or public user

Ngabo is not a patient-facing AMR decision product.

### Hospital with no functional microbiology surveillance data

Ngabo cannot create reliable AMR surveillance from data that is never generated or captured.

### Facility seeking only a dashboard

A dashboard-only need is not Ngabo's strongest differentiated wedge.

### Institution seeking autonomous outbreak declaration or treatment policy

A3 official/clinical authority is deliberately outside Ngabo's autonomous lane.

---

# 42. Persona-Specific Positioning

## AMR focal person / microbiology data manager

> **Stop operating the surveillance workflow manually. Ngabo keeps your laboratory data current, watches for meaningful resistance signals, assembles the investigation, and closes the permitted coordination loop.**

## Microbiologist

> **Spend specialist time judging microbiology, not stitching surveillance data together. Ngabo prepares the traceable context before you need it.**

## Biostatistician / data officer

> **Replace recurring spreadsheet plumbing with a reproducible, provenance-aware surveillance pipeline that stays current automatically.**

## IPC / AMS lead

> **Receive the signal with the evidence, uncertainty, verification state, and coordination trail already attached instead of chasing context across teams.**

## National AMR programme / surveillance network

> **Turn multi-site submissions into a continuously maintained, exception-driven surveillance operation instead of a recurring cycle of file handling, cleaning, analysis, and follow-up.**

---

# 43. Product Implications

These personas imply several product priorities.

## Data ingestion is a first-class product surface

Ngabo's ingestion architecture should mature beyond a demo CSV toward:

```text
manual governed import
        ↓
watched-folder ingestion
        ↓
scheduled source connector
        ↓
event/API integration
```

The goal is to meet data where the laboratory already produces it, not force the user to become Ngabo's data-pipeline operator.

## Quiet automation is preferable to engagement

The desired usage pattern is not necessarily high UI engagement.

```text
routine data arrives
→ Ngabo processes quietly
→ no material signal
→ no interruption
```

When something matters:

```text
signal
→ automatic investigation
→ proof verification
→ safe coordination
→ acknowledgement
```

A user spending less time operating surveillance is a product success, not an engagement failure.

## Exception-driven UX

The judge/operator console should prioritize:

- what changed;
- what was automatically processed;
- what requires attention;
- why a signal was generated;
- what is fact versus hypothesis;
- what proof passed/failed;
- what action was permitted/blocked;
- whether coordination was delivered/acknowledged.

It should not become a general chat interface.

## High system autonomy, low model authority

Across every persona:

- deterministic code owns canonical facts and scientific calculations;
- Gemini contributes bounded proposals where judgment is useful;
- deterministic verification owns claim eligibility;
- deterministic policy owns autonomous action authorization;
- external systems own delivery/acknowledgement facts.

This allows Ngabo to remove human workflow without requiring users to trust model confidence as authority.

---

# 44. Validation Questions by Persona

## AMR focal person / microbiology data manager

1. What systems do you receive microbiology/AST data from?
2. How often do you export, enter, reconcile, clean, or refresh it?
3. Which parts of that process are manual?
4. How do you know the surveillance dataset is current?
5. What happens when you notice something unusual?
6. Which outputs do you repeatedly prepare?
7. Who receives them?
8. What do you wish happened automatically?

## Microbiologist

1. How much surveillance work sits alongside routine laboratory responsibilities?
2. Which data-preparation tasks consume specialist time unnecessarily?
3. What evidence/context must exist before you trust an unusual signal?
4. Which parts could software safely prepare before expert review?
5. What kinds of automation would create risk or mistrust?

## Biostatistician / data officer

1. Which files and systems do you combine?
2. What cleaning/mapping rules live in Excel or local scripts?
3. Which reports are recreated repeatedly?
4. How are duplicates and changed submissions handled?
5. Which data-quality failures consume the most time?
6. What would make a continuous ingestion pipeline trustworthy?

## IPC / AMS lead

1. How do resistance concerns reach your team today?
2. What context is usually missing from the first communication?
3. How many clarification loops occur before action is possible?
4. What information should always accompany a signal?
5. Which coordination steps could be automated safely?
6. Which decisions must remain human/institutional?

## National programme / network team

1. How do facilities currently submit AMR data?
2. How often do submissions arrive?
3. What proportion needs manual cleaning or follow-up?
4. Which source systems create the most integration friction?
5. How is freshness tracked by facility?
6. How are changed/replayed files handled?
7. How do facility-level signals get escalated or reviewed?
8. Which recurring national workflows would benefit from exception-driven automation?

---

# 45. Validation Priorities

The highest-value research questions are:

1. **Who actually owns the recurring extraction/cleaning/surveillance-refresh work at target facilities?**
2. **How often is that work performed?**
3. **Which source systems and export mechanisms are used in practice?**
4. **How many active human steps exist from new lab data to a current surveillance view?**
5. **How many steps exist from meaningful signal to coordinated follow-up?**
6. **Which steps are painful enough that users would change workflow or institutions would fund integration?**
7. **Would automatic acquisition materially reduce burden, or are upstream systems already sufficiently automated?**
8. **At what scale does Ngabo shift from facility tool to network operations infrastructure?**

Until interviews or pilot evidence answer these questions, frequency and willingness-to-pay claims remain hypotheses.

---

# 46. Strategic Persona Thesis

Ngabo's strongest user is not someone who wants to "use AI for AMR."

It is someone whose current job contains recurring surveillance operations that software can remove.

The product should therefore optimize for:

> **high-frequency recurring workflow removal + low-frequency high-value exception handling.**

At facility level:

```text
routine microbiology data
→ continuous automated surveillance maintenance
→ occasional meaningful incident
→ automatic investigation and safe coordination
```

At network level:

```text
many facilities
→ continuous incoming data and QC states
→ many surveillance updates
→ multiple possible incidents
→ prioritized automatic investigation and coordination
```

That is why Ngabo's long-term opportunity is larger than an AMR alerting dashboard or AI investigation assistant.

> **Ngabo can become an always-on AMR surveillance operating layer that removes human glue from data acquisition through acknowledged coordination while preserving institutional authority for consequential decisions.**
