# SIGMAX Quick Start Guide
**Get up and running in 10 minutes!**

---

## 📋 Prerequisites

### Required
- **Python 3.11+** - `python3 --version`
- **Node.js 18+** - `node --version`
- **npm or yarn** - Package manager

### Recommended (Optional)
- **Ollama** - Local LLM inference (free)
  - Install: https://ollama.ai
  - Run: `ollama pull llama3.1`
- **OPA** - Policy-as-code engine (optional)
  - Install: https://www.openpolicyagent.org/docs/latest/#running-opa
- **Docker** - For containerized deployment (optional)

---

## 🚀 Quick Start (Paper Trading)

### Step 1: Install Dependencies

```bash
# Backend dependencies
cd /home/user/SIGMAX
pip install -r core/requirements.txt

# Note: If pandas-ta fails, it's okay - we use pure NumPy implementations
# You can skip it: pip install $(grep -v pandas-ta core/requirements.txt)

# API dependencies
pip install -r ui/api/requirements.txt

# Frontend dependencies
cd ui/web
npm install
```

### Step 2: Configuration

The `.env` file has been created with safe defaults for paper trading:

```bash
# Already configured in .env:
TRADING_MODE=paper          # Safe paper trading
TOTAL_CAPITAL=50            # Virtual $50 starting capital
MAX_POSITION_SIZE=15        # Max $15 per position
LLM_PROVIDER=ollama         # Free local LLM (requires Ollama installed)
```

**Optional API Keys** (enhance functionality but not required):

```bash
# Get free API keys (optional):
NEWSAPI_KEY=                # https://newsapi.org (free tier)
GOLDRUSH_API_KEY=           # https://goldrush.dev (free tier)

# Fear & Greed Index - No key required ✓
# Reddit API - No key required ✓
# CoinGecko - No key required ✓
# DexScreener - No key required ✓
# Honeypot.is - No key required ✓
```

### Step 3: Start Ollama (Recommended)

```bash
# Install Ollama from https://ollama.ai
# Then pull the model:
ollama pull llama3.1

# Start Ollama (runs on localhost:11434 by default)
# It will auto-start on macOS/Linux
```

**Alternative**: Use OpenAI or Anthropic by setting in `.env`:
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

### Step 4: Start the Backend

```bash
cd /home/user/SIGMAX

# Start FastAPI backend (with auto-reload)
uvicorn ui.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend will be running at**: `http://localhost:8000`

**API Documentation**: `http://localhost:8000/docs`

### Step 5: Start the Frontend

Open a **new terminal**:

```bash
cd /home/user/SIGMAX/ui/web

# Start React development server
npm run dev
```

**Frontend will be running at**: `http://localhost:5173`

### Step 6: Open Dashboard

Visit **http://localhost:5173** in your browser!

You should see:
- ✅ System status panel
- ✅ Real-time market data
- ✅ Trading panel
- ✅ Performance chart
- ✅ Risk dashboard
- ✅ Agent debate log
- ✅ Alert panel

---

## 🎮 Using the Dashboard

### 1. System Status
- **Connection Status**: Green = WebSocket connected
- **Trading Mode**: Shows "Paper Mode"
- **System Health**: CPU, Memory, Disk usage

### 2. Quick Actions

**Start Trading:**
1. Click "Start Trading" button
2. System initializes all agents
3. Status changes to "Trading Active"

**Analyze a Symbol:**
1. Enter symbol (e.g., BTC/USDT)
2. Click "Analyze"
3. View multi-agent debate results
4. See technical indicators and patterns

**Execute Trade** (Paper Mode):
1. Enter symbol and amount
2. Select Buy or Sell
3. Click "Execute Trade"
4. See trade in Alert Panel

**Emergency Stop:**
1. Click "Emergency Stop"
2. Confirm in dialog
3. All positions closed immediately

### 3. Monitoring

- **Performance Chart**: Live portfolio value (last 100 updates)
- **Risk Dashboard**: Exposure, PnL, open positions
- **Agent Debate Log**: Multi-agent decision process
- **Alert Panel**: Trade executions and notifications

---

## 🧪 Testing the System

### Test 1: Sentiment Analysis

```bash
# In Python console:
cd /home/user/SIGMAX
python3

>>> import asyncio
>>> from core.agents.sentiment import SentimentAgent
>>>
>>> agent = SentimentAgent(None)
>>> await agent.initialize()
>>> result = await agent.analyze("BTC")
>>> print(result)
```

