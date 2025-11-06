# SIGMAX Strategy Examples

This directory contains example trading strategies demonstrating how to build custom decision logic for SIGMAX.

## Available Strategies

### 1. Mean Reversion (`strategies/mean_reversion.py`)

**Type**: Statistical arbitrage
**Timeframe**: Medium frequency (seconds to minutes)
**Difficulty**: Beginner

Trades on orderbook imbalance with mean reversion logic:
- When bid volume >> ask volume → Price likely to fall → SELL
- When ask volume >> bid volume → Price likely to rise → BUY
- Only trades when imbalance exceeds threshold (40%)

**Key Features**:
- Simple orderbook microstructure strategy
- Microprice execution for better fills
- Post-only orders (maker rebates)
- Position tracking

**Example Use Case**: Scalping on BTC/USDT during liquid market hours

---

### 2. Momentum (`strategies/momentum.py`)

**Type**: Trend following
**Timeframe**: Medium frequency (minutes)
**Difficulty**: Beginner

Follows price trends with confirmation:
- Tracks price changes over multiple windows (3 periods)
- Bullish momentum: All positive changes > 0.3% → BUY
- Bearish momentum: All negative changes < -0.3% → SELL
- Volatility filter (max 2%)

**Key Features**:
- Confirmation periods prevent false signals
- Confidence-based sizing
- Volatility filtering
- Momentum reversal detection

**Example Use Case**: Catching trending moves on altcoins during high-momentum periods

---

### 3. Market Making (`strategies/market_making.py`)

**Type**: Liquidity provision
**Timeframe**: High frequency (sub-second)
**Difficulty**: Intermediate

Dual-sided quoting with inventory management:
- Quotes both bid and ask simultaneously
- Adjusts spread based on volatility
- Inventory skewing (widen spread on heavy side)
- Automatic requoting on market moves

**Key Features**:
- Post-only orders for maker rebates
- Volatility-adjusted spreads (10-50 bps)
- Inventory risk management
- High-frequency requoting

**Example Use Case**: Providing liquidity on BTC/USDT spot markets, earning bid-ask spread

---

### 4. Arbitrage (`strategies/arbitrage.py`)

**Type**: Cross-exchange arbitrage
**Timeframe**: Ultra-high frequency (milliseconds)
**Difficulty**: Advanced

Detects and executes cross-venue arbitrage:
- Monitors prices across multiple exchanges
- Detects arbitrage opportunities (buy low, sell high)
- Accounts for fees and slippage (min 20 bps profit)
- Simultaneous execution on both venues

**Key Features**:
- Multi-venue price monitoring
- Staleness filtering (100ms threshold)
- Fee accounting (maker/taker fees)
- IOC market orders for speed

**Example Use Case**: Arbitraging BTC/USDT price differences between Binance and Coinbase

---

## How to Use These Strategies

### Integration with SIGMAX

These strategies are **reference implementations**. To use them in SIGMAX:

1. **Study the logic**: Understand how each strategy generates signals
2. **Adapt to your needs**: Modify parameters, add filters, combine strategies
3. **Integrate with Decision Layer**:
   - Add to `apps/decision/strategies/` directory
   - Register in decision engine configuration
   - Implement required interface (`generate_signal`, `on_fill`)

### Strategy Interface

All strategies follow a common interface:

```python
class Strategy:
    def __init__(self, config):
        """Initialize with configuration"""
        pass

    def generate_signal(self, features: FeatureFrame) -> OrderIntent:
        """
        Generate trading signal from features.

        Args:
            features: Market features (price, spread, imbalance, volatility, etc.)

        Returns:
            OrderIntent or None
        """
        pass

    def on_fill(self, symbol_id: int, side: Side, qty: float):
        """Update position tracking on fill"""
        pass
```

### Running a Strategy

```python
# Example: Running mean reversion strategy
from examples.strategies.mean_reversion import MeanReversionStrategy, STRATEGY_CONFIG

# Initialize strategy
strategy = MeanReversionStrategy(STRATEGY_CONFIG)

# Generate signals (called by decision engine)
signal = strategy.generate_signal(features)

# Handle fills (called by execution engine)
if fill:
    strategy.on_fill(symbol_id, side, qty)
```

