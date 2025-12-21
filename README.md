# SIGMAX

**Autonomous Multi-Agent AI Crypto Trading Operating System**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-blue.svg)](https://reactjs.org/)

> ⚠️ **EDUCATIONAL USE ONLY** - See [Disclaimer](#-disclaimer) before use

---

## What is SIGMAX?

SIGMAX is an **open-source, autonomous AI trading system** that combines multi-agent intelligence, quantum optimization, and advanced risk management for cryptocurrency trading.

### Key Highlights

🤖 **Multi-Agent Debate** - Bull vs Bear agents with researcher arbitration
⚛️ **Quantum Optimization** - VQE/QAOA portfolio optimization with Qiskit
🛡️ **Safety-First** - Auto-pause triggers, two-man rule, zero-trust architecture
🎨 **Neural Cockpit** - 3D visualization with React + Three.js
🔊 **Multiple Interfaces** - Telegram, Web UI, CLI, Python/TypeScript SDKs
💯 **100% Local** - No cloud dependencies, full control

---

## Quick Start

### Prerequisites

- **OS:** macOS 13+ or Linux (Ubuntu 22.04+)
- **RAM:** 16GB minimum
- **Tools:** Docker/Podman, Node.js 20+, Python 3.11+, Rust 1.75+

### One-Command Deploy

```bash
git clone https://github.com/I-Onlabs/SIGMAX.git
cd SIGMAX
bash deploy.sh
```

This will:
1. Install dependencies
2. Start backend services (Podman)
3. Launch UI at `http://localhost:3000`
4. Build macOS .app (if on macOS)
5. Open setup wizard

### Manual Setup

<details>
<summary>Click to expand manual installation steps</summary>

```bash
# 1. Backend
cd core
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Frontend
cd ../ui/web
npm install

# 3. Environment
cp .env.example .env
# Edit .env with your API keys

# 4. Services
podman-compose up -d

# 5. Start UI
npm run dev

# 6. Start orchestrator
cd ../../core
python main.py
```

</details>

---

## For Different Users

<table>
<tr>
<th>🎯 I want to...</th>
<th>📖 Start here</th>
</tr>
<tr>
<td><strong>Trade crypto with AI</strong></td>
<td>
<code>bash deploy.sh</code> → Use Telegram bot<br/>
See <a href="#telegram-bot-commands">Telegram Commands</a>
</td>
</tr>
<tr>
<td><strong>Build apps on SIGMAX</strong></td>
<td>
Install SDK: <code>pip install sigmax-sdk</code><br/>
See <a href="docs/SDK_OVERVIEW.md">SDK Guide</a>
</td>
</tr>
<tr>
<td><strong>Automate trading ops</strong></td>
<td>
Use CLI: <code>sigmax analyze BTC/USDT</code><br/>
See <a href="docs/CLI.md">CLI Guide</a>
</td>
</tr>
<tr>
<td><strong>Research AI trading</strong></td>
<td>
Read <a href="docs/ARCHITECTURE.md">Architecture</a><br/>
See <a href="docs/ENHANCEMENTS_SUMMARY.md">Enhancements</a>
</td>
</tr>
<tr>
<td><strong>Contribute code</strong></td>
<td>
Fork repo → Read <a href="CONTRIBUTING.md">Contributing</a><br/>
Join <a href="https://discord.gg/sigmax">Discord</a>
</td>
</tr>
</table>

---

## Features

### 🧠 Multi-Agent Intelligence

```
┌─────────────┐
│  Planner    │  Creates structured plan
└──────┬──────┘
       ▼
┌──────────────┐
│ Researcher   │  Executes tasks in parallel (1.8-2.4x speedup)
└──────┬───────┘
       ▼
┌──────────────┐
│  Validator   │  4D quality checks, re-research if needed
└──────┬───────┘
       ▼
┌──────────────┐
│ Fundamental  │  On-chain metrics + financial ratios
└──────┬───────┘
       ▼
┌──────────────┐
│ Bull vs Bear │  Informed debate
│    Debate    │
└──────┬───────┘
       ▼
┌─────────────────┐
│ Risk + Privacy  │  Final safety check
└─────────────────┘
```

**Specialized Agents:**
- **Sentiment** - Multi-source aggregation (news, social, on-chain)
- **Technical** - ML ensemble (XGBoost, LightGBM, Random Forest)
- **Fundamentals** - P/F, MC/TVL, NVT, token velocity
- **Risk** - Exposure monitoring, auto-pause triggers
- **Arbitrage** - 50+ DEX/CEX scanning
- **Privacy** - PII detection, anti-collusion
- **Compliance** - EU AI Act + SEC compliant

### ⚛️ Quantum Computing

- **Portfolio Optimization** - VQE + QAOA algorithms
- **Hot-starting** - Faster convergence
- **Real-time Visualization** - Live circuit rendering
- **Classical Hybrid** - Graceful fallback

### 📊 Advanced Trading

- **Freqtrade Integration** - Paper + Live trading
- **HFT Support** - LEAN engine integration
- **Multi-Chain** - BTC, ETH, Solana, Base, Arbitrum, Polygon
- **MEV Shield** - Anti-sandwich, anti-frontrun
- **Backtesting** - Sharpe/Sortino, max drawdown, walk-forward

### 🛡️ Safety & Compliance

**Risk Caps (Configurable):**
- Max Exposure: $50 total
- Position Size: $10-15 per trade
- Stop Loss: -1.5% per trade
- Daily Loss Limit: $10

**Auto-Pause Triggers:**
- 3 consecutive losses
- API error burst (>5 errors/min)
- Sentiment drop (<-0.3)
- MEV attack (slippage >1%)

**Two-Man Rule:**
Critical actions require confirmation:
- Leverage increase
- Risk cap removal
- Emergency withdraw

**Audit Trail:**
- ZK-SNARK proofs for every decision
- Daily snapshots via Telegram
- Weekly PDF tearsheets

### 🎨 Neural Cockpit UI

- **3D Agent Swarm** - Live agent activity visualization
- **Quantum Circuit Viewer** - Interactive simulator
- **Latency Waterfall** - Microsecond performance tracking
- **Performance Charts** - Real-time PnL, win rate, Sharpe ratio
- **Voice Commands** - Natural language control
- **macOS Native** - Tauri .app (6MB installer)

---

## Usage

### Telegram Bot Commands

```bash
/status                   # Current PnL, open trades
/start balanced           # Start with balanced risk profile
/pause 2h                 # Pause for 2 hours
/resume                   # Resume trading
/panic                    # Emergency stop + close all
/why BTC/USDT            # Explain last BTC decision
/quantum portfolio        # Show quantum optimization
/agents                   # Show agent debate history
```

### CLI

```bash
# Install with CLI support
pip install -e ".[cli]"

# Configure API access
sigmax config set api_key YOUR_API_KEY

# Analyze trading pairs
sigmax analyze BTC/USDT --risk balanced

# Check system status
sigmax status

# Create and manage proposals
sigmax propose ETH/USDT --size 1000
sigmax approve PROP-abc123
sigmax execute PROP-abc123

# Interactive shell mode
sigmax shell
```

**[📖 Full CLI Documentation](docs/CLI.md)**

### Python SDK

```bash
pip install sigmax-sdk
```

```python
from sigmax_sdk import SigmaxClient, RiskProfile, TradeMode

async with SigmaxClient(api_url="http://localhost:8000") as client:
    # Get system status
    status = await client.get_status()

    # Streaming analysis (SSE)
    async for event in client.analyze_stream("BTC/USDT"):
        print(f"[{event['status']}] {event.get('message', '')}")
        if event.get('final'):
            break

    # Synchronous analysis
    result = await client.analyze("ETH/USDT", RiskProfile.BALANCED)

    # Trading workflow
    proposal = await client.propose_trade("BTC/USDT", mode=TradeMode.PAPER, size=0.1)
    await client.approve_proposal(proposal.proposal_id)
    await client.execute_proposal(proposal.proposal_id)
```

**[📖 Python SDK Documentation](sdk/python/README.md)**

### TypeScript SDK

```bash
npm install @sigmax/sdk
```

```typescript
import { SigmaxClient, RiskProfile, TradeMode } from '@sigmax/sdk';

const client = new SigmaxClient({
  apiUrl: 'http://localhost:8000'
});

// Get system status
const status = await client.getStatus();

// Streaming analysis (SSE)
for await (const event of client.analyzeStream('BTC/USDT')) {
  console.log(`[${event.status}] ${event.message || ''}`);
  if (event.final) break;
}

// Synchronous analysis
const result = await client.analyze('ETH/USDT', RiskProfile.BALANCED);

// Trading workflow
const proposal = await client.proposeTrade('BTC/USDT', {
  mode: TradeMode.PAPER,
  size: 0.1
});
await client.approveProposal(proposal.proposalId);
await client.executeProposal(proposal.proposalId);
```

**[📖 TypeScript SDK Documentation](sdk/typescript/README.md)**

### Web API

```bash
# Streaming analysis (SSE)
curl -N -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message":"Analyze BTC","symbol":"BTC/USDT"}' \
  http://localhost:8000/api/chat/stream

# Trade proposals
curl -X POST -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC/USDT"}' \
  http://localhost:8000/api/chat/proposals

# List proposals
curl -H "Authorization: Bearer $API_KEY" \
  http://localhost:8000/api/chat/proposals

# Approve proposal
curl -X POST -H "Authorization: Bearer $API_KEY" \
  http://localhost:8000/api/chat/proposals/PROP-123/approve

# Execute proposal
curl -X POST -H "Authorization: Bearer $API_KEY" \
  http://localhost:8000/api/chat/proposals/PROP-123/execute
```

---

## Architecture

```
SIGMAX/
├── core/                   # Multi-agent orchestrator
│   ├── main.py            # Main entry point
│   ├── agents/            # Specialized AI agents
│   ├── modules/           # Trading, quantum, arbitrage
│   └── interfaces/        # Multi-channel contracts
├── trading/               # Trading engines
│   ├── freqtrade/        # Main bot
│   └── lean/             # HFT backup
├── ui/                    # Neural Cockpit
│   ├── web/              # React frontend
│   ├── desktop/          # Tauri wrapper
│   └── api/              # FastAPI backend
├── infra/                 # Deployment
│   ├── podman-compose.yml
│   └── prometheus/
└── docs/                  # Documentation
```

### Multi-Channel Support

SIGMAX supports multiple interfaces feeding the same orchestrator:

| Interface | Status | Use Case |
|-----------|--------|----------|
| **Telegram Bot** | ✅ Production | Natural language control |
| **Web UI** | ✅ Production | 3D visualization |
| **Web API** | ✅ Production | REST + SSE streaming |
| **CLI** | ✅ Production | Automation/scripting ([docs](docs/CLI.md)) |
| **Python SDK** | ✅ Available | Programmatic access ([docs](sdk/python/README.md)) |
| **TypeScript SDK** | ✅ Available | Web/Node.js integration ([docs](sdk/typescript/README.md)) |
| **WebSocket** | ✅ Available | Real-time bidirectional ([docs](docs/WEBSOCKET.md)) |

See [Interface Enhancement Plan](docs/INTERFACE_ENHANCEMENT_PLAN.md) for details.

---

## Documentation

### Getting Started
- [Quickstart Guide](docs/QUICKSTART.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

### Architecture & Design
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Agent Design](docs/AGENTS.md) *(coming soon)*
- [Safety & Risk Management](docs/SAFETY.md)
- [Quantum Integration](docs/QUANTUM.md) *(coming soon)*

### Enhancements
- [Complete Enhancement Summary](docs/ENHANCEMENTS_SUMMARY.md)
- [Phase 1: Validation](docs/PHASE1_VALIDATION.md)
- [Phase 2: Planning System](docs/PHASE2_PLANNING.md)
- [Phase 3: Fundamental Analysis](docs/PHASE3_FUNDAMENTALS.md)
- [Integration Testing](docs/INTEGRATION_TESTING.md)

### API & Development
- [API Reference](docs/API_REFERENCE.md)
- [CLI Guide](docs/CLI.md)
- [SDK Overview](docs/SDK_OVERVIEW.md)
- [Python SDK](sdk/python/README.md)
- [TypeScript SDK](sdk/typescript/README.md)
- [WebSocket Protocol](docs/WEBSOCKET.md)
- [Contributing Guide](CONTRIBUTING.md)

---

## Testing

### Backtesting

```bash
# Run 1-year backtest
python core/main.py --backtest --start 2024-01-01 --end 2024-12-31

# Generate report
python core/main.py --report --output reports/2024.pdf
```

### Safety Tests

```bash
# All safety tests
pytest tests/safety/ -v

# Specific tests
pytest tests/safety/test_risk_limits.py
pytest tests/safety/test_mev_protection.py
pytest tests/safety/test_policy_validator.py
```

### Load Testing

```bash
locust -f tests/load/locustfile.py --host http://localhost:8000
```

---

## Roadmap

### ✅ Phase 0: Paper Trading + Enhancements (Complete)
- Multi-agent orchestrator
- Freqtrade integration
- Quantum optimizer
- Telegram bot
- Enhancement phases 1-3 (validation, planning, fundamentals)

### ✅ Phase 1: Multi-Interface (Complete)
- ✅ CLI interface
- ✅ Python SDK (sigmax-sdk v1.0.0)
- ✅ TypeScript SDK (@sigmax/sdk v1.0.0)
- ✅ WebSocket support
- ✅ Enhanced documentation

### 🔲 Phase 2: Live Trading ($50 cap)
- Live BTC/USDT only
- Real-time monitoring
- MEV protection
- Two-man rule enforcement

### 🔲 Phase 3: Multi-Asset
- Add ETH, SOL, ARB, BASE
- Memecoin scanner
- Leverage 2x (with safety)
- Advanced arbitrage

### 🔲 Phase 4: Community (Q2 2025)
- Multi-user support
- Strategy marketplace
- Mobile app
- Cloud deployment option
- DAO governance

---

## Performance

### System Metrics
- **Latency:** <30ms agent decision
- **UI FPS:** 60fps (3D swarm)
- **Memory:** ~4GB RAM usage
- **CPU:** ~15% idle, ~40% active

### Backtested Results
Run `python core/main.py --backtest` to generate performance metrics.

---

## Configuration

### Environment Variables

```bash
# Trading
EXCHANGE=binance
API_KEY=your_key
API_SECRET=your_secret
TESTNET=true

# LLM (Optional - uses Ollama by default)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=your_id

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
```

See [.env.example](.env.example) for full configuration.

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Pre-commit hooks
pre-commit install

# Run tests
pytest

# Lint
ruff check .
mypy core/

# Format
black core/ ui/api/
```

---

## License

MIT License - See [LICENSE](LICENSE) for details.

### Third-Party Licenses
- Freqtrade: GPL-3.0
- Qiskit: Apache 2.0
- React: MIT
- Tauri: MIT/Apache 2.0

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

## Acknowledgments

Built with: [Freqtrade](https://www.freqtrade.io/) • [Qiskit](https://qiskit.org/) • [LangChain](https://www.langchain.com/) • [Tauri](https://tauri.app/) • [React](https://reactjs.org/) • [Three.js](https://threejs.org/)

Inspired by: Soly_AI • FinRobot • AutoGPT • Metagpt

---

## Support

- **Issues:** [GitHub Issues](https://github.com/I-Onlabs/SIGMAX/issues)
- **Discussions:** [GitHub Discussions](https://github.com/I-Onlabs/SIGMAX/discussions)
- **Discord:** [Join Community](https://discord.gg/sigmax) *(coming soon)*

---

<div align="center">

**Built with ❤️ by the SIGMAX Community**

[⭐ Star us on GitHub](https://github.com/I-Onlabs/SIGMAX) | [📖 Read the Docs](docs/ARCHITECTURE.md)

</div>
