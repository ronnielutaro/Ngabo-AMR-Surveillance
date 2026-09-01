# Ngabo

[![Delivery Develop](https://github.com/ronnielutaro/Ngabo-AMR-Surveillance/actions/workflows/delivery-develop.yml/badge.svg)](https://github.com/ronnielutaro/Ngabo-AMR-Surveillance/actions/workflows/delivery-develop.yml)

**Autonomous AMR Surveillance & Incident Response**

Ngabo is an **open-source, event-driven antimicrobial resistance surveillance and incident-response system** that transforms AMR surveillance signals into structured, evidence-backed investigations and coordinated response workflows.

Its product direction is an **always-on AMR surveillance and coordination layer**: **Connect → Watch → Investigate → Coordinate**. It is designed to meet governed laboratory data where it already exists, keep surveillance state current, investigate meaningful signals automatically, and complete only permitted coordination with machine-verifiable proof.

> **Current release status:** deployed synthetic `v0.1.0` hackathon demo; release tag/freeze pending.<br>
> **Data:** Synthetic demonstration data only in the public v0.1 release.<br>
> **Integration:** No production ALIS, WHONET, LIS/LIMS, instrument, or hospital connector is currently claimed.<br>
> **Safety:** Ngabo is not a clinical diagnostic or prescribing system and does not autonomously confirm outbreaks.

## Live Hackathon Demo

- **Public dashboard:** [ngabo-web on Cloud Run](https://ngabo-web-2zhvmdaotq-uc.a.run.app/)
- **Synthetic input:** [`demo/connect/synthetic_gulu_surveillance_export.csv`](./demo/connect/synthetic_gulu_surveillance_export.csv)
- **Deployed architecture:** [`docs/ARCHITECTURE_DIAGRAM.md`](./docs/ARCHITECTURE_DIAGRAM.md)
- **High-resolution diagram:** [`docs/NGABO_DEPLOYED_ARCHITECTURE.png`](./docs/NGABO_DEPLOYED_ARCHITECTURE.png)

The dashboard is public, but `ngabo-core` is intentionally private. The web service reads the core through its Cloud Run service identity; the browser never receives credentials or calls Firestore, Gemini or the private core directly.

The deployed Connect slice starts when the synthetic CSV is uploaded through Ngabo Connect. It then performs deterministic cleaning and signal detection, launches the governed ADK/Gemini investigation, verifies the proof-carrying package, applies the A1 safety gates, sends one signed coordination request and records the machine acknowledgement. Pub/Sub and Cloud Storage remain part of the broader event-driven roadmap but are not presented as exercised components in this direct Connect demo path.

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
authenticated Connect batch / surveillance event
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

The broader product wedge is the recurring surveillance operating loop:

> **Connect governed laboratory data → continuously watch deterministic surveillance state → investigate meaningful signals → complete one permitted coordination step with acknowledgement.**

The public v0.1 release is designed to prove a narrower, complete slice using a committed synthetic WHONET-style source:

> **Synthetic source → deterministic surveillance signal → proof-verified investigation package → one authorized, acknowledged safe-coordination action.**

Production source adapters remain a post-v0.1 product-hardening direction. Existing laboratory and surveillance systems remain the upstream systems of record; Ngabo does not claim to replace them.

The current product-strategy documents are:

- [`docs/LEAN_CANVAS.md`](./docs/LEAN_CANVAS.md) — problem, customer, solution, channels, sustainability, costs, metrics, advantage and validation assumptions;
- [`docs/COMPETITOR_ANALYSIS.md`](./docs/COMPETITOR_ANALYSIS.md) — public and commercial alternatives, Uganda-specific context, qualitative practitioner pain signals, capability matrices and competitive claim guardrails;
- [`docs/VALUE_PROPOSITION_CANVAS.md`](./docs/VALUE_PROPOSITION_CANVAS.md) — separate value propositions for the primary surveillance practitioner, institutional adopter/governor and upstream platform or implementation partner;
- [`docs/USER_PERSONAS.md`](./docs/USER_PERSONAS.md) — prioritized operational personas, workflow pains, adoption roles, anti-personas and validation questions.

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

## Technology Stack

| Capability | Technology | Current v0.1 status |
| --- | --- | --- |
| Web dashboard | Next.js, TypeScript, Tailwind CSS | Implemented and deployed on Cloud Run |
| Core service | Python, FastAPI, Pydantic v2 | Implemented and deployed as a private Cloud Run service |
| Agent runtime | Google ADK Python `2.8.0` | Implemented in the hero investigation path |
| Primary model | Gemini 3.6 Flash via Gemini API | Implemented for bounded triage and proof-carrying synthesis |
| Canonical state | Firestore | Implemented for incidents, isolates, workflow state and ActionIntents |
| Secrets | Secret Manager | Implemented for the Gemini credential |
| External action | Signed Cloud Run demo receiver | Implemented for the synthetic A1 delivery/acknowledgement proof |
| Containers | Artifact Registry + digest-bound Cloud Run deployment | Implemented |
| Observability | Cloud Logging plus application events | Implemented at the deployed runtime level |
| Event/file expansion | Pub/Sub and Cloud Storage | Broader roadmap; omitted from the direct Connect runtime diagram |
| Optional models | EmbeddingGemma / MedGemma | Not implemented in the submitted core path |
| Testing | pytest, Vitest, architecture and container gates | Implemented in CI |

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

The reconciled deployed visual is in [`docs/ARCHITECTURE_DIAGRAM.md`](./docs/ARCHITECTURE_DIAGRAM.md), with an upload-ready [PNG](./docs/NGABO_DEPLOYED_ARCHITECTURE.png) and editable [Mermaid source](./docs/NGABO_DEPLOYED_ARCHITECTURE.mmd).

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

## Reproduce the Current v0.1 Slice

The reproduction boundary is explicit:

- **Any contributor** can install the locked dependencies, run the deterministic/agent safety suites, build the web app, and exercise the desktop queue/signing flow against the local intake emulator.
- **A maintainer with access to `ngabo-amr-2026`** can run the real Firestore + Gemini + signed receiver E2E and the deployed desktop-to-dashboard demonstration.
- **A fork owner** needs a separate billed GCP project, Gemini credential, Firestore database, service accounts and Workload Identity Federation configuration. The checked-in GCP automation is intentionally bound to this repository/project and is not a portable one-command installer.

See the complete [reproduction runbook](./docs/REPRODUCING_NGABO.md) for the cloud topology, required environment contract, success criteria and fork boundary.

### 1. Clean checkout and locked installation

Prerequisites:

- Git;
- Node.js 20 or newer;
- Corepack with `pnpm@11.22.0`;
- Python 3.11 or newer;
- [uv](https://docs.astral.sh/uv/);
- Docker only when reproducing the container artifacts;
- Google Cloud CLI only for the real deployed E2E.

```bash
git clone https://github.com/ronnielutaro/Ngabo-AMR-Surveillance.git
cd Ngabo-AMR-Surveillance
corepack enable
corepack prepare pnpm@11.22.0 --activate
pnpm install --frozen-lockfile
uv sync --project services/core --frozen
```

### 2. Verify the repository

```bash
pnpm web:lint
pnpm web:typecheck
pnpm web:test
pnpm web:build
pnpm core:lint
pnpm core:typecheck
pnpm core:test
pnpm core:architecture
```

These commands verify the web build, deterministic AMR/connect behavior, proof-verification and safety policies, zero-human hero composition, and the Clean Architecture dependency rule. Passing tests are software evidence; they are not clinical validation.

### 3. Reproduce the desktop ingestion edge locally

Start the HMAC-validating local intake in terminal one:

```bash
uv run --project services/core python scripts/local_connect_intake.py
```

In terminal two, point the desktop client at that local intake.

PowerShell:

```powershell
$env:NGABO_INTAKE_URL = "http://127.0.0.1:8099/connect/batches"
uv run --project services/core python scripts/ngabo_connect_desktop.py
```

macOS/Linux:

```bash
NGABO_INTAKE_URL=http://127.0.0.1:8099/connect/batches \
  uv run --project services/core python scripts/ngabo_connect_desktop.py
```

Choose an empty watched folder, click **Start Watching**, and copy [`demo/connect/synthetic_gulu_surveillance_export.csv`](./demo/connect/synthetic_gulu_surveillance_export.csv) into it. The desktop window should report `DETECTED` followed by `ACKNOWLEDGED`.

This local intake proves file stability checks, SHA-256 identity, the durable SQLite queue, HMAC signing, retry handling and acknowledgement. It deliberately does **not** pretend to run Firestore, Gemini or the external A1 action locally.

### 4. Run the real cloud E2E (authorized maintainer)

After authenticating `gcloud`, selecting the `ngabo-amr-2026` project, and supplying `GEMINI_API_KEY` without committing or printing it:

```bash
uv run --project services/core python scripts/deadline_demo_e2e_smoke.py
```

Success ends with:

```text
E2E_RESULT: HERO_COMPLETED
```

The result must also contain a non-empty `delivery_id`, `ack_id`, `ack_verified=true`, and zero values for every human-intervention counter. A blocked/abstained run is a safe outcome, not successful hero completion.

### 5. Launch the deployed desktop-to-dashboard demo (authorized maintainer)

```bash
uv run --project services/core python scripts/ngabo_connect_desktop.py
```

Use the default private core endpoint, choose a clean folder, start watching, and then drop the synthetic fixture. The signed-in `gcloud` identity must be authorized to impersonate the narrow `ngabo-connect-demo` invoker service account. Watch the public dashboard for persisted batch counts, signal state, completion, delivery ID, acknowledgement ID and zero-human counters.

## Development Commands

```bash
pnpm dev             # Next.js development server
pnpm web:build       # production web build
pnpm web:test        # Vitest
pnpm core:health     # core bootstrap health check
pnpm core:test       # pytest
pnpm lint            # web + core lint
pnpm typecheck       # web + core typing
pnpm test            # web + core tests
pnpm build           # production web build
```

Container build, scan, immutable publication and deployment commands are documented in [`docs/CONTAINERS.md`](./docs/CONTAINERS.md). Trusted cloud delivery uses the checked-in GitHub Actions workflows and immutable Artifact Registry digests rather than `latest` tags.

## Current Repository State

The repository now contains an executable synthetic Connect-to-hero slice: desktop folder intake, deterministic validation/normalization/quarantine, deterministic AMR signal detection, Firestore-backed incident and workflow state, Google ADK orchestration, Gemini 3.6 Flash bounded reasoning, approved evidence retrieval, proof-carrying verification, A1 policy/freshness/idempotency, a signed external receiver, machine acknowledgement and a public Cloud Run dashboard.

Remaining release work includes reconciling all submission evidence, completing the release tag/freeze, hardening portable deployment automation, and validating the product with real practitioners and institutions. No real patient data, production hospital integration, clinical validation, product-market fit or national adoption is claimed.

## License

See [`LICENSE`](./LICENSE).
