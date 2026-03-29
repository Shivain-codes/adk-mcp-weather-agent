# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install Node.js for npx (required to run MCP filesystem server)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs npm curl && \
    rm -rf /var/lib/apt/lists/*

# Pre-install the MCP filesystem server so npx doesn't download at runtime
RUN npm install -g @modelcontextprotocol/server-filesystem

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY agent.py .
COPY main.py .
COPY weather_data/ ./weather_data/

# Cloud Run port
ENV PORT=8080
EXPOSE 8080

# Non-root user
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

CMD ["python", "main.py"]