### Testing a Strategy

Use the backtesting framework (future work) or paper trading:

```bash
# Run SIGMAX in paper trading mode
python tools/runner.py --profile=a --paper-trading

# Load your strategy in apps/decision/config.yaml
# Monitor performance via Grafana dashboards
```

---

## Strategy Parameters

### Mean Reversion
```yaml
imbalance_threshold: 0.4      # 40% orderbook imbalance
min_spread_bps: 5.0          # Minimum 5 bps spread
max_position_qty: 1.0        # Max 1 BTC position
order_size_pct: 0.1          # 10% of max per trade
```

### Momentum
```yaml
momentum_threshold: 0.3      # 0.3% price change required
confirmation_periods: 3      # Need 3 consecutive signals
volatility_threshold: 0.02   # Max 2% volatility
max_position_qty: 1.0        # Max 1 BTC position
order_size_pct: 0.15         # 15% of max per trade
```

### Market Making
```yaml
base_spread_bps: 10.0        # Base 10 bps spread
min_spread_bps: 5.0          # Min 5 bps
max_spread_bps: 50.0         # Max 50 bps (high vol)
quote_size: 0.1              # 0.1 BTC per side
max_inventory: 2.0           # Max 2 BTC inventory deviation
inventory_skew_factor: 2.0   # Spread adjustment factor
```

### Arbitrage
```yaml
min_profit_bps: 20.0         # Min 20 bps profit after fees
maker_fee_bps: 2.0           # 0.02% maker fee
taker_fee_bps: 5.0           # 0.05% taker fee
max_arb_qty: 0.5             # Max 0.5 BTC per arb
staleness_threshold_ms: 100  # Max 100ms price age
```

---

## Performance Considerations

### Mean Reversion
- **Latency**: Medium (500ms - 2s)
- **Frequency**: 10-100 trades/day
- **Risk**: Moderate (directional bias during trends)
- **Capital**: $10k-$50k recommended

### Momentum
- **Latency**: Medium (1s - 5s)
- **Frequency**: 5-20 trades/day
- **Risk**: Moderate (whipsaws in choppy markets)
- **Capital**: $10k-$50k recommended

### Market Making
- **Latency**: Low (<100ms)
- **Frequency**: 1000s of trades/day
- **Risk**: High (inventory risk, adverse selection)
- **Capital**: $50k-$100k+ recommended

### Arbitrage
- **Latency**: Ultra-low (<10ms target)
- **Frequency**: 100s of trades/day
- **Risk**: Low (market-neutral)
- **Capital**: $20k-$100k recommended

---

## Risk Warnings

⚠️ **These are educational examples, not production-ready strategies!**

Before deploying:
1. **Backtest thoroughly** on historical data
2. **Paper trade** for extended periods (weeks/months)
3. **Start small** - use 10% of intended capital
4. **Monitor closely** - watch for unexpected behavior
5. **Set stop losses** - protect against catastrophic losses
6. **Understand market microstructure** - each venue has quirks
7. **Account for fees** - maker/taker fees significantly impact profitability
8. **Consider slippage** - market orders may fill at worse prices
9. **Regulatory compliance** - ensure you're allowed to trade algorithmically

---

## Next Steps

1. **Study the code**: Read through each strategy implementation
2. **Modify parameters**: Experiment with different thresholds and sizes
3. **Combine strategies**: Use multiple strategies simultaneously
4. **Add filters**: Implement additional risk filters (time-of-day, volatility regime, etc.)
5. **Build your own**: Create custom strategies based on your research

---

## Resources

- [SIGMAX Architecture](../README.md)
- [Quick Start Guide](../docs/QUICKSTART.md)
- [Decision Layer Documentation](../apps/decision/README.md)
- [Risk Engine Documentation](../apps/risk/README.md)
- [Feature Engineering](../apps/features/README.md)

---

## Contributing

Have a strategy idea? Submit a PR with:
- Strategy implementation following the interface
- Configuration example
- Documentation
- Unit tests

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.
