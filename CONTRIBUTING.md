# Contributing to Ngabo

Thank you for contributing to Ngabo.

Ngabo is an AMR surveillance and incident-response system with explicit safety boundaries. Contributions must preserve the distinction between deterministic surveillance logic, agentic investigation, and human authority.

Before contributing, read:

1. `CLAUDE.md`
2. `AGENTS.md`
3. `ROADMAP.md`
4. `docs/PRD.md`
5. `docs/LEAN_CANVAS.md`
6. `docs/COMPETITOR_ANALYSIS.md`
7. `docs/VALUE_PROPOSITION_CANVAS.md`
8. `docs/SYSTEM_DESIGN.md`
9. `docs/AGENT_ARCHITECTURE.md`
10. `docs/DATA_SAFETY_EVALUATION.md`
11. `docs/UI_UX_SPEC.md`

The product-strategy documents explain whom Ngabo is intended to serve, which alternatives already exist, where Ngabo aims to differentiate and which assumptions still require validation. They guide scope and messaging but do not supersede the active issue, safety contracts, Clean Architecture or evidence requirements.

---

## Development Workflow

Ngabo uses a **Gitflow-style workflow** adapted to GitHub.

### Long-lived branches

- `main` — released/release-ready history
- `develop` — integration branch for the next release

Do not develop features directly on `main`.

### Feature branches

Create from `develop`:

```bash
git switch develop
git pull
git switch -c feature/<short-name>
```

Examples:

```text
feature/ast-normalizer
feature/incident-timeline
feature/agent-clarification
```

Open a pull request back to `develop`.

### Release branches

Create from `develop` when a version's planned functionality is complete:

```text
release/v0.2.0
```

A release branch may contain:

- final defect fixes;
- version metadata;
- changelog/release notes;
- documentation;
- release evaluation/hardening.

Do not add new product scope to a release branch.

Merge the finished release branch to `main`, tag the release, then merge/reconcile the release branch back into `develop`.

### Hotfix branches

For urgent fixes to a released version:

```text
hotfix/v0.2.1
```

Create from `main`; merge into `main` and `develop`.

---

## Semantic Versioning

Ngabo uses **Semantic Versioning 2.0.0**.

```text
MAJOR.MINOR.PATCH
```

After `1.0.0`:

- MAJOR — incompatible public API/event/schema change;
- MINOR — backward-compatible functionality;
- PATCH — backward-compatible bug fix.

During `0.y.z` initial development:

- bug fixes normally increment PATCH;
- feature/release milestones normally increment MINOR;
- breaking changes must still be explicitly documented as breaking and normally increment MINOR;
- `1.0.0` is a deliberate production-readiness milestone and must not be produced automatically simply because a breaking commit exists.

See `ROADMAP.md` for Ngabo's release maturity policy.

---

## Conventional Commits

Every commit must follow **Conventional Commits 1.0.0**:

```text
<type>[optional scope]: <description>
```

Preferred types:

```text
feat
fix
docs
test
refactor
perf
build
ci
chore
revert
```

Preferred scopes:

```text
web
core
surveillance
agent
evidence
events
data
eval
infra
docs
release
```

Examples:

```text
feat(agent): add clarification resume workflow
fix(surveillance): exclude unknown AST values from similarity score
test(eval): add fabricated citation guard case
docs(api): document incident review endpoint
ci(release): validate conventional commits
```

Breaking changes use `!` and/or a `BREAKING CHANGE:` footer:

```text
feat(events)!: revise incident event envelope
```

Keep commits focused. If a change has two unrelated purposes, split it.

---

## Pull Request Requirements

A pull request should explain:

- what changed;
- why it changed;
- how it was tested;
- whether it changes a public API/schema/event;
- whether it affects safety or human-review boundaries;
- whether documentation must change;
- whether an ADR is required.

Before merge:

- relevant tests pass;
- type/lint checks pass;
- no real patient data is present;
- no secret is committed;
- documentation reflects changed contracts;
- architecture/safety invariants remain intact.

### Required PR quality gates

PRs into `develop` or `main` run the repository-owned quality contract described in `docs/CI_QUALITY_GATES.md`.

The stable required result is `PR Quality Gate`. It always runs; path classification may skip an expensive core/web/infra lane only after the workflow has started. Shared CI/toolchain changes run the cross-cutting lanes, while docs-only changes still produce the policy, dependency-review and final-gate checks.

Use the same local contracts before review:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm web:build
pnpm core:lock:check
pnpm core:sync:frozen
pnpm core:architecture
pnpm core:build
pnpm core:audit
pnpm web:audit
pnpm infra:test
pnpm ci:test
pnpm ci:pins
```

CI dependency installs are frozen. Caches are performance aids only and never replace lockfile or validation checks. High-severity dependency findings fail the web/Dependency Review gates; the core uv audit currently fails on any reported vulnerability.

Changes to CI control-plane files are separately inspected by `CI Control Plane`. That metadata-only workflow never checks out PR-head code. An owner-authored protected change requires an explicit approval marker bound to the exact current PR head SHA:

```text
CI-Control-Plane-Approval: <PR_HEAD_SHA>
```

Any new push changes the SHA and requires a fresh marker. This is an auditable control, not a hidden bypass. See `docs/CI_QUALITY_GATES.md` for the complete path and ruleset contract.

CI validates source/build quality; it does not prove deployed behavior.

---

## Architecture Decisions

Material architecture changes require an Architecture Decision Record under:

```text
docs/adr/
```

Examples that require an ADR:

- replacing Firestore;
- changing the event architecture;
- introducing another orchestration framework;
- moving deterministic surveillance logic into an LLM;
- changing human-review boundaries;
- introducing a real clinical-data integration architecture.

Routine refactors that preserve public behavior do not require an ADR.

---

## Safety Requirements

Contributions must not:

- make the runtime agent prescribe treatment;
- make the runtime agent autonomously confirm an outbreak;
- let model output replace deterministic scientific calculations;
- fabricate evidence/citations;
- bypass the human review gate;
- silently convert missing laboratory facts into guessed values;
- commit real patient data to the public repository.

---

## Data Contributions

Public fixtures and demonstration datasets must be synthetic unless a separately governed contribution explicitly permits otherwise.

Synthetic data should be clearly labelled and should not reconstruct identifiable real patient records.

---

## Release Checklist

Before a formal release:

- [ ] release branch created from `develop`;
- [ ] target version selected under SemVer policy;
- [ ] tests/evaluation pass;
- [ ] security/safety regressions reviewed;
- [ ] `CHANGELOG.md` updated;
- [ ] README/docs match actual behavior;
- [ ] final release merged into `main`;
- [ ] Git tag `vX.Y.Z` created;
- [ ] release changes reconciled back into `develop`.

---

## References

- Semantic Versioning 2.0.0: https://semver.org/
- Conventional Commits 1.0.0: https://www.conventionalcommits.org/en/v1.0.0/
- Gitflow model: https://nvie.com/posts/a-successful-git-branching-model/
