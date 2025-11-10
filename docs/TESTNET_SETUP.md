# SIGMAX Testnet Configuration Guide

**Version:** 1.0
**Last Updated:** November 9, 2025
**Purpose:** Phase 1 Testnet Validation (2-week continuous testing)

---

## 📋 Overview

This guide walks through configuring SIGMAX for testnet trading validation before production deployment. Testnet allows you to:

- ✅ Validate all features with real market data but fake money
- ✅ Test RL model predictions in live conditions
- ✅ Verify safety mechanisms trigger correctly
- ✅ Measure system performance and latency
- ✅ Debug issues without financial risk
- ✅ Build confidence before live trading

**Recommended Duration:** 2 weeks continuous operation
**Capital:** Virtual testnet funds (no real money)
**Risk Level:** Zero financial risk

---

## 🎯 Prerequisites

### 1. Completed Work

Ensure you've completed:
- ✅ Week 1 implementation (RL module, news sentiment, researcher APIs, tests, runbooks, microservices, monitoring)
- ✅ All integration tests passing
- ✅ Monitoring infrastructure deployed (Prometheus, Grafana, AlertManager)
- ✅ Operational runbook reviewed

### 2. Required Accounts

You'll need testnet API credentials from:

**Binance Testnet** (Primary - Recommended)
- Website: https://testnet.binance.vision/
- Features: Spot trading, futures, WebSocket feeds
- Free virtual funds: 10,000 USDT + BTC/ETH
- API Rate Limits: Same as production

**Alternative: Bybit Testnet**
- Website: https://testnet.bybit.com/
- Features: Spot, futures, derivatives
- Free virtual funds: 100,000 USDT

**Alternative: OKX Testnet**
- Website: https://www.okx.com/demo-trading
- Features: Spot, futures, options
- Demo account with virtual funds

### 3. System Requirements

- **OS:** Linux (Ubuntu 20.04+ recommended)
- **RAM:** 8GB minimum, 16GB recommended
- **CPU:** 4 cores minimum
- **Disk:** 50GB free space
- **Network:** Stable internet (100+ Mbps recommended)
- **Python:** 3.11+
- **Docker:** 20.10+ (for databases and monitoring)

---

## 🔧 Step 1: Get Testnet API Credentials

### Option A: Binance Testnet (Recommended)

1. **Create Account**
   ```bash
   # Visit Binance Testnet
   open https://testnet.binance.vision/
   ```

2. **Get API Keys**
   - Click "Generate HMAC_SHA256 Key"
   - Save your API Key and Secret Key
   - **IMPORTANT:** These are testnet-only credentials (no real funds)

3. **Fund Account**
   - Testnet account starts with virtual funds
   - Additional funds: Click "Get Test Assets" button
   - Default: 10,000 USDT, 10 BTC, 100 ETH

4. **Verify API Access**
   ```bash
   # Test API connectivity
   curl -X GET 'https://testnet.binance.vision/api/v3/account' \
     -H "X-MBX-APIKEY: YOUR_API_KEY"
   ```

### Option B: Bybit Testnet

1. **Create Account**
   - Visit: https://testnet.bybit.com/
   - Sign up with email
   - Verify email

2. **Get API Keys**
   - Go to Account > API Management
   - Create new API key
   - Save API Key and Secret

3. **Fund Account**
   - Automatic 100,000 USDT virtual funds
   - Can request more from support

### Option C: OKX Testnet

1. **Create Demo Account**
   - Visit: https://www.okx.com/demo-trading
   - Sign up or use existing OKX account
   - Switch to "Demo Trading" mode

2. **Get API Keys**
   - Demo API keys available in account settings
   - Same API structure as production

---

## ⚙️ Step 2: Configure Environment

### Create Testnet Environment File

```bash
cd /home/user/SIGMAX

# Create testnet environment configuration
cp .env.example .env.testnet
```

### Edit `.env.testnet`