**Expected**: Sentiment scores from Fear & Greed Index, Reddit, etc.

### Test 2: Technical Analysis

```python
>>> from core.agents.analyzer import AnalyzerAgent
>>>
>>> analyzer = AnalyzerAgent(None, None)
>>> market_data = {
>>>     "price": 45000,
>>>     "prices": [44000, 44500, 45000, 45200, 45100],
>>>     "volumes": [1000000, 1100000, 1050000, 980000, 1020000]
>>> }
>>> result = await analyzer.analyze("BTC/USDT", market_data)
>>> print(result['indicators'])
>>> print(result['patterns'])
```

**Expected**: RSI, MACD, Bollinger Bands, detected patterns

### Test 3: Scam Checker

```python
>>> from core.utils.scam_checker import ScamChecker
>>>
>>> checker = ScamChecker()
>>> # Example with known safe token (USDC on Ethereum)
>>> result = await checker.check(
>>>     "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
>>>     "ethereum"
>>> )
>>> print(f"Risk Score: {result['risk_score']}")
>>> print(f"Recommendation: {result['recommendation']}")
```

**Expected**: Low risk score, "SAFE" recommendation

### Test 4: API Endpoints

```bash
# System status
curl http://localhost:8000/api/status

# Analyze symbol
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC/USDT", "include_debate": true}'

# Portfolio status
curl http://localhost:8000/api/portfolio
```

---

## 📊 Understanding the Output

### Agent Debate Format

When you analyze a symbol, you'll see a multi-agent debate:

```
🔍 RESEARCHER:
  "Gathering market intelligence for BTC/USDT..."
  [News sentiment, social signals, on-chain metrics]

📈 BULL AGENT:
  "Positive factors: Strong uptrend, increasing volume..."
  Confidence: 75%

📉 BEAR AGENT:
  "Risk factors: Overbought RSI, resistance at $46k..."
  Confidence: 60%

📊 ANALYZER:
  RSI: 72.3 (Overbought)
  MACD: Bullish
  Patterns: Ascending Triangle (Bullish)

🛡️ RISK AGENT:
  Risk Level: Medium
  Volatility: 45% (Medium)
  Liquidity: Very High
  APPROVED ✓

⚛️ OPTIMIZER:
  Recommended action: BUY
  Position size: $12.50 (25% of max)
  Quantum confidence: 0.78
```

### Trade Execution Flow

```
1. User clicks "Execute Trade"
   ↓
2. Compliance check (OPA policies)
   ↓
3. Risk validation (size, leverage, blacklist)
   ↓
4. Paper trade execution
   ↓
5. Portfolio update
   ↓
6. WebSocket broadcast to UI
   ↓
7. Alert displayed in Alert Panel
```

---

## 🔧 Advanced Configuration

### Enable OPA (Policy-as-Code)

```bash
# 1. Install OPA
# macOS: brew install opa
# Linux: https://www.openpolicyagent.org/docs/latest/#running-opa

# 2. Start OPA server
opa run --server --addr :8181

# 3. Load SIGMAX policies
opa load core/config/opa_policies.rego

# 4. OPA is now running!
# SIGMAX will auto-detect and use it
```

**Benefits**:
- Centralized policy management
- Real-time policy updates
- Compliance audit trails
- No code changes for policy updates

### Enable Additional APIs

**NewsAPI** (crypto news sentiment):
```bash
# Get free key: https://newsapi.org
NEWSAPI_KEY=your_key_here
```

**GoldRush** (on-chain metrics):
```bash
# Get free key: https://goldrush.dev
GOLDRUSH_API_KEY=your_key_here
```

### Adjust Risk Profiles

Edit `.env`:
```bash
# Conservative (default)
MAX_POSITION_SIZE=15
MAX_LEVERAGE=1
MAX_DAILY_LOSS=10

# Balanced
MAX_POSITION_SIZE=25
MAX_LEVERAGE=2
MAX_DAILY_LOSS=15

# Aggressive (not recommended for beginners)
MAX_POSITION_SIZE=40
MAX_LEVERAGE=3
MAX_DAILY_LOSS=25
```

---

## 🐛 Troubleshooting

### Backend won't start

**Error**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
```bash
pip install -r core/requirements.txt
pip install -r ui/api/requirements.txt
```

### Frontend won't start

**Error**: `npm ERR! code ENOENT`

