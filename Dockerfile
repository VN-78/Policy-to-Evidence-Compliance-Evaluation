# =====================================================================
# Build Stage: Install dependencies with uv
# =====================================================================
FROM python:3.14-slim AS builder

# Install uv binary from official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation and copy link mode for optimal container caching
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copy dependency specifications
COPY pyproject.toml uv.lock* ./

# Install production dependencies into virtual environment
RUN uv sync --frozen --no-install-project --no-dev


# =====================================================================
# Production Runtime Stage
# =====================================================================
FROM python:3.14-slim

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Set environment variables for runtime
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Copy application source code
COPY app /app/app

# Expose default HTTP port (Render overrides with $PORT at runtime)
EXPOSE 8000

# Container healthcheck hitting the FastAPI /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:' + str(__import__('os').getenv('PORT', 8000)) + '/health').read()" || exit 1

# Start Uvicorn web server binding to dynamic $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
