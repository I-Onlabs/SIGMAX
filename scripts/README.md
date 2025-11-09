# SIGMAX Automation Scripts

Production-ready automation scripts for SIGMAX deployment, monitoring, and operations.

---

## 📋 Scripts Overview

| Script | Purpose | Use Case |
|--------|---------|----------|
| `deploy.py` | Production deployment automation | Deploy SIGMAX to testnet/production |
| `health_check.py` | Comprehensive health monitoring | Manual or automated health checks |
| `emergency_shutdown.py` | Emergency trading shutdown | Critical incident response |
| `backup_restore.py` | Database backup and restoration | Data protection and recovery |
| `security_check.py` | Security vulnerability scanning | Dependency & code security audits |

---

## 🚀 deploy.py

**Purpose:** Automate SIGMAX deployment with pre-flight checks and validation.

### Usage

```bash
# Testnet deployment
python scripts/deploy.py --env testnet

# Production deployment (requires confirmation)
python scripts/deploy.py --env production

# Dry-run mode (no actual changes)
python scripts/deploy.py --env production --dry-run

# Skip pre-flight checks
python scripts/deploy.py --env testnet --skip-checks
```

### What It Does

1. **Pre-flight Checks**
   - Docker and Docker Compose installed
   - Python 3.11+ available
   - Environment file exists (.env.testnet or .env.production)
   - Docker Compose file present

2. **Deployment Steps**
   - Creates database backup (production only)
   - Starts infrastructure services (PostgreSQL, Redis, ClickHouse, Prometheus, Grafana)
   - Waits for services to be healthy
   - Runs database migrations
   - Starts SIGMAX trading services
   - Validates deployment success

3. **Post-Deployment**
   - Checks all containers running
   - Verifies Prometheus targets
   - Confirms Grafana accessibility
   - Prints next steps and documentation links

### Environment Variables

Requires `.env.{environment}` file with:
- Exchange API credentials
- Database URLs
- Trading configuration
- Safety parameters

See `docs/TESTNET_SETUP.md` for complete configuration.

---

## 🏥 health_check.py

**Purpose:** Comprehensive health monitoring for all SIGMAX components.

### Usage

```bash
# Basic health check
python scripts/health_check.py

# Detailed output with component details
python scripts/health_check.py --detailed

# JSON output (for monitoring systems)
python scripts/health_check.py --json

# Send alerts on failure
python scripts/health_check.py --alert-on-failure

# Scheduled execution (cron example)
*/5 * * * * /usr/bin/python3 /path/to/scripts/health_check.py --alert-on-failure
```

### Health Checks

1. **Docker Services**
   - sigmax-postgres, sigmax-redis, sigmax-clickhouse
   - sigmax-prometheus, sigmax-grafana, sigmax-alertmanager

2. **Databases**
   - PostgreSQL: Connection, database size, connection count
   - Redis: Ping, memory usage, connected clients
   - ClickHouse: Connection (optional)

3. **Monitoring**
   - Prometheus: Targets up/down count
   - Grafana: API health, version

4. **System Resources**
   - Disk space: Usage percentage, free space
   - Memory: Usage percentage, available RAM
   - CPU: Current usage percentage

### Exit Codes

- `0`: All checks healthy
- `1`: Degraded (warnings present)
- `2`: Unhealthy (critical issues)

### Output Formats

**Text Output:**
```
✓ docker_services    healthy     All 4 services running
✓ database_postgres  healthy     PostgreSQL connected
✓ database_redis     healthy     Redis connected
...
Overall Status: HEALTHY
```

**JSON Output:**
```json
{
  "timestamp": "2025-11-09T19:30:00Z",
  "overall_status": "healthy",
  "checks": [...]
}
```

---

## 🚨 emergency_shutdown.py

**Purpose:** Immediately stop trading in emergency situations.

### Usage

```bash
# Check current status (no shutdown)
python scripts/emergency_shutdown.py --status

# Graceful shutdown
python scripts/emergency_shutdown.py --graceful

# 🚨 PANIC SHUTDOWN (immediate stop)
python scripts/emergency_shutdown.py --panic
```

### Shutdown Modes

#### Graceful Mode

**When to use:** Planned shutdown, non-critical issues

