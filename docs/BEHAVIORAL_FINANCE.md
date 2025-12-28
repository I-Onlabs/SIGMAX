# SIGMAX Behavioral Finance Module

**Inspired by TwinMarket: Realistic agent behavior modeling for market simulation**

## Overview

The SIGMAX Behavioral Finance Module introduces human-like cognitive biases and social dynamics to AI trading agents. This enables:

1. **Realistic Market Simulation** - Agents exhibit behavioral biases
2. **Social Network Effects** - Sentiment propagation and herd behavior
3. **Risk Assessment** - Better understanding of market dynamics
4. **Strategy Testing** - Test against behaviorally-realistic opponents

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  BehavioralAgentWrapper                         │
│  (Wraps any trading agent with behavioral finance layer)       │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────────┐
│ InvestorBelief│   │ BehavioralBias  │   │ SocialSentiment     │
│ (Persona)     │   │ Engine          │   │ Network             │
│               │   │                 │   │                     │
│ - Risk level  │   │ - Disposition   │   │ - Follow graph      │
│ - Confidence  │   │ - Loss aversion │   │ - Sentiment spread  │
│ - Memory      │   │ - Overconfidence│   │ - Fear & Greed      │
└───────────────┘   └─────────────────┘   └─────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ MatchingEngine  │
                    │                 │
                    │ - Order book    │
                    │ - Price-time    │
                    │ - Market impact │
                    └─────────────────┘
```

## Components

### 1. InvestorBelief (`core/behavioral/investor_belief.py`)

Defines agent personas with distinct trading characteristics.

**Persona Types:**
- `CONSERVATIVE` - Low risk, high loss aversion
- `MODERATE` - Balanced approach
- `AGGRESSIVE` - High risk tolerance
- `CONTRARIAN` - Trades against the crowd
- `MOMENTUM` - Follows trends

**Usage:**
```python
from core.behavioral import InvestorBelief, PersonaType

# Create persona
persona = InvestorBelief(
    persona_type=PersonaType.AGGRESSIVE,
    initial_confidence=0.8
)

# Get persona's risk tolerance
risk = persona.risk_tolerance  # 0.8

# Update belief based on experience
persona.update_from_outcome(profit=0.05)  # Increase confidence
persona.update_from_outcome(profit=-0.10) # Decrease confidence

# Get current state
state = persona.to_dict()
```

**Persona Characteristics:**

| Persona | Risk Tolerance | Loss Aversion | Overconfidence |
|---------|---------------|---------------|----------------|
| Conservative | 0.2 | 2.5 | 0.0 |
| Moderate | 0.5 | 2.0 | 0.1 |
| Aggressive | 0.8 | 1.5 | 0.3 |
| Contrarian | 0.6 | 1.8 | 0.2 |
| Momentum | 0.7 | 1.6 | 0.25 |

### 2. BehavioralBiasEngine (`core/behavioral/behavioral_biases.py`)

Applies cognitive biases to trading decisions.

**Supported Biases:**

| Bias | Effect |
|------|--------|
| Disposition Effect | Hold losers too long, sell winners too early |
| Loss Aversion | Weight losses 2x more than gains |
| Lottery Preference | Overweight small probability gains |
| Overconfidence | Overestimate prediction accuracy |
| Anchoring | Over-rely on initial price point |
| Herding | Follow crowd behavior |

**Usage:**
```python
from core.behavioral import BehavioralBiasEngine

engine = BehavioralBiasEngine()

# Apply all biases to a decision
adjusted = engine.apply_all_biases(
    decision={
        "action": "sell",
        "confidence": 0.7,
        "position": {"entry_price": 100, "current_price": 90}
    },
    persona=persona,
    market_context={"trend": "bearish", "volatility": 0.3}
)

# Check specific bias effect
disposition = engine.apply_disposition_effect(position, action)
loss_aversion = engine.apply_loss_aversion(expected_gain, expected_loss)
```

**Prospect Theory Implementation:**

The module implements Kahneman & Tversky's prospect theory:

```
Value Function: v(x) = x^α if x >= 0
                       -λ(-x)^β if x < 0

Probability Weighting: w(p) = p^γ / (p^γ + (1-p)^γ)^(1/γ)

Parameters:
- α = 0.88 (diminishing sensitivity to gains)
- β = 0.88 (diminishing sensitivity to losses)
- λ = 2.25 (loss aversion coefficient)
- γ = 0.61 (probability distortion)
```

### 3. SocialSentimentNetwork (`core/behavioral/social_sentiment.py`)

Models social influence and herd behavior.

**Features:**
- Follow relationships between agents
- Sentiment propagation
- Fear & Greed Index calculation
- Herd event detection

**Usage:**
```python
from core.behavioral import SocialSentimentNetwork

network = SocialSentimentNetwork()

# Register agents
network.register_agent("agent1", influence_weight=0.8)
network.register_agent("agent2", influence_weight=0.5)
network.register_agent("agent3", influence_weight=0.3)

# Create follow relationships
network.add_follow("agent2", "agent1")  # agent2 follows agent1
network.add_follow("agent3", "agent1")
network.add_follow("agent3", "agent2")

# Update sentiment
network.update_sentiment("agent1", 0.8, "bullish")

# Propagate sentiment
network.propagate_sentiment()

# Get Fear & Greed Index
fg_index = network.get_fear_greed_index()
print(f"Fear & Greed: {fg_index}")  # 0-100 scale

# Check for herd behavior
if network.detect_herd_behavior(threshold=0.7):
    print("Herd behavior detected!")
