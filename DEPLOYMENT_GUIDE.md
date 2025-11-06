# SIGMAX Production Deployment Guide

**Version:** 1.0
**Date:** November 6, 2025
**Validation Status:** ✅ CORE TESTS PASSING (37/37)

## Pre-Deployment Checklist

### ✅ Phase 1: Core System Validation (COMPLETED)

- [x] Backtest engine validated (6/6 tests)
- [x] Protocol interfaces tested (7/7 tests)
- [x] Environment configuration validated (11/11 tests)
- [x] Emergency stop tested (5/5 tests)
- [x] Cache management verified (8/8 tests)
- [x] Safety limits enforced (max 3x leverage)
- [x] API key validation working
- [x] All critical paths tested

**Result:** 37/37 core tests passing ✅

### 📋 Phase 2: Pre-Production Setup (TODO)

#### Environment Configuration

```bash
# 1. Set trading mode to paper
export TRADING_MODE=paper

# 2. Configure capital
export TOTAL_CAPITAL=10000  # Start conservative

# 3. Set safety limits (RECOMMENDED)
export MAX_DAILY_LOSS=500        # 5% of capital
export MAX_POSITION_SIZE=1000    # 10% of capital
export STOP_LOSS_PCT=2           # 2% stop loss
export MAX_OPEN_TRADES=3         # Limit concurrent trades
export MAX_LEVERAGE=1            # No leverage initially

# 4. Configure exchange
export EXCHANGE=binance
export TESTNET=True              # Use testnet first!

# 5. Configure LLM (choose one)
export OLLAMA_BASE_URL=http://localhost:11434  # For local Ollama
# OR
export OPENAI_API_KEY=sk-...    # For OpenAI
# OR
export ANTHROPIC_API_KEY=sk-ant-...  # For Claude

# 6. Optional: Database
export POSTGRES_URL=postgresql://user:pass@localhost/sigmax
export REDIS_URL=redis://localhost:6379
```

#### Validation Steps

```bash
# 1. Run core test suite
python -m pytest tests/validation/test_backtest_realistic.py \
                 tests/validation/test_protocol_interfaces.py \
                 tests/validation/test_environment_validation.py \
                 tests/validation/test_emergency_and_cache.py -v

# Expected: 37/37 tests passing

# 2. Validate configuration
python -c "from core.config.validator import ConfigValidator; v = ConfigValidator(); v.validate_all(); print(v.get_summary())"

# 3. Test emergency stop
python -c "
import asyncio
from core.modules.execution import ExecutionModule
async def test():
    exec_mod = ExecutionModule(mode='paper')
    await exec_mod.initialize()
    result = await exec_mod.close_all_positions()
    print(f'Emergency stop: {result}')
asyncio.run(test())
"
```

### 📋 Phase 3: Paper Trading Deployment (1-2 weeks)

#### Week 1: Initial Testing

**Day 1-3: System Initialization**
- [ ] Deploy to paper trading environment
- [ ] Configure Telegram bot for alerts
- [ ] Set up monitoring dashboard
- [ ] Verify all modules initialize correctly
- [ ] Test with single symbol (BTC/USDT)

**Day 4-7: Expanded Testing**
- [ ] Add more symbols (ETH, SOL, etc.)
- [ ] Monitor performance metrics
- [ ] Verify emergency stop works in production
- [ ] Check cache performance
- [ ] Review logs daily

#### Week 2: Validation & Tuning

**Day 8-10: Performance Analysis**
- [ ] Analyze win rate vs backtest predictions
- [ ] Review Sharpe/Sortino ratios
- [ ] Check drawdown levels
- [ ] Verify risk limits are respected
- [ ] Analyze agent decision quality

**Day 11-14: Final Preparation**
- [ ] Tune strategy parameters if needed
- [ ] Stress test with high volatility
- [ ] Verify compliance checks
- [ ] Document any issues found
- [ ] Create incident response plan

### 📋 Phase 4: Live Trading Preparation (BEFORE REAL MONEY)

#### Safety Configuration

```bash
# CRITICAL: Update for live trading
export TRADING_MODE=live
export TESTNET=False  # ⚠️ REAL MONEY
export API_KEY=your_real_api_key
export API_SECRET=your_real_api_secret

# ULTRA-CONSERVATIVE LIMITS FOR FIRST MONTH
export TOTAL_CAPITAL=1000        # Start very small!
export MAX_DAILY_LOSS=50         # 5% max daily loss
export MAX_POSITION_SIZE=100     # 10% max position
export STOP_LOSS_PCT=1.5         # Tight stop loss
export MAX_OPEN_TRADES=2         # Only 2 concurrent trades
export MAX_LEVERAGE=1            # NO LEVERAGE
```

#### Pre-Live Checklist

- [ ] Paper trading ran successfully for 2+ weeks
- [ ] Win rate acceptable (>45%)
- [ ] Max drawdown manageable (<15%)
- [ ] Emergency stop tested multiple times
- [ ] All alerts working correctly
- [ ] Telegram notifications verified
- [ ] API keys secured properly
- [ ] Backup and disaster recovery plan ready
- [ ] Trading journal/log system active
- [ ] Team member trained on emergency procedures

#### Go-Live Steps

1. **Double-check configuration**
   ```bash
   python -c "from core.config.validator import ConfigValidator; v = ConfigValidator(); assert v.validate_all(), 'Config invalid!'"
   ```

2. **Start with minimal capital**
   - Use $500-$1000 maximum initially
   - Verify real trades execute correctly
   - Monitor for 24 hours continuously

3. **Gradual scale-up**
   - Week 1: $1,000 capital
   - Week 2: $2,500 capital (if performing well)
   - Week 3: $5,000 capital (if stable)
   - Month 2+: Scale based on performance