**What it does:**
1. Cancels all open orders on exchange
2. Sets pause flag (`.emergency_pause`)
3. Stops SIGMAX processes gracefully (SIGTERM)
4. Leaves infrastructure running (databases, monitoring)
5. Creates incident report

**Downtime:** ~30 seconds

#### Panic Mode

**When to use:** Critical emergency, system malfunction, security breach

**What it does:**
1. Immediately cancels all open orders
2. Sets pause flag
3. Kills all SIGMAX processes (SIGKILL)
4. Stops all Docker services
5. Creates incident report

**Downtime:** ~10 seconds

**⚠️ WARNING:** Requires typing "PANIC" to confirm

### What Gets Stopped

**SIGMAX Services:**
- Market data ingestion
- Order book management
- Feature calculation
- Decision engine
- Risk management
- Order routing
- Execution engine
- Sentiment scanner

**Infrastructure (Panic mode only):**
- PostgreSQL
- Redis
- ClickHouse
- Prometheus
- Grafana
- AlertManager

### Recovery

After emergency shutdown:

1. **Investigate Root Cause**
   ```bash
   # Review incident report
   cat incidents/emergency_shutdown_YYYYMMDD_HHMMSS.log

   # Check system logs
   tail -1000 logs/sigmax_*.log

   # Review Grafana dashboards
   open http://localhost:3001
   ```

2. **Fix the Issue**
   - Address the problem that triggered shutdown
   - Update configuration if needed
   - Test the fix in isolated environment

3. **Resume Trading**
   ```bash
   # Remove pause flag
   rm .emergency_pause

   # Restart services
   python scripts/deploy.py --env <environment>

   # Monitor closely
   python scripts/health_check.py --detailed
   ```

### Incident Reports

Saved in `incidents/` directory:
```
incidents/
  emergency_shutdown_20251109_193000.log
  emergency_shutdown_20251110_020000.log
```

Each report contains:
- Shutdown type (PANIC or GRACEFUL)
- Timestamp
- Complete shutdown log
- Actions taken

---

## 💾 backup_restore.py

**Purpose:** Backup and restore SIGMAX databases.

### Usage

```bash
# Full backup of all databases
python scripts/backup_restore.py backup --all

# Backup individual databases
python scripts/backup_restore.py backup --postgres
python scripts/backup_restore.py backup --redis
python scripts/backup_restore.py backup --clickhouse

# Tagged backup (for organization)
python scripts/backup_restore.py backup --all --tag daily
python scripts/backup_restore.py backup --all --tag pre-deploy

# List available backups
python scripts/backup_restore.py list

# Restore from specific backup
python scripts/backup_restore.py restore --file backups/sigmax_backup_20251109_193000.tar.gz

# Restore from latest backup
python scripts/backup_restore.py restore --latest
```

### What Gets Backed Up

1. **PostgreSQL**
   - All trading data (orders, fills, positions)
   - User configuration
   - Historical records
   - Format: SQL dump

2. **Redis**
   - Cache data
   - Session state
   - Real-time data
   - Format: RDB snapshot

3. **ClickHouse** (Optional)
   - Time-series data
   - Analytics data
   - Audit logs
   - Format: SQL schema

### Backup Files

```
backups/
  sigmax_backup_20251109_093000.tar.gz          (Full backup)
  sigmax_backup_20251109_120000_daily.tar.gz   (Tagged backup)
  sigmax_backup_20251109_180000_pre-deploy.tar.gz
```

Each archive contains:
- `postgres_TIMESTAMP.sql` - PostgreSQL dump
- `redis_TIMESTAMP.rdb` - Redis database file
- `clickhouse_TIMESTAMP.sql` - ClickHouse schema

### Backup Schedule Recommendations

**Development/Testnet:**
- Daily backups
- Keep 7 days

**Production:**
- Hourly backups (during trading hours)
- Daily backups (overnight)
- Weekly backups (long-term retention)
- Keep hourly for 24h, daily for 30 days, weekly for 1 year

**Pre-Deployment:**
- Always backup before deploying
- Tag with version number

### Automated Backups (Cron)

