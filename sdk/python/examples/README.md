# SIGMAX SDK Examples

This directory contains comprehensive examples demonstrating the SIGMAX SDK functionality.

## Running Examples

1. **Install the SDK:**
   ```bash
   pip install sigmax-sdk
   # or for development:
   cd ../
   pip install -e .
   ```

2. **Ensure SIGMAX API is running:**
   ```bash
   # Default: http://localhost:8000
   # Or set custom URL in examples
   ```

3. **Run any example:**
   ```bash
   python examples/basic_usage.py
   python examples/streaming.py
   python examples/async_operations.py
   python examples/error_handling.py
   ```

## Available Examples

### 1. basic_usage.py

**What it demonstrates:**
- Client initialization
- System status checks
- Synchronous market analysis
- Listing trade proposals
- Basic error handling

**Best for:** Getting started with the SDK

**Key concepts:**
```python
async with SigmaxClient(api_url="http://localhost:8000") as client:
    status = await client.get_status()
    result = await client.analyze("BTC/USDT")
    proposals = await client.list_proposals()
```

**Run time:** ~30 seconds

---

### 2. streaming.py

**What it demonstrates:**
- Server-Sent Events (SSE) streaming
- Real-time analysis progress
- Event filtering
- Concurrent streams
- Timestamp tracking

**Best for:** Understanding real-time updates

**Key concepts:**
```python
async for event in client.analyze_stream("BTC/USDT"):
    print(f"Event: {event['type']}")
    print(f"Status: {event['status']}")
    if event.get('final'):
        break
```

**Run time:** ~1-2 minutes (streaming)

---

### 3. async_operations.py

**What it demonstrates:**
- Concurrent batch operations
- Task gathering with `asyncio.gather()`
- Retry patterns with exponential backoff
- Complete proposal workflow
- Parallel proposal creation
- System monitoring
- Advanced async patterns

**Best for:** Production-ready async code

**Key concepts:**
```python
# Concurrent analysis
tasks = [client.analyze(symbol) for symbol in symbols]
results = await asyncio.gather(*tasks, return_exceptions=True)

# Retry with backoff
for attempt in range(max_retries):
    try:
        return await client.analyze(symbol)
    except SigmaxTimeoutError:
        await asyncio.sleep(2 ** attempt)
```

**Run time:** ~2-3 minutes

---

### 4. error_handling.py

**What it demonstrates:**
- Complete exception hierarchy
- Authentication errors
- Connection failures
- Validation errors
- Rate limiting
- Timeout handling
- Graceful degradation
- Context manager cleanup

**Best for:** Robust error handling patterns

**Key concepts:**
```python
try:
    result = await client.analyze("BTC/USDT")
except SigmaxAuthenticationError:
    print("Invalid API key")
except SigmaxRateLimitError as e:
    await asyncio.sleep(e.retry_after or 5)
except SigmaxConnectionError:
    print("API unavailable, using fallback")
```

**Run time:** ~1-2 minutes

---

## Common Patterns

### Client Initialization

```python
# With context manager (recommended)
async with SigmaxClient(
    api_url="http://localhost:8000",
    api_key="your-key",  # Optional
    timeout=60.0,
) as client:
    # Use client
    pass

# Manual management
client = SigmaxClient()
try:
    # Use client
    pass
finally:
    await client.close()
```

### Error Handling

```python
from sigmax_sdk import (
    SigmaxAPIError,
    SigmaxAuthenticationError,
    SigmaxConnectionError,
)

try:
    result = await client.analyze("BTC/USDT")
except SigmaxAuthenticationError:
    # Handle auth errors
    pass
except SigmaxConnectionError:
    # Handle connection errors
    pass
except SigmaxAPIError as e:
    # Handle all API errors
    print(f"Error: {e.message} (status: {e.status_code})")
```

### Batch Operations

```python
# Concurrent analysis
symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
tasks = [client.analyze(symbol) for symbol in symbols]
results = await asyncio.gather(*tasks, return_exceptions=True)

for symbol, result in zip(symbols, results):
    if isinstance(result, Exception):
        print(f"{symbol}: Error - {result}")
    else:
        print(f"{symbol}: {result}")
```

### Streaming Analysis

```python
async for event in client.analyze_stream("BTC/USDT"):
    event_type = event.get("type")
    status = event.get("status")

    if event_type == "progress":
        print(f"Progress: {status}")
    elif event_type == "complete":
        print("Analysis complete!")
        break
```

### Complete Workflow

```python
# 1. Analyze market
result = await client.analyze("BTC/USDT", RiskProfile.MODERATE)

# 2. Create proposal
proposal = await client.propose_trade(
    "BTC/USDT",
    risk_profile=RiskProfile.MODERATE,
    size=0.1
)

# 3. Review and approve
retrieved = await client.get_proposal(proposal.proposal_id)
if retrieved.status == ProposalStatus.PENDING:
    await client.approve_proposal(proposal.proposal_id)

# 4. Execute
result = await client.execute_proposal(proposal.proposal_id)
```

## Customization

### Change API URL

Edit examples to use your deployment:

```python
client = SigmaxClient(
    api_url="https://your-sigmax-instance.com",
    api_key="your-api-key"
)
```

### Adjust Risk Profiles

```python
from sigmax_sdk import RiskProfile

# Conservative (default)
await client.analyze("BTC/USDT", RiskProfile.CONSERVATIVE)

# Moderate
await client.analyze("BTC/USDT", RiskProfile.MODERATE)

# Aggressive
await client.analyze("BTC/USDT", RiskProfile.AGGRESSIVE)
```

### Trading Modes

```python
from sigmax_sdk import TradeMode

# Paper trading (simulated)
await client.propose_trade("BTC/USDT", mode=TradeMode.PAPER)

# Live trading (real money)
await client.propose_trade("BTC/USDT", mode=TradeMode.LIVE)
```

## Troubleshooting

### Connection Refused

```
SigmaxConnectionError: Connection failed
```

**Solution:** Ensure SIGMAX API is running on the configured URL

### Import Errors

```
ModuleNotFoundError: No module named 'sigmax_sdk'
```

**Solution:** Install SDK: `pip install sigmax-sdk`

### Authentication Errors

```
SigmaxAuthenticationError: Authentication failed
```

**Solution:** Check API key or remove for local development

### Timeout Errors

```
SigmaxTimeoutError: Request timeout
```

**Solution:** Increase timeout or check API performance

## Next Steps

1. **Read the main README:** `../README.md`
2. **Review API documentation:** See docstrings in `sigmax_sdk/client.py`
3. **Explore data models:** Check `sigmax_sdk/models.py`
4. **Build your application:** Use examples as templates

## Support

- **Issues:** https://github.com/I-Onlabs/SIGMAX/issues
- **Discussions:** https://github.com/I-Onlabs/SIGMAX/discussions
- **Documentation:** https://github.com/I-Onlabs/SIGMAX/tree/main/sdk/python
