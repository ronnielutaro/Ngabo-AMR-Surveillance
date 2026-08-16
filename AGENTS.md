# AGENTS.md — Ngabo Coding-Agent Rules

This file applies to AI coding agents working anywhere in this repository.

Read `CLAUDE.md` first. `CLAUDE.md` contains the project-wide implementation contract; this file summarizes execution behavior and local invariants for coding agents.

---

## Mission

Build Ngabo as a **safe, event-driven AMR incident-response system**.

The current release target is the `0.1.x` hackathon MVP, but coding agents must preserve the longer product trajectory documented in `ROADMAP.md`.

Do not optimize for feature count. Optimize for:

- working autonomy;
- deterministic scientific logic;
- explicit state;
- traceability;
- bounded clinical/public-health claims;
- reproducibility;
- maintainable release discipline;
- a clear 4-minute demo for v0.1.

---

## Required Read Order

Before major implementation:

1. `CLAUDE.md`
2. `ROADMAP.md`
3. `CONTRIBUTING.md`
4. `docs/PRD.md`
5. `docs/SYSTEM_DESIGN.md`
6. `docs/AGENT_ARCHITECTURE.md`
7. `docs/DATA_SAFETY_EVALUATION.md`
8. `docs/UI_UX_SPEC.md`
9. `docs/IMPLEMENTATION_PLAN.md`

Also consult `CHANGELOG.md` before release-oriented work.

---

## Product Identity vs Release Maturity

Do not describe Ngabo itself as merely “the prototype” in permanent product identity copy.

Preferred:

> **Ngabo is an open-source AMR surveillance and incident-response system.**

Then state maturity separately, for example:

> `v0.1.0` hackathon MVP in development.

Use `ROADMAP.md` as the source of truth for maturity stages.

---

## Runtime Boundary

### Deterministic layer owns

- ingest;
- parsing;
- schema validation;
- normalization;
- AST calculations;
- resistance-profile similarity;
- temporal/location windows;
- baseline calculations;
- signal scoring;
- state transitions;
- idempotency.

### Agentic layer owns

- investigation planning;
- choosing approved tools;
- gathering contextual evidence;
- identifying missing information;
- asking targeted clarification;
- evidence synthesis;
- hypothesis generation with labels;
- incident-package drafting.

### Human owns

- clinically/public-health consequential approval;
- outbreak confirmation through appropriate professional processes;
- patient treatment decisions.

Never blur these boundaries.

---

## Agent Runtime Restrictions

The Ngabo runtime agent must not:

- execute arbitrary shell commands;
- issue unrestricted database queries;
- browse arbitrary URLs as approved evidence;
- mutate raw source data;
- send alerts before review approval;
- prescribe treatment;
- claim an outbreak is confirmed;
- fabricate citations.

Keep runtime tools narrow, typed, and auditable.

---

## UI Restrictions

Do not build the core experience as a chat window.

Implement the operational hierarchy from `docs/UI_UX_SPEC.md`:

- dashboard;
- import/validation;
- incident queue;
- incident detail;
- deterministic signal explanation;
- resistance-profile table;
- agent/tool timeline;
- targeted clarification;
- structured package;
- human review;
- response tracking.

Do not expose hidden model chain-of-thought.

---

## Data Rules

- synthetic demo data only for public v0.1;
- every fixture declares that it is synthetic;
- never commit real patient data;
- unknown/missing values remain unknown/missing;
- do not generate plausible-looking values to make a demo prettier;
- keep raw import and normalized data logically distinct.

Future real-world datasets must follow the governance and release-stage constraints in `ROADMAP.md`.

---

## Evidence Rules

- evidence corpus is curated for v0.1;
- each source has source ID, title, publisher, URL, and version/date where possible;
- generated package may cite only retrieved source IDs;
- “no source found” is an acceptable result;
- fabricated guidance is not.

---

## State / Event Rules

- Firestore is canonical operational state;
- incident transitions are explicit;
- event handlers are retry-safe;
- duplicate Pub/Sub events do not create duplicate actions;
- persisted audit events are append-only;
- failed workflow steps produce visible failure state.

---

## Coding Standards

### Python

- Python 3.11+
- FastAPI
- Pydantic v2
- type annotations on public interfaces
- pytest
- keep domain logic independent of HTTP and cloud SDKs

### TypeScript

- strict TypeScript
- typed API models
- shadcn/ui primitives where appropriate
- avoid client-side reinterpretation of medical/scientific strings
- Playwright for critical user journeys

### General

- small modules;
- explicit dependencies;
- no magic global state;
- no swallowed exceptions;
- structured logs;
- configuration through environment/settings objects;
- no secrets in code or docs.

---

## Gitflow — Mandatory Branch Discipline

Ngabo uses a **Gitflow-style workflow** adapted to GitHub.

### Long-lived branches

- `main` — released / release-ready history;
- `develop` — integration branch for the next release.

Once `develop` exists, feature work must not be committed directly to `main`.

### Feature branches

Create from `develop`:

```text
feature/<short-name>
```

Merge through a PR into `develop`.

Examples:

```text
feature/ast-normalizer
feature/incident-timeline
feature/agent-clarification
```

### Release branches

Create from `develop`:

```text
release/vX.Y.Z
```

Release branches are for:

- final fixes;
- version metadata;
- changelog/release notes;
- documentation;
- final evaluation/hardening.