```bash
# Daily backup at 2 AM
0 2 * * * /usr/bin/python3 /path/to/scripts/backup_restore.py backup --all --tag daily

# Hourly backup during trading hours (9 AM - 5 PM)
0 9-17 * * * /usr/bin/python3 /path/to/scripts/backup_restore.py backup --all --tag hourly

# Weekly backup on Sundays
0 3 * * 0 /usr/bin/python3 /path/to/scripts/backup_restore.py backup --all --tag weekly
```

### Restore Process

⚠️ **WARNING:** Restore will overwrite existing data!

**Before Restore:**
1. Stop all SIGMAX services
2. Backup current state (just in case)
3. Verify backup file integrity

**Restore Steps:**
```bash
# 1. Stop SIGMAX
python scripts/emergency_shutdown.py --graceful

# 2. Restore from backup
python scripts/backup_restore.py restore --file backups/sigmax_backup_YYYYMMDD_HHMMSS.tar.gz

# 3. Verify restore
python scripts/health_check.py --detailed

# 4. Restart SIGMAX
python scripts/deploy.py --env <environment>
```

---

## 🔒 security_check.py

**Purpose:** Comprehensive security vulnerability scanning and auditing.

### Usage

```bash
# Run all security checks
python scripts/security_check.py --all

# Check dependencies only
python scripts/security_check.py --dependencies

# Check for committed secrets
python scripts/security_check.py --secrets

# Code security scan
python scripts/security_check.py --code

# Configuration audit
python scripts/security_check.py --config

# File permissions check
python scripts/security_check.py --permissions
```

### Security Checks

1. **Dependency Vulnerabilities**
   - Uses `pip-audit` to scan for known CVEs
   - Checks all packages in requirements.txt
   - Reports vulnerable packages with fix versions
   - Categorizes by severity (critical/high/medium/low)

2. **Secrets Detection**
   - Scans code for accidentally committed secrets
   - Patterns: API keys, passwords, tokens, private keys
   - Checks .env files not in .gitignore
   - Validates environment variable usage

3. **Code Security**
   - Uses `bandit` to scan Python code
   - Detects common security anti-patterns
   - SQL injection vulnerabilities
   - XSS, command injection, insecure deserialization
   - Hardcoded credentials, weak crypto

4. **Configuration Audit**
   - Checks .env.example for secure defaults
   - Docker configuration review
   - Debug mode detection
   - Weak default credentials

5. **File Permissions**
   - Checks scripts for proper permissions
   - Validates sensitive file permissions (.env, .pem, .key)
   - World-writable file detection
   - Recommends chmod fixes

### Output

```
[INFO] Starting SIGMAX Security Check
[INFO] Checking dependencies for vulnerabilities...
[SUCCESS] ✓ No known vulnerabilities found in dependencies
[INFO] Checking for committed secrets...
[SUCCESS] ✓ No secrets found in code
[INFO] Checking code for security issues...
[WARNING] ✗ Found 2 code security issues
[INFO] Checking configurations...
[SUCCESS] ✓ No configuration issues found
[INFO] Checking file permissions...
[SUCCESS] ✓ File permissions look good

SECURITY CHECK SUMMARY
======================================================================

Total Findings: 2

  MEDIUM: 2

MEDIUM Severity Issues:
----------------------------------------------------------------------

1. Code security issue (B608)
   Description: core/agents/researcher.py:45 - Possible SQL injection
   Recommendation: Review code and apply security best practices

2. Using ':latest' tag in Dockerfile
   Description: Docker image uses ':latest' tag which is not reproducible
   Recommendation: Pin specific version tags for reproducibility

======================================================================
For detailed remediation steps, see: docs/SECURITY_ASSESSMENT.md
======================================================================
```

### Exit Codes

- `0`: No issues found (all clear)
- `1`: Medium severity issues found
- `2`: Critical or high severity issues found

### Integration

**CI/CD Pipeline:**
```yaml
# .github/workflows/security.yml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Security Check
        run: python scripts/security_check.py --all
```

**Pre-commit Hook:**
```bash
# .git/hooks/pre-commit
#!/bin/bash
python scripts/security_check.py --secrets --permissions
if [ $? -eq 2 ]; then
    echo "Critical security issues found. Commit aborted."
    exit 1
fi
```

