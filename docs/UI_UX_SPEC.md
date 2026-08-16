# Ngabo — UI/UX Implementation Specification

**Version:** 0.1  
**Date:** 2026-08-16  
**Status:** Source-of-truth frontend implementation contract  
**Frontend:** Next.js + TypeScript + Tailwind CSS + shadcn/ui

---

## 1. Product UI Principle

> **Ngabo is an AMR incident-response console, not “ChatGPT for antimicrobial resistance.”**

The agent should mostly work behind the scenes. The UI exists to make the system's autonomous execution **visible, inspectable, auditable, and safe**.

A user should be able to understand:

1. what data entered the system;
2. whether it passed validation;
3. what surveillance signal was detected;
4. why it was detected;
5. what Ngabo is investigating;
6. which deterministic tools have run;
7. which evidence has been retrieved;
8. what remains uncertain or missing;
9. whether human input is required;
10. what incident package Ngabo prepared;
11. whether a human approved it;
12. whether an alert was sent and acknowledged.

The UI must **never hide the distinction** between observed data, deterministic calculations, model-generated hypotheses, guidance, and human decisions.

---

## 2. Information Architecture

Recommended application routes:

```text
/
├── dashboard
│   └── surveillance overview
│
├── imports
│   ├── new
│   └── [importId]
│
├── incidents
│   ├── index
│   └── [incidentId]
│
├── evidence
│   └── [sourceId]
│
└── about
    └── prototype / synthetic-data / safety disclosure
```

Suggested Next.js App Router structure:

```text
apps/web/app/
├── page.tsx
├── imports/
│   ├── new/page.tsx
│   └── [importId]/page.tsx
├── incidents/
│   ├── page.tsx
│   └── [incidentId]/page.tsx
├── evidence/
│   └── [sourceId]/page.tsx
└── about/page.tsx
```

---

## 3. Global Application Shell

### Header

Contains:

- Ngabo wordmark/name;
- prototype badge;
- navigation: Dashboard, Imports, Incidents;
- compact environment indicator: `Synthetic Demo`;
- optional link to GitHub.

### Persistent synthetic-data banner

Public prototype must visibly state:

> **Synthetic demonstration data only — not for clinical decision-making.**

This should be visible on all operational screens, not buried in a footer.

### Global status behavior

Use semantic status labels consistently:

- `NORMAL`
- `SIGNAL DETECTED`
- `INVESTIGATING`
- `WAITING FOR CLARIFICATION`
- `WAITING FOR REVIEW`
- `APPROVED`
- `REJECTED`
- `NOTIFICATION PENDING`
- `NOTIFIED`
- `ACKNOWLEDGED`
- `CLOSED`
- `FAILED`

Do not invent alternative labels per screen.

---

## 4. Dashboard

### Purpose

Give a microbiologist / AMR surveillance officer a fast operational picture of what Ngabo has processed and what requires attention.

### Required sections

#### A. Summary metrics

- isolates processed;
- imports analyzed;
- suspicious signals detected;
- incidents awaiting review;
- open incidents.

These metrics must come from backend state. Do not hardcode demo numbers into components.

#### B. Recent surveillance activity

A compact timeline/list of recent:

- imports;
- signals;
- investigation starts;
- review events;
- notifications.

#### C. Active incidents

Table/cards with:

- incident ID;
- organism;
- ward/location;
- date window;
- priority;
- current state;
- last activity;
- action CTA.

#### D. Data-health / validation summary

Show latest import quality:

- valid rows;
- invalid rows;
- missing metadata;
- duplicate rows.

### Empty state

> “No AMR data has been imported yet. Upload a representative WHONET-style CSV to begin.”

CTA: **Import data**

---

## 5. Import Screen

### Route

`/imports/new`

### Purpose

Upload a representative WHONET-style dataset and clearly communicate the deterministic ingestion process.

### Required components

- drag-and-drop/file picker;
- supported format copy;
- synthetic-data notice;
- upload progress;
- import ID after acceptance.

### Upload lifecycle

```text
SELECTED
  ↓
UPLOADING
  ↓
RECEIVED
  ↓
VALIDATING
  ↓
NORMALIZING
  ↓
ANALYZING
  ↓
COMPLETE / FAILED
```

### After import

Show:

