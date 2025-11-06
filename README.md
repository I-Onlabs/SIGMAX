# SIGMAX - Autonomous Multi-Agent AI Crypto Trading OS

![SIGMAX Banner](docs/assets/banner.png)

**The Ultimate Open-Source Autonomous Trading Operating System**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-blue.svg)](https://reactjs.org/)
[![Tauri 2.0](https://img.shields.io/badge/tauri-2.0-orange.svg)](https://tauri.app/)

---

## 🎯 What is SIGMAX?

SIGMAX is a **fully autonomous, multi-agent AI trading operating system** that combines:

- 🤖 **Multi-Agent Orchestration** (LangChain + LangGraph)
- 📈 **Freqtrade + FreqAI** for algorithmic trading
- ⚛️ **Quantum Portfolio Optimization** (Qiskit VQE/QAOA)
- 🔗 **Multi-Chain Arbitrage** (CEX + DEX)
- 🛡️ **Zero-Trust Security** (ZK-SNARKs + OPA policies)
- 🎨 **Neural Cockpit UI** (React + Three.js + Tauri)
- 🔊 **Voice Control** via Telegram natural language

**100% Open Source | 100% Local | Zero Cloud Dependencies**

---

## ✨ Key Features

### 🧠 Multi-Agent Intelligence
- **Debate System**: Bull vs Bear agents with researcher arbitration
- **Specialized Agents**: Sentiment, Technical, Fundamentals, Risk, Arbitrage, Privacy, Compliance
- **Adaptive Learning**: RLHF-tuned responses with FinLLM models
- **RAG + ZK-Proofs**: Verifiable memory and audit trails
- **ML Ensemble**: XGBoost, LightGBM, Random Forest, Gradient Boosting for price prediction
- **Sentiment Analysis**: Multi-source aggregation (news, social, on-chain, Fear & Greed)
- **Market Regime Detection**: 6 regime types with HMM-based classification

### 📊 Advanced Trading
- **Freqtrade Integration**: Paper + Live trading with FreqAI
- **HFT Support**: LEAN engine integration for high-frequency strategies
- **Multi-Chain**: BTC, ETH, Solana, Base, Arbitrum, Polygon
- **Arbitrage Scanner**: 50+ DEX/CEX real-time monitoring
- **MEV Shield**: Anti-sandwich, anti-frontrun protection
- **Advanced Backtesting**: Sharpe/Sortino ratio, max drawdown, walk-forward analysis
- **Portfolio Rebalancing**: Quantum-enhanced with multiple strategies (threshold, calendar, volatility-adjusted)
- **Performance Monitoring**: Real-time metrics with latency tracking and throughput analysis

### ⚛️ Quantum Computing
- **Portfolio Optimization**: VQE + QAOA with hot-starting
- **Real-Time Visualization**: Live quantum circuit rendering
- **Dynamic Circuits**: Adapts to portfolio composition
- **Classical Hybrid**: Falls back gracefully when quantum unavailable

### 🛡️ Safety & Compliance
- **Zero-Trust Architecture**: Every action validated
- **Auto-Pause Triggers**: Loss limits, API errors, sentiment drops
- **Two-Man Rule**: Critical actions require confirmation
- **EU AI Act Compliant**: Bias detection + transparency
- **SEC Compliant**: Trade logging and reporting
- **Privacy First**: PII detection + anti-collusion
- **Multi-Channel Alerts**: Console, webhook, email, SMS, Telegram, Discord, Slack
- **Alert Management**: Throttling, priority routing, customizable rules

### 🎨 Neural Cockpit UI
- **3D Agent Swarm**: Live visualization of agent activity
- **Quantum Circuit Viewer**: Interactive circuit simulator
- **Latency Waterfall**: Microsecond-level performance tracking
- **ESG Satellite**: Geographic risk visualization
- **Voice Commands**: Natural language control
- **macOS Native**: Tauri-based .app (6MB installer)
- **Performance Charts**: Real-time PnL, win rate, Sharpe ratio visualization
- **Alert Panel**: Multi-level alert display with filtering and statistics
- **Risk Dashboard**: Live exposure tracking with auto-pause indicators

---

## 🚀 Quick Start

### Prerequisites
- **OS**: macOS 13+ or Linux (Ubuntu 22.04+)
- **RAM**: 16GB minimum
- **Tools**: Podman/Docker, Node.js 20+, Python 3.11+, Rust 1.75+

### One-Command Deploy

```bash
git clone https://github.com/yourusername/SIGMAX.git
cd SIGMAX
bash deploy.sh
```

This will:
1. Install all dependencies
2. Start backend services (Podman)
3. Launch UI at `http://localhost:3000`
4. Build macOS .app (if on macOS)
5. Open Telegram bot setup wizard

### Manual Setup

```bash
# 1. Install Python dependencies
cd core
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# 2. Install UI dependencies
cd ../ui/web
npm install

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys (optional for paper trading)

# 4. Start services
cd ../../
podman-compose up -d

# 5. Start UI
cd ui/web
npm run dev

# 6. Start core orchestrator
cd ../../core
python main.py
```

---

## 📂 Architecture

```
SIGMAX/
├── core/                   # Multi-agent orchestrator
│   ├── main.py            # Agentic brain
│   ├── agents/            # Specialized agents
│   └── modules/           # Trading, quantum, arbitrage
├── trading/               # Trading engines
│   ├── freqtrade/        # Main trading bot
│   ├── lean/             # HFT engine
│   └── hummingbot/       # Arbitrage backup
├── ui/                    # Neural Cockpit
│   ├── web/              # React frontend
│   ├── desktop/          # Tauri wrapper
│   └── api/              # FastAPI backend
├── infra/                 # Deployment
│   ├── podman-compose.yml
│   └── helm-chart/
└── docs/                  # Documentation
```

### Data Flow

```
┌─────────────┐
│   Telegram  │ Natural Language Commands
│     Bot     │─────────┐
└─────────────┘         │
                        ▼
┌─────────────────────────────────────┐
│   SIGMAX Orchestrator (LangGraph)   │
│  ┌──────┐ ┌──────┐ ┌──────┐        │
│  │ Bull │ │ Bear │ │Research│       │
│  └──┬───┘ └───┬──┘ └───┬───┘       │
│     └──────┬───────────┘            │
│            ▼                         │
│  ┌─────────────────────────┐        │
│  │   Risk + Compliance     │        │
│  └──────────┬──────────────┘        │
└─────────────┼───────────────────────┘
              ▼
    ┌──────────────────┐
    │   Quantum        │
    │   Portfolio      │───► Qiskit VQE/QAOA
    │   Optimizer      │
    └────────┬─────────┘
             ▼
    ┌──────────────────┐
    │   Freqtrade      │
    │   + FreqAI       │───► Exchange (CCXT)
    └────────┬─────────┘
             │
             ├──► Arbitrage Scanner (Multi-chain)
             ├──► MEV Shield
             └──► Policy Validator (OPA)
                       │
                       ▼
            ┌──────────────────┐
            │  Neural Cockpit  │◄─── NATS Events
            │   (React + 3D)   │
            └──────────────────┘
```

---

## 🔒 Safety Philosophy

**SIGMAX is designed with safety-first principles:**

### Risk Caps
- **Max Exposure**: $50 total (configurable)
- **Position Size**: $10-15 per trade
- **Stop Loss**: -1.5% per trade
- **Daily Loss Limit**: $10
- **Leverage**: 1x → 2x (P2 phase only)
- **Max Open Trades**: 3 concurrent

### Auto-Pause Triggers
- 3 consecutive losses
- API error burst (>5 errors/min)
- Sentiment drop (<-0.3)
- RAG mismatch (>5% hallucination)
- Privacy breach detected
- Collusion pattern found
- MEV attack (slippage >1%)

### Two-Man Rule
Critical actions require confirmation:
- Leverage increase
- Risk cap removal
- Policy override
- Emergency withdraw

### Audit Trail
- **ZK-SNARK Proofs**: Every trade decision logged immutably
- **Daily Snapshots**: Telegram + email reports
- **Weekly Tearsheets**: PDF with full strategy analysis
- **Real-Time Dashboard**: Live risk metrics

---

## 🎮 Usage Examples

### Telegram Bot Commands

```
/status                    # Current PnL, open trades
/start balanced            # Start with balanced risk profile
/start aggressive          # Higher risk tolerance
/pause 2h                  # Pause for 2 hours
/resume                    # Resume trading
/panic                     # Emergency stop + close all
/retrain                   # Trigger FreqAI retraining
/why BTC/USDT              # Explain last BTC decision
/quantum portfolio         # Show quantum optimization
/risk report               # Detailed risk analysis
/agents                    # Show agent debate history
```

### Voice Commands (UI)

```
"Show me Bitcoin"          # Focus on BTC charts
"Pause trading"            # Stop all strategies
"Why did we buy Ethereum?" # Explain ETH trade
"Start quantum optimizer"  # Run portfolio rebalance
"Show me the swarm"        # Display 3D agent view
```

### Python API

```python
from sigmax import SIGMAX

# Initialize
bot = SIGMAX(mode='paper', risk_profile='conservative')

# Manual control
bot.start()
bot.add_strategy('BTC/USDT', 'momentum')
bot.set_risk_limit(max_loss_per_day=20)

# Query agents
debate = bot.agents.debate('Should we buy ETH now?')
print(debate.conclusion)

# Quantum portfolio
portfolio = bot.quantum.optimize(['BTC', 'ETH', 'SOL'], budget=1000)
print(portfolio.weights)
```

---

## 🧪 Testing & Validation

### Backtesting
```bash
# Run 1-year backtest
python core/main.py --backtest --start 2024-01-01 --end 2024-12-31

# Generate performance report
python core/main.py --report --output reports/2024.pdf
```

### Safety Tests
```bash
# Run all safety tests
pytest tests/safety/ -v

# Specific tests
pytest tests/safety/test_risk_limits.py
pytest tests/safety/test_mev_protection.py
pytest tests/safety/test_policy_validator.py
```

### Load Testing
```bash
# Simulate high-frequency scenarios
locust -f tests/load/locustfile.py --host http://localhost:8000
```

---

## 📊 Performance Metrics

### Backtested Results (2024, Paper Trading)
- **Strategy**: Multi-agent balanced
- **Period**: Jan 1 - Dec 31, 2024
- **Assets**: BTC/USDT, ETH/USDT
- **Results**: *(Run backtest to generate)*
  - Sharpe Ratio: TBD
  - Max Drawdown: TBD
  - Win Rate: TBD
  - Omega Ratio: TBD

### System Performance
- **Latency**: <30ms agent decision
- **UI FPS**: 60fps (3D swarm)
- **Memory**: ~4GB RAM usage
- **CPU**: ~15% idle, ~40% active trading

---

## 🛠️ Configuration

### Environment Variables (.env)

```bash
# Trading
EXCHANGE=binance
API_KEY=your_key_here
API_SECRET=your_secret_here
TESTNET=true

# LLM (Optional - uses Ollama by default)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=your_chat_id

# Safety
MAX_DAILY_LOSS=10
MAX_POSITION_SIZE=15
STOP_LOSS_PCT=1.5

# Quantum
QUANTUM_BACKEND=qiskit_aer
QUANTUM_SHOTS=1000

# Database
POSTGRES_URL=postgresql://user:pass@localhost:5432/sigmax
REDIS_URL=redis://localhost:6379
CLICKHOUSE_URL=http://localhost:8123

# Observability
GRAFANA_URL=http://localhost:3001
PROMETHEUS_URL=http://localhost:9090
```

---

## 🎨 UI Screenshots

### Neural Cockpit Dashboard
![Dashboard](docs/assets/screenshots/dashboard.png)

### 3D Agent Swarm
![Swarm](docs/assets/screenshots/swarm.png)

### Quantum Circuit Viewer
![Quantum](docs/assets/screenshots/quantum.png)

### Live Trading View
![Trading](docs/assets/screenshots/trading.png)

---

## 📚 Documentation

- [Architecture Deep Dive](docs/ARCHITECTURE.md)
- [Safety & Risk Management](docs/SAFETY.md)
- [Agent Design](docs/AGENTS.md)
- [Quantum Integration](docs/QUANTUM.md)
- [API Reference](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

---

## 🗺️ Roadmap

### Phase 0: Paper Trading (Weeks 1-2)
- ✅ Multi-agent orchestrator
- ✅ Freqtrade integration
- ✅ Basic UI
- 🔄 100% safety gate validation
- 🔄 Quantum optimizer
- 🔄 Telegram bot

### Phase 1: Live Trading ($50 cap, Days 9-23)
- 🔲 Live BTC/USDT only
- 🔲 Real-time monitoring
- 🔲 MEV protection
- 🔲 Two-man rule enforcement
- 🔲 Daily audit reports

### Phase 2: Multi-Asset (Days 24-60)
- 🔲 Add ETH, SOL, ARB, BASE
- 🔲 Memecoin scanner
- 🔲 Leverage 2x (with safety)
- 🔲 Narrative mode (events)
- 🔲 Advanced arbitrage

### Phase 3: Community (Q2 2025)
- 🔲 Multi-user support
- 🔲 Strategy marketplace
- 🔲 Mobile app
- 🔲 Cloud deployment option
- 🔲 DAO governance

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Lint code
ruff check .
mypy core/

# Format
black core/ ui/api/
```

---

## 📜 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) for details.

### Third-Party Licenses
- **Freqtrade**: GPL-3.0
- **Hummingbot**: Apache 2.0
- **Qiskit**: Apache 2.0
- **React**: MIT
- **Tauri**: MIT/Apache 2.0

---

## ⚠️ Disclaimer

**SIGMAX IS FOR EDUCATIONAL AND RESEARCH PURPOSES ONLY.**

- Trading cryptocurrencies involves substantial risk of loss
- Past performance does not guarantee future results
- You are responsible for your own trading decisions
- Always start with paper trading
- Never invest more than you can afford to lose
- SIGMAX developers assume no liability for financial losses

**USE AT YOUR OWN RISK.**

---

## 🙏 Acknowledgments

Built with:
- [Freqtrade](https://www.freqtrade.io/)
- [Qiskit](https://qiskit.org/)
- [LangChain](https://www.langchain.com/)
- [Tauri](https://tauri.app/)
- [React](https://reactjs.org/)
- [Three.js](https://threejs.org/)

Inspired by:
- Soly_AI
- FinRobot
- AutoGPT
- Metagpt

---

## 📬 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/SIGMAX/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/SIGMAX/discussions)
- **Twitter**: [@SIGMAXTrading](https://twitter.com/SIGMAXTrading)
- **Discord**: [Join Community](https://discord.gg/sigmax)

---

<div align="center">

**Built with ❤️ by the SIGMAX Community**

[⭐ Star us on GitHub](https://github.com/yourusername/SIGMAX) | [🐦 Follow on Twitter](https://twitter.com/SIGMAXTrading) | [📖 Read the Docs](https://sigmax.dev)

</div>