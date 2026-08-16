# Ngabo Product & Release Roadmap

Ngabo is an **open-source, event-driven antimicrobial resistance surveillance and incident-response system** that transforms AMR surveillance signals into structured, evidence-backed investigations and coordinated human-reviewed response workflows.

This roadmap describes the maturity path of the product. The product identity remains **Ngabo** throughout; terms such as MVP, research prototype, pilot, and production deployment describe the maturity of a release, not what the product fundamentally is.

> **Important:** roadmap versions describe software/product maturity. They are not, by themselves, claims of clinical validation, regulatory approval, or suitability for patient-care decisions.

---

## 1. Release Philosophy

Ngabo will evolve through explicit, inspectable release cycles:

```text
Ngabo
  │
  ├─ 0.1.x  Hackathon MVP
  │          synthetic data
  │          complete surveillance-to-action workflow
  │
  ├─ 0.2.x  Technical Prototype
  │          stronger evaluation
  │          reliability + observability
  │          domain-expert feedback
  │
  ├─ 0.3.x  Research Prototype
  │          retrospective real-world datasets where approved
  │          deeper surveillance evaluation
  │          research reproducibility
  │
  ├─ 0.4.x  Shadow-Mode Pilot
  │          hospital/facility workflow integration
  │          no autonomous operational authority
  │          prospective shadow evaluation
  │
  ├─ 0.5.x  Validation & Pilot Hardening
  │          prospective evaluation
  │          governance + security + interoperability
  │          operational reliability
  │
  ├─ 0.9.x  Production Candidate
  │          stable public contracts
  │          deployment hardening
  │          documented operating model
  │
  └─ 1.0.0  Production-Ready Release
             stable documented public interfaces
             validated intended-use boundaries
             security + governance + integration baseline
             production deployment readiness
```

Versions after `1.0.0` follow normal semantic-versioning compatibility rules.

Dates beyond the hackathon release are intentionally not promised. Research validation, partner access, governance review, and real-world pilot readiness must determine pace—not arbitrary calendar deadlines.

---

## 2. v0.1.x — Hackathon MVP

### Product goal

Prove the core Ngabo thesis end-to-end:

> **A suspicious AMR surveillance signal can trigger an autonomous, evidence-backed investigation workflow that ends in human-reviewed coordinated action.**

### Required capabilities

- synthetic WHONET-style data ingestion;
- deterministic schema validation and normalization;
- deterministic resistance-pattern surveillance;
- persisted investigation candidate / incident;
- Pub/Sub-triggered agent workflow;
- Google ADK + Gemini investigation;
- deterministic tools for calculations/context;
- approved evidence retrieval;
- targeted clarification pause/resume;
- structured incident-response package;
- human safety gate;
- notification action;
- acknowledgement/follow-up state;
- audit trail;
- Next.js incident-response console;
- Google Cloud deployment;
- reproducible tests and evaluation artifact.

### Explicit exclusions

- real patient data;
- clinical validation claims;
- autonomous treatment decisions;
- autonomous outbreak confirmation;
- production hospital integration;
- genomics as a core requirement.

### Initial release

Target release: **`v0.1.0`**

Patch releases such as `v0.1.1` may fix defects without changing the release's core scope.

---

## 3. v0.2.x — Technical Prototype

### Product goal

Move from a winning/demo-quality MVP to a technically stronger system that can withstand external engineering and domain review.

### Priorities

- expand deterministic surveillance scenario benchmark;
- stronger false-alert and edge-case evaluation;
- improve idempotency/retry testing;
- failure recovery and resumability;
- structured agent evaluation suite;
- stronger observability/tracing;
- security review of runtime boundaries;
- evidence-corpus quality controls;
- improve UX from microbiologist/IPC feedback;
- formal domain-expert review;
- document known limitations and technical debt.

### Exit signal

Ngabo can repeatedly execute its intended workflow under a materially broader test suite and has incorporated feedback from relevant AMR/microbiology/public-health professionals.

---

## 4. v0.3.x — Research Prototype

### Product goal

Test the product hypothesis against appropriately governed retrospective real-world data and develop a publishable/reproducible scientific evaluation approach.

