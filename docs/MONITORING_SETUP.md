# SIGMAX Production Monitoring Setup Guide

**Version:** 1.0
**Last Updated:** November 9, 2025
**Status:** Production Ready

---

## 📊 Overview

This guide covers the complete monitoring infrastructure for SIGMAX, including:
- **Prometheus** - Metrics collection and alerting
- **Grafana** - Dashboard visualization
- **AlertManager** - Alert routing and notifications
- **Dashboards** - 5 comprehensive dashboards for different aspects
- **Alerts** - 30+ alert rules across 9 categories

---

## 🚀 Quick Start

### 1. Start Monitoring Stack

```bash
# Start Prometheus, Grafana, and AlertManager
cd /home/user/SIGMAX
docker-compose up -d prometheus grafana alertmanager

# Verify services are running
docker-compose ps | grep -E 'prometheus|grafana|alertmanager'

# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

### 2. Access Dashboards

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| **Grafana** | http://localhost:3001 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **AlertManager** | http://localhost:9093 | - |

### 3. Import Dashboards

Dashboards are auto-provisioned from `/infra/prometheus/grafana-dashboards/`:
- ✅ System Health Dashboard
- ✅ Trading Metrics Dashboard
- ✅ ML & RL Metrics Dashboard (NEW)
- ✅ Sentiment & Research Dashboard (NEW)
- ✅ Safety & Risk Controls Dashboard (NEW)

---

## 📈 Dashboard Overview

### 1. System Health Dashboard
**Purpose:** Infrastructure monitoring
**Refresh:** 10s
**Time Range:** Last 30 minutes

**Key Panels:**
- Service status (all microservices)
- CPU & Memory usage
- Network I/O
- Disk usage
- Database connections

**Use Cases:**
- Monitor infrastructure health
- Detect resource exhaustion
- Identify network issues
- Track database performance

**Critical Thresholds:**
- CPU > 80% → Warning
- Memory > 90% → Critical
- Disk > 85% → Warning

---

### 2. Trading Metrics Dashboard
**Purpose:** Trading activity monitoring
**Refresh:** 5s
**Time Range:** Last 1 hour

**Key Panels:**
- Orders per second
- Fill rate
- Realized P&L
- Current positions
- Risk rejections
- Latency metrics

**Use Cases:**
- Monitor trading performance
- Track P&L in real-time
- Identify order issues
- Measure execution quality

**Critical Thresholds:**
- Fill rate < 70% → Warning
- Daily P&L < -$10 → Critical (auto-pause)
- Rejection rate > 20% → Warning

---

### 3. ML & RL Metrics Dashboard (NEW)
**Purpose:** Reinforcement Learning monitoring
**Refresh:** 30s
**Time Range:** Last 6 hours

**Key Panels:**
- RL model status (initialized/not ready)
- Training timesteps & episodes
- Training reward per episode
- Prediction rate (predictions/sec)
- Action distribution (buy/sell/hold)
- Prediction latency (p50/p95/p99)
- Model load errors
- Trading environment state

**Use Cases:**
- Verify RL model is operational
- Monitor training progress
- Track prediction performance
- Debug model issues
- Analyze action patterns

**Critical Thresholds:**
- Model not initialized > 5min → Warning
- Prediction latency p99 > 1s → Warning
- Model load errors > 0.1/sec → Critical
- Predictions stopped > 3min → Warning

**Example Queries:**
```promql
# RL prediction rate
rate(sigmax_rl_predictions_total[1m])

# Action distribution
rate(sigmax_rl_actions_total[5m])

# Prediction latency p99
histogram_quantile(0.99, rate(sigmax_rl_prediction_duration_seconds_bucket[5m]))
```

---

### 4. Sentiment & Research Dashboard (NEW)
**Purpose:** News & social sentiment monitoring
**Refresh:** 1m
**Time Range:** Last 12 hours

**Key Panels:**
- News sentiment score (-1 to +1)
- Social media sentiment
- Articles processed count
- RSS feed health status
- Research API latency (CryptoPanic, Reddit, CoinGecko, Fear&Greed)
- API errors and success rates
- On-chain whale activity
- Fear & Greed Index
- Sentiment data freshness

**Use Cases:**
- Track market sentiment
- Monitor external API health
- Detect sentiment shifts
- Validate data freshness
- Debug API integration issues

**Critical Thresholds:**
- News sentiment < -0.7 → Warning (extreme negative)
- Social sentiment < -0.7 → Warning
- API error rate > 30% → Warning
- API latency p95 > 10s → Warning
- RSS feed failures > 15min → Warning
- Data staleness > 600s → Warning
- Fear & Greed < 20 → Info (extreme fear)

**Example Queries:**
```promql
# News sentiment by symbol
sigmax_news_sentiment_score

