# =============================================================================
# English Teacher Academy - Development Dockerfile
# Optimized for Development with HTTP Only
# =============================================================================

# Use a more accessible base image
FROM python:3.9-slim as base

# Set environment variables for development
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r -g 1000 django && useradd -r -g django -u 1000 django

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --user --no-cache-dir -r requirements.txt

# Create app directories with proper permissions
RUN mkdir -p /app /app/staticfiles /app/media /app/logs /app/temp && \
    chown -R django:django /app && \
    chmod 755 /app && \
    chmod 755 /app/staticfiles && \
    chmod 755 /app/media && \
    chmod 755 /app/logs && \
    chmod 755 /app/temp

# Copy Python packages to user directory
RUN cp -r /root/.local /home/django/.local && \
    chown -R django:django /home/django/.local

# Copy application code
COPY --chown=django:django . .

# Copy entrypoint script and make it executable
COPY --chown=django:django entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Security: Remove sensitive files and set secure permissions
RUN find /app -name "*.pyc" -delete && \
    find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true && \
    # Remove any potential sensitive files
    rm -f /app/.env* /app/secret_key.txt /app/.secret_key 2>/dev/null || true && \
    # Set secure permissions
    chmod -R go-rwx /app/logs

# Switch to non-root user
USER django

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ --max-time 10 --silent --show-error || exit 1

# Expose port
EXPOSE 8000

# Labels
LABEL maintainer="EnglishTeacher Academy" \
      version="2.0" \
      description="Django application for development" \
      environment="development"

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command for development
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"] 