### Priorities

- approved retrospective AMR datasets;
- institution-specific baseline modelling where appropriate;
- compare surveillance approaches;
- characterize false positives/false negatives;
- evaluate data-quality sensitivity;
- stronger epidemiological context;
- research protocol and reproducible evaluation;
- begin phenotype/genotype evidence work where justified;
- optional AMRFinderPlus integration after the phenotype workflow is stable;
- expert interpretation of evaluation outcomes.

### Data rule

Real-world data enters only under appropriate authorization, governance, privacy, and security arrangements. Public repository fixtures remain synthetic/de-identified as appropriate.

### Exit signal

The system has credible research evidence describing what it can detect, what it cannot infer, and where human review remains essential.

---

## 5. v0.4.x — Shadow-Mode Pilot

### Product goal

Evaluate Ngabo inside a real operational environment without giving it autonomous operational authority.

### Shadow mode

Ngabo may process permitted surveillance signals and prepare incident packages while existing professional workflows remain authoritative.

This allows comparison of:

- time-to-investigation;
- signal usefulness;
- alert burden;
- evidence quality;
- workflow fit;
- human acceptance;
- failure modes.

### Priorities

- facility identity and access controls;
- deployment isolation;
- audit/security hardening;
- actual interoperability connector(s);
- workflow configuration;
- monitoring and incident-management procedures;
- prospective shadow evaluation;
- structured user feedback.

### Exit signal

There is sufficient evidence to decide whether Ngabo should progress into a more active operational pilot and what safeguards are required.

---

## 6. v0.5.x — Validation & Pilot Hardening

### Product goal

Prepare Ngabo for increasingly consequential real-world use within explicitly defined intended-use boundaries.

### Priorities

- prospective evaluation;
- robust security controls;
- role-based access control;
- privacy/data-governance controls;
- facility tenancy where needed;
- observability/SLOs;
- data retention policies;
- operational support procedures;
- validated integration contracts;
- model/version governance;
- evidence-source governance;
- human-oversight procedures;
- deployment and rollback procedures.

### Exit signal

Technical, scientific, governance, and operational stakeholders agree that the system can enter production-candidate hardening for its defined use case.

---

## 7. v0.9.x — Production Candidate

### Product goal

Stabilize the public and operational contracts expected to become `1.0.0`.

### Priorities

- stable APIs/events/schemas;
- migration policy;
- backward-compatibility review;
- production security review;
- deployment automation;
- backup/recovery where applicable;
- monitoring and alerting;
- integration documentation;
- operator runbooks;
- support/escalation model;
- release-candidate evaluation;
- complete production documentation.

Breaking public-interface changes should become rare at this stage.

---

## 8. v1.0.0 — Production-Ready Release

`1.0.0` is a deliberate milestone, not an automatic result of a breaking Conventional Commit during `0.x` development.

For Ngabo, `1.0.0` means the project has a stable documented public interface and has satisfied the technical, scientific, security, governance, and operational exit criteria required for the intended production use case.

It does **not** mean Ngabo can make arbitrary clinical decisions. Human-authority boundaries remain part of the product architecture.

Minimum expectations include:

- stable documented public API/event/data contracts;
- production deployment process;
- appropriate security and access control;
- monitoring and auditability;
- data-governance model;
- release/rollback process;
- documented intended use and limitations;
- evidence from appropriate validation/pilot work;
- human-review boundaries implemented and governed.

---

# Release Governance

## 9. Semantic Versioning

Ngabo uses **Semantic Versioning 2.0.0**:

```text
MAJOR.MINOR.PATCH
```

General rule after `1.0.0`:

- **MAJOR** — incompatible public API/event/schema changes;
- **MINOR** — backward-compatible functionality;
- **PATCH** — backward-compatible fixes.

### Initial development policy (`0.y.z`)

Semantic Versioning defines `0.y.z` as initial development, where the public API is not yet stable.

Ngabo applies this project policy during `0.x`:

