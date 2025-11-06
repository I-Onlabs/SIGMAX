# SIGMAX - Algorithmic Crypto Trading Bot

A modular, event-driven algorithmic trading bot for cryptocurrency markets with zero legal risk (permissive OSS licenses only).

## 🎯 Purpose

SIGMAX is a personal, open-source trading bot designed for:
- **Primary**: Low-latency CEX market making and arbitrage with strict safety
- **Secondary**: Strategy research and swing trading via Backtrader/QuantConnect LEAN
- **Future**: Extensible DEX support (Solana, Orderly Network)

## ⚡ Performance SLOs

- **Tick-to-Trade Latency**: p50 ≤ 10ms, p99 ≤ 20ms (Profile A)
- **Risk Gate Latency**: p99 ≤ 100µs
- **Replay Determinism**: Near-zero drift in nightly replays
- **Observability**: Nanosecond-precision timestamps across pipeline

## 🏗️ Architecture

### Event-Driven Pipeline

```
Market Feeds → Ingestion → Order Books → Features → Signals
                                              ↓
                                          Decision Layer
                                          (L0-L5 Hybrid)
                                              ↓
                                          Risk Engine
                                              ↓
                                        Smart Router
                                              ↓
                                      Execution Gateway
                                              ↓
                                      Fills & Positions
```

### Core Components

