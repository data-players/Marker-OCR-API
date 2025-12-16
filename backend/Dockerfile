# Production build
FROM python:3.11-slim as production

# Install all dependencies (build + runtime)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgssapi-krb5-2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user early
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

# Switch to appuser for everything
USER appuser

# Set working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p uploads outputs logs

# Install dependencies in order (three-level hierarchy):
# LEVEL 3: Install model dependencies FIRST (heavy ML models, rarely change)
# This layer will be cached separately from other dependencies
# Using BuildKit cache mount to improve cache hit rate for pip installs
COPY --chown=appuser:appuser requirements-models.txt .
RUN --mount=type=cache,target=/home/appuser/.cache/pip \
    pip install --no-cache-dir --user -r requirements-models.txt

# LEVEL 1: Install minimal dependencies SECOND (base dependencies for all environments)
COPY --chown=appuser:appuser requirements-minimal.txt .
RUN --mount=type=cache,target=/home/appuser/.cache/pip \
    pip install --no-cache-dir --user -r requirements-minimal.txt

# LEVEL 2: Install additional dev/prod dependencies LAST (supplements minimal)
# Docker will reuse cached layers if only this changes
COPY --chown=appuser:appuser requirements-base.txt .
RUN --mount=type=cache,target=/home/appuser/.cache/pip \
    pip install --no-cache-dir --user -r requirements-base.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Set PATH to include user's local bin and PYTHONPATH
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/ || exit 1

# Expose port
EXPOSE 8000

# Run the application with HTTP/2 support via Hypercorn
# Note: SSE works perfectly on HTTP/1.1, but HTTP/2 provides better performance
CMD ["hypercorn", "app.main:app", "--bind", "0.0.0.0:8000", "--workers", "1", "--log-level", "info"] 