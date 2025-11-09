# SIGMAX Operational Runbook

**Version:** 1.0
**Last Updated:** November 2025
**Status:** Phase 0 - Paper Trading Ready

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Pre-Flight Checklist](#pre-flight-checklist)
3. [Starting the System](#starting-the-system)
4. [Monitoring & Health Checks](#monitoring--health-checks)
5. [Common Operations](#common-operations)
6. [Incident Response](#incident-response)
7. [Troubleshooting Guide](#troubleshooting-guide)
8. [Maintenance Procedures](#maintenance-procedures)
9. [Emergency Procedures](#emergency-procedures)
10. [Performance Optimization](#performance-optimization)

---

## System Overview

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                     SIGMAX Trading System                    │
├─────────────────────────────────────────────────────────────┤
│  Core Orchestrator                                          │
│  ├── Multi-Agent System (7 agents)                         │
│  ├── Decision History & Explainability                     │
│  └── Safety Enforcer (Auto-pause triggers)                 │
├─────────────────────────────────────────────────────────────┤
│  Modules                                                     │
│  ├── Data Module (CCXT, APIs)                              │
│  ├── RL Module (Stable Baselines 3 PPO)                    │
│  ├── Quantum Module (Qiskit VQE)                           │
│  ├── Execution Module (Paper/Live)                         │
│  ├── Arbitrage Scanner                                      │
│  └── Compliance Engine (OPA)                               │
├─────────────────────────────────────────────────────────────┤
│  External Integrations                                       │
│  ├── News APIs (CryptoPanic, RSS feeds)                    │
│  ├── Social APIs (Reddit)                                   │
│  ├── On-chain APIs (CoinGecko)                             │
│  └── Exchange APIs (Binance, Coinbase, Kraken)             │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure                                              │
│  ├── PostgreSQL (trade history, decisions)                 │
│  ├── Redis (caching, decision history)                     │
│  ├── NATS (message queue)                                   │
│  └── Prometheus (metrics)                                   │
└─────────────────────────────────────────────────────────────┘
```

### Key Metrics
- **Decision Latency**: <30ms target (current ~30ms)
- **Uptime Target**: 99.5% for Phase 1
- **Maximum Daily Loss**: $10 (configurable)
- **Position Size Limit**: Configurable per profile
- **Auto-pause Triggers**: 6 safety mechanisms

---

## Pre-Flight Checklist

### Before Starting SIGMAX

#### 1. Environment Configuration

```bash
# Create .env file from template
cp .env.example .env

# Edit .env with required values
vim .env
```

**Required Environment Variables:**

```bash
# Trading Configuration
TRADING_MODE=paper              # or 'live' for production
TESTNET=true                    # Use testnet for Phase 1
MAX_POSITION_SIZE=10           # USD
MAX_DAILY_LOSS=10              # USD

# Exchange API (for live trading)
EXCHANGE=binance               # binance, coinbase, kraken
API_KEY=your_api_key
API_SECRET=your_api_secret

# LLM Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key  # Optional
OLLAMA_URL=http://localhost:11434      # Optional local LLM

# Database (Optional for production)
POSTGRES_URL=postgresql://user:pass@localhost:5432/sigmax
REDIS_URL=redis://localhost:6379

# External APIs (Optional)
NEWSAPI_KEY=your_newsapi_key   # Optional for premium news
```

#### 2. Dependency Check

```bash
# Verify Python version
python --version  # Should be 3.11+

# Install dependencies
cd /home/user/SIGMAX/core
pip install -r requirements.txt

# Verify critical packages
python -c "import ccxt, qiskit, stable_baselines3, langchain; print('✓ All critical dependencies installed')"
```

#### 3. Service Health Check

```bash
# Check PostgreSQL (if using)
pg_isready -h localhost -p 5432

# Check Redis (if using)
redis-cli ping

# Check NATS (if using)
nats-server --version
```

#### 4. Configuration Validation

```bash
# Run configuration validator
python -c "
from core.config.validator import ConfigValidator
validator = ConfigValidator()
validator.validate_all()
print('✓ Configuration valid')
"
```

---

## Starting the System

### Quick Start (Paper Trading)

```bash
cd /home/user/SIGMAX

# Start core orchestrator
python core/main.py --mode paper --profile conservative

# Or use Telegram bot
python core/utils/telegram_bot.py
```

### Full System Start (with UI)

```bash
# Terminal 1: Start backend services (if using Docker)
docker-compose up -d postgres redis nats

# Terminal 2: Start SIGMAX core
cd /home/user/SIGMAX/core
python main.py --mode paper --profile conservative

# Terminal 3: Start API server
cd /home/user/SIGMAX/ui/api
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 4: Start UI (development)
cd /home/user/SIGMAX/ui/web
npm run dev
```

### Verification Steps

1. **Check logs for startup messages:**
   ```bash
   tail -f logs/sigmax.log
   ```

2. **Verify agent initialization:**
   ```
   ✓ Researcher agent initialized
   ✓ Bull agent initialized
   ✓ Bear agent initialized
   ✓ Analyzer agent initialized
   ✓ Risk agent initialized
   ✓ Privacy agent initialized
   ✓ Optimizer agent initialized
   ```

3. **Check system status:**
   ```bash
   # Via API
   curl http://localhost:8000/api/status

   # Via Telegram
   /status
   ```

4. **Expected output:**
   ```json
   {
     "mode": "paper",
     "running": true,
     "paused": false,
     "agents": {
       "orchestrator": "active",
       "researcher": "active",
       "analyzer": "active"
     },
     "modules": {
       "rl": "initialized",
       "quantum": "initialized",
       "execution": "paper_mode"
     }
   }
   ```

---

## Monitoring & Health Checks

### Real-time Monitoring

#### 1. System Health Dashboard

```bash
# Via API
curl http://localhost:8000/api/health

# Expected response
{
  "status": "healthy",
  "uptime": 3600,
  "last_decision": "2025-11-08T10:30:00Z",
  "safety_status": {
    "paused": false,
    "consecutive_losses": 0,
    "daily_pnl": 2.5
  }
}
```

#### 2. Key Metrics to Monitor

| Metric | Command | Healthy Range | Alert Threshold |
|--------|---------|---------------|-----------------|
| **Decision Latency** | Check logs | <30ms | >100ms |
| **Memory Usage** | `ps aux | grep python` | <4GB | >6GB |
| **CPU Usage** | `top -p $(pgrep -f main.py)` | <50% | >80% |
| **Daily PnL** | `/status` in Telegram | Positive | <-$10 |
| **API Error Rate** | Check logs | <1% | >5% |
| **Consecutive Losses** | `/status` | 0-2 | ≥3 (auto-pause) |

#### 3. Log Monitoring

```bash
# Watch logs in real-time
tail -f logs/sigmax.log | grep -E "ERROR|WARNING|TRADE|PAUSE"

# Search for errors
grep "ERROR" logs/sigmax.log | tail -20

# Check recent trades
grep "TRADE" logs/sigmax.log | tail -10

# Monitor safety triggers
grep "PAUSE" logs/sigmax.log | tail -10
```

### Automated Health Checks

```bash
# Create health check script
cat > check_health.sh <<'EOF'
#!/bin/bash

# Check if process is running
if ! pgrep -f "core/main.py" > /dev/null; then
    echo "❌ SIGMAX not running!"
    exit 1
fi

# Check API health
if ! curl -s http://localhost:8000/api/health | grep -q "healthy"; then
    echo "⚠️  API health check failed"
    exit 1
fi

# Check recent log errors
ERROR_COUNT=$(grep -c "ERROR" logs/sigmax.log | tail -100)
if [ "$ERROR_COUNT" -gt 10 ]; then
    echo "⚠️  High error count: $ERROR_COUNT"
    exit 1
fi

echo "✓ All health checks passed"
exit 0
EOF

chmod +x check_health.sh

# Run every 5 minutes
# */5 * * * * /home/user/SIGMAX/check_health.sh
```

---

## Common Operations

### 1. Analyzing a Symbol

```bash
# Via API
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC/USDT"}'

# Via Telegram
/analyze BTC/USDT

# Via Python
python -c "
import asyncio
from core.main import SIGMAX

async def analyze():
    sigmax = SIGMAX(mode='paper')
    await sigmax.initialize()
    result = await sigmax.orchestrator.analyze_symbol('BTC/USDT')
    print(result)
    await sigmax.stop()

asyncio.run(analyze())
"
```

### 2. Executing a Trade

```bash
# Via API
curl -X POST http://localhost:8000/api/trade \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC/USDT",
    "action": "buy",
    "size": 0.01
  }'

# Via Telegram
/trade BTC/USDT buy 0.01
```

### 3. Checking Portfolio

```bash
# Via API
curl http://localhost:8000/api/portfolio

# Via Telegram
/portfolio

# Expected output
{
  "total_value_usd": 10050.25,
  "positions": {
    "BTC/USDT": {
      "size": 0.1,
      "entry_price": 95000,
      "current_price": 96000,
      "pnl": 100.00,
      "pnl_pct": 1.05
    }
  },
  "cash": 500.25,
  "daily_pnl": 50.25
}
```

### 4. Pausing/Resuming Trading

```bash
# Pause for 1 hour
curl -X POST http://localhost:8000/api/control/pause \
  -d '{"duration": 3600}'

# Or via Telegram
/pause 1h

# Resume trading
curl -X POST http://localhost:8000/api/control/resume

# Or via Telegram
/resume
```

### 5. Getting Decision Explanation

```bash
# Via Telegram
/why BTC/USDT

# Via API
curl http://localhost:8000/api/history?symbol=BTC/USDT&limit=1

# Expected output
{
  "symbol": "BTC/USDT",
  "timestamp": "2025-11-08T10:30:00Z",
  "decision": "BUY",
  "confidence": 0.85,
  "reasoning": {
    "bull_argument": "Strong bullish momentum, RSI oversold...",
    "bear_argument": "High volatility, resistance at 96k...",
    "risk_assessment": "Medium risk, within limits...",
    "technical_analysis": "RSI: 35, MACD bullish cross...",
    "sentiment": 0.6
  }
}
```

---

## Incident Response

### Auto-Pause Scenarios

SIGMAX will automatically pause trading in these situations:

#### 1. Consecutive Losses (3+ trades)

**Symptoms:**
- System logs: `PAUSE: Consecutive loss limit reached (3)`
- Telegram notification: "🛑 Trading paused: 3 consecutive losses"

**Response:**
1. Check recent trades: `/history`
2. Review decision reasoning: `/why BTC/USDT`
3. Analyze market conditions
4. Decision:
   - If market conditions poor: Keep paused, adjust parameters
   - If system issue: Investigate logs, fix bugs
   - If normal variance: Resume with caution: `/resume`

#### 2. Daily Loss Limit Exceeded

**Symptoms:**
- Log: `PAUSE: Daily loss limit exceeded (-$12.50 / -$10.00)`
- Telegram: "🛑 Trading paused: Daily loss limit"

**Response:**
1. Review daily P&L: `/status`
2. Check all trades: `/history --today`
3. Identify loss causes
4. Actions:
   - **Do not override** unless absolutely certain
   - Review risk parameters
   - Consider reducing position sizes
   - Resume next trading day

#### 3. API Error Burst

**Symptoms:**
- Log: `PAUSE: API error burst detected (7 errors in 60s)`
- Telegram: "⚠️  High API error rate detected"

**Response:**
1. Check exchange API status
2. Verify network connectivity
3. Review API rate limits
4. Actions:
   - Wait for API recovery
   - Check API credentials
   - Resume when errors clear

#### 4. High Slippage / MEV Attack

**Symptoms:**
- Log: `PAUSE: High slippage detected (2.5%)`
- Telegram: "🛑 Excessive slippage, possible MEV attack"

**Response:**
1. Review affected trade
2. Check if market-wide issue
3. Verify no account compromise
4. Actions:
   - Investigate execution logs
   - Consider increasing slippage tolerance
   - Resume with smaller position sizes

#### 5. Sentiment Drop

**Symptoms:**
- Log: `PAUSE: Market sentiment dropped below threshold (-0.35)`
- Telegram: "📉 Negative market sentiment detected"

**Response:**
1. Check news: Review recent articles
2. Verify sentiment sources
3. Monitor social sentiment
4. Actions:
   - Wait for sentiment recovery
   - Reduce position sizes
   - Resume when sentiment improves

#### 6. Privacy Breach Detection

**Symptoms:**
- Log: `PAUSE: Privacy breach detected (PII in logs)`
- Telegram: "🔒 Privacy violation detected"

**Response:**
1. **Immediately** stop system: `/panic`
2. Review logs for sensitive data
3. Purge PII from logs
4. Actions:
   - Fix privacy leak
   - Update privacy filters
   - Resume only after verification

---

## Troubleshooting Guide

### Common Issues

#### Issue 1: System Won't Start

**Symptoms:**
```
ImportError: No module named 'stable_baselines3'
```

**Solution:**
```bash
cd /home/user/SIGMAX/core
pip install -r requirements.txt
```

---

#### Issue 2: Quantum Module Initialization Fails

**Symptoms:**
```
WARNING: Qiskit not available: ...
```

**Solution:**
```bash
pip install qiskit qiskit-aer qiskit-algorithms
```

**Note:** This is not critical - system will fall back to classical optimization.

---

#### Issue 3: LLM API Errors

**Symptoms:**
```
ERROR: OpenAI API error: Invalid API key
```

**Solution:**
```bash
# Check API key
echo $OPENAI_API_KEY

# Or set in .env
OPENAI_API_KEY=sk-...

# Alternative: Use local Ollama
OLLAMA_URL=http://localhost:11434
```

---

#### Issue 4: Exchange API Connection Fails

**Symptoms:**
```
ERROR: CCXT: binance.exceptions.AuthenticationError
```

**Solution:**
1. Verify API credentials in .env
2. Check API permissions (trading enabled)
3. Verify IP whitelist (if applicable)
4. Test with testnet first:
   ```bash
   TESTNET=true python core/main.py
   ```

---

#### Issue 5: High Memory Usage

**Symptoms:**
- Memory usage >6GB
- System slow or unresponsive

**Solution:**
```bash
# Check memory usage
ps aux | grep python

# Restart with memory limit
python -Xms2g -Xmx4g core/main.py

# Or reduce concurrent operations in config
```

---

#### Issue 6: Decision Latency Too High

**Symptoms:**
- Decisions taking >100ms
- Logs show slow agent responses

**Solution:**
1. Enable response caching
2. Use local Ollama instead of OpenAI
3. Reduce number of agents
4. Optimize database queries

---

## Maintenance Procedures

### Daily Maintenance

```bash
# Check disk space
df -h

# Review logs
tail -100 logs/sigmax.log

# Check daily P&L
curl http://localhost:8000/api/status | jq '.performance.daily_pnl'

# Backup decision history
cp decision_history.json backups/decision_history_$(date +%Y%m%d).json
```

### Weekly Maintenance

```bash
# Rotate logs
logrotate /etc/logrotate.d/sigmax

# Update RL model with recent data
python scripts/train_rl_model.py --days 7

# Review safety violations
grep "PAUSE" logs/sigmax.log | wc -l

# Database vacuum (if using PostgreSQL)
psql -d sigmax -c "VACUUM ANALYZE;"
```

### Monthly Maintenance

```bash
# Update dependencies
pip install --upgrade -r core/requirements.txt

# Review and update safety parameters
vim core/config/safety.yaml

# Audit trade history
python scripts/audit_trades.py --month $(date +%Y-%m)

# Performance review
python scripts/generate_report.py --period month
```

---

## Emergency Procedures

### PANIC: Emergency Stop

```bash
# Via Telegram (fastest)
/panic

# Via API
curl -X POST http://localhost:8000/api/control/panic

# Via kill command (if unresponsive)
pkill -9 -f "core/main.py"
```

**This will:**
1. Immediately stop all trading
2. Close all open positions (market orders)
3. Pause the system
4. Send alerts

### Recovery from Crash

```bash
# 1. Check if process is running
pgrep -f "core/main.py"

# 2. Check logs for crash reason
tail -100 logs/sigmax.log

# 3. Verify no stuck positions
python -c "
from core.modules.execution import ExecutionModule
import asyncio

async def check():
    exec_module = ExecutionModule()
    await exec_module.initialize()
    portfolio = await exec_module.get_portfolio()
    print('Open positions:', portfolio)
    await exec_module.close()

asyncio.run(check())
"

# 4. Restart system
python core/main.py --mode paper --profile conservative
```

### Data Corruption

```bash
# Restore from backup
cp backups/decision_history_$(date +%Y%m%d).json decision_history.json

# Rebuild decision history from trades
python scripts/rebuild_history.py

# Verify integrity
python scripts/verify_data.py
```

---

## Performance Optimization

### Optimizing Decision Latency

```python
# In core/config/optimization.yaml
agents:
  use_cache: true          # Cache LLM responses
  parallel_execution: true # Run agents in parallel
  timeout: 5000           # 5s timeout per agent

modules:
  rl:
    batch_predictions: true
  quantum:
    shots: 100            # Reduce for faster decisions
```

### Optimizing Memory Usage

```yaml
# In core/config/memory.yaml
decision_history:
  max_entries: 1000      # Limit in-memory history
  persist_to_redis: true

data_module:
  cache_ttl: 60          # Clear old cache data
```

### Monitoring Performance

```bash
# Profile code
python -m cProfile -o profile.stats core/main.py
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumtime').print_stats(20)"

# Monitor in real-time
htop -p $(pgrep -f "core/main.py")
```

---

## Appendix

### Useful Commands

```bash
# Tail logs with filtering
tail -f logs/sigmax.log | grep -E "TRADE|ERROR|PAUSE"

# Count trades by action
grep "TRADE" logs/sigmax.log | grep -oE "action: (buy|sell|hold)" | sort | uniq -c

# Calculate win rate
python scripts/calculate_win_rate.py

# Export trades to CSV
python scripts/export_trades.py --format csv --output trades.csv
```

### Configuration Files Reference

| File | Purpose | Location |
|------|---------|----------|
| `.env` | Environment variables | `/home/user/SIGMAX/.env` |
| `config.yaml` | Main configuration | `/home/user/SIGMAX/core/config/config.yaml` |
| `safety.yaml` | Safety parameters | `/home/user/SIGMAX/core/config/safety.yaml` |
| `agents.yaml` | Agent configuration | `/home/user/SIGMAX/core/config/agents.yaml` |

---

## Support & Escalation

### Severity Levels

| Level | Description | Response Time | Action |
|-------|-------------|---------------|--------|
| **P1 - Critical** | System down, funds at risk | Immediate | Emergency stop + investigate |
| **P2 - High** | Auto-pause triggered | <15 min | Review logs + decide on resume |
| **P3 - Medium** | Performance degradation | <1 hour | Monitor + optimize |
| **P4 - Low** | Cosmetic issues | <24 hours | Log for future fix |

### Contact Information

- **GitHub Issues**: https://github.com/I-Onlabs/SIGMAX/issues
- **Documentation**: `/home/user/SIGMAX/docs/`
- **Logs**: `/home/user/SIGMAX/logs/`

---

**End of Operational Runbook**
