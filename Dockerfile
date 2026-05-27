# syntax=docker/dockerfile:1.7

# ---------- Frontend build ----------
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---------- Backend / runtime ----------
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 1000 hivemind \
    && useradd -u 1000 -g hivemind -m -s /bin/bash hivemind

COPY backend/pyproject.toml ./backend/pyproject.toml
COPY README.md ./README.md
COPY backend/src ./backend/src
COPY backend/alembic.ini ./backend/alembic.ini
COPY backend/alembic ./backend/alembic

RUN pip install ./backend

COPY --from=frontend /app/frontend/dist /app/backend/src/hivemind/static

USER hivemind
WORKDIR /app/backend
ENV PYTHONPATH=/app/backend/src \
    HIVEMIND_HOST=0.0.0.0 \
    HIVEMIND_PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8080/api/health || exit 1

CMD ["uvicorn", "hivemind.main:app", "--host", "0.0.0.0", "--port", "8080"]
