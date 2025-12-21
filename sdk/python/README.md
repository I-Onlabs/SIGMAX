# SIGMAX Python SDK

> ⚠️ **NOT YET PUBLISHED TO PyPI - INSTALL FROM SOURCE**
>
> This SDK is functional code but **not yet published** to PyPI.
> Use source installation below. Publishing planned for v0.3.0.

Official Python SDK for [SIGMAX](https://github.com/I-Onlabs/SIGMAX) - an autonomous AI-powered cryptocurrency trading system.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)](https://github.com/I-Onlabs/SIGMAX)

## ⚠️ Current Status

- **Version**: 0.2.0-alpha (NOT published)
- **Maturity**: Alpha - Research Software
- **Use Case**: Educational and Research Only
- **Production Ready**: No - Use at your own risk

## Features

- **Async-First Design**: Built on `httpx` for high-performance async operations
- **Type-Safe**: Complete type hints with Pydantic models for validation
- **Streaming Support**: Real-time analysis updates via Server-Sent Events (SSE)
- **Well-Tested**: Unit tests with pytest and async support
- **Easy to Use**: Pythonic API with context managers and async iterators

## Installation

### ~~From PyPI~~ **[NOT AVAILABLE YET]**

```bash
# ❌ This will NOT work until we publish to PyPI
# pip install sigmax-sdk
```

### From Source (Required for now)

```bash
git clone https://github.com/I-Onlabs/SIGMAX.git
cd SIGMAX/sdk/python
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage

```python
import asyncio
from sigmax_sdk import SigmaxClient, RiskProfile, TradeMode

async def main():
    # Initialize client
    async with SigmaxClient(
        api_url="http://localhost:8000",
        api_key="your-api-key"  # Optional for local development
    ) as client:
        # Get system status
        status = await client.get_status()
        print(f"System: {status.status}")
        print(f"Active trades: {status.active_trades}")

        # Analyze a trading pair
        result = await client.analyze(
            "BTC/USDT",
            risk_profile=RiskProfile.MODERATE
        )
        print(f"Analysis: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Streaming Analysis

```python
from sigmax_sdk import SigmaxClient, RiskProfile

async def stream_analysis():
    async with SigmaxClient() as client:
        # Stream real-time analysis updates
        async for event in client.analyze_stream(
            "ETH/USDT",
            risk_profile=RiskProfile.AGGRESSIVE
        ):
            print(f"Event: {event.get('type')}")
            print(f"Status: {event.get('status')}")
            print(f"Message: {event.get('message')}")

asyncio.run(stream_analysis())
```

### Trade Proposal Workflow

```python
from sigmax_sdk import SigmaxClient, RiskProfile, TradeMode

async def trade_workflow():
    async with SigmaxClient() as client:
        # Create a trade proposal
        proposal = await client.propose_trade(
            symbol="BTC/USDT",
            risk_profile=RiskProfile.MODERATE,
            mode=TradeMode.PAPER,
            size=0.1
        )
        print(f"Proposal created: {proposal.proposal_id}")
        print(f"Side: {proposal.side}, Size: {proposal.size}")
        print(f"Rationale: {proposal.rationale}")

        # List all proposals
        proposals = await client.list_proposals()
        print(f"Total proposals: {len(proposals)}")

        # Approve the proposal
        approval = await client.approve_proposal(proposal.proposal_id)
        print(f"Approved: {approval}")

        # Execute the proposal
        result = await client.execute_proposal(proposal.proposal_id)
        print(f"Execution result: {result}")

asyncio.run(trade_workflow())
```

## API Reference

### Client Initialization

```python
SigmaxClient(
    api_url: str = "http://localhost:8000",
    api_key: Optional[str] = None,
    timeout: float = 60.0,
    max_retries: int = 3
)
```

**Parameters:**
- `api_url`: Base URL of SIGMAX API
- `api_key`: Authentication key (optional for local development)
- `timeout`: Request timeout in seconds
- `max_retries`: Maximum retry attempts on failure

### Core Methods

#### `analyze(symbol, risk_profile, mode)`

Synchronous market analysis (returns final result only).

**Parameters:**
- `symbol` (str): Trading pair (e.g., "BTC/USDT")
- `risk_profile` (RiskProfile): CONSERVATIVE, MODERATE, or AGGRESSIVE
- `mode` (TradeMode): PAPER or LIVE

**Returns:** `dict[str, Any]` - Final analysis result

**Example:**
```python
result = await client.analyze("BTC/USDT", RiskProfile.CONSERVATIVE)
```

#### `analyze_stream(symbol, risk_profile, mode)`

Streaming market analysis with real-time updates.

**Parameters:** Same as `analyze()`

**Yields:** `StreamEvent` - Progress events

**Example:**
```python
async for event in client.analyze_stream("ETH/USDT"):
    print(event['status'])
```

#### `get_status()`

Get current system status.

**Returns:** `SystemStatus` - System health and metrics

**Example:**
```python
status = await client.get_status()
print(f"Uptime: {status.uptime_seconds}s")
```

#### `propose_trade(symbol, risk_profile, mode, size)`

Create a new trade proposal.

**Parameters:**
- `symbol` (str): Trading pair
- `risk_profile` (RiskProfile): Risk level
- `mode` (TradeMode): Trading mode
- `size` (Optional[float]): Trade size

**Returns:** `TradeProposal`

**Example:**
```python
proposal = await client.propose_trade("BTC/USDT", size=0.1)
```

#### `list_proposals()`

List all trade proposals.

**Returns:** `dict[str, TradeProposal]` - Mapping of proposal IDs to proposals

**Example:**
```python
proposals = await client.list_proposals()
for pid, proposal in proposals.items():
    print(f"{pid}: {proposal.status}")
```

#### `get_proposal(proposal_id)`

Get specific proposal details.

**Parameters:**
- `proposal_id` (str): Unique proposal identifier

**Returns:** `TradeProposal`

**Example:**
```python
proposal = await client.get_proposal("prop_123")
```

#### `approve_proposal(proposal_id)`

Approve a pending proposal.

**Parameters:**
- `proposal_id` (str): Proposal to approve

**Returns:** `dict[str, Any]` - Approval result

**Example:**
```python
result = await client.approve_proposal("prop_123")
```

#### `execute_proposal(proposal_id)`

Execute an approved proposal.

**Parameters:**
- `proposal_id` (str): Proposal to execute

**Returns:** `dict[str, Any]` - Execution result

**Example:**
```python
result = await client.execute_proposal("prop_123")
```

## Data Models

### RiskProfile (Enum)

```python
class RiskProfile(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
```

### TradeMode (Enum)

```python
class TradeMode(str, Enum):
    PAPER = "paper"  # Simulated trading
    LIVE = "live"    # Real trading
```

### ProposalStatus (Enum)

```python
class ProposalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
```

### TradeProposal

```python
class TradeProposal(BaseModel):
    proposal_id: str
    symbol: str
    side: str  # "buy" or "sell"
    size: Decimal
    price: Optional[Decimal]
    stop_loss: Optional[Decimal]
    take_profit: Optional[Decimal]
    status: ProposalStatus
    risk_profile: RiskProfile
    mode: TradeMode
    rationale: str
    created_at: datetime
    updated_at: datetime
```

### SystemStatus

```python
class SystemStatus(BaseModel):
    status: str  # "online", "offline", "degraded"
    version: str
    uptime_seconds: float
    active_trades: int
    pending_proposals: int
    mode: TradeMode
    api_health: bool
    database_health: bool
    exchange_health: bool
    timestamp: datetime
```

## Error Handling

The SDK provides comprehensive exception handling:

```python
from sigmax_sdk import (
    SigmaxError,              # Base exception
    SigmaxAPIError,           # API-level errors
    SigmaxAuthenticationError, # 401/403 errors
    SigmaxRateLimitError,     # 429 rate limit
    SigmaxValidationError,    # 400/422 validation
    SigmaxConnectionError,    # Network errors
    SigmaxTimeoutError,       # Timeout errors
)

async def safe_analysis():
    try:
        async with SigmaxClient() as client:
            result = await client.analyze("BTC/USDT")
    except SigmaxAuthenticationError:
        print("Invalid API key")
    except SigmaxRateLimitError as e:
        print(f"Rate limited, retry after {e.retry_after}s")
    except SigmaxConnectionError:
        print("Cannot connect to API")
    except SigmaxTimeoutError:
        print("Request timed out")
    except SigmaxAPIError as e:
        print(f"API error: {e.message} (status: {e.status_code})")
```

## Advanced Usage

### Manual Client Management

```python
# Without context manager
client = SigmaxClient(api_key="your-key")

try:
    status = await client.get_status()
finally:
    await client.close()
```

### Batch Operations

```python
async def batch_analysis():
    async with SigmaxClient() as client:
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

        # Concurrent analysis
        tasks = [
            client.analyze(symbol, RiskProfile.MODERATE)
            for symbol in symbols
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                print(f"{symbol} failed: {result}")
            else:
                print(f"{symbol} result: {result}")
```

### Custom Timeout

```python
# Per-client timeout
client = SigmaxClient(timeout=120.0)

# Or override per-request (modify client internals)
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# With coverage
pytest --cov=sigmax_sdk --cov-report=html
```

### Type Checking

```bash
mypy sigmax_sdk
```

### Code Formatting

```bash
# Format code
black sigmax_sdk

# Lint
ruff check sigmax_sdk
```

## Requirements

- Python 3.11+
- httpx >= 0.27.0
- httpx-sse >= 0.4.0
- pydantic >= 2.0.0

## Contributing

Contributions are welcome! Please see the [main repository](https://github.com/I-Onlabs/SIGMAX) for contribution guidelines.

## License

MIT License - see [LICENSE](https://github.com/I-Onlabs/SIGMAX/blob/main/LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/I-Onlabs/SIGMAX/issues)
- **Documentation**: [SIGMAX Docs](https://github.com/I-Onlabs/SIGMAX/tree/main/docs)
- **Discussions**: [GitHub Discussions](https://github.com/I-Onlabs/SIGMAX/discussions)

## Related Projects

- [SIGMAX Core](https://github.com/I-Onlabs/SIGMAX) - Main trading system
- [SIGMAX CLI](https://github.com/I-Onlabs/SIGMAX/tree/main/core/cli) - Command-line interface

---

**Disclaimer**: Cryptocurrency trading carries significant risk. This software is provided "as is" without warranty. Always test with paper trading before using real funds.
