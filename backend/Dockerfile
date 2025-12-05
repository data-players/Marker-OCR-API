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

# Copy requirements and install as appuser
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

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

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"] 