- **apps/ingest_cex**: CCXT-based market data ingestion with gap recovery
- **apps/book_shard**: Single-writer L2 order books
- **apps/features**: Micro-window metrics (microprice, spread, imbalance, RV)
- **apps/signals/**: Pluggable signals (volatility, news, listings, social)
- **apps/decision**: Hybrid "LLM under control" (L0-L5 layers)
- **apps/risk**: Pre-trade risk checks with reason codes
- **apps/router**: Smart order router with rate-limiting
- **apps/exec_cex**: Async CEX execution via CCXT
- **apps/obs**: Prometheus/eBPF/Kibana observability suite
- **apps/replay**: Deterministic replay and backtesting

## 🔧 Tech Stack (Permissive Licenses)

- **Timing**: ntpd-rs (MIT/Apache 2.0)
- **IPC**: ZeroMQ (MIT) / Aeron (Apache 2.0)
- **Python**: uvloop, orjson, pysimdjson (MIT/Apache 2.0)
- **Execution**: CCXT, asyncio-ccxt (MIT)
- **ML/AI**: Scikit-learn, LightGBM, RLlib (Apache 2.0)
- **Research**: Backtrader (MIT), QuantConnect LEAN (Apache 2.0)
- **Databases**: Postgres (BSD), SQLite (Public Domain), ClickHouse (Apache 2.0)
- **Monitoring**: Prometheus, Kibana, Redash (Apache 2.0)
- **Networking**: DPDK (BSD 2-Clause)

## 🚀 Quick Start

### 5-Minute Setup

```bash
# 1. Clone and enter directory
git clone <repo-url>
cd SIGMAX

# 2. Complete setup (using Makefile)
make setup

# 3. Run the trading system!
make run

# Alternative: Manual setup
# docker-compose -f infra/compose/docker-compose.yml up -d
# pip install -r requirements.txt
# python tools/init_database.py --profile=a
# python tools/runner.py --profile=a
```

**See [Quick Start Guide](docs/QUICKSTART.md) for detailed walkthrough.**

### Makefile Commands

```bash
make help              # Show all available commands
make setup             # Complete development setup
make run               # Run trading system
make test              # Run all tests
make health            # Check system health
make benchmark         # Run performance benchmark
make analyze-trades    # Analyze historical trades
make import-dashboards # Import Grafana dashboards
```

### Development Setup

```bash
# Use development docker-compose (includes all services)
docker-compose -f docker-compose.dev.yml up -d

# Or run services individually for debugging
python -m apps.ingest_cex.main --profile=a
python -m apps.book_shard.main --profile=a
python -m apps.features.main --profile=a
```

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- 4GB RAM minimum (128GB recommended for ML models)
- Network connectivity to exchanges (for live trading)

## 📊 Profiles

### Profile A (Simple)
- Pure Python with ZeroMQ IPC
- No LLM, no Rust dependencies
- Rapid prototyping and ease of use
- Target: p99 < 20ms

### Profile B (Performance)
- Aeron/SBE IPC, Rust executor
- LLM enabled, DPDK networking
- Target: p99 < 5ms

## 🗂️ Directory Structure

```
SIGMAX/
  /apps           # Microservices (ingest, book, features, decision, risk, router, exec)
  /pkg            # Shared libraries (schemas, common utils, IPC)
  /db             # Database migrations (Postgres, ClickHouse)
  /infra          # Infrastructure (Docker, Prometheus, Grafana dashboards)
  /profiles       # Profile A/B configurations
  /tests          # Unit, integration, soak tests
  /tools          # Utility scripts (runner, benchmark, health check, trade analysis)
  /examples       # Example strategies (mean reversion, momentum, market making, arbitrage)
  /docs           # Documentation (QUICKSTART, DEPLOYMENT, guides)
```

## 🔐 Security

- **Bindings**: All services on 127.0.0.1
- **Secrets**: SOPS-encrypted files, OS keyring
- **Audit**: WORM hash-chaining in ClickHouse
- **Egress**: Allow-lists on executor processes

## 📈 Implementation Status

### ✅ Completed (Production Ready)

**Core Trading Pipeline:**
- ✅ Market data ingestion (CCXT WebSocket)
- ✅ Single-writer L2 order books
- ✅ Feature extraction engine
- ✅ Pluggable signal modules
- ✅ Hybrid decision layer (L0-L5)
- ✅ Pre-trade risk engine
- ✅ Smart order router
- ✅ CEX execution gateway

**Infrastructure:**
- ✅ Docker & Docker Compose
- ✅ Postgres + ClickHouse databases
- ✅ Prometheus + Grafana monitoring
- ✅ Service orchestration runner
- ✅ Database initialization scripts

**Testing & CI/CD:**
- ✅ Unit test framework (100+ tests)
- ✅ Integration test framework
- ✅ GitHub Actions CI/CD
- ✅ Automated testing pipeline

**Documentation:**
- ✅ Quick Start Guide
- ✅ Deployment Guide (VPS, K8s, systemd)
- ✅ Architecture documentation
- ✅ Comprehensive Contributing Guide

**Monitoring & Observability:**
- ✅ Grafana dashboards (trading metrics, system health)
- ✅ Prometheus metrics integration
- ✅ Performance benchmarking tool
- ✅ System health checker
- ✅ Trade analysis tool

**Examples & Tools:**
- ✅ Example trading strategies (4 strategies)
  - Mean reversion (orderbook imbalance)
  - Momentum (trend following)
  - Market making (dual-sided quoting)
  - Arbitrage (cross-exchange)
- ✅ Enhanced Makefile (30+ commands)
- ✅ Automated dashboard import
- ✅ Development workflow automation

### 🔮 Future Enhancements

- Backtrader/QuantConnect LEAN integration
- DEX support (Solana, Orderly Network)
- ML model training pipeline (L2/L3 layers)
- L4 LLM integration (Claude/Grok)
- eBPF tracing (Profile B)
- DPDK networking (Profile B)
- Deterministic replay service
- Additional strategy examples

## 🧪 Testing

```bash
# Run all tests
make test

# Unit tests only
make test-unit

# Integration tests (1-hour volatile replay)
make test-integration

# Soak tests (6-8 hours)
make test-soak

# Test coverage report
make test-coverage

# Alternative: Direct pytest commands
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/soak/ -v
```

## 📊 Example Strategies

SIGMAX includes 4 complete trading strategy implementations:

### 1. Mean Reversion (`examples/strategies/mean_reversion.py`)
Trades on orderbook imbalance with mean reversion logic
- **Logic**: Strong bid pressure → SELL, Strong ask pressure → BUY
- **Timeframe**: Medium frequency (seconds to minutes)
- **Use case**: Scalping on BTC/USDT during liquid hours

### 2. Momentum (`examples/strategies/momentum.py`)
Trend-following strategy with confirmation
- **Logic**: 3 consecutive price movements → Follow trend
- **Timeframe**: Medium frequency (minutes)
- **Use case**: Catching trending moves on altcoins

### 3. Market Making (`examples/strategies/market_making.py`)
Dual-sided quoting with inventory management
- **Logic**: Quote both sides, adjust spread based on inventory
- **Timeframe**: High frequency (sub-second)
- **Use case**: Providing liquidity, earning bid-ask spread

### 4. Arbitrage (`examples/strategies/arbitrage.py`)
Cross-exchange arbitrage detection
- **Logic**: Buy low on exchange A, sell high on exchange B
- **Timeframe**: Ultra-high frequency (milliseconds)
- **Use case**: Price differences between Binance and Coinbase

**See [Strategy Examples](examples/README.md) for detailed documentation and usage.**

## 🛠️ Utility Tools

```bash
# Performance benchmarking
make benchmark
# Measures tick-to-trade latency, throughput, SLO compliance

# System health monitoring
make health
# Checks all services, databases, resources

# Historical trade analysis
make analyze-trades
# P&L, win rate, Sharpe ratio, strategy breakdown

# Import Grafana dashboards
make import-dashboards
# Automated dashboard import for monitoring
```

## 📝 License

MIT License - See LICENSE file for details.

All dependencies use permissive licenses (MIT, Apache 2.0, BSD-like) to ensure zero legal risk.

## ⚠️ Disclaimer

**This software is for educational and research purposes only. Live trading involves significant financial risk. Not financial advice. Consult professionals before trading.**

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## 📚 Documentation

**Getting Started:**
- **[Quick Start Guide](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment (VPS, K8s, systemd)
- [Architecture Overview](#architecture) - System design and dataflow

**Development:**
- [Contributing Guide](CONTRIBUTING.md) - Comprehensive contributor guide
- [Strategy Examples](examples/README.md) - 4 example trading strategies
- [Makefile Commands](#makefile-commands) - Development workflow automation

**Monitoring:**
- [Grafana Dashboards](infra/prometheus/grafana-dashboards/README.md) - Trading metrics and system health
- Performance Benchmarking - `make benchmark` or `python tools/benchmark.py`
- System Health Checks - `make health` or `python tools/health_check.py`
- Trade Analysis - `make analyze-trades` or `python tools/analyze_trades.py`

**Other:**
- [License](LICENSE) - MIT License details

## 🙏 Acknowledgments

- Inspired by Algo Trade Camp's Python-focused curriculum
- Built on QuantConnect LEAN and Backtrader
- Incorporates 2025 HFT/DeFi best practices