# SIGMAX Deployment Guide

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- 8GB RAM minimum (128GB recommended for quantized models)
- Ubuntu 20.04+ or similar Linux distribution
- Network connectivity to exchanges

## Quick Start

### 1. Clone and Setup

```bash
git clone <repo-url>
cd SIGMAX

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Start Infrastructure

```bash
# Option A: Docker Compose (recommended for development)
docker-compose -f docker-compose.dev.yml up -d

# Option B: Production infrastructure only
make docker-up
```

### 3. Initialize Databases

```bash
# Install Python dependencies
pip install -r requirements.txt

# Initialize databases
python tools/init_database.py --profile=a

# Verify database setup
psql postgresql://sigmax:sigmax@localhost:5432/sigmax -c "SELECT * FROM symbols;"
```

### 4. Configure Exchange API Keys

Edit `.env` file:

```bash
# Binance
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here

# Coinbase
COINBASE_API_KEY=your_key_here
COINBASE_API_SECRET=your_secret_here
```

### 5. Run Trading System

```bash
# Run all services
python tools/runner.py --profile=a

# Or use Make
make profile-a
```

## Production Deployment

### VPS Deployment (Hetzner/AWS/DigitalOcean)

#### 1. Server Setup

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3.11 python3.11-venv python3-pip docker.io docker-compose git

# Create application user
sudo useradd -m -s /bin/bash sigmax
sudo usermod -aG docker sigmax
```

#### 2. Application Setup

```bash
# Switch to sigmax user
sudo su - sigmax

# Clone repository
git clone <repo-url> sigmax
cd sigmax

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

#### 3. Configure Systemd Service

Create `/etc/systemd/system/sigmax.service`:

```ini
[Unit]
Description=SIGMAX Trading Bot
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=sigmax
WorkingDirectory=/home/sigmax/sigmax
Environment="PATH=/home/sigmax/sigmax/venv/bin"
ExecStartPre=/usr/bin/docker-compose up -d
ExecStart=/home/sigmax/sigmax/venv/bin/python tools/runner.py --profile=a
ExecStop=/usr/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable sigmax
sudo systemctl start sigmax
sudo systemctl status sigmax
```

#### 4. Monitoring

```bash
# View logs
sudo journalctl -u sigmax -f

# Access Grafana
open http://your-server-ip:3000
# Default credentials: admin/admin

# Access Prometheus
open http://your-server-ip:9090
```

### Kubernetes Deployment

#### 1. Create Namespace

```bash
kubectl create namespace sigmax
```

#### 2. Deploy Infrastructure

```yaml
# kubernetes/infrastructure.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sigmax-config
  namespace: sigmax
data:
  profile: "a"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sigmax-postgres
  namespace: sigmax
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:16-alpine
        env:
        - name: POSTGRES_DB
          value: "sigmax"
        - name: POSTGRES_USER
          value: "sigmax"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: sigmax-secrets
              key: postgres-password
        ports:
        - containerPort: 5432
```

#### 3. Deploy Trading Bot

```yaml
# kubernetes/sigmax.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sigmax
  namespace: sigmax
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sigmax
  template:
    metadata:
      labels:
        app: sigmax
    spec:
      containers:
      - name: sigmax
        image: sigmax:latest
        env:
        - name: SIGMAX_PROFILE
          valueFrom:
            configMapKeyRef:
              name: sigmax-config
              key: profile
        - name: BINANCE_API_KEY
          valueFrom:
            secretKeyRef:
              name: sigmax-secrets
              key: binance-api-key
        ports:
        - containerPort: 9090
          name: metrics
```

## Configuration

### Profile A (Simple - Recommended for Getting Started)

```yaml
# profiles/profile_a.yaml
profile: "a"
environment: "development"

# Enable paper trading
exchanges:
  binance:
    testnet: true

# Conservative risk limits
risk:
  max_position_usd: 1000.0
  max_order_usd: 100.0
