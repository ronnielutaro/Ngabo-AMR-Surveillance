# Ngabo Container Artifacts (Issue #89)

**Status:** Issue #89 — Cloud Foundation 1A.5: Build and publish immutable core and web containers
**Boundary:** artifacts only. Issue #90 owns the first Cloud Run deployment and the minimal HTTP adapters.

## Primary invariant

> The artifact deployed later is the tested artifact: promotion reuses an immutable digest and never rebuilds different bytes from the same release decision.

## Images

| Image | Dockerfile | Build context | Base image (immutable digest) | Runtime user | Ports |
| --- | --- | --- | --- | --- | --- |
| `ngabo-core` | `services/core/Dockerfile` | `services/core` | `python:3.11.16-slim@sha256:1042b61448fef4ba92d16a8c7eb4996d027568ce64792a7877fd88511e0af7c6` | `ngabo` (uid 10001) | none (framework-free; HTTP adapter deferred to #90) |
| `ngabo-web` | `apps/web/Dockerfile` | repository root | `node:24-slim@sha256:ba849c60be29959425b8734d57b8b4b7d56f98edd9504c9af091d5281095a71e` | `ngabo` (uid 10001) | `8080` (`PORT`/`HOSTNAME` configurable) |

- The core image installs the production wheel (built with pinned `uv==0.12.4`) into a virtualenv; no source tree is bind-mounted at runtime. Default process is the real `ngabo-health` diagnostic (one-shot, exits 0 on success). `ngabo-certify-hero` remains invocable explicitly. No long-running process is fabricated.
- The web image builds Next.js with `output: "standalone"` from a frozen pnpm install (`pnpm@11.22.0`) and runs the standalone server non-root.
- OCI metadata (`org.opencontainers.image.source/revision/title/version` + `ngabo.service`/`ngabo.revision`) binds each artifact to its source commit. Build args `SOURCE_REVISION`, `SOURCE_URL`, `APP_VERSION` are passed by CI.

## Local commands

```bash
pnpm container:core:build        # docker build -t ngabo-core:<sha> services/core
pnpm container:web:build         # docker build -t ngabo-web:<sha> (root context)
pnpm container:core:test         # docker run ngabo-core:<sha> ngabo-health
pnpm container:web:smoke         # run + curl + stop ngabo-web:<sha> on 127.0.0.1:18080
pnpm container:inspect           # docker inspect both images
pnpm container:scan              # trivy (HIGH,CRITICAL, exit 1 on findings)
```

## Artifact Registry contract

- Repository `ngabo-artifacts`, region `us-central1`, project `ngabo-amr-2026`.
- Packages: `ngabo-core`, `ngabo-web`.
- Tags are navigation only: `<full-sha>` and `sha-<full-sha>`. **Never `latest`.** The authoritative identity is `sha256:<64-hex>`.
- IAM: `ngabo-deployer` holds repository-scoped `roles/artifactregistry.writer` on `ngabo-artifacts` only (no project-wide writer/admin/editor/owner). The obsolete #87-era reader is revoked on convergence.

## Trusted publish flow (post-merge certification)

1. #89 PR merges code and workflows.
2. develop synchronized; desired IAM applied/validated from merged code (`pnpm infra:identity:plan` / `validate` / `apply` by the maintainer).
3. `Publish Containers` workflow is manually dispatched against develop.
4. It authenticates keylessly via WIF (`environment: dev`, `ngabo-deployer`), builds, verifies, scans, and pushes the exact image objects (single buildx build; pushed digest == locally loaded/scan digest).
5. Evidence JSON (`infra/github/container_evidence.py`) binds repository → commit → workflow run → URI → tag → digest → scan summary → runtime user → base digest → reproducibility observation; uploaded as an artifact.

## Vulnerability scanning

Pinned `aquasecurity/trivy-action` (v0.36.0) in both the PR lane and the publish workflow. Gate: fails on ALL HIGH/CRITICAL findings except the explicit per-CVE exceptions listed with justification in `.trivyignore` (base-image packages with no published upstream fix, and packages bundled inside the Next.js server closure whose versions are pinned by the upstream release). No broad gate relaxation. Concise sanitized scan tables are uploaded as evidence; no raw databases are stored.

## Reproducibility

Both Dockerfiles build from locked inputs (frozen lockfiles, pinned uv/pnpm, digest-pinned base images) and are built with `--provenance=false` plus `BUILDKIT_SOURCE_DATE_EPOCH` derived from the source commit timestamp, yielding **byte-identical image digests** for the same commit (verified locally for both images). The provenance/attestation index is intentionally disabled because its embedded build timestamps would break digest determinism; the machine-readable evidence document binds commit → workflow → digest instead.

## Secrets hygiene

Build contexts exclude `.git`, `.env`/secret variants, credentials (`gha-creds-*`, service-account/JSON keys), caches, test outputs, and scratch content via `.dockerignore` (root for web context, `services/core/.dockerignore` for core). No source-control credentials, no `.env`, no user-managed keys in images.
