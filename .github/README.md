# Ngabo

[![Delivery Develop](https://github.com/ronnielutaro/Ngabo-AMR-Surveillance/actions/workflows/delivery-develop.yml/badge.svg)](https://github.com/ronnielutaro/Ngabo-AMR-Surveillance/actions/workflows/delivery-develop.yml)

**Autonomous AMR Surveillance & Incident Response**

Ngabo is an **open-source, event-driven antimicrobial resistance surveillance and incident-response system** that transforms AMR surveillance signals into structured, evidence-backed investigations and coordinated response workflows.

> **Current release status:** `v0.1.0` hackathon MVP in development.  
> **Data:** Synthetic demonstration data only in the public v0.1 release.  
> **Safety:** Ngabo is not a clinical diagnostic or prescribing system and does not autonomously confirm outbreaks.

## Hackathon Target

Ngabo is being built for the **All Things Agentic Hackathon 2026** in **The Taskmaster** category.

The canonical hero workflow is designed to complete **with zero human intervention after the surveillance event**:

```text
synthetic AMR data
        ↓
deterministic validation + normalization
        ↓
deterministic surveillance signal
        ↓
Pub/Sub event
        ↓
Google ADK workflow starts automatically
        ↓
parallel deterministic investigation + join
        ↓
Gemini 3.6 Flash bounded triage
        ↓
approved evidence retrieval
        ↓
Gemini proof-carrying synthesis
        ↓
deterministic claim/evidence verification
   ├─ invalid → bounded automatic repair → verify again
   └─ repair exhausted → autonomous abstention
        ↓
deterministic A1 autonomy policy
        ↓
freshness + ActionIntent/idempotency
        ↓
real authorized safe external action
        ↓
machine acknowledgement
```

Hero targets:

```text
manual prompts       0
human interventions  0
human active steps   0
clarifications       0
approval clicks      0
```

## The Twist — Proof-Carrying Autonomy

Ngabo's competition twist is **Proof-Carrying Autonomy**:

> **Ngabo completes the AMR investigation-to-coordination workflow without human intervention, but it does not trust its own LLM. Every action-relevant model claim must carry machine-checkable references to canonical data, deterministic findings, and/or approved evidence before it can influence autonomous action.**

The governing implementation rule is:

> **LLM proposes; deterministic machinery verifies whatever can be verified before the claim may influence autonomous action.**

Material model claims are typed, including:

- `OBSERVED_FACT` — must reference canonical records;
- `DERIVED_FINDING` — must reference deterministic result IDs;
- `EVIDENCE_STATEMENT` — must reference retrieved approved evidence;
- `HYPOTHESIS` — must stay labelled as a hypothesis and preserve uncertainty;
- `ACTION_JUSTIFICATION` — may explain an A1 candidate but cannot authorize it.

Unknown records/findings/sources, unsupported factual assertions, claim-type escalation, and prohibited diagnosis/prescribing/outbreak-confirmation claims fail deterministic verification. Private chain-of-thought is not treated as evidence, persisted as truth, or displayed.

See [`docs/PROOF_CARRYING_REASONING.md`](./docs/PROOF_CARRYING_REASONING.md) and ADR 0009.

## Safe Zero-Human Autonomy

Ngabo does not achieve autonomy by allowing unrestricted clinical decisions.

It uses deterministic action classes:

```text
A0 INTERNAL_STATE
→ autonomous

A1 SAFE_EXTERNAL_COORDINATION
→ autonomous after claim verification + policy + freshness + idempotency gates

A2 REAL_OPERATIONAL_ESCALATION
→ outside autonomous public-v0.1 envelope unless separately authorized

A3 CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION
→ never autonomous in v0.1
```

The hackathon hero action is A1: a real authorized test/sandbox/internal coordination action clearly labelled as an **investigation candidate**, not a diagnosis, treatment recommendation or confirmed outbreak.

If data, evidence, proof verification, or policy is insufficient, Ngabo autonomously abstains rather than fabricating completion.

See [`docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`](./docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md).

## Bring Your Own Friction

Ngabo's Taskmaster story is grounded in a personal repeated workflow encountered while researching/building AMR intelligence:

```text
inspect signal/data
→ compare isolates/resistance patterns
→ inspect context/baseline
→ find trusted evidence
→ separate facts from hypotheses
→ assemble a defensible incident package
→ validate sources/claims
→ route the result
→ track completion
```

Ngabo is the agent built to automate that fragmented workflow in the background.

See [`docs/BYOF_FRICTION.md`](./docs/BYOF_FRICTION.md) and [`docs/OPERATIONAL_UTILITY_EVALUATION.md`](./docs/OPERATIONAL_UTILITY_EVALUATION.md).

## Product Strategy and Market Position

Ngabo enters an active AMR technology landscape. WHONET, AMASS, laboratory information systems, national platforms and commercial surveillance products already support data management, analysis, reporting, alerts and parts of infection-management workflows. Ngabo does not position itself as their replacement.

Its intended wedge begins after a usable signal exists:

> **Turn a suspicious AMR signal into a proof-verified investigation package and one authorized, acknowledged safe-coordination action.**

The current product-strategy documents are:

- [`docs/LEAN_CANVAS.md`](./docs/LEAN_CANVAS.md) — problem, customer, solution, channels, sustainability, costs, metrics, advantage and validation assumptions;
- [`docs/COMPETITOR_ANALYSIS.md`](./docs/COMPETITOR_ANALYSIS.md) — public and commercial alternatives, Uganda-specific context, qualitative practitioner pain signals, capability matrices and competitive claim guardrails;
- [`docs/VALUE_PROPOSITION_CANVAS.md`](./docs/VALUE_PROPOSITION_CANVAS.md) — separate value propositions for the primary surveillance practitioner, institutional adopter/governor and upstream platform or implementation partner.

These documents distinguish research-supported problems from unvalidated product, customer, adoption and partnership hypotheses. They do not establish clinical validation, product-market fit, institutional adoption or market superiority.

## Architecture

Ngabo uses **Clean Architecture inside a monorepo**.

```text
Frameworks / Infrastructure
          ↓
Interfaces / Adapters
          ↓
Application / Use Cases / Ports
          ↓
Domain / Entities / Value Objects / Domain Services
```

Repository target:

```text
ngabo/
├── apps/web/          # Next.js incident/autonomy console
├── services/core/     # FastAPI + deterministic core + ADK infrastructure
├── data/              # synthetic fixtures, schemas, approved guidance
├── docs/
├── infra/
└── .github/
```

`ngabo-web` and `ngabo-core` remain independently deployable Cloud Run services.

## Graph-First Orchestration

Governing rule:

> **Deterministic when the workflow is known; agentic when the decision is ambiguous; dynamic only when the workflow itself cannot reasonably be known in advance.**

Core investigation/action path:

```text
incident context
      ↓
parallel deterministic fan-out
  ├── resistance-profile comparison
  ├── baseline summary
  └── missing-field assessment
      ↓
join
      ↓
Gemini triage
      ↓
approved evidence
      ↓
Gemini proof-carrying synthesis
      ↓
deterministic claim/evidence verifier
      ↓
bounded repair or abstention
      ↓
deterministic A1 policy
      ↓
freshness + ActionIntent/idempotency
      ↓
external action + machine acknowledgement
```

Fixed routing, scientific calculations, proof validation, action authorization, freshness and idempotency do not belong to Gemini.

See [`docs/ORCHESTRATION_PATTERNS.md`](./docs/ORCHESTRATION_PATTERNS.md).

## Proof-Carrying Validation & Repair

Model-generated packages must pass deterministic proof verification. A fluent statement is not trusted simply because it sounds plausible.

If verification fails:

```text
structured verification errors
→ bounded Gemini repair using existing facts/findings/evidence
→ deterministic verifier
```

The model cannot waive verifier failures or mutate canonical truth. Exhausted repair budget produces a safe abstention.

## Long-Running Truth

```text
Firestore/application state = canonical incident/workflow truth
ADK session/checkpoint      = execution continuity
Cloud Storage               = files/large artifacts
model memory                = not authoritative AMR truth
```

Before an A1 external action, Ngabo revalidates freshness against current canonical state.

See [`docs/LONG_RUNNING_AGENT.md`](./docs/LONG_RUNNING_AGENT.md).

## Planned Stack

- **Frontend:** Next.js, TypeScript, Tailwind CSS, shadcn/ui
- **Backend:** Python, FastAPI, Pydantic v2
- **Agent runtime:** Google ADK Python
- **Primary model:** Gemini 3.6 Flash via Gemini API
- **Planned retrieval model:** EmbeddingGemma after core is green
- **Gated stretch model:** MedGemma only if evaluation proves value
- **State:** Firestore
- **Files/artifacts:** Cloud Storage
- **Events:** Pub/Sub
- **Compute:** Cloud Run
- **Observability:** Cloud Logging + supported Trace/OpenTelemetry integration
- **Testing:** pytest, ADK evaluations, Playwright

## ADK API Discipline

Before production runtime implementation, Ngabo requires a pinned-version capability spike to verify the exact supported ADK orchestration, session, evaluation and observability APIs.

See [`docs/ADK_CAPABILITY_SPIKE.md`](./docs/ADK_CAPABILITY_SPIKE.md).

## Evaluation

Before submission Ngabo will publish `EVALUATION.md` containing real results for:

- deterministic surveillance/scientific tests;
- graph/fan-out/join tests;
- zero-human hero E2E;
- proof-carrying claim/reference verification;
- fabricated record/finding/source adversarial tests;
- hypothesis→fact and forbidden-claim escalation tests;
- `unsafe_claim_escape_rate` on the committed software adversarial suite;
- action-class safety tests;
- bounded automatic repair;
- prompt injection/source integrity;
- freshness/idempotency;
- restart/recovery;
- BYOF operational utility benchmark;
- real external A1 action + machine acknowledgement;
- optional EmbeddingGemma/MedGemma only if implemented.

`unsafe_claim_escape_rate == 0` is a **software-suite target**, not a clinical-safety or universal hallucination-elimination claim.

The canonical deployed hero must pass at least three consecutive times before demo freeze.

## Judge-Facing Diagram

The current target judge-facing visual is in [`docs/ARCHITECTURE_DIAGRAM.md`](./docs/ARCHITECTURE_DIAGRAM.md).

It must be reconciled to the actual deployed `v0.1.0` release before submission.

## Hackathon Risk / Evidence Controls

- [`docs/HACKATHON_ALIGNMENT.md`](./docs/HACKATHON_ALIGNMENT.md) — competition contract
- [`docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`](./docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md) — safe literal zero-human hero
- [`docs/PROOF_CARRYING_REASONING.md`](./docs/PROOF_CARRYING_REASONING.md) — proof-carrying autonomy / hallucination boundary
- [`docs/BYOF_FRICTION.md`](./docs/BYOF_FRICTION.md) — personal-friction story
- [`docs/HACKATHON_RISK_REGISTER.md`](./docs/HACKATHON_RISK_REGISTER.md) — competition risk controls
- [`docs/SUBMISSION_EVIDENCE.md`](./docs/SUBMISSION_EVIDENCE.md) — claim-to-proof matrix
- [`docs/SUBMISSION_FREEZE.md`](./docs/SUBMISSION_FREEZE.md) — immutable judged release
- [`docs/THIRD_PARTY_PROVENANCE.md`](./docs/THIRD_PARTY_PROVENANCE.md) — licensing/data/pre-existing-work controls

## Bonus Strategy

Only after the core is stable:

- public LinkedIn build article with required hackathon-purpose statement;
- social post using exact `#AllThingsAgenticHackathon`;
- EmbeddingGemma if successfully integrated/evaluated;
- MedGemma only if it materially improves evaluation;
- multimodal AST/PDF extraction only as a human-verified draft and only after core freeze.

No bonus feature will be claimed if it exists only in documentation.

## Release Governance

Ngabo uses:

- Semantic Versioning;
- Conventional Commits;
- Gitflow-style `main` + `develop`;
- release tags `vX.Y.Z`;
- `CHANGELOG.md`.

Hackathon submission uses an immutable judged release policy described in [`docs/SUBMISSION_FREEZE.md`](./docs/SUBMISSION_FREEZE.md).

## Development

**Prerequisites:** Node.js 20+ with pnpm (version pinned in `package.json`) and Python 3.11 with [uv](https://docs.astral.sh/uv/).

Install:

```bash
pnpm install                    # frontend workspace (apps/web)
cd services/core && uv sync     # Python core
```

Frontend (`ngabo-web`):

```bash
pnpm dev            # Next.js dev server
pnpm web:build      # production build
pnpm web:lint       # ESLint
pnpm web:typecheck  # tsc --noEmit
pnpm web:test       # Vitest
```

Core (`ngabo-core`):

```bash
pnpm core:lint       # ruff
pnpm core:typecheck  # mypy (strict)
pnpm core:test       # pytest
pnpm core:health     # bootstrap health check (ngabo-health)
```

Everything:

```bash
pnpm lint && pnpm typecheck && pnpm test && pnpm build
```

The M1A scaffold establishes the monorepo and Clean Architecture boundaries only. No Ngabo product behavior is implemented yet; the commands above verify the tooling and layer-boundary discipline (including an architecture smoke test that forbids framework/vendor imports in the inner layers).

## Current Repository State

The repository is design-first with an M1A executable scaffold: the monorepo layout, Python Clean Architecture layer boundaries, and frontend tooling are in place and verified. Application/product code, deployment proof, evaluation results and hosted URLs must still be produced during implementation; design documents are not treated as execution proof.

## License

See [`LICENSE`](./LICENSE).