```

### Profile B (Performance - For Production)

```yaml
# profiles/profile_b.yaml
profile: "b"
environment: "production"

exchanges:
  binance:
    testnet: false

risk:
  max_position_usd: 50000.0
  max_order_usd: 5000.0

# Enable performance features
decision:
  enable_ml: true
  enable_llm: false  # Optional
```

## Security

### API Key Management

**Never commit API keys to git!**

Use one of:

1. **Environment Variables** (Recommended)
   ```bash
   export BINANCE_API_KEY="your_key"
   export BINANCE_API_SECRET="your_secret"
   ```

2. **SOPS Encryption**
   ```bash
   # Install SOPS
   brew install sops  # or apt-get install sops
   
   # Encrypt secrets
   sops -e secrets.yaml > secrets.enc.yaml
   ```

3. **OS Keyring**
   ```python
   import keyring
   keyring.set_password("sigmax", "binance_api_key", "your_key")
   ```

### Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 3000/tcp  # Grafana
sudo ufw allow 9090/tcp  # Prometheus
sudo ufw enable
```

## Backup & Recovery

### Database Backups

```bash
# Postgres backup
pg_dump postgresql://sigmax:sigmax@localhost:5432/sigmax > backup_$(date +%Y%m%d).sql

# ClickHouse backup
clickhouse-client --query="SELECT * FROM sigmax.ticks FORMAT Native" > backup_ticks_$(date +%Y%m%d).native

# Automated daily backups
cat > /etc/cron.daily/sigmax-backup << 'CRON'
#!/bin/bash
pg_dump postgresql://sigmax:sigmax@localhost:5432/sigmax | gzip > /backups/sigmax_$(date +%Y%m%d).sql.gz
CRON
chmod +x /etc/cron.daily/sigmax-backup
```

### Recovery

```bash
# Restore Postgres
psql postgresql://sigmax:sigmax@localhost:5432/sigmax < backup_20250101.sql

# Restore ClickHouse
cat backup_ticks_20250101.native | clickhouse-client --query="INSERT INTO sigmax.ticks FORMAT Native"
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs -f

# Check service status
systemctl status sigmax

# Check ports
netstat -tlnp | grep python
```

### Database Connection Issues

```bash
# Test Postgres
psql postgresql://sigmax:sigmax@localhost:5432/sigmax -c "SELECT 1;"

# Test ClickHouse
clickhouse-client --query="SELECT 1"
```

### Exchange Connection Issues

```bash
# Test CCXT connectivity
python -c "import ccxt; exchange = ccxt.binance(); print(exchange.fetch_ticker('BTC/USDT'))"
```

### High Latency

```bash
# Check Prometheus metrics
curl http://localhost:9090/metrics | grep latency

# Enable debug logging
export SIGMAX_LOG_LEVEL=DEBUG
```

## Monitoring & Alerts

### Grafana Dashboards

Access: `http://localhost:3000`

Default dashboards:
- System Overview
- Trading Metrics
- Latency Analysis
- Risk Metrics

### Prometheus Alerts

Configure AlertManager in `infra/prometheus/alertmanager.yml`:

```yaml
receivers:
  - name: 'email'
    email_configs:
      - to: 'alerts@example.com'
        from: 'sigmax@example.com'
```

## Performance Tuning

### For High-Frequency Trading

1. **Enable Profile B**
   ```bash
   python tools/runner.py --profile=b
   ```

2. **Optimize Network**
   ```bash
   # Increase network buffers
   sudo sysctl -w net.core.rmem_max=134217728
   sudo sysctl -w net.core.wmem_max=134217728
   ```

3. **CPU Pinning**
   ```bash
   # Pin services to specific cores
   taskset -c 0-3 python tools/runner.py --profile=b
   ```

## Support

- GitHub Issues: <repo-url>/issues
- Documentation: docs/
- Logs: ./logs/ or /var/log/sigmax/

## License

MIT License - See LICENSE file
