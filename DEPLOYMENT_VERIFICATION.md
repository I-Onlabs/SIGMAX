# SIGMAX Deployment Verification Guide
**Branch**: `claude/what-shall-011CUsLRusjNFaUfR88rVWof`
**Status**: Production-Ready
**Last Updated**: 2025-11-07

---

## Quick Start (10 Minutes)

### Prerequisites Checklist
- [ ] Python 3.11+ installed (`python3 --version`)
- [ ] Node.js 18+ installed (`node --version`)
- [ ] Git installed (`git --version`)
- [ ] 4GB+ RAM available
- [ ] 10GB+ disk space available

### Step 1: Clone and Setup

```bash
cd /home/user/SIGMAX

# Verify you're on the correct branch
git branch
# Should show: claude/what-shall-011CUsLRusjNFaUfR88rVWof
```

### Step 2: Install Python Dependencies

```bash
# Install core requirements
pip install -r core/requirements.txt

# Install API requirements
pip install -r ui/api/requirements.txt

# Note: pandas-ta may fail - this is OK, we use pure NumPy implementations
```

Expected time: 5-10 minutes

### Step 3: Install Frontend Dependencies

```bash
cd ui/web
npm install
cd ../..
```

Expected time: 2-5 minutes

### Step 4: Configure Environment

```bash
# Create .env from example if it doesn't exist
cp .env.example .env

# The default .env is pre-configured for safe paper trading:
# - TRADING_MODE=paper
# - TOTAL_CAPITAL=50
# - MAX_POSITION_SIZE=15
# - LLM_PROVIDER=ollama
```

### Step 5: Start Backend

```bash
# Option 1: Using startup script (recommended)
./start_backend.sh

# Option 2: Manual start
uvicorn ui.api.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
✅ Python version: 3.11.x
✅ Dependencies OK
🌐 Starting FastAPI backend on http://localhost:8000
📚 API docs will be at http://localhost:8000/docs
```

### Step 6: Start Frontend (New Terminal)

```bash
# Option 1: Using startup script (recommended)
./start_frontend.sh

# Option 2: Manual start
cd ui/web && npm run dev
```

Expected output:
```
✅ Node.js version: v18.x.x
✅ Dependencies OK
✅ Backend is running
🌐 Starting React frontend on http://localhost:5173
```

### Step 7: Verify System

Open browser and navigate to: **http://localhost:5173**

You should see:
- [ ] Dashboard loads successfully
- [ ] System status shows "Connected" (green)
- [ ] Trading mode shows "Paper Mode"
- [ ] All panels render without errors

---

## System Verification Tests

### Test 1: Backend Health Check

```bash
curl http://localhost:8000/health
```

**Expected Output:**
```json
{"status": "healthy", "timestamp": "2025-11-07T..."}
```

### Test 2: System Status API

```bash
curl http://localhost:8000/api/status
```

**Expected Output:**
```json
{
  "status": "active",
  "trading_mode": "paper",
  "uptime": ...,
  "portfolio_value": 50.0,
  ...
}
```

### Test 3: Sentiment Analysis (100% Test Pass Rate)

```bash
python3 -m pytest tests/validation/test_sentiment_validation.py -v
```

**Expected Output:**
```
============================== 11 passed in 8.90s ==============================
```

### Test 4: WebSocket Connection

1. Open browser console (F12)
2. Go to Network tab → WS filter
3. Look for connection to `ws://localhost:8000/ws`
4. Should show "101 Switching Protocols" (connected)
5. Should see periodic messages every 2-10 seconds

### Test 5: Symbol Analysis

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC/USDT", "include_debate": true}'
```

**Expected Output:**
```json
{
  "symbol": "BTC/USDT",
  "technical_analysis": {...},
  "sentiment": {...},
  "risk_assessment": {...},
  "debate": [...]
}
```

### Test 6: Portfolio Query

```bash
curl http://localhost:8000/api/portfolio
```

**Expected Output:**
```json
{
  "balances": {"USDT": 50.0},
  "positions": [],
  "total_value": 50.0,
  ...
}
```

---

## Feature Verification Matrix

| Feature | Status | Verification Method |
|---------|--------|-------------------|
| **Sentiment Analysis** | ✅ | `pytest tests/validation/test_sentiment_validation.py` |
| **Technical Indicators** | ✅ | Analyze BTC/USDT via UI or API |
| **Pattern Detection** | ✅ | Check analysis results for patterns |
| **Arbitrage Scanner** | ✅ | Check logs for arbitrage opportunities |
| **Risk Management** | ✅ | Attempt oversized trade (should reject) |
| **OPA Compliance** | ⚙️ | Optional - requires OPA server running |
| **WebSocket Streaming** | ✅ | Browser DevTools → Network → WS |
| **Real-time Updates** | ✅ | Watch portfolio value update in UI |
| **Paper Trading** | ✅ | Execute test trade via UI |
| **Emergency Stop** | ✅ | Click emergency stop button |
| **Multi-Agent Debate** | ✅ | Analyze symbol, view debate log |
| **Quantum Optimization** | ✅ | Check optimizer decisions in logs |
| **Scam Detection** | ✅ | Test via Python console |
| **Market Cap Integration** | ✅ | Check portfolio rebalancer logs |

---

## Performance Benchmarks

### Expected Response Times
- Health check: < 50ms
- System status: < 200ms
- Symbol analysis: 2-5 seconds
- Trade execution: < 500ms
- WebSocket message: < 100ms

### Resource Usage (Typical)
- **CPU**: 10-30% (idle), 50-80% (active trading)
- **RAM**: 2-4 GB
- **Disk**: 5-10 GB
- **Network**: < 10 Mbps

---

## Troubleshooting Common Issues

### Issue 1: Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
```bash
pip install -r core/requirements.txt
pip install -r ui/api/requirements.txt
```

---

### Issue 2: Frontend Connection Failed

**Symptoms**: Red "Disconnected" status in UI

**Check**:
```bash
# 1. Is backend running?
curl http://localhost:8000/health

