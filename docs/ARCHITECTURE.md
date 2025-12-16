# SIGMAX Architecture

## Overview

SIGMAX is a multi-layer autonomous trading operating system that combines:

- **Agent Layer**: Multi-agent debate system using LangGraph
- **Strategy Layer**: Freqtrade + FreqAI for execution
- **Intelligence Layer**: Quantum computing + RL for optimization
- **Safety Layer**: Zero-trust policy enforcement
- **UI Layer**: Neural Cockpit with 3D visualization

## System Components

### 1. Multi-Agent Orchestrator (LangGraph)

The core brain of SIGMAX, coordinating specialized agents:

```
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
    │   Decision       │
    └──────────────────┘
```

**Agent Roles:**

- **Orchestrator**: Coordinates workflow and synthesizes decisions
- **Researcher**: Gathers market intelligence from news, social, on-chain
- **Bull Agent**: Presents bullish arguments with technical evidence
- **Bear Agent**: Presents bearish arguments and risks
- **Analyzer**: Performs technical analysis (RSI, MACD, etc.)
- **Risk Agent**: Validates against policy constraints
- **Privacy Agent**: Detects PII leakage and collusion
- **Optimizer**: Quantum portfolio optimization

### 2. Data Module

Multi-source data aggregation:

- **Exchange Data**: CCXT for CEX prices and orderbooks
- **Blockchain Data**: Web3 for DEX and on-chain metrics
- **News/Sentiment**: CryptoPanic, NewsAPI, Twitter
- **Economic Data**: Fed policy, DXY, VIX

### 3. Quantum Module (Qiskit)

Portfolio optimization using:

- **VQE (Variational Quantum Eigensolver)**: Portfolio weights
- **QAOA**: Combinatorial optimization
- **Hot-starting**: Classical → Quantum hybrid approach
- **Circuit Visualization**: Real-time SVG rendering

### 4. Execution Module

Trade execution with safety:

- **Paper Trading**: Simulated with mock balance
- **Live Trading**: CCXT integration with real exchanges
- **Risk Limits**: Position size, stop-loss, daily loss caps
- **Order Types**: Market, limit, stop-loss

### 5. Freqtrade Integration

- **Strategy**: `SIGMAXStrategy.py` with technical indicators
- **FreqAI**: Machine learning for signal generation
- **Hyperopt**: Parameter optimization
- **Backtesting**: Historical performance validation

### 6. Neural Cockpit UI

React + Three.js futuristic interface:

- **3D Agent Swarm**: Live visualization of agent activity
- **Quantum Circuit**: Interactive circuit display
- **Trading Panel**: Real-time analysis and execution
- **Agent Debate Log**: Transparent decision-making
- **Voice Control**: Natural language commands (planned)

### 7. Safety & Compliance

Zero-trust architecture:

- **Policy Validator (OPA)**: Rego-based rule enforcement
- **Auto-Pause Triggers**: Loss limits, API errors, sentiment drops
- **Two-Man Rule**: Critical action confirmation
- **ZK-SNARK Audit Trail**: Immutable decision logging
- **PII Detection**: Regex + NLP-based scanning

## Data Flow

```
User Input (Telegram/UI/Web Chat)
         │
         ▼
   Orchestrator
         │
    ┌────┴────┐
    │         │
    ▼         ▼
Researcher  Analyzer
    │         │
    └────┬────┘
         ▼
    Bull/Bear Debate
         │
         ▼
   Risk Validation
         │
         ▼
  Quantum Optimizer
         │
         ▼
    Decision Made
         │
    ┌────┴────┐
    │         │
    ▼         ▼
Execution  Logging
    │         │
    ▼         ▼
Exchange   Database
```

## AI-Centric Chat Interface (Web) & Execution Gating

SIGMAX exposes an AI chat interface via FastAPI that streams **step-level progress** (planner → research → validation → debate → risk) and returns **artifacts** (plans, summaries, risk reports).

Safety model:
- **Preferred**: proposal → approve (optional) → execute
- **Default**: direct trade execution endpoints are gated/disabled unless explicitly enabled


## Technology Stack

| Layer | Technology |
|-------|------------|
| Orchestration | LangChain, LangGraph |
| LLM | Ollama (local), OpenAI (optional) |
| Trading | Freqtrade, CCXT |
| Quantum | Qiskit, Aer Simulator |
| ML/RL | Stable-Baselines3, scikit-learn |
| Database | PostgreSQL, Redis, ClickHouse |
| Message Queue | NATS, Kafka |
| API | FastAPI, WebSockets |
| UI | React, Three.js, Tailwind CSS |
| Desktop | Tauri v2 (macOS .app) |
| Monitoring | Prometheus, Grafana |
| Deployment | Podman, Docker Compose |

## Deployment Architecture

```
┌─────────────────────────────────────┐
│         Load Balancer (Nginx)       │
└─────────────┬───────────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
┌──────┐  ┌──────┐  ┌──────┐
│ UI   │  │ API  │  │ Core │
└──┬───┘  └──┬───┘  └──┬───┘
   │         │         │
   └─────────┼─────────┘
             │
    ┌────────┼────────┐
    │        │        │
    ▼        ▼        ▼
┌──────┐ ┌──────┐ ┌──────┐
│  DB  │ │Cache │ │ MQ   │
└──────┘ └──────┘ └──────┘
```

## Security Model

### Defense in Depth

1. **Input Validation**: All user inputs sanitized
2. **Authentication**: JWT tokens for API access
3. **Authorization**: Role-based access control (RBAC)
4. **Policy Enforcement**: OPA validates every trade
5. **Encryption**: TLS for transit, at-rest encryption for secrets
6. **Audit Logging**: Immutable logs with ZK-SNARKs
7. **Network Isolation**: Container network segmentation

### Risk Management

- **Position Limits**: Max $15 per trade, $50 total
- **Stop Loss**: Automatic -1.5% per trade
- **Daily Loss Cap**: Auto-pause at -$10
- **Leverage Limits**: 1x (paper), 2x (live with approval)
- **Consecutive Loss Trigger**: Pause after 3 losses

## Scalability

### Horizontal Scaling

- **API Servers**: Load-balanced FastAPI instances
- **Agent Workers**: Distributed LangGraph executors
- **Database**: Read replicas for PostgreSQL
- **Cache**: Redis cluster with sharding

### Vertical Scaling

- **CPU**: Multi-core for quantum simulations
- **Memory**: 16GB minimum, 32GB recommended
- **GPU**: Optional for ML training

## Future Enhancements

- [ ] Multi-user support with isolated accounts
- [ ] Strategy marketplace for community strategies
- [ ] Mobile app (React Native)
- [ ] Real quantum hardware integration (IBM Quantum)
- [ ] Advanced narrative trading (news events)
- [ ] Cross-chain DEX aggregator
- [ ] DAO governance for strategy voting
