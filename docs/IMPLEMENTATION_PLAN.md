# Ngabo — Implementation Plan

**Version:** 0.2  
**Created:** 2026-08-16  
**Official hackathon deadline:** 2026-08-31, 5:00 PM Pacific Time

## 1. Principle

> **Do not spend the final 48 hours implementing core architecture.**

Feature-complete several days early; reserve the end for evaluation, deployment proof, UI polish, article, demo, and submission.

## 2. Critical Path

```text
repo scaffold
   ↓
synthetic data + schema
   ↓
parser / normalizer
   ↓
surveillance detector
   ↓
incident state machine
   ↓
agent tools
   ↓
agent investigation
   ↓
clarification
   ↓
incident package
   ↓
human approval
   ↓
notification + acknowledgement
   ↓
UI
   ↓
Cloud deployment
   ↓
evaluation
   ↓
demo + article + Devpost
```

## Aug 16 — Freeze Design & Handoff Contract

- [x] Lean Canvas
- [x] Devpost pitch
- [x] LinkedIn article strategy
- [x] PRD
- [x] Tech stack
- [x] System design
- [x] Agent design
- [x] Data/safety/evaluation design
- [x] UI/UX implementation specification
- [x] Implementation plan
- [x] GitHub repository exists
- [x] Add `CLAUDE.md` implementation contract
- [x] Add `AGENTS.md` coding-agent rules
- [x] Add README skeleton/document map
- [x] Add LICENSE
- [x] Add SECURITY.md
- [x] Add baseline architecture ADR
- [x] Copy implementation design docs into repository

**Exit:** Claude Code can begin Milestone 1 without guessing the product, UI, safety model, agent boundary, or stack.

## Aug 17 — Scaffold + Domain Core

- [ ] monorepo structure
- [ ] `apps/web`
- [ ] `services/core`
- [ ] uv + pnpm
- [ ] lint/type/test scripts
- [ ] `.env.example`
- [ ] domain entities
- [ ] incident state machine
- [ ] state-transition tests

Optional implementation aid:

- [ ] run `uvx google-agents-cli setup` if useful in the Claude Code environment; preserve Ngabo's frozen architecture rather than letting a generated scaffold redefine it.

**Exit:** domain layer runs locally with tests green.

## Aug 18 — Synthetic Data + Ingestion

- [ ] supported input columns
- [ ] baseline dataset
- [ ] seeded suspicious cluster
- [ ] malformed/noisy dataset
- [ ] parser
- [ ] normalizer
- [ ] validation report
- [ ] duplicate handling
- [ ] import API
- [ ] file hashing

**Exit:** CSV → canonical isolates + validation report.

## Aug 19 — Surveillance Engine

- [ ] resistance representation
- [ ] similarity method
- [ ] temporal concentration
- [ ] ward concentration
- [ ] baseline comparison
- [ ] signal score
- [ ] trigger explanation
- [ ] scenario tests

**Exit:** seeded signal detected deterministically.

## Aug 20–21 — ADK + Agent Tools

- [ ] scaffold Google ADK inside established backend structure
- [ ] Gemini 3.6 Flash
- [ ] local ADK playground/eval workflow
- [ ] incident context tool
- [ ] profile comparison tool
- [ ] baseline tool
- [ ] missing-fields tool
- [ ] approved-guidance tool
- [ ] clarification tool
- [ ] package schema
- [ ] tool logging
- [ ] max steps/timeouts
- [ ] citation validation
- [ ] prohibited-claim validation

**Exit:** pre-created signal → valid evidence-backed incident package locally.

## Aug 22 — Persistent Event Workflow

- [ ] Firestore adapter
- [ ] incident persistence
- [ ] event timeline
- [ ] Pub/Sub contracts
- [ ] import event handler
- [ ] signal event handler
- [ ] incident event handler
- [ ] processed-event idempotency
- [ ] resume state

**Exit:** restart/retry cannot duplicate incident or side effect.

## Aug 23 — Human Gate + Action

- [ ] clarification endpoint
- [ ] pause/resume
- [ ] approve
- [ ] reject
- [ ] request more info
- [ ] notification port
- [ ] demo notification adapter
- [ ] real email/webhook if stable
- [ ] acknowledgement

**Exit:** backend end-to-end workflow complete.