```bash
# ============================================
# TESTNET CONFIGURATION
# ============================================

# Environment
ENVIRONMENT=testnet
LOG_LEVEL=INFO
DEBUG=false

# ============================================
# Exchange Configuration
# ============================================

# Binance Testnet
EXCHANGE=binance
TESTNET=true
BINANCE_TESTNET_API_KEY=your_binance_testnet_api_key_here
BINANCE_TESTNET_API_SECRET=your_binance_testnet_secret_key_here
BINANCE_TESTNET_API_URL=https://testnet.binance.vision

# Exchange Settings
EXCHANGE_TIMEOUT=10
EXCHANGE_RATE_LIMIT=1200  # requests per minute
EXCHANGE_ENABLE_RATE_LIMIT=true

# ============================================
# Trading Configuration
# ============================================

# Trading Mode
TRADING_MODE=testnet
PAPER_TRADING=false  # Using real testnet API
DRY_RUN=false

# Symbols to Trade
TRADING_SYMBOLS=BTC/USDT,ETH/USDT
PRIMARY_SYMBOL=BTC/USDT

# Position Limits (Conservative for testnet)
MAX_POSITION_SIZE_USD=1000  # $1k max position
MAX_DAILY_LOSS_USD=50       # $50 daily loss limit
MAX_POSITIONS=2             # Max 2 concurrent positions

# Risk Parameters
POSITION_SIZE_PERCENT=0.1   # 10% of capital per trade
STOP_LOSS_PERCENT=2.0       # 2% stop loss
TAKE_PROFIT_PERCENT=4.0     # 4% take profit
MAX_SLIPPAGE_PERCENT=0.5    # 0.5% max slippage

# ============================================
# Safety Mechanisms
# ============================================

# Auto-Pause Triggers
SAFETY_CONSECUTIVE_LOSSES=3
SAFETY_DAILY_LOSS_LIMIT=50
SAFETY_POSITION_LIMIT=1000
SAFETY_API_ERROR_THRESHOLD=5

# Circuit Breaker
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_ERROR_THRESHOLD=10
CIRCUIT_BREAKER_TIME_WINDOW=60

# ============================================
# RL Module Configuration
# ============================================

RL_ENABLED=true
RL_MODEL_PATH=models/rl_trading_model
RL_TRAINING_MODE=false  # Set to true to train during testnet
RL_TRAINING_TIMESTEPS=10000
RL_UPDATE_INTERVAL=3600  # Update every hour

# RL Environment
RL_ENV_LOOKBACK=100
RL_ENV_COMMISSION=0.001  # 0.1% commission

# RL Decision Weight
RL_DECISION_WEIGHT=0.3  # 30% weight in decision ensemble

# ============================================
# Sentiment & Research Configuration
# ============================================

# News Sentiment
NEWS_SENTIMENT_ENABLED=true
NEWS_POLL_INTERVAL=300  # 5 minutes
NEWS_SENTIMENT_THRESHOLD=0.5

# Research APIs
RESEARCHER_ENABLED=true
CRYPTOPANIC_API_KEY=free  # Use "free" for public endpoint
REDDIT_API_ENABLED=true
COINGECKO_API_ENABLED=true
FEARGREED_API_ENABLED=true

# API Timeouts
RESEARCH_API_TIMEOUT=10
RESEARCH_API_RETRY_MAX=3

# Sentiment Decision Weight
SENTIMENT_DECISION_WEIGHT=0.2  # 20% weight

# ============================================
# Database Configuration
# ============================================

# PostgreSQL (OLTP)
POSTGRES_URL=postgresql://sigmax:sigmax@localhost:5432/sigmax_testnet
POSTGRES_POOL_SIZE=20
POSTGRES_MAX_OVERFLOW=10

# Redis (Cache)
REDIS_URL=redis://localhost:6379/1
REDIS_POOL_SIZE=10

# ClickHouse (OLAP)
CLICKHOUSE_URL=http://localhost:8123
CLICKHOUSE_DATABASE=sigmax_testnet
CLICKHOUSE_USER=sigmax
CLICKHOUSE_PASSWORD=sigmax

# ============================================
# Monitoring Configuration
# ============================================

# Prometheus
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
METRICS_EXPORT_PORT=9091  # Port for this service

# Grafana
GRAFANA_ENABLED=true
GRAFANA_URL=http://localhost:3001

# Logging
LOG_FILE=logs/sigmax_testnet.log
LOG_ROTATION=daily
LOG_RETENTION_DAYS=30

# Sentry (Optional - for error tracking)
SENTRY_ENABLED=false
SENTRY_DSN=your_sentry_dsn_here

# ============================================
# Feature Flags
# ============================================

# Core Features
ENABLE_RL_MODULE=true
ENABLE_NEWS_SENTIMENT=true
ENABLE_RESEARCHER_APIS=true
ENABLE_QUANTUM_VQE=false  # Disable expensive features for testnet

# Safety Features
ENABLE_AUTO_PAUSE=true
ENABLE_CIRCUIT_BREAKER=true
ENABLE_POSITION_LIMITS=true
ENABLE_LOSS_LIMITS=true

# ============================================
# Performance Configuration
# ============================================

# Latency Monitoring
LATENCY_MONITORING_ENABLED=true
TARGET_TICK_TO_TRADE_LATENCY_MS=100

# Queue Sizes
ORDER_QUEUE_SIZE=1000
MARKET_DATA_QUEUE_SIZE=10000

# Worker Threads
DECISION_WORKERS=2
EXECUTION_WORKERS=2

# ============================================
# Notification Configuration (Optional)
# ============================================

# Telegram Alerts
TELEGRAM_ENABLED=false
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Email Alerts
EMAIL_ENABLED=false
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=sigmax@yourdomain.com
EMAIL_TO=alerts@yourdomain.com

# ============================================
# Advanced Configuration
# ============================================

# Backtest Data
BACKTEST_START_DATE=2024-01-01
BACKTEST_END_DATE=2024-12-31

# Simulation
SIMULATION_LATENCY_MS=50  # Simulate 50ms latency
SIMULATION_SLIPPAGE_BPS=5  # Simulate 5bps slippage

# Debug
DEBUG_SAVE_DECISIONS=true  # Save all decisions for analysis
DEBUG_SAVE_MARKET_DATA=false  # Don't save all ticks (too much data)
```

