# Ngabo PR Quality Gates

**Status:** Issue #88 — Cloud Foundation 1A.4: Enforce monorepo PR quality gates in GitHub Actions  
**Scope:** deterministic pull-request validation only  
**Cloud authority:** none

## Required checks

Pull requests targeting `develop` or `main` start `.github/workflows/pr-quality.yml` without workflow-level path filters. Expensive lanes may skip only after `Changed Paths` deterministically classifies the explicit PR diff. The stable `PR Quality Gate` job always runs and fails if any required lane failed, was cancelled, or was incorrectly skipped.

After staged post-merge activation, the repository ruleset also requires `CI Control Plane`. The ruleset is managed by `infra/github/pr_quality_ruleset.py` and targets only `develop` and `main`.

CI does **not** prove deployed behavior and receives no GCP credentials, OIDC permission, service-account identity, Secret Manager access, or deployment authority.

## Change classification

### Rename-aware changed-path collection

`scripts/ci/collect_changed_paths.py` runs `git diff --name-status -z --find-renames` and parses the NUL-separated output to capture **both** source and destination for renames and copies. This prevents a rename such as `services/core/ngabo/domain/foo.py → docs/foo.py` from bypassing the core lane.

Required semantics per status letter:

| Status | Paths emitted |
|--------|---------------|
| M, A, D, T | single path |
| R (rename) | old path + new path |
| C (copy) | old path + new path |

Filenames with spaces are handled safely via NUL-delimited parsing.

### Classification rules

`scripts/ci/classify_changes.py` owns path classification.

- `services/core/**` and `data/**` require the core lane.
- `apps/web/**` requires the web lane.
- `pnpm-lock.yaml`-only changes require the web lane (`web_required = true` and `dependency_changed = true`) because the root pnpm lockfile governs web package installations.
- `infra/gcp/**` requires the infrastructure regression lane.
- `.github/workflows/**`, `.github/actions/**`, `scripts/ci/**`, `infra/github/**`, and shared repository/toolchain configuration are cross-cutting and require all relevant lanes.
- documentation-only changes may skip core/web/infra, but `CI Policy`, `Dependency Review`, `Dependency Security`, and `PR Quality Gate` still produce real checks.
- unknown non-documentation paths (such as `Dockerfile`, `new-root-config.toml`, `.github/dependabot.yml`, or unrecognized configuration) fail closed by conservatively requiring all executable lanes (`core`, `web`, `infra`, and `shared`), setting `conservative_fallback = true`.
- an empty diff fails safe by requiring every lane.

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

`uv lock --check` and `uv sync --frozen` prevent manifest/lock drift. The architecture checker (`scripts/ci/check_architecture.py`) enforces the Clean Architecture dependency rule from `docs/CLEAN_ARCHITECTURE.md`. It resolves both absolute and relative `ImportFrom` statements (including `node.level`, `node.module`, aliases, and package resolution via `importlib.util.resolve_name`) into their effective targets:
- `domain` cannot depend on `application`, `interfaces`, `infrastructure`, `bootstrap`, or vendor SDKs (rejecting absolute imports such as `from ngabo import infrastructure` as well as relative imports such as `from ..infrastructure import repository` and `from .. import infrastructure`).
- `application` cannot depend on `interfaces`, `infrastructure`, `bootstrap`, or vendor SDKs.

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

Local equivalents for this lane are `pnpm infra:typecheck` (runs `cd services/core && uv run mypy ../../infra/gcp` — the exact hosted lane mypy command) and `pnpm infra:test` (`cd services/core && uv run pytest ../../infra/gcp/tests`).

Any changed `infra/gcp/*.py` file is additionally passed to Ruff. Normal PR CI never runs `gcloud`, `infra:apply`, `identity:apply`, or any cloud mutation.

## Dependency security and native Dependency Review

Every PR runs dual defense-in-depth dependency validation:

1. **Native GitHub Dependency Review**:
   - Job: `Dependency Review`
   - Action: `actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294` (v5.0.0 pinned to full 40-hex commit SHA)
   - Configuration: `fail-on-severity: high`
   - Investigation diagnosis: The initial unsupported result (`Dependency review is not supported on this repository`) was resolved by enabling repository `vulnerability-alerts` on this public repository, which opened the REST API `dependency-graph/compare` and SBOM export endpoints.
2. **Package-Manager Audit Defense-in-Depth**:
   - Job: `Dependency Security`
   - Commands:
     ```bash
     cd services/core
     uv --preview audit --frozen
     cd ../..
     pnpm audit --audit-level=high
     ```