## Aug 24–25 — Incident Console

Implement against `docs/UI_UX_SPEC.md`.

- [ ] app shell + synthetic-data banner
- [ ] dashboard
- [ ] import UI
- [ ] validation report
- [ ] incident queue
- [ ] incident header
- [ ] deterministic “why flagged” card
- [ ] resistance-profile comparison
- [ ] live agent/tool investigation timeline
- [ ] clarification card
- [ ] evidence-backed package
- [ ] source links/details
- [ ] human review panel
- [ ] response tracking
- [ ] loading/error/empty states
- [ ] demo reset/seeded scenario controls
- [ ] accessibility pass

**Exit:** a non-developer can understand the autonomous flow from the UI alone; it does not look like a generic chatbot.

## Aug 26 — GCP Deployment

- [ ] billing alert
- [ ] Cloud Storage
- [ ] Firestore
- [ ] Pub/Sub
- [ ] `ngabo-core` Cloud Run
- [ ] `ngabo-web` Cloud Run
- [ ] secret handling
- [ ] Cloud Logging
- [ ] observability
- [ ] deployed URLs
- [ ] capture Cloud Run proof

**Exit:** full scenario works on Google Cloud.

## Aug 27 — Evaluation

- [ ] deterministic unit suite
- [ ] scenario benchmark
- [ ] ADK evals
- [ ] prompt injection test
- [ ] fabricated-source test
- [ ] hallucinated-isolate test
- [ ] prohibited clinical-claim tests
- [ ] duplicate-event test
- [ ] notification retry test
- [ ] end-to-end integration test
- [ ] `EVALUATION.md`
- [ ] metrics captured

**Exit:** demo is reproducible and limitations documented.

## Aug 28 — Technical Story

- [ ] final architecture diagram
- [ ] product screenshots
- [ ] LinkedIn Article draft
- [ ] explicitly state article was created for purposes of entering the hackathon
- [ ] domain/technical critique if feasible
- [ ] README spin-up instructions polished

## Aug 29–30 — Demo + Devpost

### Demo

- [ ] under 4 minutes
- [ ] problem in first ~30 seconds
- [ ] unedited live workflow
- [ ] visible Google Cloud execution
- [ ] architecture explanation
- [ ] safety boundary
- [ ] public YouTube/Vimeo video

### Devpost

- [ ] summary/features
- [ ] technology/data sources
- [ ] findings/learnings
- [ ] GitHub URL
- [ ] hosted URL
- [ ] architecture diagram
- [ ] reproducible spin-up instructions
- [ ] LinkedIn Article URL
- [ ] social post with `#AllThingsAgenticHackathon`
- [ ] final claims audit

**Internal target:** submission-ready by end of Aug 30.

## Aug 31 — Buffer + Submit

Only:
- critical fixes;
- link verification;
- final test;
- submission.

No major new features.

## 3. Stretch Order

Only after core is green:

1. real email/webhook;
2. parallel ADK investigation;
3. richer baseline visualization;
4. additional Google AI model if genuinely useful;
5. AMRFinderPlus genomics prototype.

> **Genomics is last, not first.**

## 4. Demo Freeze Rule

After three consecutive successful deployed end-to-end runs:

1. tag `demo-candidate`;
2. stop architecture refactors;
3. fix only bugs and presentation problems.

## 5. Current Rule Checklist

- [ ] Gemini 3.5+
- [ ] qualifying Google Agent Framework
- [ ] Google Cloud infrastructure
- [ ] hosted project
- [x] repository
- [ ] final README spin-up instructions
- [ ] architecture diagram
- [ ] <=4 minute public demo
- [ ] visible Google Cloud backend execution
- [ ] one category selected
- [ ] project/code built within submission period as required
- [ ] authorized third-party integrations

Optional:
- [ ] public build content
- [ ] social post with `#AllThingsAgenticHackathon`
- [ ] additional Google AI model only if useful

Rules: https://allthingsagentichackathon.devpost.com/rules

## 6. Winning Loop

```text
build
  ↓
test
  ↓
deploy
  ↓
measure
  ↓
document
  ↓
demo
  ↓
submit
```

Ngabo should win on **working autonomy + architectural discipline + credible health-domain framing + a clean demo**, not feature count.