### Set Environment Variables

```bash
# Load testnet environment
export $(cat .env.testnet | grep -v '^#' | xargs)

# Or use direnv for automatic loading
echo "dotenv .env.testnet" > .envrc
direnv allow
```

---

## 🚀 Step 3: Start Infrastructure

### Start Databases and Monitoring

```bash
# Start PostgreSQL, Redis, ClickHouse, Prometheus, Grafana
docker-compose -f docker-compose.yml --env-file .env.testnet up -d \
  postgres redis clickhouse prometheus grafana alertmanager

# Verify services are healthy
docker-compose ps

# Expected output:
# sigmax-postgres       Up (healthy)
# sigmax-redis          Up (healthy)
# sigmax-clickhouse     Up (healthy)
# sigmax-prometheus     Up (healthy)
# sigmax-grafana        Up (healthy)
# sigmax-alertmanager   Up (healthy)
```

### Initialize Databases

```bash
# Run database migrations
python scripts/db_migrate.py --env testnet

# Verify tables created
psql postgresql://sigmax:sigmax@localhost:5432/sigmax_testnet \
  -c "\dt" | grep -E 'orders|fills|positions'
```

### Verify Monitoring

```bash
# Access Grafana
open http://localhost:3001
# Login: admin / admin (change on first login)

# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | \
  jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# All should show health: "up"
```

---

## 🎬 Step 4: Run Pre-Flight Checks

### Validate Configuration

```bash
# Run configuration validator
python -m core.utils.config_validator --env testnet

# Expected output:
# ✓ Environment: testnet
# ✓ Exchange: binance (testnet mode)
# ✓ API credentials: valid
# ✓ Database connections: healthy
# ✓ Monitoring: enabled
# ✓ Safety mechanisms: enabled
# ✓ RL module: configured
# ✓ Sentiment APIs: configured
```

### Test Exchange Connectivity

