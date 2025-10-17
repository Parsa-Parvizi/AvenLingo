# =============================================================================
# English Teacher Academy - Production-Ready Dockerfile
# Optimized with Multi-Stage Build, Layer Caching & Minimal Size
# =============================================================================

# =============================================================================
# Stage 1: Base Image with System Dependencies
# =============================================================================
FROM python:3.11-slim-bookworm AS base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies (minimal set)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client and development libraries
    postgresql-client \
    libpq-dev \
    # Build essentials for Python packages
    gcc \
    # Health check utility
    curl \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

# =============================================================================
# Stage 2: Python Dependencies Builder
# =============================================================================
FROM base AS builder

# Create virtual environment for better isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only requirements first (for better layer caching)
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies in virtual environment
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    # Remove unnecessary files to reduce size
    find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete && \
    find /opt/venv -type f -name "*.pyo" -delete

# =============================================================================
# Stage 3: Final Production Image
# =============================================================================
FROM base AS production

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd -r -g 1000 django && \
    useradd -r -g django -u 1000 -m -s /bin/bash django

# Set work directory
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/staticfiles /app/media /app/logs /app/temp && \
    chown -R django:django /app && \
    chmod 755 /app /app/staticfiles /app/media /app/logs /app/temp

# Copy entrypoint script
COPY --chown=django:django setup/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy application code (this layer changes most frequently, so it's last)
COPY --chown=django:django . /app/

# Security: Remove sensitive files and optimize
RUN find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /app -type f -name "*.pyc" -delete && \
    find /app -type f -name "*.pyo" -delete && \
    rm -f /app/.env* /app/secret_key.txt /app/.secret_key 2>/dev/null || true && \
    chmod -R go-rwx /app/logs

# Switch to non-root user
USER django

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ --max-time 10 --silent --show-error || exit 1

# Expose port
EXPOSE 8000

# Labels for metadata
LABEL maintainer="EnglishTeacher Academy" \
      version="3.0" \
      description="Django application - Production Ready" \
      environment="production"

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command (can be overridden)
CMD ["gunicorn", "EnglishTeacher.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]

# =============================================================================
# Stage 4: Development Image (Optional)
# =============================================================================
FROM production AS development

USER root

# Install development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    django-debug-toolbar \
    ipython \
    pytest \
    pytest-django

USER django

# Override CMD for development
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