- raw filename;
- SHA-256 short fingerprint;
- rows received;
- rows valid;
- rows rejected/flagged;
- duplicates;
- unknown mappings;
- link to validation report.

The UI must not imply that Gemini parsed or repaired the CSV.

Use wording such as:

> “Validated deterministically by Ngabo's ingestion pipeline.”

---

## 6. Import Detail / Validation Report

### Route

`/imports/[importId]`

### Required sections

- import metadata;
- processing status;
- validation summary;
- validation errors table;
- normalized-record preview;
- surveillance-analysis outcome.

### Error table columns

- row;
- field;
- value;
- error code;
- explanation.

### Surveillance outcome

If no signal:

> “No configured surveillance signal was triggered in this batch.”

If signal:

> “1 investigation candidate detected.”

CTA: **View incident**

Avoid the phrase “outbreak detected.”

---

## 7. Incident Queue

### Route

`/incidents`

### Filters

- state;
- priority;
- organism;
- ward/location;
- date range.

### Table columns

- incident;
- priority;
- organism;
- ward;
- signal window;
- isolate count;
- state;
- last update.

### Priority representation

Priority is workflow triage, **not clinical severity or outbreak probability**.

Include tooltip/help text explaining this.

---

## 8. Incident Detail — Primary Demo Screen

### Route

`/incidents/[incidentId]`

This is the most important screen in the project and should carry the hackathon demo.

Recommended layout:

```text
┌───────────────────────────────────────────────────────┐
│ Incident Header                                       │
│ organism · ward · date window · priority · state      │
└───────────────────────────────────────────────────────┘

┌───────────────────────┐ ┌─────────────────────────────┐
│ Why It Was Flagged    │ │ Investigation Timeline      │
│ deterministic signal  │ │ live agent/tool progression │
└───────────────────────┘ └─────────────────────────────┘

┌───────────────────────────────────────────────────────┐
│ Resistance Profile Comparison                        │
└───────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────┐
│ Clarification / Human Input (conditional)             │
└───────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────┐
│ Incident Response Package                             │
│ evidence · findings · hypotheses · uncertainty        │
└───────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────┐
│ Human Review                                          │
└───────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────┐
│ Response Tracking                                     │
└───────────────────────────────────────────────────────┘
```

On narrower displays, stack sections vertically.

---

## 9. Incident Header

Display:

- incident ID;
- organism;
- ward/location;
- date window;
- isolate count;
- current state badge;
- priority;
- last update.

Secondary metadata:

- source import;
- detector configuration version;
- incident package version;
- correlation ID (developer/details drawer only).

Do not display “AI confidence” unless there is a mathematically defined metric. Prototype signal score must be labelled **signal score**, not confidence.

---

## 10. “Why It Was Flagged” Card

This card is entirely deterministic.

Example:

```text
WHY THIS SIGNAL WAS FLAGGED

4 K. pneumoniae isolates
Neonatal Unit
6-day window

Resistance-profile similarity     0.94
Temporal concentration            High
Representative baseline excess    2.8×

Prototype signal score            0.87
```

Include:

> “This is an investigation-priority signal, not a confirmed outbreak.”

The reasons must come directly from the persisted surveillance signal object.

---

## 11. Resistance Profile Comparison

Purpose: make the underlying AMR pattern understandable.

Recommended UI:

- isolates as rows;
- tested antibiotics as columns;
- S / I / R values as compact badges/cells;
- missing/unknown distinctly marked;
- optional similarity summary.

Required behaviors:

- horizontal scroll for many antibiotics;
- legend explaining S/I/R;
- hover/detail for raw value if available;
- no model-generated values.

The UI must render canonical backend data only.

---

## 12. Agent Investigation Timeline

This is the primary way judges see autonomy.

Do **not** expose private chain-of-thought.

Expose **workflow actions and tool outcomes**.

Example:

```text
14:03:11  DATA NORMALIZED
247 isolates processed

14:03:12  SIGNAL DETECTED
Possible K. pneumoniae cluster requires investigation

14:03:13  NGABO INVESTIGATING
Gathering incident context

14:03:14  TOOL COMPLETED
Resistance profile comparison · mean similarity 0.94

14:03:15  TOOL COMPLETED
Representative baseline retrieved

14:03:16  EVIDENCE RETRIEVED
2 approved IPC/AMR sources

14:03:17  CLARIFICATION REQUIRED
Specimen type missing for UGA-039

14:04:02  CLARIFICATION RECEIVED
Blood

14:04:03  INVESTIGATION RESUMED

14:04:05  INCIDENT PACKAGE READY
Awaiting professional review
```

