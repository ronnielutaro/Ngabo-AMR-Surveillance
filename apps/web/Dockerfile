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

WORKDIR /app

# Workspace manifests, linker config, and frozen lockfile first for layer
# caching.
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json apps/web/
RUN npm install --global pnpm@11.22.0 \
    && pnpm install --frozen-lockfile

COPY apps/web apps/web
RUN pnpm --filter ngabo-web build

# ---------------------------------------------------------------------------
# Runtime stage: standalone Next.js server, non-root, minimal files.
# ---------------------------------------------------------------------------
FROM node:24-slim@sha256:ba849c60be29959425b8734d57b8b4b7d56f98edd9504c9af091d5281095a71e

ARG SOURCE_REVISION=unknown
ARG SOURCE_URL=https://github.com/ronnielutaro/Ngabo-AMR-Surveillance
ARG APP_VERSION=0.1.0

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

# Apply available Debian security patches (e.g. util-linux, openssl) and drop
# the base image's bundled npm CLI (unused at runtime; its bundled
# brace-expansion carried a published advisory). Remaining CVEs without
# upstream fixes are recorded in .trivyignore with justification.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx

# Non-root runtime identity (fixed uid for reproducibility).
RUN useradd --system --uid 10001 --create-home --shell /usr/sbin/nologin ngabo

WORKDIR /app
COPY --from=builder --chown=ngabo:ngabo /app/apps/web/.next/standalone ./
COPY --from=builder --chown=ngabo:ngabo /app/apps/web/.next/static ./apps/web/.next/static
# The app currently ships no static `public/` directory; add
# `COPY --from=builder /app/apps/web/public ./apps/web/public` when one exists.

USER ngabo
EXPOSE 8080

CMD ["node", "apps/web/server.js"]