**Scheduled Scan (Cron):**
```bash
# Weekly security scan
0 2 * * 0 cd /opt/sigmax && python scripts/security_check.py --all >> logs/security_scan.log
```

### Dependencies

Required tools (auto-installed if missing):
- `pip-audit` - Dependency vulnerability scanner
- `bandit` - Python code security scanner

Install manually:
```bash
pip install pip-audit bandit
```

### Remediation

See `docs/SECURITY_ASSESSMENT.md` for:
- Detailed vulnerability explanations
- Step-by-step remediation guides
- Security best practices
- Ongoing maintenance procedures

---

## 🔄 Common Workflows

### Daily Operations

```bash
# Morning: Health check before trading starts
python scripts/health_check.py --detailed

# Deploy or restart if needed
python scripts/deploy.py --env production

# Evening: Health check and backup
python scripts/health_check.py --detailed
python scripts/backup_restore.py backup --all --tag daily
```

### Pre-Deployment

```bash
# 1. Run security scan
python scripts/security_check.py --all

# 2. Create pre-deployment backup
python scripts/backup_restore.py backup --all --tag pre-deploy-v1.2.0

# 3. Run health check
python scripts/health_check.py --detailed

# 4. Deploy
python scripts/deploy.py --env production

# 5. Post-deployment validation
sleep 30
python scripts/health_check.py --detailed
```

### Incident Response

```bash
# 1. Emergency shutdown
python scripts/emergency_shutdown.py --panic  # or --graceful

# 2. Check status
python scripts/emergency_shutdown.py --status

# 3. Investigate
tail -1000 logs/sigmax_*.log
cat incidents/emergency_shutdown_*.log

# 4. Fix and restore if needed
python scripts/backup_restore.py restore --latest

# 5. Resume
rm .emergency_pause
python scripts/deploy.py --env production
```

---

## 📊 Monitoring Integration

All scripts can be integrated with monitoring systems:

### Prometheus

```python
# Example custom exporter
from prometheus_client import Gauge, generate_latest

health_status = Gauge('sigmax_health_status', 'Overall health status', ['component'])

# Run health check and expose metrics
runner = HealthCheckRunner()
await runner.run_all_checks()

for check in runner.checks:
    status_value = 1 if check.status == HealthStatus.HEALTHY else 0
    health_status.labels(component=check.name).set(status_value)
```

### Cron + Alerting

```bash
# Health check every 5 minutes with alerts
*/5 * * * * python scripts/health_check.py --alert-on-failure || \
  curl -X POST https://your-alerting-service.com/alert
```

### SystemD

```ini
# /etc/systemd/system/sigmax-health-check.service
[Unit]
Description=SIGMAX Health Check
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /opt/sigmax/scripts/health_check.py --alert-on-failure
User=sigmax
WorkingDirectory=/opt/sigmax

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/sigmax-health-check.timer
[Unit]
Description=Run SIGMAX health check every 5 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

---

## 🔒 Security Considerations

### Access Control

- Restrict script execution to authorized users only
- Use proper file permissions (chmod 750)
- Store credentials securely (environment variables, secrets vault)

### Backup Security

- Encrypt backup files before storing
- Store backups in secure location (not in git repository)
- Use separate credentials for backup access
- Implement backup retention policy

### Emergency Shutdown

- Require confirmation for panic mode
- Log all shutdown events
- Create incident reports automatically
- Notify relevant team members

---

## 📚 Additional Resources

- **Operational Runbook:** `../docs/OPERATIONAL_RUNBOOK.md`
- **Monitoring Setup:** `../docs/MONITORING_SETUP.md`
- **Testnet Configuration:** `../docs/TESTNET_SETUP.md`
- **Codebase Audit Summary:** `../CODEBASE_AUDIT_SESSION_SUMMARY.md`

---

## 🤝 Contributing

When adding new scripts:

1. Follow existing naming convention
2. Include comprehensive docstrings
3. Add error handling and logging
4. Support `--help` flag
5. Update this README
6. Test thoroughly in testnet
7. Make executable: `chmod +x script_name.py`

---

**Last Updated:** November 9, 2025
**Version:** 1.0
**Maintained By:** SIGMAX Engineering Team