```bash
# Test Binance testnet connection
python -c "
import ccxt
exchange = ccxt.binance({
    'apiKey': '$BINANCE_TESTNET_API_KEY',
    'secret': '$BINANCE_TESTNET_API_SECRET',
    'options': {'defaultType': 'spot'},
    'urls': {'api': 'https://testnet.binance.vision'}
})
exchange.set_sandbox_mode(True)
print('Balance:', exchange.fetch_balance())
print('BTC/USDT ticker:', exchange.fetch_ticker('BTC/USDT'))
"
```

### Run Health Checks

```bash
# Run comprehensive health check
python -m core.utils.healthcheck --detailed

# Expected output:
# ✓ System: OK
# ✓ Database (PostgreSQL): Connected
# ✓ Database (Redis): Connected
# ✓ Database (ClickHouse): Connected
# ✓ Exchange (Binance Testnet): Connected
# ✓ RL Module: Initialized
# ✓ News Sentiment: Running
# ✓ Researcher APIs: Available
# ✓ Safety Enforcer: Active
# ✓ Monitoring: Collecting metrics
```

---

## ▶️ Step 5: Start SIGMAX

### Start Core Services

```bash
# Method 1: Start all services with orchestrator
python -m core.main --env testnet --mode testnet

# Method 2: Start services individually (for debugging)
# Terminal 1: Market data ingestion
python -m apps.ingest_cex.main --env testnet &

# Terminal 2: Order book management
python -m apps.book_shard.main --env testnet &

# Terminal 3: Feature calculation
python -m apps.features.main --env testnet &

# Terminal 4: Decision engine
python -m apps.decision.main --env testnet &

# Terminal 5: Risk management
python -m apps.risk.main --env testnet &

# Terminal 6: Order routing
python -m apps.router.main --env testnet &

# Terminal 7: Execution
python -m apps.exec_cex.main --env testnet &

# Terminal 8: News sentiment scanner
python -m apps.signals.news_sentiment.main --env testnet &
```

### Verify Services Started

```bash
# Check processes
ps aux | grep python | grep -E 'ingest|book|features|decision|risk|router|exec|sentiment'

# Check logs
tail -f logs/sigmax_testnet.log

# Check metrics
curl -s http://localhost:9091/metrics | grep sigmax_

# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | \
  jq '.data.activeTargets[] | select(.health != "up")'
# Should return empty (all targets healthy)
```

---

## 📊 Step 6: Monitor Testnet Operation

### Access Dashboards