The Python audit fails on any vulnerability reported by uv, which is stricter than the Issue #88 high-severity floor. The pnpm audit fails on high/critical findings. Both jobs are strictly required in the final `PR Quality Gate` aggregator.

## Action pinning and caches

Every external Action reference must be a full 40-hex commit SHA. `scripts/ci/check_workflow_pins.py` enforces that contract across committed workflow files.

Caches may contain package-manager download/store data only. Frozen installs and lock checks still run on cache hits. `node_modules`, `.venv`, build output, credentials, and prior test results are not trusted as validation substitutes.

## CI control-plane changes

`.github/workflows/ci-control-plane.yml` uses `pull_request_target` **only for GitHub metadata inspection**. It never checks out or executes PR-head code.

### Rename-aware file enumeration

The control-plane workflow extracts **both** `filename` and `previous_filename` from the PR files API for each file object. This prevents a rename such as `.github/workflows/wif-auth-proof.yml → docs/wif-auth-proof.yml` from evading protected-path detection.

The `scripts/ci/collect_pr_files.py` utility provides testable `extract_all_paths()` and `classify_pr_files()` functions with offline unit tests covering:
- protected source → unprotected destination
- unprotected source → protected destination
- protected → protected rename
- ordinary unprotected modification

### Protected paths

Protected control-plane paths include workflows, local composite actions under `.github/actions/**` (both `action.yml`/`action.yaml` manifests and any helper scripts they invoke), `scripts/ci/**`, `infra/github/**`, package/toolchain manifests, and web lint/type/test/build configuration. A protected change must be authored by the repository owner and the PR body must contain an approval bound to the exact current head SHA:

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
pnpm infra:typecheck
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

The contract pins GitHub's server-populated pull-request parameters explicitly (`require_extra_approval_for_unattributed_changes: true` — the secure GitHub default requiring an extra approval for commits with no attributed author; `required_reviewers: []`). Validation compares the complete governed parameter dictionaries, the observed rule types, and the rule count verbatim: any undeclared enforcement parameter, unknown rule type, duplicated rule, or type-less rule is reported as drift (`UPDATE` / post-apply failure) — the validator fails closed rather than silently accepting undeclared policy.

Ruleset activation is a staged post-merge acceptance step. A green implementation PR alone does not close Issue #88.

## Machine-readable evidence

`infra/github/ci_quality_evidence.py` generates `ci-quality-evidence.json` with strict PR/run attribution validation. The output separates:

- **`observed`**: values fetched from the GitHub API (PR head SHA, run ID, run conclusion, job conclusions, duration)
- **`contract`**: repository policy assertions verified by tests (classifier contracts, architecture checker, merge governance, `privacy_review_status = EXTERNAL_REVIEW_REQUIRED`)
- **`historical_negative_proofs`**: explicit run IDs/descriptions for recorded bypass proofs (architecture import bypass and high-severity dependency). A hosted rename-bypass negative proof is deliberately `NOT_RECORDED` and is not claimed as recorded evidence.

Before emitting evidence, the generator validates:
- PR exists and number matches
- Run ID matches, name is `PR Quality`, event is `pull_request`
- Run status is `completed` with conclusion `success`
- Run head SHA matches PR head SHA
- Run is associated with the requested PR
- All required jobs (`Changed Paths`, `CI Policy`, `Dependency Review`, `Dependency Security`, `PR Quality Gate`) completed successfully
- Optional lanes (`Core Quality`, `Web Quality`, `Infrastructure Regression`) are `success` or `skipped`

Fails closed with `EVIDENCE_VALIDATION_FAILED:` on any mismatch.

## Post-merge acceptance procedure

The correct staged acceptance after merge must include enforcement proof:

1. Merge PR into develop with expected-head protection
2. Synchronize develop
3. Verify both workflows exist on the default branch
4. Apply `Ngabo Required PR Quality` ruleset
5. Validate exact ruleset state
6. Create a temporary harmless probe branch + PR into develop
7. Verify GitHub reports both required checks: `PR Quality Gate` and `CI Control Plane`
8. Verify the PR is not merge-eligible while required checks are pending/failing
9. Verify a normal harmless/docs-only PR receives real success for both required checks
10. Perform a bounded protected-control-plane metadata proof
11. Verify required checks originate from GitHub Actions integration ID 15368
12. Close probe PR without merging
13. Inspect active ruleset again
14. Only then update Issue #88 acceptance criteria and close

Issue #88 must not be closed merely because the ruleset API returns expected JSON. Enforcement behavior — not configuration-only proof — is required.
