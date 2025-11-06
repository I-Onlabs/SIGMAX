# SIGMAX Quick Start Guide

Welcome to **SIGMAX** - your autonomous multi-agent AI trading operating system! 🚀

## What Did We Build?

SIGMAX is a **production-ready, open-source autonomous trading platform** that combines:

✅ **Multi-Agent AI System** - Bull/Bear debate with LangGraph orchestration
✅ **Quantum Computing** - Portfolio optimization with Qiskit VQE/QAOA
✅ **Freqtrade Integration** - Professional-grade execution engine
✅ **Neural Cockpit UI** - Futuristic 3D visualization with React + Three.js
✅ **Zero-Trust Security** - Comprehensive safety rails and compliance
✅ **One-Command Deploy** - Get running in minutes

## Repository Structure

```
SIGMAX/
├── core/                    # 🧠 Multi-agent brain
│   ├── agents/             # Bull, Bear, Researcher, etc.
│   ├── modules/            # Trading, Quantum, RL, Arbitrage
│   └── utils/              # Telegram bot, Health checker
├── trading/                # 📈 Freqtrade integration
├── ui/                     # 🎨 Neural Cockpit
│   ├── api/               # FastAPI backend
│   └── web/               # React + Three.js frontend
├── infra/                  # 🐳 Deployment configs
├── docs/                   # 📚 Documentation
└── deploy.sh              # 🚀 One-click deployment
```

## Quick Start (5 minutes)

### 1. Clone and Enter

```bash
git clone <your-repo-url>
cd SIGMAX
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your exchange API keys (optional for paper trading)
```

### 3. Deploy Everything

```bash
bash deploy.sh
```

This will:
- Install all dependencies (Python, Node.js)
- Set up virtual environments
- Start backend services (PostgreSQL, Redis, NATS, Prometheus, Grafana)
- Launch the FastAPI server
- Start the Neural Cockpit UI
- Open your browser automatically

### 4. Access the System

🎨 **Neural Cockpit**: http://localhost:3000
🔌 **API Server**: http://localhost:8000
📊 **API Docs**: http://localhost:8000/docs
📈 **Grafana**: http://localhost:3001 (admin/admin)
🔍 **Prometheus**: http://localhost:9090

## Key Features

### 1. Multi-Agent Debate System

Six specialized agents collaborate to make trading decisions:

- **🔍 Researcher**: Gathers market intelligence from news, social, on-chain
- **🐂 Bull Agent**: Presents bullish case with evidence
- **🐻 Bear Agent**: Counters with bearish arguments and risks
- **📊 Analyzer**: Technical analysis (RSI, MACD, Bollinger Bands)
- **🛡️ Risk Agent**: Validates against policy constraints
- **🔒 Privacy Agent**: Detects PII and collusion patterns

**Watch them debate in real-time** via the Agent Debate Log panel!

### 2. Quantum Portfolio Optimization

Uses **Qiskit VQE/QAOA** algorithms to optimize:
- Portfolio weights across assets
- Risk-adjusted position sizing
- Dynamic rebalancing

**See live quantum circuits** rendering in the UI!

### 3. Neural Cockpit UI

**Futuristic glass-morphic interface** with:
- 🌐 **3D Agent Swarm**: Watch agents orbit and pulse with activity
- ⚛️ **Quantum Circuit Viewer**: Interactive circuit simulation
- 📊 **Real-time Trading Panel**: Analyze any symbol instantly
- 🎙️ **Voice Control**: "Show me Bitcoin" (coming soon)
- 📱 **Responsive Design**: Works on all devices

### 4. Safety-First Architecture

**Zero-Trust Model** with:

✅ Max $50 total capital ($10-15 per position)
✅ -1.5% stop loss per trade
✅ Auto-pause on 3 losses or $10 daily loss
✅ Policy validation (OPA) for every trade
✅ Two-man rule for critical actions
✅ ZK-SNARK audit trails
✅ PII detection and anti-collusion

**You CANNOT lose more than your limits allow.**

### 5. Telegram Bot Control

Natural language control via Telegram:

```
/status               # Check current state
/start balanced       # Start trading with balanced risk
/pause 2h            # Pause for 2 hours
/panic               # Emergency stop
/why BTC/USDT        # Explain last decision
```

## Usage Examples

### Analyze a Symbol

```python
from sigmax import SIGMAX

bot = SIGMAX(mode='paper', risk_profile='conservative')
await bot.initialize()

# Let agents debate
decision = await bot.analyze_symbol('BTC/USDT')
print(f"Decision: {decision['action']}")
print(f"Confidence: {decision['confidence']:.1%}")
print(f"Reasoning: {decision['reasoning']}")
```

### Via UI

1. Open Neural Cockpit at http://localhost:3000
2. Enter symbol (e.g., "BTC/USDT") in Trading Panel
3. Click "Analyze"
4. Watch agents debate in real-time
5. See quantum optimization visualized
6. Get actionable decision with confidence score

### Via Telegram

