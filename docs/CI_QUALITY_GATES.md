# Ngabo PR Quality Gates

**Status:** Issue #88 implementation contract  
**Scope:** deterministic pull-request validation only  
**Cloud authority:** none

## Required checks

Pull requests targeting `develop` or `main` start `.github/workflows/pr-quality.yml` without workflow-level path filters. Expensive lanes may skip only after `Changed Paths` deterministically classifies the explicit PR diff. The stable `PR Quality Gate` job always runs and fails if any required lane failed, was cancelled, or was incorrectly skipped.

After staged post-merge activation, the repository ruleset also requires `CI Control Plane`. The ruleset is managed by `infra/github/pr_quality_ruleset.py` and targets only `develop` and `main`.

CI does **not** prove deployed behavior and receives no GCP credentials, OIDC permission, service-account identity, Secret Manager access, or deployment authority.

## Change classification

`scripts/ci/classify_changes.py` owns path classification.

- `services/core/**` and `data/**` require the core lane.
- `apps/web/**` requires the web lane.
- `infra/gcp/**` requires the infrastructure regression lane.
- `.github/workflows/**`, `scripts/ci/**`, `infra/github/**`, and shared repository/toolchain configuration are cross-cutting and require all relevant lanes.
- documentation-only changes may skip core/web/infra, but `CI Policy`, `Dependency Security`, and `PR Quality Gate` still produce real checks.
- an empty/unclassifiable diff fails safe by requiring every lane.

The workflow itself never uses `paths:` or `paths-ignore:` to disappear a required check.

## Core lane

Pinned CI runtime: Python `3.11.16`; uv `0.12.4`.

```bash
cd services/core
uv lock --check
uv sync --frozen
uv run ruff check .
uv run mypy ngabo tests
uv run python ../../scripts/ci/check_architecture.py ngabo
uv run pytest
uv build
```

`uv lock --check` and `uv sync --frozen` prevent manifest/lock drift. The architecture checker enforces the frozen Clean Architecture dependency rule from `docs/CLEAN_ARCHITECTURE.md`: domain cannot depend on application/interfaces/infrastructure/bootstrap or framework/cloud/network SDKs; application cannot depend on interfaces/infrastructure/bootstrap or those vendor SDKs.

## Web lane

Pinned CI runtime: pnpm `11.22.0`; Node `24.19.0`.

```bash
pnpm install --frozen-lockfile
pnpm --filter ngabo-web exec eslint .
pnpm --filter ngabo-web exec tsc --noEmit
pnpm --filter ngabo-web exec vitest run
pnpm --filter ngabo-web exec next build
```

CI invokes the underlying tools directly rather than trusting mutable package scripts, so a PR cannot turn a required lint/type/test/build script into a no-op and still satisfy the gate. The frozen install validates `package.json` against `pnpm-lock.yaml`.

## Infrastructure regression lane

Infrastructure changes are verified offline only. Full mypy and tests run across `infra/gcp`; Ruff is applied to changed `infra/gcp` Python files so #88 does not retroactively rewrite the already-certified #87 identity implementation solely to clear pre-existing style debt.

```bash
cd services/core
uv lock --check
uv sync --frozen
uv run mypy ../../infra/gcp
uv run pytest ../../infra/gcp/tests
```

Any changed `infra/gcp/*.py` file is additionally passed to Ruff. Normal PR CI never runs `gcloud`, `infra:apply`, `identity:apply`, or any cloud mutation.

## Dependency security

Every PR runs the always-blocking `Dependency Security` job:

```bash
cd services/core
uv --preview audit --frozen
cd ../..
pnpm audit --audit-level=high
```

The Python audit fails on any vulnerability reported by uv, which is stricter than the Issue #88 high-severity floor. The pnpm audit fails on high/critical findings. Audit execution failures fail closed.

A first live #88 run also attempted GitHub's native `actions/dependency-review-action`, but GitHub returned `Dependency review is not supported on this repository` because the repository Dependency Graph is currently disabled. The connector available to this implementation has no repository security-analysis settings mutation. #88 therefore does not disguise that platform setting as a passing check: package-manager audits are the blocking dependency-security contract until the Dependency Graph is enabled and native Dependency Review can be added honestly.

## Action pinning and caches

Every external Action reference must be a full 40-hex commit SHA. `scripts/ci/check_workflow_pins.py` enforces that contract across committed workflow files.

Caches may contain package-manager download/store data only. Frozen installs and lock checks still run on cache hits. `node_modules`, `.venv`, build output, credentials, and prior test results are not trusted as validation substitutes.

## CI control-plane changes

`.github/workflows/ci-control-plane.yml` uses `pull_request_target` **only for GitHub metadata inspection**. It never checks out or executes PR-head code.

Protected control-plane paths include workflows, `scripts/ci/**`, `infra/github/**`, package/toolchain manifests, and web lint/type/test/build configuration. A protected change must be authored by the repository owner and the PR body must contain an approval bound to the exact current head SHA:

```text
CI-Control-Plane-Approval: <PR_HEAD_SHA>
```

A new push changes the head SHA and invalidates the previous marker. This is intentionally explicit and auditable; it is not a hidden bypass.

The Issue #88 bootstrap PR is staged because `CI Control Plane` cannot protect itself until its workflow exists on the default branch. Issue #88 therefore remains open until post-merge ruleset activation and default-branch control-plane proof are independently accepted.

## Failure evidence

Jobs write concise summaries and upload only sanitized failure evidence for five days. Do not upload environment dumps, `.env` files, Git credentials, `GITHUB_TOKEN`, OIDC tokens, Google credentials, or `gha-creds-*.json`.

## Local equivalents

Before requesting review, run:

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

For ruleset inspection from an authorized maintainer environment:

```bash
pnpm ci:ruleset:plan
pnpm ci:ruleset:validate
pnpm ci:ruleset:teardown:dry-run
```

Do not run ruleset `apply` from normal PR CI.

## Intended repository ruleset

`Ngabo Required PR Quality` targets exactly:

```text
refs/heads/develop
refs/heads/main
```

It is designed to require pull requests, `PR Quality Gate`, `CI Control Plane`, strict up-to-date status checks, resolved review threads, and blocked force pushes. It requires zero approving reviews so the solo-maintainer hackathon workflow remains operable; independent review remains a documented maintainer acceptance process.

Ruleset activation is a staged post-merge acceptance step. A green implementation PR alone does not close Issue #88.