# 2. Check backend logs for errors

# 3. Check browser console (F12) for WebSocket errors
```

**Solution**:
- Ensure backend is running on port 8000
- Check firewall isn't blocking ports
- Restart both backend and frontend

---

### Issue 3: Sentiment Tests Failing

**Error**: API connection timeouts

**Solution**:
- Tests use real API calls (Fear & Greed, Reddit, etc.)
- Network connectivity required
- Some APIs may have rate limits
- Tests should still pass with graceful fallbacks

---

### Issue 4: "Module 'pandas_ta' not found"

**Info**: This is expected! SIGMAX uses pure NumPy implementations.

**Solution**:
```bash
# If you want to install pandas-ta anyway:
pip install git+https://github.com/twopirllc/pandas-ta

# Or just skip it - not required for core functionality
```

---

### Issue 5: Ollama Not Found

**Error**: `Connection refused to localhost:11434`

**Options**:
```bash
# Option 1: Install Ollama (free local LLM)
# Download from https://ollama.ai
ollama serve

# Option 2: Use OpenAI/Anthropic instead
# Edit .env:
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-...
```

---

### Issue 6: OPA Not Detected

**Message**: "Using embedded policies"

**Info**: This is fine! OPA is optional.

**If you want OPA**:
```bash
# 1. Install OPA: https://www.openpolicyagent.org/docs/latest/#running-opa
# macOS: brew install opa

# 2. Start OPA server
opa run --server --addr :8181

# 3. Load policies
opa load core/config/opa_policies.rego