Do not introduce new product scope on a release branch.

A completed release merges to `main`, receives tag `vX.Y.Z`, and is merged/reconciled back into `develop`.

### Hotfix branches

Create urgent release fixes from `main`:

```text
hotfix/vX.Y.Z
```

Merge into both `main` and `develop`.

See `CONTRIBUTING.md` and `ROADMAP.md` for the full workflow.

---

## Semantic Versioning — Mandatory

Ngabo uses **Semantic Versioning 2.0.0**.

Formal releases use:

```text
MAJOR.MINOR.PATCH
```

and Git tags:

```text
vMAJOR.MINOR.PATCH
```

During `0.y.z` initial development:

- bug fix → normally PATCH;
- backward-compatible feature/release milestone → normally MINOR;
- breaking change → explicitly marked and normally MINOR while pre-1.0;
- **never automatically create `1.0.0`** solely because a breaking commit exists.

`1.0.0` is the deliberate production-readiness milestone defined in `ROADMAP.md`.

Do not mutate an existing released tag/version; create a new release.

---

## Conventional Commits — Mandatory

All commits must follow **Conventional Commits 1.0.0**:

```text
<type>[optional scope]: <description>
```

Allowed/recommended types:

- `feat`
- `fix`
- `docs`
- `test`
- `refactor`
- `perf`
- `build`
- `ci`
- `chore`
- `revert`

Recommended scopes:

- `web`
- `core`
- `surveillance`
- `agent`
- `evidence`
- `events`
- `data`
- `eval`
- `infra`
- `docs`
- `release`

Examples:

```text
feat(agent): add clarification resume workflow
fix(events): prevent duplicate incident creation
test(eval): add prompt injection scenario
docs(roadmap): clarify pilot exit criteria
```

Breaking changes must use `!` and/or a `BREAKING CHANGE:` footer:

```text
feat(events)!: revise surveillance signal schema
```

Coding agents must not create vague messages such as:

```text
update stuff
fix
changes
wip
```

unless the user explicitly requests a temporary local commit strategy that will be cleaned before merge.

---

## Pull Request Discipline

Substantive work should be merged through PRs.

A PR should state:

- scope;
- reason;
- tests run;
- public API/schema/event impact;
- safety/human-review impact;
- documentation impact;
- ADR requirement if applicable.

Do not merge knowingly failing required tests.

---

## Changelog Discipline

Maintain `CHANGELOG.md`.

User/operator-visible changes should enter `Unreleased` during development and move into the appropriate version section during release preparation.

Do not generate a changelog that merely dumps commit hashes; summarize meaningful behavior changes.

---

## Before Completing Any Task

Run the checks appropriate to the changed surface.

Expected eventual commands may include:

```bash
# Python
uv run pytest
uv run ruff check .
uv run mypy .

# Web
pnpm lint
pnpm typecheck
pnpm test
pnpm exec playwright test
```

If the repository uses different finalized commands after scaffolding, update README/CLAUDE.md rather than silently diverging.

Before a commit or PR, also verify:

- branch follows Gitflow naming/purpose;
- commit message follows Conventional Commits;
- release impact is compatible with SemVer policy;
- changelog/docs are updated when required.

---

## Commit / Change Discipline

For each milestone:

- keep changes focused;
- avoid mass formatting unrelated files;
- do not rename established product concepts casually;
- update docs when public contracts change;
- create ADR for material architecture changes;
- do not introduce stretch features before core acceptance criteria are green.

One commit should represent one coherent purpose where practical.

---

## Product Vocabulary

Preferred:

- surveillance signal;
- investigation candidate;
- possible cluster;
- incident;
- evidence-backed package;
- human review;
- approved escalation;
- prototype signal score.

Avoid autonomous factual use of:

- confirmed outbreak;
- diagnosis;
- treatment recommendation;
- clinical confidence score.

---

## Primary Demo Scenario

The canonical v0.1 demo scenario is a synthetic neonatal-unit *Klebsiella pneumoniae* resistance-pattern cluster with one intentionally missing metadata field.

The system must demonstrate:

```text
import
  ↓
validation
  ↓
signal
  ↓
autonomous investigation
  ↓
clarification
  ↓
resume
  ↓
incident package
  ↓
human approval
  ↓
notification
  ↓
acknowledgement
```

Do not replace the real path with canned UI state.

---

## Stop Conditions

Stop and surface the issue instead of guessing when:

- docs contradict each other materially;
- a requested feature violates the safety boundary;
- a dependency requires replacing a frozen architecture decision;
- the available data cannot support a claimed calculation;
- a model output cannot be validated;
- a third-party integration would require credentials/permissions not available;
- requested release/version action conflicts with `ROADMAP.md` or SemVer policy;
- a branch/merge request would violate Gitflow and the user has not explicitly authorized an exception.

---

## Scope Freeze

Until the end-to-end v0.1 core works and passes acceptance tests, do not add:

- pathogen genomics;
- AMRFinderPlus;
- vector database;
- BigQuery;
- GKE;
- Redis/Kafka;
- LangGraph;
- mobile app;
- real patient data;
- production hospital connector.

---

## Success Criterion

The coding agent has succeeded when the repository truthfully demonstrates the PRD's Definition of Done **and** leaves behind a coherent versioned release history—not when it has generated the largest amount of code.