- backward-compatible bug fix → PATCH;
- backward-compatible feature/release milestone → MINOR;
- breaking change → explicitly marked `BREAKING CHANGE`, documented, and normally increments MINOR while the project remains pre-1.0;
- **no automated process may promote Ngabo to `1.0.0`** solely because a breaking commit exists.

`1.0.0` requires the explicit production-readiness decision described above.

### Pre-release identifiers

Where useful:

```text
v0.4.0-alpha.1
v0.4.0-beta.1
v0.9.0-rc.1
```

### Git tags

Every formal release is tagged:

```text
v0.1.0
v0.2.0
v1.0.0
```

Released tags are immutable. Fixes require a new release.

---

## 10. Conventional Commits

All commits use **Conventional Commits 1.0.0**.

Format:

```text
<type>[optional scope]: <description>
```

Recommended types:

- `feat` — product functionality;
- `fix` — bug fix;
- `docs` — documentation only;
- `test` — tests/evaluation;
- `refactor` — internal restructuring without behavior change;
- `perf` — performance improvement;
- `build` — build/dependency changes;
- `ci` — CI/CD;
- `chore` — maintenance;
- `revert` — revert prior change.

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
feat(surveillance): add phenotype similarity detector
fix(events): prevent duplicate incident creation
feat(agent): add targeted clarification workflow
test(eval): add prompt injection scenario
docs(roadmap): define shadow pilot release
```

Breaking changes use `!` and/or a `BREAKING CHANGE:` footer:

```text
feat(events)!: revise surveillance signal schema
```

---

## 11. Gitflow Workflow

Ngabo uses a Gitflow-style release workflow adapted to GitHub and the repository's `main` branch.

### Long-lived branches

#### `main`

- contains released / release-ready history;
- every formal release merged to `main` receives a SemVer tag;
- direct feature development on `main` is prohibited once Gitflow is initialized.

#### `develop`

- integration branch for the next release;
- feature branches normally merge here through pull requests.

### Supporting branches

#### Features

```text
feature/<short-name>
```

Branch from: `develop`  
Merge into: `develop`

Examples:

```text
feature/ast-normalizer
feature/incident-timeline
feature/agent-clarification
```

#### Release branches

```text
release/v<MAJOR>.<MINOR>.<PATCH>
```

Branch from: `develop`  
Merge into: `main` **and** back into `develop`

Use release branches for:

- version metadata;
- changelog/release notes;
- final documentation;
- release-only bug fixes;
- final regression/evaluation.

No new product features should enter a release branch.

#### Hotfix branches

```text
hotfix/v<MAJOR>.<MINOR>.<PATCH>
```

Branch from: `main`  
Merge into: `main` **and** `develop`

Use only for urgent defects affecting a released version.

### Pull requests

- substantive changes should arrive through PRs;
- CI/tests must pass before merge;
- PR description should state scope, tests, and architecture/safety impact;
- material architecture changes require an ADR;
- squash/rebase policy may evolve, but resulting commit history must preserve Conventional Commit semantics needed for releases.

---

## 12. Release Cycle

A normal release proceeds:

```text
develop
   ↓
release/v0.2.0
   ↓
final tests + docs + changelog
   ↓
main
   ↓
tag v0.2.0
   ↓
merge release changes back into develop
```

The release is complete only when:

- release criteria pass;
- documentation reflects actual behavior;
- changelog/release notes are updated;
- version is tagged;
- release changes are reconciled back to `develop`.

---

## 13. Changelog

Maintain `CHANGELOG.md` using an `Unreleased` section plus versioned releases.

The changelog should communicate meaningful changes to users/operators rather than merely list commit hashes.

---

## 14. Roadmap Change Policy

This roadmap is directional, not immutable.

A change to timing or feature sequencing is normal. A change to product safety boundaries, validation posture, or major maturity criteria should be explicitly documented rather than silently rewritten.

When evidence contradicts the roadmap, **change the roadmap—not the evidence**.

---

## References

- Semantic Versioning 2.0.0: https://semver.org/
- Conventional Commits 1.0.0: https://www.conventionalcommits.org/en/v1.0.0/
- Gitflow model (adapted for `main`): https://nvie.com/posts/a-successful-git-branching-model/