**Solution**:
```bash
cd ui/web
npm install
npm run dev
```

### "Connection Failed" in UI

**Issue**: WebSocket not connecting

**Solution**:
1. Check backend is running: `http://localhost:8000/health`
2. Check no firewall blocking port 8000
3. Check browser console for errors

### Ollama not found

**Error**: `Connection refused to localhost:11434`

**Solution**:
```bash
# Install Ollama: https://ollama.ai
# Start Ollama (auto-starts on most systems)
ollama serve

# Alternative: Use OpenAI/Anthropic instead
# Edit .env: LLM_PROVIDER=openai
```

### No market data

**Issue**: Empty charts, no prices

**Explanation**: Paper mode uses simulated data by default

**Solution**: Wait 2-5 seconds for WebSocket broadcasts to populate

### OPA not detected

**Issue**: "Using embedded policies" in logs

**Check**:
```bash
# Is OPA running?
curl http://localhost:8181/health

# Start OPA if not running
opa run --server --addr :8181
```

---

## 📈 Next Steps After Quick Start

### 1. Paper Trading Practice

- Start the system and let it run for a few hours
- Analyze various symbols (BTC/USDT, ETH/USDT, SOL/USDT)
- Execute some paper trades
- Monitor performance metrics
- Test emergency stop functionality

### 2. Explore Advanced Features

**Arbitrage Scanner**:
```python
from core.modules.arbitrage import ArbitrageModule

arb = ArbitrageModule(min_profit_percentage=0.5)
await arb.initialize()
opportunities = await arb.scan_opportunities()
```

**Scam Detection**:
```python
from core.utils.scam_checker import ScamChecker

checker = ScamChecker()
result = await checker.check("0x...", "ethereum")
```

**Quantum Portfolio Optimization**:
- Available in optimizer agent
- Uses Qiskit for portfolio allocation
- Integrated into trading decisions

### 3. Monitor Performance

- Track portfolio value over time
- Analyze win/loss ratio
- Review agent debate accuracy
- Check risk metrics (Sharpe ratio, drawdown)

### 4. Customize Strategies

**Edit Risk Limits**: `.env` file
**Edit Policies**: `core/config/opa_policies.rego`
**Add Indicators**: `core/agents/analyzer.py`
**Add Sentiment Sources**: `core/agents/sentiment.py`

### 5. Production Deployment (When Ready)

⚠️ **Only after extensive paper trading!**

1. Set up exchange API keys (testnet first!)
2. Change `TRADING_MODE=live` in `.env`
3. Start with small position sizes
4. Monitor closely
5. Use stop-losses
6. Enable OPA for strict policy enforcement

---

## 📚 Additional Resources

- **Full Documentation**: `/docs/`
- **API Reference**: `http://localhost:8000/docs`
- **Development Status**: `/DEVELOPMENT_STATUS.md`
- **Troubleshooting**: `/docs/TROUBLESHOOTING.md`
- **Architecture**: `/docs/ARCHITECTURE.md`

---

## 🆘 Getting Help

**Logs Location**:
```bash
# Backend logs (in terminal where you ran uvicorn)
# Frontend logs (browser console: F12)
# System logs: core/logs/ (if configured)
```

**Common Commands**:
```bash
# Check system health
curl http://localhost:8000/health

# View WebSocket events (in browser console)
# F12 → Network → WS → Select connection → Messages

# Check Ollama
curl http://localhost:11434/api/tags

# Check OPA
curl http://localhost:8181/health
```

---

## ✅ Verification Checklist

After completing this guide, you should have:

- [x] Backend running on `http://localhost:8000`
- [x] Frontend running on `http://localhost:5173`
- [x] Dashboard displaying with real-time updates
- [x] "Connected" status in header (green dot)
- [x] Paper trading mode active
- [x] Ollama running (or alternative LLM configured)
- [x] Able to analyze symbols
- [x] Able to execute paper trades
- [x] WebSocket receiving updates every 2-10 seconds

---

## 🎉 You're Ready!

SIGMAX is now running in paper trading mode. You can:

- ✅ Analyze any crypto symbol
- ✅ See multi-agent debates
- ✅ Execute paper trades
- ✅ Monitor performance in real-time
- ✅ Test arbitrage detection
- ✅ Check tokens for scams
- ✅ View technical indicators and patterns

**Happy Trading!** 🚀

---

*For issues or questions, check `/docs/TROUBLESHOOTING.md` or review the logs.*
