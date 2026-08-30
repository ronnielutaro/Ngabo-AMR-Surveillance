# syntax=docker/dockerfile:1.7

# ngabo-core production container (Issues #89/#90).
#
# The core runs the FastAPI HTTP adapter serving typed /health, /ready,
# /version endpoints for Cloud Run. `ngabo-health` and
# `ngabo-certify-hero` remain invocable explicitly; the default process is
# the HTTP server on $PORT (8080).
#
# Base image pinned by immutable digest (python:3.11.16-slim, linux/amd64
# manifest-list digest). No mutable tags.
#
# Production Python dependencies are installed by `uv sync --locked` from
# the committed uv.lock. This is deliberate: installing the project wheel
# with plain pip would re-resolve FastAPI/Uvicorn ranges from PyPI and could
# produce different runtime bytes for the same source commit.

# ---------------------------------------------------------------------------
# Build stage: exact locked production environment, non-editable project.
# ---------------------------------------------------------------------------
FROM python:3.11.16-slim@sha256:1042b61448fef4ba92d16a8c7eb4996d027568ce64792a7877fd88511e0af7c6 AS builder

ARG SOURCE_REVISION=unknown
ARG SOURCE_URL=https://github.com/ronnielutaro/Ngabo-AMR-Surveillance
ARG APP_VERSION=0.1.0
ARG SOURCE_DATE_EPOCH=0

ENV SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH} \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# Exact uv version used by repository CI.
RUN python -m pip install --no-cache-dir uv==0.12.4

WORKDIR /src
COPY pyproject.toml uv.lock README.md ./
COPY ngabo ./ngabo

# --locked validates that pyproject.toml and uv.lock agree and installs the
# exact versions already selected in uv.lock. --no-dev keeps the runtime
# minimal; --no-editable makes the copied venv independent of /src.
RUN uv sync --locked --no-dev --no-editable --no-cache \
    && find /opt/venv -exec touch -c -h -d "@${SOURCE_DATE_EPOCH}" {} +

# ---------------------------------------------------------------------------
# Runtime stage: minimal non-root image with only the locked environment.
# ---------------------------------------------------------------------------
FROM python:3.11.16-slim@sha256:1042b61448fef4ba92d16a8c7eb4996d027568ce64792a7877fd88511e0af7c6

ARG SOURCE_REVISION=unknown
ARG SOURCE_URL=https://github.com/ronnielutaro/Ngabo-AMR-Surveillance
ARG APP_VERSION=0.1.0
ARG SOURCE_DATE_EPOCH=0

ENV SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}

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

# Keep the pinned base deterministic while hardening its system Python
# packaging tools. These are outside /opt/venv; uv-created project envs do
# not need pip/setuptools to run Ngabo.
RUN python -m pip install --no-cache-dir --upgrade \
        "wheel==0.46.2" "jaraco.context==6.1.0" "backports.tarfile==1.2.0" \
    && python -m pip uninstall -y setuptools \
    && find /usr/local/lib/python3.11 /usr/local/bin \
        -exec touch -c -h -d "@${SOURCE_DATE_EPOCH}" {} +

RUN useradd --system --uid 10001 --create-home --shell /usr/sbin/nologin ngabo \
    && find /etc /home \( -path /etc/hosts -o -path /etc/resolv.conf \) -prune -o \
        -exec touch -c -h -d "@${SOURCE_DATE_EPOCH}" {} +

COPY --from=builder /opt/venv /opt/venv
RUN find /opt -exec touch -c -h -d "@${SOURCE_DATE_EPOCH}" {} +

USER ngabo
WORKDIR /home/ngabo

EXPOSE 8080

CMD ["ngabo-http"]
