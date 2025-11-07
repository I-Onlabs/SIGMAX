# FinRobot + RD-Agent Integration

## Overview

SIGMAX now integrates with two powerful AI agent frameworks for autonomous strategy evolution:

- **FinRobot**: AI4Finance Foundation's financial agent platform for market analysis, risk assessment, and portfolio optimization
- **RD-Agent**: Microsoft's research & development automation for autonomous strategy evolution

## Features

### FinRobot Capabilities
- **Market Analysis**: Advanced market condition analysis with specialized financial agents
- **Risk Assessment**: Comprehensive risk evaluation and recommendations
- **Portfolio Optimization**: Intelligent portfolio allocation and rebalancing
- **Strategy Generation**: AI-powered trading strategy creation

### RD-Agent Capabilities
- **Strategy Evolution**: Autonomous improvement of trading strategies based on performance
- **Strategy Research**: Discovery and evaluation of new trading approaches
- **Backtesting**: Automated strategy validation and scoring
- **Continuous Learning**: Self-improving strategies through iterative refinement

## Architecture

```
SIGMAX Orchestrator
├── Standard Agents (LangGraph)
│   ├── Researcher Agent
│   ├── Analyzer Agent
│   ├── Optimizer Agent
│   ├── Risk Agent
│   └── Privacy Agent
│
└── Autonomous Strategy Engine (Optional)
    ├── FinRobot Wrapper
    │   ├── Market Analyst
    │   ├── Financial Analyst
    │   ├── Risk Assessor
    │   ├── Portfolio Optimizer
    │   └── Strategy Generator
    │
    └── RD-Agent Wrapper
        ├── Strategy Evolution Loop
        ├── Strategy Researcher
        └── Strategy Evaluator
```

## Installation

### Quick Install (PyPI - In Progress)
```bash
pip install finrobot rdagent
```

### Development Install (From Source)
```bash
# Clone repositories
git clone https://github.com/AI4Finance-Foundation/FinRobot external/FinRobot
git clone https://github.com/microsoft/RD-Agent external/RD-Agent

# Install in editable mode
pip install -e external/FinRobot
pip install -e external/RD-Agent
```

## Configuration

### Enable/Disable

**Via Environment Variables**:
```bash
# Enable both (default)
export FINROBOT_ENABLED=true
export RDAGENT_ENABLED=true

# Disable individually
export FINROBOT_ENABLED=false
export RDAGENT_ENABLED=false
```

**Via Code**:
```python
from core.agents.orchestrator import SIGMAXOrchestrator

# Enable autonomous engine (default)
orchestrator = SIGMAXOrchestrator(
    data_module=data_module,
    execution_module=execution_module,
    # ... other modules
    enable_autonomous_engine=True  # Enable FinRobot + RD-Agent
)

# Disable autonomous engine
orchestrator = SIGMAXOrchestrator(
    # ... modules
    enable_autonomous_engine=False  # Use only standard SIGMAX agents
)
```

### LLM Configuration

FinRobot and RD-Agent use the same LLM configuration as SIGMAX:
```python
# In .env file
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo, etc.

# Or use Ollama
OLLAMA_MODEL=llama2
```

## Usage

### 1. Enhanced Market Analysis

Use FinRobot for advanced market analysis:

```python
# Standard analysis (LangGraph agents)
result = await orchestrator.analyze_symbol("BTCUSDT")

# Enhanced analysis (FinRobot + RD-Agent)
portfolio = {
    "total_value": 100000,
    "positions": [
        {"symbol": "BTCUSDT", "size": 0.5, "value": 50000}
    ]
}

market_data = await data_module.get_market_data("BTCUSDT")

result = await orchestrator.analyze_with_autonomous_engine(
    symbol="BTCUSDT",
    portfolio=portfolio,
    market_data=market_data
)

# Result includes:
# - market_analysis: FinRobot's market assessment
# - risk_assessment: Comprehensive risk evaluation
# - portfolio_optimization: Suggested portfolio changes
# - overall_confidence: Combined confidence score
```

### 2. Strategy Evolution

Use RD-Agent to evolve your trading strategies:

```python
# Define current strategy
current_strategy = {
    "name": "Momentum Strategy",
    "version": 1,
    "entry_criteria": ["RSI > 50", "MACD bullish"],
    "exit_criteria": ["Stop loss: -2%", "Take profit: +5%"],
    "risk_parameters": {
        "max_position_size": 0.1,
        "max_daily_loss": 0.02
    }
}

# Performance history
performance_history = [
    {"return": 0.01, "sharpe": 1.2, "timestamp": "2025-01-01"},
    {"return": 0.02, "sharpe": 1.5, "timestamp": "2025-01-02"},
    {"return": -0.01, "sharpe": 1.1, "timestamp": "2025-01-03"}
]

# Evolve strategy
result = await orchestrator.evolve_strategy(
    current_strategy=current_strategy,
    performance_history=performance_history,
    market_data=market_data
)

# Result includes:
# - evolved_strategy: Improved strategy version
# - evaluation: Performance metrics and viability assessment
```

### 3. Direct Access to Autonomous Engine