# Research API health
rate(sigmax_research_api_requests_total{status="success"}[5m]) /
rate(sigmax_research_api_requests_total[5m])

# Sentiment data age
time() - sigmax_sentiment_last_update_timestamp
```

---

### 5. Safety & Risk Controls Dashboard (NEW)
**Purpose:** Safety mechanism monitoring
**Refresh:** 10s
**Time Range:** Last 3 hours

**Key Panels:**
- System pause status (ACTIVE/PAUSED)
- Last pause reason
- Auto-pause trigger count by type (24h)
- Consecutive losses tracker
- Daily loss amount
- Position size vs limit
- API error rate (per minute)
- Safety violations by type (pie chart)
- Risk check rejections
- Circuit breaker status
- Slippage violations

**Use Cases:**
- Monitor safety mechanisms
- Track auto-pause triggers
- Prevent catastrophic losses
- Validate risk controls
- Incident response

**Critical Thresholds:**
- System paused → Critical (immediate investigation)
- Consecutive losses >= 2 → Warning (approaching limit of 3)
- Daily loss < -$8 → Warning (approaching -$10 limit)
- Daily loss < -$10 → Critical (should be auto-paused)
- Auto-pauses > 3/hour → Warning (system unstable)
- Position > 85% of limit → Warning
- API errors > 5/min → Warning (burst detection)
- Circuit breaker open → Critical
- Slippage violations > 0.5/sec → Warning

**Auto-Pause Reasons:**
1. **Consecutive Losses** - 3+ losing trades in a row
2. **Daily Loss Limit** - Total daily loss exceeds -$10
3. **Position Limit** - Position size exceeds configured limit
4. **API Error Burst** - >5 API errors per minute
5. **Sentiment Drop** - Sharp negative sentiment change
6. **Manual Override** - Human intervention

**Example Queries:**
```promql
# System pause status
sigmax_safety_paused

# Consecutive losses
sigmax_consecutive_losses

# Daily loss tracking
sigmax_daily_loss_usd