### Event categories

- SYSTEM
- DETECTOR
- AGENT
- TOOL
- EVIDENCE
- HUMAN
- ACTION
- ERROR

### Timeline must show

- timestamp;
- event title;
- concise description;
- optional expandable structured details.

Never render hidden model reasoning tokens.

---

## 13. Clarification Card

Visible only while clarification is required or after it has been answered.

Example:

> **Ngabo needs clarification**  
> Specimen type is missing for isolate UGA-039. Please confirm the specimen source before Ngabo finalizes this assessment.

Controls:

- constrained select when options are known;
- short text only when genuinely necessary;
- Submit answer.

After submission:

- disable editing by default;
- show answer;
- show responder and timestamp if available;
- show `Investigation resumed` state.

The clarification UI is the only intentionally conversational part of v0.1.

---

## 14. Incident Response Package

Separate information into explicit categories.

### A. Observed evidence

Facts from source data.

### B. Derived findings

Deterministic calculations/tool outputs.

### C. Hypotheses

Agent-generated interpretations, visually labelled **Hypothesis**.

### D. Uncertainties

What Ngabo cannot determine.

### E. Missing information

Outstanding data gaps.

### F. Guidance

Approved evidence with:

- source title;
- publisher;
- source ID;
- hyperlink;
- short relevant summary.

### G. Investigation checklist

Actionable investigation steps for professional consideration.

### H. Draft escalation

Clearly labelled draft.

Never visually merge hypotheses with observed facts.

---

## 15. Evidence Source Interaction

Clicking a guidance source opens either:

- an in-app evidence-detail route; or
- the authoritative external URL in a new tab.

Evidence details include:

- source title;
- publisher;
- publication/update date;
- canonical URL;
- retrieved/approved excerpt;
- tags;
- source ID.

No arbitrary web-search result should appear as approved evidence in v0.1.

---

## 16. Human Review Panel

Visible at `WAITING_FOR_REVIEW` and afterwards.

### Reviewer sees

- package version;
- evidence;
- uncertainty;
- limitations;
- proposed notification recipients/action.

### Actions

#### Approve

Requires confirmation modal:

> “Approve this incident package for the configured notification workflow?”

#### Reject

Requires short reason.

#### Request more information

Requires a reason/question and returns workflow to `NEEDS_MORE_INFO` / investigation.

### Important

Do not label approval as:

> “Confirm outbreak.”

Use:

> “Approve incident package / escalation.”

---

## 17. Response Tracking

After approval, show:

```text
ALERT ROUTING

Recipient             IPC Lead
Status                Sent
Sent at                14:05:17
Delivery attempt       1
Acknowledgement        Received 14:07:02
Follow-up              Scheduled
```

The demo notification adapter must be visually distinguishable from a real integration if a demo adapter is being used.

Example label:

> `Demo notification channel`

Do not imply a real hospital was contacted.

---

## 18. Loading States

Do not use generic full-screen spinners for long-running agent workflows.

Prefer progressive visible states:

```text
✓ Data validated
✓ Signal detected
● Investigating context
○ Retrieving evidence
○ Preparing package
```

The user should know the workflow is alive.

---

## 19. Error States

### Import failure

Show exact validation issue and remediation.

### Agent/tool failure

Example:

> “Investigation paused because the evidence retrieval tool failed. No incident package was generated.”

Actions:

- Retry when safe;
- view details;
- never show a fake completed package.

### Notification failure

Show:

- failed status;
- retry state;
- last error category;
- no duplicate-send ambiguity.

---

## 20. Empty States

Every main screen should have an intentional empty state.

Examples:

### No incidents

> “No investigation candidates are currently open.”

### No guidance retrieved

> “No approved guidance source matched this investigation. Ngabo will not fabricate a recommendation.”

### No missing information

> “No material clarification is currently required.”

---

## 21. Accessibility

Minimum frontend expectations:

- keyboard-accessible controls;
- semantic headings;
- form labels;
- focus visibility;
- no status communicated by color alone;
- table alternatives/accessible labels;
- sufficient contrast;
- responsive layouts;
- `aria-live` or equivalent for meaningful live workflow-status updates where appropriate.

