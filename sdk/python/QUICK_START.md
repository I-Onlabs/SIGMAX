# SIGMAX SDK - Quick Start Guide

Get started with the SIGMAX Python SDK in 5 minutes.

## Installation

```bash
pip install sigmax-sdk
```

## Minimal Example

```python
import asyncio
from sigmax_sdk import SigmaxClient

async def main():
    async with SigmaxClient() as client:
        status = await client.get_status()
        print(f"SIGMAX is {status.status}")

asyncio.run(main())
```

## Common Use Cases

### 1. Market Analysis

```python
from sigmax_sdk import SigmaxClient, RiskProfile

async with SigmaxClient() as client:
    result = await client.analyze(
        "BTC/USDT",
        risk_profile=RiskProfile.MODERATE
    )
    print(f"Recommendation: {result.get('recommendation')}")
```

### 2. Streaming Analysis

```python
async with SigmaxClient() as client:
    async for event in client.analyze_stream("ETH/USDT"):
        print(f"{event['status']}: {event.get('message', '')}")
        if event.get('final'):
            break
```

### 3. Trade Proposal

```python
from sigmax_sdk import TradeMode

async with SigmaxClient() as client:
    # Create proposal
    proposal = await client.propose_trade(
        "BTC/USDT",
        mode=TradeMode.PAPER,
        size=0.1
    )

    # Approve it
    await client.approve_proposal(proposal.proposal_id)

    # Execute it
    await client.execute_proposal(proposal.proposal_id)
```

### 4. Batch Analysis

```python
symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

async with SigmaxClient() as client:
    results = await asyncio.gather(*[
        client.analyze(symbol) for symbol in symbols
    ])

    for symbol, result in zip(symbols, results):
        print(f"{symbol}: {result.get('recommendation')}")
```

### 5. Error Handling

```python
from sigmax_sdk import (
    SigmaxAPIError,
    SigmaxConnectionError,
    SigmaxTimeoutError,
)

try:
    async with SigmaxClient() as client:
        result = await client.analyze("BTC/USDT")
except SigmaxConnectionError:
    print("Cannot connect to API")
except SigmaxTimeoutError:
    print("Request timed out")
except SigmaxAPIError as e:
    print(f"API error: {e.message}")
```

## Configuration

### API URL

```python
client = SigmaxClient(
    api_url="https://your-sigmax-instance.com",
    api_key="your-api-key"
)
```

### Timeout

```python
client = SigmaxClient(timeout=120.0)  # 2 minutes
```

### Custom Headers

```python
client = SigmaxClient(api_key="your-key")
# Headers automatically include Authorization
```

## Available Enums

```python
from sigmax_sdk import RiskProfile, TradeMode, ProposalStatus

# Risk levels
RiskProfile.CONSERVATIVE
RiskProfile.MODERATE
RiskProfile.AGGRESSIVE

# Trading modes
TradeMode.PAPER  # Simulated
TradeMode.LIVE   # Real money

# Proposal states
ProposalStatus.PENDING
ProposalStatus.APPROVED
ProposalStatus.EXECUTED
```

## Data Models

All responses are validated Pydantic models:

```python
from sigmax_sdk import SystemStatus, TradeProposal

# System status
status: SystemStatus = await client.get_status()
print(status.active_trades)  # Typed integer
print(status.uptime_seconds)  # Typed float

# Trade proposal
proposal: TradeProposal = await client.propose_trade(...)
print(proposal.size)  # Typed Decimal
print(proposal.created_at)  # Typed datetime
```

## Next Steps

1. **Read the full README**: [README.md](README.md)
2. **Try examples**: `python examples/basic_usage.py`
3. **Check API docs**: See docstrings in code
4. **Review error handling**: [examples/error_handling.py](examples/error_handling.py)
5. **Learn async patterns**: [examples/async_operations.py](examples/async_operations.py)

## Tips

- Always use `async with` for automatic cleanup
- Handle specific exceptions before generic ones
- Use `asyncio.gather()` for concurrent requests
- Check `status.api_health` before operations
- Use `TradeMode.PAPER` for testing
- Stream analysis for real-time updates

## Help

- **Examples**: See `examples/` directory
- **Issues**: https://github.com/I-Onlabs/SIGMAX/issues
- **Docs**: [PACKAGE_OVERVIEW.md](PACKAGE_OVERVIEW.md)

---

Ready to trade? Start with `TradeMode.PAPER` and test everything before going live!
