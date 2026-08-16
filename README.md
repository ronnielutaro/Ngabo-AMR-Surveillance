# Ngabo

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
Gemini evidence-grounded synthesis
        ↓
deterministic package validation
   └─ bounded automatic repair if needed
        ↓
deterministic autonomy policy
        ↓
freshness + idempotency
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

## Safe Zero-Human Autonomy

Ngabo does not achieve autonomy by allowing unrestricted clinical decisions.

It uses deterministic action classes:

```text
A0 INTERNAL_STATE
→ autonomous

A1 SAFE_EXTERNAL_COORDINATION
→ autonomous after validation/policy/freshness/idempotency gates

A2 REAL_OPERATIONAL_ESCALATION
→ outside autonomous public-v0.1 envelope unless separately authorized

A3 CLINICAL_OR_OFFICIAL_PUBLIC_HEALTH_DECISION
→ never autonomous in v0.1
```

The hackathon hero action is A1: a real authorized test/sandbox/internal coordination action clearly labelled as an **investigation candidate**, not a diagnosis, treatment recommendation or confirmed outbreak.

If data/evidence/policy is insufficient, Ngabo autonomously abstains rather than fabricating completion.

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

Core investigation:

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
Gemini synthesis
      ↓
deterministic validation
```

Fixed routing, scientific calculations, action authorization, freshness and idempotency do not belong to Gemini.

See [`docs/ORCHESTRATION_PATTERNS.md`](./docs/ORCHESTRATION_PATTERNS.md).

## Automatic Validation & Repair

Model-generated incident packages must pass deterministic validation.

If a package is invalid:

```text
validator errors
→ bounded Gemini repair
→ validator
```

The model cannot waive validator failures. Exhausted repair budget produces a safe stop.

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
- action-class safety tests;
- automatic package repair;
- prompt injection/source integrity;
- freshness/idempotency;
- restart/recovery;
- BYOF operational utility benchmark;
- real external A1 action + machine acknowledgement;
- optional EmbeddingGemma/MedGemma only if implemented.

The canonical deployed hero must pass at least three consecutive times before demo freeze.

## Judge-Facing Diagram

The current target judge-facing visual is in [`docs/ARCHITECTURE_DIAGRAM.md`](./docs/ARCHITECTURE_DIAGRAM.md).

It must be reconciled to the actual deployed `v0.1.0` release before submission.

## Hackathon Risk / Evidence Controls

- [`docs/HACKATHON_ALIGNMENT.md`](./docs/HACKATHON_ALIGNMENT.md) — competition contract
- [`docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md`](./docs/TASKMASTER_ZERO_HUMAN_AUTONOMY.md) — safe literal zero-human hero
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

## Current Repository State

The repository is currently design-first. Application code, deployment proof, evaluation results and hosted URLs must be produced during implementation; design documents are not treated as execution proof.

## License

See [`LICENSE`](./LICENSE).