```

**Fear & Greed Components:**
- Market momentum (20%)
- Price volatility (15%)
- Volume trends (15%)
- Social sentiment (25%)
- Agent consensus (25%)

### 4. MatchingEngine (`core/behavioral/matching_engine.py`)

Simulates realistic order book mechanics.

**Features:**
- Limit and market orders
- Price-time priority matching
- Partial fills
- Market impact simulation
- Spread calculation

**Usage:**
```python
from core.behavioral import MatchingEngine, OrderSide, OrderType

engine = MatchingEngine()

# Submit limit order
order, trades = engine.submit_order(
    agent_id="trader1",
    symbol="BTC/USDT",
    side=OrderSide.BUY,
    order_type=OrderType.LIMIT,
    quantity=1.0,
    price=50000.0
)

# Submit market order (immediate execution)
order, trades = engine.submit_order(
    agent_id="trader2",
    symbol="BTC/USDT",
    side=OrderSide.SELL,
    order_type=OrderType.MARKET,
    quantity=0.5
)

# Check market impact
impact = engine.simulate_market_impact(
    symbol="BTC/USDT",
    side=OrderSide.BUY,
    quantity=10.0
)
print(f"Expected slippage: {impact['slippage_percent']}%")

# Get order book depth
depth = engine.get_order_book("BTC/USDT")
```

## BehavioralAgentWrapper

Wraps any trading agent with behavioral modifications:

```python
from core.agents import BehavioralAgentWrapper

# Wrap existing agent
behavioral_agent = BehavioralAgentWrapper(
    base_agent=my_trading_agent,
    persona_type="aggressive",
    enable_biases=True,
    social_network=network
)

# Make decision (biases applied automatically)
decision = await behavioral_agent.decide(market_data)

# Get behavioral metrics
metrics = behavioral_agent.get_behavioral_metrics()
print(f"Biases applied: {metrics['biases_applied']}")
print(f"Social influence: {metrics['social_influence']}")
```

## Multi-Agent Simulation

Run behavioral market simulations:

```bash
# Run simulation
python tools/behavioral_simulation.py \
  --agents 20 \
  --rounds 100 \
  --symbol BTC/USDT \
  --output simulation_results.json

# With custom distribution
python tools/behavioral_simulation.py \
  --agents 50 \
  --conservative 30 \
  --moderate 30 \
  --aggressive 20 \
  --contrarian 10 \
  --momentum 10
```

**Simulation Features:**
- Agent persona distribution
- Social network formation
- Order book dynamics
- Herd event detection
- Performance metrics by persona

## API Endpoints

The behavioral dashboard provides REST API access:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/behavioral/status` | GET | Current behavioral status |
| `/behavioral/personas` | GET | Persona distribution |
| `/behavioral/biases` | GET | Bias application metrics |
| `/behavioral/sentiment` | GET | Sentiment and Fear & Greed |
| `/behavioral/herd-events` | GET | Recent herd events |
| `/behavioral/dashboard` | GET | Complete dashboard data |
| `/behavioral/register-agent` | POST | Register agent for tracking |
| `/behavioral/record-decision` | POST | Record behavioral decision |
| `/behavioral/agent/{id}` | GET | Agent-specific analytics |

**Example: Get Fear & Greed**
```bash
curl http://localhost:8000/api/behavioral/sentiment
```

**Response:**
```json
{
  "current": {
    "fear_greed_index": 65.5,
    "sentiment": "greed",
    "bullish_ratio": 0.72
  },
  "history": [...],
  "data_points": 48
}
```

## Configuration

Customize behavioral parameters:

```python
from core.behavioral import BehavioralBiasEngine, SocialSentimentNetwork

# Adjust bias strengths
engine = BehavioralBiasEngine(
    disposition_strength=1.0,    # Default: 1.0
    loss_aversion_lambda=2.25,   # Kahneman-Tversky default
    overconfidence_factor=0.2    # 20% overconfidence
)

# Configure social network
network = SocialSentimentNetwork(
    propagation_decay=0.8,       # Sentiment decay per hop
    herd_threshold=0.7,          # Consensus for herd detection
    update_interval=60           # Seconds between propagation
)
```

## Metrics & Analytics

Track behavioral patterns:

```python
# Get comprehensive metrics
metrics = behavioral_agent.get_behavioral_metrics()

# Available metrics:
# - decisions_made: Total decisions
# - biases_applied: Count by bias type
# - persona_shifts: Confidence changes
# - social_influence: Network effects
# - herd_participation: Herd event involvement
```

## Use Cases

### 1. Strategy Backtesting
Test strategies against behaviorally-realistic market participants:
```python
simulation = BehavioralMarketSimulation(agents=50)
results = simulation.run(strategy=my_strategy, rounds=1000)
```

### 2. Risk Assessment
Understand behavioral risks in your portfolio:
```python
risk = assess_behavioral_risk(portfolio, market_sentiment)
```

### 3. Agent Training
Train RL agents against behavioral opponents:
```python
env = BehavioralTradingEnv(opponents=behavioral_agents)
agent.train(env, episodes=10000)
```

### 4. Market Analysis
Detect herd behavior and sentiment extremes:
```python
if network.detect_herd_behavior():
    alert("Herd behavior detected - increased volatility expected")
```

## Testing

Run behavioral module tests:

```bash
# All behavioral tests
pytest tests/behavioral/ -v

# Specific component
pytest tests/behavioral/test_behavioral_biases.py -v
pytest tests/behavioral/test_social_sentiment.py -v
pytest tests/behavioral/test_matching_engine.py -v
```

## References

- TwinMarket: Twin Multi-Agent Society for Financial Market Simulation
- Kahneman & Tversky: Prospect Theory (1979)
- Behavioral Finance: Psychology, Decision-Making, and Markets
- Agent-Based Computational Finance: Literature Review