```python
# Access the autonomous engine directly
if orchestrator.autonomous_engine:
    # Market analysis
    analysis = await orchestrator.autonomous_engine.finrobot.analyze_market(
        symbol="BTCUSDT",
        context={"timeframe": "1h"}
    )

    # Risk assessment
    risk = await orchestrator.autonomous_engine.finrobot.assess_risk(portfolio)

    # Portfolio optimization
    optimization = await orchestrator.autonomous_engine.finrobot.optimize_portfolio(
        current_portfolio=portfolio,
        market_data=market_data
    )

    # Strategy research
    new_strategies = await orchestrator.autonomous_engine.rdagent.research_new_strategies(
        market_conditions={"volatility": "high"},
        constraints={"max_risk": 0.05}
    )
```

## Fallback Behavior

The integration is designed to gracefully handle missing dependencies:

### When FinRobot/RD-Agent Not Installed
- System falls back to SIGMAX's built-in agent implementations
- All functionality remains available
- Warnings logged but no errors thrown

### When Packages Partially Available
- System uses whatever is available
- Example: If only FinRobot installed, RD-Agent features use fallback

### Check Integration Status
```python
status = await orchestrator.get_status()

print(status["autonomous_engine"])
# Output:
# {
#   "enabled": True,
#   "finrobot": True,  # Using real FinRobot
#   "rdagent": True    # Using real RD-Agent
# }
```

## Testing

### Run Integration Tests
```bash
# Test full integration
pytest tests/test_finrobot_integration.py -v

# Test specific components
pytest tests/test_finrobot_integration.py::TestFinRobotIntegration -v
pytest tests/test_finrobot_integration.py::TestRDAgentIntegration -v
pytest tests/test_finrobot_integration.py::TestAutonomousStrategyEngine -v
```

### Test Results
- ✅ 15/15 tests passing
- ✅ Fallback mode tested and working
- ✅ Integration with orchestrator verified

## Performance Considerations

### Memory Usage
- FinRobot agents: ~200-500MB per agent
- RD-Agent: ~500MB-1GB depending on strategy complexity
- Recommendation: Minimum 8GB RAM for full integration

### Latency
- FinRobot analysis: 2-5 seconds per request
- RD-Agent strategy evolution: 10-60 seconds depending on complexity
- Recommendation: Use asynchronous calls for parallel processing

### Cost (LLM API)
- FinRobot market analysis: ~2,000-5,000 tokens per request
- RD-Agent strategy evolution: ~10,000-50,000 tokens per evolution
- Recommendation: Use GPT-3.5-turbo for development, GPT-4 for production

## Troubleshooting

### Issue: "FinRobot not available"
**Solution**: Install dependencies
```bash
pip install finrobot
# Or from source
pip install -e external/FinRobot
```

### Issue: "RD-Agent not available"
**Solution**: Install dependencies
```bash
pip install rdagent
# Or from source
pip install -e external/RD-Agent
```

### Issue: "No module named 'finnhub'"
**Solution**: Install FinRobot data source dependencies
```bash
pip install finnhub-python yfinance mplfinance
```

### Issue: "No module named 'pydantic_settings'"
**Solution**: Install RD-Agent dependencies
```bash
pip install pydantic-settings
```

### Issue: Slow performance
**Solution**:
1. Use smaller LLM model (e.g., GPT-3.5-turbo)
2. Reduce max_iterations in strategy evolution
3. Cache market data to avoid redundant API calls

## Advanced Configuration

### Custom FinRobot Agents

```python
from core.agents.finrobot_integration import FinRobotAgentWrapper

# Initialize with custom model
wrapper = FinRobotAgentWrapper(model="gpt-3.5-turbo")

# Add custom agent
wrapper.agents["custom_agent"] = {
    "name": "Custom Analyst",
    "role": "Specialized analysis for crypto derivatives",
    "model": "gpt-4"
}
```

### Custom RD-Agent Evolution Strategy

```python
from core.agents.finrobot_integration import RDAgentWrapper

wrapper = RDAgentWrapper()

# Configure evolution parameters
result = await wrapper.evolve_strategy(
    current_strategy=strategy,
    performance_metrics={
        "min_sharpe": 1.5,  # Minimum acceptable Sharpe ratio
        "max_drawdown": 0.15,  # Maximum acceptable drawdown
        "target_return": 0.20   # Target annual return
    },
    market_data=market_data
)
```

## References

- [FinRobot Documentation](https://github.com/AI4Finance-Foundation/FinRobot)
- [FinRobot Paper](https://arxiv.org/abs/2405.14767)
- [RD-Agent Documentation](https://github.com/microsoft/RD-Agent)
- [RD-Agent Tech Report](https://aka.ms/RD-Agent-Tech-Report)
- [SIGMAX Documentation](../README.md)

## Support

For issues specific to:
- **FinRobot**: Report at https://github.com/AI4Finance-Foundation/FinRobot/issues
- **RD-Agent**: Report at https://github.com/microsoft/RD-Agent/issues
- **SIGMAX Integration**: Report at SIGMAX repository issues

## License

- FinRobot: MIT License
- RD-Agent: MIT License
- SIGMAX: See main repository LICENSE
