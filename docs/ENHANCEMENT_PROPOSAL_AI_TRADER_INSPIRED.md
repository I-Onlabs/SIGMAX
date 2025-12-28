# SIGMAX Enhancement Proposal: AI-Trader Inspired Improvements

**Date**: December 27, 2024
**Source**: [AI-Trader Research Paper](https://arxiv.org/abs/2512.10971) & [GitHub](https://github.com/HKUDS/AI-Trader)
**Status**: Proposal

---

## Executive Summary

AI-Trader introduces a **live benchmarking framework** for LLM agents in financial markets with key innovations in autonomous operation, anti-look-ahead controls, and multi-model competition. This document proposes enhancements for SIGMAX inspired by their research findings and implementation patterns.

### Key Research Findings

1. **General AI intelligence doesn't guarantee trading capability**
2. **Risk control determines cross-market robustness**
3. **AI generates excess returns more readily in liquid markets** (crypto) vs regulated environments (stocks)
4. **Data contamination is a critical issue** in historical backtesting

---

## Proposed Enhancements

### 1. MCP Toolchain Architecture

**Current SIGMAX**: Direct function calls to trading modules
**AI-Trader Pattern**: Model Context Protocol (MCP) for standardized tool access

#### Proposal: Implement MCP-Based Tool Layer

```python
# Proposed MCP tool configuration
MCP_CONFIG = {
    "analysis": {
        "transport": "streamable_http",
        "url": "http://localhost:8001/mcp",
        "tools": ["analyze_symbol", "get_sentiment", "quantum_optimize"]
    },
    "trading": {
        "transport": "streamable_http",
        "url": "http://localhost:8002/mcp",
        "tools": ["create_proposal", "execute_trade", "close_position"]
    },
    "data": {
        "transport": "streamable_http",
        "url": "http://localhost:8003/mcp",
        "tools": ["get_price", "get_orderbook", "get_history"]
    },
    "search": {
        "transport": "streamable_http",
        "url": "http://localhost:8004/mcp",
        "tools": ["search_news", "get_financials", "search_social"]
    }
}
```

**Benefits**:
- Standardized tool interface across all agents
- Easy integration with LangChain/LangGraph
- Modular service deployment
- Tool versioning and discovery

---

### 2. Live Benchmarking Framework

**Current SIGMAX**: Historical backtesting via Freqtrade
**AI-Trader Pattern**: Live, uncontaminated evaluation in real markets

#### Proposal: Add Live Benchmarking Mode

```python
class LiveBenchmark:
    """
    Live benchmarking framework for uncontaminated AI evaluation.
    """
    def __init__(self, agents: List[BaseAgent], capital: float = 50000):
        self.agents = agents
        self.initial_capital = capital
        self.start_time = datetime.utcnow()

    async def run_competition(self, duration_days: int = 30):
        """Run head-to-head agent competition with identical conditions."""
        for agent in self.agents:
            agent.register_with_capital(self.initial_capital)

        while self.is_running():
            for agent in self.agents:
                await agent.make_autonomous_decision()
            await self.record_metrics()

    def get_leaderboard(self) -> pd.DataFrame:
        """Return ranked performance across all agents."""
        return self.calculate_metrics(['returns', 'sharpe', 'max_drawdown', 'win_rate'])
```

**Key Features**:
- Identical starting conditions for all agents
- Real-time performance dashboard
- No human intervention during competition
- Standardized metrics (Sharpe, drawdown, win rate)

---

### 3. Multi-Model Competition Arena

**Current SIGMAX**: Single orchestrator with Bull/Bear debate
**AI-Trader Pattern**: Multiple independent AI models competing

#### Proposal: Multi-Strategy Arena

SIGMAX already has multi-agent debate (Bull vs Bear). Enhance to support:

1. **Multiple Trading Strategies** (not just Bull/Bear)
   - Momentum Agent
   - Mean Reversion Agent
   - Sentiment Agent
   - Quantum-Optimized Agent

2. **Model Diversity**
   - GPT-4o strategy
   - Claude Opus strategy
   - DeepSeek strategy
   - Qwen strategy
   - Local Ollama strategy

```python
# Configuration example
COMPETITION_CONFIG = {
    "strategies": [
        {"name": "momentum-gpt4", "model": "gpt-4o", "strategy": "momentum"},
        {"name": "sentiment-claude", "model": "claude-3.5-sonnet", "strategy": "sentiment"},
        {"name": "quant-deepseek", "model": "deepseek-chat", "strategy": "quantitative"},
        {"name": "local-llama", "model": "llama3.2:8b", "strategy": "balanced"}
    ],
    "initial_capital": 50000,
    "trading_pairs": ["BTC/USDT", "ETH/USDT"],
    "evaluation_period": "30d"
}
```

**Benefits**:
- Discover which LLM excels at trading
- Ensemble voting for higher confidence
- Cost comparison across models
- Strategy evolution through competition

---

### 4. Anti-Look-Ahead Data Controls

**Current SIGMAX**: Standard backtesting (potential look-ahead bias)
**AI-Trader Pattern**: Strict temporal data boundaries

#### Proposal: Temporal Data Gateway

```python
class TemporalDataGateway:
    """
    Ensures agents can only access data from current simulation time and before.
    Prevents future information leakage in backtesting.
    """

    def __init__(self, simulation_time: datetime):
        self.current_time = simulation_time

    def get_price(self, symbol: str, as_of: datetime = None) -> PriceData:
        """Only return prices up to simulation time."""
        max_time = as_of or self.current_time
        return self.price_service.get_price(symbol, max_time=max_time)

    def search_news(self, query: str) -> List[NewsItem]:
        """Only return news published before simulation time."""
        return self.news_service.search(
            query=query,
            published_before=self.current_time
        )

    def get_financials(self, symbol: str) -> Financials:
        """Only return financial reports published before simulation time."""
        return self.financial_service.get_latest(
            symbol=symbol,
            published_before=self.current_time
        )
```

**Implementation in Historical Replay**:

```python
async def run_historical_simulation(self, start: str, end: str):
    """Run simulation with strict temporal controls."""

    for date in trading_dates(start, end):
        # Set temporal boundary
        self.data_gateway.set_simulation_time(date)

        # Agent can only access data up to this point
        await self.agent.make_decision(
            data_gateway=self.data_gateway  # Restricted access
        )

        # Record with actual next-day prices (for evaluation only)
        self.record_performance(date)
```

---

### 5. Minimal Information Paradigm

**Current SIGMAX**: Agents receive pre-curated market data
**AI-Trader Pattern**: Agents independently search and synthesize information

#### Proposal: Autonomous Information Discovery

Instead of feeding agents pre-processed data, require them to:

1. **Search autonomously** for relevant information
2. **Verify data authenticity**
3. **Synthesize findings** into trading decisions

```python
# Current approach (spoon-fed data)
decision = await agent.decide(
    symbol="BTC/USDT",
    price=current_price,
    sentiment=sentiment_score,
    news=latest_news
)

# Proposed approach (autonomous discovery)
decision = await agent.decide(
    symbol="BTC/USDT",
    tools=[
        SearchTool(),      # Agent must search for news
        PriceTool(),       # Agent must query prices
        SentimentTool(),   # Agent must analyze sentiment
        FinancialsTool()   # Agent must research fundamentals
    ]
)
```

**Benefits**:
- Tests true AI reasoning capability
- Reduces human bias in data selection
- More realistic production behavior
- Better evaluation of agent quality

---

### 6. Hourly Trading Granularity

**Current SIGMAX**: Primarily daily decision cycles
**AI-Trader Pattern**: Supports hourly trading (4 time points/day for stocks)

#### Proposal: Configurable Trading Frequency

```python
class TradingSchedule:
    """Configurable trading frequency."""

    FREQUENCIES = {
        "daily": ["00:00"],
        "4h": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
        "1h": [f"{h:02d}:00" for h in range(24)],
        "15m": [f"{h:02d}:{m:02d}" for h in range(24) for m in [0, 15, 30, 45]],
    }

    def __init__(self, frequency: str = "daily"):
        self.checkpoints = self.FREQUENCIES[frequency]

    def should_trade(self, current_time: datetime) -> bool:
        time_str = current_time.strftime("%H:%M")
        return time_str in self.checkpoints
```

**Benefits**:
- Capture intraday opportunities
- Better for volatile crypto markets
- More granular risk management
- Faster strategy iteration

---

### 7. Unified JSONL Logging Format

**Current SIGMAX**: PostgreSQL + Redis for storage
**AI-Trader Pattern**: JSONL files for trading records

#### Proposal: Hybrid Approach

Keep PostgreSQL for production but add JSONL export for:
- Reproducible research
- Easy data sharing
- Lightweight backtesting
- Agent training datasets

```python
class TradingLogger:
    """Unified logging with multiple backends."""

    async def log_decision(self, decision: Decision):
        # Primary: PostgreSQL (production)
        await self.postgres.insert(decision)

        # Secondary: JSONL (research/backup)
        self.jsonl_writer.write({
            "date": decision.timestamp.isoformat(),
            "symbol": decision.symbol,
            "action": decision.action,
            "amount": decision.amount,
            "reasoning": decision.reasoning,
            "confidence": decision.confidence,
            "agent": decision.agent_id
        })
```

**Standard JSONL Format**:
```json
{"date": "2024-12-27T10:30:00", "symbol": "BTC/USDT", "action": "buy", "amount": 0.1, "reasoning": "Bullish momentum detected...", "confidence": 0.85, "positions": {"BTC": 0.1, "ETH": 0, "USDT": 45000}}
```

---

## Implementation Milestones

### Milestone 1: Foundation
**Goal**: Enable research-quality backtesting

- [ ] Add JSONL logging export alongside PostgreSQL
- [ ] Implement hourly trading schedule support
- [ ] Create temporal data gateway for anti-look-ahead
- [ ] Add data boundary validation in backtesting

### Milestone 2: Agent Enhancement
**Goal**: Improve agent autonomy and diversity

- [ ] Implement minimal information paradigm (agents search autonomously)
- [ ] Add multi-model strategy support (GPT, Claude, DeepSeek, Ollama)
- [ ] Create strategy comparison dashboard
- [ ] Build ensemble voting mechanism

### Milestone 3: Infrastructure
**Goal**: Production-ready competition framework

- [ ] Migrate tool layer to MCP protocol
- [ ] Implement live benchmarking framework
- [ ] Create real-time leaderboard
- [ ] Add agent performance analytics

---

## Comparison Matrix

| Feature | SIGMAX Current | AI-Trader | Proposed |
|---------|---------------|-----------|----------|
| Agent Architecture | Bull/Bear Debate | Multi-Model Competition | Both (Debate + Competition) |
| Optimization | Quantum (VQE/QAOA) | None | Keep Quantum |
| Tool Interface | Direct calls | MCP | Add MCP layer |
| Data Access | Pre-curated | Autonomous search | Add autonomous mode |
| Trading Frequency | Daily | Daily + Hourly | Add hourly |
| Backtesting | Standard | Anti-look-ahead | Add temporal controls |
| Logging | PostgreSQL | JSONL | Hybrid |
| Risk Management | Safety triggers | Basic | Keep SIGMAX approach |
| Live Trading | Phase 6 planned | Live benchmark | Align approaches |

---

## Unique SIGMAX Advantages to Preserve

1. **Quantum Optimization** - AI-Trader lacks this; keep VQE/QAOA
2. **Bull vs Bear Debate** - Novel approach; enhance, don't replace
3. **Safety-First Design** - Auto-pause triggers superior to AI-Trader
4. **Multi-Interface** - CLI, SDK, Telegram, Web - more complete
5. **Risk Caps** - Configurable limits ($50 max exposure) - keep

---

## Next Steps

1. [ ] Review proposal with team
2. [ ] Prioritize enhancements based on Phase 6 requirements
3. [ ] Create detailed technical specs for top priorities
4. [ ] Prototype MCP toolchain integration
5. [ ] Design live benchmarking dashboard

---

## References

- Fan, Tianyu et al. "AI-Trader: Benchmarking Autonomous Agents in Real-Time Financial Markets." arXiv:2512.10971 (2025)
- [AI-Trader GitHub Repository](https://github.com/HKUDS/AI-Trader)
- [Model Context Protocol](https://github.com/modelcontextprotocol)
- [LangChain MCP Adapters](https://github.com/langchain-ai/langchain-mcp-adapters)
