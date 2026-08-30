# syntax=docker/dockerfile:1.7

# ngabo-web production container (Issue #89).
#
# Build context is the repository root (the app is part of the pnpm
# workspace; the frozen lockfile and workspace manifest live at the root).
# The image runs the production Next.js standalone server as a non-root
# user with a configurable PORT for later Cloud Run use (Issue #90).
#
# Base image pinned by immutable digest (node:24.19.0-slim, linux/amd64
# manifest-list digest). No mutable tags.

# ---------------------------------------------------------------------------
# Build stage: frozen pnpm install (hoisted layout per pnpm-workspace.yaml)
# + production Next.js build with self-contained standalone output.
# ---------------------------------------------------------------------------
FROM node:24-slim@sha256:ba849c60be29959425b8734d57b8b4b7d56f98edd9504c9af091d5281095a71e AS builder

ARG SOURCE_REVISION=unknown
ARG SOURCE_URL=https://github.com/ronnielutaro/Ngabo-AMR-Surveillance
ARG APP_VERSION=0.1.0
ARG SOURCE_DATE_EPOCH=0

ENV NGABO_SOURCE_REVISION=${SOURCE_REVISION}

WORKDIR /app

# Workspace manifests, linker config, and frozen lockfile first for layer
# caching.
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json apps/web/
RUN npm install --global pnpm@11.22.0 \
    && pnpm install --frozen-lockfile

COPY apps/web apps/web
COPY scripts/ci/normalize_next_build.cjs scripts/ci/
RUN pnpm --filter ngabo-web build

# Next.js 16 embeds per-build random preview keys (previewModeId and the
# signing/encryption keys) in prerender-manifest.json and
# server-reference-manifest.{js,json}; its cache is disabled inside
# containers, so fresh builds of the same commit would differ. Derive the
# keys deterministically from the source revision so the build output is
# byte-identical for the same commit.
RUN node scripts/ci/normalize_next_build.cjs /app/apps/web/.next \
    "${NGABO_SOURCE_REVISION}"

# Normalize file mtimes of the build output (copied into the runtime stage)
# to SOURCE_DATE_EPOCH for layer determinism.
RUN find /app/apps/web/.next -exec touch -c -h -d "@${SOURCE_DATE_EPOCH}" {} +

# ---------------------------------------------------------------------------
# Runtime stage: standalone Next.js server, non-root, minimal files.
# ---------------------------------------------------------------------------
FROM node:24-slim@sha256:ba849c60be29959425b8734d57b8b4b7d56f98edd9504c9af091d5281095a71e

ARG SOURCE_REVISION=unknown
ARG SOURCE_URL=https://github.com/ronnielutaro/Ngabo-AMR-Surveillance
ARG APP_VERSION=0.1.0
ARG SOURCE_DATE_EPOCH=0

ENV SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}

# OCI metadata binding the artifact to its source (Issue #89 contract).
LABEL org.opencontainers.image.source="${SOURCE_URL}" \
      org.opencontainers.image.revision="${SOURCE_REVISION}" \
      org.opencontainers.image.title="ngabo-web" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.description="Ngabo AMR surveillance web console (Next.js standalone)" \
      ngabo.service="ngabo-web" \
      ngabo.revision="${SOURCE_REVISION}"

ENV NODE_ENV=production \
    PORT=8080 \
    HOSTNAME=0.0.0.0

# Drop the base image's bundled npm CLI (unused at runtime; its bundled
# brace-expansion carried a published advisory). NO apt-get update/upgrade:
# resolving the current Debian repositories at build time would make the
# image irreproducible; OS-package findings are recorded as explicit
# .trivyignore exceptions against the digest-pinned base image.
# The removal bumps parent directory mtimes; normalize the whole /usr/local
# tree (files and directories) to SOURCE_DATE_EPOCH for layer determinism.
RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx \
    && find /usr/local -exec touch -c -h -d "@${SOURCE_DATE_EPOCH}" {} +

# Non-root runtime identity (fixed uid for reproducibility). useradd bumps
# the mtimes of the account files AND their parent directories; normalize
# /etc and /home (files and directories) for layer determinism. The build
# container's /etc/hosts and /etc/resolv.conf are read-only bind mounts and
# are excluded.
RUN useradd --system --uid 10001 --create-home --shell /usr/sbin/nologin ngabo \
    && find /etc /home \( -path /etc/hosts -o -path /etc/resolv.conf \) -prune -o \
        -exec touch -c -h -d "@${SOURCE_DATE_EPOCH}" {} +

WORKDIR /app
COPY --from=builder --chown=ngabo:ngabo /app/apps/web/.next/standalone ./
COPY --from=builder --chown=ngabo:ngabo /app/apps/web/.next/static ./apps/web/.next/static
# Normalize the mtimes of the copied runtime files and created directories
# (/app and below) for layer determinism.
RUN find /app -exec touch -c -h -d "@${SOURCE_DATE_EPOCH}" {} +
# The app currently ships no static `public/` directory; add
# `COPY --from=builder /app/apps/web/public ./apps/web/public` when one exists.

USER ngabo
EXPOSE 8080

CMD ["node", "apps/web/server.js"]
