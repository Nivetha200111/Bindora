# Multi-stage Docker build for Bindora Backend
FROM python:3.10-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM base AS production

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash bindora && \
    chown -R bindora:bindora /app

USER bindora

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Development stage (for local development)
FROM base AS development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    isort \
    flake8

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash bindora && \
    chown -R bindora:bindora /app

USER bindora

# Expose port
EXPOSE 8000

# Start with reload for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