4. **Daily monitoring**
   - Check performance metrics every morning
   - Review trades and decisions
   - Monitor risk metrics
   - Be ready to hit emergency stop

## Monitoring & Maintenance

### Daily Checks

```bash
# 1. System health
curl http://localhost:8000/health  # If API enabled

# 2. Check logs
tail -f logs/sigmax.log | grep -E "(ERROR|WARNING|EMERGENCY)"

# 3. Performance summary
python scripts/daily_report.py  # Create this script

# 4. Emergency stop test (weekly)
python -c "
import asyncio
from core.main import SIGMAX
async def test():
    sigmax = SIGMAX()
    await sigmax.initialize()
    result = await sigmax.emergency_stop()
    print(f'Emergency stop OK: {result}')
asyncio.run(test())
"
```

### Key Metrics to Monitor

**Performance Metrics:**
- Daily PnL
- Win rate
- Sharpe ratio
- Max drawdown
- Average trade duration

**Risk Metrics:**
- Current positions vs MAX_OPEN_TRADES
- Position sizes vs MAX_POSITION_SIZE
- Daily loss vs MAX_DAILY_LOSS
- Leverage used vs MAX_LEVERAGE

**System Metrics:**
- Cache hit rate (should be >80%)
- API call frequency
- Memory usage
- Error rates

### Alert Thresholds

**EMERGENCY (Immediate Action):**
- Daily loss > 80% of MAX_DAILY_LOSS
- Single position loss > 5%
- API connection failures
- Data module failures

**WARNING (Review Required):**
- Win rate < 40%
- Drawdown > 10%
- Cache hit rate < 70%
- High error rates

**INFO (Monitor):**
- New high in equity
- Unusual market volatility
- Performance milestones

## Emergency Procedures

### Emergency Stop Protocol

**When to trigger:**
- Unexpected large losses
- System behaving erratically
- Market flash crash
- API issues
- Any safety concern

**How to trigger:**

1. **Via Telegram Bot:**
   ```
   /emergency_stop
   ```

2. **Via Python:**
   ```python
   import asyncio
   from core.main import SIGMAX

   async def emergency():
       sigmax = SIGMAX()
       await sigmax.initialize()
       await sigmax.emergency_stop()

   asyncio.run(emergency())
   ```

3. **Via CLI:**
   ```bash
   python -m core.main --emergency-stop
   ```

**Post-Emergency Actions:**
1. Verify all positions closed
2. Review logs for root cause
3. Document the incident
4. Fix any issues found
5. Run validation tests before restart
6. Consider reducing capital/limits

## Performance Expectations

### Realistic Targets (Based on Backtests)

**Conservative Strategy:**
- Annual Return: 15-30%
- Win Rate: 45-55%
- Sharpe Ratio: 1.0-2.0
- Max Drawdown: 10-20%

**Moderate Strategy:**
- Annual Return: 30-60%
- Win Rate: 50-60%
- Sharpe Ratio: 1.5-2.5
- Max Drawdown: 15-25%

**Aggressive Strategy:** (NOT RECOMMENDED INITIALLY)
- Annual Return: 60%+
- Win Rate: 55%+
- Sharpe Ratio: 2.0+
- Max Drawdown: 20-30%

### Warning Signs

**Stop trading if:**
- 3 consecutive days of losses
- Win rate drops below 35%
- Drawdown exceeds 25%
- System errors increasing
- Compliance violations occurring

## Troubleshooting

### Common Issues

**1. High Loss Rate**
- Review agent decisions in logs
- Check if market regime changed
- Consider adjusting STOP_LOSS_PCT
- Reduce position sizes

**2. System Crashes**
- Check memory usage
- Review error logs
- Verify API connectivity
- Restart with validation tests

**3. Poor Performance**
- Analyze against backtest expectations
- Review market conditions
- Check if parameters need tuning
- Consider different symbols/timeframes

**4. API Rate Limits**
- Increase cache TTL
- Reduce update frequency
- Use longer timeframes
- Add rate limit handling

## Support & Resources

### Documentation
- `/home/user/SIGMAX/VALIDATION_REPORT.md` - Validation results
- `/home/user/SIGMAX/README.md` - System overview
- `/home/user/SIGMAX/docs/` - API documentation

### Test Suites
- `tests/validation/` - Validation tests
- `tests/integration/` - Integration tests
- `tests/modules/` - Unit tests

### Logs
- `logs/sigmax.log` - Main application log
- `logs/trades.log` - Trade execution log
- `logs/errors.log` - Error log

### Contact
- GitHub Issues: https://github.com/I-Onlabs/SIGMAX/issues
- Emergency: [Add emergency contact]

## Final Reminders

🚨 **CRITICAL SAFETY RULES:**

1. **Never disable safety limits** without thorough testing
2. **Always use TESTNET first** before live trading
3. **Start with minimal capital** ($500-$1000 max)
4. **Monitor daily** for the first month
5. **Keep emergency stop accessible** at all times
6. **Never exceed 3x leverage** without expert review
7. **Document everything** - keep trading journal
8. **Have exit strategy** - know when to stop

✅ **Success Criteria:**

- All core tests passing (37/37) ✅
- 2+ weeks successful paper trading
- Win rate > 45%
- Max drawdown < 20%
- Emergency stop tested and working
- All safety limits respected
- Monitoring and alerts active

---

**Current Status:** ✅ READY FOR PAPER TRADING
**Next Step:** Configure environment and start Phase 2
**Target Live Date:** 2-4 weeks after paper trading begins
**Recommended Start Capital:** $500-$1000
