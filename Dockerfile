# SIGMAX Trading Bot Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install package
RUN pip install -e .

# Create logs directory
RUN mkdir -p /app/logs

# Expose Prometheus metrics ports
EXPOSE 9090-9099

# Default command (can be overridden)
CMD ["python", "tools/runner.py", "--profile=a"]
