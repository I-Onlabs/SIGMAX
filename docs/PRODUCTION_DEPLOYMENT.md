# SIGMAX Production Deployment Guide

Complete guide for deploying SIGMAX v1.0.0 in production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Infrastructure Setup](#infrastructure-setup)
- [Security Configuration](#security-configuration)
- [Database Setup](#database-setup)
- [Application Deployment](#application-deployment)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum:**
- **CPU**: 4 cores
- **RAM**: 16GB
- **Disk**: 100GB SSD
- **Network**: 100 Mbps

**Recommended:**
- **CPU**: 8+ cores
- **RAM**: 32GB+
- **Disk**: 500GB NVMe SSD
- **Network**: 1 Gbps

### Software Requirements

```bash
# Operating System
- Ubuntu 22.04 LTS (recommended)
- macOS 13+ (development)
- RHEL/CentOS 8+ (enterprise)

# Runtime
- Python 3.11+
- Node.js 20+
- Docker 24+
- PostgreSQL 16+
- Redis 7+
```

---

## Infrastructure Setup

### 1. Server Provisioning

#### AWS EC2 Example

```bash
# Launch t3.xlarge (4 vCPU, 16 GB RAM)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.xlarge \
  --key-name your-key-pair \
  --security-groups sigmax-sg \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100,"VolumeType":"gp3"}}]'
```

#### GCP Compute Engine

```bash
gcloud compute instances create sigmax-production \
  --machine-type=n2-standard-4 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=100GB \
  --boot-disk-type=pd-ssd
```

### 2. Firewall Configuration

```bash
# Allow HTTPS only (API behind reverse proxy)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH (restrict to your IP)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Internal services (not exposed)
# PostgreSQL: 5432
# Redis: 6379
# NATS: 4222
# Prometheus: 9090
# Grafana: 3001
```

### 3. DNS Configuration

```bash
# Point your domain to the server
# A record: api.yourdomain.com → YOUR_SERVER_IP
# A record: app.yourdomain.com → YOUR_SERVER_IP
```

---

## Security Configuration

### 1. SSL/TLS Certificates

#### Using Let's Encrypt (Recommended)

```bash
# Install certbot
sudo snap install --classic certbot

# Obtain certificate
sudo certbot certonly --standalone \
  -d api.yourdomain.com \
  -d app.yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos

# Auto-renewal
sudo systemctl enable certbot.timer
```

### 2. Environment Variables

```bash
# Create .env file
cd /home/user/SIGMAX
cp .env.example .env

# Generate secure passwords
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export REDIS_PASSWORD=$(openssl rand -base64 32)
export GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32)
export SIGMAX_API_KEY=$(openssl rand -hex 32)

# Edit .env with generated values
nano .env
```

**Production .env Template:**

```bash
# ============================================================================
# Production Configuration
# ============================================================================

ENVIRONMENT=production

# Trading
TRADING_MODE=paper  # Start with paper trading!
TESTNET=true
RISK_PROFILE=conservative

# LLM
OPENAI_API_KEY=your-actual-key
OPENAI_MODEL=gpt-4

# Database (SET STRONG PASSWORDS!)
POSTGRES_PASSWORD=<generated-password>
POSTGRES_DB=sigmax
POSTGRES_USER=sigmax

REDIS_PASSWORD=<generated-password>

# API Security
SIGMAX_API_KEY=<generated-api-key>
CORS_ORIGINS=https://app.yourdomain.com
ALLOWED_HOSTS=api.yourdomain.com,app.yourdomain.com

# Monitoring
GRAFANA_ADMIN_PASSWORD=<generated-password>
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# Telegram
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Secrets Management (Optional but recommended)
USE_VAULT=true
VAULT_ADDR=https://vault.yourdomain.com
VAULT_TOKEN=<vault-token>
```

### 3. Secrets Management with Vault

```bash
# Install HashiCorp Vault
wget https://releases.hashicorp.com/vault/1.15.0/vault_1.15.0_linux_amd64.zip
unzip vault_1.15.0_linux_amd64.zip
sudo mv vault /usr/local/bin/

# Initialize Vault
vault server -dev &
export VAULT_ADDR='http://127.0.0.1:8200'

# Store secrets
vault kv put secret/sigmax/OPENAI_API_KEY value="sk-..."
vault kv put secret/sigmax/POSTGRES_PASSWORD value="..."
```

---

## Database Setup

### 1. PostgreSQL Installation

```bash
# Install PostgreSQL 16
sudo apt update
sudo apt install postgresql-16 postgresql-contrib-16

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE USER sigmax WITH PASSWORD '<strong-password>';
CREATE DATABASE sigmax OWNER sigmax;
GRANT ALL PRIVILEGES ON DATABASE sigmax TO sigmax;
\q
EOF
```

### 2. Redis Installation

```bash
# Install Redis 7
sudo apt install redis-server

# Configure password
sudo nano /etc/redis/redis.conf
# Add: requirepass <strong-password>

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### 3. Database Migrations

```bash
cd /home/user/SIGMAX

# Run migrations
python tools/init_database.py

# Verify
psql -U sigmax -d sigmax -c "\dt"
```

---

## Application Deployment

### Method 1: Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/I-Onlabs/SIGMAX.git
cd SIGMAX

# Set environment variables
cp .env.example .env
nano .env  # Configure production values

# Build and start services
docker-compose up -d

# Verify
docker-compose ps
docker-compose logs -f
```

### Method 2: Manual Deployment

#### Backend Setup

```bash
# Create virtual environment
cd /home/user/SIGMAX/core
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run application
python main.py --mode paper --risk-profile conservative
```

#### API Setup

```bash
cd /home/user/SIGMAX/ui/api

# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn (production WSGI server)
gunicorn main:app \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

#### Frontend Setup

```bash
cd /home/user/SIGMAX/ui/web

# Install dependencies
npm ci

# Build for production
npm run build

# Serve with nginx (see below)
```

### 3. Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/sigmax
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}

# Frontend
server {
    listen 443 ssl http2;
    server_name app.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/app.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.yourdomain.com/privkey.pem;

    root /home/user/SIGMAX/ui/web/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location /assets {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/sigmax /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Systemd Service

```ini
# /etc/systemd/system/sigmax-api.service
[Unit]
Description=SIGMAX API Server
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=sigmax
Group=sigmax
WorkingDirectory=/home/user/SIGMAX/ui/api
Environment="PATH=/home/user/SIGMAX/ui/api/venv/bin"
ExecStart=/home/user/SIGMAX/ui/api/venv/bin/gunicorn main:app \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 120

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable sigmax-api
sudo systemctl start sigmax-api
sudo systemctl status sigmax-api
```

---

## Monitoring & Logging

### 1. Application Logs

```bash
# View logs
docker-compose logs -f sigmax-api

# Or with systemd
journalctl -u sigmax-api -f

# Log rotation
sudo nano /etc/logrotate.d/sigmax
```

### 2. Prometheus Metrics

Access: `http://localhost:9090`

Key metrics to monitor:
- `api_request_duration_seconds`
- `api_request_total`
- `database_connections_active`
- `redis_connected_clients`
- `trading_position_size`
- `trading_pnl_total`

### 3. Grafana Dashboards

Access: `https://grafana.yourdomain.com`

Import dashboards:
- `infra/grafana/dashboards/trading_performance.json`
- `infra/grafana/dashboards/system_health.json`

### 4. Alerting

Configure alerts for:
- API error rate > 5%
- High CPU/memory usage
- Database connection failures
- Trading losses exceeding limits

---

## Backup & Recovery

### 1. Database Backups

```bash
# Automated daily backups
cat > /usr/local/bin/backup-sigmax.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups/sigmax
mkdir -p $BACKUP_DIR

# PostgreSQL backup
docker exec sigmax-postgres pg_dump -U sigmax sigmax | \
  gzip > $BACKUP_DIR/postgres_$DATE.sql.gz

# Redis backup
docker exec sigmax-redis redis-cli SAVE
docker cp sigmax-redis:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Rotate old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /usr/local/bin/backup-sigmax.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-sigmax.sh
```

### 2. Restore Procedure

```bash
# Restore PostgreSQL
gunzip < /backups/sigmax/postgres_20250115_020000.sql.gz | \
  docker exec -i sigmax-postgres psql -U sigmax sigmax

# Restore Redis
docker cp /backups/sigmax/redis_20250115_020000.rdb sigmax-redis:/data/dump.rdb
docker restart sigmax-redis
```

---

## Performance Tuning

### 1. PostgreSQL Optimization

```sql
-- /etc/postgresql/16/main/postgresql.conf
shared_buffers = 4GB              # 25% of RAM
effective_cache_size = 12GB       # 75% of RAM
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1            # For SSD
effective_io_concurrency = 200
work_mem = 52MB
min_wal_size = 1GB
max_wal_size = 4GB
max_connections = 200
```

### 2. Redis Optimization

```conf
# /etc/redis/redis.conf
maxmemory 8gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 3. Application Tuning

```bash
# In .env
POSTGRES_POOL_SIZE=20
POSTGRES_MAX_OVERFLOW=10
REDIS_MAX_CONNECTIONS=50
RATE_LIMIT_PER_MINUTE=100
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connections
psql -U sigmax -d sigmax -c "SELECT count(*) FROM pg_stat_activity;"

# Increase max_connections if needed
sudo nano /etc/postgresql/16/main/postgresql.conf
```

#### 2. High Memory Usage

```bash
# Check memory usage
free -h
docker stats

# Restart services
docker-compose restart
```

#### 3. API Timeout Errors

```bash
# Check API logs
docker-compose logs sigmax-api | tail -100

# Increase timeout in nginx
sudo nano /etc/nginx/sites-available/sigmax
# proxy_read_timeout 120s;
```

---

## Security Checklist

Before going live:

- [ ] Strong passwords set for all services
- [ ] SSL/TLS certificates installed and auto-renewing
- [ ] Firewall configured (only HTTPS exposed)
- [ ] API key authentication enabled
- [ ] Rate limiting configured
- [ ] CORS origins restricted to your domain
- [ ] Database backups automated
- [ ] Monitoring and alerting set up
- [ ] Log rotation configured
- [ ] Vault/secrets management enabled
- [ ] All TODO items resolved
- [ ] Security scan passed (Bandit, Safety, Trivy)
- [ ] Load testing completed

---

## Support

- **Documentation**: https://github.com/I-Onlabs/SIGMAX/tree/main/docs
- **Issues**: https://github.com/I-Onlabs/SIGMAX/issues
- **Security**: security@sigmax.dev

---

**Last Updated**: 2025-11-15
**Version**: 1.0.0
