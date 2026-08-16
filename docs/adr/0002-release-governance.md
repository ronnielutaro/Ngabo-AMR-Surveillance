# ADR 0002 — Release Governance: SemVer, Conventional Commits, and Gitflow

**Status:** Accepted  
**Date:** 2026-08-16

## Context

Ngabo is expected to evolve beyond a one-off hackathon submission into a versioned open-source system with explicit maturity stages: MVP, technical prototype, research prototype, shadow-mode pilot, validation/hardening, production candidate, and production-ready release.

The repository therefore needs a release model that:

- communicates compatibility and maturity;
- keeps commit history machine- and human-readable;
- separates active integration from released history;
- supports release stabilization and urgent hotfixes;
- gives coding agents explicit branch/version rules;
- prevents accidental claims that a software version alone establishes clinical/production validation.

## Decision

Adopt:

1. **Semantic Versioning 2.0.0** for formal release numbers.
2. **Conventional Commits 1.0.0** for commit messages.
3. A **Gitflow-style branch model** adapted to GitHub using `main` as the production/release branch and `develop` as the integration branch.
4. `CHANGELOG.md` for meaningful release history.
5. `ROADMAP.md` as the authority for product maturity-stage exit criteria.

## Gitflow Adaptation

Long-lived branches:

- `main`
- `develop`

Supporting branches:

- `feature/<name>` from `develop` -> `develop`
- `release/vX.Y.Z` from `develop` -> `main` and back to `develop`
- `hotfix/vX.Y.Z` from `main` -> `main` and `develop`

This is an intentional choice because Ngabo is being managed as explicitly versioned software with distinct release/validation cycles rather than as a continuously deployed web application with one undifferentiated production state.

## Pre-1.0 Policy

SemVer defines `0.y.z` as initial development.

Ngabo therefore uses:

- PATCH for backward-compatible fixes;
- MINOR for feature/release milestones;
- explicit breaking-change notation for incompatible changes, normally accompanied by a MINOR bump while pre-1.0;
- an explicit project decision for `1.0.0` rather than automated promotion.

`1.0.0` is reserved for the production-readiness milestone defined in `ROADMAP.md`.

## Consequences

### Positive

- predictable release history;
- clearer automated changelog/release tooling later;
- coding agents can reason about branch/version impact;
- mature product evolution remains separate from hackathon urgency;
- public releases have explicit stabilization points.

### Trade-offs

- Gitflow adds more branch/reconciliation overhead than GitHub Flow;
- a solo developer must still maintain discipline around release branches and merge-back;
- pre-1.0 breaking-change version semantics require project-specific judgement rather than blind automation.

## References

- https://semver.org/
- https://www.conventionalcommits.org/en/v1.0.0/
- https://nvie.com/posts/a-successful-git-branching-model/