```
You: Should I buy Bitcoin?
Bot: Analyzing BTC/USDT...

🐂 Bull: Strong momentum, RSI at 65, volume increasing
🐻 Bear: Resistance at $96k, potential pullback
🔍 Researcher: Sentiment score 0.45 (moderately bullish)
📊 Analyzer: MACD bullish crossover
⚛️ Optimizer: Quantum VQE suggests 8% position size

Decision: BUY with 72% confidence
```

## Configuration

### Risk Profiles

**Conservative** (default):
- Max 3 open trades
- $10-15 per position
- -1.5% stop loss
- 1x leverage only

**Balanced**:
- Max 5 open trades
- $15-20 per position
- -2% stop loss
- Up to 2x leverage

**Aggressive**:
- Max 7 open trades
- $20-30 per position
- -3% stop loss
- Up to 3x leverage (requires approval)

### Exchanges Supported

Via CCXT:
- Binance (recommended)
- Coinbase
- Kraken
- Bybit
- OKX
- And 100+ more...

### Assets

**Phase 0 (Paper)**: BTC/USDT only
**Phase 1 (Live $50)**: BTC, ETH
**Phase 2 (Expand)**: SOL, MATIC, ARB, BASE, and memecoins

## Monitoring & Observability

### Grafana Dashboards

Pre-configured dashboards for:
- Trading performance (PnL, win rate, Sharpe)
- Agent activity (debate frequency, decision distribution)
- System health (CPU, memory, latency)
- Risk metrics (exposure, drawdown, consecutive losses)

### Logs

All logs stored in:
- `logs/sigmax.log` - Core orchestrator
- `logs/api.log` - FastAPI server
- `logs/ui.log` - Frontend dev server

### Alerts

Telegram alerts for:
- Trades executed
- Auto-pause triggers
- System errors
- Daily performance summary

## Testing

### Run Unit Tests

```bash
cd core
source venv/bin/activate
pytest tests/ -v
```

### Run Backtests

```bash
python core/main.py --backtest --start 2024-01-01 --end 2024-12-31
```

### Safety Tests

```bash
pytest tests/safety/ -v
```

## Troubleshooting

### Issue: Dependencies won't install

**Solution**: Ensure you have Python 3.11+ and Node 20+
```bash
python --version  # Should be 3.11+
node --version    # Should be 20+
```

### Issue: Podman containers won't start

**Solution**: Try Docker Compose instead
```bash
docker-compose up -d
```

Or skip containers:
```bash
SKIP_CONTAINERS=true bash deploy.sh
```

### Issue: UI won't connect to API

**Solution**: Check if API is running
```bash
curl http://localhost:8000/health
```

If not running, start manually:
```bash
cd ui/api
uvicorn main:app --reload
```

### Issue: Quantum module fails

**Solution**: Quantum is optional. Disable in `.env`:
```bash
QUANTUM_ENABLED=false
```

### Issue: Out of memory

**Solution**: Increase Docker memory or disable heavy features:
```bash
FEATURE_QUANTUM=false
FEATURE_ARBITRAGE=false
```

## Phased Rollout Plan

### Week 1-2: Paper Trading

**Goal**: Validate all safety mechanisms
**Capital**: Virtual $50
**Assets**: BTC/USDT only
**Success**: 100% safety gate triggers work

### Week 3-4: Live $50

**Goal**: Real-world validation
**Capital**: Real $50 (sub-account)
**Assets**: BTC, ETH
**Success**: No losses beyond risk caps

### Week 5-8: Scale Up

**Goal**: Expand proven strategies
**Capital**: Up to $200
**Assets**: Add SOL, MATIC, ARB
**Features**: Narrative trading, arbitrage

## Next Steps

1. ✅ **Review the documentation**
   - [Architecture](docs/ARCHITECTURE.md)
   - [Safety & Risk](docs/SAFETY.md)

2. ✅ **Run in paper mode for 14 days**
   - Validate all safety triggers
   - Review agent debates
   - Check decision quality

3. ✅ **Optimize strategies**
   - Backtest on historical data
   - Tune hyperparameters
   - Compare risk profiles

4. ✅ **Go live (carefully!)**
   - Start with $50 on sub-account
   - Monitor closely for first week
   - Scale only after proven safe

## Contributing

We welcome contributions!

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## License

MIT License - see [LICENSE](LICENSE)

## Support

- 📧 Email: support@sigmax.dev
- 💬 Discord: [Join Community](https://discord.gg/sigmax)
- 🐦 Twitter: [@SIGMAXTrading](https://twitter.com/SIGMAXTrading)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/SIGMAX/issues)

## Disclaimer

⚠️ **TRADING INVOLVES SUBSTANTIAL RISK OF LOSS**

- SIGMAX is for educational and research purposes
- Past performance does NOT guarantee future results
- You are responsible for your own trading decisions
- Never invest more than you can afford to lose
- Always start with paper trading
- SIGMAX developers assume NO liability for losses

**USE AT YOUR OWN RISK**

---

## Ready to Trade?

```bash
bash deploy.sh
```

**Welcome to the future of autonomous trading.** 🚀

*Built with ❤️ by the SIGMAX Community*