---

## 22. Responsive Behavior

### Desktop

Primary target for hackathon demo.

Use multi-column incident view where helpful.

### Tablet

Cards may collapse to a single primary column plus secondary sections.

### Mobile

Must remain usable, but do not compromise desktop incident-response density to make it mobile-first.

---

## 23. Design Language

Aim for:

- professional;
- clinical-operational;
- calm;
- evidence-first;
- high information density without clutter;
- clear state transitions.

Avoid:

- neon “AI” aesthetics;
- glowing chat bubbles;
- robot mascots dominating operational screens;
- unnecessary gradients/animations;
- fake medical-device visual language;
- dark patterns that make model output look authoritative.

Use semantic design tokens rather than hard-coded component colors wherever possible.

---

## 24. Suggested Component Hierarchy

```text
<AppShell>
  <SyntheticDataBanner />
  <Navigation />

<DashboardPage>
  <SummaryMetrics />
  <RecentActivity />
  <ActiveIncidentsTable />
  <DataHealthCard />

<ImportPage>
  <FileUploader />
  <ImportProgress />
  <ValidationSummary />

<IncidentPage>
  <IncidentHeader />
  <SignalExplanationCard />
  <InvestigationTimeline />
  <ResistanceProfileTable />
  <ClarificationCard />
  <IncidentPackage />
    <ObservedEvidence />
    <DerivedFindings />
    <Hypotheses />
    <Uncertainty />
    <GuidanceSources />
    <InvestigationChecklist />
    <DraftEscalation />
  <HumanReviewPanel />
  <ResponseTracking />
```

---

## 25. Frontend Data Contract Principle

The frontend must not derive medical/scientific meaning from strings.

Backend APIs should return explicit typed fields.

Bad:

```json
{"message": "High confidence outbreak in NICU"}
```

Preferred:

```json
{
  "state": "INVESTIGATING",
  "signal": {
    "label": "INVESTIGATION_CANDIDATE",
    "score": 0.87,
    "score_type": "PROTOTYPE_SIGNAL_SCORE",
    "reasons": []
  }
}
```

The UI renders meaning already encoded by domain contracts.

---

## 26. Live Update Contract

Preferred implementation:

- Server-Sent Events for incident progress;
- polling fallback if SSE threatens reliability.

Frontend event examples:

- `incident.state_changed`
- `investigation.tool_started`
- `investigation.tool_completed`
- `incident.clarification_requested`
- `incident.package_ready`
- `incident.review_recorded`
- `notification.sent`
- `notification.acknowledged`

UI updates must tolerate reconnect/replay without duplicating timeline entries.

---

## 27. Demo Mode

Provide a clearly labelled demo/reset capability.

Recommended:

- `Load seeded scenario`
- `Reset synthetic demo`

The seeded demo is allowed to make the workflow reproducible but **must run the real application path**. It must not simply swap in pre-rendered final-state JSON.

A judge should see real:

- import;
- persistence;
- detector execution;
- Pub/Sub/event flow;
- agent/tool calls;
- state transitions;
- human review;
- notification action.

---

## 28. UI Acceptance Criteria

The frontend is ready for demo when:

- [ ] a new user understands Ngabo without opening a chat box;
- [ ] synthetic-data status is always visible;
- [ ] import validation is visible;
- [ ] signal explanation is visibly deterministic;
- [ ] agent actions/tool outcomes stream into the timeline;
- [ ] hidden chain-of-thought is never exposed;
- [ ] clarification pauses/resumes the workflow visibly;
- [ ] facts, derived findings, hypotheses, uncertainty, and guidance are visually separated;
- [ ] evidence links work;
- [ ] review controls enforce the human gate;
- [ ] notification status and acknowledgement are visible;
- [ ] failure states never masquerade as success;
- [ ] the full seeded scenario is understandable in an unedited <4-minute demo.

---

## 29. Implementation Rule for Claude Code

If an implementation choice conflicts with this document, the PRD, or the safety/agent contracts:

1. do not silently change product behavior;
2. stop and document the conflict;
3. propose an ADR;
4. preserve the architectural invariant that Ngabo is an **incident-response console with bounded agentic autonomy**, not a generic AI chat application.