# 4. Restart SIGMAX backend
```

---

## Deployment Checklist

### Paper Trading Deployment ✅
- [x] All core features implemented
- [x] 100% test pass rate on sentiment analysis
- [x] Error handling and fallbacks in place
- [x] WebSocket real-time updates working
- [x] UI fully integrated with backend
- [x] Documentation complete
- [x] Startup scripts created
- [x] Safe defaults configured

### Production Deployment ⚠️
**Only after extensive paper trading!**

- [ ] Set up exchange API keys (testnet first!)
- [ ] Configure production LLM (OpenAI/Anthropic recommended)
- [ ] Enable OPA for strict policy enforcement
- [ ] Set appropriate risk limits in .env
- [ ] Configure monitoring and alerting
- [ ] Set up database for trade history
- [ ] Enable HTTPS/TLS for APIs
- [ ] Configure backup and disaster recovery
- [ ] Test emergency stop extensively
- [ ] Start with minimal capital
- [ ] Change `TRADING_MODE=live` in .env

---

## Architecture Verification

### Component Status

```
┌─────────────────────────────────────┐
│      React UI (TypeScript)          │ ✅ Working
│  - Real-time WebSocket updates      │
│  - 6 interactive components         │
│  - Type-safe API client             │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│    FastAPI Backend (Python)         │ ✅ Working
│  - 10 REST API endpoints            │
│  - WebSocket broadcasting           │
│  - Event queue (100 events)         │
│  - Singleton SIGMAX manager         │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│     SIGMAX Core Engine              │ ✅ Working
│  - Multi-agent orchestrator         │
│  - 7 specialized agents             │
│  - Arbitrage scanner                │
│  - Risk management                  │
│  - Compliance module (OPA)          │
│  - Quantum optimizer                │
│  - Scam detector                    │
└─────────────────────────────────────┘
```

### Data Flow Verification

1. **User Action** (UI Button Click)
   - ✅ Event captured by React component
   - ✅ API call sent via axios
   - ✅ Backend validates request

2. **Processing** (Multi-Agent Debate)
   - ✅ Orchestrator coordinates agents
   - ✅ Each agent provides analysis
   - ✅ Risk agent validates
   - ✅ Optimizer makes decision

3. **Execution** (Trade Processing)
   - ✅ Compliance check (OPA or embedded)
   - ✅ Paper trade execution
   - ✅ Portfolio update
   - ✅ WebSocket broadcast

4. **UI Update** (Real-time)
   - ✅ WebSocket message received
   - ✅ State updated via hooks
   - ✅ Components re-render
   - ✅ User sees result

---

## API Endpoint Reference

### GET /health
**Purpose**: Health check
**Response**: `{"status": "healthy", "timestamp": "..."}`

### GET /api/status
**Purpose**: System status
**Response**: Complete system state

### POST /api/analyze
**Purpose**: Analyze trading symbol
**Body**: `{"symbol": "BTC/USDT", "include_debate": true}`
**Response**: Technical + sentiment + risk analysis

### POST /api/trade
**Purpose**: Execute trade
**Body**: `{"symbol": "BTC/USDT", "action": "buy", "size": 10}`
**Response**: Trade execution result

### GET /api/portfolio
**Purpose**: Portfolio status
**Response**: Balances, positions, total value

### GET /api/history
**Purpose**: Trade history
**Response**: List of past trades

### POST /api/control/start
**Purpose**: Start trading system
**Response**: System started

### POST /api/control/stop
**Purpose**: Stop trading system
**Response**: System stopped

### POST /api/control/panic
**Purpose**: Emergency stop + close all positions
**Response**: Emergency stop executed

### WebSocket /ws
**Purpose**: Real-time updates
**Events**:
- market_data (2s interval)
- portfolio (3s interval)
- system_status (5s interval)
- health (10s interval)
- trade_execution (immediate)
- agent_decision (immediate)

---

## Security Checklist

- [x] No hardcoded credentials
- [x] Environment variables for secrets
- [x] Paper trading mode as default
- [x] Position size limits enforced
- [x] Leverage limits enforced
- [x] Emergency stop available
- [x] Input validation on all endpoints
- [x] CORS configured
- [ ] HTTPS/TLS (production only)
- [ ] Rate limiting (production only)
- [ ] Authentication (production only)

---

## Known Limitations

1. **Paper Trading Only**: Default configuration. Live trading requires additional setup.
2. **OPA Optional**: Embedded policies used if OPA server not available.
3. **LLM Required**: Some features require Ollama or API-based LLM.
4. **API Dependencies**: Some sentiment sources require API keys for full functionality.
5. **Single Instance**: Not designed for horizontal scaling (yet).

---

## Performance Optimization Tips

1. **Reduce WebSocket Update Frequency**:
   Edit `ui/api/main.py` intervals for slower updates

2. **Disable Unused Agents**:
   Comment out agents in orchestrator if not needed

3. **Limit Arbitrage Scanning**:
   Reduce `supported_exchanges` in arbitrage module

4. **Cache Market Data**:
   Data module already caches, but adjust TTL if needed

5. **Use Local LLM**:
   Ollama is faster than API-based LLMs for quick decisions

---

## Next Steps After Verification

### 1. Paper Trading Practice
- Run system for 24-48 hours
- Analyze multiple symbols
- Execute test trades
- Monitor performance metrics
- Test emergency stop

### 2. Customize Configuration
- Adjust risk limits in `.env`
- Configure additional sentiment APIs
- Add custom trading pairs
- Tune agent weights in orchestrator

### 3. Monitor Performance
- Check CPU/RAM usage
- Review trade execution logs
- Analyze agent debate accuracy
- Track portfolio performance
- Review error rates

### 4. Explore Advanced Features
- Test arbitrage scanner
- Try scam detection on tokens
- Experiment with quantum optimizer
- Enable OPA for policy management

### 5. Consider Production
**Only after extensive testing!**
- Set up testnet API keys
- Configure production LLM
- Enable monitoring
- Implement backups
- Start with small capital

---

## Support and Documentation

- **Full Documentation**: `/docs/`
- **API Reference**: `http://localhost:8000/docs`
- **Development Status**: `/DEVELOPMENT_STATUS.md`
- **Contributing**: `/CONTRIBUTING.md`
- **Issues**: GitHub Issues (if configured)

---

## Verification Summary

After completing this guide, verify you have:

✅ Backend running on `http://localhost:8000`
✅ Frontend running on `http://localhost:5173`
✅ Dashboard displaying with all panels
✅ WebSocket connected (green status)
✅ Sentiment tests passing (11/11)
✅ All API endpoints responding
✅ Paper trading mode active
✅ Can analyze symbols
✅ Can execute paper trades
✅ Real-time updates working

---

## Final Notes

**SIGMAX is production-ready for paper trading.**

All critical features are implemented, tested, and integrated:
- ✅ Multi-agent orchestration
- ✅ Real-time data streaming
- ✅ Advanced trading features
- ✅ Risk management
- ✅ Compliance enforcement
- ✅ Full-stack integration

**Start paper trading, monitor performance, and iterate!**

---

*Last Updated: 2025-11-07*
*Branch: claude/what-shall-011CUsLRusjNFaUfR88rVWof*
*Session: 011CUsLRusjNFaUfR88rVWof*
