# syntax=docker/dockerfile:1.7

# ngabo-core production container (Issue #89).
#
# The core is currently framework-free with NO HTTP adapter (Issue #90 owns
# the minimal deployment adapter). This image therefore executes the real
# production diagnostic entrypoint `ngabo-health` as its default process and
# exposes no network port. `ngabo-certify-hero` remains invocable explicitly.
#
# Base image pinned by immutable digest (python:3.11.16-slim, linux/amd64
# manifest-list digest). No mutable tags.

# ---------------------------------------------------------------------------
# Build stage: produce the production wheel with pinned uv, then install it
# into a self-contained virtualenv.
# ---------------------------------------------------------------------------
FROM python:3.11.16-slim@sha256:1042b61448fef4ba92d16a8c7eb4996d027568ce64792a7877fd88511e0af7c6 AS builder

ARG SOURCE_REVISION=unknown
ARG SOURCE_URL=https://github.com/ronnielutaro/Ngabo-AMR-Surveillance
ARG APP_VERSION=0.1.0

# Pin the exact uv version used by the repository CI (uv 0.12.4).
RUN python -m pip install --no-cache-dir uv==0.12.4

WORKDIR /src
COPY pyproject.toml uv.lock README.md ./
COPY ngabo ./ngabo
RUN uv build --wheel --out-dir /dist

# Deterministic runtime virtualenv containing only the production wheel.
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir /dist/ngabo_core-*.whl

# ---------------------------------------------------------------------------
# Runtime stage: minimal non-root image with only the installed package.
# ---------------------------------------------------------------------------
FROM python:3.11.16-slim@sha256:1042b61448fef4ba92d16a8c7eb4996d027568ce64792a7877fd88511e0af7c6

ARG SOURCE_REVISION=unknown
ARG SOURCE_URL=https://github.com/ronnielutaro/Ngabo-AMR-Surveillance
ARG APP_VERSION=0.1.0

# OCI metadata binding the artifact to its source (Issue #89 contract).
LABEL org.opencontainers.image.source="${SOURCE_URL}" \
      org.opencontainers.image.revision="${SOURCE_REVISION}" \
      org.opencontainers.image.title="ngabo-core" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.description="Ngabo AMR surveillance core runtime (framework-free; HTTP adapter deferred to Issue #90)" \
      ngabo.service="ngabo-core" \
      ngabo.revision="${SOURCE_REVISION}"

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    NGABO_SERVICE_VERSION="${APP_VERSION}" \
    NGABO_SOURCE_REVISION="${SOURCE_REVISION}"

# Non-root runtime identity (fixed uid for reproducibility).
RUN useradd --system --uid 10001 --create-home --shell /usr/sbin/nologin ngabo

COPY --from=builder /opt/venv /opt/venv

USER ngabo
WORKDIR /home/ngabo

# No EXPOSE: the core exposes no network service in Issue #89.
# Default process: production health diagnostic (one-shot, exits 0 on success).
CMD ["ngabo-health"]