# Auto-pause triggers (24h)
increase(sigmax_safety_pause_count_total[24h])
```

---

## 🚨 Alert Rules

### Alert Categories

1. **sigmax_latency** (2 rules)
   - Tick-to-trade latency high
   - Stage latency spikes

2. **sigmax_queue** (2 rules)
   - Queue depth high/critical

3. **sigmax_errors** (2 rules)
   - High error rate
   - Risk blocks spike

4. **sigmax_trading** (3 rules)
   - Order rejection rate high
   - Position size near limit
   - Unrealized P&L drop

5. **sigmax_infrastructure** (2 rules)
   - Service down
   - Database connection issues

6. **sigmax_time_sync** (1 rule)
   - PTP offset too high

7. **sigmax_rl_module** (4 rules - NEW)
   - RL model not initialized
   - RL prediction latency high
   - RL model load errors
   - RL predictions stopped

8. **sigmax_sentiment_research** (7 rules - NEW)
   - News sentiment extremely negative
   - Social sentiment extremely negative
   - Research API high error rate
   - Research API timeout spike
   - RSS feed fetch failed
   - Sentiment data stale
   - Fear & Greed extreme fear

9. **sigmax_safety_mechanisms** (10 rules - NEW)
   - System auto-paused ⚠️
   - Consecutive losses high
   - Daily loss approaching limit
   - Daily loss limit exceeded ⚠️
   - Auto-pause triggers frequent
   - Position approaching limit
   - API error burst
   - Circuit breaker opened ⚠️
   - Slippage violations frequent
   - Risk rejections spike

**Total:** 33 alert rules

### Alert Severity Levels

| Severity | Meaning | Response Time | Examples |
|----------|---------|---------------|----------|
| **Critical** | Immediate action required | < 5 minutes | System paused, service down, circuit breaker open |
| **Warning** | Action needed soon | < 30 minutes | High latency, approaching limits, API errors |
| **Info** | Informational only | Best effort | Market sentiment shifts |

### Alert Configuration

**File:** `/infra/prometheus/alerts.yml`

**AlertManager Configuration:** `/infra/prometheus/alertmanager.yml`

**Routing:**
- Critical alerts → `critical` receiver (webhook + future: email, Slack, PagerDuty)
- Warning alerts → `warning` receiver (webhook)
- Default → `default` receiver (webhook)

**Inhibition Rules:**
- Critical alerts suppress related warning alerts

---

## 🔧 Configuration

### Prometheus Configuration

**File:** `/infra/prometheus/prometheus.yml`

**Scrape Interval:** 5 seconds
**Evaluation Interval:** 5 seconds
**Retention:** 30 days

**Scrape Targets:**
- Prometheus itself (port 9090)
- SIGMAX microservices (ports 9091-9098):
  - ingest_cex (9091)
  - book_shard (9092)
  - features (9093)
  - decision (9094)
  - risk (9095)
  - router (9096)
  - exec_cex (9097)
  - obs (9098)
- PostgreSQL (5432)
- ClickHouse (8123)
- Redis (6379)

### Grafana Configuration

**File:** `/infra/prometheus/grafana-datasources.yml`

**Data Sources:**
- Prometheus (http://prometheus:9090)

**Dashboard Provisioning:**
- Auto-import from `/infra/prometheus/grafana-dashboards/*.json`

**Plugins:**
- grafana-clock-panel
- grafana-piechart-panel

---

## 📝 Metrics Reference

### Core Trading Metrics

```promql
# Orders
sigmax_orders_total{status="sent|filled|rejected"}
sigmax_orders_rejected_total

# Fills
sigmax_fills_total
rate(sigmax_fills_total[1m]) / rate(sigmax_orders_total{status="sent"}[1m])  # Fill rate

# P&L
sigmax_pnl_realized  # Realized P&L
sigmax_unrealized_pnl_usd  # Unrealized P&L
sigmax_daily_loss_usd  # Daily loss tracker

# Positions
sigmax_position_qty  # Position quantity
sigmax_position_size  # Position size (USD)
sigmax_position_limit  # Position limit

# Risk
sigmax_risk_checks_total{result="pass|reject"}
sigmax_risk_blocks_total
sigmax_risk_rejections_total
```

### RL Module Metrics (NEW)

```promql
# Model Status
sigmax_rl_model_initialized  # 0 or 1
sigmax_rl_model_load_errors_total

# Training
sigmax_rl_training_timesteps_total
sigmax_rl_training_episodes_total
sigmax_rl_training_reward  # Last episode reward

# Predictions
sigmax_rl_predictions_total
sigmax_rl_actions_total{action="buy|sell|hold"}
sigmax_rl_prediction_duration_seconds  # Histogram

# Environment
sigmax_rl_env_price
sigmax_rl_env_position
sigmax_rl_env_pnl
```

### Sentiment & Research Metrics (NEW)

```promql
# Sentiment Scores
sigmax_news_sentiment_score  # -1 to +1
sigmax_social_sentiment_score  # -1 to +1
sigmax_fear_greed_index  # 0-100

# Data Processing
sigmax_news_articles_processed_total
sigmax_rss_feed_fetch_success  # 0 or 1
sigmax_sentiment_last_update_timestamp

# API Health
sigmax_research_api_requests_total{api="cryptopanic|reddit|coingecko|feargreed", status="success|error"}
sigmax_research_api_errors_total
sigmax_research_api_duration_seconds  # Histogram

# On-Chain
sigmax_onchain_whale_activity  # 0=bearish, 1=neutral, 2=bullish
```

### Safety Metrics (NEW)

```promql
# Pause Status
sigmax_safety_paused  # 0 or 1
sigmax_safety_pause_reason  # Enum
sigmax_safety_pause_count_total{reason="consecutive_losses|daily_loss_limit|..."}

# Loss Tracking
sigmax_consecutive_losses  # Current streak
sigmax_daily_loss_usd  # Cumulative daily loss

# Risk Controls
sigmax_circuit_breaker_open  # 0 or 1
sigmax_slippage_violations_total
sigmax_safety_violations_total{violation_type="..."}

# Errors
sigmax_api_errors_total{api="..."}
```

---

## 🎯 Common Monitoring Tasks

### Check System Health

```bash
# Check all services up
curl -s http://localhost:9090/api/v1/query?query=up | jq '.data.result[] | select(.value[1] == "0")'

# Check for firing alerts
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state == "firing")'

# Check AlertManager status
curl -s http://localhost:9093/api/v1/status | jq '.data.uptime'
```

### View Specific Metrics

```bash
# Current positions
curl -s 'http://localhost:9090/api/v1/query?query=sigmax_position_qty' | jq '.data.result'

# Daily P&L
curl -s 'http://localhost:9090/api/v1/query?query=sigmax_daily_loss_usd' | jq '.data.result'

# RL model status
curl -s 'http://localhost:9090/api/v1/query?query=sigmax_rl_model_initialized' | jq '.data.result'

# Sentiment score
curl -s 'http://localhost:9090/api/v1/query?query=sigmax_news_sentiment_score' | jq '.data.result'

# Safety pause status
curl -s 'http://localhost:9090/api/v1/query?query=sigmax_safety_paused' | jq '.data.result'
```

### Export Metrics for Analysis

```bash
# Export last hour of P&L data
curl -s 'http://localhost:9090/api/v1/query_range?query=sigmax_pnl_realized&start='$(date -u -d '1 hour ago' +%s)'&end='$(date -u +%s)'&step=60' | jq '.data.result' > pnl_data.json

# Export sentiment timeline
curl -s 'http://localhost:9090/api/v1/query_range?query=sigmax_news_sentiment_score&start='$(date -u -d '24 hours ago' +%s)'&end='$(date -u +%s)'&step=300' | jq '.data.result' > sentiment_timeline.json
```

---

## 📧 Alert Notifications

### Configure Email Alerts

Edit `/infra/prometheus/alertmanager.yml`:

```yaml
receivers:
  - name: 'critical'
    email_configs:
      - to: 'alerts@yourcompany.com'
        from: 'sigmax@yourcompany.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your-email@gmail.com'
        auth_password: 'your-app-password'
        headers:
          Subject: '🚨 SIGMAX Critical Alert: {{ .GroupLabels.alertname }}'
```

### Configure Slack Alerts

```yaml
receivers:
  - name: 'critical'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#sigmax-critical-alerts'
        title: '🚨 {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true
```

### Configure PagerDuty

```yaml
receivers:
  - name: 'critical'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
        description: '{{ .GroupLabels.alertname }}: {{ .Annotations.summary }}'
```

### Reload AlertManager

```bash
# After configuration changes
docker-compose restart alertmanager

# Verify configuration
curl -X POST http://localhost:9093/-/reload
```

---

## 🔍 Troubleshooting

### Prometheus Not Scraping Targets

**Problem:** Targets showing as "down" in Prometheus

**Solutions:**
```bash
# 1. Check if service is exposing metrics
curl http://localhost:9091/metrics

# 2. Check network connectivity from Prometheus container
docker exec sigmax-prometheus wget -O- http://host.docker.internal:9091/metrics

# 3. Verify prometheus.yml configuration
docker exec sigmax-prometheus cat /etc/prometheus/prometheus.yml

# 4. Check Prometheus logs
docker logs sigmax-prometheus
```

### Grafana Dashboards Not Loading

**Problem:** Dashboards show "No data" or fail to load

**Solutions:**
```bash
# 1. Check Prometheus data source
curl http://localhost:3001/api/datasources

# 2. Verify Prometheus is reachable from Grafana
docker exec sigmax-grafana wget -O- http://prometheus:9090/api/v1/query?query=up

# 3. Check dashboard provisioning
docker exec sigmax-grafana ls /etc/grafana/provisioning/dashboards/

# 4. Check Grafana logs
docker logs sigmax-grafana
```

### Alerts Not Firing

**Problem:** Expected alerts not triggering

**Solutions:**
```bash
# 1. Check if metric exists
curl -s 'http://localhost:9090/api/v1/query?query=sigmax_safety_paused' | jq

# 2. Verify alert rules loaded
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name == "sigmax_safety_mechanisms")'

# 3. Check alert evaluation
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.alertname == "SystemAutoPaused")'

# 4. Validate alertmanager connection
curl -s http://localhost:9090/api/v1/alertmanagers | jq
```

### High Memory Usage

**Problem:** Prometheus using too much memory

**Solutions:**
```bash
# 1. Check retention settings (default: 30 days)
# Reduce in docker-compose.yml:
--storage.tsdb.retention.time=15d

# 2. Reduce scrape interval
# Edit prometheus.yml:
scrape_interval: 15s  # instead of 5s

# 3. Limit metric cardinality
# Add relabeling rules to drop high-cardinality labels
```

---

## 📊 Best Practices

### 1. Dashboard Organization

✅ **DO:**
- Use consistent time ranges per dashboard type
- Set appropriate refresh intervals (faster for trading, slower for infra)
- Add threshold lines to graphs
- Use color coding (green=good, yellow=warning, red=critical)
- Include descriptions in panel titles

❌ **DON'T:**
- Overload dashboards with too many panels
- Use auto-refresh < 5s (causes load)
- Mix unrelated metrics on same dashboard

### 2. Alert Configuration

✅ **DO:**
- Set appropriate `for:` durations to avoid flapping
- Use meaningful alert names and descriptions
- Group related alerts
- Test alerts before deploying
- Document runbook links in annotations

❌ **DON'T:**
- Alert on every anomaly (causes alert fatigue)
- Use same thresholds for dev/prod
- Skip testing alert delivery

### 3. Metric Naming

✅ **DO:**
- Follow naming convention: `sigmax_<component>_<metric>_<unit>`
- Use consistent label names
- Add units to metric names (`_seconds`, `_bytes`, `_total`)
- Version metric schemas if changing

❌ **DON'T:**
- Change metric names frequently
- Use inconsistent label values
- Create high-cardinality labels (e.g., user IDs)

### 4. Capacity Planning

- **Prometheus Storage:** ~100MB per scrape target per day (with 5s interval)
- **Grafana:** Minimal resources needed
- **AlertManager:** Minimal resources needed

**Recommended Resources (Production):**
- Prometheus: 4GB RAM, 2 CPU cores, 100GB SSD
- Grafana: 2GB RAM, 1 CPU core
- AlertManager: 512MB RAM, 0.5 CPU cores

---

## 🎓 Training & Resources

### Learning Resources

1. **Prometheus Basics**
   - [Official Docs](https://prometheus.io/docs/)
   - [PromQL Tutorial](https://prometheus.io/docs/prometheus/latest/querying/basics/)

2. **Grafana Basics**
   - [Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/)
   - [Alert Notifications](https://grafana.com/docs/grafana/latest/alerting/fundamentals/notifications/)

3. **SIGMAX-Specific**
   - [Operational Runbook](./OPERATIONAL_RUNBOOK.md)
   - [Codebase Audit Session Summary](../CODEBASE_AUDIT_SESSION_SUMMARY.md)

### Example PromQL Queries

```promql
# Trading Performance
sum(rate(sigmax_fills_total[5m])) by (symbol)  # Fills per second by symbol
avg(delta(sigmax_pnl_realized[1h]))  # Average hourly P&L change

# RL Module Analysis
histogram_quantile(0.95, sum(rate(sigmax_rl_prediction_duration_seconds_bucket[10m])) by (le))  # p95 latency
sum(rate(sigmax_rl_actions_total[5m])) by (action)  # Action distribution

# Sentiment Analysis
avg_over_time(sigmax_news_sentiment_score[1h])  # 1h moving average sentiment
deriv(sigmax_fear_greed_index[30m])  # Sentiment change rate

# Safety Monitoring
count(sigmax_consecutive_losses > 0)  # Number of symbols with losing streaks
sum(abs(sigmax_position_size)) / sum(sigmax_position_limit)  # Total position utilization
```

---

## 🆘 Support

For monitoring issues:

1. Check this guide first
2. Review Prometheus/Grafana logs
3. Consult [Operational Runbook](./OPERATIONAL_RUNBOOK.md)
4. Open GitHub issue: https://github.com/I-Onlabs/SIGMAX/issues

---

## 📋 Checklist: Production Monitoring Setup

Use this checklist when setting up monitoring for a new environment:

### Infrastructure Setup
- [ ] Start Prometheus container
- [ ] Start Grafana container
- [ ] Start AlertManager container
- [ ] Verify all containers healthy
- [ ] Check Prometheus targets are up
- [ ] Verify Grafana can reach Prometheus

### Dashboard Configuration
- [ ] Access Grafana UI (http://localhost:3001)
- [ ] Change default admin password
- [ ] Verify all 5 dashboards loaded
- [ ] Test each dashboard displays data
- [ ] Set dashboard permissions
- [ ] Configure dashboard refresh intervals

### Alert Configuration
- [ ] Verify alert rules loaded in Prometheus
- [ ] Test alert evaluation (check /alerts endpoint)
- [ ] Configure AlertManager receivers (email/Slack/PagerDuty)
- [ ] Test alert delivery
- [ ] Document escalation procedures
- [ ] Set up on-call rotation

### Metrics Validation
- [ ] Verify core trading metrics present
- [ ] Verify RL module metrics present
- [ ] Verify sentiment/research metrics present
- [ ] Verify safety mechanism metrics present
- [ ] Test metric queries in Prometheus UI
- [ ] Validate metric labels are correct

### Testing
- [ ] Trigger test alerts manually
- [ ] Verify alert notifications delivered
- [ ] Test dashboard performance under load
- [ ] Validate data retention settings
- [ ] Test backup/restore procedures

### Documentation
- [ ] Document custom dashboards
- [ ] Document alert runbooks
- [ ] Train team on monitoring tools
- [ ] Schedule regular monitoring reviews

---

**Last Updated:** November 9, 2025
**Version:** 1.0
**Maintained By:** SIGMAX Engineering Team
