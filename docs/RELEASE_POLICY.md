# Ngabo Release Policy

This document is a concise operational companion to `ROADMAP.md` and `CONTRIBUTING.md`.

## Standards

- Semantic Versioning 2.0.0
- Conventional Commits 1.0.0
- Gitflow-style branching adapted to `main` + `develop`

## Branches

```text
main                  released / release-ready history
develop               next-release integration
feature/<name>        feature work from develop
release/vX.Y.Z        release stabilization from develop
hotfix/vX.Y.Z         urgent released-version fix from main
```

## Version Rules

### During 0.x

- fix -> PATCH
- feature/release milestone -> MINOR
- breaking change -> mark explicitly; normally MINOR while pre-1.0
- never auto-promote to 1.0.0

### From 1.0.0

- breaking public contract -> MAJOR
- backward-compatible feature -> MINOR
- backward-compatible fix -> PATCH

## Commit Format

```text
<type>[optional scope]: <description>
```

Examples:

```text
feat(agent): add evidence synthesis workflow
fix(events): make notification handler idempotent
docs(release): update v0.2 exit criteria
```

## Release Flow

```text
develop
   ↓
release/vX.Y.Z
   ↓
final tests + docs + CHANGELOG
   ↓
main
   ↓
tag vX.Y.Z
   ↓
merge release changes back into develop
```

Formal release tags are immutable.

## Authority

Release numbers communicate software maturity/compatibility. They do not independently establish scientific, clinical, regulatory, security, or production validation.

Maturity-stage promotion must satisfy the evidence/exit criteria in `ROADMAP.md` and requires deliberate project-owner/stakeholder approval.
