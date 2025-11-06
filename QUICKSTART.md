# SIGMAX Quick Start Guide

**Get SIGMAX running in 5 minutes**

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file:

```bash
# Essential Configuration
TRADING_MODE=paper
TOTAL_CAPITAL=10000
EXCHANGE=binance
TESTNET=True

# Safety Limits
MAX_DAILY_LOSS=500
MAX_POSITION_SIZE=1000
STOP_LOSS_PCT=2
MAX_OPEN_TRADES=3
MAX_LEVERAGE=1

# LLM (choose one)
OLLAMA_BASE_URL=http://localhost:11434
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Validate Configuration

```bash
python -c "from core.config.validator import ConfigValidator; v = ConfigValidator(); print('✅ Valid' if v.validate_all() else '❌ Invalid')"
```

### 4. Run Tests

```bash
# Core validation tests (should pass)
pytest tests/validation/test_backtest_realistic.py \
       tests/validation/test_protocol_interfaces.py \
       tests/validation/test_environment_validation.py \
       tests/validation/test_emergency_and_cache.py -v

# Expected: 37/37 passing ✅
```

### 5. Run Backtest

```bash
python -m core.main --backtest --start 2024-01-01 --end 2024-12-31
```

### 6. Start Paper Trading

```bash
python -m core.main
```

## 📊 Core Tests: ✅ 37/37 PASSING

| Test Suite | Tests | Coverage |
|------------|-------|----------|
| Backtest Realistic | 6/6 ✅ | Buy & hold, multiple trades, metrics |
| Protocol Interfaces | 7/7 ✅ | DI, emergency stop, concurrent ops |
| Environment Validation | 11/11 ✅ | Config safety, API keys, limits |
| Emergency Stop | 5/5 ✅ | Position closing, idempotency |
| Cache Management | 8/8 ✅ | TTL, multi-symbol, concurrency |

## 🎯 Common Commands

```bash
# Run all validation tests
pytest tests/validation/ -v

# Paper trading mode
python -m core.main

# Backtest mode
python -m core.main --backtest --start 2024-01-01 --end 2024-12-31

# Emergency stop
python -m core.main --emergency-stop
```

## 🔗 Resources

- **VALIDATION_REPORT.md** - Comprehensive test results
- **DEPLOYMENT_GUIDE.md** - Production deployment steps
- **tests/validation/** - All validation tests

**Status:** ✅ READY FOR PAPER TRADING
