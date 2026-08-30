# syntax=docker/dockerfile:1.7

# ngabo-core production container (Issue #89).
#
# The core runs the FastAPI HTTP adapter (Issue #90) serving the typed
# /health, /ready, /version endpoints for Cloud Run. `ngabo-health`
# (one-shot diagnostic) and `ngabo-certify-hero` remain invocable
# explicitly; the default process is the HTTP server on $PORT (8080).
#
# Base image pinned by immutable digest (python:3.11.16-slim, linux/amd64
# manifest-list digest). No mutable tags.
#
# Reproducibility: the build is driven by SOURCE_DATE_EPOCH (declared here so
# BuildKit's frontend consumes it for OCI created/history metadata). File
# mtimes written by pip/useradd/COPY are normalized to that epoch with touch
# so two builds of the same commit produce byte-identical layers.

# ---------------------------------------------------------------------------
# Build stage: produce the production wheel with pinned uv, then install it
# into a self-contained virtualenv.
# ---------------------------------------------------------------------------
FROM python:3.11.16-slim@sha256:1042b61448fef4ba92d16a8c7eb4996d027568ce64792a7877fd88511e0af7c6 AS builder

ARG SOURCE_REVISION=unknown
ARG SOURCE_URL=https://github.com/ronnielutaro/Ngabo-AMR-Surveillance
ARG APP_VERSION=0.1.0
ARG SOURCE_DATE_EPOCH=0

ENV SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}

# Pin the exact uv version used by the repository CI (uv 0.12.4).
RUN python -m pip install --no-cache-dir uv==0.12.4

WORKDIR /src
COPY pyproject.toml uv.lock README.md ./
COPY ngabo ./ngabo
RUN uv build --wheel --out-dir /dist

# Deterministic runtime virtualenv containing only the production wheel.
# The venv inherits ensurepip's pip-bundled packages; upgrade the two with
# published security fixes and drop setuptools (which vendors an outdated
# wheel) so the scan gate is clean for actionable findings.
# File mtimes are normalized to SOURCE_DATE_EPOCH for layer determinism.
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir /dist/ngabo_core-*.whl \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade \
        "wheel==0.46.2" "jaraco.context==6.1.0" "backports.tarfile==1.2.0" \
    && /opt/venv/bin/pip uninstall -y setuptools \
    && find /opt/venv -exec touch -c -h -d "@${SOURCE_DATE_EPOCH}" {} +

# ---------------------------------------------------------------------------
# Runtime stage: minimal non-root image with only the installed package.
# ---------------------------------------------------------------------------
FROM python:3.11.16-slim@sha256:1042b61448fef4ba92d16a8c7eb4996d027568ce64792a7877fd88511e0af7c6

ARG SOURCE_REVISION=unknown
ARG SOURCE_URL=https://github.com/ronnielutaro/Ngabo-AMR-Surveillance
ARG APP_VERSION=0.1.0
ARG SOURCE_DATE_EPOCH=0

ENV SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}

# OCI metadata binding the artifact to its source (Issue #89 contract).
LABEL org.opencontainers.image.source="${SOURCE_URL}" \
      org.opencontainers.image.revision="${SOURCE_REVISION}" \
      org.opencontainers.image.title="ngabo-core" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.description="Ngabo AMR surveillance core runtime (FastAPI HTTP adapter, Issue #90)" \
      ngabo.service="ngabo-core" \
      ngabo.revision="${SOURCE_REVISION}"

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    NGABO_SERVICE_VERSION="${APP_VERSION}" \
    NGABO_SOURCE_REVISION="${SOURCE_REVISION}"

# NO apt-get update/upgrade: resolving the current Debian repositories at
# build time would make the image irreproducible. The base image is pinned by
# immutable digest; OS-package findings (with or without upstream fixes) are
# recorded as explicit .trivyignore exceptions.
# The base image's system pip bundles wheel/jaraco.context with published
# fixes; upgrade them with exact pins so the scan gate is clean for
# actionable findings. pip writes site-packages, compiled bytecode, and
# scripts; normalize the mtimes of the whole affected trees (files and
# directories) to SOURCE_DATE_EPOCH for layer determinism.
RUN python -m pip install --no-cache-dir --upgrade \
        "wheel==0.46.2" "jaraco.context==6.1.0" "backports.tarfile==1.2.0" \
    && python -m pip uninstall -y setuptools \
    && find /usr/local/lib/python3.11 /usr/local/bin \
        -exec touch -c -h -d "@${SOURCE_DATE_EPOCH}" {} +

# Non-root runtime identity (fixed uid for reproducibility). useradd bumps
# the mtimes of the account files AND their parent directories; normalize
# /etc and /home (files and directories) for layer determinism. The build
# container's /etc/hosts and /etc/resolv.conf are read-only bind mounts and
# are excluded.
RUN useradd --system --uid 10001 --create-home --shell /usr/sbin/nologin ngabo \
    && find /etc /home \( -path /etc/hosts -o -path /etc/resolv.conf \) -prune -o \
        -exec touch -c -h -d "@${SOURCE_DATE_EPOCH}" {} +

COPY --from=builder /opt/venv /opt/venv
# COPY creates /opt; normalize the whole venv tree including /opt itself.
RUN find /opt -exec touch -c -h -d "@${SOURCE_DATE_EPOCH}" {} +

USER ngabo
WORKDIR /home/ngabo

# Cloud Run port convention (Issue #90): the FastAPI adapter runs under
# uvicorn on $PORT (default 8080). EXPOSE is informational only — Cloud Run
# always routes to $PORT.
EXPOSE 8080

# Default process: FastAPI HTTP adapter (typed health/ready/version).
CMD ["ngabo-http"]
