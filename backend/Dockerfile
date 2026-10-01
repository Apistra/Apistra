ARG PYTHON_BASE=python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
FROM ${PYTHON_BASE} AS build
WORKDIR /build
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/app/.venv
RUN pip install --no-cache-dir uv==0.12.20
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY backend/src ./src
RUN uv sync --locked --no-dev --no-editable

FROM ${PYTHON_BASE} AS runtime
ARG APISTRA_VERSION=0.0.0-dev
ARG APISTRA_COMMIT=unknown
LABEL org.opencontainers.image.title="Apistra backend" org.opencontainers.image.version="${APISTRA_VERSION}" org.opencontainers.image.revision="${APISTRA_COMMIT}" org.opencontainers.image.source="https://github.com/Apistra/Apistra"
ENV PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 APISTRA_VERSION=${APISTRA_VERSION} APISTRA_COMMIT=${APISTRA_COMMIT}
WORKDIR /app
COPY --from=build --chown=10001:10001 /app/.venv .venv
USER 10001:10001

FROM runtime AS api
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "apistra.entrypoints.api.main:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]

FROM runtime AS worker
CMD ["python", "-m", "apistra.entrypoints.worker.main"]
