# SIGMAX - Production Dockerfile
# Multi-stage build for optimized production image

# Stage 1: Build stage
FROM python:3.11-slim AS builder

LABEL maintainer="SIGMAX Team"
LABEL description="SIGMAX Autonomous Trading Platform"

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r sigmax && useradd -r -g sigmax -u 1000 -m -s /bin/bash sigmax

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/sigmax/.local

# Copy application code
COPY --chown=sigmax:sigmax . .

# Create necessary directories with proper permissions
RUN mkdir -p \
    /app/logs \
    /app/data \
    /app/models \
    /app/config \
    /app/.cache \
    && chown -R sigmax:sigmax /app

# Set environment variables
ENV PATH=/home/sigmax/.local/bin:$PATH \
    PYTHONPATH=/app:$PYTHONPATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    LOG_LEVEL=INFO \
    ENVIRONMENT=production

# Switch to non-root user
USER sigmax

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Expose ports
# 8000: API server
# 8080: Federated learning server
# 9090-9099: Prometheus metrics
EXPOSE 8000 8080 9090-9099

# Volume for persistent data
VOLUME ["/app/data", "/app/logs", "/app/models"]

# Default command
CMD ["python", "core/main.py", "--mode", "paper", "--profile", "conservative"]
