# ── Stage 1: builder ───────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# System deps needed to compile some Python packages (e.g. asyncpg, reportlab)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime ───────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy application source
COPY app ./app

# Writable dirs for uploads/exports
RUN mkdir -p /tmp/uploads /tmp/exports && chown -R appuser:appgroup /tmp

USER appuser

EXPOSE 8000

# Single worker — avoids startup race conditions with DB table creation.
# Scale horizontally via docker-compose replicas instead of --workers.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