1. **Grafana Dashboards** (http://localhost:3001)
   - System Health Dashboard
   - Trading Metrics Dashboard
   - ML & RL Metrics Dashboard
   - Sentiment & Research Dashboard
   - Safety & Risk Controls Dashboard

2. **Prometheus** (http://localhost:9090)
   - Raw metrics queries
   - Alert status
   - Target health

3. **AlertManager** (http://localhost:9093)
   - Active alerts
   - Notification status

### Key Metrics to Watch

```promql
# Trading Activity
sum(rate(sigmax_orders_total[5m]))  # Orders per second

# Fill Rate
rate(sigmax_fills_total[5m]) / rate(sigmax_orders_total{status="sent"}[5m])

# P&L Tracking
sigmax_pnl_realized  # Cumulative P&L
sigmax_daily_loss_usd  # Daily loss

# RL Module
sigmax_rl_model_initialized  # Should be 1
rate(sigmax_rl_predictions_total[1m])  # Predictions/sec

# Sentiment
sigmax_news_sentiment_score  # -1 to +1
sigmax_social_sentiment_score

# Safety
sigmax_safety_paused  # Should be 0 (not paused)
sigmax_consecutive_losses  # Should be < 3
```

### Daily Monitoring Checklist

**Morning (9:00 AM):**
- [ ] Check all services running (`docker-compose ps`)
- [ ] Review overnight alerts (check AlertManager)
- [ ] Check daily P&L (should be within limits)
- [ ] Verify no auto-pause triggers
- [ ] Review trading activity (order count, fill rate)

**Midday (1:00 PM):**
- [ ] Check RL predictions happening
- [ ] Verify sentiment data updating
- [ ] Review API error rates (should be low)
- [ ] Check position sizes (within limits)

**Evening (6:00 PM):**
- [ ] Review daily P&L
- [ ] Check for any alerts fired
- [ ] Verify database sizes (not growing too fast)
- [ ] Export logs for analysis

**Before Sleep (10:00 PM):**
- [ ] Final P&L check
- [ ] Verify all services healthy
- [ ] Check overnight monitoring is active

---

## 🔍 Step 7: Testing Scenarios

### Test 1: Normal Operation (Days 1-3)

**Goal:** Verify system works in normal market conditions

**Steps:**
1. Let system trade automatically
2. Monitor for 72 hours continuously
3. Track metrics:
   - Total orders placed
   - Fill rate
   - Average latency
   - RL prediction accuracy
   - Sentiment correlation with price

**Success Criteria:**
- ✅ No crashes or service restarts
- ✅ Fill rate > 70%
- ✅ Latency < 200ms average
- ✅ RL making predictions regularly
- ✅ Sentiment data updating every 5min

### Test 2: Safety Mechanism Triggers (Days 4-5)

**Goal:** Verify auto-pause triggers work correctly

**Test 2a: Consecutive Losses**
```bash
# Manually trigger consecutive losses for testing
python -m tests.safety.trigger_consecutive_losses --count 3

# Expected: System should auto-pause after 3rd loss
# Verify: sigmax_safety_paused == 1
# Verify: Alert "SystemAutoPaused" fires
```

**Test 2b: Daily Loss Limit**
```bash
# Simulate daily loss exceeding $50
python -m tests.safety.trigger_daily_loss --amount 51

# Expected: System should auto-pause
# Verify: Alert "DailyLossLimitExceeded" fires
```

**Test 2c: Position Limit**
```bash
# Try to take position > $1000
python -m tests.safety.trigger_position_limit --size 1100

# Expected: Order should be rejected
# Verify: sigmax_risk_rejections_total increases
```

**Success Criteria:**
- ✅ All safety triggers activate correctly
- ✅ Alerts fire within 30 seconds
- ✅ System pauses trading when expected
- ✅ Manual resume works after pause

### Test 3: API Failures (Days 6-7)

**Goal:** Verify graceful degradation when APIs fail

**Test 3a: Exchange API Timeout**
```bash
# Simulate exchange API delays using toxiproxy
docker-compose up -d toxiproxy

# Add 5s latency to exchange API
curl -X POST http://localhost:8474/proxies/exchange/toxics \
  -d '{"name":"latency","type":"latency","attributes":{"latency":5000}}'

# Expected: System should detect slow API and potentially pause
# Verify: Alert "ResearchAPITimeoutSpike" may fire
```

**Test 3b: Sentiment API Failure**
```bash
# Disable sentiment APIs temporarily
export NEWS_SENTIMENT_ENABLED=false
export RESEARCHER_ENABLED=false

# Restart relevant services
# Expected: System should continue trading with reduced decision confidence
# Verify: RL and technical analysis still working
```

**Success Criteria:**
- ✅ System doesn't crash on API failures
- ✅ Graceful fallback to available data sources
- ✅ Alerts fire for API issues
- ✅ Recovery when APIs come back

### Test 4: RL Model Performance (Days 8-10)

**Goal:** Evaluate RL model decision quality

**Steps:**
1. Track RL predictions vs actual outcomes
2. Measure:
   - Prediction accuracy (how often buy/sell was correct)
   - Action distribution (buy/sell/hold ratio)
   - Correlation with P&L
   - Latency of predictions

**Analysis:**
```bash
# Export RL decisions for analysis
python -m scripts.export_rl_decisions \
  --start "2025-11-09 00:00:00" \
  --end "2025-11-12 00:00:00" \
  --output rl_analysis.csv

# Analyze with pandas
python -c "
import pandas as pd
df = pd.read_csv('rl_analysis.csv')
print('Action Distribution:', df['action'].value_counts())
print('Win Rate by Action:', df.groupby('action')['profitable'].mean())
print('Average Latency:', df['latency_ms'].mean(), 'ms')
"
```

**Success Criteria:**
- ✅ RL predictions complete in < 1s
- ✅ Action distribution roughly balanced (not all one action)
- ✅ Some correlation with profitable trades
- ✅ No model loading errors

### Test 5: Sentiment Integration (Days 11-12)

**Goal:** Verify sentiment data influences decisions appropriately

**Steps:**
1. Track sentiment scores over time
2. Correlate with trading decisions
3. Verify data freshness

**Analysis:**
```bash
# Export sentiment timeline
curl -s 'http://localhost:9090/api/v1/query_range?query=sigmax_news_sentiment_score&start='$(date -u -d '48 hours ago' +%s)'&end='$(date -u +%s)'&step=300' > sentiment_timeline.json

# Analyze sentiment vs price
python -m scripts.analyze_sentiment_correlation \
  --sentiment sentiment_timeline.json \
  --symbol BTC/USDT
```

**Success Criteria:**
- ✅ Sentiment updates every 5 minutes
- ✅ No data staleness > 10 minutes
- ✅ RSS feeds successfully fetched
- ✅ Research APIs responding < 10s average

### Test 6: Full Load Test (Days 13-14)

**Goal:** Test system under maximum load

**Steps:**
```bash
# Increase trading symbols
export TRADING_SYMBOLS=BTC/USDT,ETH/USDT,BNB/USDT,SOL/USDT,ADA/USDT

# Reduce decision interval (more frequent decisions)
export DECISION_INTERVAL=10  # Every 10 seconds

# Restart system
docker-compose restart

# Run for 48 hours
# Monitor CPU, memory, network usage
```

**Success Criteria:**
- ✅ CPU < 80% average
- ✅ Memory < 8GB
- ✅ Network bandwidth adequate
- ✅ No queue overflows
- ✅ Latency still acceptable

---

## 📈 Step 8: Performance Analysis

### Export Test Results

```bash
# Export all trading activity
python -m scripts.export_testnet_results \
  --start "2025-11-09" \
  --end "2025-11-23" \
  --output testnet_results/

# Generates:
# - orders.csv (all orders)
# - fills.csv (all fills)
# - pnl.csv (P&L timeline)
# - rl_decisions.csv (RL predictions)
# - sentiment.csv (sentiment scores)
# - alerts.csv (all alerts fired)
# - metrics.csv (aggregated metrics)
```

### Key Metrics to Calculate

```python
import pandas as pd

# Load data
orders = pd.read_csv('testnet_results/orders.csv')
fills = pd.read_csv('testnet_results/fills.csv')
pnl = pd.read_csv('testnet_results/pnl.csv')

# Calculate metrics
print("=== TESTNET RESULTS (2 WEEKS) ===")
print(f"Total Orders: {len(orders)}")
print(f"Total Fills: {len(fills)}")
print(f"Fill Rate: {len(fills)/len(orders)*100:.1f}%")
print(f"Total P&L: ${pnl['realized_pnl'].sum():.2f}")
print(f"Win Rate: {(pnl['pnl'] > 0).sum() / len(pnl) * 100:.1f}%")
print(f"Average Trade P&L: ${pnl['pnl'].mean():.2f}")
print(f"Max Drawdown: ${pnl['pnl'].cumsum().min():.2f}")
print(f"Sharpe Ratio: {pnl['pnl'].mean() / pnl['pnl'].std():.2f}")

# Auto-pause analysis
alerts = pd.read_csv('testnet_results/alerts.csv')
auto_pauses = alerts[alerts['alert_name'] == 'SystemAutoPaused']
print(f"\nAuto-Pause Triggers: {len(auto_pauses)}")
print("Reasons:", auto_pauses['reason'].value_counts())

# RL performance
rl = pd.read_csv('testnet_results/rl_decisions.csv')
print(f"\nRL Predictions: {len(rl)}")
print(f"Average Latency: {rl['latency_ms'].mean():.1f}ms")
print("Action Distribution:", rl['action'].value_counts())

# Sentiment correlation
sentiment = pd.read_csv('testnet_results/sentiment.csv')
print(f"\nSentiment Updates: {len(sentiment)}")
print(f"Average News Sentiment: {sentiment['news_score'].mean():.2f}")
print(f"Average Social Sentiment: {sentiment['social_score'].mean():.2f}")
```

### Generate Report

```bash
# Automatic report generation
python -m scripts.generate_testnet_report \
  --data testnet_results/ \
  --output reports/testnet_report.md

# View report
cat reports/testnet_report.md
```

---

## ✅ Step 9: Go/No-Go Decision

### Evaluation Criteria

Review these criteria to decide if ready for production:

#### System Stability
- [ ] Zero crashes during 2-week period
- [ ] All services started successfully every day
- [ ] No memory leaks or resource exhaustion
- [ ] Database performance acceptable

#### Trading Performance
- [ ] Fill rate > 70%
- [ ] Average latency < 200ms
- [ ] P&L positive or neutral (testnet P&L is informational)
- [ ] Order rejection rate < 20%

#### RL Module
- [ ] Model initialized successfully every time
- [ ] Predictions completing in < 1s
- [ ] No model loading errors
- [ ] Action distribution reasonable (not stuck on one action)

#### Sentiment & Research
- [ ] APIs responding reliably (>95% success rate)
- [ ] Data freshness maintained (<10min staleness)
- [ ] RSS feeds fetching successfully
- [ ] Sentiment scores updating regularly

#### Safety Mechanisms
- [ ] Auto-pause triggers working correctly
- [ ] All safety limits respected
- [ ] Circuit breaker functional
- [ ] Manual resume working after pause

#### Monitoring & Alerts
- [ ] All metrics collecting correctly
- [ ] Dashboards displaying data
- [ ] Alerts firing when expected
- [ ] No false positive alerts

#### Documentation
- [ ] Operational runbook reviewed and updated
- [ ] Monitoring setup guide followed
- [ ] Testnet learnings documented
- [ ] Production playbook prepared

### Decision Matrix

| Criterion | Weight | Score (0-10) | Weighted |
|-----------|--------|--------------|----------|
| System Stability | 25% | ___ | ___ |
| Trading Performance | 20% | ___ | ___ |
| RL Module | 15% | ___ | ___ |
| Sentiment/Research | 10% | ___ | ___ |
| Safety Mechanisms | 20% | ___ | ___ |
| Monitoring/Alerts | 10% | ___ | ___ |
| **TOTAL** | **100%** | | **/10** |

**Go/No-Go Threshold:** ≥ 7.0/10

### Next Steps

**If SCORE ≥ 7.0 (GO):**
1. Address any remaining issues found during testnet
2. Update configuration for production (lower limits, stricter safety)
3. Set up production monitoring alerts (email, Slack, PagerDuty)
4. Prepare for Phase 1 live trading with $50 limit
5. Review security hardening (Dependabot alerts, API key rotation)

**If SCORE < 7.0 (NO-GO):**
1. Document all issues encountered
2. Prioritize fixes for critical issues
3. Extend testnet period by 1 week
4. Re-run failed test scenarios
5. Re-evaluate after improvements

---

## 🐛 Troubleshooting

### Issue: Exchange API Returns "Invalid Signature"

**Cause:** API keys incorrect or signature generation wrong

**Solution:**
```bash
# Verify API key format
echo $BINANCE_TESTNET_API_KEY  # Should be 64-char hex string
echo $BINANCE_TESTNET_API_SECRET  # Should be 64-char hex string

# Test signature manually
python -c "
import hmac
import hashlib
import time
secret = '$BINANCE_TESTNET_API_SECRET'
timestamp = str(int(time.time() * 1000))
params = f'timestamp={timestamp}'
signature = hmac.new(secret.encode(), params.encode(), hashlib.sha256).hexdigest()
print(f'Signature test: {signature}')
"

# Regenerate keys if needed
open https://testnet.binance.vision/
```

### Issue: "Insufficient Balance" Error

**Cause:** Testnet account out of virtual funds

**Solution:**
```bash
# Check balance
python -c "
import ccxt
exchange = ccxt.binance({
    'apiKey': '$BINANCE_TESTNET_API_KEY',
    'secret': '$BINANCE_TESTNET_API_SECRET',
    'urls': {'api': 'https://testnet.binance.vision'}
})
exchange.set_sandbox_mode(True)
print(exchange.fetch_balance())
"

# Get more testnet funds
# Visit https://testnet.binance.vision/
# Click "Get Test Assets"
```

### Issue: RL Model Failing to Load

**Cause:** Model file not found or corrupted

**Solution:**
```bash
# Check model file exists
ls -lh models/rl_trading_model*

# If missing, train new model
python -m core.modules.rl \
  --mode train \
  --timesteps 10000 \
  --save-path models/rl_trading_model

# Verify model loads
python -c "
from stable_baselines3 import PPO
model = PPO.load('models/rl_trading_model')
print('Model loaded successfully')
"
```

### Issue: Sentiment Data Not Updating

**Cause:** News APIs failing or network issues

**Solution:**
```bash
# Test news sentiment scanner directly
python -m apps.signals.news_sentiment.main --env testnet --debug

# Check RSS feeds manually
curl -I https://www.coindesk.com/arc/outboundfeeds/rss/

# Test research APIs
python -c "
import aiohttp
import asyncio

async def test_apis():
    async with aiohttp.ClientSession() as session:
        # Test CryptoPanic
        url = 'https://cryptopanic.com/api/v1/posts/?auth_token=free&currencies=BTC'
        async with session.get(url) as resp:
            print('CryptoPanic:', resp.status, await resp.json())

        # Test Reddit
        url = 'https://www.reddit.com/r/CryptoCurrency/hot.json?limit=5'
        async with session.get(url) as resp:
            print('Reddit:', resp.status)

asyncio.run(test_apis())
"
```

### Issue: System Auto-Paused Unexpectedly

**Cause:** Safety trigger activated

**Solution:**
```bash
# Check pause reason
curl -s 'http://localhost:9090/api/v1/query?query=sigmax_safety_pause_reason' | jq

# Check what triggered it
curl -s http://localhost:9093/api/v1/alerts | \
  jq '.data[] | select(.labels.alertname == "SystemAutoPaused")'

# Review recent trading activity
tail -100 logs/sigmax_testnet.log | grep -E 'pause|loss|error'

# Manual resume (after fixing issue)
python -m core.utils.safety_override --action resume --reason "Investigated and resolved"
```

### Issue: Prometheus Targets Down

**Cause:** Services not exposing metrics or network issues

**Solution:**
```bash
# Check which targets are down
curl -s http://localhost:9090/api/v1/targets | \
  jq '.data.activeTargets[] | select(.health != "up") | {job: .labels.job, error: .lastError}'

# Test metrics endpoint directly
curl http://localhost:9091/metrics

# Check service logs
docker logs sigmax-prometheus

# Restart Prometheus
docker-compose restart prometheus
```

---

## 📚 Additional Resources

- **Operational Runbook:** `/docs/OPERATIONAL_RUNBOOK.md`
- **Monitoring Setup Guide:** `/docs/MONITORING_SETUP.md`
- **Codebase Audit Summary:** `/CODEBASE_AUDIT_SESSION_SUMMARY.md`
- **Binance Testnet Docs:** https://testnet.binance.vision/
- **CCXT Documentation:** https://docs.ccxt.com/

---

## 📝 Testnet Log Template

Use this template to track daily testnet progress:

```markdown
# SIGMAX Testnet Log - Day X

**Date:** YYYY-MM-DD
**Tester:** Your Name
**Environment:** Binance Testnet

## Summary
- System Uptime: X hours
- Orders Placed: X
- Fills: X (X% fill rate)
- P&L: $X.XX
- Auto-Pause Triggers: X

## Issues Encountered
1. [Issue description]
   - Severity: Critical/Warning/Info
   - Resolution: [What you did]
   - Status: Resolved/Open

## Metrics
- Average Latency: Xms
- RL Predictions: X
- Sentiment Updates: X
- API Errors: X

## Notes
[Any observations or learnings]

## Action Items
- [ ] [Task to do tomorrow]
```

---

**End of Testnet Setup Guide**

**Next:** After successful 2-week testnet validation, proceed to production setup with Phase 1 live trading ($50 capital limit).

**Questions?** Review the [Operational Runbook](./OPERATIONAL_RUNBOOK.md) or open a GitHub issue.
