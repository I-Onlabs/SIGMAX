# SIGMAX Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Configuration](#configuration)
4. [Deployment Options](#deployment-options)
5. [Security Hardening](#security-hardening)
6. [Monitoring & Logging](#monitoring--logging)
7. [Backup & Recovery](#backup--recovery)
8. [Performance Tuning](#performance-tuning)

---

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB SSD
- Network: Stable internet connection

**Recommended:**
- CPU: 8+ cores
- RAM: 16GB+
- Storage: 100GB+ NVMe SSD
- Network: High-speed, low-latency connection

### Software Dependencies

```bash
# Operating System
- Linux (Ubuntu 22.04+ / Debian 12+ / RHEL 9+)
- macOS 12+
- Windows 11 with WSL2

# Required
- Python 3.11+
- Node.js 20+
- Docker 24+ & Docker Compose v2
- PostgreSQL 16+
- Redis 7+

# Optional
- Kubernetes 1.28+ (for production)
- Nginx/Traefik (reverse proxy)
- Prometheus & Grafana (monitoring)
```

---

## Installation Methods

### Method 1: Quick Start (Recommended for Testing)

```bash
# Clone repository
git clone https://github.com/yourusername/SIGMAX.git
cd SIGMAX

# Run one-click deployment
chmod +x deploy.sh
./deploy.sh

# Follow prompts to configure
```

### Method 2: Docker Compose (Recommended for Production)

```bash
# 1. Set up environment
cp .env.example .env
nano .env  # Configure your settings

# 2. Start infrastructure services
docker-compose up -d postgres redis nats

# 3. Wait for services to be ready
docker-compose ps

# 4. Start SIGMAX services
docker-compose up -d api web

# 5. Verify deployment
docker-compose ps
docker-compose logs -f
```

### Method 3: Kubernetes (Enterprise Production)

```bash
# 1. Create namespace
kubectl create namespace sigmax

# 2. Apply configurations
kubectl apply -f infra/k8s/configmap.yaml
kubectl apply -f infra/k8s/secrets.yaml

# 3. Deploy infrastructure
kubectl apply -f infra/k8s/postgres.yaml
kubectl apply -f infra/k8s/redis.yaml

# 4. Deploy SIGMAX
kubectl apply -f infra/k8s/deployment.yaml
kubectl apply -f infra/k8s/service.yaml

# 5. Verify deployment
kubectl get pods -n sigmax
kubectl logs -f -n sigmax deployment/sigmax-api
```

### Method 4: Manual Installation (Development)

```bash
# 1. Install Python dependencies
cd core
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Install Node.js dependencies
cd ../ui/web
npm install

# 3. Set up databases
createdb sigmax
redis-server

# 4. Configure environment
cp ../.env.example .env
# Edit .env with your settings

# 5. Run migrations (if applicable)
# cd core && alembic upgrade head

# 6. Start services
# Terminal 1: API
cd ui/api
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Web UI
cd ui/web
npm run dev

# Terminal 3: Core system
cd core
python main.py --mode paper
```

---

## Configuration

### Essential Environment Variables

```bash
# Trading Configuration
TOTAL_CAPITAL=50.0
MAX_POSITION_SIZE=15.0
MAX_DAILY_LOSS=10.0
TRADING_MODE=paper  # paper or live

# API Configuration
SIGMAX_API_KEY=your-secure-api-key-here  # Generate with: openssl rand -hex 32
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
ENVIRONMENT=production
ALLOWED_HOSTS=localhost,yourdomain.com

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sigmax
POSTGRES_USER=sigmax
POSTGRES_PASSWORD=secure-password-here

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# LLM Configuration (choose one)
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Local (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Exchange Configuration
EXCHANGE_NAME=binance
EXCHANGE_API_KEY=
EXCHANGE_SECRET_KEY=
EXCHANGE_SANDBOX=true

# Features
QUANTUM_ENABLED=true
FEATURE_ARBITRAGE=true
TELEGRAM_ENABLED=false
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/sigmax.log
```

### Security Best Practices

1. **Generate Strong API Key**
```bash
# Generate secure API key
openssl rand -hex 32

# Add to .env
echo "SIGMAX_API_KEY=$(openssl rand -hex 32)" >> .env
```

2. **Restrict CORS Origins**
```bash
# Only allow specific domains
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

3. **Enable HTTPS**
```bash
# Use reverse proxy (Nginx example)
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

4. **Database Security**
```bash
# Use strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Restrict network access
# In postgresql.conf:
listen_addresses = 'localhost'

# In pg_hba.conf:
host    sigmax    sigmax    127.0.0.1/32    scram-sha-256
```

---

## Deployment Options

### Local Development

```bash
# Start with auto-reload
cd core
python main.py --mode paper --risk-profile conservative

cd ui/api
uvicorn main:app --reload

cd ui/web
npm run dev
```

### Production - Single Server

```bash
# 1. Use systemd services
sudo cp infra/systemd/sigmax-core.service /etc/systemd/system/
sudo cp infra/systemd/sigmax-api.service /etc/systemd/system/
sudo systemctl daemon-reload

# 2. Start services
sudo systemctl enable sigmax-core sigmax-api
sudo systemctl start sigmax-core sigmax-api

# 3. Check status
sudo systemctl status sigmax-core
sudo journalctl -u sigmax-core -f
```

### Production - Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    restart: always
    environment:
      POSTGRES_DB: sigmax
      POSTGRES_USER: sigmax
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sigmax"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: .
      dockerfile: ui/api/Dockerfile
    restart: always
    ports:
      - "8000:8000"
    environment:
      - SIGMAX_API_KEY=${SIGMAX_API_KEY}
      - POSTGRES_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  web:
    build:
      context: ui/web
      dockerfile: Dockerfile
    restart: always
    ports:
      - "3000:80"
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:
```

### Production - Kubernetes

See `infra/k8s/` directory for complete Kubernetes manifests.

Key features:
- High availability with 3+ replicas
- Horizontal Pod Autoscaling (HPA)
- Persistent volumes for data
- Network policies for security
- Ingress with TLS
- Prometheus monitoring

```bash
# Deploy to production cluster
kubectl apply -k infra/k8s/overlays/production/
```

---

## Security Hardening

### 1. Network Security

```bash
# Firewall (UFW example)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Or with iptables
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -j DROP
```

### 2. Application Security

```bash
# Set file permissions
chmod 600 .env
chmod 700 deploy.sh
chmod 700 stop.sh

# Run as non-root user
sudo useradd -r -s /bin/false sigmax
sudo chown -R sigmax:sigmax /opt/sigmax
```

### 3. API Security Checklist

- [x] API key authentication enabled
- [x] Rate limiting configured
- [x] CORS properly restricted
- [x] HTTPS/TLS enforced
- [x] Request logging enabled
- [x] Input validation on all endpoints
- [x] SQL injection protection (use parameterized queries)
- [x] XSS protection headers
- [x] CSRF protection (if using cookies)

### 4. Secrets Management

**Option A: Environment Variables (Simple)**
```bash
# Use .env file (never commit to git)
echo ".env" >> .gitignore
```

**Option B: HashiCorp Vault (Advanced)**
```bash
# Store in Vault
vault kv put secret/sigmax \
    api_key=$SIGMAX_API_KEY \
    postgres_password=$POSTGRES_PASSWORD

# Retrieve in app
export SIGMAX_API_KEY=$(vault kv get -field=api_key secret/sigmax)
```

**Option C: Kubernetes Secrets**
```bash
kubectl create secret generic sigmax-secrets \
    --from-literal=api-key=$SIGMAX_API_KEY \
    --from-literal=postgres-password=$POSTGRES_PASSWORD
```

---

## Monitoring & Logging

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Readiness probe (Kubernetes)
curl http://localhost:8000/health/ready

# Liveness probe
curl http://localhost:8000/health/live

# Detailed metrics
curl http://localhost:8000/metrics
```

### Logging Setup

**1. Application Logs**
```python
# Logs are stored in:
logs/sigmax.log          # Main application log
logs/api.log             # API requests
reports/                 # Trading reports
```

**2. Centralized Logging (ELK Stack)**
```bash
# docker-compose with logging
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**3. Log Rotation**
```bash
# /etc/logrotate.d/sigmax
/opt/sigmax/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 sigmax sigmax
    sharedscripts
    postrotate
        systemctl reload sigmax-core
    endscript
}
```

### Metrics Collection

**Prometheus Configuration**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'sigmax-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

**Grafana Dashboards**
- Import dashboards from `infra/grafana/dashboards/`
- Monitor: request rates, error rates, latency, system resources

---

## Backup & Recovery

### Database Backup

```bash
# Automated daily backup script
#!/bin/bash
BACKUP_DIR="/backup/sigmax"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
pg_dump -U sigmax sigmax | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# Backup Redis
redis-cli --rdb "$BACKUP_DIR/redis_$DATE.rdb"

# Backup configs
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" .env docker-compose.yml

# Keep only last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 sync $BACKUP_DIR s3://my-backup-bucket/sigmax/
```

### Restore Procedure

```bash
# 1. Stop services
docker-compose down

# 2. Restore database
gunzip < backup.sql.gz | psql -U sigmax sigmax

# 3. Restore Redis
redis-cli --rdb dump.rdb

# 4. Restart services
docker-compose up -d
```

### Disaster Recovery Plan

1. **Data Loss Prevention**
   - Daily automated backups
   - Off-site backup storage (S3, etc.)
   - Database replication (master-slave)

2. **Recovery Time Objective (RTO): 1 hour**
   - Keep backup server ready
   - Automated restoration scripts
   - Regular disaster recovery drills

3. **Recovery Point Objective (RPO): 24 hours**
   - Daily backups retained for 30 days
   - Transaction logs for point-in-time recovery

---

## Performance Tuning

### Database Optimization

```sql
-- PostgreSQL tuning
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '10MB';
ALTER SYSTEM SET max_worker_processes = 8;
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers = 8;

-- Restart PostgreSQL
sudo systemctl restart postgresql
```

### Redis Configuration

```bash
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### Application Performance

```python
# Enable caching in .env
CACHE_ENABLED=true
CACHE_TTL=300  # 5 minutes

# Use connection pooling
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

### Scaling Strategies

**Vertical Scaling**
- Upgrade CPU/RAM
- Use faster storage (NVMe)
- Optimize database queries

**Horizontal Scaling**
- Multiple API instances behind load balancer
- Database read replicas
- Redis Cluster for distributed caching
- Kubernetes with HPA

---

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues and solutions.

## Next Steps

1. ✅ Complete installation
2. ✅ Configure environment
3. ✅ Test with paper trading
4. ✅ Set up monitoring
5. ✅ Configure backups
6. ⚠️ Gradually transition to live trading

## Support

- 📖 Documentation: [docs/](./docs/)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/SIGMAX/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/SIGMAX/discussions)
- 📧 Email: support@sigmax.ai (if applicable)

---

**Last Updated:** 2025-11-06
**Version:** 2.0.0
